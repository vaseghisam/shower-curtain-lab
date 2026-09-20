"""Validate and assemble the complete publication repository."""
from pathlib import Path
import argparse,hashlib,json,re,zipfile,subprocess,sys
import xml.etree.ElementTree as ET
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'__pycache__','.render-tmp','.git','.venv','pilot'}


def included():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and not EXCLUDED.intersection(p.relative_to(ROOT).parts)
                  and not p.name.endswith(('.tmp','.lock','.pyc','.zip')))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT.parent/'shower-curtain-publication.zip')
    args=parser.parse_args()
    subprocess.run([sys.executable,'-m','curtainflow.validate_publication','--strict-assets',
                    '--require-tk','--json','docs/publication_preflight.json'],cwd=ROOT,check=True)
    files=included();archives=0;images=0;links=0
    for path in files:
        if path.suffix=='.npz':
            with zipfile.ZipFile(path) as archive:
                bad=archive.testzip()
                if bad:raise ValueError(f'Corrupt numerical archive: {path.name}: {bad}')
            archives+=1
        elif path.suffix=='.png':
            with Image.open(path) as im:im.verify()
            with Image.open(path) as im:im.load()
            images+=1
        elif path.suffix=='.svg':ET.parse(path)
        elif path.suffix=='.md':
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text()):
                if '://' in target or target.startswith(('#','mailto:')):continue
                target=target.split('#')[0]
                if target and not (path.parent/target).exists():raise ValueError(f'Broken local link in {path}: {target}')
                links+=1
    for name,entry in json.loads((ROOT/'render_manifest.json').read_text()).items():
        for source in entry.get('sources',[]):
            path=ROOT/'data'/source['file']
            if hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']:
                raise ValueError('Visual source changed: '+source['file'])
    status={'numerical_archives_CRC_checked':archives,'PNG_files_fully_decoded':images,
            'SVG_files_parsed':sum(p.suffix=='.svg' for p in files),'local_markdown_links_checked':links,
            'visual_source_hashes_match':True,'media_full_decode_audit':'docs/render_validation.json',
            'excluded':'superseded pilot outputs, caches and temporary files',
            'status':'passed before bundling'}
    (ROOT/'docs/delivery_validation.json').write_text(json.dumps(status,indent=2)+'\n')
    files=[p for p in included() if p.name!='FILES.sha256']
    (ROOT/'FILES.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}\n' for p in files))
    subprocess.run([sys.executable,'-m','curtainflow.validate_publication','--strict-assets',
                    '--require-tk','--check-inventory'],cwd=ROOT,check=True)
    files=included();temporary=args.output.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary,'w',allowZip64=True) as archive:
        for path in files:
            compressed=path.suffix in {'.npz','.png','.gif','.mp4'}
            archive.write(path,ROOT.name+'/'+path.relative_to(ROOT).as_posix(),compress_type=zipfile.ZIP_STORED if compressed else zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(temporary) as archive:
        bad=archive.testzip()
        if bad:raise ValueError('Corrupt delivery bundle: '+bad)
    temporary.replace(args.output)
    digest=hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix('.zip.sha256').write_text(digest+'  '+args.output.name+'\n')
    print(json.dumps(status|{'output':str(args.output),'files':len(files),'bytes':args.output.stat().st_size,'sha256':digest,'largest_member_bytes':max(p.stat().st_size for p in files)},indent=2))

if __name__=='__main__':main()
