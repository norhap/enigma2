from errno import ENOENT
from os import environ, symlink, unlink, walk
from os.path import exists, isfile, join, realpath
from time import gmtime, localtime, strftime, tzset
from urllib.request import urlopen, Request
from Components.config import ConfigSelection, ConfigSubsection, config, ConfigBoolean, ConfigText
from Tools.Geolocation import geolocation
from Tools.Directories import fileReadXML, fileWriteLine
from Tools.StbHardware import setRTCoffset

MODULE_NAME = __name__.split(".")[-1]

# The DEFAULT_AREA setting is usable by the image maintainers to select the
# default UI mode and location settings used by their image.  If the value
# of "Classic" is used then images that use the "Time zone area" and
# "Time zone" settings will have the "Time zone area" set to "Classic" and the
# "Time zone" field will be an expanded version of the classic list of GMT
# related offsets.  Images that only use the "Time zone" setting should use
# "Classic" to maintain their chosen UI for time zone selection.  That is,
# users will only be presented with the list of GMT related offsets.
#
# The DEFAULT_ZONE is used to select the default time zone within the time
# zone area.  For example, if the "Time zone area" is selected to be
# "Europe" then the image maintainers can select an appropriate country or
# city within Europe as the default location in that time zone area.  Images
# can select any defaults they deem appropriate.
#
# NOTE: Even if the DEFAULT_AREA of "Classic" is selected a DEFAULT_ZONE
# must still be selected.
#
# For images that use both the "Time zone area" and "Time zone" configuration
# options then the DEFAULT_AREA should be set to an area most appropriate for
# the image.  For example, if "Europe" is selected then the DEFAULT_ZONE can
# be used to select a more appropriate time zone selection for the image.
#
# Please ensure that any defaults selected are valid, unique and available
# in the "/usr/share/zoneinfo/" directory tree.
#
DEFAULT_AREA = "Europe"
DEFAULT_ZONE = "London"
TIMEZONE_FILE = "/etc/timezone.xml"  # This should be SCOPE_TIMEZONES_FILE!  This file moves arond the filesystem!!!  :(
TIMEZONE_DATA = "/usr/share/zoneinfo/"  # This should be SCOPE_TIMEZONES_DATA!
LANGUAGE_CODE = "/usr/share/zoneinfo/LanguageCode"


def InitTimeZones():
	config.timezone = ConfigSubsection()
	config.timezone.area = ConfigSelection(default=DEFAULT_AREA, choices=timezones.getTimezoneAreaList())
	config.timezone.val = ConfigSelection(default=timezones.getTimezoneDefault(), choices=timezones.getTimezoneList())
	if not config.timezone.area.value and config.timezone.val.value.find("/") == -1:
		config.timezone.area.value = "Generic"
	try:
		tzLink = realpath("/etc/localtime")[20:]
		msgs = []
		if config.timezone.area.value == "Classic":
			if config.timezone.val.value != tzLink:
				msgs.append("time zone '%s' != '%s'" % (config.timezone.val.value, tzLink))
		else:
			tzSplit = tzLink.find("/")
			if tzSplit == -1:
				tzArea = "Generic"
				tzVal = tzLink
			else:
				tzArea = tzLink[:tzSplit]
				tzVal = tzLink[tzSplit + 1:]
			if config.timezone.area.value != tzArea:
				msgs.append("area '%s' != '%s'" % (config.timezone.area.value, tzArea))
			if config.timezone.val.value != tzVal:
				msgs.append("zone '%s' != '%s'" % (config.timezone.val.value, tzVal))
		if len(msgs):
			print("[Timezones] Warning: Enigma2 time zone does not match system time zone (%s), setting system to Enigma2 time zone!" % ",".join(msgs))
	except OSError as err:
		print("[Timezones] Error %d: Unable to resolve current time zone from '/etc/localtime'!  (%s)" % (err.errno, err.strerror))

	def timezoneAreaChoices(configElement):
		choices = timezones.getTimezoneList(area=configElement.value)
		config.timezone.val.setChoices(choices=choices, default=timezones.getTimezoneDefault(area=configElement.value, choices=choices))
		if config.timezone.val.saved_value and config.timezone.val.saved_value in [x[0] for x in choices]:
			config.timezone.val.value = config.timezone.val.saved_value

	def timezoneNotifier(configElement):
		timezones.activateTimezone(configElement.value, config.timezone.area.value)

	config.timezone.area.addNotifier(timezoneAreaChoices, initial_call=False)
	config.timezone.val.addNotifier(timezoneNotifier)


