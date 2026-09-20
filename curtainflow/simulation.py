"""Executed air/parcel calculation and one-way pressure-to-strip continuation.

This phase-one study keeps the flow boundary fixed. Structural displacement is
a computed response to its load, not an assertion that the air domain moved.
"""
from dataclasses import dataclass,asdict
from pathlib import Path
import json,time
import numpy as np
from scipy.integrate import solve_ivp
from .grid import Grid
from .droplets import Cloud
from .mechanics import matrices,elastic


@dataclass
class Config:
    shape: tuple = (24,32,32)
    length: tuple = (1.8,2.4,2.4)
    curtain_x: float = .9
    bottom: float = .3
    top: float = 2.1
    dt: float = .004
    duration: float = 12.
    output_interval: float = .1
    flow_lpm: float = 8.
    diameter_mm: float = 1.
    speed: float = 1.
    tilt_deg: float = 20.
    cone_half_deg: float = 8.
    head: tuple = (.45,.35,2.1)
    head_radius: float = .05
    rays: int = 12
    water_delta_T: float = 18.
    momentum: bool = True
    heat: bool = False
    rho: float = 1.2
    nu: float = .003015
    alpha: float = .004307
    beta: float = 1/295.15
    g: float = 9.81


def run(cfg,output=None,quiet=False):
    start=time.monotonic()
    grid=Grid(cfg.shape,cfg.length,curtain_x=cfg.curtain_x,bottom=cfg.bottom,top=cfg.top)
    cloud=Cloud(grid,**{k:getattr(cfg,k) for k in ['flow_lpm','diameter_mm','speed','tilt_deg','cone_half_deg','head','head_radius','rays','water_delta_T','momentum','heat']},curtain_x=cfg.curtain_x,curtain_bottom=cfg.bottom,curtain_top=cfg.top,rho_air=cfg.rho,g=cfg.g)
    u=np.zeros((3,)+tuple(cfg.shape));theta=np.zeros(cfg.shape);p=np.zeros(cfg.shape)
    ix=round(cfg.curtain_x/grid.h[0]);iz=np.flatnonzero((grid.axes[2]>cfg.bottom)&(grid.axes[2]<cfg.top))
    cut=int(np.argmin(abs(grid.axes[0]-.45)))
    other=int(np.argmin(abs(grid.axes[1]-.6)))
    steps=int(np.ceil(cfg.duration/cfg.dt));dt=cfg.duration/steps
    stride=max(1,round(cfg.output_interval/dt))
    history=[];pressures=[];temperature=[];velocity=[];cross_pressure=[];cross_velocity=[];loads=[];viscous=[];parts=[]
    maxdiv=0.;maxcfl=0.;maxleak=0.;min_temp=0.;max_mass_error=0.;max_water_momentum_error=0.;max_water_heat_error=0.;diag={}
    def rhs(v):return -grid.convection(v)+cfg.nu*grid.diffusion(v)
    for it in range(steps+1):
        if it%stride==0 or it==steps:
            dp=p[ix][:,iz]-p[ix-1][:,iz]
            uc=grid.centers(u)
            history.append([it*dt,float(dp.mean()),float(dp.min()),float(dp.max()),float(np.max(np.linalg.norm(uc,axis=0))),float(theta.max()),float(theta[:ix].mean()),float(theta[ix:].mean()),len(cloud.positions)])
            pressures.append(p[cut].astype('f4'));temperature.append(theta[cut].astype('f4'));velocity.append(uc[:,cut].astype('f4'))
            cross_pressure.append(p[:,other,:].astype('f4'));cross_velocity.append(uc[:,:,other,:].astype('f4'))
            loads.append(dp.astype('f4'))
            correction=-2*cfg.rho*cfg.nu*(u[0,ix]+u[0,ix-2])/grid.h[0]
            viscous.append(correction[:,iz].astype('f4'))
            # Deterministic representative subset, with NaN padding. These are water parcels.
            snap=np.full((200,3),np.nan,dtype='f4')
            if len(cloud.positions):
                select=np.linspace(0,len(cloud.positions)-1,min(200,len(cloud.positions))).astype(int)
                snap[:len(select)]=cloud.positions[select]
            parts.append(snap)
        if it==steps:break
        force,heat_rate,diag=cloud.step(u,theta,dt,it*dt)
        buoy=np.zeros_like(u);buoy[2]=cfg.g*cfg.beta*theta
        body=force/cfg.rho+grid.faces(buoy)
        # SSPRK2 air transport; parcel exchange held over this small time step.
        first,pfirst=grid.project(u+dt*(rhs(u)+body),dt,cfg.rho)
        unew,psecond=grid.project(.5*u+.5*(first+dt*(rhs(first)+body)),dt,cfg.rho)
        # Both projection corrections contribute to the full-step pressure.
        p=.5*pfirst+psecond
        if cfg.heat:
            k1=-grid.scalar_transport(u,theta,scheme='tvd')+cfg.alpha*grid.lap(theta)+heat_rate
            stage=theta+dt*k1
            k2=-grid.scalar_transport(first,stage,scheme='tvd')+cfg.alpha*grid.lap(stage)+heat_rate
            theta=.5*theta+.5*(stage+dt*k2)
        u=unew
        div=float(np.max(abs(grid.div(u))));cfl=dt*sum(float(abs(u[d]).max())/grid.h[d] for d in range(3))
        leak=float(np.max(abs(u)*(1-grid.mask_faces)))
        maxdiv=max(maxdiv,div);maxcfl=max(maxcfl,cfl);maxleak=max(maxleak,leak)
        min_temp=min(min_temp,float(theta.min()))
        max_mass_error=max(max_mass_error,abs(diag.get('mass_balance_error_kg',0)))
        max_water_momentum_error=max(max_water_momentum_error,float(np.max(abs(np.array(diag.get('water_momentum_balance_error_kg_m_s',[0]))))))
        max_water_heat_error=max(max_water_heat_error,abs(diag.get('water_heat_balance_error_J',0)))
        if not np.isfinite(u).all() or not np.isfinite(theta).all() or cfl>.8:
            raise RuntimeError(f'Numerical state failed at {it*dt:.3f}s; CFL {cfl:.4f}')
        if not quiet and it%max(1,steps//6)==0:
            print(f't={it*dt:.2f}s grid={cfg.shape} elapsed={time.monotonic()-start:.1f}s dp={history[-1][1]:+.5f}Pa',flush=True)
    air_heat=float(theta.sum()*np.prod(grid.h)*cfg.rho*1005)
    meta=asdict(cfg)|{'actual_dt':dt,'wall_seconds':time.monotonic()-start,'max_divergence':maxdiv,'max_CFL':maxcfl,'max_wall_leak_m_s':maxleak,'min_air_temperature_rise_K':min_temp,'max_water_mass_balance_error_kg':max_mass_error,'max_water_momentum_balance_error_N_s':max_water_momentum_error,'max_water_energy_balance_error_J':max_water_heat_error,'air_heat_J':air_heat,'air_heat_balance_error_J':air_heat-diag.get('gas_sensible_heat_J',0),'last_cloud_diagnostics':diag,'trace_columns':['t_s','mean_dp_Pa','min_dp_Pa','max_dp_Pa','max_air_speed_m_s','max_air_deltaT_K','mean_inside_deltaT_K','mean_outside_deltaT_K','parcels'],'model':'3D impermeable fixed baffle; explicit parcel drag/heat; free-slip insulating outer walls; no evaporation or bather','pressure_definition':'reduced pressure outside minus inside at adjacent cells sharing the blocked curtain face'}
    result={'trace':np.asarray(history),'pressure_yz':np.asarray(pressures),'temperature_yz':np.asarray(temperature),'velocity_yz':np.asarray(velocity),'pressure_xz':np.asarray(cross_pressure),'velocity_xz':np.asarray(cross_velocity),'pressure_load':np.asarray(loads),'viscous_load':np.asarray(viscous),'parcels':np.asarray(parts),'x':grid.axes[0],'y':grid.axes[1],'z':grid.axes[2],'load_z':grid.axes[2][iz],'final_u':u.astype('f4'),'final_p':p.astype('f4'),'final_theta':theta.astype('f4'),'metadata':np.array(json.dumps(meta))}
    if output:
        output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
        temporary=output.with_name(output.name+'.tmp')
        with temporary.open('wb') as handle:np.savez_compressed(handle,**result)
        temporary.replace(output)
        output.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
        output.with_name(output.stem+'_config.json').write_text(json.dumps(asdict(cfg),indent=2)+'\n')
    return result


def strip_response(data,sigma=.2,hem=.05,damping=.08,n=64,clearance=.15,include_viscous=False):
    """Each width strip receives the saved spatial/time pressure, not mean force.

    Stop each strip independently at first contact or |slope|=0.3; do not
    simulate a stuck sheet or extrapolate a small-slope model beyond its domain.
    """
    meta=json.loads(str(data['metadata']));H=meta['top']-meta['bottom']
    s,k,m,w=matrices(n,H,sigma,hem)
    time_axis=data['trace'][:,0];load=data['pressure_load'].copy();source_s=meta['top']-data['load_z'][::-1]
    if include_viscous:load=load+data['viscous_load']
    # Fixed physical probes remove a hidden change of sample position on refinement.
    widths=np.linspace(.15,meta['length'][1]-.15,9) if load.shape[1]>9 else data['y']
    results=[]
    for width in widths:
        if len(data['y'])==1:
            profile=load[:,0,:]
        else:
            j=int(np.clip(np.searchsorted(data['y'],width)-1,0,len(data['y'])-2))
            fraction=np.clip((width-data['y'][j])/(data['y'][j+1]-data['y'][j]),0,1)
            profile=(1-fraction)*load[:,j,:]+fraction*load[:,j+1,:]
        spatial=np.array([np.interp(s[1:],source_s,q[::-1]) for q in profile])
        def forcing(t):
            it=min(np.searchsorted(time_axis,t,side='right')-1,len(time_axis)-2);it=max(it,0)
            a=(t-time_axis[it])/(time_axis[it+1]-time_axis[it]);return (1-a)*spatial[it]+a*spatial[it+1]
        def rhs(t,state):return np.r_[state[n:],(forcing(t)*w-elastic(state[:n],k)-damping*w*state[n:])/m]
        def contact(t,state):return clearance-np.max(state[:n])
        def slope(t,state):return .3-np.max(abs(np.diff(np.r_[0,state[:n]]))/(H/n))
        contact.terminal=True;contact.direction=-1;slope.terminal=True;slope.direction=-1
        sol=solve_ivp(rhs,(0,time_axis[-1]),np.zeros(2*n),method='DOP853',rtol=2e-7,atol=2e-9,t_eval=time_axis,events=[contact,slope])
        if not sol.success:raise RuntimeError(sol.message)
        reason='end';event_time=None
        for name,te,ye in zip(['first_contact','small_slope_limit'],sol.t_events,sol.y_events):
            if len(te):
                reason=name;event_time=float(te[0]);sol.t=np.r_[sol.t,te[0]];sol.y=np.c_[sol.y,ye[0]]
        results.append({'width_y_m':float(width),'t':sol.t,'s':s,'y':np.c_[np.zeros(len(sol.t)),sol.y[:n].T],'reason':reason,'event_time':event_time})
    return results
