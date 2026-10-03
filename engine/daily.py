from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys

from . import llm
from .city import city_context
from .config import load_config
from .gallery import rebuild
from .genome import DEFAULT_GENOME, clamp_deltas, clamp_genome, explore, mutate, stable_seed
from .render import clean_palette
from .score import fallback_critique, score
from .weather import city_for_day, fallback_direction, fallback_weather, fetch_weather


ROOT = Path(__file__).resolve().parents[1]
CONFIG = load_config()


def read_json(path: Path, default):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sanitize_direction(raw: dict, fallback: dict) -> dict:
    title = str(raw.get("title", fallback["title"]))[:100]
    palette = clean_palette(raw.get("palette"))
    mutation = clamp_deltas(raw.get("mutation"))
    return {
        "title": title,
        "palette": palette,
        "mutation": mutation,
        "rationale": str(raw.get("rationale", fallback["rationale"]))[:400],
        "source": raw.get("source", "cloudflare"),
    }


def run(day: date, offline: bool = False, force: bool = False) -> dict:
    day_key = day.isoformat()
    day_path = ROOT / "data" / "days" / f"{day_key}.json"
    if day_path.exists() and not force:
        print(f"{day_key} already exists; nothing to do.")
        return read_json(day_path, {})

    errors = []
    city = city_for_day(day)
    if offline:
        weather = fallback_weather(city, "offline mode")
    else:
        try:
            weather = fetch_weather(city)
        except Exception as exc:
            errors.append({"component": "weather", "message": str(exc)[:240]})
            weather = fallback_weather(city, str(exc)[:160])

    context = city_context(city, offline=offline)
    if context.get("source_error"):
        errors.append({"component": "city", "message": context["source_error"]})

    champion_state = read_json(ROOT / "data" / "champion.json", {})
    champion = clamp_genome(champion_state.get("genome", DEFAULT_GENOME))
    previous_critic = champion_state.get("critic_mutation", {})
    recent_records = []
    for path in sorted((ROOT / "data" / "days").glob("*.json"))[-7:]:
        recent_records.append(read_json(path, {}))
    recent_genomes = [item.get("winning_genome") for item in recent_records if item.get("winning_genome")]

    fallback = fallback_direction(weather)
    direction = fallback
    if not offline and CONFIG["model"]["director_enabled"] and llm.available():
        try:
            direction = sanitize_direction(
                llm.direct(weather, context, champion, recent_records, stable_seed(day_key)), fallback
            )
        except Exception as exc:
            errors.append({"component": "director", "message": str(exc)[:240]})
    direction = sanitize_direction(direction, fallback)

    genomes = {
        "champion": champion,
        "director": mutate(champion, direction["mutation"]),
        "critic": mutate(champion, previous_critic),
        "explorer": explore(champion, day_key),
    }
    candidates = {}
    for name, genome in genomes.items():
        candidate_score = score(genome, direction["palette"], weather, recent_genomes)
        candidates[name] = {"genome": genome, "score": candidate_score}

    winner = max(candidates, key=lambda name: candidates[name]["score"]["total"])
    winning_genome = candidates[winner]["genome"]
    critique = fallback_critique(candidates[winner]["score"]["components"])
    if not offline and CONFIG["model"]["critic_enabled"] and llm.available():
        try:
            raw_critique = llm.critique(
                weather, winning_genome, candidates[winner]["score"]["components"], stable_seed(day_key)
            )
            critique = {
                "verdict": str(raw_critique.get("verdict", critique["verdict"]))[:400],
                "mutation": clamp_deltas(raw_critique.get("mutation", critique["mutation"]), scale=0.5),
                "source": "cloudflare",
            }
        except Exception as exc:
            errors.append({"component": "critic", "message": str(exc)[:240]})

    # Persist the winning recipe and score summaries, not rendered images or
    # losing genomes. The artwork can be reconstructed from this small record.
    public_candidates = {
        name: {"score": candidate["score"]} for name, candidate in candidates.items()
    }
    record = {
        "date": day_key,
        "title": direction["title"],
        "palette": direction["palette"],
        "weather": weather,
        "city": context,
        "direction_source": direction["source"],
        "direction_rationale": direction["rationale"],
        "candidates": public_candidates,
        "winner": winner,
        "winning_genome": winning_genome,
        "critique": critique,
        "errors": errors,
    }
    write_json(day_path, record)
    write_json(ROOT / "data" / "champion.json", {
        "generation": int(champion_state.get("generation", 0)) + 1,
        "updated": day_key,
        "genome": winning_genome,
        "critic_mutation": critique.get("mutation", {}),
    })
    rebuild(ROOT)
    print("Candidate measurements: " + json.dumps({name: item["score"] for name, item in candidates.items()}))
    print(f"Published {day_key}: {direction['title']} ({winner}, {candidates[winner]['score']['total']}/10)")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate one Skyloom artwork")
    parser.add_argument("--date", help="YYYY-MM-DD; defaults to today")
    parser.add_argument("--offline", action="store_true", help="Do not call weather or LLM services")
    parser.add_argument("--force", action="store_true", help="Replace an existing day's record")
    args = parser.parse_args(argv)
    selected = date.fromisoformat(args.date) if args.date else date.today()
    run(selected, offline=args.offline, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
