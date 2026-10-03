from __future__ import annotations

import json
from urllib.parse import quote, unquote, urlencode, urlparse
from urllib.request import Request, urlopen


CITY_PROFILES = {
    "Chicago": {
        "country_name": "United States", "continent": "North America",
        "wikipedia_title": "Chicago", "known_for": "architecture, blues, railways, and the lakefront",
        "brief": "Chicago grew where the Great Lakes meet the Mississippi watershed, turning a portage into one of North America's great transport, architecture, and cultural centers.",
        "fact": "The Home Insurance Building, completed in Chicago in 1885, is widely regarded as the world's first skyscraper.",
        "fact_source": "https://en.wikipedia.org/wiki/Home_Insurance_Building",
        "landmark": {"name": "Cloud Gate", "wiki_title": "Cloud_Gate"},
        "person": {"name": "Michelle Obama", "wiki_title": "Michelle_Obama"},
    },
    "Reykjavik": {
        "country_name": "Iceland", "continent": "Europe", "wikipedia_title": "Reykjav%C3%ADk",
        "known_for": "geothermal energy, music, and North Atlantic light",
        "brief": "Reykjavík is Iceland's capital and largest city, set on Faxaflói bay amid a landscape shaped by glaciers, geothermal heat, and the North Atlantic.",
        "fact": "Reykjavík is the world's northernmost capital of a sovereign state.",
        "fact_source": "https://en.wikipedia.org/wiki/Reykjav%C3%ADk",
        "landmark": {"name": "Hallgrímskirkja", "wiki_title": "Hallgr%C3%ADmskirkja"},
        "person": {"name": "Björk", "wiki_title": "Bj%C3%B6rk"},
    },
    "Kyoto": {
        "country_name": "Japan", "continent": "Asia", "wikipedia_title": "Kyoto",
        "known_for": "temples, gardens, craft traditions, and imperial history",
        "brief": "Kyoto was Japan's imperial capital for more than a millennium. Its grid, temples, gardens, craft traditions, and layered neighborhoods still carry that history into daily life.",
        "fact": "Kyoto served as Japan's imperial capital from 794 until the imperial court moved to Tokyo in 1869.",
        "fact_source": "https://en.wikipedia.org/wiki/Kyoto",
        "landmark": {"name": "Kinkaku-ji", "wiki_title": "Kinkaku-ji"},
        "person": {"name": "Shigeru Miyamoto", "wiki_title": "Shigeru_Miyamoto"},
    },
    "Nairobi": {
        "country_name": "Kenya", "continent": "Africa", "wikipedia_title": "Nairobi",
        "known_for": "diplomacy, technology, wildlife, and East African culture",
        "brief": "Nairobi is Kenya's capital and a major East African center for business, diplomacy, technology, and culture, with a national park directly beside the urban core.",
        "fact": "The name Nairobi comes from the Maasai phrase Enkare Nairobi, commonly translated as “place of cool waters.”",
        "fact_source": "https://en.wikipedia.org/wiki/Nairobi",
        "landmark": {"name": "Nairobi National Park", "wiki_title": "Nairobi_National_Park"},
        "person": {"name": "Wangari Maathai", "wiki_title": "Wangari_Maathai"},
    },
    "Lisbon": {
        "country_name": "Portugal", "continent": "Europe", "wikipedia_title": "Lisbon",
        "known_for": "Atlantic light, tiled streets, hills, and maritime history",
        "brief": "Lisbon rises across hills beside the Tagus estuary. Its maritime history, tiled streets, dense historic quarters, and Atlantic light give the city a distinctive physical rhythm.",
        "fact": "After the destructive 1755 earthquake, central Lisbon was rebuilt with an early system of earthquake-resistant wooden framing.",
        "fact_source": "https://en.wikipedia.org/wiki/1755_Lisbon_earthquake",
        "landmark": {"name": "Belém Tower", "wiki_title": "Bel%C3%A9m_Tower"},
        "person": {"name": "Fernando Pessoa", "wiki_title": "Fernando_Pessoa"},
    },
    "Melbourne": {
        "country_name": "Australia", "continent": "Oceania", "wikipedia_title": "Melbourne",
        "known_for": "laneways, design, sport, gardens, and food culture",
        "brief": "Melbourne sits on the traditional lands of the Kulin nations around Port Phillip Bay and is known for its laneways, cultural institutions, public gardens, and layered immigrant history.",
        "fact": "Melbourne's central street plan, laid out in 1837, is still known as the Hoddle Grid.",
        "fact_source": "https://en.wikipedia.org/wiki/Hoddle_Grid",
        "landmark": {"name": "Flinders Street Station", "wiki_title": "Flinders_Street_railway_station"},
        "person": {"name": "Cate Blanchett", "wiki_title": "Cate_Blanchett"},
    },
    "Buenos Aires": {
        "country_name": "Argentina", "continent": "South America", "wikipedia_title": "Buenos_Aires",
        "known_for": "tango, literature, football, cafés, and neighborhood life",
        "brief": "Buenos Aires is Argentina's capital on the Río de la Plata, shaped by immigration, port commerce, neighborhood identity, literature, football, and the culture of tango.",
        "fact": "Buenos Aires was founded twice: first in 1536 and again permanently in 1580.",
        "fact_source": "https://en.wikipedia.org/wiki/Buenos_Aires",
        "landmark": {"name": "Obelisk of Buenos Aires", "wiki_title": "Obelisk_of_Buenos_Aires"},
        "person": {"name": "Jorge Luis Borges", "wiki_title": "Jorge_Luis_Borges"},
    },
    "Vancouver": {
        "country_name": "Canada", "continent": "North America", "wikipedia_title": "Vancouver",
        "known_for": "ocean, mountains, film, and temperate rainforest",
        "brief": "Vancouver is a Pacific port city framed by ocean, mountains, and temperate rainforest on the traditional territories of the Musqueam, Squamish, and Tsleil-Waututh peoples.",
        "fact": "Stanley Park is larger than New York City's Central Park and occupies a peninsula immediately beside downtown Vancouver.",
        "fact_source": "https://en.wikipedia.org/wiki/Stanley_Park",
        "landmark": {"name": "Canada Place", "wiki_title": "Canada_Place"},
        "person": {"name": "Ryan Reynolds", "wiki_title": "Ryan_Reynolds"},
    },
    "Paris": {
        "country_name": "France", "continent": "Europe", "wikipedia_title": "Paris",
        "known_for": "art, fashion, cafés, monuments, and urban design",
        "brief": "Paris grew around the Seine into a center of art, politics, learning, and design. Its boulevards, neighborhoods, museums, and public spaces continue to shape how cities are imagined.",
        "fact": "Paris is divided into 20 numbered arrondissements that spiral clockwise from the city center.",
        "fact_source": "https://en.wikipedia.org/wiki/Arrondissements_of_Paris",
        "landmark": {"name": "Eiffel Tower", "wiki_title": "Eiffel_Tower"},
        "person": {"name": "Édith Piaf", "wiki_title": "%C3%89dith_Piaf"},
    },
    "Cairo": {
        "country_name": "Egypt", "continent": "Africa", "wikipedia_title": "Cairo",
        "known_for": "the Nile, medieval streets, scholarship, cinema, and nearby pyramids",
        "brief": "Cairo is Egypt's vast capital on the Nile and the largest urban center in the Arab world. Layers of Pharaonic, Coptic, Islamic, and modern history meet across the metropolis.",
        "fact": "Historic Cairo contains one of the world's greatest concentrations of medieval Islamic architecture.",
        "fact_source": "https://en.wikipedia.org/wiki/Islamic_Cairo",
        "landmark": {"name": "Cairo Citadel", "wiki_title": "Cairo_Citadel"},
        "person": {"name": "Naguib Mahfouz", "wiki_title": "Naguib_Mahfouz"},
    },
    "Mexico City": {
        "country_name": "Mexico", "continent": "North America", "wikipedia_title": "Mexico_City",
        "known_for": "murals, food, museums, music, and layered Indigenous history",
        "brief": "Mexico City occupies the high basin where the Mexica built Tenochtitlan. Today it is a huge cultural capital where archaeological remains, colonial streets, and contemporary life overlap.",
        "fact": "Mexico City was built over the Mexica capital Tenochtitlan, which stood on islands in Lake Texcoco.",
        "fact_source": "https://en.wikipedia.org/wiki/Tenochtitlan",
        "landmark": {"name": "Palacio de Bellas Artes", "wiki_title": "Palacio_de_Bellas_Artes"},
        "person": {"name": "Frida Kahlo", "wiki_title": "Frida_Kahlo"},
    },
    "Mumbai": {
        "country_name": "India", "continent": "Asia", "wikipedia_title": "Mumbai",
        "known_for": "cinema, finance, street food, design, and the Arabian Sea",
        "brief": "Mumbai is India's great Arabian Sea port and financial capital, formed from seven islands. Dense neighborhoods, cinema, commerce, and migration give the city its restless energy.",
        "fact": "Mumbai developed from seven islands that were joined through major land-reclamation projects.",
        "fact_source": "https://en.wikipedia.org/wiki/Seven_Islands_of_Bombay",
        "landmark": {"name": "Gateway of India", "wiki_title": "Gateway_of_India"},
        "person": {"name": "Sachin Tendulkar", "wiki_title": "Sachin_Tendulkar"},
    },
    "Seoul": {
        "country_name": "South Korea", "continent": "Asia", "wikipedia_title": "Seoul",
        "known_for": "design, technology, food, music, and mountain-backed neighborhoods",
        "brief": "Seoul is South Korea's capital on the Han River, where royal palaces and traditional neighborhoods sit beside one of the world's most connected and fast-moving urban economies.",
        "fact": "Seoul has served as Korea's principal capital since 1394, when the Joseon dynasty moved its capital there.",
        "fact_source": "https://en.wikipedia.org/wiki/Seoul",
        "landmark": {"name": "Gyeongbokgung", "wiki_title": "Gyeongbokgung"},
        "person": {"name": "Park Chan-wook", "wiki_title": "Park_Chan-wook"},
    },
}


