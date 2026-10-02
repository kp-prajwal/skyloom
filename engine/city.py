from __future__ import annotations

import json
from urllib.parse import quote
from urllib.request import Request, urlopen


CITY_PROFILES = {
    "Chicago": {
        "wikipedia_title": "Chicago",
        "brief": "Chicago grew where the Great Lakes meet the Mississippi watershed, turning a portage into one of North America's great transport, architecture, and cultural centers.",
        "fact": "The Home Insurance Building, completed in Chicago in 1885, is widely regarded as the world's first skyscraper.",
        "fact_source": "https://en.wikipedia.org/wiki/Home_Insurance_Building",
    },
    "Reykjavik": {
        "wikipedia_title": "Reykjav%C3%ADk",
        "brief": "Reykjavík is Iceland's capital and largest city, set on Faxaflói bay amid a landscape shaped by glaciers, geothermal heat, and the North Atlantic.",
        "fact": "Reykjavík is the world's northernmost capital of a sovereign state.",
        "fact_source": "https://en.wikipedia.org/wiki/Reykjav%C3%ADk",
    },
    "Kyoto": {
        "wikipedia_title": "Kyoto",
        "brief": "Kyoto was Japan's imperial capital for more than a millennium. Its grid, temples, gardens, craft traditions, and layered neighborhoods still carry that history into daily life.",
        "fact": "Kyoto served as Japan's imperial capital from 794 until the imperial court moved to Tokyo in 1869.",
        "fact_source": "https://en.wikipedia.org/wiki/Kyoto",
    },
    "Nairobi": {
        "wikipedia_title": "Nairobi",
        "brief": "Nairobi is Kenya's capital and a major East African center for business, diplomacy, technology, and culture, with a national park directly beside the urban core.",
        "fact": "The name Nairobi comes from the Maasai phrase Enkare Nairobi, commonly translated as “place of cool waters.”",
        "fact_source": "https://en.wikipedia.org/wiki/Nairobi",
    },
    "Lisbon": {
        "wikipedia_title": "Lisbon",
        "brief": "Lisbon rises across hills beside the Tagus estuary. Its maritime history, tiled streets, dense historic quarters, and Atlantic light give the city a distinctive physical rhythm.",
        "fact": "After the destructive 1755 earthquake, central Lisbon was rebuilt with an early system of earthquake-resistant wooden framing.",
        "fact_source": "https://en.wikipedia.org/wiki/1755_Lisbon_earthquake",
    },
    "Melbourne": {
        "wikipedia_title": "Melbourne",
        "brief": "Melbourne sits on the traditional lands of the Kulin nations around Port Phillip Bay and is known for its laneways, cultural institutions, public gardens, and layered immigrant history.",
        "fact": "Melbourne's central street plan, laid out in 1837, is still known as the Hoddle Grid.",
        "fact_source": "https://en.wikipedia.org/wiki/Hoddle_Grid",
    },
    "Buenos Aires": {
        "wikipedia_title": "Buenos_Aires",
        "brief": "Buenos Aires is Argentina's capital on the Río de la Plata, shaped by immigration, port commerce, neighborhood identity, literature, football, and the culture of tango.",
        "fact": "Buenos Aires was founded twice: first in 1536 and again permanently in 1580.",
        "fact_source": "https://en.wikipedia.org/wiki/Buenos_Aires",
    },
    "Vancouver": {
        "wikipedia_title": "Vancouver",
        "brief": "Vancouver is a Pacific port city framed by ocean, mountains, and temperate rainforest on the traditional territories of the Musqueam, Squamish, and Tsleil-Waututh peoples.",
        "fact": "Stanley Park is larger than New York City's Central Park and occupies a peninsula immediately beside downtown Vancouver.",
        "fact_source": "https://en.wikipedia.org/wiki/Stanley_Park",
    },
}


def _trim_summary(text: str, limit: int = 520) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    sentences = clean[: limit + 1].split(". ")
    if len(sentences) > 1:
        return ". ".join(sentences[:-1]).rstrip(".") + "."
    return clean[:limit].rsplit(" ", 1)[0] + "…"


def city_context(city: dict, offline: bool = False, timeout: int = 15) -> dict:
    profile = CITY_PROFILES[city["name"]].copy()
    title = profile.pop("wikipedia_title")
    profile["source"] = f"https://en.wikipedia.org/wiki/{title}"
    profile["source_label"] = "Wikipedia"
    profile["source_status"] = "curated-fallback"
    if offline:
        return profile

    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title, safe='%')}"
    request = Request(url, headers={"User-Agent": "Skyloom/1.0 (city portrait; GitHub project)"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
        extract = payload.get("extract")
        if extract:
            profile["brief"] = _trim_summary(extract)
            profile["source"] = payload.get("content_urls", {}).get("desktop", {}).get("page", profile["source"])
            profile["source_status"] = "live"
    except Exception as exc:
        profile["source_error"] = str(exc)[:180]
    return profile

