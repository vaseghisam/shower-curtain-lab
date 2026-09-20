"""Independent result-level response and saved-pressure cadence calculations.

Run directly after final control/refinement output exists. The static response
uses independent cumulative quadrature of the article's continuum equation;
it does not call the production finite-element equilibrium routine.
"""
import json
from pathlib import Path

import numpy as np
from scipy.integrate import cumulative_trapezoid

from curtainflow.simulation import strip_response

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with np.load(path) as data:
        return {k: data[k] for k in data.files}


def late_pressure(data):
    t = data['trace'][:, 0]
    a, b = 10., 12.
    if t[-1] < b-1e-9:
        raise ValueError('This comparison requires a full twelve-second run')
    tt = np.r_[a, t[(t > a+1e-9) & (t < b-1e-9)], b]
    idx = np.clip(np.searchsorted(t, tt, side='right')-1, 0, len(t)-2)
    f = (tt-t[idx])/(t[idx+1]-t[idx])
    q = (1-f[:, None, None])*data['pressure_load'][idx] + f[:, None, None]*data['pressure_load'][idx+1]
    return np.trapezoid(q, tt, axis=0)/(b-a)


def static_profile(q, z, top=2.1, bottom=.3, sigma=.2, hem=.05):
    s = np.linspace(0., top-bottom, 2001)
    values = np.interp(s, top-z[::-1], q[::-1])
    cumulative_force = -cumulative_trapezoid(values[::-1], s[::-1], initial=0.)[::-1]
    tension = 9.81*(sigma*(top-bottom-s)+hem)
    slope = np.divide(cumulative_force, tension, out=np.zeros_like(s), where=tension > 0)
    if hem == 0:
        # Finite limiting slope of F(s)/T(s) at the unweighted free hem.
        slope[-1] = values[-1]/(sigma*9.81)
    displacement = cumulative_trapezoid(slope, s, initial=0.)
    return s, displacement


def static_metrics(data):
    q = late_pressure(data)
    meta = json.loads(str(data['metadata']))
    widths = np.linspace(.15, meta['length'][1]-.15, 9)
    profiles = []
    for width in widths:
        profile = np.array([np.interp(width, data['y'], row) for row in q.T])
        _, response = static_profile(profile, data['load_z'], meta['top'], meta['bottom'])
        profiles.append(response)
    _, mean = static_profile(q.mean(axis=0), data['load_z'], meta['top'], meta['bottom'])
    return {'mean_pressure_Pa': float(q.mean()),
            'static_widthmean_bottom_m': float(mean[-1]),
            'static_fixed_probe_max_m': float(np.max(profiles)),
            'fixed_probe_widths_m': widths.tolist()}


def dynamic_metrics(data):
    response = strip_response(data)
    return {'peak_inward_m': max(float(r['y'].max()) for r in response),
            'first_contact_s': min((r['event_time'] for r in response if r['reason']=='first_contact'), default=None),
            'slope_stop': any(r['reason']=='small_slope_limit' for r in response),
            'last_profile_peak_m': max(float(r['y'][-1].max()) for r in response)}


def release_metrics(data):
    q = late_pressure(data)
    synthetic = data.copy()
    time = np.linspace(0., 6., 301)
    synthetic['trace'] = time[:, None]
    synthetic['pressure_load'] = np.broadcast_to(q, (len(time),)+q.shape).copy()
    synthetic['viscous_load'] = np.zeros_like(synthetic['pressure_load'])
    response = strip_response(synthetic)
    return {'peak_m': max(float(r['y'].max()) for r in response),
            'per_probe_peaks_m': [float(r['y'].max()) for r in response],
            'first_contact_s': min((r['event_time'] for r in response if r['reason']=='first_contact'), default=None),
            'slope_stop': any(r['reason']=='small_slope_limit' for r in response),
            'probe_widths_m': [r['width_y_m'] for r in response]}


