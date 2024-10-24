from enigma import eServiceCenter, eServiceReference, pNavigation, getBestPlayableServiceReference, iPlayableService, setPreferredTuner, eStreamServer, iRecordableServicePtr, eDVBLocalTimeHandler, eTimer
from Components.ImportChannels import ImportChannels
from Components.ParentalControl import parentalControl
from Components.SystemInfo import SystemInfo
from Components.config import config, configfile
from Tools.BoundFunction import boundFunction
from Tools.StbHardware import getFPWasTimerWakeup
from Tools.Alternatives import ResolveCiAlternative
from Tools.Notifications import AddNotification
from time import time
import PowerTimer
import RecordTimer
import Screens.Standby
import NavigationInstance
from ServiceReference import ServiceReference, isPlayableForCur
from Screens.InfoBar import InfoBar
from Components.Sources.StreamService import StreamServiceList
from os.path import exists
from Screens.InfoBarGenerics import streamrelay

# TODO: remove pNavgation, eNavigation and rewrite this stuff in python.


class Navigation:
	def __init__(self, nextRecordTimerAfterEventActionAuto=False, nextPowerManagerAfterEventActionAuto=False):
		if NavigationInstance.instance is not None:
			raise NavigationInstance.instance

		NavigationInstance.instance = self
		self.ServiceHandler = eServiceCenter.getInstance()

		Screens.Standby.TVstate()
		self.pnav = pNavigation()
		self.pnav.m_event.get().append(self.dispatchEvent)
		self.pnav.m_record_event.get().append(self.dispatchRecordEvent)
		self.event = []
		self.record_event = []
		self.currentlyPlayingServiceReference = None
		self.currentlyPlayingServiceOrGroup = None
		self.currentlyPlayingService = None
		self.skipServiceReferenceReset = False
		self.isCurrentServiceStreamRelay = False
		self.RecordTimer = RecordTimer.RecordTimer()
		self.PowerTimer = PowerTimer.PowerTimer()
		self.__wasTimerWakeup = False
		self.__nextRecordTimerAfterEventActionAuto = nextRecordTimerAfterEventActionAuto
		self.__nextPowerManagerAfterEventActionAuto = nextPowerManagerAfterEventActionAuto
		if getFPWasTimerWakeup():
			self.__wasTimerWakeup = True
			self._processTimerWakeup()

		self.__isRestartUI = config.misc.RestartUI.value
		startup_to_standby = config.usage.startup_to_standby.value
		wakeup_time_type = config.misc.prev_wakeup_time_type.value
		if config.usage.remote_fallback_import_restart.value and not config.clientmode.enabled.value:
			ImportChannels()
		if config.clientmode.enabled.value and config.clientmode_import_restart.value:
			import Components.ChannelsImporter
			Components.ChannelsImporter.autostart()
		if self.__wasTimerWakeup:
			if wakeup_time_type == 3 and not config.misc.isNextRecordTimerAfterEventActionAuto.value:  # "inStandby". Do not execute setWasInDeepStandby static method if recording exists.
				RecordTimer.RecordTimerEntry.setWasInDeepStandby()
		if config.misc.RestartUI.value:
			config.misc.RestartUI.value = False
			config.misc.RestartUI.save()
			configfile.save()
		else:
			if config.usage.remote_fallback_import.value and not config.usage.remote_fallback_import_restart.value:
				ImportChannels()
			if startup_to_standby == "yes" or self.__wasTimerWakeup and config.misc.prev_wakeup_time.value and (wakeup_time_type == 0 or wakeup_time_type == 1 or (wakeup_time_type == 3 and startup_to_standby == "except")):
				if not Screens.Standby.inTryQuitMainloop:
					self.standbytimer = eTimer()
					self.standbytimer.callback.append(self.gotostandby)
					self.standbytimer.start(15000, True)  # Time increse 15 second for standby.

	def _processTimerWakeup(self):
		now = time()
		timeHandlerCallbacks = eDVBLocalTimeHandler.getInstance().m_timeUpdated.get()
		if self.__nextRecordTimerAfterEventActionAuto and now < eDVBLocalTimeHandler.timeOK:
			print('[Navigation] RECTIMER: wakeup to standby but system time not set.')
			if self._processTimerWakeup not in timeHandlerCallbacks:
				timeHandlerCallbacks.append(self._processTimerWakeup)
			return
		if self._processTimerWakeup in timeHandlerCallbacks:
			timeHandlerCallbacks.remove(self._processTimerWakeup)

		if self.__nextRecordTimerAfterEventActionAuto and abs(self.RecordTimer.getNextRecordingTime() - now) <= 360:
			print('[Navigation] RECTIMER: wakeup to standby detected.')
			with open("/tmp/was_rectimer_wakeup", "w") as f:
				f.write("1")
			# as we woke the box to record, place the box in standby.
			self.standbytimer = eTimer()
			self.standbytimer.callback.append(self.gotostandby)
			self.standbytimer.start(15000, True)

		elif self.__nextPowerManagerAfterEventActionAuto:
			print('[Navigation] POWERTIMER: wakeup to standby detected.')
			with open("/tmp/was_powertimer_wakeup", "w") as f:
				f.write("1")
			# as a PowerTimer WakeToStandby was actiond to it.
			self.standbytimer = eTimer()
			self.standbytimer.callback.append(self.gotostandby)
			self.standbytimer.start(15000, True)

	def wasTimerWakeup(self):
		return self.__wasTimerWakeup

	def gotostandby(self):
		print('[Navigation] TIMER: now entering standby')
		AddNotification(Screens.Standby.Standby)

	def isRestartUI(self):
		return self.__isRestartUI

	def dispatchEvent(self, i):
		for x in self.event:
			x(i)
		if i == iPlayableService.evEnd:
			if not self.skipServiceReferenceReset:
				self.currentlyPlayingServiceReference = None
				self.currentlyPlayingServiceOrGroup = None
			self.currentlyPlayingService = None

	def dispatchRecordEvent(self, rec_service, event):
		# print "[Navigation] record_event", rec_service, event
		for x in self.record_event:
			x(rec_service, event)

	def playService(self, ref, checkParentalControl=True, forceRestart=False, adjust=True, ignoreStreamRelay=False):
		session = None
		startPlayingServiceOrGroup = None
		count = isinstance(adjust, list) and len(adjust) or 0
		if count > 1 and adjust[0] == 0:
			session = adjust[1]
			if count == 3:
				startPlayingServiceOrGroup = adjust[2]
			adjust = adjust[0]
		oldref = self.currentlyPlayingServiceOrGroup
		if ref and oldref and ref == oldref and not forceRestart:
			print("[Navigation] ignore request to play already running service(1)")
			return 1
		print("[Navigation] playing", ref and ref.toString())
		if exists("/proc/stb/lcd/symbol_signal"):
			with open("/proc/stb/lcd/symbol_signal", "w") as f:
				f.write("1" if ref and "0:0:0:0:0:0:0:0:0" not in ref.toString() and config.lcd.mode.value else "0")
		if ref is None:
			self.stopService()
			return 0
		from Components.ServiceEventTracker import InfoBarCount
		InfoBarInstance = InfoBarCount == 1 and InfoBar.instance
		isStreamRelay = False
		if not checkParentalControl or parentalControl.isServicePlayable(ref, boundFunction(self.playService, checkParentalControl=False, forceRestart=forceRestart, adjust=(count > 1 and [0, session] or adjust)), session=session):
			if ref.flags & eServiceReference.isGroup:
				oldref = self.currentlyPlayingServiceReference or eServiceReference()
				playref = getBestPlayableServiceReference(ref, oldref)
				if playref and config.misc.use_ci_assignment.value and not isPlayableForCur(playref):
					alternative_ci_ref = ResolveCiAlternative(ref, playref)
					if alternative_ci_ref:
						playref = alternative_ci_ref
				if not ignoreStreamRelay:
					playref, isStreamRelay = streamrelay.streamrelayChecker(playref)
				print("[Navigation] playref", playref)
				if playref and oldref and playref == oldref and not forceRestart:
					print("[Navigation] ignore request to play already running service(2)")
					return 1
				if not playref:
					alternativeref = getBestPlayableServiceReference(ref, eServiceReference(), True)
					self.stopService()
					if alternativeref and self.pnav:
						self.currentlyPlayingServiceReference = alternativeref
						self.currentlyPlayingServiceOrGroup = ref
						if self.pnav.playService(alternativeref):
							print("[Navigation] Failed to start: ", alternativeref.toString())
							self.currentlyPlayingServiceReference = None
							self.currentlyPlayingServiceOrGroup = None
							if streamrelay.checkService(oldref):
								print("[Navigation] Streaming was active -> try again")  # use timer to give the streamserver the time to deallocate the tuner
								self.retryServicePlayTimer = eTimer()
								self.retryServicePlayTimer.callback.append(boundFunction(self.playService, ref, checkParentalControl, forceRestart, adjust))
								self.retryServicePlayTimer.start(500, True)
						else:
							print("[Navigation] alternative ref as simulate: ", alternativeref.toString())
					return 0
				elif checkParentalControl and not parentalControl.isServicePlayable(playref, boundFunction(self.playService, checkParentalControl=False, forceRestart=forceRestart, adjust=(count > 1 and [0, session, ref] or adjust)), session=session):
					if self.currentlyPlayingServiceOrGroup and InfoBarInstance and InfoBarInstance.servicelist.servicelist.setCurrent(self.currentlyPlayingServiceOrGroup, adjust):
						self.currentlyPlayingServiceOrGroup = InfoBarInstance.servicelist.servicelist.getCurrent()
					return 1
			else:
				playref = ref
			if self.pnav:
				if not SystemInfo["FCCactive"]:
					self.pnav.stopService()
				else:
					self.skipServiceReferenceReset = True
				self.currentlyPlayingServiceReference = playref
				if not ignoreStreamRelay:
					playref, isStreamRelay = streamrelay.streamrelayChecker(playref)
				print("[Navigation] playref", playref.toString())
				self.currentlyPlayingServiceOrGroup = ref
				if startPlayingServiceOrGroup and startPlayingServiceOrGroup.flags & eServiceReference.isGroup and not ref.flags & eServiceReference.isGroup:
					self.currentlyPlayingServiceOrGroup = startPlayingServiceOrGroup
				if InfoBarInstance and InfoBarInstance.servicelist.servicelist.setCurrent(ref, adjust):
					self.currentlyPlayingServiceOrGroup = InfoBarInstance.servicelist.servicelist.getCurrent()
				setPriorityFrontend = False
				if SystemInfo["DVB-T_priority_tuner_available"] or SystemInfo["DVB-C_priority_tuner_available"] or SystemInfo["DVB-S_priority_tuner_available"] or SystemInfo["ATSC_priority_tuner_available"]:
					str_service = self.currentlyPlayingServiceReference.toString()
					if '%3a//' not in str_service and not str_service.rsplit(":", 1)[1].startswith("/"):
						type_service = self.currentlyPlayingServiceReference.getUnsignedData(4) >> 16
						if type_service == 0xEEEE:
							if SystemInfo["DVB-T_priority_tuner_available"] and config.usage.frontend_priority_dvbt.value != "-2":
								if config.usage.frontend_priority_dvbt.value != config.usage.frontend_priority.value:
									setPreferredTuner(int(config.usage.frontend_priority_dvbt.value))
									setPriorityFrontend = True
							if SystemInfo["ATSC_priority_tuner_available"] and config.usage.frontend_priority_atsc.value != "-2":
								if config.usage.frontend_priority_atsc.value != config.usage.frontend_priority.value:
									setPreferredTuner(int(config.usage.frontend_priority_atsc.value))
									setPriorityFrontend = True
						elif type_service == 0xFFFF:
							if SystemInfo["DVB-C_priority_tuner_available"] and config.usage.frontend_priority_dvbc.value != "-2":
								if config.usage.frontend_priority_dvbc.value != config.usage.frontend_priority.value:
									setPreferredTuner(int(config.usage.frontend_priority_dvbc.value))
									setPriorityFrontend = True
							if SystemInfo["ATSC_priority_tuner_available"] and config.usage.frontend_priority_atsc.value != "-2":
								if config.usage.frontend_priority_atsc.value != config.usage.frontend_priority.value:
									setPreferredTuner(int(config.usage.frontend_priority_atsc.value))
									setPriorityFrontend = True
						else:
							if SystemInfo["DVB-S_priority_tuner_available"] and config.usage.frontend_priority_dvbs.value != "-2":
								if config.usage.frontend_priority_dvbs.value != config.usage.frontend_priority.value:
									setPreferredTuner(int(config.usage.frontend_priority_dvbs.value))
									setPriorityFrontend = True
				if config.misc.softcam_streamrelay_delay.value and self.isCurrentServiceStreamRelay:
					self.skipServiceReferenceReset = False
					self.isCurrentServiceStreamRelay = False
					self.currentlyPlayingServiceReference = None
					self.currentlyPlayingServiceOrGroup = None
					print("[Navigation] Streamrelay was active -> delay the zap till tuner is freed")
					self.retryServicePlayTimer = eTimer()
					self.retryServicePlayTimer.callback.append(boundFunction(self.playService, ref, checkParentalControl, forceRestart, adjust))
					self.retryServicePlayTimer.start(config.misc.softcam_streamrelay_delay.value, True)
					return 0
				elif self.pnav.playService(playref):
					print("[Navigation] Failed to start", playref.toString())
					self.currentlyPlayingServiceReference = None
					self.currentlyPlayingServiceOrGroup = None
					if streamrelay.checkService(oldref):
						print("[Navigation] Streaming was active -> try again")  # use timer to give the streamserver the time to deallocate the tuner
						self.retryServicePlayTimer = eTimer()
						self.retryServicePlayTimer.callback.append(boundFunction(self.playService, ref, checkParentalControl, forceRestart, adjust))
						self.retryServicePlayTimer.start(500, True)
				elif SystemInfo["FbcTunerPowerAlwaysOn"]:
					if streamrelay.checkService(oldref):
						print("[Navigation] Zap any service with SR or not SR with FCC active or not active and any config Mode tuner FBC")  # stop and restart service with timer
						self.currentlyPlayingServiceReference = None
						self.currentlyPlayingServiceOrGroup = None
						self.pnav.stopService()
						self.retryServicePlayTimer = eTimer()
						self.retryServicePlayTimer.callback.append(boundFunction(self.playService, ref, checkParentalControl, forceRestart, adjust))
						self.retryServicePlayTimer.start(3000, True)
				self.skipServiceReferenceReset = False
				if isStreamRelay and not self.isCurrentServiceStreamRelay:
					self.isCurrentServiceStreamRelay = True
				if setPriorityFrontend:
					setPreferredTuner(int(config.usage.frontend_priority.value))
				return 0
		elif oldref and InfoBarInstance and InfoBarInstance.servicelist.servicelist.setCurrent(oldref, adjust):
			self.currentlyPlayingServiceOrGroup = InfoBarInstance.servicelist.servicelist.getCurrent()
		return 1

	def getCurrentlyPlayingServiceReference(self):
		return self.currentlyPlayingServiceReference

	def getCurrentlyPlayingServiceOrGroup(self):
		return self.currentlyPlayingServiceOrGroup

	def recordService(self, ref, simulate=False, type=pNavigation.isUnknownRecording):
		service = None
		if not simulate:
			print("[Navigation] recording service:", (ref and ref.toString()))
		if isinstance(ref, ServiceReference):
			ref = ref.ref
		if ref:
			if ref.flags & eServiceReference.isGroup:
				ref = getBestPlayableServiceReference(ref, eServiceReference(), simulate)
			if type != (pNavigation.isPseudoRecording | pNavigation.isFromEPGrefresh):
				ref, isStreamRelay = streamrelay.streamrelayChecker(ref)
			service = ref and self.pnav and self.pnav.recordService(ref, simulate, type)
			if service is None:
				print("[Navigation] record returned non-zero")
		return service

	def restartService(self):
		self.playService(self.currentlyPlayingServiceOrGroup, forceRestart=True)

	def stopRecordService(self, service):
		ret = -1
		if service and isinstance(service, iRecordableServicePtr):
			ret = self.pnav and self.pnav.stopRecordService(service)
		return ret

	def getRecordings(self, simulate=False, type=pNavigation.isAnyRecording):
		recs = self.pnav and self.pnav.getRecordings(simulate)
		if not simulate and StreamServiceList:
			for rec in recs[:]:
				if rec.__deref__() in StreamServiceList:
					recs.remove(rec)
		return recs

	def getCurrentService(self):
		if not self.currentlyPlayingService:
			self.currentlyPlayingService = self.pnav and self.pnav.getCurrentService()
		return self.currentlyPlayingService

	def stopService(self):
		if self.pnav:
			self.pnav.stopService()
		self.currentlyPlayingServiceReference = None
		self.currentlyPlayingServiceOrGroup = None
		if exists("/proc/stb/lcd/symbol_signal"):
			with open("/proc/stb/lcd/symbol_signal", "w") as f:
				f.write("0")

	def pause(self, p):
		return self.pnav and self.pnav.pause(p)

	def shutdown(self):
		self.RecordTimer.shutdown()
		self.PowerTimer.shutdown()
		self.ServiceHandler = None
		self.pnav = None

	def stopUserServices(self):
		self.stopService()

	def getClientsStreaming(self):
		return eStreamServer.getInstance() and eStreamServer.getInstance().getConnectedClients()

	# def getChannelIPToSAT(self):
	# 	if exists("/etc/enigma2/iptosat.json"):
	# 		with open("/etc/enigma2/iptosat.json", "r") as fr:
	# 			for refiptosat in fr.readlines():
	# 				if "sref" in refiptosat and str(self.currentlyPlayingServiceReference.toString()) in refiptosat:
	# 					return True
	# 			return False
