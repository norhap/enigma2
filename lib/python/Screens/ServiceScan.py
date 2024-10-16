from enigma import eDVBDB, eServiceReference, eTimer

from Screens.Screen import Screen
import Screens.InfoBar
from Components.ServiceScan import ServiceScan as CScan
from Components.ProgressBar import ProgressBar
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.FIFOList import FIFOList
from Components.Sources.FrontendInfo import FrontendInfo
from Components.config import config
from os.path import exists
from Screens.Processing import Processing
from Tools.Directories import SCOPE_CONFIG, fileReadLines, resolveFilename, isPluginInstalled

MODULE_NAME = __name__.split(".")[-1]


class ServiceScanSummary(Screen):
	skin = """
	<screen position="0,0" size="132,64">
		<widget name="Title" position="6,4" size="120,42" font="Regular;16" transparent="1" />
		<widget name="scan_progress" position="6,50" zPosition="1" borderWidth="1" size="56,12" backgroundColor="dark" />
		<widget name="Service" position="6,22" size="120,26" font="Regular;12" transparent="1" />
	</screen>"""

	def __init__(self, session, parent, showStepSlider=True):
		Screen.__init__(self, session, parent)

		self["Title"] = Label(parent.title or _("Service Scan"))
		self["Service"] = Label(_("No service"))
		self["scan_progress"] = ProgressBar()

	def updateProgress(self, value):
		self["scan_progress"].setValue(value)

	def updateService(self, name):
		self["Service"].setText(name)


class ServiceScan(Screen):
	def __init__(self, session, scanList):  # noqa: F811
		Screen.__init__(self, session)
		self.setTitle(_("Service Scan"))
		self.scanList = scanList
		self.bouquetLastScanned = None
		if hasattr(session, 'infobar'):
			self.currentInfobar = Screens.InfoBar.InfoBar.instance
			if self.currentInfobar:
				self.currentServiceList = self.currentInfobar.servicelist
				if self.session.pipshown and self.currentServiceList:
					if self.currentServiceList.dopipzap:
						self.currentServiceList.togglePipzap()
					if hasattr(self.session, 'pip'):
						del self.session.pip
					self.session.pipshown = False
		else:
			self.currentInfobar = None
		self.session.nav.stopService()
		self["scan_progress"] = ProgressBar()
		self["scan_state"] = Label(_("scan state"))
		self["network"] = Label()
		self["transponder"] = Label()
		self["pass"] = Label("")
		self["servicelist"] = FIFOList(len=10)
		self["FrontendInfo"] = FrontendInfo()
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("OK"))
		self["actions"] = ActionMap(["SetupActions", "MenuActions"], {
			"ok": self.ok,
			"save": self.ok,
			"cancel": self.cancel,
			"menu": self.doCloseRecursive
		}, -2)
		self.onFirstExecBegin.append(self.doServiceScan)
		self.scanTimer = eTimer()
		self.scanTimer.callback.append(self.scanPoll)
		if isPluginInstalled("LCNScanner"):
			from Plugins.SystemPlugins.LCNScanner.plugin import LCNScanner
			self.LCNScanner = LCNScanner()
		else:
			self.LCNScanner = None

	def ok(self):
		print("[ServiceScan] ok")
		if self["scan"].isDone():
			if self.currentInfobar.__class__.__name__ == "InfoBar":
				selectedService = self["servicelist"].getCurrentSelection()
				if selectedService and self.currentServiceList is not None:
					self.currentServiceList.setTvMode()
					bouquets = self.currentServiceList.getBouquetList()
					last_scanned_bouquet = bouquets and next((x[1] for x in bouquets if x[0] == "Last Scanned"), None)
					if last_scanned_bouquet:
						self.currentServiceList.enterUserbouquet(last_scanned_bouquet)
						self.currentServiceList.setCurrentSelection(eServiceReference(selectedService[1]))
						service = self.currentServiceList.getCurrentSelection()
						if not self.session.postScanService or service != self.session.postScanService:
							self.session.postScanService = service
							self.currentServiceList.addToHistory(service)
						config.servicelist.lastmode.save()
						self.currentServiceList.saveChannel(service)
						self.doCloseRecursive()
			self.cancel()

	def cancel(self):
		self.exit(False)

	def doCloseRecursive(self):
		self.exit(True)

	def exit(self, returnValue):
		if self.currentInfobar.__class__.__name__ == "InfoBar":
			self.close(returnValue)
		self.close()
		if exists(str(self.bouquetLastScanned)) and "en" not in config.osd.language.value:
			with open(self.bouquetLastScanned, "r") as fr:
				bouquetread = fr.readlines()
				with open(self.bouquetLastScanned, "w") as fw:
					for line in bouquetread:
						fw.write(line.replace("Last Scanned", _("Last Scanned")))
			eDVBDB.getInstance().reloadBouquets()
		self.bouquetLastScanned = "/etc/enigma2/userbouquet.LastScanned.tv"

	def scanPoll(self):
		if self["scan"].isDone():
			self.scanTimer.stop()
			self.runLCNScanner()
			self["servicelist"].moveToIndex(0)
			selectedService = self["servicelist"].getCurrentSelection()
			if selectedService:
				self.session.summary.updateService(selectedService[0])

	def doServiceScan(self):
		self["servicelist"].len = self["servicelist"].instance.size().height() // self["servicelist"].l.getItemSize().height()
		self["scan"] = CScan(self["scan_progress"], self["scan_state"], self["servicelist"], self["pass"], self.scanList, self["network"], self["transponder"], self["FrontendInfo"], self.session.summary)

	def runLCNScanner(self):
		def performScan():
			def lcnScannerCallback():
				def clearProcessing():
					Processing.instance.hideProgress()

				self.timer = eTimer()  # This must be in the self context to keep the code alive when the method exits.
				self.timer.callback.append(clearProcessing)
				self.timer.startLongTimer(2)

			try:
				self.LCNScanner.lcnScan(callback=lcnScannerCallback)
			except Exception as err:
				print(f"[ServiceScan] Error: Unable to run the LCNScanner!  ({err})")
				Processing.instance.hideProgress()

		lines = fileReadLines(resolveFilename(SCOPE_CONFIG, "lcndb"), default=[], source=MODULE_NAME)
		if self.LCNScanner and len(lines) > 1:
			print("[ServiceScan] Running the LCNScanner after a scan.")
			Processing.instance.setDescription(_("Please wait while LCN bouquets are created/updated..."))
			Processing.instance.showProgress(endless=True)
			self.timer = eTimer()  # This must be in the self context to keep the code alive when the method exits.
			self.timer.callback.append(performScan)
			self.timer.start(0, True)  # Yield to the idle loop to allow a screen update.

	def createSummary(self):
		print("[ServiceScan] CreateSummary")
		return ServiceScanSummary
