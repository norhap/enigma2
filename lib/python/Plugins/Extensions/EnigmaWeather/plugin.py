"""EnigmaWeather v2.0.0 - Modern Weather Plugin for Enigma2

A completely new weather plugin using Open-Meteo API.
Configuration namespace: config.plugins.enigmaweather

No connection to any previous weather implementations.
No external dependencies - uses only Python stdlib.
"""

__version__ = "2.0.0"
__author__ = "EnigmaWeather Team"

import json
import logging
import math
import queue
import re
import tempfile
import threading
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from os import unlink
from typing import Optional, List, Dict
from Components.config import ConfigSubsection, ConfigText, config, configfile

logger = logging.getLogger(__name__)

config.plugins.enigmaweather = ConfigSubsection()
config.plugins.enigmaweather.location = ConfigText(default="", fixed_size=False)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass(frozen=True)
class Location:
	"""Geographic location data."""
	city: str
	country: str
	latitude: float
	longitude: float
	timezone: str


def save_location(location: Location):
	config.plugins.enigmaweather.location.value = json.dumps(asdict(location), ensure_ascii=True)
	config.plugins.enigmaweather.location.save()
	configfile.save()


def load_saved_location() -> Optional[Location]:
	value = config.plugins.enigmaweather.location.value
	if not value:
		return None
	try:
		data = json.loads(value)
		if not isinstance(data, dict):
			raise ValueError("location is not an object")
		location = Location(**data)
		if not all(isinstance(item, str) for item in (location.city, location.country, location.timezone)):
			raise ValueError("invalid location text")
		if not location.city.strip() or not location.timezone.strip():
			raise ValueError("missing city or timezone")
		if any(isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item)
			for item in (location.latitude, location.longitude)):
			raise ValueError("invalid coordinates")
		if not -90 <= location.latitude <= 90 or not -180 <= location.longitude <= 180:
			raise ValueError("coordinates out of range")
		return location
	except (TypeError, ValueError) as error:
		raise ValueError("Invalid saved weather location: %s" % error) from error


@dataclass(frozen=True)
class CurrentWeather:
	"""Real-time weather conditions."""
	temperature: float
	condition: str
	weather_code: int
	wind_speed: float
	wind_direction: str
	humidity: int
	pressure: float
	is_day: bool


@dataclass(frozen=True)
class DailyForecast:
	"""Daily weather forecast."""
	date: str
	max_temp: float
	min_temp: float
	condition: str
	weather_code: int
	wind_speed: float
	wind_direction: str
	humidity: int
	precipitation: float
	precipitation_prob: int
	sunrise: Optional[str] = None
	sunset: Optional[str] = None


@dataclass(frozen=True)
class HourlyForecast:
	"""Hourly weather forecast in the location's local time."""
	time: str
	temperature: float
	condition: str
	weather_code: int
	wind_speed: float
	wind_direction: str
	humidity: int
	precipitation: float
	precipitation_prob: int
	is_day: bool


@dataclass(frozen=True)
class WeatherData:
	"""Complete weather dataset."""
	location: Location
	current: CurrentWeather
	daily_forecast: List[DailyForecast]
	updated_at: datetime
	hourly_forecast: List[HourlyForecast] = field(default_factory=list)


# ============================================================================
# UTILITIES
# ============================================================================

class WeatherMapper:
	"""Weather condition mapping and formatting utilities."""

	# WMO code to icon mapping
	CONDITION_ICONS = {
		(0, True): "sun", (0, False): "moon",
		(1, True): "sun_cloud", (1, False): "moon_cloud",
		(2, True): "sun_cloud", (2, False): "moon_cloud",
		(3, True): "cloud", (3, False): "cloud",
		(45, True): "fog", (45, False): "fog",
		(48, True): "fog", (48, False): "fog",
		(51, True): "drizzle", (51, False): "drizzle",
		(61, True): "rain", (61, False): "rain",
		(63, True): "rain", (63, False): "rain",
		(65, True): "rain_heavy", (65, False): "rain_heavy",
		(71, True): "snow", (71, False): "snow",
		(73, True): "snow", (73, False): "snow",
		(75, True): "snow_heavy", (75, False): "snow_heavy",
		(77, True): "snow", (77, False): "snow",
		(80, True): "rain_shower", (80, False): "rain_shower",
		(81, True): "rain_heavy", (81, False): "rain_heavy",
		(82, True): "rain_heavy", (82, False): "rain_heavy",
		(85, True): "snow_shower", (85, False): "snow_shower",
		(86, True): "snow_shower", (86, False): "snow_shower",
		(95, True): "thunderstorm", (95, False): "thunderstorm",
		(96, True): "thunderstorm_hail", (96, False): "thunderstorm_hail",
		(99, True): "thunderstorm_hail", (99, False): "thunderstorm_hail",
	}

	@staticmethod
	def get_icon(code: int, is_day: bool = True) -> str:
		"""Get icon name for weather code."""
		return WeatherMapper.CONDITION_ICONS.get((code, is_day), "unknown")

	@staticmethod
	def get_wind_direction(degrees: int) -> str:
		"""Convert degrees to cardinal direction."""
		directions = [
			"N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
			"S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
		]
		return directions[round(degrees / 22.5) % 16]

	@staticmethod
	def format_temperature(celsius: float, unit: str = "C") -> str:
		"""Format temperature for display."""
		if unit == "F":
			fahrenheit = (celsius * 9 / 5) + 32
			return f"{fahrenheit:.1f}°F"
		return f"{celsius:.1f}°C"

	@staticmethod
	def format_wind(speed: float, direction: str) -> str:
		"""Format wind speed and direction."""
		return f"{direction} {speed:.1f} km/h"

	@staticmethod
	def get_description(code: int) -> str:
		"""Get human-readable description for weather code."""
		descriptions = {
			0: _("Clear sky"),
			1: _("Mainly clear"),
			2: _("Partly cloudy"),
			3: _("Overcast"),
			45: _("Foggy"),
			48: _("Depositing rime fog"),
			51: _("Light drizzle"),
			53: _("Moderate drizzle"),
			55: _("Dense drizzle"),
			56: _("Light freezing drizzle"),
			57: _("Dense freezing drizzle"),
			61: _("Slight rain"),
			63: _("Moderate rain"),
			65: _("Heavy rain"),
			66: _("Light freezing rain"),
			67: _("Heavy freezing rain"),
			71: _("Slight snow"),
			73: _("Moderate snow"),
			75: _("Heavy snow"),
			77: _("Snow grains"),
			80: _("Slight rain showers"),
			81: _("Moderate rain showers"),
			82: _("Violent rain showers"),
			85: _("Slight snow showers"),
			86: _("Heavy snow showers"),
			95: _("Thunderstorm"),
			96: _("Thunderstorm with slight hail"),
			99: _("Thunderstorm with heavy hail"),
		}
		return descriptions.get(code, _("Weather code %d") % code)


