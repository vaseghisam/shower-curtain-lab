"""Local publication checks; not an actual TK import or experimental validation."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image, ImageSequence
from scipy.integrate import cumulative_trapezoid
from .export_article import tk_text

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / 'article/why-a-shower-curtain-attacks-you.md'
TK = ROOT / 'why-a-shower-curtain-attacks-you-tk.md'
EXCLUDED = {'__pycache__', '.render-tmp', '.git', 'pilot', '.venv'}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def normalize_article(text):
    return tk_text(text)


class Audit:
    def __init__(self):
        self.failures = []
        self.checks = {}

    def require(self, condition, message):
        if not condition:
            self.failures.append(message)

    def run(self, name, fn):
        try:
            self.checks[name] = fn()
        except Exception as exc:
            self.failures.append(f'{name}: {type(exc).__name__}: {exc}')


def check_math(text):
    displays = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if '$$' in line:
            if not re.fullmatch(r'\s*\$\$.+\$\$\s*', line) or line.count('$$') != 2:
                raise ValueError(f'display equation must occupy one physical line: {line_number}')
            displays.append(line.strip()[2:-2])
    rest = re.sub(r'\$\$.*?\$\$', '', text)
    if len(re.findall(r'(?<!\\)\$', rest)) % 2:
        raise ValueError('unbalanced inline dollar delimiters')
    inline = re.findall(r'(?<!\\)\$(.*?)(?<!\\)\$', rest, flags=re.S)
    for expression in displays + inline:
        if '\n\n' in expression:
            raise ValueError('math span crosses a paragraph')
        depth = 0
        for token in re.findall(r'(?<!\\)[{}]', expression):
            depth += 1 if token == '{' else -1
            if depth < 0:
                raise ValueError('closing brace precedes opening brace in math')
        if depth:
            raise ValueError('unbalanced math braces')
        if len(re.findall(r'\\left\b', expression)) != len(re.findall(r'\\right\b', expression)):
            raise ValueError('unbalanced left/right math delimiters')
    return {'display_equations': len(displays), 'inline_equations': len(inline)}


def check_article(audit, require_tk):
    text = CANONICAL.read_text()
    audit.require(not re.search(r'\[FIRE\]|#HERE|\b(?:FIGURE|ANIMATION|RESULTS|SIMULATION)\s+PLACEHOLDER\b', text), 'editorial marker or placeholder remains')
    audit.require('```' not in text, 'code fences remain in the article')
    audit.require(not re.search(r'</?[A-Za-z][^>]*>', text), 'raw HTML remains in the article')
    math = check_math(text)
    parts = re.split(r'(?m)^(?:#{1,6}\s+References|\*\*References\*\*)\s*$', text, maxsplit=1)
    if len(parts) != 2:
        raise ValueError('one References section is required')
    body, references = parts
    ref_numbers = [int(n) for n in re.findall(r'(?m)^\s*(\d+)\.\s+', references)]
    expected = list(range(1, len(ref_numbers) + 1))
    audit.require(ref_numbers == expected and len(expected) >= 1, 'references are not a consecutive numbered list')
    groups = re.findall(r'\[(\d+(?:\s*,\s*\d+)*)\](?!\()', body)
    citations = [int(n) for group in groups for n in group.split(',')]
    first = list(dict.fromkeys(citations))
    audit.require(first == expected, f'citation/reference first-appearance mismatch: {first} vs {expected}')
    images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', text)
    audit.require(len(images) == 10, f'expected 10 article media links, found {len(images)}')
    for name, target in images:
        audit.require(not re.match(r'\w+://', target), f'article asset must be bundled locally: {target}')
        path = (CANONICAL.parent / target).resolve()
        audit.require(path.is_file() and path.stat().st_size > 0, f'missing/empty article media: {target}')
        audit.require(path.is_relative_to(ROOT), f'article media leaves package: {target}')
    for category in ('Figure', 'Animation'):
        nums = []
        for line in body.splitlines():
            match = re.match(r'^\s*(?:\*{1,2})?' + category + r'\s+(\d+)[.\s:]', line)
            if match:
                nums.append(int(match.group(1)))
        audit.require(nums == [1, 2, 3, 4, 5], f'{category} caption sequence is {nums}, expected 1-5')
    if require_tk or TK.exists():
        tk = TK.read_text()
        audit.require(tk == normalize_article(text), 'TK file differs from normalized canonical article')
        check_math(tk)
    return math | {'references': len(ref_numbers), 'citation_first_appearance': first, 'article_media_links': len(images), 'canonical_sha256': digest(CANONICAL), 'tk_sha256': digest(TK) if TK.exists() else None}


def source_path(file, manifest, legacy=False):
    p = Path(file)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError(f'unsafe manifest path: {file}')
    if len(p.parts) > 1:
        return ROOT / p
    return (ROOT / 'data' / p) if legacy else (manifest.parent / p)


def check_manifest(audit, strict_assets):
    manifest = ROOT / 'assets/publication_manifest.json'
    if not manifest.exists():
        if strict_assets:
            raise ValueError('publication asset manifest does not exist')
        return {'status': 'not required yet'}
    obj = json.loads(manifest.read_text())
    count = 0
    files = []
    def walk(node, group=None):
        nonlocal count
        if isinstance(node, dict):
            if 'file' in node and 'sha256' in node:
                file = source_path(node['file'], manifest, legacy=group == 'sources')
                audit.require(file.is_file(), f'manifest file missing: {node["file"]}')
                if file.is_file():
                    audit.require(digest(file) == node['sha256'], f'manifest hash mismatch: {node["file"]}')
                    count += 1
                    if group == 'files':
                        files.append(file)
            for key, value in node.items():
                if key not in ('file', 'sha256'):
                    walk(value, key if key in ('sources', 'files') else group)
        elif isinstance(node, list):
            for value in node:
                walk(value, group)
    walk(obj)
    audit.require(count > 0, 'publication manifest contains no hashed files')
    provenance = ROOT / 'assets/generation_source.json'
    if provenance.exists():
        proof = json.loads(provenance.read_text())
        walk(proof, 'sources')
        audit.require(proof.get('manifest_sha256') == digest(manifest), 'media verification refers to an older publication manifest')
        audit.require(proof.get('verified_media_files') == len(set(files)), 'media verification count does not match manifest outputs')
    elif strict_assets:
        audit.require(False, 'publication media verification/provenance report missing')
    if strict_assets:
        expected = {'figure_01_geometry', 'figure_02_prescribed_strip', 'figure_03_pressure_to_strip', 'figure_04_mass_response', 'figure_05_parameter_study', 'animation_01_droplet', 'animation_02_vortex', 'animation_03_thermal', 'animation_04_airflow', 'animation_05_mean_load_release'}
        audit.require(set(obj) == expected, 'publication manifest is not the complete set of five figures and five animations')
        for target in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', CANONICAL.read_text()):
            audit.require((CANONICAL.parent/target).resolve() in {p.resolve() for p in files}, f'article media absent from hashed manifest: {target}')
    legacy = ROOT / 'render_manifest.json'
    legacy_count = 0
    if legacy.exists():
        for entry in json.loads(legacy.read_text()).values():
            for item in entry.get('sources', []):
                p = source_path(item['file'], legacy, legacy=True)
                audit.require(digest(p) == item['sha256'], f'phase1 visual source changed: {item["file"]}')
                legacy_count += 1
    return {'publication_hashes_checked': count, 'phase1_source_hashes_checked': legacy_count, 'publication_output_files': len(set(files))}


def check_media(audit, strict_assets):
    if not strict_assets:
        return {'status': 'not requested'}
    stats = {'PNG_files_fully_decoded': 0, 'SVG_files_parsed': 0, 'GIF_frames_fully_decoded': {}, 'MP4_streams_probed': {}}
    for path in sorted((ROOT / 'assets').glob('*')):
        suffix = path.suffix.lower()
        if suffix == '.png':
            with Image.open(path) as im:
                im.load()
            stats['PNG_files_fully_decoded'] += 1
        elif suffix == '.svg':
            ET.parse(path)
            stats['SVG_files_parsed'] += 1
        elif suffix == '.gif':
            frames = 0
            with Image.open(path) as im:
                for frame in ImageSequence.Iterator(im):
                    frame.load()
                    frames += 1
            audit.require(frames > 1, f'GIF has no animation: {path.name}')
            stats['GIF_frames_fully_decoded'][path.name] = frames
        elif suffix == '.mp4':
            result = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,nb_frames,duration', '-of', 'json', str(path)], check=True, capture_output=True, text=True)
            streams = json.loads(result.stdout)['streams']
            audit.require(bool(streams) and int(streams[0].get('nb_frames', 0)) > 1, f'MP4 missing frames: {path.name}')
            stats['MP4_streams_probed'][path.name] = streams[0] if streams else {}
    audit.require(len(stats['GIF_frames_fully_decoded']) == 5, 'expected five publication GIFs')
    audit.require(len(stats['MP4_streams_probed']) == 5, 'expected five publication MP4s')
    return stats


def check_numbers(audit):
    result = {}
    article_text = CANONICAL.read_text()
    material = json.loads((ROOT / 'data/material_summary.json').read_text())
    summary = json.loads((ROOT / 'data/results_summary.json').read_text())
    release_summary = json.loads((ROOT / 'data/release_summary.json').read_text())
    for kind in ('spray', 'heat', 'both'):
        name = 'grid_fine_' + kind
        source = ROOT / 'data' / (name + '.npz')
        with np.load(source, allow_pickle=False) as data:
            t = data['trace'][:, 0]
            mask = (t >= 10 - 1e-8) & (t <= 12 + 1e-8)
            tt = t[mask]
            q = data['pressure_load'][mask].astype(float)
            mean = np.sum((q[1:] + q[:-1]) * .5 * np.diff(tt)[:, None, None], axis=0) / (tt[-1] - tt[0])
            meta = json.loads(str(data['metadata']))
            s_source = meta['top'] - data['load_z'][::-1]
            H = meta['top'] - meta['bottom']
            s = np.linspace(0, H, 8193)
            profiles = np.array([np.interp(s, s_source, row[::-1]) for row in mean])
            load_from_top = cumulative_trapezoid(profiles, s, axis=1, initial=0)
            below = load_from_top[:, -1, None] - load_from_top
            baseline = cumulative_trapezoid(below / (9.81 * (.2 * (H-s) + .05)), s, axis=1, initial=0)
        entry = summary[name]
        np.testing.assert_allclose(mean.mean(), entry['mean_pressure_Pa'], rtol=1e-8, atol=1e-10)
        with np.load(ROOT / 'data' / ('static_' + name + '.npz'), allow_pickle=False) as static:
            np.testing.assert_allclose(static['y'][:, -1].mean(), entry['static_mean_hem_m'], rtol=1e-10, atol=1e-12)
            # An independent continuous integral is compared with the saved 256-element
            # lumped-load discretization, allowing its small quadrature error.
            np.testing.assert_allclose(baseline[:, -1], static['y'][:, -1], rtol=1e-3, atol=1e-6)
            quadrature_error = float(np.max(np.abs(baseline[:, -1] - static['y'][:, -1])))
        with np.load(ROOT / 'data' / ('release_' + name + '.npz'), allow_pickle=False) as release:
            metadata = json.loads(str(release['metadata']))
            np.testing.assert_allclose(release['computed_mean_pressure'], mean, rtol=1e-8, atol=1e-10)
            audit.require(metadata['source_sha256'] == digest(source), f'release source hash mismatch: {name}')
            peaks = [float(release[f'y_{i}'].max()) for i in range(len(release['width_y_m']))]
            audit.require(int(np.argmax(peaks)) == metadata['selected_probe_index'], f'incorrect release probe: {name}')
            np.testing.assert_allclose(peaks, metadata['all_probe_peaks_m'], rtol=1e-12, atol=1e-12)
            np.testing.assert_allclose(max(peaks), release_summary[name]['maximum_sampled_excursion_m'], rtol=1e-12, atol=1e-12)
            audit.require(metadata['airflow_window_s'] == [10., 12.], f'wrong release averaging window: {name}')
        label = {'spray': 'Spray momentum', 'heat': 'Sensible heating', 'both': 'Both together'}[kind]
        rows = [line for line in article_text.splitlines() if re.match(r'\|\s*' + label + r'\s*\|', line)]
        audit.require(len(rows) == 1, f'missing or duplicate baseline result row: {label}')
        if rows:
            audit.require(f'{mean.mean():.4f} Pa' in rows[0] and f'{100*entry["static_mean_hem_m"]:.2f} cm' in rows[0], f'article table differs from saved results: {label}')
        audit.require(f'{100*max(peaks):.2f} cm' in article_text, f'article release peak missing or changed: {kind}')
        result[kind] = {'mean_pressure_Pa': float(mean.mean()), 'mean_static_hem_cm': 100 * entry['static_mean_hem_m'], 'maximum_sampled_mean_load_release_cm': 100 * max(peaks), 'independent_quadrature_max_hem_error_m': quadrature_error}
    for i, label in enumerate(('0.10 kg/m²; no added hem mass', '0.20 kg/m²; no added hem mass', '0.20 kg/m²; 0.05 kg/m hem', '0.20 kg/m²; 0.10 kg/m hem')):
        rows = [line for line in article_text.splitlines() if line.startswith('| '+label+' |')]
        audit.require(len(rows) == 1, f'missing or duplicate material row: {label}')
        if rows:
            observed = re.findall(r'([0-9]+\.[0-9]+) cm', rows[0])
            expected = [f'{100*material[kind][i]["mean_hem_m"]:.2f}' for kind in ('spray', 'heat', 'both')]
            audit.require(observed == expected, f'article material table differs from saved results: {label}')
    q, H, sigma, hem = .2, 1.8, .2, .1
    result['analytic_uniform_example'] = {'unweighted_m': q*H/(sigma*9.81), 'weighted_m': q/(sigma*9.81)*(H-hem/sigma*np.log1p(sigma*H/hem))}
    return result


def inventory_files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and not EXCLUDED.intersection(p.relative_to(ROOT).parts) and not p.name.endswith(('.tmp', '.lock', '.pyc', '.zip')) and p.name != 'FILES.sha256')


def check_inventory(audit):
    entries = {}
    for line in (ROOT / 'FILES.sha256').read_text().splitlines():
        sha, rel = line.split('  ', 1)
        audit.require(rel not in entries, f'duplicate inventory entry: {rel}')
        path = ROOT / rel
        audit.require(path.resolve().is_relative_to(ROOT), f'inventory path leaves package: {rel}')
        entries[rel] = sha
        audit.require(path.is_file() and digest(path) == sha, f'inventory hash mismatch: {rel}')
    actual = {p.relative_to(ROOT).as_posix() for p in inventory_files()}
    audit.require(actual == set(entries), f'inventory coverage mismatch: missing={sorted(actual-set(entries))}, extra={sorted(set(entries)-actual)}')
    return {'files_hashed': len(entries), 'coverage_complete': actual == set(entries)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strict-assets', action='store_true')
    parser.add_argument('--require-tk', action='store_true')
    parser.add_argument('--check-inventory', action='store_true')
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    audit = Audit()
    audit.run('article', lambda: check_article(audit, args.require_tk))
    audit.run('source_and_output_hashes', lambda: check_manifest(audit, args.strict_assets))
    audit.run('media', lambda: check_media(audit, args.strict_assets))
    audit.run('independent_numeric_consistency', lambda: check_numbers(audit))
    if args.check_inventory:
        audit.run('inventory', lambda: check_inventory(audit))
    report = {'status': 'passed' if not audit.failures else 'failed', 'checks': audit.checks, 'failures': audit.failures, 'scope': 'Local syntax and saved-data/integrity checks; no actual TK import, full CFD rerun, or experimental validation.'}
    rendered = json.dumps(report, indent=2) + '\n'
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered)
    print(rendered, end='')
    return 0 if not audit.failures else 1


if __name__ == '__main__':
    sys.exit(main())
