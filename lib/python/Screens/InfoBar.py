from os import access, W_OK
from os.path import exists, splitext
from glob import glob
from ast import literal_eval
from re import sub
from pathlib import Path
from enigma import eServiceReference, eProfileWrite, eServiceCenter, iPlayableService  # noqa: E402
eProfileWrite("LOAD:enigma")
import NavigationInstance  # noqa: E402
from ServiceReference import serviceRefIPToSAT  # noqa: E402
from Tools.Directories import fileExists, isPluginInstalled  # noqa: E402
from Tools.Notifications import AddNotification  # noqa: E402
from Tools.SubtitleRenderer import SubtitleRenderer  # noqa: E402
from Components.SystemInfo import BRAND, MODEL  # noqa: E402
from Components.Label import Label  # noqa: E402
from Components.Pixmap import MultiPixmap  # noqa: E402
# workaround for required config entry dependencies.
from Screens.MovieSelection import MovieSelection, moveServiceFiles  # noqa: E402
from Screens.AudioSelection import AudioSelection  # noqa: E402
from Screens.Hotkey import InfoBarHotkey  # noqa: E402
from Screens.Screen import Screen  # noqa: E402
from Screens.MessageBox import MessageBox  # noqa: E402
eProfileWrite("LOAD:InfoBarGenerics")
from Screens.InfoBarGenerics import InfoBarShowHide, \
	InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarRdsDecoder, InfoBarResolutionSelection, InfoBarAspectSelection, \
	InfoBarEPG, InfoBarSeek, InfoBarInstantRecord, InfoBarRedButton, InfoBarTimerButton, InfoBarVmodeButton, \
	InfoBarAudioSelection, InfoBarAdditionalInfo, InfoBarNotifications, InfoBarDish, InfoBarUnhandledKey, \
	InfoBarSubserviceSelection, InfoBarShowMovies, InfoBarTimeshift,  \
	InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, InfoBarBuffer, \
	InfoBarSummarySupport, InfoBarMoviePlayerSummarySupport, InfoBarTimeshiftState, InfoBarTeletextPlugin, InfoBarExtensions, \
	InfoBarSubtitleSupport, InfoBarPiP, InfoBarPlugins, InfoBarServiceErrorPopupSupport, InfoBarJobman, InfoBarZoom, InfoBarOpenOnTopHelper, InfoBarPowersaver, \
	InfoBarHDMI, InfoBarHdmi2, setResumePoint, delResumePoint  # noqa: E402
eProfileWrite("LOAD:InitBar_Components")
from Components.ActionMap import HelpableActionMap  # noqa: E402
from Components.config import config  # noqa: E402
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase  # noqa: E402
from Components.Console import Console  # noqa: E402
eProfileWrite("LOAD:HelpableScreen")
from Screens.HelpMenu import HelpableScreen  # noqa: E402