def _trim_summary(text: str, limit: int = 430) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    sentences = clean[: limit + 1].split(". ")
    if len(sentences) > 1:
        return ". ".join(sentences[:-1]).rstrip(".") + "."
    return clean[:limit].rsplit(" ", 1)[0] + "…"


def _page_summary(title: str, timeout: int) -> dict:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title, safe='%')}"
    request = Request(url, headers={"User-Agent": "Skyloom/1.1 (city portrait; GitHub project)"})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _get_json(url: str, timeout: int) -> dict:
    request = Request(url, headers={"User-Agent": "Skyloom/1.2 (city portrait; GitHub project)"})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _nearby_pages(city: dict, timeout: int) -> list[dict]:
    params = {
        "action": "query", "format": "json", "formatversion": "2",
        "generator": "geosearch", "ggsnamespace": "0", "ggslimit": "24",
        "ggsradius": "10000", "ggscoord": f"{city['latitude']}|{city['longitude']}",
        "prop": "extracts|pageimages|info", "exintro": "1", "explaintext": "1",
        "piprop": "thumbnail", "pithumbsize": "900", "inprop": "url",
    }
    payload = _get_json("https://en.wikipedia.org/w/api.php?" + urlencode(params), timeout)
    return sorted(payload.get("query", {}).get("pages", []), key=lambda page: page.get("index", 999))


