from __future__ import annotations

from copy import deepcopy
import hashlib
import random


DEFAULT_GENOME = {
    "stroke_count": 520,
    "steps": 24,
    "flow_scale": 0.011,
    "curl": 1.8,
    "step_length": 7.5,
    "stroke_width": 1.35,
    "opacity": 0.27,
    "horizon": 0.58,
    "light_x": 0.67,
    "light_y": 0.34,
}

BOUNDS = {
    "stroke_count": (160, 1100),
    "steps": (10, 42),
    "flow_scale": (0.004, 0.028),
    "curl": (0.3, 4.5),
    "step_length": (3.0, 14.0),
    "stroke_width": (0.45, 3.2),
    "opacity": (0.07, 0.70),
    "horizon": (0.32, 0.76),
    "light_x": (0.08, 0.92),
    "light_y": (0.08, 0.70),
}

INTEGER_GENES = {"stroke_count", "steps"}

MAX_DAILY_DELTA = {
    "stroke_count": 120,
    "steps": 4,
    "flow_scale": 0.003,
    "curl": 0.5,
    "step_length": 1.5,
    "stroke_width": 0.3,
    "opacity": 0.08,
    "horizon": 0.05,
    "light_x": 0.08,
    "light_y": 0.08,
}


def clamp_genome(candidate: dict | None) -> dict:
    candidate = candidate or {}
    clean = {}
    for gene, default in DEFAULT_GENOME.items():
        low, high = BOUNDS[gene]
        try:
            value = float(candidate.get(gene, default))
        except (TypeError, ValueError):
            value = default
        value = min(high, max(low, value))
        clean[gene] = int(round(value)) if gene in INTEGER_GENES else round(value, 5)
    return clean


def mutate(base: dict, deltas: dict | None) -> dict:
    result = deepcopy(clamp_genome(base))
    for gene, delta in (deltas or {}).items():
        if gene not in BOUNDS:
            continue
        try:
            result[gene] += float(delta)
        except (TypeError, ValueError):
            continue
    return clamp_genome(result)


def clamp_deltas(deltas: dict | None, scale: float = 1.0) -> dict:
    clean = {}
    if not isinstance(deltas, dict):
        return clean
    for gene, raw_value in deltas.items():
        if gene not in MAX_DAILY_DELTA:
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        limit = MAX_DAILY_DELTA[gene] * scale
        clean[gene] = round(min(limit, max(-limit, value)), 6)
    return clean


def explore(base: dict, seed: str) -> dict:
    rng = random.Random(stable_seed(seed))
    spans = {gene: high - low for gene, (low, high) in BOUNDS.items()}
    deltas = {}
    for gene, span in spans.items():
        if rng.random() < 0.72:
            deltas[gene] = rng.uniform(-0.075, 0.075) * span
    return mutate(base, deltas)


def stable_seed(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def normalized_distance(left: dict, right: dict) -> float:
    total = 0.0
    count = 0
    for gene, (low, high) in BOUNDS.items():
        span = high - low
        total += ((float(left[gene]) - float(right[gene])) / span) ** 2
        count += 1
    return (total / max(count, 1)) ** 0.5
