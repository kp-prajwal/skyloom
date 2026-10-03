#!/usr/bin/env python3
"""Build Skyloom's compact, deterministic GeoNames city catalog."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen
import zipfile


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://download.geonames.org/export/dump"
USER_AGENT = "Skyloom/1.2 (city portrait; GitHub project)"
ALLOWED_FEATURES = {"PPL", "PPLC", "PPLG", "PPLA", "PPLA2", "PPLA3", "PPLA4", "PPLA5"}
CONTINENTS = {
    "AF": "Africa", "AS": "Asia", "EU": "Europe", "NA": "North America",
    "OC": "Oceania", "SA": "South America", "AN": "Antarctica",
}


def download(name: str) -> bytes:
    request = Request(f"{BASE_URL}/{name}", headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=90) as response:
        return response.read()


def countries(payload: bytes) -> dict[str, tuple[str, str]]:
    result = {}
    for raw in payload.decode("utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        fields = raw.split("\t")
        if len(fields) > 8:
            result[fields[0]] = (fields[4], CONTINENTS.get(fields[8], fields[8]))
    return result


def admin_regions(payload: bytes) -> dict[str, str]:
    result = {}
    for raw in payload.decode("utf-8").splitlines():
        fields = raw.split("\t")
        if len(fields) >= 2:
            result[fields[0]] = fields[1]
    return result


def stable_order(row: tuple[str, ...]) -> str:
    return hashlib.sha256(f"skyloom-city-v1:{row[0]}".encode()).hexdigest()


def build() -> int:
    country_lookup = countries(download("countryInfo.txt"))
    region_lookup = admin_regions(download("admin1CodesASCII.txt"))
    archive = zipfile.ZipFile(io.BytesIO(download("cities5000.zip")))
    rows = []
    with archive.open("cities5000.txt") as raw:
        for fields in csv.reader(io.TextIOWrapper(raw, encoding="utf-8"), delimiter="\t"):
            if len(fields) < 18 or fields[7] not in ALLOWED_FEATURES or fields[8] not in country_lookup:
                continue
            country_name, continent = country_lookup[fields[8]]
            region = region_lookup.get(f"{fields[8]}.{fields[10]}", "")
            rows.append((
                fields[0], fields[1], fields[4], fields[5], fields[8], country_name,
                region, continent, fields[14] or "0", fields[17],
            ))
    rows.sort(key=stable_order)

    destination = ROOT / "data" / "cities.tsv.gz"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        with gzip.GzipFile(filename="", mode="wb", fileobj=temporary, mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                writer = csv.writer(text, delimiter="\t")
                writer.writerow(("geoname_id", "name", "latitude", "longitude", "country", "country_name", "region", "continent", "population", "timezone"))
                writer.writerows(rows)
    temporary_path.replace(destination)
    destination.chmod(0o644)
    print(f"Wrote {len(rows):,} cities and towns to {destination}")
    return len(rows)


if __name__ == "__main__":
    build()