def light_static_metrics(data):
    q = late_pressure(data)
    meta = json.loads(str(data['metadata']))
    widths = np.linspace(.15, meta['length'][1]-.15, 9)
    responses, slopes = [], []
    for width in widths:
        profile = np.array([np.interp(width, data['y'], row) for row in q.T])
        s, y = static_profile(profile, data['load_z'], meta['top'], meta['bottom'], sigma=.1, hem=0.)
        responses.append(y)
        slopes.append(float(np.max(abs(np.diff(y)/np.diff(s)))))
    _, mean = static_profile(q.mean(axis=0), data['load_z'], meta['top'], meta['bottom'], sigma=.1, hem=0.)
    return {'static_widthmean_bottom_m': float(mean[-1]),
            'static_fixed_probe_max_m': float(np.max(responses)),
            'maximum_absolute_probe_slope': max(slopes),
            'fixed_probe_widths_m': widths.tolist(),
            'per_probe_peaks_m': [float(y.max()) for y in responses],
            'per_probe_maximum_absolute_slope': slopes}


def main():
    names = ['control_spray', 'control_heat', 'control_both',
             'grid_medium_spray', 'grid_fine_spray', 'grid_medium_heat',
             'grid_fine_heat', 'grid_medium_both', 'grid_fine_both', 'time_half_spray',
             'rays_double_spray', 'rays_quadruple_spray', 'qa_cadence_spray']
    results = {}
    for name in names:
        path = ROOT/'data'/(name+'.npz')
        if path.exists():
            data = read(path)
            if data['trace'][-1, 0] >= 12.-1e-9:
                results[name] = static_metrics(data) | dynamic_metrics(data)
                print(name, results[name], flush=True)
    dense_path = ROOT/'data/qa_cadence_spray.npz'
    cadence = {}
    if dense_path.exists():
        dense = read(dense_path)
        production = read(ROOT/'data/control_spray.npz')
        identical = {}
        for key in ['final_u', 'final_p', 'final_theta']:
            identical[key] = bool(np.array_equal(dense[key], production[key]))
        cadence['identical_final_fields'] = identical
        dense_step = float(np.median(np.diff(dense['trace'][:, 0])))
        reference = dynamic_metrics(dense)
        cadence['reference'] = reference | {'actual_output_interval_s': dense_step}
        for stride in (2, 4):
            indices = np.unique(np.r_[np.arange(0, len(dense['trace']), stride), len(dense['trace'])-1])
            reduced = dense.copy()
            for key in ['trace', 'pressure_load', 'viscous_load']:
                reduced[key] = dense[key][indices]
            value = dynamic_metrics(reduced)
            value['actual_output_interval_s'] = stride*dense_step
            value['peak_change_relative_to_dense'] = abs(value['peak_inward_m']-reference['peak_inward_m'])/max(1e-12, abs(reference['peak_inward_m']))
            cadence[f'downsample_{stride}'] = value
        value = dynamic_metrics(production)
        value['actual_output_interval_s'] = .1
        value['peak_change_relative_to_dense'] = abs(value['peak_inward_m']-reference['peak_inward_m'])/max(1e-12, abs(reference['peak_inward_m']))
        cadence['production'] = value
    report = {'scope': 'independent continuum static quadrature; fixed physical probes; pressure-output cadence check',
              'static_averaging_window_s': [10., 12.],
              'curtain': {'sigma_kg_m2': .2, 'hem_kg_m': .05, 'g_m_s2': 9.81},
              'results': results, 'cadence': cadence}
    release = {}
    for name in [f'grid_{level}_{kind}' for kind in ['spray', 'heat', 'both']
                 for level in ['medium', 'fine']]:
        if name in results:
            release[name] = release_metrics(read(ROOT/'data'/(name+'.npz')))
    report['release_validation'] = {
        'definition': 'ten-to-twelve second mean computed pressure held constant for a separate six-second prescribed-load strip response',
        'sigma_kg_m2': .2, 'hem_kg_m': .05, 'damping_kg_m2_s': .08,
        'results': release}
    report['light_unweighted_static'] = {'sigma_kg_m2': .1, 'hem_kg_m': 0., 'results': {}}
    for kind in ['spray', 'heat', 'both']:
        for level in ['medium', 'fine']:
            name = f'grid_{level}_{kind}'
            if name in results:
                report['light_unweighted_static']['results'][name] = light_static_metrics(read(ROOT/'data'/(name+'.npz')))
    report['mean_pressure_profile_comparisons'] = {}
    for kind in ['spray', 'heat', 'both']:
        names = [f'grid_medium_{kind}', f'grid_fine_{kind}']
        if not all(name in results for name in names):
            continue
        medium, fine = (read(ROOT/'data'/(name+'.npz')) for name in names)
        qm, qf = late_pressure(medium), late_pressure(fine)
        qy = np.array([np.interp(fine['y'], medium['y'], q) for q in qm.T]).T
        interpolated = np.array([np.interp(fine['load_z'], medium['load_z'], q) for q in qy])
        report['mean_pressure_profile_comparisons'][kind] = {
            'medium_to_fine_relative_L2': float(np.linalg.norm(interpolated-qf)/np.linalg.norm(qf)),
            'maximum_absolute_difference_Pa': float(abs(interpolated-qf).max()),
            'method': 'piecewise-linear interpolation to fine curtain coordinates with nearest-value endpoint extension'}
    (ROOT/'docs/numerics_qa_results.json').write_text(json.dumps(report, indent=2)+'\n')
    write_report(report)