def _person_from_city(city: dict, timeout: int) -> dict | None:
    geoname_id = city.get("geoname_id")
    if not geoname_id:
        return None
    query = f'''SELECT ?person ?personLabel ?article ?sitelinks WHERE {{
      ?place wdt:P1566 "{geoname_id}" .
      ?person wdt:P31 wd:Q5; wdt:P19 ?place; wikibase:sitelinks ?sitelinks .
      ?article schema:about ?person; schema:isPartOf <https://en.wikipedia.org/> .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }} ORDER BY DESC(?sitelinks) LIMIT 1'''
    params = urlencode({"query": query, "format": "json"})
    payload = _get_json(f"https://query.wikidata.org/sparql?{params}", timeout)
    bindings = payload.get("results", {}).get("bindings", [])
    if not bindings:
        return None
    match = bindings[0]
    article = match["article"]["value"]
    title = unquote(urlparse(article).path.rsplit("/", 1)[-1])
    person = {"name": match["personLabel"]["value"], "source": article, "image": ""}
    try:
        page = _page_summary(title, timeout)
        person["source"] = page.get("content_urls", {}).get("desktop", {}).get("page", article)
        person["image"] = page.get("thumbnail", {}).get("source", "")
    except Exception:
        pass
    return person


LANDMARK_WORDS = (
    "abbey", "arena", "basilica", "bridge", "castle", "cathedral", "church", "fort",
    "garden", "hall", "historic", "landmark", "memorial", "monument", "mosque", "museum",
    "palace", "park", "square", "stadium", "station", "temple", "theatre", "tower",
)


