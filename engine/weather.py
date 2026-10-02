from __future__ import annotations

from datetime import date
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


CITIES = [
    {"name": "Chicago", "country": "US", "latitude": 41.8781, "longitude": -87.6298},
    {"name": "Reykjavik", "country": "IS", "latitude": 64.1466, "longitude": -21.9426},
    {"name": "Kyoto", "country": "JP", "latitude": 35.0116, "longitude": 135.7681},
    {"name": "Nairobi", "country": "KE", "latitude": -1.2921, "longitude": 36.8219},
    {"name": "Lisbon", "country": "PT", "latitude": 38.7223, "longitude": -9.1393},
    {"name": "Melbourne", "country": "AU", "latitude": -37.8136, "longitude": 144.9631},
    {"name": "Buenos Aires", "country": "AR", "latitude": -34.6037, "longitude": -58.3816},
    {"name": "Vancouver", "country": "CA", "latitude": 49.2827, "longitude": -123.1207},
]


def city_for_day(day: date) -> dict:
    return CITIES[(day.timetuple().tm_yday - 1) % len(CITIES)]


def fallback_weather(city: dict, reason: str = "offline") -> dict:
    return {
        "city": city["name"],
        "country": city["country"],
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "temperature_c": 12.0,
        "cloud_cover": 45,
        "wind_kph": 10.0,
        "wind_direction": 225,
        "precipitation_mm": 0.0,
        "weather_code": 2,
        "is_day": 1,
        "source": "fallback",
        "fallback_reason": reason,
    }


def fetch_weather(city: dict, timeout: int = 15) -> dict:
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "current": ",".join([
            "temperature_2m",
            "cloud_cover",
            "wind_speed_10m",
            "wind_direction_10m",
            "precipitation",
            "weather_code",
            "is_day",
        ]),
        "timezone": "auto",
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "Skyloom/1.0"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    current = payload["current"]
    return {
        "city": city["name"],
        "country": city["country"],
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "temperature_c": current["temperature_2m"],
        "cloud_cover": current["cloud_cover"],
        "wind_kph": current["wind_speed_10m"],
        "wind_direction": current["wind_direction_10m"],
        "precipitation_mm": current["precipitation"],
        "weather_code": current["weather_code"],
        "is_day": current["is_day"],
        "source": "Open-Meteo",
    }


def weather_mutation(weather: dict) -> dict:
    wind = min(float(weather.get("wind_kph", 0)), 55) / 55
    clouds = float(weather.get("cloud_cover", 0)) / 100
    rain = min(float(weather.get("precipitation_mm", 0)), 8) / 8
    return {
        "curl": (wind - 0.35) * 0.65,
        "stroke_count": round((clouds + rain - 0.6) * 100),
        "opacity": (0.45 - clouds) * 0.05,
        "horizon": (clouds - 0.5) * 0.04,
    }


def fallback_direction(weather: dict) -> dict:
    clouds = float(weather.get("cloud_cover", 45))
    temperature = float(weather.get("temperature_c", 12))
    rain = float(weather.get("precipitation_mm", 0))
    if rain > 0.2:
        palette = ["#101b2d", "#425d73", "#9ab0bd", "#e6c7a3"]
        image = "rain threads through the waking streets"
    elif clouds > 70:
        palette = ["#182236", "#536579", "#a8a6a0", "#e7c8a2"]
        image = "clouds gather their quiet weight"
    elif temperature > 24:
        palette = ["#23203d", "#d56d4b", "#f2b866", "#fff0bf"]
        image = "warm light gathers at the roofs"
    else:
        palette = ["#17263f", "#527c94", "#e19a67", "#f5d7a4"]
        image = "pale light crosses the open sky"
    city = weather["city"]
    return {
        "title": f"First Light over {city}",
        "poem": [
            f"Above {city}, {image},",
            "the wind carries one color into another,",
            "and morning begins before anyone asks it to.",
        ],
        "palette": palette,
        "mutation": weather_mutation(weather),
        "rationale": "Deterministic weather direction used because cloud inference was unavailable.",
        "source": "fallback",
    }
