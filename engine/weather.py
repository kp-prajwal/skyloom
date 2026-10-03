from __future__ import annotations

from datetime import date, datetime
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


CITIES = [
    {"name": "Chicago", "country": "US", "country_name": "United States", "latitude": 41.8781, "longitude": -87.6298},
    {"name": "Reykjavik", "country": "IS", "country_name": "Iceland", "latitude": 64.1466, "longitude": -21.9426},
    {"name": "Kyoto", "country": "JP", "country_name": "Japan", "latitude": 35.0116, "longitude": 135.7681},
    {"name": "Nairobi", "country": "KE", "country_name": "Kenya", "latitude": -1.2921, "longitude": 36.8219},
    {"name": "Lisbon", "country": "PT", "country_name": "Portugal", "latitude": 38.7223, "longitude": -9.1393},
    {"name": "Melbourne", "country": "AU", "country_name": "Australia", "latitude": -37.8136, "longitude": 144.9631},
    {"name": "Buenos Aires", "country": "AR", "country_name": "Argentina", "latitude": -34.6037, "longitude": -58.3816},
    {"name": "Vancouver", "country": "CA", "country_name": "Canada", "latitude": 49.2827, "longitude": -123.1207},
    {"name": "Paris", "country": "FR", "country_name": "France", "latitude": 48.8566, "longitude": 2.3522},
    {"name": "Cairo", "country": "EG", "country_name": "Egypt", "latitude": 30.0444, "longitude": 31.2357},
    {"name": "Mexico City", "country": "MX", "country_name": "Mexico", "latitude": 19.4326, "longitude": -99.1332},
    {"name": "Mumbai", "country": "IN", "country_name": "India", "latitude": 19.0760, "longitude": 72.8777},
    {"name": "Seoul", "country": "KR", "country_name": "South Korea", "latitude": 37.5665, "longitude": 126.9780},
]


def city_for_day(day: date) -> dict:
    return CITIES[(day.timetuple().tm_yday - 1) % len(CITIES)]


def fallback_weather(city: dict, reason: str = "offline") -> dict:
    return {
        "city": city["name"],
        "country": city["country"],
        "country_name": city.get("country_name", city["country"]),
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "temperature_c": 12.0,
        "apparent_temperature_c": 11.0,
        "relative_humidity": 58,
        "cloud_cover": 45,
        "wind_kph": 10.0,
        "wind_direction": 225,
        "precipitation_mm": 0.0,
        "weather_code": 2,
        "is_day": 1,
        "timezone": "Local time unavailable",
        "local_time": "—",
        "sunrise": "06:30",
        "sunset": "18:30",
        "daylight_minutes": 720,
        "source": "fallback",
        "fallback_reason": reason,
    }


def fetch_weather(city: dict, timeout: int = 15) -> dict:
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "current": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "cloud_cover",
            "wind_speed_10m",
            "wind_direction_10m",
            "precipitation",
            "weather_code",
            "is_day",
        ]),
        "daily": "sunrise,sunset",
        "forecast_days": 1,
        "timezone": "auto",
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "Skyloom/1.0"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    current = payload["current"]
    sunrise = payload["daily"]["sunrise"][0]
    sunset = payload["daily"]["sunset"][0]
    daylight_minutes = int((datetime.fromisoformat(sunset) - datetime.fromisoformat(sunrise)).total_seconds() / 60)
    return {
        "city": city["name"],
        "country": city["country"],
        "country_name": city.get("country_name", city["country"]),
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "temperature_c": current["temperature_2m"],
        "apparent_temperature_c": current["apparent_temperature"],
        "relative_humidity": current["relative_humidity_2m"],
        "cloud_cover": current["cloud_cover"],
        "wind_kph": current["wind_speed_10m"],
        "wind_direction": current["wind_direction_10m"],
        "precipitation_mm": current["precipitation"],
        "weather_code": current["weather_code"],
        "is_day": current["is_day"],
        "timezone": payload.get("timezone_abbreviation", payload.get("timezone", "local")),
        "local_time": current["time"],
        "sunrise": sunrise[11:16],
        "sunset": sunset[11:16],
        "daylight_minutes": daylight_minutes,
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
    elif clouds > 70:
        palette = ["#182236", "#536579", "#a8a6a0", "#e7c8a2"]
    elif temperature > 24:
        palette = ["#23203d", "#d56d4b", "#f2b866", "#fff0bf"]
    else:
        palette = ["#17263f", "#527c94", "#e19a67", "#f5d7a4"]
    city = weather["city"]
    country = weather.get("country_name", weather["country"])
    return {
        "title": f"{city}, {country}",
        "palette": palette,
        "mutation": weather_mutation(weather),
        "rationale": "Deterministic weather direction used because cloud inference was unavailable.",
        "source": "fallback",
    }
