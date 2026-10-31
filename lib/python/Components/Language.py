# -*- coding: UTF-8 -*-
import gettext
from locale import LC_CTYPE, LC_COLLATE, LC_TIME, LC_MONETARY, LC_MESSAGES, LC_NUMERIC, setlocale
from os import listdir, environ, system
from Tools.Directories import SCOPE_LANGUAGE, resolveFilename

DATADIR_PO = resolveFilename(SCOPE_LANGUAGE)
packageprefix = "enigma2-locale-"
_ = gettext.gettext


class Language:
	LANG_NAME = 0
	LANG_MAX = 6

	LANGUAGE_DATA = {
		"aa": ("Afar", _("Afar"), "Afaraf", "", "", ("DJ", "ER", "ET")),
		"ab": ("Abkhazian", _("Abkhazian"), "Аҧсуа", "", "", ("GE",)),
		"af": ("Afrikaans", _("Afrikaans"), "Afrikaans", "ISO-8859-1", "",
				("ZA", "NA", "BW")),
		"am": ("Amharic", _("Amharic"), "አማርኛ", "", "", ("ET",)),
		"ar": ("Arabic", _("Arabic"), "العربية", "", "",
				("SA", "IQ", "AE", "KW", "QA", "OM", "YE", "JO", "LB", "SY",
					"EG", "LY", "TD", "DZ", "MA", "TN", "PS", "SD", "SO", "DJ", "ER")),
		"as": ("Assamese", _("Assamese"), "অসমীয়া", "", "", ("IN",)),
		"az": ("Azerbaijani", _("Azerbaijani"), "Azərbaycanca", "", "", ("AZ",)),
		"be": ("Belarusian", _("Belarusian"), "Беларуская", "", "", ("BY",)),
		"bg": ("Bulgarian", _("Bulgarian"), "Български", "ISO-8859-2", "", ("BG", "MK")),
		"bn": ("Bengali", _("Bengali"), "বাংলা", "", "", ("BD", "IN")),
		"bm": ("Bambara", _("Bambara"), "Bamanankan", "", "",
				("ML", "BF", "CI", "GN", "NE", "SN")),
		"br": ("Breton", _("Breton"), "Brezhoneg", "", "", ("FR",)),
		"bs": ("Bosnian", _("Bosnian"), "Bosanski", "ISO-8859-2", "", ("BA",)),
		"ca": ("Catalan", _("Catalan"), "Català", "ISO-8859-15", "", ("ES", "FR", "AD", "IT")),
		"co": ("Corsican", _("Corsican"), "Corsu", "", "", ("FR",)),
		"cv": ("Chuvash", _("Chuvash"), "Чӑвашла", "", "", ("RU",)),
		"cs": ("Czech", _("Czech"), "Čeština", "ISO-8859-2", "", ("CZ", "SK")),
		"cy": ("Welsh", _("Welsh"), "Cymraeg", "", "", ("GB",)),
		"da": ("Danish", _("Danish"), "Dansk", "ISO-8859-1", "", ("DK", "FO")),
		"de": ("German", _("German"), "Deutsch", "ISO-8859-1", "",
				("DE", "AT", "CH", "LI", "LU")),
		"el": ("Greek", _("Greek"), "Ελληνικά", "ISO-8859-7", "", ("GR", "CY")),
		"en": ("English", _("English"), "English", "", "",
				("US", "GB", "AU", "CA", "IE", "NZ", "ZA", "HK", "SG", "MY", "PH")),
		"eo": ("Esperanto", _("Esperanto"), "Esperanto", "", "", ()),
		"es": ("Spanish / Castilian", _("Spanish / Castilian"), "Español", "ISO-8859-15", "",
				("ES", "AR", "BO", "CL", "CO", "CR", "CU", "DO", "EC", "GT", "HN", "MX",
					"NI", "PA", "PE", "PR", "PY", "SV", "US", "UY", "VE")),
		"et": ("Estonian", _("Estonian"), "Eesti", "", "", ("EE",)),
		"eu": ("Basque", _("Basque"), "Euskara", "", "", ("ES", "FR")),
		"fa": ("Persian", _("Persian"), "فارسی", "", "", ("IR", "AF", "TJ")),
		"ff": ("Fula", _("Fula"), "Fulfulde", "", "",
				("SN", "GM", "MR", "ML", "NE", "GN", "CI", "BF", "TG")),
		"fi": ("Finnish", _("Finnish"), "Suomi", "ISO-8859-1", "", ("FI", "SE")),
		"fo": ("Faroese", _("Faroese"), "Føroyskt", "", "", ("FO",)),
		"fr": ("French", _("French"), "Français", "ISO-8859-1", "",
				("FR", "BE", "CH", "LU", "MC", "CA", "RE", "MQ", "GP", "GF", "YT")),
		"fy": ("Frisian", _("Frisian"), "Frysk", "", "", ("NL",)),
		"ga": ("Irish", _("Irish"), "Gaeilge", "", "", ("IE",)),
		"gd": ("Scottish Gaelic", _("Scottish Gaelic"), "Gàidhlig", "", "", ("GB",)),
		"gl": ("Galician", _("Galician"), "Galego", "ISO-8859-15", "", ("ES",)),
		"gn": ("Guarani", _("Guarani"), "Avañe'ẽ", "", "", ("PY", "BR", "BO")),
		"gu": ("Gujarati", _("Gujarati"), "ગુજરાતી", "", "", ("IN",)),
		"ha": ("Hausa", _("Hausa"), "Hausa", "", "", ("NG", "NE", "SD")),
		"he": ("Hebrew", _("Hebrew"), "עברית", "ISO-8859-8", "", ("IL",)),
		"hi": ("Hindi", _("Hindi"), "हिन्दी", "", "", ("IN", "NP")),
		"hr": ("Croatian", _("Croatian"), "Hrvatski", "ISO-8859-2", "", ("HR", "BA")),
		"ht": ("Haitian", _("Haitian"), "Kreyòl Ayisyen", "", "", ("HT",)),
		"hu": ("Hungarian", _("Hungarian"), "Magyar", "ISO-8859-2", "", ("HU", "RO", "AT")),
		"hy": ("Armenian", _("Armenian"), "Հայերեն", "", "", ("AM",)),
		"id": ("Indonesian", _("Indonesian"), "Bahasa Indonesia", "", "", ("ID", "MY")),
		"ig": ("Igbo", _("Igbo"), "Igbo", "", "", ("NG",)),
		"is": ("Icelandic", _("Icelandic"), "Íslenska", "", "", ("IS",)),
		"it": ("Italian", _("Italian"), "Italiano", "ISO-8859-1", "", ("IT", "CH", "SM", "VA")),
		"ja": ("Japanese", _("Japanese"), "日本語", "", "", ("JP",)),
		"jv": ("Javanese", _("Javanese"), "Basa Jawa", "", "", ("ID",)),
		"ka": ("Georgian", _("Georgian"), "ქართული", "", "", ("GE",)),
		"kk": ("Kazakh", _("Kazakh"), "Қазақша", "", "", ("KZ",)),
		"km": ("Khmer", _("Khmer"), "ខ្មែរ", "", "", ("KH",)),
		"kn": ("Kannada", _("Kannada"), "ಕನ್ನಡ", "", "", ("IN",)),
		"ko": ("Korean", _("Korean"), "한국어", "", "", ("KR", "KP")),
		"ku": ("Kurdish", _("Kurdish"), "Kurdî", "", "", ("TR", "IQ", "IR", "SY")),
		"ky": ("Kyrgyz", _("Kyrgyz"), "Кыргызча", "", "", ("KG",)),
		"la": ("Latin", _("Latin"), "Latina", "", "", ("VA",)),
		"lb": ("Luxembourgish", _("Luxembourgish"), "Lëtzebuergesch", "", "", ("LU",)),
		"lo": ("Lao", _("Lao"), "ລາວ", "", "", ("LA",)),
		"lt": ("Lithuanian", _("Lithuanian"), "Lietuvių", "", "", ("LT",)),
		"lv": ("Latvian", _("Latvian"), "Latviešu", "", "", ("LV",)),
		"mg": ("Malagasy", _("Malagasy"), "Malagasy", "", "", ("MG",)),
		"mk": ("Macedonian", _("Macedonian"), "Македонски", "ISO-8859-5", "", ("MK",)),
		"mi": ("Maori", _("Maori"), "Te Reo Māori", "", "", ("NZ",)),
		"mn": ("Mongolian", _("Mongolian"), "Монгол", "", "", ("MN",)),
		"mr": ("Marathi", _("Marathi"), "मराठी", "", "", ("IN",)),
		"ms": ("Malay", _("Malay"), "Bahasa Melayu", "", "", ("MY", "BN", "SG")),
		"mt": ("Maltese", _("Maltese"), "Malti", "", "", ("MT",)),
		"my": ("Burmese", _("Burmese"), "မြန်မာစာ", "", "", ("MM",)),
		"ne": ("Nepali", _("Nepali"), "नेपाली", "", "", ("NP", "IN")),
		"nl": ("Dutch", _("Dutch"), "Nederlands", "ISO-8859-1", "", ("NL", "BE", "SR", "AW", "BQ")),
		"no": ("Norwegian", _("Norwegian"), "Norsk", "", "", ("NO", "SJ")),
		"ny": ("Chichewa", _("Chichewa"), "Chichewa", "", "", ("MW", "ZM", "TZ")),
		"oc": ("Occitan", _("Occitan"), "Occitan", "", "", ("FR",)),
		"or": ("Oriya", _("Oriya"), "ଓଡ଼ିଆ", "", "", ("IN",)),
		"pa": ("Punjabi", _("Punjabi"), "ਪੰਜਾਬੀ", "", "", ("IN", "PK")),
		"pap": ("Papiamento", _("Papiamento"), "Papiamentu", "", "", ("CW", "AW")),
		"pl": ("Polish", _("Polish"), "Polski", "ISO-8859-2", "", ("PL",)),
		"ps": ("Pashto", _("Pashto"), "پښتو", "", "", ("AF", "PK")),
		"pt": ("Portuguese", _("Portuguese"), "Português", "ISO-8859-1", "",
				("PT", "BR", "AO", "MZ", "CV", "ST", "GW", "TL")),
		"qu": ("Quechua", _("Quechua"), "Runasimi", "", "", ("PE", "BO", "EC")),
		"rm": ("Romansh", _("Romansh"), "Rumantsch", "", "", ("CH",)),
		"ro": ("Romanian", _("Romanian"), "Română", "ISO-8859-2", "", ("RO", "MD")),
		"ru": ("Russian", _("Russian"), "Русский", "KOI8-R", "", ("RU", "BY", "KZ", "UA")),
		"rw": ("Kinyarwanda", _("Kinyarwanda"), "Ikinyarwanda", "", "", ("RW",)),
		"si": ("Sinhala", _("Sinhala"), "සිංහල", "", "", ("LK",)),
		"sk": ("Slovak", _("Slovak"), "Slovenčina", "ISO-8859-2", "", ("SK",)),
		"sl": ("Slovenian", _("Slovenian"), "Slovenščina", "ISO-8859-2", "", ("SI",)),
		"sm": ("Samoan", _("Samoan"), "Gagana Sāmoa", "", "", ("WS", "AS", "NU")),
		"smi": ("Sami", _("Sami"), "Sámegiella", "", "", ("NO", "SE", "FI")),
		"sn": ("Shona", _("Shona"), "chiShona", "", "", ("ZW", "MZ")),
		"so": ("Somali", _("Somali"), "Soomaali", "", "", ("SO", "ET", "KE", "DJ")),
		"sq": ("Albanian", _("Albanian"), "Shqip", "ISO-8859-2", "", ("AL", "MK")),
		"sr": ("Serbian", _("Serbian"), "Српски", "", "", ("RS", "BA", "ME")),
		"st": ("Sesotho", _("Sesotho"), "Sesotho", "", "", ("LS", "ZA")),
		"su": ("Sundanese", _("Sundanese"), "Basa Sunda", "", "", ("ID",)),
		"sv": ("Swedish", _("Swedish"), "Svenska", "ISO-8859-1", "", ("SE", "FI", "AX")),
		"sw": ("Swahili", _("Swahili"), "Kiswahili", "", "",
				("KE", "TZ", "UG", "RW", "MZ", "CD", "SO", "BI")),
		"ta": ("Tamil", _("Tamil"), "தமிழ்", "", "", ("IN", "LK", "MY", "SG")),
		"te": ("Telugu", _("Telugu"), "తెలుగు", "", "", ("IN",)),
		"tg": ("Tajik", _("Tajik"), "Тоҷикӣ", "", "", ("TJ",)),
		"th": ("Thai", _("Thai"), "ไทย", "TIS-620", "", ("TH",)),
		"tk": ("Turkmen", _("Turkmen"), "Türkmençe", "", "", ("TM",)),
		"tl": ("Tagalog", _("Tagalog"), "Tagalog", "", "", ("PH",)),
		"tr": ("Turkish", _("Turkish"), "Türkçe", "ISO-8859-9", "", ("TR", "CY")),
		"tt": ("Tatar", _("Tatar"), "Татарча", "", "", ("RU",)),
		"ug": ("Uyghur", _("Uyghur"), "ئۇيغۇرچە", "", "", ("CN",)),
		"uk": ("Ukrainian", _("Ukrainian"), "Українська", "KOI8-U", "", ("UA",)),
		"ur": ("Urdu", _("Urdu"), "اردو", "", "", ("PK", "IN")),
		"uz": ("Uzbek", _("Uzbek"), "Oʻzbekcha", "", "", ("UZ",)),
		"vi": ("Vietnamese", _("Vietnamese"), "Tiếng Việt", "ISO-8859-7", "", ("VN",)),
		"wa": ("Walloon", _("Walloon"), "Walon", "", "", ("BE",)),
		"xh": ("Xhosa", _("Xhosa"), "isiXhosa", "", "", ("ZA",)),
		"yi": ("Yiddish", _("Yiddish"), "ייִדיש", "", "", ()),
		"yo": ("Yoruba", _("Yoruba"), "Yorùbá", "", "", ("NG", "BJ", "TG")),
		"zh": ("Chinese", _("Chinese"), "中文", "", "", ("CN", "TW", "HK", "SG", "MY")),
		"zu": ("Zulu", _("Zulu"), "isiZulu", "", "", ("ZA", "SZ", "MZ")),
	}

	def __init__(self):
		gettext.install('enigma2', resolveFilename(SCOPE_LANGUAGE))
		gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
		gettext.textdomain("enigma2")
		self.activeLanguage = 0
		self.catalog = None
		self.lang = {}
		self.InitLang()
		self.callbacks = []

	def InitLang(self):
		self.langlist = []
		self.langlistselection = []
		self.languageDirectory = listdir(DATADIR_PO)
		# FIXME make list dynamically
		# name, iso-639 language, iso-3166 country. Please don't mix language&country!
		self.addLanguage("Arabic", "ar", "AE", "ISO-8859-15")
		self.addLanguage("Български", "bg", "BG", "ISO-8859-15")
		self.addLanguage("Bokmål", "nb", "NO", "ISO-8859-15")
		self.addLanguage("Català", "ca", "AD", "ISO-8859-15")
		self.addLanguage("Česky", "cs", "CZ", "ISO-8859-15")
		self.addLanguage("SChinese", "zh", "CN", "UTF-8")
		self.addLanguage("TChinese", "zh", "HK", "UTF-8")
		self.addLanguage("Dansk", "da", "DK", "ISO-8859-15")
		self.addLanguage("Deutsch", "de", "DE", "ISO-8859-15")
		self.addLanguage("Ελληνικά", "el", "GR", "ISO-8859-7")
		self.addLanguage("English (AU)", "en", "AU", "ISO-8859-1")
		self.addLanguage("English (UK)", "en", "GB", "ISO-8859-15")
		self.addLanguage("English (US)", "en", "US", "ISO-8859-15")
		self.addLanguage("Español", "es", "ES", "ISO-8859-15")
		self.addLanguage("Eesti", "et", "EE", "ISO-8859-15")
		self.addLanguage("Persian", "fa", "IR", "ISO-8859-15")
		self.addLanguage("Suomi", "fi", "FI", "ISO-8859-15")
		self.addLanguage("Français", "fr", "FR", "ISO-8859-15")
		self.addLanguage("Frysk", "fy", "NL", "ISO-8859-15")
		self.addLanguage("Hebrew", "he", "IL", "ISO-8859-15")
		self.addLanguage("Hrvatski", "hr", "HR", "ISO-8859-15")
		self.addLanguage("Magyar", "hu", "HU", "ISO-8859-15")
		self.addLanguage("Indonesian", "id", "ID", "ISO-8859-15")
		self.addLanguage("Íslenska", "is", "IS", "ISO-8859-15")
		self.addLanguage("Italiano", "it", "IT", "ISO-8859-15")
		self.addLanguage("Kurdish", "ku", "KU", "ISO-8859-15")
		self.addLanguage("Lietuvių", "lt", "LT", "ISO-8859-15")
		self.addLanguage("Latviešu", "lv", "LV", "ISO-8859-15")
		self.addLanguage("Nederlands", "nl", "NL", "ISO-8859-15")
		self.addLanguage("Norsk Bokmål", "nb", "NO", "ISO-8859-15")
		self.addLanguage("Norsk", "no", "NO", "ISO-8859-15")
		self.addLanguage("Polski", "pl", "PL", "ISO-8859-15")
		self.addLanguage("Português", "pt", "PT", "ISO-8859-15")
		self.addLanguage("Português do Brasil", "pt", "BR", "ISO-8859-15")
		self.addLanguage("Romanian", "ro", "RO", "ISO-8859-15")
		self.addLanguage("Русский", "ru", "RU", "ISO-8859-15")
		self.addLanguage("Slovensky", "sk", "SK", "ISO-8859-15")
		self.addLanguage("Slovenščina", "sl", "SI", "ISO-8859-15")
		self.addLanguage("Srpski", "sr", "YU", "ISO-8859-15")
		self.addLanguage("Svenska", "sv", "SE", "ISO-8859-15")
		self.addLanguage("ภาษาไทย", "th", "TH", "ISO-8859-15")
		self.addLanguage("Türkçe", "tr", "TR", "ISO-8859-15")
		self.addLanguage("Українська", "uk", "UA", "ISO-8859-15")
		self.addLanguage("Tiếng Việt", "vi", "VN", "UTF-8")

	def addLanguage(self, name, lang, country, encoding):
		try:
			if lang in self.languageDirectory or (lang + "_" + country) in self.languageDirectory:
				self.lang[str(lang + "_" + country)] = ((name, lang, country, encoding))
				self.langlist.append(str(lang + "_" + country))
		except:
			print(f"[Language] Language {str(name)} not found")
		self.langlistselection.append((str(lang + "_" + country), name))

	def activateLanguage_TRY(self, locale):
		if locale not in self.lang:
			print(f"[Language] Selected language {locale} is not installed, fallback to es_ES!")
			locale = "es_ES"
		lang = self.lang[locale]
		print(f"[Language] Activating language {lang[0]}")
		self.catalog = gettext.translation('enigma2', resolveFilename(SCOPE_LANGUAGE), languages=[locale], fallback=True)
		self.catalog.install(names=("ngettext", "pgettext"))
		self.activeLanguage = locale
		# LC_ALL use default (C) locale = getlocale() then don't include it in this for.
		for category in [LC_CTYPE, LC_COLLATE, LC_TIME, LC_MONETARY, LC_MESSAGES, LC_NUMERIC]:
			try:
				setlocale(category, locale)
			except Exception:  # Second resort to unsupported locale setting.
				try:
					if category in [LC_TIME, LC_MESSAGES]:
						setlocale(category, locale)
				except Exception:  # Last resort to unsupported locale setting.
					try:
						setlocale(LC_TIME, locale)
					except Exception:
						pass  # TRY to establish it more times.
		environ["LC_TIME"] = f"{locale}'.UTF-8'"
		environ["LANGUAGE"] = f"{locale}'.UTF-8'"
		environ["LANGUAGE2"] = locale
		environ["GST_SUBTITLE_ENCODING"] = self.getGStreamerSubtitleEncoding()
		return True

	def activateLanguage(self, locale):
		if not self.activateLanguage_TRY(locale):
			print("[Language] - retry with ", "es_ES")
			self.activateLanguage_TRY("es_ES")

	def activateLanguageIndex(self, locale):
		if locale < len(self.langlist):
			self.activateLanguage(self.langlist[locale])

	def getLanguageList(self):
		return [(x, self.lang[x]) for x in self.langlist]

	def getLanguageListSelection(self):
		return self.langlistselection

	def getActiveLanguage(self):
		return self.activeLanguage

	def getActiveCatalog(self):
		return self.catalog

	def getActiveLanguageIndex(self):
		idx = 0
		for x in self.langlist:
			if x == self.activeLanguage:
				return idx
			idx += 1
		return None

	def getLanguage(self):
		return self.lang[self.activeLanguage][1] + "_" + self.lang[self.activeLanguage][2] if self.activeLanguage != 0 else ""

	def getGStreamerSubtitleEncoding(self):
		return self.lang[self.activeLanguage][3] if self.activeLanguage != 0 else 'ISO-8859-15'

	def addCallback(self, callback):
		self.callbacks.append(callback)

	def delLanguage(self, delLang=None):
		from Components.config import config
		if delLang:
			lang = config.osd.language.value
			print(f"[Language] DELETE LANG, {delLang}")
			if delLang[:2] == "es":
				print("[Language] Default Language can not be deleted !!")
				return
			elif delLang == "pt_BR":
				delLang = delLang.lower()
				delLang = delLang.replace('_', '-')
				system("opkg remove --autoremove --force-depends " + packageprefix + delLang)
			else:
				system("opkg remove --autoremove --force-depends " + packageprefix + delLang[:2])
		else:
			lang = self.activeLanguage
			print(f"[Language] Delete all lang except, {lang}")
			for x in self.languageDirectory:
				if len(x) > 2:
					if x != lang and x[:2] != "es":
						x = x.lower()
						x = x.replace('_', '-')
						system("opkg remove --autoremove --force-depends " + packageprefix + x)
				else:
					if x != lang[:2] and x != "es":
						system("opkg remove --autoremove --force-depends " + packageprefix + x)
		system("touch /etc/enigma2/.removelang")
		self.InitLang()


language = Language()
