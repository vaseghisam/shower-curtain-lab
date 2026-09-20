"""Named, inspectable experimental-design configurations; no fitted targets."""
from dataclasses import replace,asdict
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import argparse,json
from .simulation import Config,run

ROOT=Path(__file__).resolve().parents[1]

def design():
    base=Config(duration=12.)
    cases={
        'control_off':replace(base,momentum=False,heat=False),
        'control_spray':base,
        'control_heat':replace(base,momentum=False,heat=True),
        'control_both':replace(base,heat=True),
    }
    for kind in ('spray','heat','both'):
        c=cases['control_'+kind]
        cases['grid_medium_'+kind]=replace(c,shape=(36,48,48))
        cases['grid_fine_'+kind]=replace(c,shape=(48,64,64),dt=.002)
    cases['time_half_spray']=replace(base,dt=.002)
    cases['time_half_both']=replace(base,heat=True,dt=.002)
    cases['rays_double_spray']=replace(base,rays=24)
    cases['rays_double_both']=replace(base,heat=True,rays=24)
    for name,changes in {
        'flow_low':{'flow_lpm':5.},'flow_high':{'flow_lpm':10.},
        'diameter_small':{'diameter_mm':.5},'diameter_large':{'diameter_mm':1.5},
        'speed_low':{'speed':.5},'speed_high':{'speed':3.},
        'tilt_vertical':{'tilt_deg':0.},'tilt_high':{'tilt_deg':35.},
        'mixing_low':{'nu':.001515,'alpha':.002164},
        'mixing_high':{'nu':.006015,'alpha':.008593},
    }.items():cases[name]=replace(base,**changes)
    cases['water_35C']=replace(base,heat=True,water_delta_T=13.)
    cases['water_41C']=replace(base,heat=True,water_delta_T=19.)
    return cases

def one(item):
    name,cfg=item
    r=run(cfg,ROOT/'data'/(name+'.npz'),quiet=True)
    return name,r['trace'][-1].tolist()

def main():
    p=argparse.ArgumentParser();p.add_argument('--cases',nargs='+');p.add_argument('--workers',type=int,default=3);p.add_argument('--write-design',action='store_true');a=p.parse_args()
    allcases=design()
    if a.write_design:
        (ROOT/'docs/experiment_design.json').write_text(json.dumps({k:asdict(v) for k,v in allcases.items()},indent=2)+'\n')
        return
    selected=[(k,allcases[k]) for k in (a.cases or list(allcases))]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for name,result in pool.map(one,selected):print(name,result,flush=True)

if __name__=='__main__':main()
