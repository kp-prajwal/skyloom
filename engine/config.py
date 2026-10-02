from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DEFAULTS = {
    "studio": {
        "name": "Skyloom",
        "tagline": "Weather suggests. Models propose. Skyloom decides.",
        "timezone": "America/Chicago",
    },
    "model": {
        "provider": "cloudflare",
        "name": "@cf/openai/gpt-oss-20b",
        "director_enabled": True,
        "critic_enabled": True,
    },
    "archive": {
        "recent_days": 90,
        "rendered_images_in_git": False,
        "retain_recipes_forever": True,
    },
}


@lru_cache(maxsize=1)
def load_config() -> dict:
    config = {section: values.copy() for section, values in DEFAULTS.items()}
    path = ROOT / "skyloom.json"
    if not path.exists():
        return config
    with path.open(encoding="utf-8") as handle:
        supplied = json.load(handle)
    for section, values in supplied.items():
        if isinstance(values, dict):
            config.setdefault(section, {}).update(values)
    return config
