# Skyloom

> Weather suggests. Models propose. Skyloom decides.

Skyloom publishes one weather-driven generative artwork and poem each day. An open-weight cloud model proposes creative direction; deterministic code breeds and measures four candidates; the strongest becomes tomorrow's champion.

The system uses GitHub Actions, GitHub Pages, Open-Meteo, and `gpt-oss-20b` through Cloudflare Workers AI. It has no always-on server, paid image model, or database.

## One-command cloud setup

Before running setup, complete two one-time prerequisites:

1. Install and sign in to the GitHub CLI with `gh auth login`.
2. In Cloudflare, open **Workers AI → Use REST API**, create a Workers AI API token, and keep the token and Account ID ready.

Then run:

```bash
./scripts/setup.sh
```

The script tests Skyloom, creates a public GitHub repository, pushes the project, stores the Cloudflare credentials as encrypted GitHub secrets, enables Pages, and launches the first cloud generation. It is designed to be safely rerun after an interrupted setup.

Never paste the Cloudflare token into source code, `.env`, configuration files, commit messages, or chat. The setup script reads it through a hidden terminal prompt and sends it directly to GitHub Secrets.

## Test locally

Python 3.9 or newer is sufficient; the engine has no package dependencies.

```bash
python3 -m unittest discover -s tests -v
python3 -m engine.daily --offline
python3 -m http.server 8000 --directory docs
```

Open `http://localhost:8000`.

## The daily loop

1. Select the day's city.
2. Read current weather from Open-Meteo.
3. Ask the open-weight model for a palette, title, poem, and bounded mutation.
4. Breed champion, director, previous-critic, and explorer candidates.
5. Score composition, coverage, stroke length, contrast, weather fit, and novelty.
6. Save the winning recipe.
7. Let a metrics-only critic propose a challenger for tomorrow.
8. Rebuild the small recent and monthly archive manifests.

If weather or model inference fails, deterministic fallbacks still publish the day's recipe and record the error.

## Retention strategy

Skyloom does not commit rendered SVG or PNG files. The browser reconstructs each artwork from a small recipe containing its date seed, palette, genome, weather, poem, and score.

- Winning recipes are retained permanently.
- `docs/data/recent.json` is capped at 90 recipes.
- Older recipes are grouped into monthly manifests under `docs/data/archive/`.
- Thumbnails render lazily only when they approach the viewport.
- Losing genomes are written to the temporary workflow log, not permanent storage.
- Daily records keep candidate score summaries for auditability.

This changes expected archive growth from roughly 80 MB of SVG files per year to only a few megabytes of JSON recipes per year.

## Cost controls

- Keep Cloudflare on **Workers Free**.
- Do not enable Workers Paid, R2, or prepaid AI Gateway credits.
- The workflow makes at most two capped model calls per generated day.
- A date that already exists exits before making external calls.
- The job has a ten-minute timeout.
- Public GitHub repositories receive free standard Actions usage and Pages hosting.
- Failure of a free external service invokes a local fallback instead of blocking publication.

## Important files

```text
skyloom.json           product and retention configuration
scripts/setup.sh       idempotent cloud bootstrap
engine/daily.py        daily orchestration and idempotency
engine/llm.py          Cloudflare Workers AI calls
engine/genome.py       bounded style genome and mutation
engine/score.py        deterministic candidate fitness
engine/weather.py      Open-Meteo and weather fallbacks
engine/gallery.py      recent and monthly recipe manifests
data/champion.json     reigning genome and critic proposal
data/days/             permanent daily records
docs/app.js            browser-side recipe renderer
docs/data/              bounded public archive indexes
```

Weather data is supplied by [Open-Meteo](https://open-meteo.com/) under CC BY 4.0 and is attributed in the gallery.