def languageCode():
	languagecode = ""
	config.misc.firstrun = ConfigBoolean(default=True)
	if exists(TIMEZONE_FILE) and config.misc.firstrun.value:
		geolocationData = geolocation.getGeolocationData(fields="status,message,timezone,proxy")
		tz = geolocationData.get("timezone", None)
		if tz:
			area, zone = tz.split("/", 1)
			config.timezone.area.value = area
			config.timezone.val.value = zone
			with open(TIMEZONE_FILE, "r") as fr:
				for city in fr.readlines():
					if config.timezone.val.value in city:
						languagecode = city.split('localeCode="')[1].split('" />')[0]
						config.osd.language = ConfigText(default=languagecode)
						config.osd.language.save()
						with open(LANGUAGE_CODE, "w") as fw:
							fw.write(languagecode)
						break
		else:
			try:
				header = {"User-Agent": "Enigma2 - TimeZone"}
				responseip = ""
				responsetz = ""
				# from requests import get
				# from json import loads
				# ip = get("https://freeipapi.com/api/json/", verify=False)  # FREE ALTERNATIVE https://freeipapi.com/api/json/
				# dictionary = loads(ip.content)
				# publicip = dictionary.get("ipAddress", "")
				publicip = "http://api.ipify.org?format=json/"  # FREE ALTERNATIVE https://reallyfreegeoip.org/json/
				iprequest = Request(publicip, headers=header)
				responseip = urlopen(iprequest)
				publicip = responseip.read()
				tz = f"http://worldtimeapi.org/api/ip:{publicip}"
				timezonerequest = Request(tz, headers=header)
				responsetz = urlopen(timezonerequest)
				timezone = responsetz.read()
				with open(TIMEZONE_DATA + "timezone", "wb") as tzwrite:
					tzwrite.write(timezone)
				with open(TIMEZONE_DATA + "timezone", "r") as tzread:
					result = tzread.readlines()
					for tz in result:
						if "timezone" in tz:
							config.timezone.area.value = tz.split('"timezone":"')[1].split('/')[0]
							config.timezone.val.value = tz.split('/')[1].split('",')[0]
						with open(TIMEZONE_FILE, "r") as fr:
							for city in fr.readlines():
								if config.timezone.val.value in city:
									languagecode = city.split('localeCode="')[1].split('" />')[0]
									config.osd.language = ConfigText(default=languagecode)
									config.osd.language.save()
									with open(LANGUAGE_CODE, "w") as fw:
										fw.write(languagecode)
									break
			except Exception:
				pass
	else:
		if exists(LANGUAGE_CODE):
			with open(LANGUAGE_CODE, "r") as fr:
				languagecode = fr.read().split('\n', 1)[0]
		elif exists(TIMEZONE_FILE):
			with open(TIMEZONE_FILE, "r") as fr:
				for city in fr.readlines():
					if config.timezone.val.value in city:
						languagecode = city.split('localeCode="')[1].split('" />')[0]
						with open(LANGUAGE_CODE, "w") as fw:
							fw.write(languagecode)
							break
		else:
			languagecode = "es_ES"
	return languagecode


