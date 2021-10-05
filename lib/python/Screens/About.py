try:
	import urllib2
except ImportError:
	import urllib

from enigma import eConsoleAppContainer, eDVBResourceManager, eGetEnigmaDebugLvl, eLabel, eTimer, getDesktop, getE2Rev, ePoint, eSize
from boxbranding import getBoxType, getDisplayType, getHaveTranscoding, getHaveMultiTranscoding
from os import listdir, popen, remove
from os.path import getmtime, isfile, join as pathjoin
from six import PY2, PY3, ensure_str as ensurestr, text_type as texttype
from PIL import Image
import skin, os, re, urllib2, sys
from skin import parameters
from Screens.HelpMenu import HelpableScreen
from Screens.Screen import Screen, ScreenSummary
from Screens.MessageBox import MessageBox

from Components.config import config
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Sources.StaticText import StaticText
from Components.Harddisk import harddiskmanager, Harddisk
from Components.NimManager import nimmanager
from Components.About import about
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from Components.Console import Console
from Components.GUIComponent import GUIComponent
from Components.Pixmap import MultiPixmap, Pixmap
from Components.Network import iNetwork
from Components.SystemInfo import SystemInfo

from Tools.Directories import SCOPE_PLUGINS, resolveFilename, fileExists, fileHas, pathExists, fileReadLines, fileWriteLine
from Tools.Geolocation import geolocation
from Tools.StbHardware import getFPVersion, getBrandModel
from Tools.LoadPixmap import LoadPixmap


MODULE_NAME = __name__.split(".")[-1]

INFO_COLORS = ["N", "H", "P", "V", "M"]
INFO_COLOR = {
	"B": None,
	"N": 0x00ffffff,  # Normal.
	"H": 0x00ffffff,  # Headings.
	"P": 0x00888888,  # Prompts.
	"V": 0x00888888,  # Values.
	"M": 0x00ffff00  # Messages.
}

URL ='https://raw.githubusercontent.com/norhap/enigma2-openvision-1/develop/NEWS'

def news(url):
    text = ""
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        link = response.read().decode("windows-1252")
        response.close()
        text = link.encode("utf-8")

    except:
        print("ERROR novedades alvaro %s" %(url))

    return text


class InformationBase(Screen, HelpableScreen):
	def __init__(self, session):
		Screen.__init__(self, session, mandatoryWidgets=["information"])
		HelpableScreen.__init__(self)
		self.skinName = ["Information"]
		self["information"] = ScrollLabel()
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Refresh"))
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))
		self["actions"] = HelpableActionMap(self, ["CancelSaveActions", "OkActions", "NavigationActions"], {
			"cancel": (self.keyCancel, _("Close the screen")),
			"close": (self.closeRecursive, _("Close the screen and exit all menus")),
			"save": (self.refreshInformation, _("Refresh the screen")),
			"ok": (self.refreshInformation, _("Refresh the screen")),
			"top": (self["information"].moveTop, _("Move to first line / screen")),
			"pageUp": (self["information"].pageUp, _("Move up a screen")),
			"up": (self["information"].pageUp, _("Move up a screen")),
			"down": (self["information"].pageDown, _("Move down a screen")),
			"pageDown": (self["information"].pageDown, _("Move down a screen")),
			"bottom": (self["information"].moveBottom, _("Move to last line / screen"))
		}, prio=0, description=_("Common Information Actions"))
		if isfile(resolveFilename(SCOPE_PLUGINS, pathjoin("boxes", "%s.png" % (getBoxType())))):
			self["key_info"] = StaticText(_("INFO"))
			self["infoActions"] = HelpableActionMap(self, ["InfoActions"], {
				"info": (self.showReceiverImage, _("Show receiver image(s)"))
			}, prio=0, description=_("Receiver Information Actions"))
		colors = parameters.get("InformationColors", (0x00ffffff, 0x00ffffff, 0x00888888, 0x00888888, 0x00ffff00))
		if len(colors) == len(INFO_COLORS):
			for index in range(len(colors)):
				INFO_COLOR[INFO_COLORS[index]] = colors[index]
		else:
			print("[Information] Warning: %d colors are defined in the skin when %d were expected!" % (len(colors), len(INFO_COLORS)))
		self["information"].setText(_("Loading information, please wait..."))
		self.onInformationUpdated = [self.displayInformation]
		self.onLayoutFinish.append(self.displayInformation)
		self.console = Console()
		self.informationTimer = eTimer()
		self.informationTimer.callback.append(self.fetchInformation)
		self.informationTimer.start(25)

	def showReceiverImage(self):
		self.session.openWithCallback(self.informationWindowClosed, InformationImage)

	def keyCancel(self):
		self.console.killAll()
		self.close()

	def closeRecursive(self):
		self.console.killAll()
		self.close(True)

	def informationWindowClosed(self, *retVal):
		if retVal and retVal[0]:
			self.close(True)

	def fetchInformation(self):
		self.informationTimer.stop()
		for callback in self.onInformationUpdated:
			callback()

	def refreshInformation(self):
		self.informationTimer.start(25)
		for callback in self.onInformationUpdated:
			callback()

	def displayInformation(self):
		pass

	def getSummaryInformation(self):
		pass

	def createSummary(self):
		return InformationSummary


def formatLine(style, left, right=None):
	styleLen = len(style)
	leftStartColor = "" if styleLen > 0 and style[0] == "B" else "\c%08x" % (INFO_COLOR.get(style[0], "P") if styleLen > 0 else INFO_COLOR["P"])
	leftEndColor = "" if leftStartColor == "" else "\c%08x" % INFO_COLOR["N"]
	leftIndent = "    " * int(style[1]) if styleLen > 1 and style[1].isdigit() else ""
	rightStartColor = "" if styleLen > 2 and style[2] == "B" else "\c%08x" % (INFO_COLOR.get(style[2], "V") if styleLen > 2 else INFO_COLOR["V"])
	rightEndColor = "" if rightStartColor == "" else "\c%08x" % INFO_COLOR["N"]
	rightIndent = "    " * int(style[3]) if styleLen > 3 and style[3].isdigit() else ""
	if right is None:
		colon = "" if styleLen > 0 and style[0] in ("M", "P", "V") else ""
		return "%s%s%s%s%s" % (leftIndent, leftStartColor, left, colon, leftEndColor)
	return "%s%s%s:%s|%s%s%s%s" % (leftIndent, leftStartColor, left, leftEndColor, rightIndent, rightStartColor, right, rightEndColor)