def _dynamic_context(city: dict, offline: bool, timeout: int) -> dict:
    name = city["name"]
    country = city.get("country_name", city["country"])
    region = city.get("region", "")
    location = ", ".join(part for part in (region, country) if part)
    geoname_url = f"https://www.geonames.org/{city.get('geoname_id', '')}"
    population = int(city.get("population", 0))
    population_fact = (
        f"GeoNames records {name} as a populated place in {location} with approximately {population:,} residents."
        if population else f"GeoNames records {name} as a populated place in {location}."
    )
    result = {
        "country_name": country,
        "continent": city.get("continent", "World"),
        "known_for": "its local history, landscape, and community life",
        "brief": f"{name} is a city or town in {location}. Skyloom selected it from its worldwide city catalog.",
        "fact": population_fact,
        "fact_source": geoname_url,
        "source": geoname_url,
        "source_label": "GeoNames",
        "source_status": "catalog-fallback",
        "landmark": {"name": name, "source": geoname_url, "image": ""},
        "person": {"name": f"People of {name}", "source": geoname_url, "image": ""},
    }
    if offline:
        return result

    errors = []
    try:
        pages = _nearby_pages(city, timeout)
        city_name = name.casefold()
        city_page = next((page for page in pages if page.get("title", "").casefold() == city_name), None)
        city_page = city_page or next((page for page in pages if page.get("extract")), None)
        if city_page:
            extract = _trim_summary(city_page.get("extract", ""))
            if extract:
                result["brief"] = extract
                sentences = [sentence.strip() for sentence in extract.split(". ") if sentence.strip()]
                result["fact"] = (sentences[1] if len(sentences) > 1 else sentences[0]).rstrip(".") + "."
            result["source"] = city_page.get("fullurl", result["source"])
            result["fact_source"] = result["source"]
            result["source_label"] = "Wikipedia"
            result["source_status"] = "live"
            result["landmark"] = {
                "name": name,
                "source": result["source"],
                "image": city_page.get("thumbnail", {}).get("source", ""),
            }

        landmark_candidates = []
        for index, page in enumerate(pages):
            if page is city_page or not page.get("thumbnail"):
                continue
            title_text = page.get("title", "").casefold()
            extract_text = page.get("extract", "").casefold()
            title_hits = sum(word in title_text for word in LANDMARK_WORDS)
            extract_hits = sum(word in extract_text for word in LANDMARK_WORDS)
            score = title_hits * 30 + extract_hits * 3 - index
            landmark_candidates.append((score, page))
        if landmark_candidates:
            score, landmark_page = max(landmark_candidates, key=lambda item: item[0])
            if score > 0:
                result["landmark"] = {
                    "name": landmark_page["title"],
                    "source": landmark_page.get("fullurl", result["source"]),
                    "image": landmark_page.get("thumbnail", {}).get("source", ""),
                }
    except Exception as exc:
        errors.append(f"city: {exc}")

    try:
        person = _person_from_city(city, timeout)
        if person:
            result["person"] = person
    except Exception as exc:
        errors.append(f"person: {exc}")
    if errors:
        result["source_error"] = "; ".join(errors)[:300]
    return result


def _public_asset(asset: dict) -> dict:
    title = asset["wiki_title"]
    return {
        "name": asset["name"],
        "source": f"https://en.wikipedia.org/wiki/{title}",
        "image": "",
    }


def city_context(city: dict, offline: bool = False, timeout: int = 15) -> dict:
    if city["name"] not in CITY_PROFILES:
        return _dynamic_context(city, offline, timeout)
    profile = CITY_PROFILES[city["name"]].copy()
    title = profile.pop("wikipedia_title")
    landmark = _public_asset(profile.pop("landmark"))
    person = _public_asset(profile.pop("person"))
    result = {
        **profile,
        "source": f"https://en.wikipedia.org/wiki/{title}",
        "source_label": "Wikipedia",
        "source_status": "curated-fallback",
        "landmark": landmark,
        "person": person,
    }
    if offline:
        return result

    errors = []
    try:
        payload = _page_summary(title, timeout)
        if payload.get("extract"):
            result["brief"] = _trim_summary(payload["extract"])
            result["source"] = payload.get("content_urls", {}).get("desktop", {}).get("page", result["source"])
            result["source_status"] = "live"
    except Exception as exc:
        errors.append(f"city: {exc}")

    originals = [CITY_PROFILES[city["name"]]["landmark"], CITY_PROFILES[city["name"]]["person"]]
    for key, original in zip(("landmark", "person"), originals):
        try:
            page = _page_summary(original["wiki_title"], timeout)
            result[key]["source"] = page.get("content_urls", {}).get("desktop", {}).get("page", result[key]["source"])
            result[key]["image"] = page.get("thumbnail", {}).get("source", "")
        except Exception as exc:
            errors.append(f"{key}: {exc}")
    if errors:
        result["source_error"] = "; ".join(errors)[:300]
    return result
