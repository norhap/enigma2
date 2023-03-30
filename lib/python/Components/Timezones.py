from errno import ENOENT
from os import environ, path, symlink, unlink, walk
from os.path import exists, isfile, join as pathjoin, realpath
from time import gmtime, localtime, strftime, time, tzset
from xml.etree.cElementTree import ParseError, parse

from Components.config import ConfigSelection, ConfigSubsection, config
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
DEFAULT_ZONE = "Madrid"
TIMEZONE_FILE = "/etc/timezone.xml"  # This should be SCOPE_TIMEZONES_FILE!  This file moves arond the filesystem!!!  :(
TIMEZONE_DATA = "/usr/share/zoneinfo/"  # This should be SCOPE_TIMEZONES_DATA!
OSD_LANGUAGE = {
	# Init default user language
	"Abu Dhabi": "ar_AE",
	"Abuja": "en_NG",
	"Accra": "en_GH",
	"Addis Ababa": "am_ET",
	"Algiers": "ar_DZ",
	"Amman": "ar_JO",
	"Amsterdam": "nl_NL",
	"Andorra la Vella": "ca_AD",
	"Ankara": "tr_TR",
	"Antananarivo": "fr_MG",
	"Apia": "en_WS",
	"Ashgabat": "tk_TM",
	"Asmara": "ar_ER",
	"Astana": "kk_KZ",
	"Asunción": "es_PY",
	"Athens": "el_GR",
	"Baghdad": "ar_IQ",
	"Baku": "az_AZ",
	"Bamako": "fr_ML",
	"Bandar Seri Begawan": "ms_BN",
	"Bangkok": "th_TH",
	"Bangui": "fr_CF",
	"Banjul": "en_GM",
	"Basseterre": "en_KN",
	"Beijing": "zh_CN",
	"Beirut": "ar_LB",
	"Belgrade": "sr_RS",
	"Belmopan": "en_BZ",
	"Berlin": "de_DE",
	"Bern": "de_CH",
	"Bishkek": "ky_KG",
	"Bissau": "pt_GW",
	"Bogota": "es_CO",
	"Brasilia": "pt_BR",
	"Bratislava": "sk_SK",
	"Brazzaville": "fr_CG",
	"Bridgetown": "en_BB",
	"Brussels": "fr_BE",
	"Bucharest": "ro_RO",
	"Budapest": "hu_HU",
	"Buenos Aires": "es_AR",
	"Bujumbura": "fr_BI",
	"Cairo": "ar_EG",
	"Canberra": "en_AU",
	"Caracas": "es_VE",
	"Castries": "en_LC",
	"Chisinau": "ru_MD",
	"Conakry": "fr_GN",
	"Copenagen": "da_DK",
	"Dakar": "fr_SN",
	"Damascus": "ar_SY",
	"Dhaka": "bn_BD",
	"Dili": "pt_TL",
	"Djibouti": "ar_DJ",
	"Dodoma": "en_TZ",
	"Doha": "ar_QA",
	"Dublin": "en_IE",
	"Dushanbe": "tg_TJ",
	"East Jerusalem": "ar_PS",
	"Freetown": "en_SL",
	"Funafuti": "en_TV",
	"Gaborone": "en_BW",
	"Georgetown": "en_GY",
	"Guatemala City": "es_GT",
	"Hanoi": "vi_VN",
	"Harare": "en_ZW",
	"Havana": "es_CU",
	"Helsinki": "fi_FI",
	"Honiara": "en_SB",
	"Islamabad": "en_PK",
	"Jakarta": "in_ID",
	"Jerusalem": "he_IL",
	"Juba": "en_SS",
	"Kabul": "fa_AF",
	"Kampala": "en_UG",
	"Kathmandu": "ne_NP",
	"Khartoum": "en_SD",
	"Kiev": "uk_UA",
	"Kigali": "fr_RW",
	"Kingston": "en_JM",
	"Kingstown": "en_VC",
	"Kinshasa": "fr_CD",
	"Kuala Lumpur": "ms_MY",
	"Kuwait City": "ar_KW",
	"Libreville": "fr_GA",
	"Lilongwe": "en_MW",
	"Lima": "es_PE",
	"Lisbon": "pt_PT",
	"Ljubljana": "sl_SI",
	"Lomé": "fr_TG",
	"London": "en_US",
	"Luanda": "pt_AO",
	"Lusaka": "en_ZM",
	"Luxembourg": "lb_LU",
	"Madrid": "es_ES",
	"Majuro": "en_MH",
	"Malabo": "es_GQ",
	"Malé": "dv_MV",
	"Managua": "es_NI",
	"Manama": "ar_BH",
	"Manila": "fil_PH",
	"Maputo": "pt_MZ",
	"Maseru": "en_LS",
	"Mbabane": "en_SZ",
	"Melekeok": "en_PW",
	"Mexico City": "es_MX",
	"Minsk": "be_BY",
	"Mogadishu": "ar_SO",
	"Monaco": "fr_MC",
	"Monrovia": "en_LR",
	"Montevideo": "es_UY",
	"Moroni": "ar_KM",
	"Moscow": "ru_RU",
	"Muscat": "ar_OM",
	"Nairobi": "en_KE",
	"Nassau": "en_BS",
	"Naypyidaw": "my_MM",
	"N'Djamena": "ar_TD",
	"New Delhi": "en_IN",
	"Niamey": "fr_NE",
	"Nicosia": "el_CY",
	"Nouakchott": "ar_MR",
	"Nukualofa": "en_TO",
	"Oslo": "no_NO",
	"Ottawa": "en_CA",
	"Ouagadougou": "fr_BF",
	"Palikir": "en_FM",
	"Panama City": "es_PA",
	"Paramaribo": "nl_SR",
	"Paris": "fr_FR",
	"Phnom Penh": "km_KH",
	"Podgorica": "sr_ME",
	"Port Louis": "en_MU",
	"Port Moresby": "en_PG",
	"Port of Spain": "en_TT",
	"Port Vila": "en_VU",
	"Port-au-Prince": "fr_HT",
	"Porto Novo": "fr_BJ",
	"Prague": "cs_CZ",
	"Praia": "pt_CV",
	"Pretoria": "en_ZA",
	"Pristina": "sq_XK",
	"Pyongyang": "ko_KP",
	"Quito": "es_EC",
	"Rabat": "ar_MA",
	"Reykjavík": "is_IS",
	"Riga": "lv_LV",
	"Riyadh": "ar_SA",
	"Rome": "it_IT",
	"Roseau": "en_DM",
	"San José": "es_CR",
	"San Marino": "it_SM",
	"San Salvador": "es_SV",
	"Sana'a": "ar_YE",
	"Santiago": "es_CL",
	"Santo Domingo": "es_DO",
	"São Tomé": "pt_ST",
	"Sarajevo": "hr_BA",
	"Seoul": "ko_KR",
	"Singapore": "en_SG",
	"Skopje": "mk_MK",
	"Sofia": "bg_BG",
	"Sri Jayawardenapura Kotte": "si_LK",
	"St. George's": "en_GD",
	"St. John's": "en_AG",
	"Stockholm": "sv_SE",
	"Sucre": "es_BO",
	"Suva": "en_FJ",
	"Taipei": "zh_TW",
	"Tallinn": "et_EE",
	"Tarawa": "en_KI",
	"Tashkent": "zu_UZ",
	"Tbilisi": "ka_GE",
	"Tegucigalpa": "es_HN",
	"Tehran": "fa_IR",
	"Thimphu": "dz_BT",
	"Tirana": "sq_AL",
	"Tokyo": "ja_JP",
	"Tripoli": "ar_LY",
	"Tunis": "ar_TN",
	"Ulaanbaatar": "mn_MN",
	"Vaduz": "de_LI",
	"Valletta": "mt_MT",
	"Vatican City": "it_VA",
	"Victoria": "en_SC",
	"Vienna": "de_AT",
	"Vientiane": "lo_LA",
	"Vilnius": "lt_LT",
	"Warsaw": "pl_PL",
	"Washington D.C.": "en_US",
	"Wellington": "en_NZ",
	"Windhoek": "en_NA",
	"Yamoussoukro": "fr_CI",
	"Yaoundé": "en_CM",
	"Yaren": "en_NR",
	"Yerevan": "hy_AM",
	"Zagreb": "hr_HR"
}


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
	except (IOError, OSError) as err:
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
			print("[Timezones] Warning: No areas or zones found in '%s'!" % TIMEZONE_DATA)
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
				if exists(pathjoin(TIMEZONE_DATA, zonePath)):
					zones.append((zonePath, name))
				else:
					print("[Timezones] Warning: Classic time zone '%s' (%s) is not available in '%s'!" % (name, zonePath, TIMEZONE_DATA))
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
		tz = zone if area in ("Classic", "Generic") else pathjoin(area, zone)
		file = pathjoin(TIMEZONE_DATA, tz)
		if not isfile(file):
			print("[Timezones] Error: The time zone '%s' is not available!  Using 'UTC' instead." % tz)
			tz = "UTC"
			file = pathjoin(TIMEZONE_DATA, tz)
		print("[Timezones] Setting time zone to '%s'." % tz)
		try:
			unlink("/etc/localtime")
		except (IOError, OSError) as err:
			if err.errno != ENOENT:  # No such file or directory.
				print("[Timezones] Error %d: Unlinking '/etc/localtime'!  (%s)" % (err.errno, err.strerror))
		try:
			symlink(file, "/etc/localtime")
		except (IOError, OSError) as err:
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
