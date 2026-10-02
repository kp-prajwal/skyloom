from __future__ import annotations

from datetime import date, datetime, timedelta
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
        "best_window": {
            "start": "15:00",
            "end": "18:00",
            "label": "3–6 PM",
            "score": 72,
            "reason": "A mild, mostly dry three-hour stretch with manageable wind.",
            "rain_probability": 10,
            "temperature_c": 12.0,
            "wind_kph": 10.0,
        },
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
        "hourly": ",".join([
            "temperature_2m",
            "precipitation_probability",
            "cloud_cover",
            "wind_speed_10m",
            "uv_index",
            "is_day",
        ]),
        "daily": "sunrise,sunset",
        "forecast_days": 2,
        "timezone": "auto",
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "Skyloom/1.0"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    current = payload["current"]
    best_window = _best_window(payload)
    sunrise = payload["daily"]["sunrise"][0]
    sunset = payload["daily"]["sunset"][0]
    daylight_minutes = int((datetime.fromisoformat(sunset) - datetime.fromisoformat(sunrise)).total_seconds() / 60)
    return {
        "city": city["name"],
        "country": city["country"],
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
        "best_window": best_window,
        "source": "Open-Meteo",
    }


def _clock_label(iso_time: str) -> str:
    moment = datetime.fromisoformat(iso_time)
    hour = moment.hour
    suffix = "AM" if hour < 12 else "PM"
    display = hour % 12 or 12
    return f"{display}:{moment.minute:02d} {suffix}"


def _best_window(payload: dict) -> dict:
    hourly = payload["hourly"]
    current_time = datetime.fromisoformat(payload["current"]["time"])
    candidates = []
    times = [datetime.fromisoformat(value) for value in hourly["time"]]
    for start in range(0, len(times) - 2):
        block_times = times[start : start + 3]
        if block_times[0] < current_time or block_times[-1] > current_time + timedelta(hours=18):
            continue
        daylight = hourly["is_day"][start : start + 3]
        if sum(daylight) < 2:
            continue
        rain = sum(hourly["precipitation_probability"][start : start + 3]) / 3
        temperature = sum(hourly["temperature_2m"][start : start + 3]) / 3
        wind = sum(hourly["wind_speed_10m"][start : start + 3]) / 3
        uv = sum(hourly["uv_index"][start : start + 3]) / 3
        comfort = max(0, 1 - abs(temperature - 20) / 18)
        rain_score = max(0, 1 - rain / 100)
        wind_score = max(0, 1 - wind / 45)
        uv_score = 1 if uv <= 5 else max(0.25, 1 - (uv - 5) / 8)
        score = rain_score * 0.48 + comfort * 0.27 + wind_score * 0.15 + uv_score * 0.10
        candidates.append((score, start, rain, temperature, wind, uv))

    if not candidates:
        return fallback_weather({"name": "", "country": "", "latitude": 0, "longitude": 0})["best_window"]
    score, start, rain, temperature, wind, uv = max(candidates)
    start_time = hourly["time"][start]
    # Each hourly value represents the beginning of an hour, so a three-point
    # block that starts at 15:00 ends at 18:00, not 17:00.
    end_moment = datetime.fromisoformat(hourly["time"][start + 2]) + timedelta(hours=1)
    end_time = end_moment.isoformat(timespec="minutes")
    qualities = []
    if rain <= 15:
        qualities.append("dry")
    elif rain <= 35:
        qualities.append("lower-rain")
    if wind <= 18:
        qualities.append("calm")
    if 12 <= temperature <= 26:
        qualities.append("comfortable")
    if uv > 6:
        qualities.append("bright—use sun protection")
    phrase = ", ".join(qualities[:2]) if qualities else "the day's most balanced conditions"
    return {
        "start": start_time[11:16],
        "end": end_time[11:16],
        "label": f"{_clock_label(start_time)}–{_clock_label(end_time)}",
        "score": round(score * 100),
        "reason": f"The strongest outdoor window: {phrase}, with {round(rain)}% average rain probability.",
        "rain_probability": round(rain),
        "temperature_c": round(temperature, 1),
        "wind_kph": round(wind, 1),
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
