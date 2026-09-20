"""Apply saved air loads to the article's hanging-strip equations."""
from pathlib import Path
import argparse,json
import numpy as np
from .simulation import strip_response
from .mechanics import equilibrium
from .averaging import mean_over_window

ROOT=Path(__file__).resolve().parents[1]

def metric(data,structures):
    time=data['trace'][:,0];late=time>=time[-1]-2.-1e-7
    p=data['pressure_load'][late];v=data['viscous_load'][late]
    peaks=[float(r['y'].max()) for r in structures]
    return {
        'end_time_s':float(time[-1]),'late_window_s':[float(time[late][0]),float(time[-1])],
        'mean_pressure_Pa':float(mean_over_window(time,data['pressure_load'],time[-1]-2.,time[-1]).mean()),'rms_pressure_Pa':float(np.sqrt(np.mean(p*p))),
        'mean_viscous_correction_Pa':float(v.mean()),
        'rms_viscous_to_pressure':float(np.sqrt(np.mean(v*v)/np.mean(p*p))) if np.any(p) else 0.,
        'inward_area_time_fraction':float(np.mean(p>0)),
        'peak_sampled_strip_displacement_m':max(peaks),
        'last_sampled_strip_displacement_m':max(float(r['y'][-1].max()) for r in structures),
        'earliest_contact_s':min((r['event_time'] for r in structures if r['reason']=='first_contact'),default=None),
        'slope_limit_reached':any(r['reason']=='small_slope_limit' for r in structures),
        'strip_widths_m':[r['width_y_m'] for r in structures],
        'strip_peak_displacements_m':peaks,
    }

def static_response(data,sigma=.2,hem=.05,include_viscous=False):
    meta=json.loads(str(data['metadata']));H=meta['top']-meta['bottom']
    time=data['trace'][:,0];late=time>=time[-1]-2.-1e-7
    q=mean_over_window(time,data['pressure_load'],time[-1]-2.,time[-1])
    if include_viscous:q=q+mean_over_window(time,data['viscous_load'],time[-1]-2.,time[-1])
    source_s=meta['top']-data['load_z'][::-1]
    profiles=[]
    for row in q:
        s,y=equilibrium(lambda a:np.interp(a,source_s,row[::-1]),n=256,H=H,sigma=sigma,hem=hem)
        profiles.append(y)
    y=np.array(profiles)
    return {'s':s,'y':y,'width_y_m':data['y'],'max_m':float(y.max()),'mean_hem_m':float(y[:,-1].mean()),'max_slope':float(np.max(abs(np.diff(y,axis=1)))/(H/256))}

def save_structures(path,results,**meta):
    out={'width_y_m':np.array([r['width_y_m'] for r in results]),
         'reason':np.array([r['reason'] for r in results]),
         'event_time':np.array([r['event_time'] if r['event_time'] is not None else np.nan for r in results]),
         'metadata':np.array(json.dumps(meta))}
    for i,r in enumerate(results):
        for key in ['t','s','y']:out[key+'_'+str(i)]=r[key]
    atomic_npz(path,**out)

def atomic_npz(path,**data):
    path=Path(path);temporary=path.with_suffix('.npz.tmp')
    with temporary.open('wb') as f:np.savez_compressed(f,**data)
    temporary.replace(path)

def one(path,variant='baseline',**options):
    with np.load(path,allow_pickle=False) as data:
        results=strip_response(data,**options)
        summary=metric(data,results)
        static=static_response(data,sigma=options.get('sigma',.2),hem=options.get('hem',.05),include_viscous=options.get('include_viscous',False))
        summary.update(static_max_displacement_m=static['max_m'],static_mean_hem_m=static['mean_hem_m'],static_max_slope=static['max_slope'])
    suffix='' if variant=='baseline' else '_'+variant
    atomic_npz(ROOT/'data'/('static_'+path.stem+suffix+'.npz'),s=static['s'],y=static['y'],width_y_m=static['width_y_m'],metadata=np.array(json.dumps({'source':path.name,'load_window':'last 2 s; trapezoidal time integral','sigma':options.get('sigma',.2),'hem':options.get('hem',.05),'status':'static response to averaged fixed-boundary load'})))
    save_structures(ROOT/'data'/('structural_'+path.stem+suffix+'.npz'),results,
                    source=path.name,sigma=options.get('sigma',.2),hem=options.get('hem',.05),damping=options.get('damping',.08),
                    clearance=options.get('clearance',.15),max_slope=.3,include_viscous=options.get('include_viscous',False),
                    status='one-way pressure response; airflow boundary remained fixed')
    return summary

def main():
    p=argparse.ArgumentParser();p.add_argument('--cases',nargs='+');p.add_argument('--materials',action='store_true');a=p.parse_args()
    prior=ROOT/'data/results_summary.json'
    summary=json.loads(prior.read_text()) if prior.exists() else {}
    paths=[ROOT/'data'/(n+'.npz') for n in a.cases] if a.cases else sorted(p for p in (ROOT/'data').glob('*.npz') if not p.name.startswith(('structural_','static_','release_')))
    for path in paths:
        if not path.exists():continue
        summary[path.stem]=one(path)
        print(path.stem,summary[path.stem]['mean_pressure_Pa'],summary[path.stem]['peak_sampled_strip_displacement_m'],flush=True)
        if a.materials and path.stem in ['control_spray','control_heat','control_both']:
            for name,kwargs in [('unweighted',{'hem':0}),('weighted',{'hem':.1}),('light',{'hem':0,'sigma':.1}),('heavy',{'sigma':.3}),('normal_stress',{'include_viscous':True})]:
                summary[path.stem+'_'+name]=one(path,variant=name,**kwargs)
        prior.write_text(json.dumps(summary,indent=2)+'\n')
    prior.write_text(json.dumps(summary,indent=2)+'\n')

if __name__=='__main__':main()