class InfoBar(InfoBarBase, InfoBarShowHide,
	InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarEPG, InfoBarRdsDecoder, InfoBarResolutionSelection, InfoBarAspectSelection,
	InfoBarInstantRecord, InfoBarAudioSelection, InfoBarRedButton, InfoBarTimerButton, InfoBarVmodeButton,
	HelpableScreen, InfoBarAdditionalInfo, InfoBarNotifications, InfoBarDish, InfoBarUnhandledKey,
	InfoBarSubserviceSelection, InfoBarTimeshift, InfoBarSeek, InfoBarCueSheetSupport, InfoBarBuffer,
	InfoBarSummarySupport, InfoBarTimeshiftState, InfoBarTeletextPlugin, InfoBarExtensions,
	InfoBarPiP, InfoBarPlugins, InfoBarSubtitleSupport, InfoBarServiceErrorPopupSupport, InfoBarJobman, InfoBarZoom, InfoBarOpenOnTopHelper, InfoBarPowersaver,
	InfoBarHDMI, InfoBarHdmi2, InfoBarHotkey, Screen):

	ALLOW_SUSPEND = True
	instance = None

	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = HelpableActionMap(self, ["InfobarActions"], {
			"showMovies": (self.showMovies, _("Play recorded movies")),
			"showRadio": (self.showRadio, _("Show the radio player")),
			"showTv": (self.showTv, _("Show the TV player")),
			"toggleTvRadio": (self.toggleTvRadio, _("Toggle the TV and the radio player")),
			"ZoomInOut": (self.ZoomInOut, _("Zoom In/Out TV")),
			"ZoomOff": (self.ZoomOff, _("Zoom Off"))
		}, prio=2, description=_("Live TV Actions"))
		if isPluginInstalled("AutoTimer"):
			self["key_yellow"] = Label()
			self["key_yellow"].setText(_("AutoTimer"))
		self.radioTV = 0
		self.allowPiP = True
		for x in HelpableScreen, \
			InfoBarBase, InfoBarShowHide, \
			InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarEPG, InfoBarRdsDecoder, InfoBarResolutionSelection, InfoBarAspectSelection, \
			InfoBarInstantRecord, InfoBarAudioSelection, InfoBarRedButton, InfoBarTimerButton, InfoBarUnhandledKey, InfoBarVmodeButton, \
			InfoBarAdditionalInfo, InfoBarNotifications, InfoBarDish, InfoBarSubserviceSelection, InfoBarBuffer, \
			InfoBarTimeshift, InfoBarSeek, InfoBarCueSheetSupport, InfoBarSummarySupport, InfoBarTimeshiftState, \
			InfoBarTeletextPlugin, InfoBarExtensions, InfoBarPiP, InfoBarSubtitleSupport, InfoBarJobman, InfoBarZoom, InfoBarOpenOnTopHelper, InfoBarPowersaver, \
			InfoBarHdmi2, InfoBarPlugins, InfoBarServiceErrorPopupSupport, InfoBarHotkey:
			x.__init__(self)

		self.helpList.append((self["actions"], "InfobarActions", [("showMovies", _("Watch recordings"))]))
		self.helpList.append((self["actions"], "InfobarActions", [("showRadio", _("Listen to the radio"))]))

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
			iPlayableService.evUpdatedEventInfo: self.__eventInfoChanged
		})

		self.current_begin_time = 0
		if InfoBar.instance is not None:
			raise AssertionError("class InfoBar is a singleton class and just one instance of this class is allowed!")
		InfoBar.instance = self
		self.zoomrate = 0
		self.zoomin = 1

	def __onClose(self):
		InfoBar.instance = None

	def __eventInfoChanged(self):
		if self.execing:
			service = self.session.nav.getCurrentService()
			old_begin_time = self.current_begin_time
			info = service and service.info()
			ptr = info and info.getEvent(0)
			self.current_begin_time = ptr and ptr.getBeginTime() or 0
			if config.usage.show_infobar_on_event_change.value:
				if old_begin_time and old_begin_time != self.current_begin_time:
					self.doShow()

	def serviceStarted(self):  # override from InfoBarShowHide
		new = self.servicelist.newServicePlayed()
		if self.execing:
			InfoBarShowHide.serviceStarted(self)
			self.current_begin_time = 0
		elif self.__checkServiceStarted not in self.onShown and new:
			self.onShown.append(self.__checkServiceStarted)

	def __checkServiceStarted(self):
		self.serviceStarted()
		self.onShown.remove(self.__checkServiceStarted)

	def showTvButton(self):
		if BRAND == "GigaBlue":
			self.toggleTvRadio()
		elif MODEL in ("sezam5000hd", "mbtwin", "ini-3000", "ini-5000", "ini-7000", "ini-7012"):
			self.showMovies()
		else:
			self.showTv()

	def showTv(self):
		self.showTvChannelList(True)

	def showRadioButton(self):
		if BRAND in ("GigaBlue",) or MODEL in ("sezam5000hd", "mbtwin", "beyonwizt3", "ini-3000", "ini-5000", "ini-7000", "ini-7012"):
			self.toggleTvRadio()
		else:
			self.showRadio()

	def showRadio(self):
		if config.usage.e1like_radio_mode.value:
			self.showRadioChannelList(True)
		else:
			self.rds_display.hide()  # in InfoBarRdsDecoder
			from Screens.ChannelSelection import ChannelSelectionRadio
			self.session.openWithCallback(self.ChannelSelectionRadioClosed, ChannelSelectionRadio, self)

	def toggleTvRadio(self):
		if self.radioTV == 1:
			self.radioTV = 0
			self.showTv()
		else:
			self.radioTV = 1
			self.showRadio()

	def ChannelSelectionRadioClosed(self, *arg):
		self.rds_display.show()  # in InfoBarRdsDecoder
		self.servicelist.correctChannelNumber()

	def restartLastMovie(self):
		service = eServiceReference(config.usage.last_movie_played.value)
		if service:
			if exists(service.getPath()):
				from Components.ParentalControl import parentalControl
				if parentalControl.isServicePlayable(service, self.openMoviePlayer):
					self.openMoviePlayer(service)

	def showMovies(self, defaultRef=None):
		self.lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self.session.openWithCallback(self.movieSelected, MovieSelection, defaultRef or eServiceReference(config.usage.last_movie_played.value), timeshiftEnabled=self.timeshiftEnabled())

	def movieSelected(self, service):
		ref = self.lastservice
		del self.lastservice
		if service is None:
			if ref and not self.session.nav.getCurrentlyPlayingServiceOrGroup():
				self.session.nav.playService(ref)
		else:
			from Components.ParentalControl import parentalControl
			if parentalControl.isServicePlayable(service, self.openMoviePlayer):
				self.openMoviePlayer(service)

	def openMoviePlayer(self, ref):
		self.session.open(MoviePlayer, ref, slist=self.servicelist, lastservice=self.session.nav.getCurrentlyPlayingServiceOrGroup(), infobar=self)

	def ZoomInOut(self):
		zoomval = 0
		if self.zoomrate > 3:
			self.zoomin = 0
		elif self.zoomrate < -9:
			self.zoomin = 1

		if self.zoomin == 1:
			self.zoomrate += 1
		else:
			self.zoomrate -= 1

		if self.zoomrate < 0:
			zoomval = abs(self.zoomrate) + 10
		else:
			zoomval = self.zoomrate

		print('[InfoBar] zoomRate:', self.zoomrate)
		print('[InfoBar] zoomval:', zoomval)
		if fileExists("/proc/stb/vmpeg/0/zoomrate"):
			print("[InfoBar] Write to /proc/stb/vmpeg/0/zoomrate")
			open("/proc/stb/vmpeg/0/zoomrate", "w").write(int(zoomval))

	def ZoomOff(self):
		self.zoomrate = 0
		self.zoomin = 1
		if fileExists("/proc/stb/vmpeg/0/zoomrate"):
			print("[InfoBar] Write to /proc/stb/vmpeg/0/zoomrate")
			open("/proc/stb/vmpeg/0/zoomrate", "w").write(str(0))