# ============================================================================
# API CLIENT
# ============================================================================

class OpenMeteoClient:
	"""Open-Meteo API client with intelligent caching."""

	BASE_URL = "https://api.open-meteo.com/v1"
	GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1"
	CACHE_TTL = 3600  # 1 hour in seconds

	def __init__(self):
		self._cache = {}
		self._lock = threading.Lock()

	def search_locations(self, query: str, limit: int = 5) -> List[Location]:
		"""Search for locations by name."""
		if not query or not query.strip():
			return []

		try:
			params = {
				"name": query.strip(),
				"count": limit,
				"language": "en",
				"format": "json"
			}
			url = f"{self.GEOCODE_URL}/search?{urllib.parse.urlencode(params)}"
			req = urllib.request.Request(url, headers={"User-Agent": "EnigmaWeather/2.0"})

			with urllib.request.urlopen(req, timeout=10) as response:
				data = json.loads(response.read().decode("utf-8"))

			locations = []
			for result in data.get("results", []):
				locations.append(Location(
					city=result.get("name", ""),
					country=result.get("country", ""),
					latitude=float(result.get("latitude", 0.0)),
					longitude=float(result.get("longitude", 0.0)),
					timezone=result.get("timezone", "UTC"),
				))

			return locations

		except Exception as e:
			logger.error(_("Location search error: %s") % str(e))
			return []

	def fetch_weather(self, location: Location) -> Optional[WeatherData]:
		"""Fetch weather data for location with caching."""
		cache_key = f"{location.latitude:.2f}_{location.longitude:.2f}"

		# Check cache
		with self._lock:
			if cache_key in self._cache:
				weather, expiry = self._cache[cache_key]
				if datetime.now() < expiry:
					logger.debug(f"Cache hit for {location.city}")
					return weather

		try:
			params = {
				"latitude": location.latitude,
				"longitude": location.longitude,
				"timezone": location.timezone,
				"current": "temperature_2m,weather_code,wind_speed_10m,wind_direction_10m,is_day,relative_humidity_2m,pressure_msl",
				"daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,wind_speed_10m_max,wind_direction_10m_dominant,precipitation_sum,precipitation_probability_max,relative_humidity_2m_mean",
				"hourly": "temperature_2m,weather_code,wind_speed_10m,wind_direction_10m,relative_humidity_2m,precipitation,precipitation_probability,is_day",
				"forecast_days": 7,
			}

			url = f"{self.BASE_URL}/forecast?{urllib.parse.urlencode(params)}"
			req = urllib.request.Request(url, headers={"User-Agent": "EnigmaWeather/2.0"})

			with urllib.request.urlopen(req, timeout=10) as response:
				data = json.loads(response.read().decode("utf-8"))

			# Parse current conditions
			current_data = data["current"]
			current = CurrentWeather(
				temperature=current_data["temperature_2m"],
				condition=WeatherMapper.get_description(current_data["weather_code"]),
				weather_code=current_data["weather_code"],
				wind_speed=current_data["wind_speed_10m"],
				wind_direction=WeatherMapper.get_wind_direction(current_data["wind_direction_10m"]),
				humidity=current_data["relative_humidity_2m"],
				pressure=current_data.get("pressure_msl", 0.0),
				is_day=bool(current_data["is_day"]),
			)

			# Parse daily forecast
			daily_data = data["daily"]
			daily_forecast = []

			for i in range(len(daily_data["time"])):
				daily_forecast.append(DailyForecast(
					date=daily_data["time"][i],
					max_temp=daily_data["temperature_2m_max"][i],
					min_temp=daily_data["temperature_2m_min"][i],
					condition=WeatherMapper.get_description(daily_data["weather_code"][i]),
					weather_code=daily_data["weather_code"][i],
					wind_speed=daily_data["wind_speed_10m_max"][i],
					wind_direction=WeatherMapper.get_wind_direction(daily_data["wind_direction_10m_dominant"][i]),
					humidity=int(daily_data["relative_humidity_2m_mean"][i]),
					precipitation=daily_data["precipitation_sum"][i],
					precipitation_prob=int(daily_data["precipitation_probability_max"][i]),
					sunrise=daily_data.get("sunrise", [None])[i],
					sunset=daily_data.get("sunset", [None])[i],
				))

			hourly_forecast = []
			try:
				hourly_data = data["hourly"]
				current_hour = datetime.fromisoformat(current_data["time"]).replace(minute=0, second=0, microsecond=0)
				for i, time in enumerate(hourly_data["time"]):
					if datetime.fromisoformat(time) < current_hour:
						continue
					code = hourly_data["weather_code"][i]
					is_day = hourly_data["is_day"][i]
					if is_day not in (0, 1):
						raise ValueError("Invalid hourly day/night flag")
					hourly_forecast.append(HourlyForecast(
						time=time,
						temperature=float(hourly_data["temperature_2m"][i]),
						condition=WeatherMapper.get_description(code),
						weather_code=code,
						wind_speed=float(hourly_data["wind_speed_10m"][i]),
						wind_direction=WeatherMapper.get_wind_direction(hourly_data["wind_direction_10m"][i]),
						humidity=int(hourly_data["relative_humidity_2m"][i]),
						precipitation=float(hourly_data["precipitation"][i]),
						precipitation_prob=int(hourly_data["precipitation_probability"][i]),
						is_day=bool(is_day),
					))
			except (KeyError, IndexError, TypeError, ValueError) as error:
				logger.error("Hourly forecast data error: %s", error)
				hourly_forecast = []

			weather = WeatherData(
				location=location,
				current=current,
				daily_forecast=daily_forecast,
				updated_at=datetime.now(),
				hourly_forecast=hourly_forecast,
			)

			# Store in cache
			with self._lock:
				self._cache[cache_key] = (weather, datetime.now() + timedelta(seconds=self.CACHE_TTL))

			logger.debug(_("Fetched weather for %s") % location.city)
			return weather

		except Exception as e:
			logger.error(_("Weather fetch error: %s") % str(e))
			return None


