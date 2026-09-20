"""A separate mechanics experiment under calculated, time-averaged air loads.

The release clock is NOT shower startup time. No new airflow is simulated here.
The computed full spatial mean pressure is held constant without rescaling.
"""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
from .averaging import mean_over_window
from .simulation import strip_response
from .mechanics import equilibrium
from .analyze import atomic_npz,static_response

ROOT=Path(__file__).resolve().parents[1]


def release(path,damping=.08,suffix=''):
    with np.load(path,allow_pickle=False) as archive:
        original={k:archive[k] for k in ['trace','pressure_load','load_z','y','metadata']}
    load=mean_over_window(original['trace'][:,0],original['pressure_load'])
    tau=np.linspace(0.,6.,301)
    prescribed=original.copy()
    prescribed['trace']=tau[:,None]
    prescribed['pressure_load']=np.broadcast_to(load,(len(tau),)+load.shape)
    response=strip_response(prescribed,damping=damping)
    config=json.loads(str(original['metadata']))
    out={'width_y_m':np.array([r['width_y_m'] for r in response]),
         'reason':np.array([r['reason'] for r in response]),
         'event_time':np.array([r['event_time'] if r['event_time'] is not None else np.nan for r in response]),
         'computed_mean_pressure':load,'load_z':original['load_z'],'source_width_y':original['y']}
    peaks=[]
    for i,r in enumerate(response):
        for key in ['t','s','y']:out[f'{key}_{i}']=r[key]
        q=np.array([np.interp(r['width_y_m'],original['y'],row) for row in load.T])
        s,y=equilibrium(lambda a:np.interp(a,config['top']-original['load_z'][::-1],q[::-1]),n=256,H=config['top']-config['bottom'],sigma=.2,hem=.05)
        out[f'static_s_{i}']=s;out[f'static_y_{i}']=y
        peaks.append(float(r['y'].max()))
    chosen=int(np.argmax(peaks))
    metadata={'source':path.name,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'airflow_window_s':[10.,12.],'time_definition':'seconds since release under computed mean load',
              'load_definition':'trapezoidal time integral of saved pressure, held constant; no rescaling',
              'status':'separate prescribed-load mechanics experiment; no evolving airflow or geometry feedback',
              'sigma_kg_m2':.2,'hem_kg_m':.05,'damping_kg_m2_s':damping,'clearance_m':.15,
              'max_slope':.3,'selected_probe_index':chosen,'positive_displacement':'inward',
              'all_probe_peaks_m':peaks,'maximum_sampled_excursion_m':max(peaks)}
    out['metadata']=np.array(json.dumps(metadata))
    atomic_npz(path.with_name('release_'+path.stem+suffix+'.npz'),**out)
    return metadata


def refresh_static():
    """Refresh cheap static metrics after the uniform averaging definition."""
    path=ROOT/'data/results_summary.json';summary=json.loads(path.read_text())
    for name,entry in summary.items():
        static_path=ROOT/'data'/('static_'+name+'.npz')
        if not static_path.exists():continue
        with np.load(static_path) as archive:meta=json.loads(str(archive['metadata']))
        with np.load(ROOT/'data'/meta['source']) as data:
            correction=name.endswith('_normal_stress')
            result=static_response(data,meta['sigma'],meta['hem'],correction)
            t=data['trace'][:,0]
            entry['mean_pressure_Pa']=float(mean_over_window(t,data['pressure_load'],t[-1]-2,t[-1]).mean())
        entry.update(static_max_displacement_m=result['max_m'],static_mean_hem_m=result['mean_hem_m'],static_max_slope=result['max_slope'])
        meta['load_window']='last 2 s; trapezoidal time integral'
        atomic_npz(static_path,s=result['s'],y=result['y'],width_y_m=result['width_y_m'],metadata=np.array(json.dumps(meta)))
    temporary=path.with_suffix('.json.tmp');temporary.write_text(json.dumps(summary,indent=2)+'\n');temporary.replace(path)


def main():
    p=argparse.ArgumentParser();p.add_argument('--cases',nargs='+');p.add_argument('--refresh-static',action='store_true');p.add_argument('--damping-screen',action='store_true');a=p.parse_args()
    if a.refresh_static:refresh_static()
    if a.damping_screen:
        result={f'{kind}_{label}':release(ROOT/'data'/f'grid_fine_{kind}.npz',damping=c,suffix='_damping_'+label) for kind in ['spray','heat','both'] for label,c in [('half',.04),('double',.16)]}
        (ROOT/'data/damping_summary.json').write_text(json.dumps(result,indent=2)+'\n')
        for name,meta in result.items():print(name,meta['maximum_sampled_excursion_m'],flush=True)
        return
    names=a.cases or [f'grid_{resolution}_{kind}' for resolution in ['medium','fine'] for kind in ['spray','heat','both']]
    result={name:release(ROOT/'data'/(name+'.npz')) for name in names}
    (ROOT/'data/release_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    for name,meta in result.items():print(name,meta['maximum_sampled_excursion_m'],flush=True)

if __name__=='__main__':main()
