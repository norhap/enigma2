from ServiceReference import ServiceReference
from Components.config import config
from Screens.MessageBox import MessageBox
from timer import TimerEntry as TimerObject
from Tools.Directories import isPluginInstalled
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, urlopen
from xml.etree.ElementTree import ParseError, fromstring
from base64 import b64encode
from twisted.internet.threads import deferToThread


class FallbackTimerList():

	def __init__(self, parent, fallbackFunction, fallbackFunctionNOK=None):
		self.fallbackFunction = fallbackFunction
		self.fallbackFunctionNOK = fallbackFunctionNOK or fallbackFunction
		self.parent = parent
		self.headers = {}
		self.url = None
		self.list = []
		ipboxclient = False
		if isPluginInstalled("Vision"):
			from Plugins.SystemPlugins.Vision import ClientModeBox  # noqa: F401
			ipboxclient = config.ipboxclient.remotetimers.value
		if (config.usage.remote_fallback_enabled.value and config.usage.remote_fallback_external_timer.value and config.usage.remote_fallback.value) or ipboxclient:
			try:
				address = config.usage.remote_fallback.value.strip()
				parsed = urlsplit(address if "://" in address else "http://%s" % address)
				if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.port == 0:
					raise ValueError("Invalid fallback tuner URL")
				host = "[%s]" % parsed.hostname if ":" in parsed.hostname else parsed.hostname
				self.url = "%s://%s" % (parsed.scheme, host)
				userid = unquote(parsed.username or "")
				password = unquote(parsed.password or "")
				if config.usage.remote_fallback_openwebif_customize.value:
					port = config.usage.remote_fallback_openwebif_port.value
					if not 0 < port < 65536:
						raise ValueError("Invalid OpenWebif port")
					self.url = "%s:%s" % (self.url, port)
					userid = config.usage.remote_fallback_openwebif_userid.value
					password = config.usage.remote_fallback_openwebif_password.value
				if userid:
					credentials = b64encode(("%s:%s" % (userid, password)).encode("UTF-8")).decode("ASCII")
					self.headers = {"Authorization": "Basic %s" % credentials}
			except ValueError as error:
				self.url = None
				parent.onLayoutFinish.append(lambda message=str(error): self.fallback(message))
			else:
				self.getFallbackTimerList()
		else:
			parent.onLayoutFinish.append(self.fallbackFunction)

	# remove any trailing channel name from the service reference
	def cleanServiceRef(self, service_ref):
		service_ref = str(service_ref)
		if not service_ref.endswith(":"):
			service_ref = service_ref.rsplit("::", 1)[0] + ":"
		return service_ref

	def getUrl(self, url):
		address = "%s/%s" % (self.url, url)
		print("[FallbackTimer] getURL", address.split("?", 1)[0])

		def readUrl():
			request = Request(address, headers=self.headers)
			with urlopen(request, timeout=5) as response:
				return response.read()

		# Resolve hostnames through the system resolver without blocking the GUI.
		return deferToThread(readUrl)

	def getFallbackTimerList(self):
		self.list = []
		if self.url:
			self.getUrl("web/timerlist").addCallback(self.gotFallbackTimerList).addErrback(self.fallback)
		else:
			self.fallback()

	def gotFallbackTimerList(self, data):
		try:
			root = fromstring(data)
			if root.tag != "e2timerlist":
				raise ValueError("Invalid timer list response")
			timers = [
				FallbackTimerClass(
					service_ref=str(timer.findtext("e2servicereference", '')),
					name=str(timer.findtext("e2name", '')),
					disabled=int(timer.findtext("e2disabled", 0)),
					timebegin=int(timer.findtext("e2timebegin", 0)),
					timeend=int(timer.findtext("e2timeend", 0)),
					duration=int(timer.findtext("e2duration", 0)),
					startprepare=int(timer.findtext("e2startprepare", 0)),
					state=int(timer.findtext("e2state", 0)),
					repeated=int(timer.findtext("e2repeated", 0)),
					justplay=int(timer.findtext("e2justplay", 0)),
					eit=int(timer.findtext("e2eit", -1)),
					afterevent=int(timer.findtext("e2afterevent", 0)),
					dirname=str(timer.findtext("e2location", '')),
					description=str(timer.findtext("e2description", '')))
				for timer in root.findall("e2timer")]
		except (ParseError, TypeError, ValueError) as e:
			self.fallback(e)
			return
		self.list = timers
		print("[FallbackTimer] read %s timers from fallback tuner" % len(self.list))
		self.parent.session.nav.RecordTimer.setFallbackTimerList(self.list)
		self.fallback()

	def removeTimer(self, timer, fallbackFunction, fallbackFunctionNOK=None):
		self.fallbackFunction = fallbackFunction
		self.fallbackFunctionNOK = fallbackFunctionNOK or fallbackFunction
		self.getUrl("web/timerdelete?sRef=%s&begin=%s&end=%s" % (quote(self.cleanServiceRef(timer.service_ref), safe=""), timer.begin, timer.end)).addCallback(self.getUrlFallback).addErrback(self.fallback)

	def toggleTimer(self, timer, fallbackFunction, fallbackFunctionNOK=None):
		self.fallbackFunction = fallbackFunction
		self.fallbackFunctionNOK = fallbackFunctionNOK or fallbackFunction
		self.getUrl("web/timertogglestatus?sRef=%s&begin=%s&end=%s" % (quote(self.cleanServiceRef(timer.service_ref), safe=""), timer.begin, timer.end)).addCallback(self.getUrlFallback).addErrback(self.fallback)

	def cleanupTimers(self, fallbackFunction, fallbackFunctionNOK=None):
		self.fallbackFunction = fallbackFunction
		self.fallbackFunctionNOK = fallbackFunctionNOK or fallbackFunction
		if self.url:
			self.getUrl("web/timercleanup?cleanup=true").addCallback(self.getUrlFallback).addErrback(self.fallback)
		else:
			self.fallback()

	def addTimer(self, timer, fallbackFunction, fallbackFunctionNOK=None):
		self.fallbackFunction = fallbackFunction
		self.fallbackFunctionNOK = fallbackFunctionNOK or fallbackFunction
		url = "web/timeradd?sRef=%s&begin=%s&end=%s&name=%s&description=%s&disabled=%s&justplay=%s&afterevent=%s&repeated=%s&dirname=%s&eit=%s" % (
			quote(self.cleanServiceRef(timer.service_ref), safe=""),
			timer.begin,
			timer.end,
			quote(timer.name),
			quote(timer.description),
			timer.disabled,
			timer.justplay,
			timer.afterEvent,
			timer.repeated,
			quote(timer.dirname or "", safe=""),
			timer.eit or 0,
		)
		self.getUrl(url).addCallback(self.getUrlFallback).addErrback(self.fallback)

	def editTimer(self, timer, fallbackFunction, fallbackFunctionNOK=None):
		self.fallbackFunction = fallbackFunction
		self.fallbackFunctionNOK = fallbackFunctionNOK or fallbackFunction
		url = "web/timerchange?sRef=%s&begin=%s&end=%s&name=%s&description=%s&disabled=%s&justplay=%s&afterevent=%s&repeated=%s&channelOld=%s&beginOld=%s&endOld=%s&dirname=%s&eit=%s" % (
			quote(self.cleanServiceRef(timer.service_ref), safe=""),
			timer.begin,
			timer.end,
			quote(timer.name),
			quote(timer.description),
			timer.disabled,
			timer.justplay,
			timer.afterEvent,
			timer.repeated,
			quote(str(timer.service_ref_prev), safe=""),
			timer.begin_prev,
			timer.end_prev,
			quote(timer.dirname or "", safe=""),
			timer.eit or 0,
		)
		self.getUrl(url).addCallback(self.getUrlFallback).addErrback(self.fallback)

	def getUrlFallback(self, data):
		try:
			root = fromstring(data)
			state = root.findtext("e2state", "").lower()
			if state not in ("true", "false"):
				raise ValueError("Invalid timer command response")
		except (ParseError, TypeError, ValueError) as error:
			self.fallback(error)
			return
		if state == "true":
			self.getFallbackTimerList()
		else:
			self.fallback(root.findtext("e2statetext") or "Unexpected Error")

	def fallback(self, message=None):
		if message is not None:
			from Tools.Notifications import AddNotificationWithIDCallback
			if hasattr(message, "getErrorMessage"):
				message = message.getErrorMessage()
			print("[FallbackTimer] Error:", message)
			AddNotificationWithIDCallback(self.fallbackNOK, "fallbackFunctionNOK", MessageBox, _("Error while retreiving fallback timer information\n%s") % message, MessageBox.TYPE_ERROR, timeout=10)
		else:
			self.fallbackFunction()

	def fallbackNOK(self, answer=None):
		self.fallbackFunctionNOK()


