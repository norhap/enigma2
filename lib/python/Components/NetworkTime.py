from Components.Console import Console
from Components.config import config
from enigma import eTimer, eDVBLocalTimeHandler, eEPGCache
from Tools.StbHardware import setRTCtime
from time import time, ctime


def AutoNTPSync(session=None, **kwargs):
	NTPSyncPoller().start()


class NTPSyncPoller:
	"""Automatically Poll NTP"""

	def __init__(self):
		# Init Timer
		self.timer = eTimer()
		self.Console = Console()
		self.previous = 0
		self.onTimeUpdated = []
		timeHandlerCallbacks = eDVBLocalTimeHandler.getInstance().m_timeUpdated.get()
		if self._timeUpdated not in timeHandlerCallbacks:
			timeHandlerCallbacks.append(self._timeUpdated)

	def start(self):
		if self.timecheck not in self.timer.callback:
			self.timer.callback.append(self.timecheck)
		self.ntpConfigUpdated()  # update NTP url, create if not exists

	def stop(self):
		if self.timecheck in self.timer.callback:
			self.timer.callback.remove(self.timecheck)
		self.timer.stop()

	def timecheck(self):
		if config.ntp.timesync.value == "ntp":
			print('[NetworkTime] Updating from NTP')
			self.previous = time()
			# ntpd from BusyBox.
			# -n = Run in foreground
			# -q = Quit after clock is set
			# -p [keyno:NUM:]PEER... Obtain time from PEER (may be repeated)... Use key NUM for authentication... If -p is not given, 'server HOST' lines from /etc/ntp.conf are used.
			# self.Console.ePopen(["/usr/sbin/sntp", "/usr/sbin/sntp", "-S", config.ntp.server.value], self.update_schedule)  add wildcard norhap for SNTP.
			self.Console.ePopen(["/usr/sbin/ntpd", "/usr/sbin/ntpd", "-nq", "-p", config.ntp.server.value], self.update_schedule)
		else:
			self.update_schedule()

	def update_schedule(self, result=None, retVal=None, extra_args=None):
		if retVal and result:
			print("[NetworkTime] Error %d: Unable to synchronize the time!\n%s" % (retVal, result.strip()))
		nowTime = int(time())
		if nowTime > 10000:
			print(f"[NetworkTime] Setting time to {ctime(nowTime)} {(str(nowTime))} from {config.ntp.timesync.toDisplayString(config.ntp.timesync.value)}.")
			setRTCtime(nowTime)
			eDVBLocalTimeHandler.getInstance().setUseDVBTime(True)
			eEPGCache.getInstance().timeUpdated()
			self.timer.startLongTimer(int(config.misc.useNTPminutes.value if config.ntp.timesync.value == "ntp" else config.misc.useNTPminutes.default) * 60)
			if config.ntp.timesync.value == "ntp" and abs(time() - self.previous) > 60:
				for f in self.onTimeUpdated:
					if callable(f):
						f()
		else:
			print('[NetworkTime] NO TIME SET')
			self.timer.startLongTimer(10)

	def ntpConfigUpdated(self):
		self.timer.stop()  # stop current timer if this is an update from Time.py
		self.timer.startLongTimer(0)

	def _timeUpdated(self, dvbtime="DVBLocalTimerHandler"):
		print("[NetworkTime] system clock was updated using", dvbtime)
		for f in self.onTimeUpdated:
			if callable(f):
				f()

	def addTimeUpdatedCallback(self, f):
		if f not in self.onTimeUpdated:
			self.onTimeUpdated.append(f)

	def removeTimeUpdatedCallback(self, f):
		if f in self.onTimeUpdated:
			self.onTimeUpdated.remove(f)

	def __del__(self):
		timeHandlerCallbacks = eDVBLocalTimeHandler.getInstance().m_timeUpdated.get()
		if self._timeUpdated in timeHandlerCallbacks:
			timeHandlerCallbacks.remove(self._timeUpdated)


ntpsyncpoller = NTPSyncPoller()