# ============================================================================
# MAIN PLUGIN
# ============================================================================

class EnigmaWeatherPlugin:
	"""Main weather plugin interface."""

	def __init__(self):
		self.client = OpenMeteoClient()
		self.weather: Optional[WeatherData] = None
		self.last_location: Optional[Location] = None
		self.is_running = False

	def start(self):
		"""Start the plugin."""
		self.is_running = True
		logger.info(_("EnigmaWeather v2.0.0 started"))

	def stop(self):
		"""Stop the plugin."""
		self.is_running = False

	def search_locations(self, query: str) -> List[Location]:
		"""Search for locations."""
		return self.client.search_locations(query)

	def load_weather(self, location: Location) -> bool:
		"""Load weather for a location."""
		if not self.is_running:
			logger.error(_("Plugin is not running when trying to load weather"))
			return False

		self.weather = self.client.fetch_weather(location)
		if self.weather:
			self.last_location = location
			logger.info(_("Weather loaded successfully for %s") % location.city)
			return True
		logger.error(_("Failed to fetch weather for %s") % location.city)
		return False

	def get_formatted_data(self) -> Optional[Dict]:
		"""Get formatted weather data for UI display."""
		if not self.weather:
			return None

		return {
			"location": {
				"city": self.weather.location.city,
				"country": self.weather.location.country,
			},
			"current": {
				"temperature": WeatherMapper.format_temperature(self.weather.current.temperature),
				"condition": self.weather.current.condition,
				"icon": WeatherMapper.get_icon(self.weather.current.weather_code, self.weather.current.is_day),
				"wind": WeatherMapper.format_wind(
					self.weather.current.wind_speed,
					self.weather.current.wind_direction
				),
				"humidity": f"{self.weather.current.humidity}%",
				"pressure": f"{self.weather.current.pressure:.0f} hPa",
				"updated": self.weather.updated_at.strftime("%H:%M"),
			},
			"forecast": [
				{
					"date": day.date,
					"max_temp": WeatherMapper.format_temperature(day.max_temp),
					"min_temp": WeatherMapper.format_temperature(day.min_temp),
					"condition": day.condition,
					"icon": WeatherMapper.get_icon(day.weather_code),
					"wind": WeatherMapper.format_wind(day.wind_speed, day.wind_direction),
					"humidity": f"{day.humidity}%",
					"precipitation": f"{day.precipitation:.1f}mm",
					"precipitation_prob": f"{day.precipitation_prob}%",
					"sunrise": day.sunrise,
					"sunset": day.sunset,
				}
				for day in self.weather.daily_forecast
			],
		}


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

plugin_instance = EnigmaWeatherPlugin()


def fetch_satellite_frames(cancel):
	"""Yield recent AEMET infrared images, newest first, with their UTC timestamps."""
	root = "https://www.aemet.es"
	headers = {"User-Agent": "EnigmaWeather/2.0"}
	request = urllib.request.Request(root + "/es/eltiempo/observacion/satelite/infra", headers=headers)
	with urllib.request.urlopen(request, timeout=15) as response:
		page = response.read(2 * 1024 * 1024 + 1)
	if len(page) > 2 * 1024 * 1024:
		raise ValueError("AEMET satellite page is too large")
	paths = sorted(set(re.findall(rb"/imagenes_d/eltiempo/observacion/satelite/(\d{12})_s93g\.jpg", page)))[-24:]
	if not paths:
		raise ValueError("No infrared satellite image found on the AEMET page")
	total_size = 0
	failures = 0
	for value in reversed(paths):
		if cancel.is_set():
			return
		stamp = value.decode("ascii")
		try:
			timestamp = datetime.strptime(stamp, "%Y%m%d%H%M")
			path = "/imagenes_d/eltiempo/observacion/satelite/%s_s93g.jpg" % stamp
			request = urllib.request.Request(root + path, headers=headers)
			with urllib.request.urlopen(request, timeout=15) as response:
				if response.headers.get_content_type() != "image/jpeg":
					raise ValueError("AEMET satellite response is not a JPEG image")
				limit = min(1024 * 1024, 6 * 1024 * 1024 - total_size)
				image = response.read(limit + 1)
			if len(image) > limit or not image.startswith(b"\xff\xd8\xff"):
				raise ValueError("Invalid or oversized AEMET satellite image")
		except (OSError, ValueError) as error:
			logger.warning("Satellite image %s unavailable: %s", stamp, error)
			yield None, None, str(error)
			failures += 1
			if failures >= 3:
				return
			continue
		failures = 0
		total_size += len(image)
		yield image, timestamp, None


