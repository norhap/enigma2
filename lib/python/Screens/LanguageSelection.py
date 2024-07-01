from enigma import eTimer
from time import sleep
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
from Components.Language import language
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.SystemInfo import MODEL
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import ShowRemoteControl
from Screens.Standby import TryQuitMainloop
from Tools.Directories import resolveFilename, SCOPE_GUISKIN
from Tools.LoadPixmap import LoadPixmap

inWizzard = False


def LanguageEntryComponent(file, name, index):
	png = LoadPixmap(resolveFilename(SCOPE_GUISKIN, "countries/" + index + ".png"))
	if png is None:
		png = LoadPixmap(resolveFilename(SCOPE_GUISKIN, "countries/" + file + ".png"))
		if png is None:
			png = LoadPixmap(resolveFilename(SCOPE_GUISKIN, "countries/missing.png"))
	res = (index, name, png)
	return res


class LanguageSelection(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Language"))

		language.InitLang()
		self.oldActiveLanguage = language.getActiveLanguage()
		self.catalog = language.getActiveCatalog()  # This initializes the full translation of this screen in the selected language.

		self.list = []
		self["summarylangsel"] = StaticText()  # FRONT PANEL DISPLAY
		self["languages"] = List(self.list)
		self["languages"].onSelectionChanged.append(self.changed)

		self.updateList()
		self.onLayoutFinish.append(self.selectActiveLanguage)

		self["key_red"] = StaticText("")
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText("")
		self["description"] = Label()
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"left": self.pageUp,
			"right": self.pageDown,
			"ok": self.save,
			"cancel": self.cancel,
			"red": self.cancel,
			"green": self.save,
			"yellow": self.installLanguage,
			"blue": self.delLang,
			"menu": self.installLanguage
		}, -1)

	def updateCache(self):
		self.setTitle(_("Updating cache"))
		self["languages"].setList([('update cache', _('Updating cache, please wait...'), None)])
		self.updateTimer = eTimer()
		self.updateTimer.callback.append(self.startupdateCache)
		self.updateTimer.start(100)

	def startupdateCache(self):
		self.updateTimer.stop()
		self["languages"].setList(self.list)
		self.selectActiveLanguage()

	def selectActiveLanguage(self):
		try:
			if len(language.getLanguageList()) < 2:  # Language Spanish default if index is one.
				self.oldActiveLanguage = language.getActiveLanguage()
				self["key_blue"].setText("")
			else:
				activeLanguage = language.getActiveLanguage()
			pos = 0
			for pos, x in enumerate(self.list):
				if x[0] == self.oldActiveLanguage or x[0] == activeLanguage:  # self.oldActiveLanguage == "es_ES" Spanish takes over OSD.
					self["languages"].index = pos
					break
		except Exception:
			if MODEL in ("osmio4kplus"):  # Reconfigure the selected language.
				config.osd.language.setValue(config.osd.language.value)
				language.activateLanguage(config.osd.language.value)
				sleep(0.8)
			self.session.openWithCallback(self.restartGUI, MessageBox, _("GUI needs a restart to apply a new language\nDo you want to restart the GUI now?"), MessageBox.TYPE_YESNO)

	def save(self):
		self.run()
		global inWizzard
		if inWizzard:
			inWizzard = False
			if self.oldActiveLanguage != config.osd.language.value:
				self.session.open(TryQuitMainloop, 3)
			self.close()
		else:
			if self.oldActiveLanguage != config.osd.language.value:
				if MODEL in ("osmio4kplus"):  # Reconfigure the selected language.
					config.osd.language.setValue(config.osd.language.value)
					language.activateLanguage(config.osd.language.value)
					sleep(0.8)
				self.session.openWithCallback(self.restartGUI, MessageBox, _("GUI needs a restart to apply a new language\nDo you want to restart the GUI now?"), MessageBox.TYPE_YESNO)
			else:
				self.close()

	def restartGUI(self, answer=True):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.run()

	def cancel(self):
		if self.oldActiveLanguage != config.osd.language.value:
			language.activateLanguage(self.oldActiveLanguage)
			config.osd.language.setValue(self.oldActiveLanguage)
			config.osd.language.save()
		self.close()

	def delLang(self):
		if len(language.getLanguageList()) > 1:
			curlang = config.osd.language.value
			lang = curlang
			languageList = language.getLanguageListSelection()
			for t in languageList:
				if curlang == t[0]:
					lang = t[1]
					break
			if config.osd.language.value not in ("es_ES"):
				self.session.openWithCallback(self.delLangCB, MessageBox, _("Select 'Yes' to remove all languages except Spanish and the selected language.\n\nSelect 'No' to delete only the chosen language:\n\n") + lang)
			else:
				self.session.openWithCallback(self.delLangCB, MessageBox, _("Select 'Yes' to remove all languages except Spanish."))

	def delLangCB(self, answer):
		if answer:
			language.delLanguage()
			language.activateLanguage(self.oldActiveLanguage)
			self.updateList()
			self.selectActiveLanguage()
			config.pluginbrowser.languages_po.save()
		else:
			if config.osd.language.value != "es_ES":
				curlang = config.osd.language.value
				lang = curlang
				languageList = language.getLanguageListSelection()
				for t in languageList:
					if curlang == t[0]:
						lang = t[1]
						break
				self.session.openWithCallback(self.deletelanguagesCB, MessageBox, _("Do you really want to delete selected language?\n\n") + lang, default=True)
			else:
				self.close()

	def deletelanguagesCB(self, answer):
		if answer:
			curlang = config.osd.language.value
			lang = curlang
			language.delLanguage(delLang=lang)
			self.oldActiveLanguage = "es_ES"  # Spanish takes over OSD.
			self.updateList()
			self.selectActiveLanguage()

	def run(self, justlocal=False):
		lang = self["languages"].getCurrent()[0]

		if lang == 'update cache':
			return

		if lang != config.osd.language.value:
			config.osd.language.setValue(lang)
			config.osd.language.save()

		if config.misc.firstrun.value:  # define area and city without network only in first run
			from Tools.Directories import fileReadXML
			from Components.Timezones import TIMEZONE_FILE
			#  config.timezone.area.value = AREA.get(config.osd.language.value) work with dictionary in timezones AREA = "es_ES": "Europe"
			#  config.timezone.val.value = CITY.get(config.osd.language.value) work with dictionary in timezones CITY = "es_ES": "Madrid"
			fileDom = fileReadXML(TIMEZONE_FILE)
			for zone in fileDom.findall("zone"):
				if lang in zone.attrib.get("localeCode"):
					area = zone.attrib.get("zone").split("/")[0]
					config.timezone.area.value = area
					if area in zone.attrib.get("zone"):
						city = zone.attrib.get("zone").split("/")[1]
						config.timezone.val.value = city
						config.timezone.val.save()
			config.ntp.timesync.value = "dvb"
		self.setTitle(_("Language selection"))
		self["summarylangsel"].setText(self["languages"].getCurrent()[1])  # FRONT PANEL DISPLAY
		self["key_red"].setText(_("Cancel"))
		self["key_green"].setText(_("Save"))
		self["key_yellow"].setText(_("Add Language"))
		if len(language.getLanguageList()) > 1:
			self["key_blue"].setText(_("Delete Language(s)"))
			self["description"].setText(_("'Save' or 'OK' changes active language.\n\n'Add Language' or MENU adds additional language(s).\n\n'Delete Language' allows either deletion of all but Spanish and selected language.\nYou also have the option to remove only the selected language."))
		else:
			self["key_blue"].setText("")
			self["description"].setText(_("'Save' or 'OK' changes active language.\n\n'Add Language' or MENU adds additional language(s)."))
		if justlocal:
			return

		language.activateLanguage(lang)
		config.misc.languageselected.value = 0
		config.misc.languageselected.save()

	def updateList(self):
		languageList = language.getLanguageList()
		if not languageList:  # no language available => display only spanish
			list = [LanguageEntryComponent("es", "Español", "es_ES")]
		else:
			list = [LanguageEntryComponent(file=x[1][2].lower(), name=x[1][0], index=x[0]) for x in languageList]
		self.list = list
		self["languages"].list = list

	def installLanguage(self):
		from Screens.PluginBrowser import PluginDownloadBrowser
		config.pluginbrowser.languages_po.value = True
		self.session.openWithCallback(self.update_after_installLanguage, PluginDownloadBrowser, 0)

	def update_after_installLanguage(self, retval=None):
		language.InitLang()
		self.updateList()
		self.updateCache()
		config.pluginbrowser.languages_po.save()
		if MODEL in ("osmio4kplus"):  # Reconfigure the selected language.
			config.osd.language.setValue(config.osd.language.value)
			language.activateLanguage(config.osd.language.value)

	def changed(self):
		self.run(justlocal=True)

	def pageUp(self):
		self["languages"].pageUp()

	def pageDown(self):
		self["languages"].pageDown()

	def createSummary(self):
		return LanguageSelectionSummary


class LanguageSelectionSummary(Screen):
	def __init__(self, session, parent):
		Screen.__init__(self, session, parent)


class LanguageWizard(LanguageSelection, ShowRemoteControl):
	def __init__(self, session):
		LanguageSelection.__init__(self, session)
		ShowRemoteControl.__init__(self)
		global inWizzard
		inWizzard = True
		self.onLayoutFinish.append(self.selectKeys)
		# TV
		self["wizard"] = Pixmap()
		self["text"] = Label()
		# FRONT PANEL DISPLAY
		self["summarytext"] = StaticText()
		self.setText()

	def selectKeys(self):
		self.clearSelectedKeys()
		self.selectKey("UP")
		self.selectKey("DOWN")

	def changed(self):
		self.run(justlocal=True)
		self.setText()

	def setText(self):
		text = _("Use the UP and DOWN keys to select the language, then press OK button. By pressing MENU you can install a new language.")
		# TV
		self["text"].setText(text)
		# FRONT PANEL DISPLAY
		self["summarytext"].setText(text)

	def createSummary(self):
		return LanguageWizardSummary


class LanguageWizardSummary(Screen):  # WARNING: necessary for initialize the wizard if there is not internet
	def __init__(self, session, parent):
		Screen.__init__(self, session, parent)
