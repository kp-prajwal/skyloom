from __future__ import annotations

import json
from pathlib import Path

from .config import load_config


def _public_recipe(record: dict) -> dict:
    winner = record["winner"]
    winner_score = record["candidates"][winner]["score"]
    return {
        "date": record["date"],
        "seed": record["date"],
        "title": record["title"],
        "city": record["weather"]["city"],
        "country": record["weather"]["country"],
        "temperature_c": record["weather"]["temperature_c"],
        "weather": {
            "weather_code": record["weather"]["weather_code"],
            "wind_kph": record["weather"]["wind_kph"],
            "wind_direction": record["weather"]["wind_direction"],
            "precipitation_mm": record["weather"]["precipitation_mm"],
        },
        "poem": record["poem"],
        "winner": winner,
        "score": winner_score["total"],
        "palette": record["palette"],
        "genome": record["winning_genome"],
        "direction_source": record["direction_source"],
    }


def rebuild(root: Path) -> None:
    recipes = []
    for path in sorted((root / "data" / "days").glob("*.json"), reverse=True):
        with path.open(encoding="utf-8") as handle:
            record = json.load(handle)
        recipes.append(_public_recipe(record))

    public_data = root / "docs" / "data"
    archive_dir = public_data / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # This file stays bounded even after years of daily generations.
    recent_days = max(1, int(load_config()["archive"]["recent_days"]))
    (public_data / "recent.json").write_text(
        json.dumps(recipes[:recent_days], separators=(",", ":")) + "\n", encoding="utf-8"
    )

    months: dict[str, list[dict]] = {}
    for recipe in recipes:
        months.setdefault(recipe["date"][:7], []).append(recipe)
    for month, items in months.items():
        (archive_dir / f"{month}.json").write_text(
            json.dumps(items, separators=(",", ":")) + "\n", encoding="utf-8"
        )
    (public_data / "archive-index.json").write_text(
        json.dumps(sorted(months, reverse=True), separators=(",", ":")) + "\n", encoding="utf-8"
    )
