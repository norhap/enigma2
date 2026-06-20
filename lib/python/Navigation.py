from enigma import eServiceCenter, eServiceReference, pNavigation, getBestPlayableServiceReference, iPlayableService, iServiceInformation, setPreferredTuner, eStreamServer, iRecordableService, iRecordableServicePtr, eDVBLocalTimeHandler, eTimer
from Components.ImportChannels import ImportChannels
from Components.ParentalControl import parentalControl
from Components.SystemInfo import SystemInfo
from Components.config import config, configfile
from Components.RecordingConfig import recType
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
from Screens.MessageBox import MessageBox
from os.path import exists
from Screens.InfoBarGenerics import streamrelay
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from Tools.Notifications import AddPopup

# TODO: remove pNavgation, eNavigation and rewrite this stuff in python.


class Navigation:
	playServiceExtensions = []
	recordServiceExtensions = []

	def __init__(self, nextRecordTimerAfterEventActionAuto=False, nextPowerManagerAfterEventActionAuto=False):
		if NavigationInstance.instance is not None:
			raise NavigationInstance.instance

		NavigationInstance.instance = self
		self.ServiceHandler = eServiceCenter.getInstance()

		Screens.Standby.TVstate()
		self.pnav = pNavigation()
		self.pnav.m_event.get().append(self.dispatchEvent)
		self.pnav.m_record_event.get().append(self.dispatchRecordEvent)
		self.activeStreamings = []
		self.activeStreamingsByClient = {}
		eStreamServer.getInstance().streamStatusChanged.get().append(self.streamStatusChangedCB)
		self.event = []
		self.record_event = []
		self.currentlyPlayingServiceReference = None
		self.currentlyPlayingServiceOrGroup = None
		self.currentlyPlayingService = None
		self.originalPlayingServiceReference = None
		self.skipServiceReferenceReset = False
		self.isCurrentServiceStreamRelay = False
		self.firstStart = True
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

	def playService(self, ref, checkParentalControl=True, forceRestart=False, adjust=True, ignoreStreamRelay=False, event=None):
		if exists("/proc/stb/lcd/symbol_signal") and hasattr(config.lcd, "mode"):
			with open("/proc/stb/lcd/symbol_signal", "w") as f:
				f.write("1" if ref and "0:0:0:0:0:0:0:0:0" not in ref.toString() and config.lcd.mode.value else "0")
		if ref is None:
			self.stopService()
			return 0
		session = None
		startPlayingServiceOrGroup = None
		count = isinstance(adjust, list) and len(adjust) or 0
		if count > 1 and adjust[0] == 0:
			session = adjust[1]
			if count == 3:
				startPlayingServiceOrGroup = adjust[2]
			adjust = adjust[0]
		oldref = self.currentlyPlayingServiceOrGroup
		current_service_source = None
		isStreamRelay = False
		isAsyncPlay = False
		InfoBarInstance = InfoBar.instance
		if InfoBarInstance:
			current_service_source = InfoBarInstance.session.screen["CurrentService"]
		if ref and oldref and ref == oldref and not forceRestart:
			print("[Navigation] ignore request to play already running service(1)")
			return 1
		print("[Navigation] playing", ref and ref.toString())

		self.currentlyPlayingServiceReference = ref
		self.currentlyPlayingServiceOrGroup = ref
		self.originalPlayingServiceReference = ref
		if InfoBarInstance and current_service_source:
			current_service_source.newService(ref)
			# InfoBarInstance.session.screen["Event_Now"].updateSource(self.currentlyPlayingServiceReference) # respect EIT
			# InfoBarInstance.session.screen["Event_Next"].updateSource(self.currentlyPlayingServiceReference) # respect EIT
			InfoBarInstance.serviceStarted()

		if not checkParentalControl or parentalControl.isServicePlayable(ref, boundFunction(self.playService, checkParentalControl=False, forceRestart=forceRestart, adjust=(count > 1 and [0, session] or adjust)), session=session):
			if ref.flags & eServiceReference.isGroup:
				oldref = self.currentlyPlayingServiceReference or eServiceReference()
				playref = getBestPlayableServiceReference(ref, oldref)
				if playref:
					if config.misc.use_ci_assignment.value and not isPlayableForCur(playref):
						alternative_ci_ref = ResolveCiAlternative(ref, playref)
						if alternative_ci_ref:
							playref = alternative_ci_ref
					if not ignoreStreamRelay:
						playref, isStreamRelay = streamrelay.streamrelayChecker(playref)
					if not isStreamRelay:
						playref, wrappererror = self.serviceHook(playref)
						if wrappererror:
							return 1
					print("[Navigation] playref", playref)
					if oldref and playref == oldref and not forceRestart:
						print("[Navigation] ignore request to play already running service(2)")
						return 1
					if checkParentalControl and not parentalControl.isServicePlayable(playref, boundFunction(self.playService, checkParentalControl=False, forceRestart=forceRestart, adjust=(count > 1 and [0, session, ref] or adjust)), session=session):
						if self.currentlyPlayingServiceOrGroup and InfoBarInstance and InfoBarInstance.servicelist.servicelist.setCurrent(self.currentlyPlayingServiceOrGroup, adjust):
							self.currentlyPlayingServiceOrGroup = InfoBarInstance.servicelist.servicelist.getCurrent()
						return 1
				else:
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
			else:
				playref = ref
			if self.pnav:
				if not SystemInfo["FCCactive"]:
					self.pnav.stopService()
				else:
					self.skipServiceReferenceReset = True
					from enigma import eFCCServiceManager  # noqa: E402 Set FCC not enabled if fallback tuner is active.
					if config.usage.remote_fallback_enabled.value:
						eFCCServiceManager.getInstance().setFCCEnable(False)
						self.serviceHook(playref)
						return 1
					else:
						eFCCServiceManager.getInstance().setFCCEnable(True)
				self.currentlyPlayingServiceReference = playref
				if not ignoreStreamRelay:
					playref, isStreamRelay = streamrelay.streamrelayChecker(playref)
				if not isStreamRelay:
					playref, wrappererror = self.serviceHook(playref)
					if wrappererror:
						return 1
					if SystemInfo["FCCactive"] and "%3a//" in ref.toString():
						self.pnav.stopService()

				originalPlayref = playref.toString()
				for extensionFunc in Navigation.playServiceExtensions:
					ret = extensionFunc(self, playref, event, InfoBarInstance)
					if isinstance(ret, (ServiceReference, eServiceReference)):
						playref = ret
					else:
						playref, isAsyncPlay = ret
					if isAsyncPlay or playref.toString() != originalPlayref:
						break

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
						match type_service:
							case 0xEEEE:
								if SystemInfo["DVB-T_priority_tuner_available"] and config.usage.frontend_priority_dvbt.value != "-2":
									if config.usage.frontend_priority_dvbt.value != config.usage.frontend_priority.value:
										setPreferredTuner(int(config.usage.frontend_priority_dvbt.value))
										setPriorityFrontend = True
								if SystemInfo["ATSC_priority_tuner_available"] and config.usage.frontend_priority_atsc.value != "-2":
									if config.usage.frontend_priority_atsc.value != config.usage.frontend_priority.value:
										setPreferredTuner(int(config.usage.frontend_priority_atsc.value))
										setPriorityFrontend = True
							case 0xFFFF:
								if SystemInfo["DVB-C_priority_tuner_available"] and config.usage.frontend_priority_dvbc.value != "-2":
									if config.usage.frontend_priority_dvbc.value != config.usage.frontend_priority.value:
										setPreferredTuner(int(config.usage.frontend_priority_dvbc.value))
										setPriorityFrontend = True
								if SystemInfo["ATSC_priority_tuner_available"] and config.usage.frontend_priority_atsc.value != "-2":
									if config.usage.frontend_priority_atsc.value != config.usage.frontend_priority.value:
										setPreferredTuner(int(config.usage.frontend_priority_atsc.value))
										setPriorityFrontend = True
							case _:
								if SystemInfo["DVB-S_priority_tuner_available"] and config.usage.frontend_priority_dvbs.value != "-2":
									if config.usage.frontend_priority_dvbs.value != config.usage.frontend_priority.value:
										setPreferredTuner(int(config.usage.frontend_priority_dvbs.value))
										setPriorityFrontend = True
				if (config.misc.softcam_streamrelay_delay.value and self.isCurrentServiceStreamRelay) or (self.firstStart and isStreamRelay):
					self.skipServiceReferenceReset = False
					self.isCurrentServiceStreamRelay = False
					self.currentlyPlayingServiceReference = None
					self.currentlyPlayingServiceOrGroup = None
					print("[Navigation] Streamrelay was active -> delay the zap till tuner is freed")
					self.retryServicePlayTimer = eTimer()
					self.retryServicePlayTimer.callback.append(boundFunction(self.playService, ref, checkParentalControl, forceRestart, adjust))
					delay = 2000 if self.firstStart else config.misc.softcam_streamrelay_delay.value
					self.firstStart = False
					self.retryServicePlayTimer.start(delay, True)
					return 0
				elif not isAsyncPlay and self.pnav.playService(playref):
					print(f"[Navigation] Failed to start '{playref.toString()}'.")
					self.currentlyPlayingServiceReference = None
					self.originalPlayingServiceReference = None
					self.currentlyPlayingServiceOrGroup = None
					if oldref and ("://" in oldref.getPath() or streamrelay.checkService(oldref)):
						print("[Navigation] Streaming was active -> try again")  # use timer to give the streamserver the time to deallocate the tuner
						self.retryServicePlayTimer = eTimer()
						self.retryServicePlayTimer.callback.append(boundFunction(self.playService, ref, checkParentalControl, forceRestart, adjust))
						delay = 500 if not SystemInfo["FBCTuner"] else 1000
						self.retryServicePlayTimer.start(delay, True)
				self.skipServiceReferenceReset = False
				if isStreamRelay and not self.isCurrentServiceStreamRelay:
					self.isCurrentServiceStreamRelay = True
				if InfoBarInstance and "%3a//" in playref.toString() and not isAsyncPlay:
					self.originalPlayingServiceReference = None
					InfoBarInstance.serviceStarted()
				if setPriorityFrontend:
					setPreferredTuner(int(config.usage.frontend_priority.value))
				return 0
		elif oldref and InfoBarInstance and InfoBarInstance.servicelist.servicelist.setCurrent(oldref, adjust):
			self.currentlyPlayingServiceOrGroup = InfoBarInstance.servicelist.servicelist.getCurrent()
		return 1

	def serviceHook(self, ref):
		wrappererror = None
		nref = ref
		if config.usage.remote_fallback_enabled.value and SystemInfo["FCCactive"]:
			return AddPopup(_("Fallback tuner and FCC activated. Activate only one function."), type=MessageBox.TYPE_ERROR, timeout=10)
		elif hasattr(nref, "getPath"):
			for p in plugins.getPlugins(PluginDescriptor.WHERE_PLAYSERVICE):
				(newurl, errormsg) = p(service=nref)
				if errormsg:
					wrappererror = _("Error getting link via %s\n%s") % (p.name, errormsg)
					break
				elif newurl:
					nref.setCompareSref(newurl)
					break
			if wrappererror:
				AddPopup(text=wrappererror, type=MessageBox.TYPE_ERROR, timeout=5, id="channelzapwrapper")
		return nref, wrappererror

	def getCurrentlyPlayingServiceReference(self):
		return self.currentlyPlayingServiceReference

	def getCurrentlyPlayingServiceOrGroup(self):
		return self.currentlyPlayingServiceOrGroup

	def getCurrentServiceReferenceOriginal(self):
		return self.originalPlayingServiceReference or self.currentlyPlayingServiceOrGroup

	def getCurrentServiceRef(self):
		curPlayService = self.getCurrentService()
		info = curPlayService and curPlayService.info()
		return info and info.getInfoString(iServiceInformation.sServiceref)

	def isCurrentServiceIPTV(self):
		ref = self.getCurrentServiceRef()
		ref = ref and eServiceReference(ref)
		path = ref and ref.getPath()
		return path and not path.startswith("/") and ref.type in [0x1, 0x1001, 0x138A, 0x1389]

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
			for f in Navigation.recordServiceExtensions:
				ref = f(self, ref)
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

	def streamStatusChangedCB(self, status, sref, host):
		if "127.0.0.1" in host:  # Ignore local host.
			return
		print(f"[Navigation] Stream status changed: {status}, {sref}, {host}.")
		wasStreaming = bool(self.activeStreamings)
		key = (host or "", sref or "")
		if status == 0:
			ref, count = self.activeStreamingsByClient.get(key, (sref, 0))
			self.activeStreamingsByClient[key] = (ref, count + 1)
		else:
			ref, count = self.activeStreamingsByClient.get(key, (sref, 0))
			if count > 1:
				self.activeStreamingsByClient[key] = (ref, count - 1)
			else:
				self.activeStreamingsByClient.pop(key, None)
		self.activeStreamings = list(dict.fromkeys(ref for ref, count in self.activeStreamingsByClient.values() if ref))

		if wasStreaming != bool(self.activeStreamings):
			for x in self.record_event:
				x(None, iRecordableService.evStart if self.activeStreamings else iRecordableService.evEnd)

	def getRecordings(self, simulate=False, type=pNavigation.isAnyRecording):
		if ((type == pNavigation.isAnyRecording) or (type & pNavigation.isStreaming == pNavigation.isStreaming)) and self.activeStreamings:
			return self.pnav and self.pnav.getRecordings(simulate, type) + self.activeStreamings
		else:
			return self.pnav and self.pnav.getRecordings(simulate, type)

	def getCurrentService(self):
		if not self.currentlyPlayingService:
			self.currentlyPlayingService = self.pnav and self.pnav.getCurrentService()
		return self.currentlyPlayingService

	def getAnyRecordingsCount(self):
		return len(self.getRecordings(False, pNavigation.isAnyRecording))

	def getIndicatorRecordingsCount(self):
		return len(self.getRecordings(False, recType(config.recording.show_rec_symbol_for_rec_types.getValue())))

	def getRealRecordingsCount(self):
		return len(self.getRecordings(False, pNavigation.isRealRecording))

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
