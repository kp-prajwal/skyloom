from __future__ import annotations

import json
import os
import re
from urllib.request import Request, urlopen

from .config import load_config


MODEL = os.getenv("CLOUDFLARE_MODEL", load_config()["model"]["name"])


def available() -> bool:
    return bool(os.getenv("CLOUDFLARE_ACCOUNT_ID") and os.getenv("CLOUDFLARE_API_TOKEN"))


def _extract_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I | re.S)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Model response did not contain a JSON object")
    return json.loads(text[start : end + 1])


def _run(messages: list[dict], max_tokens: int, seed: int) -> dict:
    account = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    token = os.environ["CLOUDFLARE_API_TOKEN"]
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    body = json.dumps({
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.72,
        "seed": max(1, seed % 9_999_999_999),
    }).encode("utf-8")
    request = Request(
        url,
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urlopen(request, timeout=45) as response:
        payload = json.load(response)
    if not payload.get("success", True):
        raise RuntimeError(str(payload.get("errors", "Cloudflare AI call failed")))
    result = payload.get("result", payload)
    text = result.get("response") or result.get("output_text")
    if not text:
        raise ValueError("Cloudflare response did not contain generated text")
    return _extract_json(text)


def direct(weather: dict, city: dict, champion: dict, recent: list[dict], seed: int) -> dict:
    prompt = {
        "weather": weather,
        "verified_city_context": {
            "brief": city.get("brief"),
            "important_fact": city.get("fact"),
        },
        "current_genome": champion,
        "recent_titles": [item.get("title") for item in recent[-7:]],
        "allowed_mutations": {
            "stroke_count": [-120, 120], "steps": [-4, 4], "flow_scale": [-0.003, 0.003],
            "curl": [-0.5, 0.5], "step_length": [-1.5, 1.5], "stroke_width": [-0.3, 0.3],
            "opacity": [-0.08, 0.08], "horizon": [-0.05, 0.05],
            "light_x": [-0.08, 0.08], "light_y": [-0.08, 0.08],
        },
    }
    return _run([
        {"role": "system", "content": (
            "You art-direct a deterministic city data portrait. Return JSON only with keys title, poem, palette, "
            "mutation, rationale. poem must be an array of exactly 3 short lines. palette must contain exactly "
            "4 hex colors. mutation may contain only allowed gene names and must respect the supplied delta ranges. "
            "Use the verified city context only for atmosphere; do not introduce new factual claims."
        )},
        {"role": "user", "content": json.dumps(prompt, separators=(",", ":"))},
    ], max_tokens=430, seed=seed)


def critique(weather: dict, winner: dict, components: dict, seed: int) -> dict:
    prompt = {"weather": weather, "winning_genome": winner, "measured_scores": components}
    return _run([
        {"role": "system", "content": (
            "You are a metrics critic. You cannot see the image. Based only on the measurements, return JSON only "
            "with keys verdict (one sentence) and mutation (an object of small numeric deltas). Allowed genes: "
            "stroke_count, steps, flow_scale, curl, step_length, stroke_width, opacity, horizon, light_x, light_y. "
            "Keep every delta below 5 percent of the current value. Your proposal is a hypothesis for tomorrow, not a decision."
        )},
        {"role": "user", "content": json.dumps(prompt, separators=(",", ":"))},
    ], max_tokens=220, seed=seed + 17)