class MoviePlayer(InfoBarBase, InfoBarShowHide, InfoBarMenu, InfoBarSeek, InfoBarShowMovies, InfoBarInstantRecord, InfoBarVmodeButton, InfoBarResolutionSelection, InfoBarAspectSelection,
		InfoBarAudioSelection, HelpableScreen, InfoBarNotifications, InfoBarServiceNotifications, InfoBarPVRState,
		InfoBarCueSheetSupport, InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, Screen, InfoBarTeletextPlugin,
		InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarPlugins, InfoBarPiP, InfoBarZoom, InfoBarHDMI, InfoBarHdmi2, InfoBarHotkey):

	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True
	movie_instance = None

	def __init__(self, session, service, slist=None, lastservice=None, infobar=None):
		Screen.__init__(self, session)

		self["actions"] = HelpableActionMap(self, ["MoviePlayerActions"], {
			"leavePlayer": (self.leavePlayer, _("Leave movie player")),
			"leavePlayerOnExit": (self.leavePlayerOnExit, _("Leave movie player")),
			"channelUp": (self.channelUp, _("When PiPzap enabled zap channel up")),
			"channelDown": (self.channelDown, _("When PiPzap enabled zap channel down"))
		}, prio=0, description=_("Movie Player Actions"))

		self["DirectionActions"] = HelpableActionMap(self, ["DirectionActions"], {
			"left": (self.left, (_("Scan backwards"), _("Pressing this button multiple times will increase the rate of backward scan."))),
			"right": (self.right, (_("Scan forwards"), _("Pressing this button multiple times will increase the rate of forward scan.")))
		}, prio=-2, description=_("Movie Player Actions"))

		self["state"] = Label()
		self["speed"] = Label()
		self["statusicon"] = MultiPixmap()

		self.allowPiP = True

		for x in HelpableScreen, InfoBarShowHide, InfoBarMenu, \
			InfoBarBase, InfoBarSeek, InfoBarShowMovies, InfoBarInstantRecord, InfoBarVmodeButton, \
			InfoBarAudioSelection, InfoBarNotifications, InfoBarResolutionSelection, InfoBarAspectSelection, \
			InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, \
			InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, \
			InfoBarTeletextPlugin, InfoBarServiceErrorPopupSupport, InfoBarExtensions, \
			InfoBarPlugins, InfoBarPiP, InfoBarZoom, InfoBarHotkey:
			x.__init__(self)

		self.subtitle_renderer = SubtitleRenderer(self)
		self.curSubsIndex = -1
		self.onChangedEntry = []
		self.servicelist = slist
		self.infobar = infobar
		self.console = Console()
		self.lastservice = lastservice or session.nav.getCurrentlyPlayingServiceOrGroup()
		self.serviceRefIPToSAT = False
		if serviceRefIPToSAT():
			self.serviceRefIPToSAT = True
		if hasattr(service, "getPath"):
			path = splitext(service.getPath())[0]
			subs = []
			for subtitles in ("srt", "ass", "ssa"):
				subs = glob("%s*.%s" % (path, subtitles))
				if subs:
					break
			if subs:
				service.setSubUri(subs[0])  # Support currently only one external subtitles

		session.nav.playService(service)
		self.cur_service = service
		self.returning = False
		AudioSelection.fillSubtitleExt = self.subtitleListInject
		if self.onAudioSubTrackChanged not in AudioSelection.hooks:
			AudioSelection.hooks.append(self.onAudioSubTrackChanged)

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
			iPlayableService.evStart: self.__evServiceStartInit})
		self.loadSavedSubtitle(service)

		config.misc.standbyCounter.addNotifier(self.standbyCountChanged, initial_call=False)
		self.movieselection_dlg = None
		MoviePlayer.movie_instance = self

	def clearHooks(self):
		AudioSelection.fillSubtitleExt = None
		if self.onAudioSubTrackChanged in AudioSelection.hooks:
			AudioSelection.hooks.remove(self.onAudioSubTrackChanged)

	def __onClose(self):
		# clear the instance value so the skin reloader works correctly
		MoviePlayer.instance = None
		self.clearHooks()
		config.misc.standbyCounter.removeNotifier(self.standbyCountChanged)
		from Screens.MovieSelection import playlist
		del playlist[:]
		if not config.movielist.stop_service.value:
			InfoBar.instance.callServiceStarted()
		self.session.nav.playService(self.lastservice)
		config.usage.last_movie_played.value = self.cur_service and self.cur_service.toString() or ""
		config.usage.last_movie_played.save()

	def standbyCountChanged(self, value):
		if config.ParentalControl.servicepinactive.value:
			from Components.ParentalControl import parentalControl
			if parentalControl.isProtected(self.cur_service):
				self.close()

	def handleLeave(self, how):
		self.is_closing = True
		if how == "ask":
			if config.usage.setup_level.index < 2:  # -expert
				list = (
					(_("Yes"), "quit"),
					(_("No"), "continue")
				)
			else:
				list = (
					(_("Yes, return to the previous channel"), "quit"),
					(_("Yes, returning to movie list"), "movielist"),
					(_("Yes, delete this movie and return to previous channel"), "quitanddelete"),
					(_("Yes, delete this movie and return to movie list"), "deleteandmovielist"),
					(_("No"), "continue"),
					(_("No, but restart from begin"), "restart")
				)

			from Screens.ChoiceBox import ChoiceBox
			self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list=list)
		else:
			self.leavePlayerConfirmed([True, how])

	def leavePlayer(self):
		if config.usage.on_movie_stop.default and self.serviceRefIPToSAT:
			self.console.ePopen(['sleep 3'], self.killIPToSATPlayer)
		setResumePoint(self.session)
		self.selected_subtitle = (0, 0, 0, 0, "")
		self.subtitle_renderer.stopSubtitles()
		self.handleLeave(config.usage.on_movie_stop.value)
		if config.usage.on_movie_stop.value == "quit":
			self.session.nav.stopService()
			self.session.nav.playService(self.lastservice)

	def killIPToSATPlayer(self, result=None, retVal=None, extra_args=None):
		from Plugins.Extensions.IPToSAT.plugin import killActivePlayer  # noqa: E402
		killActivePlayer()

	def leavePlayerOnExit(self):
		if self.shown:
			self.hide()
		elif self.session.pipshown and "popup" in config.usage.pip_hideOnExit.value:
			if config.usage.pip_hideOnExit.value == "popup":
				self.session.openWithCallback(self.hidePipOnExitCallback, MessageBox, _("Disable Picture in Picture"), simple=True)
			else:
				self.hidePipOnExitCallback(True)
		elif config.usage.leave_movieplayer_onExit.value == "popup":
			self.session.openWithCallback(self.leavePlayerOnExitCallback, MessageBox, _("Exit movie player?"), simple=True)
		elif config.usage.leave_movieplayer_onExit.value == "without popup":
			self.leavePlayerOnExitCallback(True)
		elif config.usage.leave_movieplayer_onExit.value == "no with popup" or "no" in config.usage.leave_movieplayer_onExit.value and self.__class__.__name__ == "MoviePlayer" and self.session.nav.getRecordings():
			AddNotification(MessageBox, _("Press STOP and then EXIT to exit the movie list."), MessageBox.TYPE_INFO, timeout=8)

	def leavePlayerOnExitCallback(self, answer):
		if answer:
			setResumePoint(self.session)
			self.handleLeave("quit")
			self.session.nav.stopService()  # return to previous channel
			self.session.nav.playService(self.lastservice)

	def hidePipOnExitCallback(self, answer):
		if answer:
			self.showPiP()

	def deleteConfirmed(self, answer):
		if answer:
			self.leavePlayerConfirmed((True, "quitanddeleteconfirmed"))

	def deleteAndMovielistConfirmed(self, answer):
		if answer:
			self.leavePlayerConfirmed((True, "deleteandmovielistconfirmed"))

	def movielistAgain(self):
		from Screens.MovieSelection import playlist
		del playlist[:]
		self.leavePlayerConfirmed((True, "movielist"))

	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]
		if answer is None:
			return
		if answer in ("quitanddelete", "quitanddeleteconfirmed", "deleteandmovielist", "deleteandmovielistconfirmed"):
			ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			serviceHandler = eServiceCenter.getInstance()
			if answer in ("quitanddelete", "deleteandmovielist"):
				msg = ''
				if config.usage.movielist_trashcan.value:
					import Tools.Trashcan
					try:
						trash = Tools.Trashcan.createTrashFolder(ref.getPath())
						moveServiceFiles(ref, trash)
						# Moved to trash, okay
						if answer == "quitanddelete":
							self.close()
							self.session.nav.stopService()  # return to previous channel
							self.session.nav.playService(self.lastservice)
						else:
							self.movielistAgain()
						return
					except Exception as e:
						print("[InfoBar] Failed to move to .Trash folder:", e)
						msg = _("Cannot move to trash can") + "\n" + str(e) + "\n"
				info = serviceHandler.info(ref)
				name = info and info.getName(ref) or _("this recording")
				msg += _("Do you really want to delete %s?") % name
				if answer == "quitanddelete":
					self.session.openWithCallback(self.deleteConfirmed, MessageBox, msg)
				elif answer == "deleteandmovielist":
					self.session.openWithCallback(self.deleteAndMovielistConfirmed, MessageBox, msg)
				return

			elif answer in ("quitanddeleteconfirmed", "deleteandmovielistconfirmed"):
				offline = serviceHandler.offlineOperations(ref)
				if offline.deleteFromDisk(0):
					self.session.openWithCallback(self.close, MessageBox, _("You cannot delete this!"), MessageBox.TYPE_ERROR)
					if answer == "deleteandmovielistconfirmed":
						self.movielistAgain()
					return

		if answer in ("quit", "quitanddeleteconfirmed"):
			# make sure that playback is unpaused otherwise the
			# player driver might stop working
			self.setSeekState(self.SEEK_STATE_PLAY)
			self.session.nav.stopService()  # return to previous channel
			self.session.nav.playService(self.lastservice)
			self.close()
		elif answer in ("movielist", "deleteandmovielistconfirmed"):
			ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			self.returning = True
			self.session.openWithCallback(self.movieSelected, MovieSelection, ref)
			# make sure that playback is unpaused otherwise the
			# player driver might stop working
			self.setSeekState(self.SEEK_STATE_PLAY)
			self.session.nav.stopService()
			if not config.movielist.stop_service.value:
				self.session.nav.playService(self.lastservice)
		elif answer == "restart":
			self.doSeek(0)
			self.setSeekState(self.SEEK_STATE_PLAY)
		elif answer in ("playlist", "loop"):
			(next_service, item, length) = self.getPlaylistServiceInfo(self.cur_service)
			from Screens.MovieSelection import playlist
			if playlist:
				self.activeResumePosition(True)
			if next_service is not None:
				if config.usage.next_movie_msg.value:
					self.displayPlayedName(next_service, item, length)
				if playlist:
					self.is_closing = False
					self.activeResumePosition(True)
				self.session.nav.playService(next_service)
				self.cur_service = next_service
			else:
				if answer == "playlist":
					self.leavePlayerConfirmed([True, "movielist"])
				elif answer == "loop" and length > 0:
					self.leavePlayerConfirmed([True, "loop"])
				else:
					self.leavePlayerConfirmed([True, "quit"])
		elif answer in ("repeatcurrent"):
			if config.usage.next_movie_msg.value:
				(item, length) = self.getPlaylistServiceInfo(self.cur_service)
				self.displayPlayedName(self.cur_service, item, length)
			self.session.nav.stopService()
			self.session.nav.playService(self.cur_service)

	def doEofInternal(self, playing):
		if self.execing and playing:
			ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			if ref:
				delResumePoint(ref)
			if self.serviceRefIPToSAT and config.usage.on_movie_eof.value == "movielist":
				self.console.ePopen(['sleep 3'], self.killIPToSATPlayer)
			self.handleLeave(config.usage.on_movie_eof.value)

	def up(self):
		if self.servicelist and self.servicelist.dopipzap:
			if config.usage.oldstyle_zap_controls.value:
				self.zapDown()
			else:
				self.switchChannelUp()
		else:
			self.showMovies()

	def down(self):
		if self.servicelist and self.servicelist.dopipzap:
			if config.usage.oldstyle_zap_controls.value:
				self.zapUp()
			else:
				self.switchChannelDown()
		else:
			self.showMovies()

	def right(self):
		if self.servicelist and self.servicelist.dopipzap:
			if config.usage.oldstyle_zap_controls.value:
				self.switchChannelDown()
			else:
				self.zapDown()
		else:
			InfoBarSeek.seekFwd(self)

	def left(self):
		if self.servicelist and self.servicelist.dopipzap:
			if config.usage.oldstyle_zap_controls.value:
				self.switchChannelUp()
			else:
				self.zapUp()
		else:
			InfoBarSeek.seekBack(self)

	def channelUp(self):
		if config.usage.zap_with_ch_buttons.value and self.servicelist and self.servicelist.dopipzap:
			self.zapDown()
		else:
			return 0

	def channelDown(self):
		if config.usage.zap_with_ch_buttons.value and self.servicelist and self.servicelist.dopipzap:
			self.zapUp()
		else:
			return 0

	def switchChannelDown(self):
		if self.servicelist:
			if "keep" not in config.usage.servicelist_cursor_behavior.value:
				self.servicelist.moveDown()
			self.session.execDialog(self.servicelist)

	def switchChannelUp(self):
		if self.servicelist:
			if "keep" not in config.usage.servicelist_cursor_behavior.value:
				self.servicelist.moveUp()
			self.session.execDialog(self.servicelist)

	def zapUp(self):
		slist = self.servicelist
		if slist:
			if slist.inBouquet():
				prev = slist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value:
							if slist.atBegin():
								slist.prevBouquet()
						slist.moveUp()
						cur = slist.getCurrentSelection()
						if cur:
							playable = not (cur.flags & (64 | 8)) and hasattr(self.session, "pip") and self.session.pip.isPlayableForPipService(cur)
							if cur.toString() == prev or playable:
								break
			else:
				slist.moveUp()
			slist.zap(enable_pipzap=True)

	def zapDown(self):
		slist = self.servicelist
		if slist:
			if slist.inBouquet():
				prev = slist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value and slist.atEnd():
							slist.nextBouquet()
						else:
							slist.moveDown()
						cur = slist.getCurrentSelection()
						if cur:
							playable = not (cur.flags & (64 | 8)) and hasattr(self.session, "pip") and self.session.pip.isPlayableForPipService(cur)
							if cur.toString() == prev or playable:
								break
			else:
				slist.moveDown()
			slist.zap(enable_pipzap=True)

	def showPiP(self):
		slist = self.servicelist
		if self.session.pipshown:
			if slist and slist.dopipzap:
				slist.togglePipzap()
			if self.session.pipshown:
				del self.session.pip
				self.session.pipshown = False
		elif slist:
			from Screens.PictureInPicture import PictureInPicture
			self.session.pip = self.session.instantiateDialog(PictureInPicture)
			self.session.pip.show()
			if self.session.pip.playService(slist.getCurrentSelection()):
				self.session.pipshown = True
				self.session.pip.servicePath = slist.getCurrentServicePath()
			else:
				self.session.pipshown = False
				del self.session.pip

	def movePiP(self):
		if self.session.pipshown:
			InfoBarPiP.movePiP(self)

	def swapPiP(self):
		pass

	def showDefaultEPG(self):
		self.infobar and self.infobar.showMultiEPG()

	def openEventView(self):
		self.infobar and self.infobar.showDefaultEPG()

	def showEventInfoPlugins(self):
		self.infobar and self.infobar.showEventInfoPlugins()

	def showEventGuidePlugins(self):
		self.infobar and self.infobar.showEventGuidePlugins()

	def openSingleServiceEPG(self):
		self.infobar and self.infobar.openSingleServiceEPG()

	def openMultiServiceEPG(self):
		self.infobar and self.infobar.openMultiServiceEPG()

	def showMovies(self):
		if config.movielist.stop_service.value:
			self.session.nav.stopService()
		ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self.playingservice = ref  # movie list may change the currently playing
		self.movieselection_dlg = self.session.openWithCallback(self.movieSelected, MovieSelection, ref)

	def movieSelected(self, service):
		if service is not None:
			if self.cur_service and self.cur_service != service:
				setResumePoint(self.session)
			self.cur_service = service
			self.is_closing = False
			self.session.nav.playService(service)
			self.returning = False
		elif self.returning:
			self.close()
		else:
			self.is_closing = False
			ref = self.playingservice
			del self.playingservice
			# no selection? Continue where we left off
			if ref and not self.session.nav.getCurrentlyPlayingServiceOrGroup():
				self.session.nav.playService(ref)
		self.movieselection_dlg = None

	def getPlaylistServiceInfo(self, service):
		from Screens.MovieSelection import playlist
		for i, item in enumerate(playlist):
			if item == service:
				if config.usage.on_movie_eof.value == "repeatcurrent":
					return (i + 1, len(playlist))
				i += 1
				if i < len(playlist):
					return (playlist[i], i + 1, len(playlist))
				elif config.usage.on_movie_eof.value == "loop":
					return (playlist[0], 1, len(playlist))
		return (None, 0, 0)

	def save_subconf(self, obj, file_path: str):
		"""
		Saves the tuple using repr() into <file_path>.subconf
		"""
		repr_string = repr(obj)
		cleaned = sub(r"<bound method[^>]+>", "None", repr_string)
		cleaned = cleaned.replace("PosixPath(", "").replace("))", ")").replace("None>", "None")
		path = Path(file_path).with_suffix(".subconf")
		# Check directory write permission
		directory = path.parent
		if not access(directory, W_OK):
			return  # directory is read-only
		with path.open("w", encoding="utf-8") as f:
			f.write(cleaned)

	def load_subconf(self, file_path: str):
		"""
		Loads the tuple from <file_path>.subconf
		Removes any '<bound method ...>' entries and replaces them with None.
		"""
		path = Path('.').resolve().with_name('.subconf')
		if not path.exists():
			return None
		raw = path.read_text(encoding="utf-8")

		# Safely evaluate tuple literal
		return literal_eval(raw)

	def delete_subconf(self, file_path: str):
		"""
		Deletes the <file>.subconf file if it exists.
		"""
		path = Path(file_path).with_suffix(".subconf")

		if path.exists():
			path.unlink()   # remove the file
			return True
		return False

	def loadSavedSubtitle(self, service):
		path = service.getPath()
		if not path:
			return
		try:
			subtitle_parsed = self.load_subconf(path)
			if subtitle_parsed:
				subtitle = (subtitle_parsed[0], subtitle_parsed[1], subtitle_parsed[2], subtitle_parsed[3], subtitle_parsed[4], self.runSubtitles, subtitle_parsed[6])
				self.runSubtitles(subtitle=subtitle)
		except:
			pass  # this in case sometimes event comes too fast and is got by the MoviePlayer before the InfoBar, so the subconf file is not yet created, or any other issue with loading/parsing the file.

	def __evServiceStartInit(self):
		service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
		if not service:
			return
		self.loadSavedSubtitle(service)

	def extract_language_from_filename(self, path: Path) -> str | None:
		"""
		Extracts the language code from an .srt filename.
		Returns None if no language code is detected.
		"""
		parts = path.stem.split(".")
		if len(parts) <= 1:
			return None  # no language token

		lang = parts[-1]  # last token before extension

		# Basic heuristic: language codes are usually 2–5 chars, letters or hyphens
		if 2 <= len(lang) <= 5 and all(c.isalpha() or c == "-" for c in lang):
			return lang

		return None

	def find_related_srt_files(self, file_path: str):
		file_path_obj = Path(file_path).resolve()
		base_name = file_path_obj.stem
		directory = file_path_obj.parent

		matches = []

		for p in directory.glob(f"{base_name}*.srt"):
			if not p.is_file():
				continue

			lang = self.extract_language_from_filename(p)
			matches.append({
				"path": p,
				"language": lang
			})

		return matches

	def subtitleListInject(self, subtitlesList):
		service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
		if not service:
			return
		if subtitlesList:
			if len(subtitlesList) > 0:
				i = subtitlesList[-1][1] + 1
			else:
				i = 1
		subtitletracks = self.find_related_srt_files(service.getPath())
		for stream in subtitletracks:
			subtitlesList.append((2, i, 4, i, stream["language"], self.runSubtitles, stream["path"]))

			i += 1

	def onAudioSubTrackChanged(self):
		if self.selected_subtitle and len(self.selected_subtitle) > 5:
			return
		service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
		if service:
			self.delete_subconf(service.getPath())
		self.curSubsIndex = -1

	def loadAndParseSubs(self, stream_url):
		try:
			path = Path(stream_url)
			subs_file = path.read_text(encoding='utf-8', errors='replace')
			self.subtitle_renderer.loadSubtitles(subs_file, "SRT")
			return True
		except:
			pass
		return False

	def runSubtitles(self, subtitle, sindex=-1):
		if not subtitle and sindex > -1:
			return

		if not subtitle:
			self.subtitle_renderer.stopSubtitles()
			self.selected_subtitle = (0, 0, 0, 0, "")
			self.curSubsIndex = -1
			self.delete_subconf(self.cur_service.getPath())
			return

		print(f"Selected subtitle: {subtitle}")
		self.enableSubtitle(None)
		subs_uri = subtitle[6]
		print(f"Loading subtitles from {subs_uri}")
		self.loadAndRunSubs(subs_uri, subtitle)

	def loadAndRunSubs(self, subs_uri, subtitle):
		result = self.loadAndParseSubs(subs_uri)
		if result:
			self.subtitle_renderer.startSubtitle()
			self.selected_subtitle = subtitle
			self.curSubsIndex = subtitle[3]
			self.save_subconf(subtitle, self.cur_service.getPath())
		else:
			pass  # TODO: add message, log, etc...

	def displayPlayedName(self, ref, index, n):
		from Tools.Notifications import AddPopup
		AddPopup(text="%s/%s: %s" % (index, n, self.ref2HumanName(ref)), type=MessageBox.TYPE_INFO, timeout=5)

	def ref2HumanName(self, ref):
		return eServiceCenter.getInstance().info(ref).getName(ref)