class WeatherCanvas:
	"""Draw an independent, resolution-scaled weather dashboard."""

	BACKGROUND = 0x0B1522
	PANEL = 0x142538
	SELECTED = 0x25445E
	TEXT = 0xEEF4FA
	MUTED = 0x9FB4C8
	WARM = 0xFFB65C
	COOL = 0x6ECDF2
	CLOUD = 0xD6E4ED
	RAIN = 0x63BDF1
	HOURLY_ROWS = 7

	def __init__(self, canvas, width, height):
		from enigma import gFont, RT_HALIGN_CENTER, RT_WRAP
		self.canvas = canvas
		self.sx = width / 1920.0
		self.sy = height / 1080.0
		self.font = gFont
		self.center = RT_HALIGN_CENTER
		self.wrap = RT_WRAP

	def rect(self, x, y, width, height, color):
		self.canvas.fill(int(x * self.sx), int(y * self.sy), max(1, int(width * self.sx)), max(1, int(height * self.sy)), color)

	def line(self, x1, y1, x2, y2, color):
		self.canvas.line(int(x1 * self.sx), int(y1 * self.sy), int(x2 * self.sx), int(y2 * self.sy), color)

	def text(self, x, y, width, height, value, size=28, color=TEXT, background=BACKGROUND, flags=0):
		self.canvas.writeText(int(x * self.sx), int(y * self.sy), int(width * self.sx), int(height * self.sy),
			color, background, self.font("Regular", max(1, int(size * self.sy))), str(value), flags)

	def disk(self, x, y, radius, color):
		for offset in range(-radius, radius + 1, 2):
			span = int(math.sqrt(max(0, radius * radius - offset * offset)))
			self.rect(x - span, y + offset, 2 * span + 1, 2, color)

	def symbol(self, code, day, x, y, size, background):
		"""Paint weather symbols from WMO conditions without external image files."""
		scale = size / 100.0

		def circle(cx, cy, radius, color):
			self.disk(x + int(cx * scale), y + int(cy * scale), max(1, int(radius * scale)), color)

		def stroke(x1, y1, x2, y2, color):
			for shift in (-1, 0, 1):
				self.line(x + (x1 + shift) * scale, y + y1 * scale, x + (x2 + shift) * scale, y + y2 * scale, color)

		def block(cx, cy, width, height, color):
			self.rect(x + cx * scale, y + cy * scale, width * scale, height * scale, color)

		if code in (0, 1, 2):
			circle(38, 31, 18, self.WARM if day else self.CLOUD)
			if day:
				for angle in range(0, 360, 45):
					radians = math.radians(angle)
					stroke(38 + 23 * math.cos(radians), 31 + 23 * math.sin(radians),
						38 + 30 * math.cos(radians), 31 + 30 * math.sin(radians), self.WARM)
			else:
				circle(46, 23, 16, background)
		if code != 0:
			circle(31, 55, 16, self.CLOUD)
			circle(50, 45, 22, self.CLOUD)
			circle(70, 56, 15, self.CLOUD)
			block(26, 55, 49, 16, self.CLOUD)
		if 51 <= code <= 67 or 80 <= code <= 82:
			for px in (32, 50, 68):
				stroke(px + 5, 76, px, 91, self.RAIN)
		elif 71 <= code <= 77 or code in (85, 86):
			for px in (32, 50, 68):
				stroke(px, 77, px, 91, self.CLOUD)
				stroke(px - 5, 84, px + 5, 84, self.CLOUD)
		elif code in (95, 96, 99):
			stroke(53, 70, 43, 82, self.WARM)
			stroke(43, 82, 54, 82, self.WARM)
			stroke(54, 82, 44, 96, self.WARM)
		elif code in (45, 48):
			stroke(22, 79, 78, 79, self.MUTED)
			stroke(29, 88, 71, 88, self.MUTED)

	def date(self, value):
		day = datetime.strptime(value, "%Y-%m-%d")
		names = [_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"), _("Friday"), _("Saturday"), _("Sunday")]
		return "%s %s" % (names[day.weekday()], day.strftime("%d/%m"))

	def footer(self):
		from enigma import eLabel, eSize
		font = self.font("Regular", max(1, int(21 * self.sy)))
		bounds = eSize(10000, 10000)
		yellow_width = eLabel.calculateTextSize(font, _("YELLOW") + ":", bounds, True).width() / self.sx
		gap = max(1, 120 - yellow_width)
		actions = (
			(_("RED"), _("Forecast days"), 0xFF6060),
			(_("GREEN"), _("Forecast hours"), 0x71D878),
			(_("YELLOW"), _("Search"), 0xF5D95A),
			(_("BLUE"), _("Select"), 0x65AFFF),
			(_("MENU"), _("Satellite"), self.TEXT),
			(_("OK"), _("Refresh"), self.TEXT),
		)
		for index, (key, action, color) in enumerate(actions):
			x = 65 + index * 300
			key_width = eLabel.calculateTextSize(font, key + ":", bounds, True).width() / self.sx
			self.text(x, 1022, key_width + gap, 40, key + ":", 21, color)
			self.text(x + key_width + gap, 1022, max(1, 295 - key_width - gap), 40, action, 19, self.TEXT)

	def message(self, message):
		self.canvas.clear()
		self.rect(0, 0, 1920, 1080, self.BACKGROUND)
		self.text(65, 44, 1750, 56, "ENIGMA WEATHER", 38, self.COOL)
		self.text(80, 160, 1700, 770, message, 30, flags=self.wrap)
		self.footer()
		self.canvas.flush()

	def dashboard(self, weather):
		self.canvas.clear()
		self.rect(0, 0, 1920, 1080, self.BACKGROUND)
		self.text(65, 34, 900, 46, "ENIGMA WEATHER", 34, self.COOL)
		self.text(65, 92, 1020, 52, "%s, %s" % (weather.location.city, weather.location.country), 39)
		self.text(1360, 42, 480, 36, _("Updated") + " " + weather.updated_at.strftime("%H:%M"), 23, self.MUTED, flags=self.center)
		self.rect(60, 160, 790, 310, self.PANEL)
		current = weather.current
		self.symbol(current.weather_code, current.is_day, 95, 185, 190, self.PANEL)
		self.text(320, 185, 460, 92, WeatherMapper.format_temperature(current.temperature), 65, self.TEXT, self.PANEL)
		self.text(320, 285, 480, 42, current.condition, 30, self.TEXT, self.PANEL)
		self.text(100, 378, 700, 45, _("Wind") + ": " + WeatherMapper.format_wind(current.wind_speed, current.wind_direction), 26, self.MUTED, self.PANEL)
		self.text(100, 423, 700, 36, _("Humidity") + ": %d%%    " % current.humidity + _("Pressure") + ": %.0f hPa" % current.pressure, 23, self.MUTED, self.PANEL)

		for index, forecast in enumerate(weather.daily_forecast[1:4]):
			top = 160 + index * 105
			self.rect(890, top, 970, 96, self.PANEL)
			self.symbol(forecast.weather_code, True, 900, top + 8, 78, self.PANEL)
			self.text(1000, top + 9, 365, 34, self.date(forecast.date), 25, self.TEXT, self.PANEL)
			self.text(1000, top + 48, 500, 35, forecast.condition, 23, self.MUTED, self.PANEL)
			self.text(1510, top + 22, 315, 40, "%s / %s" % (WeatherMapper.format_temperature(forecast.max_temp), WeatherMapper.format_temperature(forecast.min_temp)), 27, self.WARM, self.PANEL, self.center)

		self.text(65, 495, 1200, 40, _("7-day forecast"), 29, self.TEXT)
		self.text(1210, 499, 210, 35, _("Maximum"), 22, self.WARM)
		self.text(1430, 499, 210, 35, _("Minimum"), 22, self.COOL)
		self.text(1630, 499, 220, 35, _("Rain chance"), 22, self.MUTED)
		days = weather.daily_forecast[:7]
		if days:
			low = min(day.min_temp for day in days)
			high = max(day.max_temp for day in days)
			span = max(high - low, 1)
			points = []
			for index, day in enumerate(days):
				x = 160 + index * 260
				ymax = 575 + int((high - day.max_temp) * 170 / span)
				ymin = 575 + int((high - day.min_temp) * 170 / span)
				points.append((x, ymax, ymin))
				self.text(x - 100, 550, 200, 30, self.date(day.date), 20, self.MUTED, flags=self.center)
				self.symbol(day.weather_code, True, x - 40, 775, 80, self.BACKGROUND)
				self.text(x - 100, 863, 200, 34, "%d%%" % day.precipitation_prob, 23, self.COOL, flags=self.center)
				self.text(x - 100, 905, 200, 34, "%.0f / %.0f °C" % (day.max_temp, day.min_temp), 23, self.TEXT, flags=self.center)
			for left, right in zip(points, points[1:]):
				for offset in (-1, 0, 1):
					self.line(left[0], left[1] + offset, right[0], right[1] + offset, self.WARM)
					self.line(left[0], left[2] + offset, right[0], right[2] + offset, self.COOL)
			for x, ymax, ymin in points:
				self.disk(x, ymax, 5, self.WARM)
				self.disk(x, ymin, 5, self.COOL)
		self.footer()
		self.canvas.flush()

	def details(self, weather, page):
		self.canvas.clear()
		self.rect(0, 0, 1920, 1080, self.BACKGROUND)
		self.text(65, 35, 1750, 50, _("Daily forecast"), 36, self.COOL)
		self.text(65, 93, 1750, 40, "%s, %s" % (weather.location.city, weather.location.country), 25, self.MUTED)
		for row, day in enumerate(weather.daily_forecast[page * 7:(page + 1) * 7]):
			top = 155 + row * 116
			self.rect(60, top, 1800, 106, self.PANEL)
			self.symbol(day.weather_code, True, 76, top + 9, 80, self.PANEL)
			self.text(175, top + 9, 350, 39, self.date(day.date), 27, self.TEXT, self.PANEL)
			self.text(175, top + 53, 360, 37, day.condition, 23, self.MUTED, self.PANEL)
			self.text(555, top + 10, 300, 35, _("Maximum") + " / " + _("Minimum"), 21, self.MUTED, self.PANEL)
			self.text(555, top + 53, 300, 37, "%s / %s" % (WeatherMapper.format_temperature(day.max_temp), WeatherMapper.format_temperature(day.min_temp)), 25, self.WARM, self.PANEL)
			self.text(875, top + 10, 300, 35, _("Rain chance") + ": %d%%" % day.precipitation_prob, 22, self.COOL, self.PANEL)
			self.text(875, top + 53, 300, 35, _("Precipitation") + ": %.1f mm" % day.precipitation, 22, self.TEXT, self.PANEL)
			self.text(1195, top + 10, 600, 35, _("Wind") + ": " + WeatherMapper.format_wind(day.wind_speed, day.wind_direction), 22, self.TEXT, self.PANEL)
			self.text(1195, top + 53, 600, 35, _("Humidity") + ": %d%%" % day.humidity, 22, self.MUTED, self.PANEL)
		self.text(65, 1000, 1750, 40, _("UP/DOWN: More days    RED/EXIT: Back"), 24, self.MUTED)
		self.canvas.flush()

	def hourly(self, weather, offset, selected):
		self.canvas.clear()
		self.rect(0, 0, 1920, 1080, self.BACKGROUND)
		self.text(65, 35, 1750, 50, _("Hourly forecast"), 36, self.COOL)
		self.text(65, 93, 1750, 40, "%s, %s" % (weather.location.city, weather.location.country), 25, self.MUTED)
		if not weather.hourly_forecast:
			self.text(65, 155, 1750, 50, _("Hourly forecast unavailable."), 27)
		for row, hour in enumerate(weather.hourly_forecast[offset:offset + self.HOURLY_ROWS]):
			top = 155 + row * 116
			background = self.SELECTED if offset + row == selected else self.PANEL
			self.rect(60, top, 1800, 106, background)
			self.symbol(hour.weather_code, hour.is_day, 76, top + 9, 80, background)
			self.text(175, top + 9, 350, 39, "%s  %s" % (self.date(hour.time[:10]), hour.time[11:16]), 25, self.TEXT, background)
			self.text(175, top + 53, 360, 37, hour.condition, 23, self.MUTED, background)
			self.text(555, top + 10, 300, 35, _("Temperature"), 21, self.MUTED, background)
			self.text(555, top + 53, 300, 37, WeatherMapper.format_temperature(hour.temperature), 25, self.WARM, background)
			self.text(875, top + 10, 300, 35, _("Rain chance") + ": %d%%" % hour.precipitation_prob, 22, self.COOL, background)
			self.text(875, top + 53, 300, 35, _("Precipitation") + ": %.1f mm" % hour.precipitation, 22, self.TEXT, background)
			self.text(1195, top + 10, 600, 35, _("Wind") + ": " + WeatherMapper.format_wind(hour.wind_speed, hour.wind_direction), 22, self.TEXT, background)
			self.text(1195, top + 53, 600, 35, _("Humidity") + ": %d%%" % hour.humidity, 22, self.MUTED, background)
		count = len(weather.hourly_forecast)
		if count > self.HOURLY_ROWS:
			track_height = 802
			thumb_height = max(12, track_height * self.HOURLY_ROWS // count)
			thumb_top = 155 + (track_height - thumb_height) * offset // (count - self.HOURLY_ROWS)
			self.rect(1874, 155, 14, track_height, self.PANEL)
			self.rect(1874, thumb_top, 14, thumb_height, self.COOL)
		self.text(65, 1000, 1750, 40, _("UP/DOWN: Hour    LEFT/RIGHT: Page    GREEN/EXIT: Back"), 24, self.MUTED)
		self.canvas.flush()


# ============================================================================
# ENIGMA2 PLUGIN INTERFACE
# ============================================================================

def main(session, **kwargs):
	"""Main entry point for the plugin."""
	from Screens.Screen import Screen
	from Components.Label import Label
	from Components.ActionMap import ActionMap
	from Components.Sources.CanvasSource import CanvasSource
	from enigma import getDesktop

	class SatelliteScreen(Screen):
		skin = """<screen position="fill" flags="wfNoBorder" backgroundColor="#0b1522">
			<widget name="title" position="65,35" size="1750,50" font="Regular;36" foregroundColor="#6ecdf2" backgroundColor="#0b1522" transparent="0" />
			<widget name="status" position="65,95" size="1750,45" font="Regular;25" foregroundColor="#eef4fa" backgroundColor="#0b1522" transparent="0" />
			<widget name="image" position="center,145" size="800,800" scale="1" />
			<widget name="source" position="65,960" size="1750,42" font="Regular;24" foregroundColor="#eef4fa" backgroundColor="#0b1522" transparent="0" />
			<widget name="help" position="65,1015" size="1750,40" font="Regular;23" foregroundColor="#9fb4c8" backgroundColor="#0b1522" transparent="0" />
		</screen>"""

		def __init__(self, session):
			from Components.Pixmap import Pixmap
			from enigma import eTimer
			Screen.__init__(self, session)
			self.active = True
			self.cancel_download = threading.Event()
			self.results = queue.Queue()
			self.frames = []
			self.frame_index = 0
			self.failures = 0
			self.playing = False
			self.timer = eTimer()
			self.timer.callback.append(self.processImage)
			self.animation = eTimer()
			self.animation.callback.append(self.advanceFrame)
			self["title"] = Label(_("Satellite clouds: Western Europe"))
			self["status"] = Label(_("Loading satellite images..."))
			self["source"] = Label("© AEMET / EUMETSAT")
			self["help"] = Label(_("OK: Play/Pause    LEFT/RIGHT: Image    EXIT: Back"))
			self["image"] = Pixmap()
			self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"], {
				"cancel": self.close, "ok": self.togglePlayback,
				"left": self.previousFrame, "right": self.nextFrame,
			}, -1)
			self.onLayoutFinish.append(self.loadImage)
			self.onClose.append(self.stopImage)

		def stopImage(self):
			self.active = False
			self.cancel_download.set()
			self.timer.stop()
			self.animation.stop()

		def loadImage(self):
			self.timer.start(250, False)
			threading.Thread(target=self.downloadImage, daemon=True).start()

		def downloadImage(self):
			try:
				for image, timestamp, error in fetch_satellite_frames(self.cancel_download):
					self.results.put(("frame", image, timestamp, error))
			except (OSError, ValueError) as error:
				logger.error("Satellite image error: %s", error)
				self.results.put(("error", str(error)))
				return
			self.results.put(("done",))

		def processImage(self):
			while self.active:
				try:
					result = self.results.get_nowait()
				except queue.Empty:
					return
				if result[0] == "error":
					self.timer.stop()
					self.showError(result[1])
					return
				if result[0] == "done":
					self.timer.stop()
					if not self.frames:
						self.showError(_("No satellite images could be loaded."))
						return
					self.frames.sort(key=lambda frame: frame[1])
					self.frame_index = 0
					if self.failures:
						self["status"].setText(_("Some satellite images could not be loaded (%d).") % self.failures)
					elif len(self.frames) == 1:
						self["status"].setText(_("Only one satellite image is available."))
					else:
						self["status"].setText("")
					if self.displayFrame() and len(self.frames) > 1:
						self.playing = True
						self.animation.start(1000, False)
					return
				image, timestamp, error = result[1:]
				if error:
					self.failures += 1
				else:
					self.frames.append((image, timestamp))
					self["status"].setText(_("Loading satellite images: %d") % len(self.frames))
					if len(self.frames) == 1:
						self.showImage(image, timestamp)

		def displayFrame(self):
			if not self.frames:
				return False
			image, timestamp = self.frames[self.frame_index]
			return self.showImage(image, timestamp)

		def advanceFrame(self):
			if self.active and self.playing and self.frames:
				self.frame_index = (self.frame_index + 1) % len(self.frames)
				if not self.displayFrame():
					self.pausePlayback()

		def pausePlayback(self):
			self.playing = False
			self.animation.stop()

		def togglePlayback(self):
			if self.playing:
				self.pausePlayback()
			elif len(self.frames) > 1 and not self.timer.isActive():
				self.playing = True
				self.animation.start(1000, False)

		def previousFrame(self):
			self.moveFrame(-1)

		def nextFrame(self):
			self.moveFrame(1)

		def moveFrame(self, direction):
			if self.frames and not self.timer.isActive():
				self.pausePlayback()
				self.frame_index = (self.frame_index + direction) % len(self.frames)
				self.displayFrame()

		def showError(self, error):
			if self.active:
				self["status"].setText(_("Satellite image unavailable: %s") % error)

		def showImage(self, image, timestamp):
			if not self.active:
				return False
			from Tools.LoadPixmap import LoadPixmap
			path = None
			try:
				with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as image_file:
					path = image_file.name
					image_file.write(image)
				pixmap = LoadPixmap(path, cached=False)
				if not pixmap:
					raise ValueError("Unable to decode satellite image")
				self["image"].instance.setPixmap(pixmap)
				self["source"].setText("© AEMET / EUMETSAT  |  %s UTC  |  %d/%d" % (
					timestamp.strftime("%Y-%m-%d %H:%M"), self.frame_index + 1, len(self.frames)))
				return True
			except (OSError, ValueError) as error:
				logger.error("Satellite image display error: %s", error)
				self.showError(str(error))
				return False
			finally:
				if path:
					try:
						unlink(path)
					except OSError as error:
						logger.warning("Unable to remove temporary satellite image: %s", error)

	class EnigmaWeatherScreen(Screen):
		skin = """<screen position="fill" flags="wfNoBorder" backgroundColor="#0b1522">
			<widget source="artwork" render="Canvas" position="fill" zPosition="1" />
		</screen>"""

		def __init__(self, session):
			from enigma import eTimer
			Screen.__init__(self, session)
			self.session = session
			self["artwork"] = CanvasSource()
			size = getDesktop(0).size()
			self.artwork = WeatherCanvas(self["artwork"], size.width(), size.height())
			self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "MenuActions"], {
				"cancel": self.back,
				"ok": self.refreshWeather,
				"yellow": self.searchLocation,
				"red": self.toggleDetails,
				"green": self.toggleHourly,
				"blue": self.selectLocationFromList,
				"menu": self.openSatellite,
				"up": self.previousItem,
				"down": self.nextItem,
				"upRepeated": self.previousHour,
				"downRepeated": self.nextHour,
				"left": self.previousHourPage,
				"right": self.nextHourPage,
			}, -1)
			self.locations = []
			self.selecting_location = False
			self.detail_view = None
			self.detail_page = 0
			self.hour_index = 0
			self.hour_offset = 0
			self.restoring = False
			self.active = True
			self.restore_results = queue.Queue(maxsize=1)
			self.restore_timer = eTimer()
			self.restore_timer.callback.append(self.finishRestore)
			self.onClose.append(self.stopRestore)
			plugin_instance.start()
			if plugin_instance.weather:
				self.showWeather()
				return
			try:
				self.saved_location = load_saved_location()
			except ValueError as error:
				logger.error("%s", error)
				self.artwork.message(_("Saved location is invalid. Press YELLOW to search again."))
				return
			if self.saved_location:
				plugin_instance.last_location = self.saved_location
				self.restoring = True
				self.artwork.message(_("Loading weather for: %s...\n\nPlease wait...") % self.saved_location.city)
				self.onLayoutFinish.append(self.restoreWeather)
			else:
				self.showWeather()

		def restoreWeather(self):
			self.restore_timer.start(250, False)
			threading.Thread(target=self.fetchSavedWeather, daemon=True).start()

		def fetchSavedWeather(self):
			self.restore_results.put(plugin_instance.client.fetch_weather(self.saved_location))

		def finishRestore(self):
			try:
				weather = self.restore_results.get_nowait()
			except queue.Empty:
				return
			self.restore_timer.stop()
			self.restoring = False
			if not self.active:
				return
			if plugin_instance.last_location != self.saved_location:
				self.showWeather()
			elif weather:
				plugin_instance.weather = weather
				self.showWeather()
			else:
				self.artwork.message(_("Error loading weather for: %s\n\nPress OK to try again.") % self.saved_location.city)

		def stopRestore(self):
			self.active = False
			self.restore_timer.stop()

		def refreshWeather(self):
			if self.restoring:
				return
			if plugin_instance.last_location:
				if not plugin_instance.load_weather(plugin_instance.last_location):
					self.artwork.message(_("Error loading weather for: %s") % plugin_instance.last_location.city)
					return
			self.showWeather()

		def showWeather(self):
			weather = plugin_instance.weather
			if not weather:
				self.artwork.message(_("No weather data available.") + "\n\n" + _("Press YELLOW to search for a city."))
			elif self.detail_view:
				if self.detail_view == "daily":
					self.detail_page = min(self.detail_page, max(0, (len(weather.daily_forecast) - 1) // 7))
					self.artwork.details(weather, self.detail_page)
				else:
					count = len(weather.hourly_forecast)
					self.hour_index = min(self.hour_index, max(0, count - 1))
					self.hour_offset = min(self.hour_offset, max(0, count - self.artwork.HOURLY_ROWS), self.hour_index)
					self.hour_offset = max(self.hour_offset, self.hour_index - self.artwork.HOURLY_ROWS + 1)
					self.artwork.hourly(weather, self.hour_offset, self.hour_index)
			else:
				self.artwork.dashboard(weather)

		def toggleDetails(self):
			weather = plugin_instance.weather
			if self.detail_view == "daily":
				self.detail_view = None
			elif weather and weather.daily_forecast:
				self.detail_view = "daily"
				self.detail_page = 0
			self.showWeather()

		def toggleHourly(self):
			if self.detail_view == "hourly":
				self.detail_view = None
			elif plugin_instance.weather:
				self.detail_view = "hourly"
				self.hour_index = 0
				self.hour_offset = 0
			self.showWeather()

		def back(self):
			if self.detail_view:
				self.detail_view = None
				self.showWeather()
			else:
				self.close()

		def previousPage(self):
			if self.detail_view == "daily" and self.detail_page > 0:
				self.detail_page -= 1
				self.showWeather()

		def nextPage(self):
			weather = plugin_instance.weather
			if self.detail_view == "daily" and weather:
				if (self.detail_page + 1) * 7 < len(weather.daily_forecast):
					self.detail_page += 1
					self.showWeather()

		def moveHour(self, step, page=False):
			weather = plugin_instance.weather
			if self.detail_view != "hourly" or not weather or not weather.hourly_forecast:
				return
			count = len(weather.hourly_forecast)
			rows = self.artwork.HOURLY_ROWS
			self.hour_index = min(max(0, self.hour_index + step), count - 1)
			if page:
				self.hour_offset = min(max(0, self.hour_offset + step), max(0, count - rows))
			self.hour_offset = min(self.hour_offset, self.hour_index)
			self.hour_offset = max(self.hour_offset, self.hour_index - rows + 1)
			self.showWeather()

		def previousItem(self):
			if self.detail_view == "hourly":
				self.previousHour()
			else:
				self.previousPage()

		def nextItem(self):
			if self.detail_view == "hourly":
				self.nextHour()
			else:
				self.nextPage()

		def previousHour(self):
			self.moveHour(-1)

		def nextHour(self):
			self.moveHour(1)

		def previousHourPage(self):
			self.moveHour(-self.artwork.HOURLY_ROWS, page=True)

		def nextHourPage(self):
			self.moveHour(self.artwork.HOURLY_ROWS, page=True)

		def searchLocation(self):
			if self.restoring:
				return
			from Screens.VirtualKeyBoard import VirtualKeyBoard
			self.session.openWithCallback(self.locationSearched, VirtualKeyBoard, title=_("Enter city name:"), text="")

		def locationSearched(self, location_name):
			if not location_name:
				self.selecting_location = False
				self.showWeather()
				return

			locations = plugin_instance.search_locations(location_name)
			if locations:
				self.locations = locations
				self.selecting_location = True
				text = _("SELECT LOCATION (Press BLUE to choose):") + "\n\n"
				for i, loc in enumerate(locations[:10]):
					text += "%d. %s, %s\n" % (i + 1, loc.city, loc.country)
				self.artwork.message(text + _("\nPress BLUE and enter number to select."))
			else:
				self.artwork.message(_("No locations found for: %s\n\n") % location_name + _("Press YELLOW to search again."))
				self.selecting_location = False

		def selectLocationFromList(self):
			if self.restoring:
				return
			if not self.selecting_location or not self.locations:
				self.artwork.message(_("No locations loaded.\n\nPress YELLOW to search first."))
				return

			from Screens.VirtualKeyBoard import VirtualKeyBoard
			title = _("Enter location number (1-%d):") % min(10, len(self.locations))
			self.session.openWithCallback(self.locationSelected, VirtualKeyBoard, title=title, text="")

		def locationSelected(self, index_str):
			if not index_str:
				self.selecting_location = False
				self.showWeather()
				return

			try:
				idx = int(index_str) - 1
			except ValueError:
				self.artwork.message(_("Invalid input.\n\nPlease enter a number.\n\n") + _("Press BLUE to try again."))
				return
			if not 0 <= idx < len(self.locations):
				self.artwork.message(_("Invalid selection.\n\nNumber must be between 1 and %d\n\n") % len(self.locations) + _("Press BLUE to try again."))
				return
			location = self.locations[idx]
			if not plugin_instance.load_weather(location):
				self.artwork.message(_("Error loading weather for: %s\n\nPress BLUE to try again.") % location.city)
				return
			save_location(location)
			self.selecting_location = False
			self.detail_view = None
			self.showWeather()

		def openSatellite(self):
			self.session.open(SatelliteScreen)

	session.open(EnigmaWeatherScreen)


def Plugins(**kwargs):
	"""Return plugin descriptors for Enigma2."""
	from Plugins.Plugin import PluginDescriptor

	return PluginDescriptor(
		name=_("EnigmaWeather"),
		description=_("Modern weather plugin using Open-Meteo API"),
		where=[PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU],
		icon="EnigmaWeather.png",
		needsRestart=False,
		fnc=main
	)
