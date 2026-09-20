#!/usr/bin/env python3
"""Shared design tokens and helpers for the Messi editorial visual system."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import html
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-messi-style")

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, findfont
from matplotlib.lines import Line2D


STATIC_CANVAS = (1600, 900)
ANIMATION_CANVAS = (1400, 900)
STATIC_MARGIN_X = 80

COLORS = {
    "background": "#FFFFFF",
    "warm_background": "#FAFAF7",
    "ink": "#18212B",
    "navy": "#34536F",
    "muted_dark": "#536273",
    "muted": "#657381",
    "line": "#D8DEE4",
    "panel": "#F7F9FB",
    "pitch": "#F4F7F9",
    "blue": "#4C78A8",
    "blue_fill": "#DCE8F3",
    "red": "#C84C4C",
    "red_fill": "#F5E2E2",
    "neutral": "#C8CDD2",
    "teal": "#75B7B2",
    "yellow": "#F2C14E",
    "orange": "#E6863B",
}

ANIMATION_COLORS = {
    "background": "#FCFCFA",
    "ink": "#1D2733",
    "muted": "#65758A",
    "grid": "#D6DEE8",
    "panel": "#F5F8FB",
    "pitch": "#EEF4F8",
    "blue": "#4C7FB3",
    "blue_fill": "#DCE8F3",
    "red": "#CF4C4C",
    "red_fill": "#F5DEDE",
}

CONCEPTUAL_COLORS = {
    "background": "#FAFAF7",
    "ink": "#18212B",
    "muted": "#667586",
    "line": "#D7DEE5",
    "panel": "#FFFFFF",
    "pitch": "#F4F7F9",
    "blue": "#4C78A8",
    "blue_fill": "#DCE8F3",
    "red": "#C84C4C",
    "red_fill": "#F5E2E2",
}

ILLUSTRATION_COLORS = {
    "paper": "#EEE9DB",
    "field_light": "#9AAE78",
    "field_mid": "#829963",
    "field_dark": "#687F50",
    "sky_blue": "#75B5D4",
}

TYPE = {
    "eyebrow": 18,
    "title": 43,
    "subtitle": 23,
    "panel_header": 16,
    "object_label": 20,
    "axis_label": 18,
    "tick": 15,
    "mark_value": 16,
    "large_value": 72,
    "note": 14,
}


def _font(family: str, weight: str = "normal") -> FontProperties:
    path = findfont(FontProperties(family=family, weight=weight), fallback_to_default=True)
    return FontProperties(fname=path)


SANS = _font("DejaVu Sans")
SANS_BOLD = _font("DejaVu Sans", "bold")
SERIF_BOLD = _font("DejaVu Serif", "bold")


def new_static_figure() -> plt.Figure:
    """Return the canonical 1600 × 900 Matplotlib figure."""
    return plt.figure(figsize=(16, 9), dpi=100, facecolor=COLORS["background"])


def add_header(
    fig: plt.Figure,
    eyebrow: str,
    title: str,
    subtitle: str,
    *,
    title_size: int = TYPE["title"],
) -> None:
    """Add the fixed three-level editorial header."""
    fig.text(0.05, 0.925, eyebrow.upper(), color=COLORS["muted_dark"], fontsize=TYPE["eyebrow"], fontproperties=SANS_BOLD)
    fig.text(0.05, 0.855, title, color=COLORS["ink"], fontsize=title_size, fontproperties=SERIF_BOLD)
    fig.text(0.05, 0.805, subtitle, color=COLORS["muted_dark"], fontsize=TYPE["subtitle"], fontproperties=SANS)


def style_axes(
    ax: plt.Axes,
    *,
    horizontal_grid: bool = True,
    xlabel: str | None = None,
    ylabel: str | None = None,
) -> None:
    """Apply the canonical quiet-axis treatment."""
    if horizontal_grid:
        ax.grid(axis="y", color=COLORS["line"], linewidth=1.0, zorder=0)
    ax.tick_params(axis="both", colors=COLORS["muted"], labelsize=TYPE["tick"], length=0, pad=10)
    for label in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        label.set_fontproperties(SANS)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(COLORS["line"])
    ax.spines["bottom"].set_color(COLORS["line"])
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=TYPE["axis_label"], color=COLORS["ink"], labelpad=18, fontproperties=SANS_BOLD)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=TYPE["axis_label"] - 1, color=COLORS["ink"], labelpad=18, fontproperties=SANS_BOLD)


def add_footer(
    fig: plt.Figure,
    left: str,
    right: str | None = None,
    *,
    rule_y: float = 0.105,
    text_y: float = 0.055,
) -> None:
    """Add a thin rule and aligned method/source text."""
    fig.lines.append(Line2D([0.05, 0.95], [rule_y, rule_y], transform=fig.transFigure, color=COLORS["line"], linewidth=1.0))
    fig.text(0.05, text_y, left, color=COLORS["muted"], fontsize=TYPE["note"], fontproperties=SANS)
    if right:
        fig.text(0.95, text_y, right, ha="right", color=COLORS["muted"], fontsize=TYPE["note"], fontproperties=SANS)


def svg_text(
    x: float,
    y: float,
    value: str,
    size: int,
    *,
    fill: str = COLORS["ink"],
    weight: int = 400,
    family: str = "sans",
    anchor: str = "start",
    italic: bool = False,
) -> str:
    """Return an SVG text element using the canonical font stack."""
    face = (
        "DejaVu Sans, Arial, Helvetica, sans-serif"
        if family == "sans"
        else "DejaVu Serif, Georgia, Times New Roman, serif"
    )
    style = "italic" if italic else "normal"
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-family="{face}" '
        f'font-size="{size}" font-weight="{weight}" font-style="{style}" '
        f'text-anchor="{anchor}">{html.escape(str(value))}</text>'
    )


def svg_panel(x: float, y: float, width: float, height: float, *, radius: float = 8) -> str:
    """Return a flat pale panel with a cool-gray border."""
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" '
        f'fill="{COLORS["panel"]}" stroke="{COLORS["line"]}" stroke-width="1.5"/>'
    )


def assert_no_unknown_colors(colors: Iterable[str]) -> None:
    """Raise when a figure silently introduces a color outside the system."""
    allowed = (
        {value.upper() for value in COLORS.values()}
        | {value.upper() for value in ANIMATION_COLORS.values()}
        | {value.upper() for value in CONCEPTUAL_COLORS.values()}
        | {value.upper() for value in ILLUSTRATION_COLORS.values()}
        | {"#FFFFFF"}
    )
    unknown = sorted({str(color).upper() for color in colors} - allowed)
    if unknown:
        raise ValueError(f"Colors outside the Messi style system: {', '.join(unknown)}")


def render_reference_plate(output: str | Path) -> Path:
    """Render a deterministic palette and type smoke test."""
    output = Path(output)
    fig = new_static_figure()
    add_header(fig, "EDITORIAL VISUAL SYSTEM", "Messi image style", "Palette, hierarchy and restrained emphasis")
    keys = ["ink", "muted_dark", "muted", "line", "blue", "blue_fill", "red", "red_fill", "panel", "pitch"]
    for index, key in enumerate(keys):
        row, col = divmod(index, 5)
        x = 0.06 + col * 0.18
        y = 0.62 - row * 0.20
        fig.patches.append(plt.Rectangle((x, y), 0.13, 0.10, transform=fig.transFigure, facecolor=COLORS[key], edgecolor=COLORS["line"], linewidth=1))
        fig.text(x, y - 0.035, key.replace("_", " "), color=COLORS["muted"], fontsize=14, fontproperties=SANS)
    add_footer(fig, "Deterministic smoke test · not an article figure", "1600 × 900")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=100, facecolor=COLORS["background"])
    plt.close(fig)
    return output


if __name__ == "__main__":
    render_reference_plate(Path(__file__).resolve().parent / "messi-style-smoke-test.png")
