"""Figures and animations of saved phase-one calculations.

This module does no flow or structural integration. Streamlines are integrated
within a saved instantaneous projected field; a pressure pixel is a saved pressure cell. All comparison
panels use common physical times and fixed scales. Displacement profiles use
equal axis scales, so motion is not magnified.

Example::

    python -m curtainflow.render --only fine
    python -m curtainflow.render --only release

``output_dir`` is the project directory, containing ``figures/`` and
``animations/``. The article and the earlier simulation package are untouched.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap, Normalize, SymLogNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import numpy as np
from PIL import Image, ImageSequence


ROOT = Path(__file__).resolve().parents[1]
CASES = ("control_off", "control_spray", "control_heat", "control_both")
FINE_CASES = ("grid_fine_spray", "grid_fine_heat", "grid_fine_both")
CASE_LABELS = ("Exchange off", "Momentum only", "Heat only", "Momentum + heat")
CASE_COLORS = ("#849397", "#426983", "#b16e52", "#25837d")
PAPER, INK, TEAL, MUTED = "#f8f6f0", "#20333d", "#25837d", "#6c7c81"
PRESSURE_CMAP = LinearSegmentedColormap.from_list(
    "phase_one_pressure", ["#355773", "#92adb9", PAPER, "#9bbdb2", "#28796f"]
)
TEMPERATURE_CMAP = LinearSegmentedColormap.from_list(
    "phase_one_temperature", [PAPER, "#d9c6a3", "#bd9060", "#98664e"]
)
plt.rcParams.update({
    "figure.facecolor": PAPER, "axes.facecolor": PAPER,
    "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK,
    "axes.edgecolor": "#b9c4c4", "font.family": "DejaVu Sans",
    "font.size": 10, "axes.titlesize": 12,
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": "#d3dddb", "grid.alpha": .6,
    "savefig.facecolor": PAPER, "svg.fonttype": "none",
})


def load_case(name, data_dir=None):
    """Load numeric arrays without pickle, including their JSON metadata."""
    path = Path(data_dir or ROOT / "data") / f"{name}.npz"
    contents = path.read_bytes()
    with np.load(io.BytesIO(contents), allow_pickle=False) as archive:
        data = {key: archive[key] for key in archive.files}
    data["meta"] = json.loads(str(data["metadata"]))
    data["source_path"] = path
    data["source_sha256"] = hashlib.sha256(contents).hexdigest()
    return data


def _controls(data_dir=None, cases=CASES):
    data = [load_case(case, data_dir) for case in cases]
    first = data[0]
    for other in data[1:]:
        for field in ("x", "y", "z", "load_z"):
            if not np.array_equal(first[field], other[field]):
                raise ValueError(f"Control {field} coordinates differ")
        if not np.array_equal(first["trace"][:, 0], other["trace"][:, 0]):
            raise ValueError("Control snapshots must have identical physical times")
        for field in ("length", "curtain_x", "bottom", "top"):
            if first["meta"][field] != other["meta"][field]:
                raise ValueError(f"Control geometry differs: {field}")
    expected = {"off": (False, False), "spray": (True, False),
                "heat": (False, True), "both": (True, True)}
    for case, d in zip(cases, data):
        switches = expected[case.rsplit("_", 1)[-1]]
        if (d["meta"]["momentum"], d["meta"]["heat"]) != switches:
            raise ValueError(f"Control switch mismatch in {d['source_path']}")
    return data


def _case_label(case):
    return dict(zip(("off", "spray", "heat", "both"), CASE_LABELS))[case.rsplit("_", 1)[-1]]


def _field_axes(count):
    """Three active fine-grid cases fit one row; four controls fit two rows."""
    if count == 3:
        fig, axes = plt.subplots(1, 3, figsize=(14.4, 7.0), squeeze=False)
        fig.subplots_adjust(left=.065, right=.86, top=.80, bottom=.26, wspace=.30)
        colorbar_position = [.9, .315, .014, .395]
    elif count == 4:
        fig, axes = plt.subplots(2, 2, figsize=(11.6, 10.8))
        fig.subplots_adjust(left=.075, right=.82, top=.84, bottom=.24, hspace=.48, wspace=.33)
        colorbar_position = [.873, .29, .019, .40]
    else:
        raise ValueError("Field comparisons need three active cases or four controls")
    return fig, axes, colorbar_position


def _dirs(output_dir=None):
    out = Path(output_dir or ROOT)
    figures, animations = out / "figures", out / "animations"
    figures.mkdir(parents=True, exist_ok=True)
    animations.mkdir(parents=True, exist_ok=True)
    return figures, animations


def _provenance(name, output_dir=None, sources=(), **details):
    out = Path(output_dir or ROOT)
    path = out / "render_manifest.json"
    source_info = []
    for d in sources:
        p = Path(d["source_path"])
        digest = d.get("source_sha256") or hashlib.sha256(p.read_bytes()).hexdigest()
        source_info.append({"file": p.name, "sha256": digest})
    private = out / ".render-tmp"
    private.mkdir(parents=True, exist_ok=True)
    # Separate render processes can complete at the same time. The lock
    # prevents a read-modify-write race between their provenance entries.
    with (private / "manifest.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        existing = json.loads(path.read_text()) if path.exists() else {}
        existing[name] = {"sources": source_info, **details}
        _atomic_export(path, lambda p: p.write_text(json.dumps(existing, indent=2) + "\n"))


def _verify_export(path, expected_frames=None):
    """Decode complete artifacts before their final filenames become visible."""
    suffix = path.suffix.lower()
    if suffix == ".png":
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            im.load()
    elif suffix == ".gif":
        with Image.open(path) as im:
            count = im.n_frames
            for frame in ImageSequence.Iterator(im):
                frame.load()
        if expected_frames is not None and count != expected_frames:
            raise ValueError(f"GIF has {count} frames, expected {expected_frames}")
    elif suffix == ".svg":
        ET.parse(path)
    elif suffix == ".mp4":
        subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-xerror",
                        "-i", str(path), "-f", "null", "-"],
                       check=True, capture_output=True)
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                                "-show_entries", "stream=nb_frames", "-of", "json", str(path)],
                               check=True, capture_output=True, text=True)
        count = int(json.loads(probe.stdout)["streams"][0]["nb_frames"])
        if expected_frames is not None and count != expected_frames:
            raise ValueError(f"MP4 has {count} frames, expected {expected_frames}")
    elif suffix == ".json":
        json.loads(path.read_text())
    else:
        raise ValueError(f"No full-file verifier for {suffix}")


def _atomic_export(target, write, expected_frames=None):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    output_root = target.parent.parent if target.parent.name in ("figures", "animations") else target.parent
    private = output_root / ".render-tmp"
    private.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="export-", dir=private) as temporary:
        pending = Path(temporary) / target.name
        write(pending)
        _verify_export(pending, expected_frames)
        # Flush the completed file before same-filesystem atomic replacement.
        with pending.open("rb") as stream:
            os.fsync(stream.fileno())
        os.replace(pending, target)


def _save_figure(fig, name, output_dir=None):
    figures, _ = _dirs(output_dir)
    paths = [figures / f"{name}.{suffix}" for suffix in ("png", "svg")]
    for path in paths:
        _atomic_export(path, lambda p: fig.savefig(p, dpi=180))
    plt.close(fig)
    return paths


def _frames(times, max_frames):
    if len(times) < 2 or np.any(np.diff(times) <= 0):
        raise ValueError("Animation requires increasing physical times")
    if max_frames is None or max_frames >= len(times):
        selected = np.arange(len(times))
    else:
        if max_frames < 2:
            raise ValueError("max_frames must be at least two")
        # A constant stride preserves constant playback timing. Include the
        # final saved state only when it falls on the same regular interval.
        stride = int(np.ceil((len(times) - 1) / (max_frames - 1)))
        selected = np.arange(0, len(times), stride)
    intervals = np.diff(times[selected])
    if not np.allclose(intervals, intervals[0], rtol=1e-7, atol=1e-9):
        raise ValueError("Saved frames must be regularly spaced for time-faithful playback")
    return selected, float(1 / intervals[0])


def _save_animation(fig, update, times, name, output_dir=None,
                    max_frames=None, sources=(), **details):
    figures, animations = _dirs(output_dir)
    selected, fps = _frames(np.asarray(times), max_frames)
    ani = FuncAnimation(fig, update, frames=selected, interval=1000 / fps,
                        blit=False, repeat=False)
    paths = [animations / f"{name}.mp4", animations / f"{name}.gif"]
    _atomic_export(paths[0], lambda p: ani.save(p, writer=FFMpegWriter(
        fps=fps, codec="libx264", bitrate=2400,
        extra_args=["-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-pix_fmt", "yuv420p"]), dpi=100), len(selected))
    _atomic_export(paths[1], lambda p: ani.save(p, writer=PillowWriter(fps=fps), dpi=100), len(selected))
    update(int(selected[-1]))
    for suffix in ("png", "svg"):
        path = figures / f"{name}_poster.{suffix}"
        _atomic_export(path, lambda p: fig.savefig(p, dpi=180))
        paths.append(path)
    plt.close(fig)
    _provenance(name, output_dir, sources, physical_times_s=np.asarray(times)[selected].tolist(),
                frames_per_second=fps, playback="1 second of simulation per second of video",
                poster_time_s=float(times[selected[-1]]), **details)
    return paths


def _symmetric_limit(arrays):
    limit = max(float(np.max(np.abs(a))) for a in arrays)
    return limit if limit else 1.0


def _cell_extent(axis):
    h = float(axis[1] - axis[0])
    return float(axis[0] - h / 2), float(axis[-1] + h / 2)


def _title(fig, title, subtitle):
    fig.text(.075, .966, title, ha="left", va="top", fontsize=18)
    fig.text(.075, .925, subtitle, ha="left", va="top", fontsize=10, color=MUTED)


def geometry(data_dir=None, output_dir=None, source_case="control_off"):
    """Geometry at declared dimensions, including the actual saved flow slice."""
    d = load_case(source_case, data_dir)
    m = d["meta"]
    lx, ly, lz = m["length"]
    cx, bottom, top = m["curtain_x"], m["bottom"], m["top"]
    cut = float(d["x"][np.argmin(abs(d["x"] - .45))])
    hx, hy, hz = m["head"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.8, 6.8), gridspec_kw={"width_ratios": [1, 1.22]})
    a.plot([0, lx, lx, 0, 0], [0, 0, lz, lz, 0], color=MUTED, lw=1.3)
    a.plot([cx, cx], [bottom, top], color=TEAL, lw=4, solid_capstyle="butt")
    a.axvline(cut, color="#8c9ba3", ls="--", lw=1)
    a.scatter([hx], [hz], s=38, color=CASE_COLORS[1], zorder=3)
    a.text(.04, .08, "Shower side", transform=a.transAxes, fontsize=10)
    a.text(.61, .08, "Other side", transform=a.transAxes, fontsize=10)
    a.text(cx + .05, 1.13, "Fixed curtain", rotation=90, va="center", color=TEAL)
    a.text(cut - .045, .57, f"Saved slice x = {cut:.4f} m", rotation=90, va="bottom", ha="right", fontsize=9, color=MUTED)
    a.set(xlim=(-.04, lx + .30), ylim=(-.04, lz + .12), xlabel="x (m)", ylabel="Height z (m)", title="Cross-section through the enclosure")
    # Dimension lines are geometry annotations, not velocity vectors.
    for lo, hi, label in ((0, bottom, f"{bottom:g} m gap"),
                           (bottom, top, f"{top-bottom:g} m sheet"),
                           (top, lz, f"{lz-top:g} m gap")):
        xx = lx + .10
        a.plot([xx, xx], [lo, hi], color=MUTED, lw=.8)
        a.plot([xx-.025, xx+.025], [lo, lo], color=MUTED, lw=.8)
        a.plot([xx-.025, xx+.025], [hi, hi], color=MUTED, lw=.8)
        a.text(xx + .045, (lo + hi) / 2, label, va="center", fontsize=8.5)
    b.plot([0, ly, ly, 0, 0], [0, 0, lz, lz, 0], color=MUTED, lw=1.3)
    b.fill_between([0, ly], bottom, top, facecolor=TEAL, alpha=.15)
    b.plot([0, ly, ly, 0, 0], [bottom, bottom, top, top, bottom], color=TEAL, lw=1.5)
    b.text(ly/2, (bottom+top)/2, f"Curtain face\nx = {cx:g} m", ha="center", va="center", color=TEAL, fontsize=13)
    b.text(ly/2, (top + lz) / 2, "Upper exchange gap", ha="center", va="center", fontsize=9)
    b.text(ly/2, bottom / 2, "Lower exchange gap", ha="center", va="center", fontsize=9)
    b.set(xlim=(-.04, ly + .04), ylim=(-.04, lz + .12), xlabel="Width y (m)", ylabel="Height z (m)", title="Face of the curtain")
    for ax, width in ((a, lx), (b, ly)):
        ax.set_aspect("equal")
        ax.set_xticks(np.arange(0, width + .01, .6))
        ax.set_yticks(np.arange(0, lz + .01, .6))
    _title(fig, "The phase-one enclosure", f"Declared geometry · {lx:g} × {ly:g} × {lz:g} m · impermeable curtain, fixed during airflow calculation")
    fig.text(.075, .060, f"Head centre = ({hx:g}, {hy:g}, {hz:g}) m; blue dot is its x–z projection. Curtain ends meet the y walls.", fontsize=9)
    fig.text(.075, .030, "The diagram shows geometry. The enclosure has no bather or ventilation; outer walls are free-slip and insulating.", fontsize=9, color=MUTED)
    fig.subplots_adjust(left=.075, right=.94, bottom=.16, top=.835, wspace=.34)
    paths = _save_figure(fig, "figure_01_geometry", output_dir)
    _provenance("figure_01_geometry", output_dir, [d], length_m=m["length"],
                curtain_x_m=cx, curtain_bottom_top_m=[bottom, top], saved_slice_x_m=cut,
                diagram="geometry only; no computed flow represented")
    return paths


def control_summary(data_dir=None, output_dir=None):
    """Saved pressure histories and signed final load profiles."""
    data = _controls(data_dir)
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.8, 6.2), gridspec_kw={"width_ratios": [1.5, 1]})
    for d, label, color in zip(data, CASE_LABELS, CASE_COLORS):
        t = d["trace"][:, 0]
        # Use the saved spatial pressure field rather than inferring a load
        # from flow speed or from a prescribed vortex.
        a.plot(t, d["pressure_load"].mean(axis=(1, 2)) * 1000,
               label=label, color=color, lw=2)
        b.plot(d["pressure_load"][-1].mean(axis=0) * 1000,
               d["load_z"], color=color, lw=2)
    a.axhline(0, color=MUTED, lw=.7)
    b.axvline(0, color=MUTED, lw=.7)
    a.set(xlabel="Physical time (s)", ylabel="Area-mean Δp (mPa)", title="Pressure load through time")
    b.set(xlabel="Width-mean Δp (mPa)", ylabel="Height z (m)", title=f"Vertical profile at {data[0]['trace'][-1,0]:g} s")
    for ax in (a, b):
        ax.grid(True)
        ax.xaxis.set_major_locator(MaxNLocator(6))
    a.legend(frameon=False, ncol=2, loc="best", fontsize=9)
    _title(fig, "Computed pressure across the fixed curtain", "Δp = outside − inside · positive load points inward, toward the shower side")
    fig.text(.075, .062, "Momentum and heat switches isolate exchange mechanisms; the single-exchange controls are artificial comparisons.", fontsize=9)
    fig.text(.075, .030, "Pressure load is shown separately from viscous normal stress. These curves are predictions of the declared model.", fontsize=9, color=MUTED)
    fig.subplots_adjust(left=.10, right=.96, bottom=.18, top=.81, wspace=.36)
    paths = _save_figure(fig, "figure_02_control_pressure", output_dir)
    _provenance("figure_02_control_pressure", output_dir, data,
                pressure_units="mPa", final_time_s=float(data[0]["trace"][-1, 0]),
                pressure_sign="outside minus inside; positive inward")
    return paths


def flow_controls(data_dir=None, output_dir=None, max_frames=None, cases=CASES, name=None):
    """Pressure and instantaneous projected streamlines on four y–z slices.

    Streamlines follow the saved (u_y, u_z) field at one instant; they are
    neither time-integrated particles nor 3D streamlines. The integration
    inside Matplotlib interpolates this saved field; no velocity is invented
    or changed. Constant-width directional marks encode orientation, not speed.
    """
    data = _controls(data_dir, cases)
    times = data[0]["trace"][:, 0]
    m = data[0]["meta"]
    cut = float(data[0]["x"][np.argmin(abs(data[0]["x"] - .45))])
    lim = _symmetric_limit([d["pressure_yz"] for d in data])
    linear_threshold = .02
    pressure_norm = SymLogNorm(linthresh=linear_threshold, linscale=1, base=10, vmin=-lim, vmax=lim)
    fig, axes, cbar_position = _field_axes(len(data))
    images, notes = [], []
    extent = [*_cell_extent(data[0]["y"]), *_cell_extent(data[0]["z"])]
    for ax, d, case in zip(axes.flat, data, cases):
        image = ax.imshow(d["pressure_yz"][0].T, origin="lower", extent=extent,
                          cmap=PRESSURE_CMAP, norm=pressure_norm,
                          interpolation="nearest", aspect="equal")
        images.append(image)
        notes.append(ax.text(0, -.21, "", transform=ax.transAxes, fontsize=9, color=MUTED))
        ax.set(xlim=(0, m["length"][1]), ylim=(0, m["length"][2]),
               xlabel="Width y (m)", ylabel="Height z (m)", title=_case_label(case))
        ax.set_xticks(np.arange(0, m["length"][1]+.01, .6))
        ax.set_yticks(np.arange(0, m["length"][2]+.01, .6))
    fine = all(case.startswith("grid_fine_") for case in cases)
    grid_label = " × ".join(map(str, m["shape"]))
    _title(fig, "Computed airflow on the finest study grid" if fine else "Air motion in the control calculations", f"Saved y–z slice at x = {cut:.5f} m · parallel to the curtain at x = {m['curtain_x']:g} m")
    clock = fig.text(.075, .891, "", fontsize=10)
    fig.text(.075, .125, "Curves: instantaneous streamlines of projected (y, z) velocity. Direction marks do not encode speed.", fontsize=9)
    fig.text(.075, .095, "These are not particle paths or 3D streamlines. The out-of-plane x velocity is omitted; the curtain stays fixed.", fontsize=9, color=MUTED)
    fig.text(.075, .065, "Pressure uses one symmetric log scale, linear within ±0.02 Pa. All extrema are retained; reference is the room mean.", fontsize=9, color=MUTED)
    fig.text(.075, .035, "Local curtain-pressure maps are not fully grid-converged; the flow images show the calculated field on this grid.", fontsize=9, color=MUTED)
    cax = fig.add_axes(cbar_position)
    cbar = fig.colorbar(images[0], cax=cax)
    cbar.set_label("Reduced pressure p′ (Pa) · symmetric log", labelpad=10)
    ticks = np.array([-10., -1., -.1, -.02, 0., .02, .1, 1., 10.])
    ticks = ticks[(ticks >= -lim) & (ticks <= lim)]
    cbar.set_ticks(ticks)
    cbar.set_ticklabels([f"{t:g}" for t in ticks])
    def update(i):
        for ax, d, im, note in zip(axes.flat, data, images, notes):
            im.set_data(d["pressure_yz"][i].T)
            # Matplotlib stores the paths as collections and their direction
            # marks as individual patches. Remove both before the next frame.
            for artist in [*ax.collections, *ax.patches]:
                artist.remove()
            vy, vz = d["velocity_yz"][i, 1], d["velocity_yz"][i, 2]
            peak_speed = float(np.hypot(vy, vz).max())
            if peak_speed > 0:
                ax.streamplot(d["y"], d["z"], vy.T, vz.T, density=.85,
                              color=INK, linewidth=.75, arrowsize=.68,
                              minlength=.15, maxlength=4,
                              integration_direction="both", broken_streamlines=True)
            note.set_text(f"Largest in-plane speed in this slice: {peak_speed:.3f} m/s")
        clock.set_text(f"Physical airflow time = {times[i]:.2f} s    ·    fixed curtain    ·    {'fine grid' if fine else 'grid'} {grid_label}")
        return (*images, *notes, clock)
    name = name or ("animation_01_fine_airflow" if fine else "animation_01_flow_controls")
    return _save_animation(fig, update, times, name, output_dir,
                           max_frames, data, slice="yz", actual_slice_x_m=cut,
                           target_slice_x_m=.45, pressure_limits_Pa=[-lim, lim],
                           pressure_reference="room mean", velocity_components=["y", "z"],
                           pressure_normalization="symmetric log, base 10, linscale 1",
                           pressure_linear_threshold_Pa=linear_threshold,
                           streamline_type="instantaneous 2D streamlines of saved projected velocity; not trajectories or 3D streamlines",
                           streamline_density=.85, direction_marks="orientation only; not velocity magnitude",
                           grid_shape=m["shape"], local_pressure_convergence="not fully grid-converged",
                           fixed_air_boundary=True)


def pressure_maps(data_dir=None, output_dir=None, max_frames=None, cases=CASES, name=None):
    """Full-curtain signed pressure maps, at synchronized physical times."""
    data = _controls(data_dir, cases)
    times = data[0]["trace"][:, 0]
    m = data[0]["meta"]
    lim = _symmetric_limit([d["pressure_load"] for d in data])
    fig, axes, cbar_position = _field_axes(len(data))
    images, notes = [], []
    extent = [*_cell_extent(data[0]["y"]), *_cell_extent(data[0]["load_z"])]
    for ax, d, case in zip(axes.flat, data, cases):
        im = ax.imshow(d["pressure_load"][0].T, origin="lower", extent=extent,
                       norm=Normalize(-lim, lim), cmap=PRESSURE_CMAP,
                       interpolation="nearest", aspect="equal")
        images.append(im)
        notes.append(ax.text(0, -.36, "", transform=ax.transAxes, fontsize=9, color=MUTED))
        ax.set(xlim=(0, m["length"][1]), ylim=(m["bottom"], m["top"]),
               xlabel="Width y (m)", ylabel="Height z (m)", title=_case_label(case))
        ax.set_xticks(np.arange(0, m["length"][1]+.01, .6))
        ax.set_yticks(np.linspace(m["bottom"], m["top"], 4))
    _title(fig, "Pressure load on the full curtain", "Δp = outside − inside at cells adjacent to the blocked curtain face · positive is inward")
    fine = all(case.startswith("grid_fine_") for case in cases)
    grid_label = " × ".join(map(str, m["shape"]))
    clock = fig.text(.075, .883, "", fontsize=10)
    fig.text(.075, .095, f"Fixed curtain at x = {m['curtain_x']:g} m · shared color scale · normal viscous stress is recorded separately.", fontsize=9, color=MUTED)
    fig.text(.075, .06, "Local pressure maps are not fully grid-converged. These pixels show the saved cell values, without spatial smoothing.", fontsize=9, color=MUTED)
    cax = fig.add_axes(cbar_position)
    cbar = fig.colorbar(images[0], cax=cax)
    cbar.set_label("Inward pressure load Δp (Pa)", labelpad=10)
    cbar.ax.yaxis.set_major_locator(MaxNLocator(5))
    def update(i):
        for d, im, note in zip(data, images, notes):
            field = d["pressure_load"][i]
            im.set_data(field.T)
            note.set_text(f"Mean {field.mean():+.4f} Pa\nRange {field.min():+.4f} to {field.max():+.4f} Pa")
        clock.set_text(f"Physical airflow time = {times[i]:.2f} s    ·    {'fine grid' if fine else 'grid'} {grid_label}    ·    entire {m['length'][1]:g} × {m['top']-m['bottom']:g} m sheet")
        return (*images, *notes, clock)
    name = name or ("animation_02_fine_curtain_pressure" if fine else "animation_02_curtain_pressure")
    return _save_animation(fig, update, times, name, output_dir,
                           max_frames, data, pressure_limits_Pa=[-lim, lim],
                           pressure_sign="outside minus inside; positive inward",
                           curtain_x_m=m["curtain_x"], grid_shape=m["shape"],
                           local_pressure_convergence="not fully grid-converged", fixed_air_boundary=True)


def temperature_controls(data_dir=None, output_dir=None, max_frames=None, cases=CASES, name=None):
    """Air temperature rise from saved parcel-to-air sensible heat exchange."""
    data = _controls(data_dir, cases)
    times = data[0]["trace"][:, 0]
    meta = data[0]["meta"]
    cut = float(data[0]["x"][np.argmin(abs(data[0]["x"] - .45))])
    low = min(0., min(float(d["temperature_yz"].min()) for d in data))
    high = max(float(d["temperature_yz"].max()) for d in data)
    high = high if high > low else low + 1.
    fig, axes, cbar_position = _field_axes(len(data))
    images, notes = [], []
    extent = [*_cell_extent(data[0]["y"]), *_cell_extent(data[0]["z"])]
    for ax, d, case in zip(axes.flat, data, cases):
        im = ax.imshow(d["temperature_yz"][0].T, origin="lower", extent=extent,
                       cmap=TEMPERATURE_CMAP, norm=Normalize(low, high),
                       interpolation="nearest", aspect="equal")
        images.append(im)
        notes.append(ax.text(0, -.21, "", transform=ax.transAxes, fontsize=9, color=MUTED))
        ax.set(xlim=(0, meta["length"][1]), ylim=(0, meta["length"][2]),
               xlabel="Width y (m)", ylabel="Height z (m)", title=_case_label(case))
        ax.set_xticks(np.arange(0, meta["length"][1]+.01, .6))
        ax.set_yticks(np.arange(0, meta["length"][2]+.01, .6))
    _title(fig, "Sensible heating of the computed air",
           f"Saved y–z slice at x = {cut:.5f} m · air temperature rise ΔT · one linear color scale for all controls")
    fine = all(case.startswith("grid_fine_") for case in cases)
    grid_label = " × ".join(map(str, meta["shape"]))
    clock = fig.text(.075, .891, "", fontsize=10)
    fig.text(.075, .105, "The upward buoyancy term in the momentum equation is gβΔT. Panel readouts use the same saved temperature field.", fontsize=9)
    fig.text(.075, .075, "Heat enters through parcel-to-air sensible exchange; the warm air is transported by the computed velocity field.", fontsize=9, color=MUTED)
    fig.text(.075, .045, "Fixed curtain · insulating outer walls · temperature is a model prediction, with no evaporation or bather heat source.", fontsize=9, color=MUTED)
    cax = fig.add_axes(cbar_position)
    cbar = fig.colorbar(images[0], cax=cax)
    cbar.set_label("Air temperature rise ΔT (K)", labelpad=10)
    cbar.ax.yaxis.set_major_locator(MaxNLocator(6))
    def update(i):
        for d, im, note in zip(data, images, notes):
            field = d["temperature_yz"][i]
            peak = float(field.max())
            buoyancy = d["meta"]["g"] * d["meta"]["beta"] * peak
            im.set_data(field.T)
            note.set_text(f"Peak ΔT {peak:.2f} K   |   peak gβΔT {buoyancy:.3f} m/s²")
        clock.set_text(f"Physical airflow time = {times[i]:.2f} s    ·    fixed curtain    ·    {'fine grid' if fine else 'grid'} {grid_label}")
        return (*images, *notes, clock)
    name = name or ("animation_04_fine_air_temperature" if fine else "animation_04_air_temperature")
    return _save_animation(fig, update, times, name, output_dir,
                           max_frames, data, slice="yz", actual_slice_x_m=cut,
                           temperature_limits_K=[low, high], temperature_normalization="linear",
                           buoyancy_readout="g * beta * maximum saved air temperature rise in the slice",
                           grid_shape=meta["shape"],
                           fixed_air_boundary=True)


def load_structure(name, data_dir=None):
    """Read the variable-length, independently terminated strip histories.

    Required NPZ keys: width_y_m, reason, event_time, metadata; and t_j, s_j,
    y_j for each strip j. y_j has shape (len(t_j), len(s_j)) and includes
    the fixed top node. An event state is kept at its actual event time.
    """
    path = Path(data_dir or ROOT / "data") / f"{name}.npz"
    contents = path.read_bytes()
    with np.load(io.BytesIO(contents), allow_pickle=False) as source:
        meta = json.loads(str(source["metadata"]))
        strips = []
        for j, width in enumerate(source["width_y_m"]):
            t, s, displacement = (source[f"{key}_{j}"] for key in ("t", "s", "y"))
            if displacement.shape != (len(t), len(s)):
                raise ValueError(f"Incompatible strip dimensions in {path.name}, strip {j}")
            if np.any(np.diff(t) < 0) or not np.isfinite(displacement).all():
                raise ValueError(f"Invalid saved strip state in {path.name}, strip {j}")
            strip = {"width_y_m": float(width), "t": t, "s": s, "y": displacement,
                     "reason": str(source["reason"][j]),
                     "event_time": float(source["event_time"][j])}
            if f"static_s_{j}" in source:
                strip["static_s"] = source[f"static_s_{j}"]
                strip["static_y"] = source[f"static_y_{j}"]
            strips.append(strip)
    return {"strips": strips, "meta": meta, "source_path": path,
            "source_sha256": hashlib.sha256(contents).hexdigest()}


def _profile_at(strip, physical_time):
    """Interpolate saved states in time; hold a terminated last state."""
    t = strip["t"]
    right = int(np.searchsorted(t, physical_time, side="right"))
    if right == 0:
        return strip["y"][0]
    if right >= len(t):
        return strip["y"][-1]
    left = right - 1
    fraction = (physical_time - t[left]) / (t[right] - t[left])
    return (1 - fraction) * strip["y"][left] + fraction * strip["y"][right]


def release_comparison(data_dir=None, output_dir=None, max_frames=None):
    """Separate release experiment under the computed 10–12 s mean load.

    The load and static reference are saved by release.py. Each mechanism uses
    its declared fixed width probe, selected for the largest saved excursion
    among nine probes. The plotted displacement is not fed into any flow field.
    """
    structures = [load_structure(f"release_{case}", data_dir) for case in FINE_CASES]
    flows = [load_case(case, data_dir) for case in FINE_CASES]
    selected_strips = []
    for case, structure, flow in zip(FINE_CASES, structures, flows):
        meta = structure["meta"]
        if meta["source"] != f"{case}.npz" or meta["source_sha256"] != flow["source_sha256"]:
            raise ValueError(f"Release source hash does not match {case}")
        if meta["positive_displacement"] != "inward":
            raise ValueError("Release displacement sign must be positive inward")
        selected = int(meta["selected_probe_index"])
        strip = structure["strips"][selected]
        if "static_y" not in strip:
            raise ValueError("Release archive must contain its matching static profile")
        largest = max(float(np.abs(s["y"]).max()) for s in structure["strips"])
        if not np.isclose(float(np.abs(strip["y"]).max()), largest, rtol=1e-10, atol=1e-12):
            raise ValueError("Declared release probe is not the largest sampled excursion")
        selected_strips.append(strip)
    times = selected_strips[0]["t"]
    if any(not np.array_equal(strip["t"], times) for strip in selected_strips[1:]):
        raise ValueError("Selected release strips must share saved time coordinates")
    window = structures[0]["meta"]["airflow_window_s"]
    sheet_mass = structures[0]["meta"]["sigma_kg_m2"]
    hem_mass = structures[0]["meta"]["hem_kg_m"]
    if any(a["meta"]["airflow_window_s"] != window for a in structures[1:]):
        raise ValueError("Release comparisons must use the same airflow averaging window")
    heights = [(flow["meta"]["bottom"], flow["meta"]["top"]) for flow in flows]
    if heights[1:] != heights[:-1]:
        raise ValueError("Release comparisons must have the same physical height")
    bottom, top = heights[0]
    histories = [100*np.max(strip["y"], axis=1) for strip in selected_strips]
    static_levels = [100*float(strip["static_y"].max()) for strip in selected_strips]
    maximum = max(float(h.max()) for h in histories)
    fig = plt.figure(figsize=(14.4, 7.8))
    outer = fig.add_gridspec(1, 3, left=.052, right=.978, top=.79, bottom=.27, wspace=.23)
    shape_lines, history_lines, dots, notes = [], [], [], []
    colors = CASE_COLORS[1:]
    for j, (case, strip, history, static, color) in enumerate(zip(FINE_CASES, selected_strips, histories, static_levels, colors)):
        inner = outer[j].subgridspec(1, 2, width_ratios=(.70, 2.6), wspace=.52)
        shape_ax, history_ax = (fig.add_subplot(inner[0, k]) for k in range(2))
        shape_ax.axvline(0, color="#b6c3c2", lw=.8)
        shape_ax.plot(strip["static_y"], top-strip["static_s"], color=INK, ls="--", lw=1.4)
        shape_line, = shape_ax.plot([], [], color=color, lw=2.2)
        shape_lines.append(shape_line)
        shape_ax.set(xlim=(-.10, .20), ylim=(bottom, top), xlabel="Y (m)", title="Shape")
        shape_ax.set_aspect("equal", adjustable="box")
        shape_ax.set_xticks([0, .1])
        shape_ax.set_yticks([bottom, (bottom+top)/2, top])
        shape_ax.tick_params(labelsize=8)
        shape_ax.set_ylabel("Height z (m)" if j == 0 else "", fontsize=9)
        shape_ax.grid(True)
        history_ax.axhline(static, color=INK, ls="--", lw=1.4)
        hline, = history_ax.plot([], [], color=color, lw=2)
        dot, = history_ax.plot([], [], "o", color=color, ms=4)
        history_lines.append(hline)
        dots.append(dot)
        history_ax.set(xlim=(times[0], times[-1]), ylim=(0, maximum*1.13),
                       xlabel="Time since release (s)", ylabel="Largest inward displacement (cm)",
                       title="Displacement history")
        history_ax.xaxis.set_major_locator(MaxNLocator(4))
        history_ax.yaxis.set_major_locator(MaxNLocator(5))
        history_ax.tick_params(labelsize=9)
        history_ax.grid(True)
        # The mechanism's fixed probe is explicit above its two related charts.
        centre = (.052 + .978)/2 + (j-1) * (.978-.052)/3
        fig.text(centre, .837, f"{_case_label(case)}  ·  y = {strip['width_y_m']:.4f} m",
                 ha="center", fontsize=12, color=color)
        notes.append(fig.text(centre, .188, "", ha="center", fontsize=9))
    _title(fig, "Release under the computed mean pressure load",
           f"Separate strip experiment · fixed {window[0]:g}–{window[1]:g} s mean load from the 48 × 64 × 64 airflow calculation")
    clock = fig.text(.075, .884, "", fontsize=10)
    fig.legend(handles=[Line2D([], [], color=INK, lw=2, label="Release response"),
                        Line2D([], [], color=INK, lw=1.4, ls="--", label="Static reference at the same width and load")],
               loc="lower left", bbox_to_anchor=(.068, .133), ncol=2, frameon=False, fontsize=9)
    fig.text(.075, .115, "Each mechanism uses the largest-excursion probe among nine fixed sampled widths; the selected width stays fixed during the animation.", fontsize=9)
    fig.text(.075, .082, "Shape axes use equal metre scales. The saved pressure load is held constant without rescaling; positive Y points inward.", fontsize=9, color=MUTED)
    fig.text(.075, .049, "This release clock is independent of the airflow clock. The prescribed-load mechanics does not move the airflow boundary.", fontsize=9, color=MUTED)
    def update(i):
        for strip, line, hline, dot, note, history, static in zip(selected_strips, shape_lines, history_lines, dots, notes, histories, static_levels):
            line.set_data(strip["y"][i], top-strip["s"])
            hline.set_data(times[:i+1], history[:i+1])
            dot.set_data([times[i]], [history[i]])
            note.set_text(f"Current maximum Y {history[i]:.2f} cm   ·   static {static:.2f} cm")
        clock.set_text(f"Time since release = {times[i]:.2f} s    ·    sheet {sheet_mass:.2f} kg/m²    ·    hem {hem_mass:.2f} kg/m")
        return (*shape_lines, *history_lines, *dots, *notes, clock)
    return _save_animation(fig, update, times, "animation_03_fine_mean_load_release", output_dir,
                           101 if max_frames is None else max_frames, [*structures, *flows],
                           time_definition="seconds since release under computed 10–12 s mean load; independent of airflow time",
                           airflow_window_s=window, fixed_air_boundary=True, load_rescaling=False,
                           selected_probe_indices=[int(s["meta"]["selected_probe_index"]) for s in structures],
                           selected_widths_y_m=[s["width_y_m"] for s in selected_strips],
                           selection="largest saved excursion among nine fixed sampled width probes per mechanism",
                           equal_displacement_height_scales=True,
                           history_quantity="largest inward displacement along the selected strip; max(Y), in cm",
                           static_references="saved static_s_i and static_y_i at the identical selected width")


def structural_response(case="control_both", variants=("_unweighted", "", "_weighted"),
                        data_dir=None, output_dir=None, max_frames=None):
    """Saved load, true-aspect strip shape, and response to different hems.

    All curves in the shape panel use the same sampled width. It is selected
    as the width with greatest saved absolute displacement in the baseline
    response. The time panel reports the largest saved absolute displacement
    across all sampled widths until the first strip terminates. This choice and its source
    are written to the render manifest; it is not an enclosure-wide maximum.
    """
    flow = load_case(case, data_dir)
    structures = [load_structure(f"structural_{case}{variant}", data_dir) for variant in variants]
    if len(structures) > 3:
        raise ValueError("At most three material variants fit the response comparison")
    times = flow["trace"][:, 0]
    meta = flow["meta"]
    baseline = structures[variants.index("")] if "" in variants else structures[0]
    selected = int(np.argmax([float(np.abs(s["y"]).max()) for s in baseline["strips"]]))
    width = baseline["strips"][selected]["width_y_m"]
    width_index = int(np.argmin(abs(flow["y"] - width)))
    widths = [s["width_y_m"] for s in baseline["strips"]]
    for structure in structures:
        if structure["meta"]["source"] != f"{case}.npz":
            raise ValueError("Structural metadata does not name the chosen flow source")
        if [s["width_y_m"] for s in structure["strips"]] != widths:
            raise ValueError("Structural comparisons must use identical sampled widths")
        if structure["meta"].get("include_viscous", False):
            raise ValueError("This pressure-fed comparison requires pressure-only structural files")
        for strip in structure["strips"]:
            if strip["reason"] == "end" and strip["t"][-1] < times[-1] - 1e-8:
                raise ValueError("Unterminated structural response ends before the flow timeline")
    pressure = flow["pressure_load"]
    pressure_limit = _symmetric_limit([pressure])
    clearance = float(baseline["meta"]["clearance"])
    low = min(float(s["y"].min()) for a in structures for s in a["strips"])
    high = max(float(s["y"].max()) for a in structures for s in a["strips"])
    xlo, xhi = min(-.04, low - .025), max(clearance + .035, high + .025)
    colors = (CASE_COLORS[2], TEAL, CASE_COLORS[1])[:len(structures)]
    labels = [f"Hem {a['meta']['hem']:g} kg/m" for a in structures]
    histories = []
    history_times = []
    for structure in structures:
        events = [s["event_time"] for s in structure["strips"] if s["reason"] != "end"]
        stop = min(events) if events else times[-1]
        ht = times[times < stop]
        ht = np.r_[ht, stop]
        history_times.append(ht)
        histories.append(np.array([max(np.abs(_profile_at(s, t)).max()
                                        for s in structure["strips"]) for t in ht]))
    fig = plt.figure(figsize=(12.8, 7.2))
    grid = fig.add_gridspec(1, 3, width_ratios=(1.35, .66, 1.8),
                           left=.08, right=.965, top=.80, bottom=.22, wspace=.45)
    paxis, saxis, taxis = [fig.add_subplot(grid[0, j]) for j in range(3)]
    pressure_line, = paxis.plot([], [], color=INK, lw=2)
    pressure_lines = []
    for sampled_width in widths:
        j = int(np.argmin(abs(flow["y"] - sampled_width)))
        line, = paxis.plot([], [], color="#9cacab", lw=.65, alpha=.65)
        pressure_lines.append((j, line))
    # Redraw the selected pressure line above the other width samples.
    pressure_line.set_zorder(4)
    paxis.axvline(0, color=MUTED, lw=.7)
    paxis.set(xlim=(-pressure_limit*1.08, pressure_limit*1.08),
              ylim=(meta["bottom"], meta["top"]), xlabel="Inward pressure Δp (Pa)",
              ylabel="Height z (m)", title="Saved pressure input")
    paxis.xaxis.set_major_locator(MaxNLocator(5))
    paxis.grid(True)
    saxis.axvline(0, color="#a7b7b7", lw=1)
    saxis.axvline(clearance, color=MUTED, lw=1, ls="--")
    saxis.text(clearance+.009, meta["bottom"]+.06, "First-contact test plane", rotation=90,
               fontsize=8, va="bottom", color=MUTED)
    shape_lines = []
    for color in colors:
        line, = saxis.plot([], [], color=color, lw=2)
        shape_lines.append(line)
    saxis.set(xlim=(xlo, xhi), ylim=(meta["bottom"], meta["top"]),
              xlabel="Displacement (m)", title="One sampled strip")
    saxis.set_aspect("equal", adjustable="box")
    saxis.set_xticks([0, clearance])
    saxis.set_yticks(np.linspace(meta["bottom"], meta["top"], 4))
    saxis.tick_params(axis="y", labelleft=False)
    saxis.grid(True)
    history_lines, dots = [], []
    for color, label in zip(colors, labels):
        line, = taxis.plot([], [], color=color, lw=2, label=label)
        dot, = taxis.plot([], [], "o", color=color, ms=4)
        history_lines.append(line)
        dots.append(dot)
    maximum = max(float(h.max()) for h in histories)
    taxis.set(xlim=(times[0], times[-1]), ylim=(0, max(.01, maximum*1.10)),
              xlabel="Physical time (s)", ylabel="Largest saved |displacement| (m)",
              title=f"Maximum over {len(widths)} sampled widths")
    taxis.grid(True)
    taxis.legend(frameon=False, fontsize=9, loc="upper left")
    case_label = CASE_LABELS[CASES.index(case)] if case in CASES else case.replace("_", " ")
    _title(fig, "From computed pressure to a one-way curtain response",
           f"{case_label} · sheet mass {baseline['meta']['sigma']:g} kg/m² · the airflow boundary remains fixed")
    clock = fig.text(.08, .874, "", fontsize=10)
    status = fig.text(.08, .13, "", fontsize=9, color=MUTED)
    fig.text(.08, .093, f"Shape: y = {width:.4f} m, chosen by the baseline’s largest saved displacement; horizontal and vertical scales are equal.", fontsize=9)
    fig.text(.08, .059, "Grey pressure curves show the other sampled widths. The test plane is a stopping condition, not a simulated body.", fontsize=9, color=MUTED)
    fig.text(.08, .029, "Stop at contact or |slope| = 0.3. Time curves end at the first strip stop; a held shape shows its saved terminal state.", fontsize=9, color=MUTED)
    def update(i):
        t = times[i]
        pressure_line.set_data(pressure[i, width_index], flow["load_z"])
        for j, line in pressure_lines:
            line.set_data(pressure[i, j], flow["load_z"])
        stopped = []
        for a, shape_line, hline, dot, ht, history, label in zip(structures, shape_lines, history_lines, dots, history_times, histories, labels):
            strip = a["strips"][selected]
            shape_line.set_data(_profile_at(strip, t), meta["top"] - strip["s"])
            last = max(1, int(np.searchsorted(ht, t, side="right")))
            hline.set_data(ht[:last], history[:last])
            dot.set_data([ht[last-1]], [history[last-1]])
            dot.set_markerfacecolor(PAPER if t > ht[-1] else dot.get_color())
            count = sum(s["reason"] != "end" and t >= s["event_time"] for s in a["strips"])
            stopped.append(f"{label}: {count}/{len(widths)} terminated")
        clock.set_text(f"Physical time = {t:.2f} s    ·    positive displacement points inward")
        status.set_text("   |   ".join(stopped))
        return (pressure_line, *shape_lines, *history_lines, *dots, clock, status)
    return _save_animation(fig, update, times, f"animation_03_response_{case}", output_dir,
                           max_frames, [flow, *structures],
                           selected_width_y_m=width, width_selection="largest absolute displacement in baseline response",
                           all_sampled_widths_y_m=widths, equal_displacement_height_scales=True,
                           material_variants=[a["meta"] for a in structures],
                           temporal_interpolation="linear between saved structural states; terminated states held",
                           history_domain="maximum over all sampled strips, ending at first strip termination",
                           fixed_air_boundary=True, pressure_only=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=["geometry", "summary", "flow", "load", "temperature", "structure", "fine", "release", "static", "all"], default="fine")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    parser.add_argument("--max-frames", type=int, default=None,
                        help="Use a constant stride through saved frames, retaining physical playback speed")
    parser.add_argument("--case", default="control_both", help="Source flow case for the structural animation")
    args = parser.parse_args()
    if args.only == "fine":
        print("Rendering finest-grid geometry", flush=True)
        geometry(args.data_dir, args.output_dir, source_case="grid_fine_both")
        for label, render in (("flow", flow_controls), ("curtain pressure", pressure_maps),
                              ("temperature", temperature_controls)):
            print(f"Rendering finest-grid {label}", flush=True)
            render(args.data_dir, args.output_dir, args.max_frames, cases=FINE_CASES)
    if args.only == "release":
        print("Rendering separate mean-load release comparison", flush=True)
        release_comparison(args.data_dir, args.output_dir, args.max_frames)
    if args.only in ("geometry", "static", "all"):
        print("Rendering geometry", flush=True)
        geometry(args.data_dir, args.output_dir)
    if args.only in ("summary", "static", "all"):
        print("Rendering control summary", flush=True)
        control_summary(args.data_dir, args.output_dir)
    if args.only in ("flow", "all"):
        print("Rendering computed flow", flush=True)
        flow_controls(args.data_dir, args.output_dir, args.max_frames)
    if args.only in ("load", "all"):
        print("Rendering curtain pressure maps", flush=True)
        pressure_maps(args.data_dir, args.output_dir, args.max_frames)
    if args.only in ("temperature", "all"):
        print("Rendering computed air temperature", flush=True)
        temperature_controls(args.data_dir, args.output_dir, args.max_frames)
    if args.only == "structure":
        print("Rendering one-way structural response", flush=True)
        structural_response(args.case, data_dir=args.data_dir, output_dir=args.output_dir, max_frames=args.max_frames)


if __name__ == "__main__":
    main()