class InformationImage(Screen, HelpableScreen):
	skin = """
	<screen name="InformationImage" title="Receiver Image" position="center,center" size="950,560">
		<widget name="name" position="10,10" size="e-20,25" font="Regular;20" halign="center" transparent="1" valign="center" />
		<widget name="image" position="10,45" size="e-20,e-105" alphatest="blend" scale="1" transparent="1" />
		<widget source="key_red" render="Label" position="10,e-50" size="180,40" backgroundColor="key_red" conditional="key_red" font="Regular;20" foregroundColor="key_text" halign="center" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="key_green" render="Label" position="200,e-50" size="180,40" backgroundColor="key_green" conditional="key_green" font="Regular;20" foregroundColor="key_text" halign="center" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="key_yellow" render="Label" position="390,e-50" size="180,40" backgroundColor="key_yellow" conditional="key_yellow" font="Regular;20" foregroundColor="key_text" halign="center" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="key_help" render="Label" position="e-90,e-50" size="80,40" backgroundColor="key_back" conditional="key_help" font="Regular;20" foregroundColor="key_text" halign="center" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="lab1" render="Label" position="0,0" size="0,0" conditional="lab1" font="Regular;22" transparent="1" />
		<widget source="lab2" render="Label" position="0,0" size="0,0" conditional="lab2" font="Regular;18" transparent="1" />
		<widget source="lab3" render="Label" position="0,0" size="0,0" conditional="lab3" font="Regular;18" transparent="1" />
		<widget source="lab4" render="Label" position="0,0" size="0,0" conditional="lab4" font="Regular;18" transparent="1" />
		<widget source="lab5" render="Label" position="0,0" size="0,0" conditional="lab5" font="Regular;18" transparent="1" />
		<widget source="lab6" render="Label" position="0,0" size="0,0" conditional="lab6" font="Regular;18" transparent="1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session, mandatoryWidgets=["name", "image"])
		HelpableScreen.__init__(self)
		self["name"] = Label()
		self["image"] = Pixmap()
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Prev Image"))
		self["key_yellow"] = StaticText(_("Next Image"))
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))
		model = getBoxType()
		boxes = "Extensions/OpenWebif/public/images/boxes/"
		remotes = "Extensions/OpenWebif/public/images/remotes/"
		self["actions"] = HelpableActionMap(self, ["OkCancelActions", "ColorActions"], {
			"cancel": (self.keyCancel, _("Close the screen")),
			"close": (self.closeRecursive, _("Close the screen and exit all menus")),
			"ok": (self.nextImage, _("Show next image")),
			"red": (self.keyCancel, _("Close the screen")),
			"GREEN": (self.prevImage, _("Show previous image")),
			"YELLOW": (self.nextImage, _("Show next image"))
		}, prio=0, description=_("Receiver Image Actions"))
		self.images = (
			(_("Front"), "%s%s.png", (boxes, model)),
			(_("Rear"), "%s%s-rear.png", (boxes, model)),
			(_("Remote Control"), "%s%s.png", (remotes, SystemInfo["RCName"])),
			(_("Flashing"), "%s%s-flashing.png", (boxes, model)),
			(_("Internal"), "%s%s-internal.png", (boxes, model))
		)
		self.imageIndex = 0
		self.widgetContext = None
		self.onLayoutFinish.append(self.layoutFinished)

	def keyCancel(self):
		self.close()

	def closeRecursive(self):
		self.close(True)

	def prevImage(self):
		self.imageIndex -= 1
		if self.imageIndex < 0:
			self.imageIndex = len(self.images) - 1
		while not isfile(resolveFilename(SCOPE_PLUGINS, self.images[self.imageIndex][1] % self.images[self.imageIndex][2])):
			self.imageIndex -= 1
			if self.imageIndex < 0:
				self.imageIndex = len(self.images) - 1
				break
		self.layoutFinished()

	def nextImage(self):
		self.imageIndex += 1
		while not isfile(resolveFilename(SCOPE_PLUGINS, self.images[self.imageIndex][1] % self.images[self.imageIndex][2])):
			self.imageIndex += 1
			if self.imageIndex >= len(self.images):
				self.imageIndex = 0
				break
		self.layoutFinished()

	def layoutFinished(self):
		BrandModel = getBrandModel()
		if self.widgetContext is None:
			self.widgetContext = tuple(self["image"].getPosition() + self["image"].getSize())
			print(self.widgetContext)
		self["name"].setText("%s  -  %s" % (self.images[self.imageIndex][0], BrandModel))
		imagePath = resolveFilename(SCOPE_PLUGINS, self.images[self.imageIndex][1] % self.images[self.imageIndex][2])
		image = LoadPixmap(imagePath)
		if image:
			img = Image.open(imagePath)
			imageWidth, imageHeight = img.size
			scale = float(self.widgetContext[2]) / imageWidth if imageWidth >= imageHeight else float(self.widgetContext[3]) / imageHeight
			sizeW = int(imageWidth * scale)
			sizeH = int(imageHeight * scale)
			posX = self.widgetContext[0] + int(self.widgetContext[2] / 2.0 - sizeW / 2.0)
			posY = self.widgetContext[1] + int(self.widgetContext[3] / 2.0 - sizeH / 2.0)
			self["image"].instance.move(ePoint(posX, posY))
			self["image"].instance.resize(eSize(sizeW, sizeH))
			self["image"].instance.setPixmap(image)


def formatLine(style, left, right=None):
	styleLen = len(style)
	leftStartColor = "" if styleLen > 0 and style[0] == "B" else "\c%08x" % (INFO_COLOR.get(style[0], "P") if styleLen > 0 else INFO_COLOR["P"])
	leftEndColor = "" if leftStartColor == "" else "\c%08x" % INFO_COLOR["N"]
	leftIndent = "    " * int(style[1]) if styleLen > 1 and style[1].isdigit() else ""
	rightStartColor = "" if styleLen > 2 and style[2] == "B" else "\c%08x" % (INFO_COLOR.get(style[2], "V") if styleLen > 2 else INFO_COLOR["V"])
	rightEndColor = "" if rightStartColor == "" else "\c%08x" % INFO_COLOR["N"]
	rightIndent = "    " * int(style[3]) if styleLen > 3 and style[3].isdigit() else ""
	if right is None:
		colon = "" if styleLen > 0 and style[0] in ("M", "P", "V") else ":"
		return "%s%s%s%s%s" % (leftIndent, leftStartColor, left, colon, leftEndColor)
	return "%s%s%s:%s|%s%s%s%s" % (leftIndent, leftStartColor, left, leftEndColor, rightIndent, rightStartColor, right, rightEndColor)


class InformationSummary(ScreenSummary):
	def __init__(self, session, parent):
		ScreenSummary.__init__(self, session, parent=parent)
		self.parent = parent
		self["information"] = StaticText()
		parent.onInformationUpdated.append(self.updateSummary)
		# self.updateSummary()

	def updateSummary(self):
		# print("[Information] DEBUG: Updating summary.")
		self["information"].setText(self.parent.getSummaryInformation())


class About(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("About"))
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))
		hddsplit = skin.parameters.get("AboutHddSplit", 0)

		model = getBoxType()

		AboutText = _("Model: ") + getBrandModel() + "\n"
		if model:
			AboutText += _("Machine: ") + about.getHardwareTypeString() + "\n"
		if fileExists("/proc/stb/info/sn"):
			hwserial = open("/proc/stb/info/sn", "r").read().strip()
			AboutText += _("Hardware serial: ") + hwserial + "\n"

		cpu = about.getCPUInfoString()
		AboutText += _("ChipSet: ") + about.getChipSetString() + "\n"
		AboutText += _("CPU: ") + cpu + "\n"
		AboutText += _("Fabricante CPU: ") + about.getCPUBrand() + "\n"
		AboutText += _("CPU Arquitectura: ") + about.getCPUArch() + "\n"
		AboutText += _("Image: ") + about.getImageTypeString() + "\n"
		AboutText += _("Last update: ") + about.getUpdateDateString() + "\n"

		# [WanWizard] Removed until we find a reliable way to determine the installation date
		# AboutText += _("Installed: ") + about.getFlashDateString() + "\n"

		EnigmaVersion = about.getEnigmaVersionString()
		EnigmaVersion = EnigmaVersion.rsplit("-", EnigmaVersion.count("-") - 2)
		if len(EnigmaVersion) == 3:
			EnigmaVersion = EnigmaVersion[0] + " (" + EnigmaVersion[2] + "-" + EnigmaVersion[1] + ")"
		else:
			EnigmaVersion = EnigmaVersion[1]
		EnigmaVersion = _("Branch Enigma2: ") + EnigmaVersion
		self["EnigmaVersion"] = StaticText(EnigmaVersion)
		AboutText += "\n" + EnigmaVersion + "\n"
		AboutText += _("Enigma2 revision: ") + getE2Rev().split("+")[1] + "\n"
		AboutText += _("Build date: ") + about.getBuildDateString() + "\n"
		AboutText += _("DVB driver version: ") + about.getDriverInstalledDate() + "\n"

		AboutText += _("Kernel version: ") + about.getKernelVersionString() + "\n"

		GStreamerVersion = _("GStreamer version: ") + about.getGStreamerVersionString().replace("GStreamer","")
		self["GStreamerVersion"] = StaticText(GStreamerVersion)
		AboutText += GStreamerVersion + "\n"

		FFmpegVersion = _("FFmpeg version: ") + about.getFFmpegVersionString()
		self["FFmpegVersion"] = StaticText(FFmpegVersion)
		AboutText += FFmpegVersion + "\n"
		AboutText += _("Python version: ") + about.getPythonVersionString() + "\n"
		AboutText += _("GCC version: ") + about.getGccVersion() + "\n"
		AboutText += _("Enigma (re)starts: %d\n") % config.misc.startCounter.value
		AboutText += _("Enigma2 debug level: %d\n") % eGetEnigmaDebugLvl()
		fp_version = getFPVersion()
		if fp_version is None:
			fp_version = ""
		else:
			fp_version = _("Frontprocessor version: %s\n") % fp_version
			AboutText += fp_version
			self["FPVersion"] = StaticText(fp_version)
		if SystemInfo["Display"] or SystemInfo["7segment"] or SystemInfo["textlcd"] or model not in ("gbip4k"):
			AboutText += _("Type Display: ") + getDisplayType() + "\n"
		else:
			AboutText += _("No Display") + "\n"
		if config.hdmicec.enabled.value:
			AboutText += "\n" + _("HDMI-CEC address") + ": " + config.hdmicec.fixed_physical_address.value + "\n"

		AboutText += _('Skin & Resolution: %s (%sx%s)\n') % (config.skin.primary_skin.value.split('/')[0], getDesktop(0).size().width(), getDesktop(0).size().height())
		AboutText += "\n"
		for x in about.GetIPsFromNetworkInterfaces():
		    AboutText += _("Uptime: ") + about.getBoxUptime()

		self["AboutScrollLabel"] = ScrollLabel(AboutText)
		self["key_green"] = Button(_("Translations"))
		self["key_red"] = Button(_("Latest Commits"))
		self["key_yellow"] = Button(_("Dmesg Info"))
		self["key_blue"] = Button(_("Memory Info"))

		self["actions"] = ActionMap(["OkCancelActions", "SetupActions", "DirectionActions"],
			{
				"cancel": self.close,
				"ok": self.close,
				"red": self.showCommits,
				"green": self.showTranslationInfo,
				"blue": self.showMemoryInfo,
				"yellow": self.showTroubleshoot,
				"up": self["AboutScrollLabel"].pageUp,
				"down": self["AboutScrollLabel"].pageDown
			})

	def showTranslationInfo(self):
		self.session.open(TranslationInfo)

	def showCommits(self):
		self.session.open(CommitInfoDevelop)

	def showMemoryInfo(self):
		self.session.open(MemoryInfo)

	def showTroubleshoot(self):
		self.session.open(Troubleshoot)


class BenchmarkInformation(InformationBase):
	def __init__(self, session):
		InformationBase.__init__(self, session)
		self.setTitle(_("Benchmark Information"))
		self.skinName.insert(0, "BenchmarkInformation")
		self.cpuTypes = []
		self.cpuBenchmark = None
		self.cpuRating = None
		self.ramBenchmark = None

	def fetchInformation(self):
		self.informationTimer.stop()
		self.cpuTypes = []
		lines = []
		lines = fileReadLines("/proc/cpuinfo", lines, source=MODULE_NAME)
		for line in lines:
			if line.startswith("model name") or line.startswith("Processor"):  # HiSilicon use the label "Processor"!
				self.cpuTypes.append([x.strip() for x in line.split(":")][1])
		self.console.ePopen(("/usr/bin/dhry", "/usr/bin/dhry"), self.cpuBenchmarkFinished)
		# Serialise the tests for better accuracy.
		# self.console.ePopen(("/usr/bin/streambench", "/usr/bin/streambench"), self.ramBenchmarkFinished)
		for callback in self.onInformationUpdated:
			callback()

	def cpuBenchmarkFinished(self, result, retVal, extraArgs):
		for line in result.split("\n"):
			if line.startswith("Open Vision DMIPS"):
				self.cpuBenchmark = int([x.strip() for x in line.split(":")][1])
			if line.startswith("Open Vision CPU status"):
				self.cpuRating = [x.strip() for x in line.split(":")][1]
		# Serialise the tests for better accuracy.
		self.console.ePopen(("/usr/bin/streambench", "/usr/bin/streambench"), self.ramBenchmarkFinished)
		for callback in self.onInformationUpdated:
			callback()

	def ramBenchmarkFinished(self, result, retVal, extraArgs):
		for line in result.split("\n"):
			if line.startswith("Open Vision copy rate"):
				self.ramBenchmark = float([x.strip() for x in line.split(":")][1])
		for callback in self.onInformationUpdated:
			callback()

	def refreshInformation(self):
		self.cpuBenchmark = None
		self.cpuRating = None
		self.ramBenchmark = None
		self.informationTimer.start(25)
		for callback in self.onInformationUpdated:
			callback()

	def displayInformation(self):
		info = []
		BrandModel = getBrandModel()
		info.append(formatLine("H", "%s %s" % (_("Benchmark for"), BrandModel)))
		info.append("")
		for index, cpu in enumerate(self.cpuTypes):
			info.append(formatLine("P1", _("CPU / Core %d type") % index, cpu))
		info.append("")
		info.append(formatLine("P1", _("CPU benchmark"), _("%d DMIPS per core") % self.cpuBenchmark if self.cpuBenchmark else _("Calculating benchmark...")))
		count = len(self.cpuTypes)
		if count > 1:
			info.append(formatLine("P1", _("Total CPU benchmark"), _("%d DMIPS with %d cores") % (self.cpuBenchmark * count, count) if self.cpuBenchmark else _("Calculating benchmark...")))
		info.append(formatLine("P1", _("CPU rating"), self.cpuRating if self.cpuRating else _("Calculating rating...")))
		info.append("")
		info.append(formatLine("P1", _("RAM benchmark"), "%.2f MB/s tasa de copia" % self.ramBenchmark if self.ramBenchmark else _("Calculating benchmark...")))
		self["information"].setText("\n".join(info).encode("UTF-8", "ignore") if PY2 else "\n".join(info))

	def getSummaryInformation(self):
		return "Benchmark Information"


class Geolocation(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Geolocation"))
		self.setTitle(_("Geolocation Information"))
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))

		GeolocationText = _("Information about your Geolocation data") + "\n"

		GeolocationText += "\n"

		try:
			geolocationData = geolocation.getGeolocationData(fields="continent,country,regionName,city,timezone,currency,lat,lon", useCache=True)
			continent = geolocationData.get("continent", None)
			if isinstance(continent, texttype):
				continent = ensurestr(continent.encode(encoding="UTF-8", errors="ignore"))
			if continent is not None:
				GeolocationText += _("Continent: ") + "\t" + continent + "\n"

			country = geolocationData.get("country", None)
			if isinstance(country, texttype):
				country = ensurestr(country.encode(encoding="UTF-8", errors="ignore"))
			if country is not None:
				GeolocationText += _("Country: ") + "\t" + country + "\n"

			state = geolocationData.get("regionName", None)
			if isinstance(state, texttype):
				state = ensurestr(state.encode(encoding="UTF-8", errors="ignore"))
			if state is not None:
				GeolocationText += _("State: ") + "\t" + state + "\n"

			city = geolocationData.get("city", None)
			if isinstance(city, texttype):
				city = ensurestr(city.encode(encoding="UTF-8", errors="ignore"))
			if city is not None:
				GeolocationText += _("City: ") + "\t" + city + "\n"

			GeolocationText += "\n"

			timezone = geolocationData.get("timezone", None)
			if isinstance(timezone, texttype):
				timezone = ensurestr(timezone.encode(encoding="UTF-8", errors="ignore"))
			if timezone is not None:
				GeolocationText += _("Timezone: ") + "\t" + timezone + "\n"

			currency = geolocationData.get("currency", None)
			if isinstance(currency, texttype):
				currency = ensurestr(currency.encode(encoding="UTF-8", errors="ignore"))
			if currency is not None:
				GeolocationText += _("Currency: ") + "\t" + currency + "\n"

			GeolocationText += "\n"

			latitude = geolocationData.get("lat", None)
			if str(float(latitude)) is not None:
				GeolocationText += _("Latitude: ") + "\t" + str(float(latitude)) + "\n"

			longitude = geolocationData.get("lon", None)
			if str(float(longitude)) is not None:
				GeolocationText += _("Longitude: ") + "\t" + str(float(longitude)) + "\n"
			self["AboutScrollLabel"] = ScrollLabel(GeolocationText)
		except Exception as err:
			self["AboutScrollLabel"] = ScrollLabel(_("Requires internet connection"))

		self["key_red"] = Button(_("Close"))

		self["actions"] = ActionMap(["ColorActions", "SetupActions", "DirectionActions"],
			{
				"cancel": self.close,
				"ok": self.close,
				"up": self["AboutScrollLabel"].pageUp,
				"down": self["AboutScrollLabel"].pageDown
			})


class TunerInformation(InformationBase):
	def __init__(self, session):
		InformationBase.__init__(self, session)
		self.setTitle(_("Tuner Information"))
		self.skinName.insert(0, "TunerInformation")

	def displayInformation(self):
		info = []
		info.append(formatLine("H", _("Detected tuners")))
		info.append("")
		nims = nimmanager.nimList()
		descList = []
		curIndex = -1
		if fileExists("/usr/bin/dvb-fe-tool"):
			import time
			try:
				cmd = 'dvb-fe-tool > /tmp/dvbfetool.txt ; dvb-fe-tool -f 1 >> /tmp/dvbfetool.txt ; cat /proc/bus/nim_sockets >> /tmp/dvbfetool.txt'
				res = Console().ePopen(cmd)
				time.sleep(0.1)
			except:
				pass
		for count in range(len(nims)):
			data = nims[count].split(":")
			idx = data[0].strip("Tuner").strip()
			desc = data[1].strip()
			if descList and descList[curIndex]["desc"] == desc:
				descList[curIndex]["end"] = idx
			else:
				descList.append({
					"desc": desc,
					"start": idx,
					"end": idx
				})
				curIndex += 1
			count += 1
		for count in range(len(descList)):
			data = descList[count]["start"] if descList[count]["start"] == descList[count]["end"] else ("%s-%s" % (descList[count]["start"], descList[count]["end"]))
			info.append(formatLine("", "Tuner %s" % data + ":" + "\n" + descList[count]["desc"]))
		# info.append("")
		# info.append(formatLine("H", _("Logical tuners")))  # Each tuner is a listed separately even if the hardware is common.
		# info.append("")
		# nims = nimmanager.nimListCompressed()
		# for count in range(len(nims)):
		# 	tuner, type = [x.strip() for x in nims[count].split(":", 1)]
		# 	info.append(formatLine("P1", tuner, type))
		info.append("")
		info.append(formatLine("", _("DVB API"), about.getDVBAPI()))
		numSlots = 0
		dvbFeToolTxt = ""
		nimSlots = nimmanager.getSlotCount()
		for nim in range(nimSlots):
			dvbFeToolTxt += eDVBResourceManager.getInstance().getFrontendCapabilities(nim)
		dvbApiVersion = dvbFeToolTxt.splitlines()[0].replace("DVB API version: ", "").strip()
		info.append(formatLine("", _("DVB API version"), dvbApiVersion))
		info.append("")
		info.append(formatLine("", _("Transcoding"), (_("Yes") if getHaveTranscoding() == "True" else _("No"))))
		info.append(formatLine("", _("MultiTranscoding"), (_("Yes") if getHaveMultiTranscoding() == "True" else _("No"))))
		info.append("")
		if fileHas("/tmp/dvbfetool.txt", "Mode 2: DVB-S"):
		     info.append(formatLine("", _("DVB-S2/C/T2 Combined"), (_("Yes"))))

		info.append(formatLine("", _("DVB-S2X"), (_("Yes") if fileHas("/tmp/dvbfetool.txt", "DVB-S2X") or pathExists("/proc/stb/frontend/0/t2mi") or pathExists("/proc/stb/frontend/1/t2mi") else _("No"))))
		info.append(formatLine("", _("DVB-S"), (_("Yes") if "DVBS" in dvbFeToolTxt or "DVB-S" in dvbFeToolTxt else _("No"))))
		info.append(formatLine("", _("DVB-T"), (_("Yes") if "DVBT" in dvbFeToolTxt or "DVB-T" in dvbFeToolTxt else _("No"))))
		info.append(formatLine("", _("DVB-C"), (_("Yes") if "DVBC" in dvbFeToolTxt or "DVB-C" in dvbFeToolTxt else _("No"))))
		info.append("")
		info.append(formatLine("", _("Multistream"), (_("Yes") if "MULTISTREAM" in dvbFeToolTxt else _("No"))))
		info.append("")
		info.append(formatLine("", _("ANNEX-A"), (_("Yes") if "ANNEX_A" in dvbFeToolTxt or "ANNEX-A" in dvbFeToolTxt else _("No"))))
		info.append(formatLine("", _("ANNEX-B"), (_("Yes") if "ANNEX_B" in dvbFeToolTxt or "ANNEX-B" in dvbFeToolTxt else _("No"))))
		info.append(formatLine("", _("ANNEX-C"), (_("Yes") if "ANNEX_C" in dvbFeToolTxt or "ANNEX-C" in dvbFeToolTxt else _("No"))))
		self["information"].setText("\n".join(info).encode("UTF-8", "ignore") if PY2 else "\n".join(info))


class Devices(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		screentitle = _("Storage Devices")
		title = screentitle
		Screen.setTitle(self, title)
		self["HDDHeader"] = StaticText(_("Detected devices:"))
		self["MountsHeader"] = StaticText(_("Network servers:"))
		self["nims"] = StaticText()
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))
		for count in (0, 1, 2, 3):
			self["Tuner" + str(count)] = StaticText("")
		self["hdd"] = StaticText()
		self["mounts"] = StaticText()
		self.list = []
		self.activityTimer = eTimer()
		self.activityTimer.timeout.get().append(self.populate2)
		self["key_red"] = Button(_("Close"))
		self["actions"] = ActionMap(["SetupActions", "ColorActions", "TimerEditActions"], {
			"cancel": self.close,
			"red": self.close,
			"save": self.close,
		})
		self.onLayoutFinish.append(self.populate)

	def populate(self):
		self.mountinfo = ''
		self["actions"].setEnabled(False)
		scanning = _("Please wait while scanning for devices...")
		self["hdd"].setText(scanning)
		self['mounts'].setText(scanning)
		self.activityTimer.start(1)

	def populate2(self):
		self.activityTimer.stop()
		self.Console = Console()
		self.hddlist = harddiskmanager.HDDList()
		self.list = []
		if self.hddlist:
			for count in range(len(self.hddlist)):
				hdd = self.hddlist[count][1]
				hddp = self.hddlist[count][0]
				if "ATA" in hddp:
					hddp = hddp.replace('ATA', '')
					hddp = hddp.replace('Internal', 'ATA Bus ')
				free = hdd.Totalfree()
				if ((float(free) / 1024) / 1024) >= 1:
					freeline = _("Free: ") + str(round(((float(free) / 1024) / 1024), 2)) + _("TB")
				elif (free / 1024) >= 1:
					freeline = _("Free: ") + str(round((float(free) / 1024), 2)) + _("GB")
				elif free >= 1:
					freeline = _("Free: ") + str(free) + _("MB")
				elif "Generic(STORAGE" in hddp:
					continue
				else:
					freeline = _("Free: ") + _("full")
				line = "%s      %s" %(hddp, freeline)
				self.list.append(line)
		self.list = '\n'.join(self.list)
		self["hdd"].setText(self.list)

		self.Console.ePopen("df -mh | grep -v '^Filesystem'", self.Stage1Complete)

	def Stage1Complete(self, result, retval, extra_args=None):
		if PY2:
			result = result.replace('\n                        ', ' ').split('\n')
		else:
			result = result.decode().replace('\n                        ', ' ').split('\n')
		self.mountinfo = ""
		for line in result:
			self.parts = line.split()
			if line and self.parts[0] and (self.parts[0].startswith('192') or self.parts[0].startswith('//192')):
				line = line.split()
				ipaddress = line[0]
				mounttotal = line[1]
				mountfree = line[3]
				if self.mountinfo:
					self.mountinfo += "\n"
				self.mountinfo += "%s (%sB, %sB %s)" % (ipaddress, mounttotal, mountfree, _("free"))
		if pathExists("/media/autofs"):
			for entry in sorted(listdir("/media/autofs")):
				mountEntry = pathjoin("/media/autofs", entry)
				self.mountinfo += _("\n %s " % (mountEntry))

		if self.mountinfo:
			self["mounts"].setText(self.mountinfo)
		else:
			self["mounts"].setText(_('none'))
		self["actions"].setEnabled(True)


class SystemNetworkInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		screentitle = _("Network")
		title = screentitle
		Screen.setTitle(self, title)
		self.skinName = ["SystemNetworkInfo", "WlanStatus"]
		self["LabelBSSID"] = StaticText()
		self["LabelESSID"] = StaticText()
		self["LabelQuality"] = StaticText()
		self["LabelSignal"] = StaticText()
		self["LabelBitrate"] = StaticText()
		self["LabelEnc"] = StaticText()
		self["BSSID"] = StaticText()
		self["ESSID"] = StaticText()
		self["quality"] = StaticText()
		self["signal"] = StaticText()
		self["bitrate"] = StaticText()
		self["enc"] = StaticText()
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))
		self["IFtext"] = StaticText()
		self["IF"] = StaticText()
		self["Statustext"] = StaticText()
		self["statuspic"] = MultiPixmap()
		self["statuspic"].setPixmapNum(1)
		self["statuspic"].show()
		self["devicepic"] = MultiPixmap()
		self["AboutScrollLabel"] = ScrollLabel()

		self.iface = None
		self.createscreen()
		self.iStatus = None

		if iNetwork.isWirelessInterface(self.iface):
			try:
				from Plugins.SystemPlugins.WirelessLan.Wlan import iStatus

				self.iStatus = iStatus
			except:
				pass
			self.resetList()
			self.onClose.append(self.cleanup)

		self["key_red"] = StaticText(_("Close"))

		self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"], {
			"cancel": self.close,
			"ok": self.close,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown
		})
		self.onLayoutFinish.append(self.updateStatusbar)

	def createscreen(self):
		self.AboutText = ""
		self.iface = "eth0"
		eth0 = about.getIfConfig('eth0')
		if 'addr' in eth0:
			self.AboutText += _("IP:") + "\t" + "\t" + eth0['addr'] + "\n"
			if 'netmask' in eth0:
				self.AboutText += _("Netmask:") + "\t" + eth0['netmask'] + "\n"
			if 'hwaddr' in eth0:
				self.AboutText += _("MAC:") + "\t" + "\t" + eth0['hwaddr'] + "\n"
			self.iface = 'eth0'

		eth1 = about.getIfConfig('eth1')
		if 'addr' in eth1:
			self.AboutText += _("IP:") + "\t" + "\t" + eth1['addr'] + "\n"
			if 'netmask' in eth1:
				self.AboutText += _("Netmask:") + "\t" + eth1['netmask'] + "\n"
			if 'hwaddr' in eth1:
				self.AboutText += _("MAC:") + "\t" + "\t" + eth1['hwaddr'] + "\n"
			self.iface = 'eth1'

		ra0 = about.getIfConfig('ra0')
		if 'addr' in ra0:
			self.AboutText += _("IP:") + "\t" + "\t" + ra0['addr'] + "\n"
			if 'netmask' in ra0:
				self.AboutText += _("Netmask:") + "\t" + ra0['netmask'] + "\n"
			if 'hwaddr' in ra0:
				self.AboutText += _("MAC:") + "\t" + "\t" + ra0['hwaddr'] + "\n"
			self.iface = 'ra0'

		wlan0 = about.getIfConfig('wlan0')
		if 'addr' in wlan0:
			self.AboutText += _("IP:") + "\t" + "\t" + wlan0['addr'] + "\n"
			if 'netmask' in wlan0:
				self.AboutText += _("Netmask:") + "\t" + wlan0['netmask'] + "\n"
			if 'hwaddr' in wlan0:
				self.AboutText += _("MAC:") + "\t" + "\t" + wlan0['hwaddr'] + "\n"
			self.iface = 'wlan0'

		wlan3 = about.getIfConfig('wlan3')
		if 'addr' in wlan3:
			self.AboutText += _("IP:") + "\t" + "\t" + wlan3['addr'] + "\n"
			if 'netmask' in wlan3:
				self.AboutText += _("Netmask:") + "\t" + wlan3['netmask'] + "\n"
			if 'hwaddr' in wlan3:
				self.AboutText += _("MAC:") + "\t" + "\t" + wlan3['hwaddr'] + "\n"
			self.iface = 'wlan3'

		rx_bytes, tx_bytes = about.getIfTransferredData(self.iface)
		self.AboutText += "\n" + _("Bytes received:") + "\t" + rx_bytes + "\n"
		self.AboutText += _("Bytes sent:") + "\t" + tx_bytes + "\n"

		geolocationData = geolocation.getGeolocationData(fields="isp,org,mobile,proxy,query", useCache=True)
		isp = geolocationData.get("isp", None)
		isporg = geolocationData.get("org", None)
		if isinstance(isp, texttype):
			isp = ensurestr(isp.encode(encoding="UTF-8", errors="ignore"))
		if isinstance(isporg, texttype):
			isporg = ensurestr(isporg.encode(encoding="UTF-8", errors="ignore"))
		self.AboutText += "\n"
		if isp is not None:
			if isporg is not None:
				self.AboutText += _("ISP: ") + "\t" + "\t" + isp + " " + "(" + isporg + ")" + "\n"
			else:
				self.AboutText +=  "\n" + _("ISP: ") + "\t" + "\t" + isp + "\n"

		mobile = geolocationData.get("mobile", False)
		if mobile is not False:
			self.AboutText += _("Mobile: ") + "\t" + "\t" + _("Yes") + "\n"
		else:
			self.AboutText += _("Mobile: ") + "\t" + "\t" + _("No") + "\n"

		proxy = geolocationData.get("proxy", False)
		if proxy is not False:
			self.AboutText += _("Proxy: ") + "\t" + "\t" + _("Yes") + "\n"
		else:
			self.AboutText += _("Proxy: ") + "\t" + "\t" + _("No") + "\n"

		publicip = geolocationData.get("query", None)
		if str(publicip) != "":
			self.AboutText +=  _("Public IP: ") + "\t" + "\t" + str(publicip) + "\n" + "\n"

		self.console = Console()
		self.console.ePopen('ethtool %s' % self.iface, self.SpeedFinished)

	def SpeedFinished(self, result, retval, extra_args):
		if PY2:
			result_tmp = result.split('\n')
		else:
			result_tmp = result.decode().split('\n')
		for line in result_tmp:
			if 'Speed:' in line:
				speed = line.split(': ')[1][:-4]
				self.AboutText += _("Speed:") + "\t" + "\t" + speed + _('Mb/s')

		hostname = file('/proc/sys/kernel/hostname').read()
		self.AboutText += "\n" + _("Hostname:") + "\t" + "\t" + hostname + "\n"
		self["AboutScrollLabel"].setText(self.AboutText)

	def cleanup(self):
		if self.iStatus:
			self.iStatus.stopWlanConsole()

	def resetList(self):
		if self.iStatus:
			self.iStatus.getDataForInterface(self.iface, self.getInfoCB)

	def getInfoCB(self, data, status):
		self.LinkState = None
		if data is not None and data:
			if status is not None:
# getDataForInterface()->iwconfigFinished() in
# Plugins/SystemPlugins/WirelessLan/Wlan.py sets fields to boolean False
# if there is no info for them, so we need to check that possibility
# for each status[self.iface] field...
#
				if self.iface == 'wlan0' or self.iface == 'wlan3' or self.iface == 'ra0':
# accesspoint is used in the "enc" code too, so we get it regardless
#
					if not status[self.iface]["accesspoint"]:
						accesspoint = _("Unknown")
					else:
						if status[self.iface]["accesspoint"] == "Not-Associated":
							accesspoint = _("Not-Associated")
							essid = _("No connection")
						else:
							accesspoint = status[self.iface]["accesspoint"]
					if 'BSSID' in self:
						self.AboutText += _('Accesspoint:') + '\t' + accesspoint + '\n'

					if 'ESSID' in self:
						if not status[self.iface]["essid"]:
							essid = _("Unknown")
						else:
							if status[self.iface]["essid"] == "off":
								essid = _("No connection")
							else:
								essid = status[self.iface]["essid"]
						self.AboutText += _('SSID:') + '\t' + essid + '\n'

					if 'quality' in self:
						if not status[self.iface]["quality"]:
							quality = _("Unknown")
						else:
							quality = status[self.iface]["quality"]
						self.AboutText += _('Link quality:') + '\t' + quality + '\n'

					if 'bitrate' in self:
						if not status[self.iface]["bitrate"]:
							bitrate = _("Unknown")
						else:
							if status[self.iface]["bitrate"] == '0':
								bitrate = _("Unsupported")
							else:
								bitrate = str(status[self.iface]["bitrate"]) + " Mb/s"
						self.AboutText += _('Bitrate:') + '\t' + bitrate + '\n'

					if 'signal' in self:
						if not status[self.iface]["signal"]:
							signal = _("Unknown")
						else:
							signal = status[self.iface]["signal"]
						self.AboutText += _('Signal strength:') + '\t' + signal + '\n'

					if 'enc' in self:
						if not status[self.iface]["encryption"]:
							encryption = _("Unknown")
						else:
							if status[self.iface]["encryption"] == "off":
								if accesspoint == "Not-Associated":
									encryption = _("Disabled")
								else:
									encryption = _("Unsupported")
							else:
								encryption = _("Enabled")
						self.AboutText += _('Encryption:') + '\t' + encryption + '\n'

					if ((status[self.iface]["essid"] and status[self.iface]["essid"] == "off") or
					    not status[self.iface]["accesspoint"] or
					    status[self.iface]["accesspoint"] == "Not-Associated"):
						self.LinkState = False
						self["statuspic"].setPixmapNum(1)
						self["statuspic"].show()
					else:
						self.LinkState = True
						iNetwork.checkNetworkState(self.checkNetworkCB)
					self["AboutScrollLabel"].setText(self.AboutText)

	def exit(self):
		self.close(True)

	def updateStatusbar(self):
		self["IFtext"].setText(_("Network:"))
		self["IF"].setText(iNetwork.getFriendlyAdapterName(self.iface))
		self["Statustext"].setText(_("Link:"))
		if iNetwork.isWirelessInterface(self.iface):
			self["devicepic"].setPixmapNum(1)
			try:
				self.iStatus.getDataForInterface(self.iface, self.getInfoCB)
			except:
				self["statuspic"].setPixmapNum(1)
				self["statuspic"].show()
		else:
			iNetwork.getLinkState(self.iface, self.dataAvail)
			self["devicepic"].setPixmapNum(0)
		self["devicepic"].show()

	def dataAvail(self, data):
		if PY3:
			data = data.decode()
		self.LinkState = None
		for line in data.splitlines():
			line = line.strip()
			if 'Link detected:' in line:
				if "yes" in line:
					self.LinkState = True
				else:
					self.LinkState = False
		if self.LinkState:
			iNetwork.checkNetworkState(self.checkNetworkCB)
		else:
			self["statuspic"].setPixmapNum(1)
			self["statuspic"].show()

	def checkNetworkCB(self, data):
		try:
			if iNetwork.getAdapterAttribute(self.iface, "up") is True:
				if self.LinkState is True:
					if data <= 2:
						self["statuspic"].setPixmapNum(0)
					else:
						self["statuspic"].setPixmapNum(1)
				else:
					self["statuspic"].setPixmapNum(1)
			else:
				self["statuspic"].setPixmapNum(1)
			self["statuspic"].show()
		except:
			pass


class SystemMemoryInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		screentitle = _("Memory")
		title = screentitle
		Screen.setTitle(self, title)
		self.skinName = ["SystemMemoryInfo", "About"]
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))
		self["AboutScrollLabel"] = ScrollLabel()
		self["key_red"] = Button(_("Close"))
		self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
		"cancel": self.close,
		"ok": self.close,
		"red": self.close,
		})

		out_lines = file("/proc/meminfo").readlines()
		self.AboutText = _("RAM") + '\n\n'
		RamTotal = "-"
		RamFree = "-"
		for lidx in range(len(out_lines) - 1):
			tstLine = out_lines[lidx].split()
			if "MemTotal:" in tstLine:
				MemTotal = out_lines[lidx].split()
				self.AboutText += _("Total memory:") + "\t" + "\t" + MemTotal[1] + "\n"
			if "MemFree:" in tstLine:
				MemFree = out_lines[lidx].split()
				self.AboutText += _("Free memory:") + "\t" + "\t" + MemFree[1] + "\n"
			if "Buffers:" in tstLine:
				Buffers = out_lines[lidx].split()
				self.AboutText += _("Buffers:") + "\t" + "\t" + Buffers[1] + "\n"
			if "Cached:" in tstLine:
				Cached = out_lines[lidx].split()
				self.AboutText += _("Cached:") + "\t" + "\t" + Cached[1] + "\n"
			if "SwapTotal:" in tstLine:
				SwapTotal = out_lines[lidx].split()
				self.AboutText += _("Total swap:") + "\t" + "\t" + SwapTotal[1] + "\n"
			if "SwapFree:" in tstLine:
				SwapFree = out_lines[lidx].split()
				self.AboutText += _("Free swap:") + "\t" + "\t" + SwapFree[1] + "\n\n"

		self["actions"].setEnabled(False)
		self.Console = Console()
		self.Console.ePopen("df -mh / | grep -v '^Filesystem'", self.Stage1Complete2)

	def Stage1Complete2(self, result, retval, extra_args=None):
		flash = str(result).replace('\n', '')
		flash = flash.split()
		RamTotal = flash[1]
		RamFree = flash[3]

		self.AboutText += _("FLASH") + '\n\n'
		self.AboutText += _("Total:") + "\t" + "\t" + RamTotal + "\n"
		self.AboutText += _("Free:") + "\t" + "\t" + RamFree + "\n\n"

		self["AboutScrollLabel"].setText(self.AboutText)
		self["actions"].setEnabled(True)


class TranslationInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Translation"))
		# don't remove the string out of the _(), or it can't be "translated" anymore.

		# TRANSLATORS: Add here whatever should be shown in the "translator" about screen, up to 6 lines (use \n for newline)
		info = _("TRANSLATOR_INFO")

		if info == "TRANSLATOR_INFO":
			info = "(N/A)"

		infolines = _("").split("\n")
		infomap = {}
		for x in infolines:
			l = x.split(': ')
			if len(l) != 2:
				continue
			(type, value) = l
			infomap[type] = value
		print(infomap)

		self["key_red"] = Button(_("Cancel"))
		self["TranslationInfo"] = StaticText(info)
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))

		translator_name = infomap.get("Language-Team", "none")
		if translator_name == "none":
			translator_name = infomap.get("Last-Translator", "")

		self["TranslatorName"] = StaticText(translator_name)

		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.close,
				"ok": self.close,
			})


class CommitInfoDevelop(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.skinName = "CommitInfoDevelop"
        self.setup_title = _("Novedades Alvaro")
        self.setTitle(self.setup_title)
        self["news"] = ScrollLabel()

        self["Actions"] = ActionMap(['OkCancelActions', 'ShortcutActions',"ColorActions","DirectionActions"], {
            "cancel" : self.cerrar,
            "ok" : self.cerrar,
            "up": self["news"].pageUp,
            "down": self["news"].pageDown,
            "left": self["news"].pageUp,
            "right": self["news"].pageDown,
        })

	self['news'].setText(news(URL))
	self["lab1"] = StaticText(_("OpenVision"))
	self["lab2"] = StaticText(_("Lets define enigma2 once more"))
	self["lab3"] = StaticText(_("Report problems to:"))
	self["lab4"] = StaticText(_("https://openvision.tech"))
	self["lab5"] = StaticText(_("Sources are available at:"))
	self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))

    def cerrar(self):
        self.close()

	def readGithubCommitLogs(self):
		url = self.projects[self.project][0]
		commitlog = ""
		from datetime import datetime
		from json import loads
		from urllib2 import urlopen
		try:
			commitlog += 80 * '-' + '\n'
			commitlog += url.split('/')[-2] + '\n'
			commitlog += 80 * '-' + '\n'
			try:
				# OpenPli 5.0 uses python 2.7.11 and here we need to bypass the certificate check
				from ssl import _create_unverified_context
				if PY2:
					log = loads(urllib2.urlopen(url, timeout=5, context=_create_unverified_context()).read())
				else:
					log = loads(urllib.request.urlopen(url, timeout=5, context=_create_unverified_context()).read())
			except:
				if PY2:
					log = loads(urllib2.urlopen(url, timeout=5).read())
				else:
					log = loads(urllib.request.urlopen(url, timeout=5).read())
			for c in log:
				creator = c['commit']['author']['name']
				title = c['commit']['message']
				date = datetime.strptime(c['commit']['committer']['date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%x %X')
				commitlog += date + ' ' + creator + '\n' + title + 2 * '\n'
			commitlog = commitlog.encode('utf-8')
			self.cachedProjects[self.projects[self.project][1]] = commitlog
		except:
			commitlog += _("Currently the commit log cannot be retrieved - please try later again")
		self["AboutScrollLabel"].setText(commitlog)

	def updateCommitLogs(self):
		if self.projects[self.project][1] in self.cachedProjects:
			self["AboutScrollLabel"].setText(self.cachedProjects[self.projects[self.project][1]])
		else:
			self["AboutScrollLabel"].setText(_("Please wait"))
			self.Timer.start(50, True)

	def left(self):
		self.project = self.project == 0 and len(self.projects) - 1 or self.project - 1
		self.updateCommitLogs()

	def right(self):
		self.project = self.project != len(self.projects) - 1 and self.project + 1 or 0
		self.updateCommitLogs()


class MemoryInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Refresh"))
		self["key_blue"] = Label(_("Clear"))
		self['lmemtext'] = Label()
		self['lmemvalue'] = Label()
		self['rmemtext'] = Label()
		self['rmemvalue'] = Label()
		self['pfree'] = Label()
		self['pused'] = Label()
		self["slide"] = ProgressBar()
		self["slide"].setValue(100)
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))


		self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
			"cancel": self.close,
			"ok": self.getMemoryInfo,
			"green": self.getMemoryInfo,
			"blue": self.clearMemory,
		})

		self["params"] = MemoryInfoSkinParams()

		self['info'] = Label(_("This info is for developers only.\nFor normal users it is not relevant.\nPlease don't panic if you see values displayed looking suspicious!"))

		self.setTitle(_("Memory Info"))
		self.onLayoutFinish.append(self.getMemoryInfo)

	def getMemoryInfo(self):
		try:
			ltext = rtext = ""
			lvalue = rvalue = ""
			mem = 1
			free = 0
			rows_in_column = self["params"].rows_in_column
			for i, line in enumerate(open('/proc/meminfo','r')):
				s = line.strip().split(None, 2)
				if len(s) == 3:
					name, size, units = s
				elif len(s) == 2:
					name, size = s
					units = ""
				else:
					continue
				if name.startswith("MemTotal"):
					mem = int(size)
				if name.startswith("MemFree") or name.startswith("Buffers") or name.startswith("Cached"):
					free += int(size)
				if i < rows_in_column:
					ltext += "".join((name,"\n"))
					lvalue += "".join((size," ",units,"\n"))
				else:
					rtext += "".join((name,"\n"))
					rvalue += "".join((size," ",units,"\n"))
			self['lmemtext'].setText(ltext)
			self['lmemvalue'].setText(lvalue)
			self['rmemtext'].setText(rtext)
			self['rmemvalue'].setText(rvalue)
			self["slide"].setValue(int(100.0*(mem-free)/mem+0.25))
			self['pfree'].setText("%.1f %s" % (100.*free/mem,'%'))
			self['pused'].setText("%.1f %s" % (100.*(mem-free)/mem,'%'))
		except Exception, e:
			print("[About] getMemoryInfo FAIL:", e)

	def clearMemory(self):
		eConsoleAppContainer().execute("sync")
		open("/proc/sys/vm/drop_caches", "w").write("3")
		self.getMemoryInfo()


class MemoryInfoSkinParams(GUIComponent):
	def __init__(self):
		GUIComponent.__init__(self)
		self.rows_in_column = 25

	def applySkin(self, desktop, screen):
		if self.skinAttributes is not None:
			attribs = [ ]
			for (attrib, value) in self.skinAttributes:
				if attrib == "rowsincolumn":
					self.rows_in_column = int(value)
			self.skinAttributes = attribs
			applySkin = GUIComponent
		return applySkin()

	GUI_WIDGET = eLabel


class Troubleshoot(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Troubleshoot"))
		self["AboutScrollLabel"] = ScrollLabel(_("Please wait"))
		self["key_red"] = Button()
		self["key_green"] = Button()
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))

		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions"], {
			"cancel": self.close,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown,
			"moveUp": self["AboutScrollLabel"].homePage,
			"moveDown": self["AboutScrollLabel"].endPage,
			"left": self.left,
			"right": self.right,
			"red": self.red,
			"green": self.green,
		})

		self.container = eConsoleAppContainer()
		self.container.appClosed.append(self.appClosed)
		self.container.dataAvail.append(self.dataAvail)
		self.commandIndex = 0
		self.updateOptions()
		self.onLayoutFinish.append(self.run_console)

	def left(self):
		self.commandIndex = (self.commandIndex - 1) % len(self.commands)
		self.updateKeys()
		self.run_console()

	def right(self):
		self.commandIndex = (self.commandIndex + 1) % len(self.commands)
		self.updateKeys()
		self.run_console()

	def red(self):
		if self.commandIndex >= self.numberOfCommands:
			self.session.openWithCallback(self.removeAllLogfiles, MessageBox, _("Do you want to remove all the crash logfiles"), default=False)
		else:
			self.close()

	def green(self):
		if self.commandIndex >= self.numberOfCommands:
			try:
				os.remove(self.commands[self.commandIndex][4:])
			except:
				pass
			self.updateOptions()
		self.run_console()

	def removeAllLogfiles(self, answer):
		if answer:
			for fileName in self.getLogFilesList():
				try:
					os.remove(fileName)
				except:
					pass
			self.updateOptions()
			self.run_console()

	def appClosed(self, retval):
		if retval:
			self["AboutScrollLabel"].setText(_("An error occurred - Please try again later"))

	def dataAvail(self, data):
		self["AboutScrollLabel"].appendText(data)

	def run_console(self):
		self["AboutScrollLabel"].setText("")
		self.setTitle("%s - %s" % (_("Troubleshoot"), self.titles[self.commandIndex]))
		command = self.commands[self.commandIndex]
		if command.startswith("cat "):
			try:
				self["AboutScrollLabel"].setText(open(command[4:], "r").read())
			except:
				self["AboutScrollLabel"].setText(_("Logfile does not exist anymore"))
		else:
			try:
				if self.container.execute(command):
					raise Exception, "failed to execute: ", command
			except Exception, e:
				self["AboutScrollLabel"].setText("%s\n%s" % (_("An error occurred - Please try again later"), e))

	def cancel(self):
		self.container.appClosed.remove(self.appClosed)
		self.container.dataAvail.remove(self.dataAvail)
		self.container = None
		self.close()

	def getDebugFilesList(self):
		import glob
		return [x for x in sorted(glob.glob("/home/root/logs/enigma2_debug_*.log"), key=lambda x: os.path.isfile(x) and os.path.getmtime(x))]

	def getLogFilesList(self):
		import glob
		home_root = "/home/root/logs/enigma2_crash.log"
		tmp = "/tmp/enigma2_crash.log"
		return [x for x in sorted(glob.glob("/mnt/hdd/*.log"), key=lambda x: os.path.isfile(x) and os.path.getmtime(x))] + (os.path.isfile(home_root) and [home_root] or []) + (os.path.isfile(tmp) and [tmp] or [])

	def updateOptions(self):
		self.titles = ["dmesg", "ifconfig", "df", "top", "ps", "messages"]
		self.commands = ["dmesg", "ifconfig", "df -h", "top -n 1", "ps -l", "cat /var/volatile/log/messages"]
		install_log = "/home/root/autoinstall.log"
		if os.path.isfile(install_log):
				self.titles.append("%s" % install_log)
				self.commands.append("cat %s" % install_log)
		self.numberOfCommands = len(self.commands)
		fileNames = self.getLogFilesList()
		if fileNames:
			totalNumberOfLogfiles = len(fileNames)
			logfileCounter = 1
			for fileName in reversed(fileNames):
				self.titles.append("logfile %s (%s/%s)" % (fileName, logfileCounter, totalNumberOfLogfiles))
				self.commands.append("cat %s" % (fileName))
				logfileCounter += 1
		fileNames = self.getDebugFilesList()
		if fileNames:
			totalNumberOfLogfiles = len(fileNames)
			logfileCounter = 1
			for fileName in reversed(fileNames):
				self.titles.append("debug log %s (%s/%s)" % (fileName, logfileCounter, totalNumberOfLogfiles))
				self.commands.append("tail -n 2500 %s" % (fileName))
				logfileCounter += 1
		self.commandIndex = min(len(self.commands) - 1, self.commandIndex)
		self.updateKeys()

	def updateKeys(self):
		self["key_red"].setText(_("Cancel") if self.commandIndex < self.numberOfCommands else _("Remove all logfiles"))
		self["key_green"].setText(_("Refresh") if self.commandIndex < self.numberOfCommands else _("Remove this logfile"))