class FallbackTimerDirs(FallbackTimerList):

	def getFallbackTimerList(self):
		if self.url:
			self.getUrl("web/getlocations").addCallback(self.getlocations).addErrback(self.fallback)
		else:
			self.fallbackFunction()

	def getlocations(self, data):
		self.locations = [c.text for c in fromstring(data)]
		self.getUrl("web/getcurrlocation").addCallback(self.getcurrlocation).addErrback(self.fallback)

	def getcurrlocation(self, data):
		currlocation = [c.text for c in fromstring(data)]
		if currlocation:
			self.fallbackFunction(currlocation[0], self.locations)
		else:
			self.fallbackFunction()


class FallbackTimerClass(TimerObject):
	def __init__(self, service_ref="", name="", disabled=0,
			timebegin=0, timeend=0, duration=0, startprepare=0,
			state=0, repeated=0, justplay=0, eit=0, afterevent=0,
			dirname="", description=""):
		self.service_ref = ServiceReference(service_ref and ':'.join(service_ref.split(':')[:11]) or None)
		self.name = name
		self.disabled = disabled
		self.begin = timebegin
		self.end = timeend
		self.duration = duration
		self.startprepare = startprepare
		self.state = state
		self.repeated = repeated
		self.justplay = justplay
		self.eit = eit
		self.afterEvent = afterevent
		self.dirname = dirname
		self.description = description

		self.findRunningEvent = True
		self.findNextEvent = False

		self.flags = ""
		self.conflict_detection = True
		self.external = True
		self.always_zap = False
		self.zap_wakeup = False
		self.pipzap = False
		self.rename_repeat = False
		self.record_ecm = False
		self.descramble = True
		self.tags = []
		self.repeatedbegindate = timebegin
