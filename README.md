# Skyloom

> Weather suggests. Models propose. Skyloom decides.

Skyloom publishes one weather-driven city portrait each day. It combines a concise city briefing, one sourced fact, a notable landmark and person, and a generative background whose color, motion, density, light, and marks directly encode the day's conditions. An open-weight cloud model proposes creative direction; deterministic code breeds and measures four candidates; the strongest becomes tomorrow's champion.

The system uses GitHub Actions, GitHub Pages, Open-Meteo, GeoNames, Wikipedia, and `gpt-oss-20b` through Cloudflare Workers AI. It has no always-on server, paid image model, or database.

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

1. Select an unused city or town from a deterministically shuffled catalog of more than 64,000 populated places.
2. Read current and hourly weather from Open-Meteo.
3. Retrieve a sourced city summary, landmark image, notable person, and important fact.
4. Ask the open-weight model for a palette and bounded visual mutation.
5. Breed champion, director, previous-critic, and explorer candidates.
6. Score composition, coverage, stroke length, contrast, weather fit, and novelty.
7. Save the winning recipe and rebuild the bounded archive manifests.

The scheduled workflow targets **7:07 a.m. America/Chicago time** every day, with automatic recovery checks at **8:23 a.m.** and **9:41 a.m.** The IANA timezone preserves local Central time through both CST and daylight-saving time. Every run is idempotent: once the day's record exists, later checks exit before weather or model calls. Selection skips every GeoNames ID already present in `data/days`, so a place cannot repeat until the catalog is exhausted. Run `python3 scripts/update_city_catalog.py` to refresh the catalog from GeoNames.

If weather or model inference fails, deterministic fallbacks still publish the day's recipe and record the error.

## Retention strategy

Skyloom does not commit rendered SVG or PNG files. The browser reconstructs each artwork from a small recipe containing its date seed, palette, genome, weather, city context, and score.

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
engine/city.py         sourced city briefing and fact fallbacks
engine/genome.py       bounded style genome and mutation
engine/score.py        deterministic candidate fitness
engine/weather.py      Open-Meteo and weather fallbacks
engine/gallery.py      recent and monthly recipe manifests
data/cities.tsv.gz     shuffled GeoNames city and town catalog
data/champion.json     reigning genome and critic proposal
data/days/             permanent daily records
docs/app.js            browser-side recipe renderer
docs/data/              bounded public archive indexes
```

Weather data is supplied by [Open-Meteo](https://open-meteo.com/) under CC BY 4.0. City briefings and fact sources link directly to Wikipedia from the interface.
City and town selection data is supplied by [GeoNames](https://www.geonames.org/) under CC BY 4.0.
The bundled country outlines come from the public-domain Natural Earth dataset via the `world.geo.json` project, so the map has no tile service, API key, or usage cost.