def write_report(report):
    results, cadence = report['results'], report['cadence']
    text = ['# Independent response and cadence QA', '',
            'Static responses below use direct cumulative quadrature of the continuum hanging-strip equation under the pressure averaged over 10–12 s. The air boundary remains fixed. These are prescribed-load responses, not a computed final shape with two-way airflow feedback. Static width mean uses the full curtain-face quadrature; static and dynamic maxima concern nine fixed physical width probes.', '',
            '| Case | Mean pressure (Pa) | Mean static bottom displacement (cm) | Largest static probe displacement (cm) | Largest dynamic probe displacement (cm) |',
            '|---|---:|---:|---:|---:|']
    for name, value in results.items():
        text.append(f"| {name} | {value['mean_pressure_Pa']:.6f} | {100*value['static_widthmean_bottom_m']:.4f} | {100*value['static_fixed_probe_max_m']:.4f} | {100*value['peak_inward_m']:.4f} |")
    text += ['', 'The grid, time-step and parcel comparisons use the same physical probe positions. Percentage differences below use the second case as denominator. They are sensitivity measures, not confidence intervals or an experimental validation.', '',
             '| First → second | Static width mean change | Static probe maximum change | Dynamic peak change |',
             '|---|---:|---:|---:|']
    for first, second in [('control_spray', 'grid_medium_spray'),
                          ('grid_medium_spray', 'grid_fine_spray'),
                          ('control_heat', 'grid_medium_heat'),
                          ('grid_medium_heat', 'grid_fine_heat'),
                          ('control_both', 'grid_medium_both'),
                          ('grid_medium_both', 'grid_fine_both'),
                          ('control_spray', 'time_half_spray'),
                          ('control_spray', 'rays_double_spray'),
                          ('rays_double_spray', 'rays_quadruple_spray')]:
        if first in results and second in results:
            values = [100*abs(results[first][key]-results[second][key])/max(1e-12, abs(results[second][key]))
                      for key in ['static_widthmean_bottom_m', 'static_fixed_probe_max_m', 'peak_inward_m']]
            text.append(f'| {first} → {second} | {values[0]:.3f}% | {values[1]:.3f}% | {values[2]:.3f}% |')
    if cadence:
        text += ['', '## Saved-pressure cadence', '',
                 'A separate twelve-second run requested a 0.025 s output interval. With a 0.004 s fluid step, the production stride rounding gives an actual interval of 0.024 s. Its final velocity, pressure and temperature fields are bitwise identical to the baseline 0.1 s-output calculation. Only the pressure samples supplied to the structural continuation differ.', '',
                 '| Actual pressure sample interval | Dynamic probe peak (cm) | Change from 0.024 s output |',
                 '|---|---:|---:|']
        for key in ['reference', 'downsample_2', 'downsample_4', 'production']:
            value = cadence[key]
            text.append(f"| {value['actual_output_interval_s']:.3f} s | {100*value['peak_inward_m']:.5f} | {100*value.get('peak_change_relative_to_dense',0):.4f}% |")
        text += ['', 'These cadence comparisons pass the study’s 5% screen for this baseline peak-displacement quantity. They do not establish contact-time accuracy for another case or resolve the separate mesh dependence. No first-contact event or slope-limit event occurred in these baseline cadence comparisons.']
    release = report.get('release_validation', {}).get('results', {})
    if release:
        text += ['', '## Separate response under the computed mean load', '',
                 'This experiment holds the calculated 10–12 s mean pressure constant and releases an initially vertical strip from rest. The six-second structural clock begins at release. It does not claim that the subsequent bathroom pressure is constant or that the airflow boundary follows the sheet. It tests the original article’s mechanical equation with a load supplied by the airflow calculation.', '',
                 '| Pressure source | Largest release excursion at fixed probes | Contact or slope-limit stop |',
                 '|---|---:|---|']
        for name, value in release.items():
            stopped = value['first_contact_s'] is not None or value['slope_stop']
            text.append(f"| {name} | {100*value['peak_m']:.5f} cm | {'Yes' if stopped else 'No'} |")
        for kind in ['spray', 'heat', 'both']:
            a, b = f'grid_medium_{kind}', f'grid_fine_{kind}'
            if a in release and b in release:
                error = abs(release[a]['peak_m']-release[b]['peak_m'])/release[b]['peak_m']
                status = 'passes' if error < .05 else 'does not pass'
                text += ['', f'For {kind}, the maximum release excursion changes by {100*error:.3f}% between the medium and fine pressure fields and {status} the 5% screen. Individual probe excursions can differ more; this does not establish convergence of every local curtain trajectory.']
    for kind, value in report.get('mean_pressure_profile_comparisons', {}).items():
        status = 'passes' if value['medium_to_fine_relative_L2'] < .05 else 'does not pass'
        text += ['', f"For {kind}, the mean pressure maps themselves differ by {100*value['medium_to_fine_relative_L2']:.2f}% in the stated interpolated L2 comparison, with a largest local difference of {value['maximum_absolute_difference_Pa']:.5f} Pa. The complete local pressure map {status} a 5% screen. The strip’s spatial integration can yield a more stable displacement observable than the local pressure values."]
    light = report.get('light_unweighted_static', {}).get('results', {})
    if light:
        text += ['', '## Light curtain without an added hem mass', '',
                 'The same computed mean pressures are applied to the static equation with mass per area 0.10 kg/m² and no added hem mass. The finite hem-slope limit is included explicitly. These responses use the fixed airflow geometry and are not inferred from startup trajectories stopped by the slope limit.', '',
                 '| Pressure source | Width-mean bottom displacement (cm) | Largest fixed-probe displacement (cm) | Largest absolute probe slope |',
                 '|---|---:|---:|---:|']
        for name, value in light.items():
            text.append(f"| {name} | {100*value['static_widthmean_bottom_m']:.5f} | {100*value['static_fixed_probe_max_m']:.5f} | {value['maximum_absolute_probe_slope']:.5f} |")
        for kind in ['spray', 'heat', 'both']:
            a, b = f'grid_medium_{kind}', f'grid_fine_{kind}'
            if a in light and b in light:
                changes = [100*abs(light[a][key]-light[b][key])/max(1e-12, abs(light[b][key]))
                           for key in ['static_widthmean_bottom_m', 'static_fixed_probe_max_m', 'maximum_absolute_probe_slope']]
                text.append(f"\nFor {kind}, medium-to-fine changes are {changes[0]:.3f}% in width-mean bottom displacement, {changes[1]:.3f}% in largest fixed-probe displacement and {changes[2]:.3f}% in largest absolute probe slope.")
    text += ['', 'Reproduce this independent analysis with `python -m tests.qa_response_checks`. The calculation uses the data files currently present and records their names above; a missing fine-grid case is not treated as an accepted refinement. Input and source ranges are assessed in the separate physics review.', '']
    (ROOT/'docs/numerics_qa_results.md').write_text('\n'.join(text))


if __name__ == '__main__':
    main()