class Timezones:
	def __init__(self):
		self.timezones = {}
		self.loadTimezones()
		self.readTimezones()
		self.callbacks = []

	def loadTimezones(self):  # Scan the zoneinfo directory tree and all load all time zones found.
		commonTimezoneNames = {
			"Antarctica/DumontDUrville": "Dumont d'Urville",
			"Asia/Ho_Chi_Minh": "Ho Chi Minh City",
			"Atlantic/Canary": "Canary Islands",
			"Australia/LHI": None,  # Duplicate entry - Exclude from list.
			"Australia/Lord_Howe": "Lord Howe Island",
			"Australia/North": "Northern Territory",
			"Australia/South": "South Australia",
			"Australia/West": "Western Australia",
			"Brazil/DeNoronha": "Fernando de Noronha",
			"Pacific/Chatham": "Chatham Islands",
			"Pacific/Easter": "Easter Island",
			"Pacific/Galapagos": "Galapagos Islands",
			"Pacific/Gambier": "Gambier Islands",
			"Pacific/Johnston": "Johnston Atoll",
			"Pacific/Marquesas": "Marquesas Islands",
			"Pacific/Midway": "Midway Islands",
			"Pacific/Norfolk": "Norfolk Island",
			"Pacific/Pitcairn": "Pitcairn Islands",
			"Pacific/Wake": "Wake Island",
		}
		for (root, dirs, files) in walk(TIMEZONE_DATA):
			base = root[len(TIMEZONE_DATA):]
			if base.startswith("posix") or base.startswith("right"):  # Skip these alternate copies of the time zone data if they exist.
				continue
			if base == "":
				base = "Generic"
			area = None
			zones = []
			for file in files:
				if file[-4:] == ".tab" or file[-2:] == "-0" or file[-1:] == "0" or file[-2:] == "+0":  # No need for ".tab", "-0", "0", "+0" files.
					continue
				tz = "%s/%s" % (base, file)
				area, zone = tz.split("/", 1)
				name = commonTimezoneNames.get(tz, zone)  # Use the more common name if one is defined.
				if name is None:
					continue
				name = name
				area = area
				zone = zone
				zones.append((zone, name.replace("_", " ")))
			if area:
				if area in self.timezones:
					zones = self.timezones[area] + zones
				self.timezones[area] = self.gmtSort(zones)
		if len(self.timezones) == 0:
			print(f"[Timezones] Warning: No areas or zones found in '{TIMEZONE_DATA}'!")
			self.timezones["Generic"] = [("UTC", "UTC")]

	def gmtSort(self, zones):  # If the Zone starts with "GMT" then those Zones will be sorted in GMT order with GMT-14 first and GMT+12 last.
		data = {}
		for (zone, name) in zones:
			if name.startswith("GMT"):
				try:
					key = int(name[4:])
					key = (key * -1) + 15 if name[3:4] == "-" else key + 15
					key = "GMT%02d" % key
				except ValueError:
					key = "GMT15"
			else:
				key = name
			data[key] = (zone, name)
		return [data[x] for x in sorted(data.keys())]

	def readTimezones(self, filename=TIMEZONE_FILE):  # Read the timezones.xml file and load all time zones found.
		fileDom = fileReadXML(filename, source=MODULE_NAME)
		zones = []
		if fileDom:
			for zone in fileDom.findall("zone"):
				name = zone.get("name", "")
				name = name
				zonePath = zone.get("zone", "")
				zonePath = zonePath
				if exists(join(TIMEZONE_DATA, zonePath)):
					zones.append((zonePath, name))
				else:
					print(f"[Timezones] Warning: Classic time zone '{name}' {(zonePath)} is not available in '{TIMEZONE_DATA}'!")
			self.timezones["Classic"] = zones
		if len(zones) == 0:
			self.timezones["Classic"] = [("UTC", "UTC")]

	def getTimezoneAreaList(self):  # Return a sorted list of all Area entries.
		return sorted(list(self.timezones.keys()))

	def getTimezoneList(self, area=None):  # Return a sorted list of all Zone entries for an Area.
		if area is None:
			area = config.timezone.area.value
		return self.timezones.get(area, [("UTC", "UTC")])

	def getTimezoneDefault(self, area=None, choices=None):  # If there is no specific default then the first Zone in the Area will be returned.
		areaDefaultZone = {
			"Australia": "Sydney",
			"Classic": "Europe/%s" % DEFAULT_ZONE,
			"Etc": "GMT",
			"Europe": DEFAULT_ZONE,
			"Generic": "UTC",
			"Pacific": "Auckland"
		}
		if area is None:
			area = config.timezone.area.value
		if choices is None:
			choices = self.getTimezoneList(area=area)
		return areaDefaultZone.setdefault(area, choices[0][0])

	def activateTimezone(self, zone, area, runCallbacks=True):
		tz = zone if area in ("Classic", "Generic") else join(area, zone)
		file = join(TIMEZONE_DATA, tz)
		if not isfile(file):
			print("[Timezones] Error: The time zone '%s' is not available!  Using 'UTC' instead." % tz)
			tz = "UTC"
			file = join(TIMEZONE_DATA, tz)
		print("[Timezones] Setting time zone to '%s'." % tz)
		try:
			unlink("/etc/localtime")
		except OSError as err:
			if err.errno != ENOENT:  # No such file or directory.
				print("[Timezones] Error %d: Unlinking '/etc/localtime'!  (%s)" % (err.errno, err.strerror))
		try:
			symlink(file, "/etc/localtime")
		except OSError as err:
			print("[Timezones] Error %d: Linking '%s' to '/etc/localtime'!  (%s)" % (err.errno, file, err.strerror))
		fileWriteLine("/etc/timezone", "%s\n" % tz, source=MODULE_NAME)
		environ["TZ"] = ":%s" % tz
		try:
			tzset()
		except Exception:
			from enigma import e_tzset
			e_tzset()
		if exists("/proc/stb/fp/rtc_offset"):
			setRTCoffset()
		timeFormat = "%a %d-%b-%Y %H:%M:%S"
		print("[Timezones] Local time is '%s'  -  UTC time is '%s'." % (strftime(timeFormat, localtime(None)), strftime(timeFormat, gmtime(None))))
		if runCallbacks:
			for callback in self.callbacks:
				callback()

	def addCallback(self, callback):
		if callable(callback) and callback not in self.callbacks:
			self.callbacks.append(callback)

	def removeCallback(self, callback):
		if callback in self.callbacks:
			self.callbacks.remove(callback)


timezones = Timezones()
