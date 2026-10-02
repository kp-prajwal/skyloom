from __future__ import annotations

import math

from .genome import normalized_distance


def _band(value: float, target: float, tolerance: float) -> float:
    return max(0.0, 1.0 - abs(value - target) / tolerance)


def _luminance(color: str) -> float:
    try:
        r, g, b = (int(color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    except (ValueError, TypeError):
        return 0.5
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def score(genome: dict, palette: list[str], weather: dict, recent_genomes: list[dict]) -> dict:
    coverage_estimate = min(
        1.0,
        genome["stroke_count"] * genome["steps"] * genome["step_length"] * genome["stroke_width"] / (896 * 896),
    )
    coverage = _band(coverage_estimate, 0.23, 0.19)
    stroke_length = _band(genome["steps"] * genome["step_length"], 190, 145)
    third_points = [(1 / 3, 1 / 3), (2 / 3, 1 / 3)]
    light_distance = min(math.dist((genome["light_x"], genome["light_y"]), point) for point in third_points)
    composition = max(0.0, 1.0 - light_distance / 0.32)
    lum = [_luminance(c) for c in palette]
    contrast = min(1.0, (max(lum) - min(lum)) / 0.62)
    wind_target = min(float(weather.get("wind_kph", 0)), 55) / 55
    wind_shape = _band(genome["curl"] / 4.5, 0.18 + wind_target * 0.48, 0.42)
    weather_fit = wind_shape
    if recent_genomes:
        novelty = min(1.0, min(normalized_distance(genome, old) for old in recent_genomes) / 0.16)
    else:
        novelty = 0.72
    components = {
        "composition": round(composition * 10, 3),
        "coverage": round(coverage * 10, 3),
        "stroke_length": round(stroke_length * 10, 3),
        "contrast": round(contrast * 10, 3),
        "weather_fit": round(weather_fit * 10, 3),
        "novelty": round(novelty * 10, 3),
    }
    total = (
        composition * 0.22 + coverage * 0.18 + stroke_length * 0.15 + contrast * 0.15
        + weather_fit * 0.18 + novelty * 0.12
    ) * 10
    return {"total": round(total, 3), "components": components}


def fallback_critique(components: dict) -> dict:
    weakest = min(components, key=components.get)
    proposals = {
        "composition": {"light_x": -0.015, "light_y": 0.01},
        "coverage": {"stroke_count": 24, "opacity": 0.008},
        "stroke_length": {"step_length": 0.3},
        "contrast": {"opacity": 0.012},
        "weather_fit": {"curl": 0.08},
        "novelty": {"flow_scale": 0.0005, "horizon": -0.01},
    }
    return {
        "verdict": f"The measured {weakest.replace('_', ' ')} score has the clearest room to improve.",
        "mutation": proposals[weakest],
        "source": "fallback",
    }

