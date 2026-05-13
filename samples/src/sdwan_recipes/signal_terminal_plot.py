"""Single-line Braille sparkline for dBm-style signals (Unicode + ANSI)."""

from __future__ import annotations

import os
from typing import Literal, Sequence

Scale = Literal["rsrp", "rssi"]

_RESET = "\033[0m"


def _no_color() -> bool:
    # https://no-color.org/ — presence of NO_COLOR disables ANSI color.
    return "NO_COLOR" in os.environ


def _resample(values: Sequence[float], width: int) -> list[float]:
    """Resample to exactly ``width`` points (linear interpolation, endpoints inclusive)."""
    if not values or width < 1:
        return []
    n = len(values)
    if n == 1:
        return [float(values[0])] * width
    if width == 1:
        return [float(values[0])]
    out: list[float] = []
    for i in range(width):
        t = i * (n - 1) / (width - 1)
        lo = int(t)
        hi = min(lo + 1, n - 1)
        frac = t - lo
        vl, vh = float(values[lo]), float(values[hi])
        out.append(vl * (1.0 - frac) + vh * frac)
    return out


def _quality_color(v: float, scale: Scale) -> tuple[int, int, int]:
    """RGB for signal quality (strong = green, medium = yellow, weak = red)."""
    if scale == "rsrp":
        if v >= -80:
            return (60, 185, 95)
        if v >= -95:
            return (220, 190, 60)
        return (215, 75, 75)
    if v >= -65:
        return (60, 185, 95)
    if v >= -80:
        return (220, 190, 60)
    return (215, 75, 75)


def _rgb_esc(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def _column_braille_bits(t: float, *, left: bool) -> int:
    """Map height t in [0,1] (bottom=0, top=1) to Braille dot bits for one 2×4 half-column."""
    level = max(0, min(4, int(round(t * 4))))
    if left:
        table = (0, 0x40, 0x40 | 0x04, 0x40 | 0x04 | 0x02, 0x40 | 0x04 | 0x02 | 0x01)
        return table[level]
    table = (0, 0x80, 0x80 | 0x20, 0x80 | 0x20 | 0x10, 0x80 | 0x20 | 0x10 | 0x08)
    return table[level]


def _braille_char(t_left: float, t_right: float) -> str:
    bits = _column_braille_bits(t_left, left=True) | _column_braille_bits(t_right, left=False)
    return chr(0x2800 + bits)


def signal_strength_terminal_plot(
    values: Sequence[float],
    *,
    width: int = 56,
    scale: Scale = "rssi",
    use_color: bool | None = None,
) -> str:
    """
    Render a one-line Braille sparkline (time left → right, strength vertical).

    Two samples map to each Braille character (2×4 dot grid per cell). Colors
    follow absolute dBm bands for ``scale`` (red / yellow / green).

    Returns a single line (no newline). Empty input returns a dim placeholder
    row of blank Braille cells.
    """
    if use_color is None:
        use_color = not _no_color()

    w = max(8, min(int(width), 256))
    if not values:
        dim = _rgb_esc(120, 120, 120) if use_color else ""
        rs = _RESET if use_color else ""
        return f"{dim}{chr(0x2800) * w}{rs}"

    n_dots = 2 * w
    raw = _resample(values, n_dots)
    lo, hi = min(raw), max(raw)
    if hi == lo:
        tvals = [0.5] * n_dots
    else:
        tvals = [(v - lo) / (hi - lo) for v in raw]

    out: list[str] = []
    for i in range(w):
        tl, tr = tvals[2 * i], tvals[2 * i + 1]
        ch = _braille_char(tl, tr)
        v_mid = 0.5 * (raw[2 * i] + raw[2 * i + 1])
        if use_color:
            r, g, b = _quality_color(v_mid, scale)
            esc = _rgb_esc(r, g, b)
            out.append(f"{esc}{ch}{_RESET}")
        else:
            out.append(ch)

    return "".join(out)
