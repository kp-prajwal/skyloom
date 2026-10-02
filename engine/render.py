from __future__ import annotations

import html
import math
import random

from .genome import stable_seed


WIDTH = 896
HEIGHT = 896


def _hex(color: str, fallback: str) -> str:
    if isinstance(color, str) and len(color) == 7 and color.startswith("#"):
        try:
            int(color[1:], 16)
            return color.lower()
        except ValueError:
            pass
    return fallback


def clean_palette(palette: list | None) -> list[str]:
    defaults = ["#17263f", "#527c94", "#e19a67", "#f5d7a4"]
    supplied = palette if isinstance(palette, list) else []
    return [_hex(supplied[i], defaults[i]) if i < len(supplied) else defaults[i] for i in range(4)]


def render_svg(genome: dict, palette: list, weather: dict, seed: str, title: str) -> str:
    colors = clean_palette(palette)
    rng = random.Random(stable_seed(seed))
    horizon_y = int(float(genome["horizon"]) * HEIGHT)
    light_x = float(genome["light_x"]) * WIDTH
    light_y = float(genome["light_y"]) * HEIGHT
    flow_scale = float(genome["flow_scale"])
    curl = float(genome["curl"])
    paths = []

    for index in range(int(genome["stroke_count"])):
        x = rng.uniform(-40, WIDTH + 40)
        y = rng.uniform(horizon_y * 0.32, HEIGHT + 30)
        points = [(x, y)]
        phase = rng.uniform(0, math.tau)
        for step in range(int(genome["steps"])):
            field = (
                math.sin((x + phase * 40) * flow_scale * 1.7)
                + math.cos((y - phase * 25) * flow_scale * 1.15)
                + 0.55 * math.sin((x + y) * flow_scale * 0.62 + phase)
            )
            pull = math.atan2(light_y - y, light_x - x) * 0.075
            angle = field * curl + pull - 0.42
            stride = float(genome["step_length"]) * (0.82 + rng.random() * 0.35)
            x += math.cos(angle) * stride
            y += math.sin(angle) * stride
            points.append((x, y))
        d = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in points)
        color = colors[1 + (index % 3)]
        width = float(genome["stroke_width"]) * rng.uniform(0.72, 1.35)
        opacity = float(genome["opacity"]) * rng.uniform(0.72, 1.08)
        paths.append(f'<path d="{d}" stroke="{color}" stroke-width="{width:.2f}" opacity="{opacity:.3f}"/>')

    effects = _weather_effects(weather, colors, rng)
    safe_title = html.escape(title)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{safe_title}">
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{colors[0]}"/>
    <stop offset="{float(genome['horizon']):.2f}" stop-color="{colors[1]}"/>
    <stop offset="1" stop-color="{colors[2]}"/>
  </linearGradient>
  <radialGradient id="light">
    <stop offset="0" stop-color="{colors[3]}" stop-opacity=".92"/>
    <stop offset="1" stop-color="{colors[3]}" stop-opacity="0"/>
  </radialGradient>
  <filter id="soft"><feGaussianBlur stdDeviation="24"/></filter>
</defs>
<rect width="896" height="896" fill="url(#sky)"/>
<circle cx="{light_x:.1f}" cy="{light_y:.1f}" r="190" fill="url(#light)" filter="url(#soft)"/>
<g fill="none" stroke-linecap="round">{''.join(paths)}</g>
{effects}
<rect x="18" y="18" width="860" height="860" rx="8" fill="none" stroke="{colors[3]}" opacity=".16"/>
</svg>'''


def _weather_effects(weather: dict, colors: list[str], rng: random.Random) -> str:
    code = int(weather.get("weather_code", 0))
    wind_angle = math.radians(float(weather.get("wind_direction", 225)) - 90)
    if 71 <= code <= 77 or code in {85, 86}:
        flakes = []
        for _ in range(90):
            flakes.append(
                f'<circle cx="{rng.uniform(0, WIDTH):.1f}" cy="{rng.uniform(0, HEIGHT):.1f}" '
                f'r="{rng.uniform(0.8, 3.4):.1f}" fill="{colors[3]}" opacity=".5"/>'
            )
        return '<g>' + "".join(flakes) + "</g>"
    if 51 <= code <= 67 or 80 <= code <= 82:
        marks = []
        for _ in range(115):
            x, y = rng.uniform(0, WIDTH), rng.uniform(0, HEIGHT)
            length = rng.uniform(9, 28)
            marks.append(
                f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + math.cos(wind_angle) * length:.1f}" '
                f'y2="{y + math.sin(wind_angle) * length:.1f}" stroke="{colors[3]}" opacity=".25"/>'
            )
        return '<g stroke-width="1.2">' + "".join(marks) + "</g>"
    if code in {45, 48}:
        return '<rect width="896" height="896" fill="#dbe3e6" opacity=".22"/>'
    return ""
