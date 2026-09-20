"""Reproduce saved configurations, analysis, scientific media, or numerical QA."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import argparse,json,subprocess,sys
from .simulation import Config,run

ROOT=Path(__file__).resolve().parents[1]


def flow_case(name):
    path=ROOT/'data'/f'{name}_config.json'
    cfg=Config(**json.loads(path.read_text()))
    run(cfg,ROOT/'data'/f'{name}.npz',quiet=True)
    return name


def call(*args):
    subprocess.run([sys.executable,*args],cwd=ROOT,check=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',required=True,choices=['flow','analysis','figures','qa'])
    p.add_argument('--cases',nargs='+')
    p.add_argument('--workers',type=int,default=2)
    a=p.parse_args()
    names=a.cases or sorted(path.name.removesuffix('_config.json') for path in (ROOT/'data').glob('*_config.json'))
    if a.stage=='flow':
        with ProcessPoolExecutor(max_workers=a.workers) as pool:
            for name in pool.map(flow_case,names):print('Completed',name,flush=True)
    elif a.stage=='analysis':
        call('-m','curtainflow.analyze','--cases',*names,'--materials')
        call('-m','curtainflow.release','--refresh-static')
        call('-m','curtainflow.release','--damping-screen')
        call('-m','curtainflow.review_charts')
    elif a.stage=='figures':
        call('-m','curtainflow.publication_visuals','--only','all')
    else:
        call('-m','unittest','discover','-s','tests','-v')
        call('-m','tests.qa_response_checks')

if __name__=='__main__':main()
