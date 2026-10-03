from __future__ import annotations

import json
from pathlib import Path

from .config import load_config


def _public_recipe(record: dict) -> dict:
    winner = record["winner"]
    winner_score = record["candidates"][winner]["score"]
    weather = record["weather"]
    city_context = record.get("city", {
        "brief": f"{weather['city']} is today's Skyloom city portrait.",
        "fact": "A verified city fact will appear on the next live generation.",
        "source": "https://en.wikipedia.org/",
        "fact_source": "https://en.wikipedia.org/",
        "source_label": "Wikipedia",
    })
    return {
        "date": record["date"],
        "seed": record["date"],
        "title": record["title"],
        "city": record["weather"]["city"],
        "country": record["weather"]["country"],
        "country_name": city_context.get("country_name", record["weather"]["country"]),
        "sample": bool(record.get("sample", False)),
        "temperature_c": weather["temperature_c"],
        "apparent_temperature_c": weather.get("apparent_temperature_c", weather["temperature_c"]),
        "relative_humidity": weather.get("relative_humidity", 50),
        "local_time": weather.get("local_time", "—"),
        "timezone": weather.get("timezone", "local"),
        "sunrise": weather.get("sunrise", "—"),
        "sunset": weather.get("sunset", "—"),
        "daylight_minutes": weather.get("daylight_minutes", 720),
        "coordinates": {"latitude": weather["latitude"], "longitude": weather["longitude"]},
        "city_context": city_context,
        "weather": {
            "weather_code": weather["weather_code"],
            "cloud_cover": weather.get("cloud_cover", 50),
            "wind_kph": weather["wind_kph"],
            "wind_direction": weather["wind_direction"],
            "precipitation_mm": weather["precipitation_mm"],
        },
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
