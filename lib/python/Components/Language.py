# -*- coding: UTF-8 -*-
import gettext
from locale import LC_CTYPE, LC_COLLATE, LC_TIME, LC_MONETARY, LC_MESSAGES, LC_NUMERIC, setlocale
from os import listdir, environ, system
from Tools.Directories import SCOPE_LANGUAGE, resolveFilename

DATADIR_PO = resolveFilename(SCOPE_LANGUAGE)
packageprefix = "enigma2-locale-"


class Language:
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
