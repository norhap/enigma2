from enigma import eBackgroundFileEraser, eActionMap, eDVBDB, eEnv, eSubtitleSettings, eSettings, setEnableTtCachingOnOff, setPreferredTuner, setSpinnerOnOff, setTunerTypePriorityOrder, Misc_Options, eServiceEvent, eDVBLocalTimeHandler, eEPGCache

from locale import AM_STR, PM_STR, nl_langinfo
from os import listdir, makedirs, remove
from glob import glob
from os.path import exists, isfile, ismount, join, normpath
from time import mktime
from gettext import ngettext
from skin import parameters
from Components.About import GetIPsFromNetworkInterfaces
from Components.config import ConfigBoolean, ConfigClock, ConfigDictionarySet, ConfigEnableDisable, ConfigInteger, ConfigIP, ConfigLocations, ConfigNumber, ConfigPassword, ConfigSelection, ConfigSelectionNumber, ConfigSet, ConfigSlider, ConfigSubDict, ConfigSubsection, ConfigText, ConfigYesNo, NoSave, config, ConfigOnOff
from Components.Console import Console
from Components.Harddisk import harddiskmanager
from keyids import KEYIDS
from Components.NimManager import nimmanager
from Components.ServiceList import refreshServiceList
from Components.SystemInfo import BoxInfo, SystemInfo, MODEL
from Tools.Directories import SCOPE_HDD, SCOPE_TIMESHIFT, SCOPE_CONFIG, defaultRecordingLocation, fileContains, fileWriteLine, resolveFilename

MODULE_NAME = __name__.split(".")[-1]
originalAudioTracks = "orj dos ory org esl qaa qaf und mis mul ORY ORJ Audio_ORJ oth"
visuallyImpairedCommentary = "NAR qad"


def InitUsageConfig():
	config.usage = ConfigSubsection()
	config.usage.dns = ConfigSelection(default="dhcp-router", choices=[
		("dhcp-router", "DHCP Router"),
		("staticip", _("Static IP Router")),
		("google", "Google DNS"),
		("quad9security", "Quad9 Security"),
		("quad9nosecurity", "Quad9 No Security"),
		("cloudflare", "Cloudflare"),
		("nordvpn", "NordVPN"),
		("opendns", "OpenDNS"),
		("opendns-2", "OpenDNS-2")
	])
	config.usage.subnetwork = ConfigYesNo(default=True)
	config.usage.subnetwork_cable = ConfigYesNo(default=True)
	config.usage.subnetwork_terrestrial = ConfigYesNo(default=True)
	config.usage.showdish = ConfigYesNo(default=True)
	config.usage.multibouquet = ConfigYesNo(default=True)

	showrotorpositionChoicesUpdate()

	config.usage.sort_pluginlist = ConfigYesNo(default=True)
	config.pluginbrowser = ConfigSubsection()
	config.pluginbrowser.languages_po = ConfigYesNo(default=False)
	config.pluginbrowser.src = ConfigYesNo(default=False)

	def correctInvalidEPGDataChange(configElement):
		eServiceEvent.setUTF8CorrectMode(int(configElement.value))

	config.usage.correct_invalid_epgdata = ConfigSelection(default="1", choices=[
		("0", _("Disabled")),
		("1", _("Enabled")),
		("2", _("Debug"))
	])
	config.usage.correct_invalid_epgdata.addNotifier(correctInvalidEPGDataChange)

	config.usage.alternative_number_mode = ConfigYesNo(default=False)

	config.parental = ConfigSubsection()
	config.parental.lock = ConfigOnOff(default=False)
	config.parental.setuplock = ConfigOnOff(default=False)

	config.expert = ConfigSubsection()
	config.expert.satpos = ConfigOnOff(default=True)
	config.expert.fastzap = ConfigOnOff(default=True)
	config.expert.skipconfirm = ConfigOnOff(default=False)
	config.expert.hideerrors = ConfigOnOff(default=False)
	config.expert.autoinfo = ConfigOnOff(default=True)

	def alternativeNumberModeChange(configElement):
		eDVBDB.getInstance().setNumberingMode(configElement.value)
		refreshServiceList()
	config.usage.alternative_number_mode.addNotifier(alternativeNumberModeChange)

	config.usage.servicelist_twolines = ConfigSelection(default="0", choices=[
		("0", _("Single line mode")),
		("1", _("Two lines")),
		("2", _("Two lines and next event"))
	])
	config.usage.servicelist_twolines.addNotifier(refreshServiceList)

	config.usage.hide_number_markers = ConfigYesNo(default=True)
	config.usage.hide_number_markers.addNotifier(refreshServiceList)

	config.usage.servicetype_icon_mode = ConfigSelection(default="1", choices=[
		("0", _("None")),
		("1", _("Left from servicename")),
		("2", _("Right from servicename"))
	])
	config.usage.servicetype_icon_mode.addNotifier(refreshServiceList)
	config.usage.crypto_icon_mode = ConfigSelection(default="2", choices=[
		("0", _("None")),
		("1", _("Left from servicename")),
		("2", _("Right from servicename"))
	])
	config.usage.crypto_icon_mode.addNotifier(refreshServiceList)
	config.usage.record_indicator_mode = ConfigSelection(default="3", choices=[
		("0", _("None")),
		("1", _("Left from servicename")),
		("2", _("Right from servicename")),
		("3", _("Red colored"))
	])
	config.usage.record_indicator_mode.addNotifier(refreshServiceList)

	choicelist = [("-1", _("Disable"))]
	for i in range(0, 1300, 100):
		choicelist.append((str(i), ngettext("%d pixel wide", "%d pixels wide", i) % i))
	config.usage.servicelist_column = ConfigSelection(default="-1", choices=choicelist)
	config.usage.servicelist_column.addNotifier(refreshServiceList)

	config.usage.service_icon_enable = ConfigYesNo(default=True)
	config.usage.service_icon_enable.addNotifier(refreshServiceList)
	config.usage.servicelist_cursor_behavior = ConfigSelection(default="keep", choices=[
		("standard", _("Standard")),
		("keep", _("Keep service")),
		("reverseB", _("Reverse bouquet buttons")),
		("keep reverseB", "%s + %s" % (_("Keep service"), _("Reverse bouquet buttons")))
	])

	choicelist = [("by skin", _("As defined by the skin"))]
	for i in range(5, 41):
		choicelist.append((str(i)))
	config.usage.servicelist_number_of_services = ConfigSelection(default="by skin", choices=choicelist)
	config.usage.servicelist_number_of_services.addNotifier(refreshServiceList)

	config.usage.multiepg_ask_bouquet = ConfigYesNo(default=False)

	config.usage.quickzap_bouquet_change = ConfigYesNo(default=False)
	config.usage.e1like_radio_mode = ConfigYesNo(default=True)
	config.usage.e1like_radio_mode_last_play = ConfigYesNo(default=False)
	choicelist = [("0", _("No timeout"))]
	for i in range(1, 12):
		choicelist.append((str(i), ngettext("%d second", "%d seconds", i) % i))
	config.usage.infobar_timeout = ConfigSelection(default="5", choices=choicelist)
	config.usage.fadeout = ConfigYesNo(default=False)
	config.usage.show_infobar_do_dimming = ConfigYesNo(default=False)
	config.usage.show_infobar_dimming_speed = ConfigSelectionNumber(min=1, max=40, stepwidth=1, default=40, wraparound=True)
	config.usage.show_infobar_on_zap = ConfigYesNo(default=True)
	config.usage.show_infobar_on_skip = ConfigYesNo(default=True)
	config.usage.show_infobar_on_event_change = ConfigYesNo(default=False)
	config.usage.show_second_infobar = ConfigSelection(default="0", choices=[("", _("None"))] + choicelist + [("EPG", _("EPG"))])
	config.usage.show_simple_second_infobar = ConfigYesNo(default=False)
	config.usage.infobar_frontend_source = ConfigSelection(default="settings", choices=[
		("settings", _("Settings")),
		("tuner", _("Tuner"))
	])
	config.usage.oldstyle_zap_controls = ConfigYesNo(default=False)
	config.usage.oldstyle_channel_select_controls = ConfigYesNo(default=False)
	config.usage.zap_with_ch_buttons = ConfigYesNo(default=False)
	config.usage.ok_is_channelselection = ConfigYesNo(default=False)
	config.usage.channelselection_preview = ConfigYesNo(default=False)
	config.usage.show_spinner = ConfigYesNo(default=True)
	config.usage.plugin_sort_weight = ConfigDictionarySet()
	config.usage.menu_sort_weight = ConfigDictionarySet(default={"mainmenu": {"submenu": {}}})
	config.usage.menu_sort_mode = ConfigSelection(default="user", choices=[
		("a_z", _("Alphabetical")),
		("default", _("Default")),
		("user", _("User defined")),
		("user_hidden", _("User defined hidden"))
	])
	config.usage.pluginListLayout = ConfigSelection(default="gridmode", choices=[
		("gridmode", _("Grid mode")),
		("listmode", _("List mode"))
	])
	if MODEL.startswith("bey"):
		config.usage.show_genre_info = ConfigYesNo(default=True)
	else:
		config.usage.show_genre_info = ConfigYesNo(default=False)
	config.usage.menu_show_numbers = ConfigYesNo(default=False)
	config.usage.showScreenPath = ConfigSelection(default="small", choices=[
		("off", _("Disabled")),
		("small", _("Small")),
		("large", _("Large"))
	])
	config.usage.enable_tt_caching = ConfigYesNo(default=False)

	config.usage.tuxtxt_font_and_res = ConfigSelection(default="TTF_SD", choices=[
		("X11_SD", _("Fixed X11 font (SD)")),
		("TTF_SD", _("TrueType font (SD)")),
		("TTF_HD", _("TrueType font (HD)")),
		("TTF_FHD", _("TrueType font (Full-HD)")),
		("expert_mode", _("Expert mode"))
	])
	config.usage.tuxtxt_UseTTF = ConfigSelection(default="1", choices=[
		("0", _("0")),
		("1", _("1"))
	])
	config.usage.tuxtxt_TTFBold = ConfigSelection(default="1", choices=[
		("0", _("0")),
		("1", _("1"))
	])
	config.usage.tuxtxt_TTFScreenResX = ConfigSelection(default="720", choices=[
		("720", _("720")),
		("1280", _("1280")),
		("1920", _("1920"))
	])
	config.usage.tuxtxt_StartX = ConfigInteger(default=50, limits=(0, 200))
	config.usage.tuxtxt_EndX = ConfigInteger(default=670, limits=(500, 1920))
	config.usage.tuxtxt_StartY = ConfigInteger(default=30, limits=(0, 200))
	config.usage.tuxtxt_EndY = ConfigInteger(default=555, limits=(400, 1080))
	config.usage.tuxtxt_TTFShiftY = ConfigSelection(default="2", choices=[
		("-9", _("-9")),
		("-8", _("-8")),
		("-7", _("-7")),
		("-6", _("-6")),
		("-5", _("-5")),
		("-4", _("-4")),
		("-3", _("-3")),
		("-2", _("-2")),
		("-1", _("-1")),
		("0", _("0")),
		("1", _("1")),
		("2", _("2")),
		("3", _("3")),
		("4", _("4")),
		("5", _("5")),
		("6", _("6")),
		("7", _("7")),
		("8", _("8")),
		("9", _("9"))
	])
	config.usage.tuxtxt_TTFShiftX = ConfigSelection(default="0", choices=[
		("-9", _("-9")),
		("-8", _("-8")),
		("-7", _("-7")),
		("-6", _("-6")),
		("-5", _("-5")),
		("-4", _("-4")),
		("-3", _("-3")),
		("-2", _("-2")),
		("-1", _("-1")),
		("0", _("0")),
		("1", _("1")),
		("2", _("2")),
		("3", _("3")),
		("4", _("4")),
		("5", _("5")),
		("6", _("6")),
		("7", _("7")),
		("8", _("8")),
		("9", _("9"))
	])
	config.usage.tuxtxt_TTFWidthFactor16 = ConfigInteger(default=29, limits=(8, 31))
	config.usage.tuxtxt_TTFHeightFactor16 = ConfigInteger(default=14, limits=(8, 31))
	config.usage.tuxtxt_CleanAlgo = ConfigInteger(default=0, limits=(0, 9))
	config.usage.tuxtxt_ConfFileHasBeenPatched = NoSave(ConfigYesNo(default=False))

	config.usage.tuxtxt_font_and_res.addNotifier(patchTuxtxtConfFile, initial_call=False, immediate_feedback=False)
	config.usage.tuxtxt_UseTTF.addNotifier(patchTuxtxtConfFile, initial_call=False, immediate_feedback=False)
	config.usage.tuxtxt_TTFBold.addNotifier(patchTuxtxtConfFile, initial_call=False, immediate_feedback=False)
	config.usage.tuxtxt_TTFScreenResX.addNotifier(patchTuxtxtConfFile, initial_call=False, immediate_feedback=False)
	config.usage.tuxtxt_StartX.addNotifier(patchTuxtxtConfFile, initial_call=False, immediate_feedback=False)
	config.usage.tuxtxt_EndX.addNotifier(patchTuxtxtConfFile, initial_call=False, immediate_feedback=False)
	config.usage.tuxtxt_StartY.addNotifier(patchTuxtxtConfFile, initial_call=False, immediate_feedback=False)
	config.usage.tuxtxt_EndY.addNotifier(patchTuxtxtConfFile, initial_call=False, immediate_feedback=False)
	config.usage.tuxtxt_TTFShiftY.addNotifier(patchTuxtxtConfFile, initial_call=False, immediate_feedback=False)
	config.usage.tuxtxt_TTFShiftX.addNotifier(patchTuxtxtConfFile, initial_call=False, immediate_feedback=False)
	config.usage.tuxtxt_TTFWidthFactor16.addNotifier(patchTuxtxtConfFile, initial_call=False, immediate_feedback=False)
	config.usage.tuxtxt_TTFHeightFactor16.addNotifier(patchTuxtxtConfFile, initial_call=False, immediate_feedback=False)
	config.usage.tuxtxt_CleanAlgo.addNotifier(patchTuxtxtConfFile, initial_call=False, immediate_feedback=False)

	config.usage.sort_settings = ConfigYesNo(default=False)
	choicelist = []
	for i in (10, 30):
		choicelist.append((str(i), ngettext("%d second", "%d seconds", i) % i))
	for i in (60, 120, 300, 600, 1200, 1800):
		m = i / 60
		choicelist.append((str(i), ngettext("%d minute", "%d minutes", m) % m))
	for i in (3600, 7200, 14400):
		h = i / 3600
		choicelist.append((str(i), ngettext("%d hour", "%d hours", h) % h))
	config.usage.hdd_standby = ConfigSelection(default="300", choices=[("0", _("No standby"))] + choicelist)
	config.usage.output_12V = ConfigSelection(default="do not change", choices=[
		("do not change", _("Do not change")),
		("off", _("Off")),
		("on", _("On"))
	])

	config.usage.pip_zero_button = ConfigSelection(default="standard", choices=[
		("standard", _("Standard")),
		("swap", _("Swap PiP and main picture")),
		("swapstop", _("Move PiP to main picture")),
		("stop", _("Stop PiP"))
	])
	config.usage.pip_hideOnExit = ConfigSelection(default="without popup", choices=[
		("no", _("No")),
		("popup", _("With popup")),
		("without popup", _("Without popup"))
	])
	choicelist = [
		("-1", _("Disabled")),
		("0", _("No timeout"))
	]
	for i in [60, 300, 600, 900, 1800, 2700, 3600]:
		m = i / 60
		choicelist.append((str(i), ngettext("%d minute", "%d minutes", m) % m))
	config.usage.pip_last_service_timeout = ConfigSelection(default="0", choices=choicelist)
	moviesPath = ""
	timeshiftPath = ""
	for partition in harddiskmanager.getMountedPartitions():
		directories = normpath(partition.mountpoint)
		if directories != "/" and ismount(str(directories)) and not exists(str(directories + "/movie")):
			makedirs(directories + "/movie")
		if directories != "/" and "movie" in directories:
			moviesPath = join(directories + "/")
		for timeshiftpath in [f"/media/{media}/timeshift" for media in listdir("/media/") if ismount(join("/media/", media))]:
			if exists(str(timeshiftpath)):
				if not exists(str(timeshiftpath + "/recordings")):
					makedirs(timeshiftpath + "/recordings")
				timeshiftPath = timeshiftpath + "/recordings/"
				break
	defaultValue = moviesPath if moviesPath and "/net/movie" not in moviesPath or moviesPath and "/autofs/movie" not in moviesPath else resolveFilename(SCOPE_HDD)
	config.usage.default_path = ConfigSelection(default=defaultValue, choices=[(defaultValue, defaultValue)])
	config.usage.default_path.load()
	if config.usage.default_path.saved_value:
		savedValue = join(config.usage.default_path.saved_value, "")
		if savedValue and savedValue != defaultValue:
			config.usage.default_path.setChoices([(defaultValue, defaultValue), (savedValue, savedValue)], default=defaultValue)
			config.usage.default_path.value = savedValue
	choiceList = [("<default>", "<default>"), ("<current>", "<current>"), ("<timer>", "<timer>")]
	config.usage.timer_path = ConfigSelection(default="<default>", choices=choiceList)
	config.usage.timer_path.load()
	if config.usage.timer_path.saved_value:
		savedValue = config.usage.timer_path.saved_value if config.usage.timer_path.saved_value.startswith("<") else join(config.usage.timer_path.saved_value, "")
		if savedValue and savedValue not in choiceList:
			config.usage.timer_path.setChoices(choiceList + [(savedValue, savedValue)], default="<default>")
			config.usage.timer_path.value = savedValue
	config.usage.instantrec_path = ConfigSelection(default="<default>", choices=choiceList)
	config.usage.instantrec_path.load()
	if config.usage.instantrec_path.saved_value:
		savedValue = config.usage.instantrec_path.saved_value if config.usage.instantrec_path.saved_value.startswith("<") else join(config.usage.instantrec_path.saved_value, "")
		if savedValue and savedValue not in choiceList:
			config.usage.instantrec_path.setChoices(choiceList + [(savedValue, savedValue)], default="<default>")
			config.usage.instantrec_path.value = savedValue
	defaultValue = timeshiftPath if timeshiftPath else resolveFilename(SCOPE_TIMESHIFT)
	config.usage.timeshift_path = ConfigSelection(default=defaultValue, choices=[(defaultValue, defaultValue)])
	config.usage.timeshift_path.load()
	if config.usage.timeshift_path.saved_value:
		savedValue = join(config.usage.timeshift_path.saved_value, "")
		if savedValue and savedValue != defaultValue:
			config.usage.timeshift_path.setChoices([(defaultValue, defaultValue), (savedValue, savedValue)], default=defaultValue)
			config.usage.timeshift_path.value = savedValue
	config.usage.allowed_timeshift_paths = ConfigLocations(default=[resolveFilename(SCOPE_TIMESHIFT)])
	config.usage.timeshift_skipreturntolive = ConfigYesNo(default=False)

	def setTimeshiftPath(configElement):
		config.usage.timeshift_path.value = configElement.value
		eSettings.setTimeshiftPath(configElement.value)

	config.usage.timeshift_path.addNotifier(setTimeshiftPath)

	config.usage.trashsort_deltime = ConfigSelection(default="no", choices=[
		("no", _("No")),
		("show record time", _("Yes, show record time")),
		("show delete time", _("Yes, show delete time"))])
	config.usage.movielist_trashcan = ConfigYesNo(default=True)
	config.usage.movielist_trashcan_network_clean = ConfigYesNo(default=False)

	config.usage.movielist_trashcan_days = ConfigSelectionNumber(min=0, max=31, stepwidth=1, default=8, wraparound=True)
	config.usage.movielist_trashcan_reserve = ConfigNumber(default=40)
	config.usage.on_movie_start = ConfigSelection(default="ask yes", choices=[
		("ask yes", _("Ask user (with default as 'Yes')")),
		("ask no", _("Ask user (with default as 'No')")),
		("resume", _("Resume from last position")),
		("beginning", _("Start from the beginning"))
	])
	config.usage.on_movie_stop = ConfigSelection(default="movielist", choices=[
		("ask", _("Ask user")),
		("movielist", _("Return to movie list")),
		("quit", _("Return to previous service"))
	])
	config.usage.on_movie_eof = ConfigSelection(default="quit", choices=[
		("ask", _("Ask user")),
		("movielist", _("Return to movie list")),
		("quit", _("Return to previous service")),
		("pause", _("Pause movie at end")),
		("playlist", _("Play next in movie list")),
		("loop", _("Continues play (loop)")),
		("repeatcurrent", _("Repeat"))
	])
	config.usage.next_movie_msg = ConfigYesNo(default=True)
	config.usage.last_movie_played = ConfigText()
	config.usage.leave_movieplayer_onExit = ConfigSelection(default="popup", choices=[
		("no", _("No")),
		("popup", _("With popup")),
		("without popup", _("Without popup"))
	])

	config.usage.setup_level = ConfigSelection(default="expert", choices=[
		("simple", _("Normal")),
		("intermediate", _("Advanced")),
		("expert", _("Expert"))
	])

	config.usage.setupShowDefault = ConfigSelection(default="newline", choices=[
		("", _("Don't show default")),
		("spaces", _("Show default after description")),
		("newline", _("Show default on new line"))
	])

	config.usage.helpSortOrder = ConfigSelection(default="headings+alphabetic", choices=[
		("headings+alphabetic", _("Alphabetical under headings")),
		("flat+alphabetic", _("Flat alphabetical")),
		("flat+remotepos", _("Flat by position on remote")),
		("flat+remotegroups", _("Flat by key group on remote"))
	])

	config.usage.helpAnimationSpeed = ConfigSelection(default="10", choices=[
		("1", _("Very fast")),
		("5", _("Fast")),
		("10", _("Default")),
		("20", _("Slow")),
		("50", _("Very slow"))
	])

	config.usage.startup_to_standby = ConfigSelection(default="no", choices=[
		("no", _("No")),
		("yes", _("Yes")),
		("except", _("No, except with wake up timer"))
	])

	config.usage.wakeup_enabled = ConfigSelection(default="no", choices=[
		("no", _("No")),
		("yes", _("Yes")),
		("standby", _("Yes, only from standby")),
		("deepstandby", _("Yes, only from deep standby"))
	])
	config.usage.wakeup_day = ConfigSubDict()
	config.usage.wakeup_time = ConfigSubDict()
	for i in range(7):
		config.usage.wakeup_day[i] = ConfigEnableDisable(default=False)
		config.usage.wakeup_time[i] = ConfigClock(default=((6 * 60 + 0) * 60))

	choicelist = [("0", _("Do nothing"))]
	for i in range(3600, 21601, 3600):
		h = abs(i / 3600)
		choicelist.append((str(i), _("Standby in %s") % (ngettext("%d hour", "%d hours", h) % h)))
	config.usage.inactivity_timer = ConfigSelection(default="0", choices=choicelist)
	config.usage.inactivity_timer_blocktime = ConfigYesNo(default=True)
	config.usage.inactivity_timer_blocktime_begin = ConfigClock(default=mktime((1970, 1, 1, 18, 0, 0, 0, 0, 0)))
	config.usage.inactivity_timer_blocktime_end = ConfigClock(default=mktime((1970, 1, 1, 23, 0, 0, 0, 0, 0)))
	config.usage.inactivity_timer_blocktime_extra = ConfigYesNo(default=False)
	config.usage.inactivity_timer_blocktime_extra_begin = ConfigClock(default=mktime((1970, 1, 1, 6, 0, 0, 0, 0, 0)))
	config.usage.inactivity_timer_blocktime_extra_end = ConfigClock(default=mktime((1970, 1, 1, 9, 0, 0, 0, 0, 0)))
	config.usage.inactivity_timer_blocktime_by_weekdays = ConfigYesNo(default=False)
	config.usage.inactivity_timer_blocktime_day = ConfigSubDict()
	config.usage.inactivity_timer_blocktime_begin_day = ConfigSubDict()
	config.usage.inactivity_timer_blocktime_end_day = ConfigSubDict()
	config.usage.inactivity_timer_blocktime_extra_day = ConfigSubDict()
	config.usage.inactivity_timer_blocktime_extra_begin_day = ConfigSubDict()
	config.usage.inactivity_timer_blocktime_extra_end_day = ConfigSubDict()
	for i in range(7):
		config.usage.inactivity_timer_blocktime_day[i] = ConfigYesNo(default=False)
		config.usage.inactivity_timer_blocktime_begin_day[i] = ConfigClock(default=mktime((1970, 1, 1, 18, 0, 0, 0, 0, 0)))
		config.usage.inactivity_timer_blocktime_end_day[i] = ConfigClock(default=mktime((1970, 1, 1, 23, 0, 0, 0, 0, 0)))
		config.usage.inactivity_timer_blocktime_extra_day[i] = ConfigYesNo(default=False)
		config.usage.inactivity_timer_blocktime_extra_begin_day[i] = ConfigClock(default=mktime((1970, 1, 1, 6, 0, 0, 0, 0, 0)))
		config.usage.inactivity_timer_blocktime_extra_end_day[i] = ConfigClock(default=mktime((1970, 1, 1, 9, 0, 0, 0, 0, 0)))

	choicelist = [
		("0", _("Disabled")),
		("event_standby", _("Standby after current event"))
	]
	for i in range(900, 7201, 900):
		m = abs(i / 60)
		choicelist.append((str(i), _("Standby in %s") % (ngettext("%d minute", "%d minutes", m) % m)))
	config.usage.sleep_timer = ConfigSelection(default="0", choices=choicelist)

	choicelist = [("0", _("Disabled"))]
	for i in [300, 600] + list(range(900, 14401, 900)):
		m = abs(i / 60)
		choicelist.append((str(i), _("After %s") % (ngettext("%d minute", "%d minutes", m) % m)))
	config.usage.standby_to_shutdown_timer = ConfigSelection(default="0", choices=choicelist)
	config.usage.standby_to_shutdown_timer_blocktime = ConfigYesNo(default=False)
	config.usage.standby_to_shutdown_timer_blocktime_begin = ConfigClock(default=mktime((1970, 1, 1, 6, 0, 0, 0, 0, 0)))
	config.usage.standby_to_shutdown_timer_blocktime_end = ConfigClock(default=mktime((1970, 1, 1, 23, 0, 0, 0, 0, 0)))

	def setLongPressedEmulationKey(configElement):
		eActionMap.getInstance().setLongPressedEmulationKey(configElement.value)

	config.usage.long_press_emulation_key = ConfigSelection(default=0, choices=[
		(0, _("None")),
		(KEYIDS["KEY_AUDIO"], "AUDIO"),
		(KEYIDS["KEY_END"], "END"),
		(KEYIDS["KEY_EPG"], "EPG"),
		(KEYIDS["KEY_FAVORITES"], "FAV"),
		(KEYIDS["KEY_HELP"], "HELP"),
		(KEYIDS["KEY_HOME"], "HOME"),
		(KEYIDS["KEY_INFO"], "INFO"),
		(KEYIDS["KEY_LIST"], "LIST"),
		(KEYIDS["KEY_RADIO"], "RADIO"),
		(KEYIDS["KEY_SUBTITLE"], "SUBTITLE"),
		(KEYIDS["KEY_TEXT"], "TEXT"),
		(KEYIDS["KEY_TV"], "TV"),
		(KEYIDS["KEY_VIDEO"], "MEDIA")
	])
	config.usage.long_press_emulation_key.addNotifier(setLongPressedEmulationKey)

	choicelist = [("0", _("Disabled"))]
	for m in (1, 5, 10, 15, 30, 60):
		choicelist.append((str(m * 60), ngettext("%d minute", "%d minutes", m) % m))
	config.usage.screen_saver = ConfigSelection(default="300", choices=choicelist)

	config.usage.check_timeshift = ConfigYesNo(default=True)

	choicelist = [("0", _("Disabled"))]
	for i in (2, 3, 4, 5, 10, 20, 30):
		choicelist.append((str(i), ngettext("%d second", "%d seconds", i) % i))
	for i in (60, 120, 300):
		m = i / 60
		choicelist.append((str(i), ngettext("%d minute", "%d minutes", m) % m))
	config.usage.timeshift_start_delay = ConfigSelection(default="0", choices=choicelist)

	config.usage.alternatives_priority = ConfigSelection(default="1", choices=[
		("0", _("DVB-S/-C/-T")),
		("1", _("DVB-S/-T/-C")),
		("2", _("DVB-C/-S/-T")),
		("3", _("DVB-C/-T/-S")),
		("4", _("DVB-T/-C/-S")),
		("5", _("DVB-T/-S/-C")),
		("127", _("No priority"))
	])

	def setHttpStartDelay(configElement):
		eSettings.setHttpStartDelay(configElement.value)

	choicelist = [(0, _("Disabled"))]
	for i in (10, 50, 100, 500, 1000, 2000):
		choicelist.append((i, _("%d ms") % i))

	config.usage.http_startdelay = ConfigSelection(default=0, choices=choicelist)
	config.usage.http_startdelay.addNotifier(setHttpStartDelay)

	def remote_fallback_changed(configElement):
		if configElement.value:
			configElement.value = "%s%s" % (not configElement.value.startswith("http://") and "http://" or "", configElement.value)
			configElement.value = "%s%s" % (configElement.value, configElement.value.count(":") == 1 and ":8001" or "")

	def setRemoteFallbackEnabled(configElement):
		eSettings.setRemoteFallbackEnabled(configElement.value)

	config.usage.remote_fallback_enabled = ConfigYesNo(default=False)
	config.usage.remote_fallback_enabled.addNotifier(setRemoteFallbackEnabled)
	config.usage.remote_fallback = ConfigText(default="", fixed_size=False)
	config.usage.remote_fallback.addNotifier(remote_fallback_changed, immediate_feedback=False)
	config.usage.remote_fallback_import_url = ConfigText(default="", fixed_size=False)
	config.usage.remote_fallback_import_url.addNotifier(remote_fallback_changed, immediate_feedback=False)
	config.usage.remote_fallback_alternative = ConfigYesNo(default=False)
	config.usage.remote_fallback_dvb_t = ConfigText(default="", fixed_size=False)
	config.usage.remote_fallback_dvb_t.addNotifier(remote_fallback_changed, immediate_feedback=False)
	config.usage.remote_fallback_dvb_c = ConfigText(default="", fixed_size=False)
	config.usage.remote_fallback_dvb_c.addNotifier(remote_fallback_changed, immediate_feedback=False)
	config.usage.remote_fallback_atsc = ConfigText(default="", fixed_size=False)
	config.usage.remote_fallback_atsc.addNotifier(remote_fallback_changed, immediate_feedback=False)
	config.usage.remote_fallback_import = ConfigSelection(default="", choices=[
		("", _("No")),
		("channels", _("Channels only")),
		("channels_epg", _("Channels and EPG")),
		("epg", _("EPG only"))
	])
	config.usage.remote_fallback_import_restart = ConfigYesNo(default=False)
	config.usage.remote_fallback_import_standby = ConfigYesNo(default=False)
	config.usage.remote_fallback_ok = ConfigYesNo(default=False)
	config.usage.remote_fallback_nok = ConfigYesNo(default=False)
	config.usage.remote_fallback_extension_menu = ConfigYesNo(default=False)
	config.usage.remote_fallback_external_timer = ConfigYesNo(default=False)
	config.usage.remote_fallback_openwebif_customize = ConfigYesNo(default=False)
	config.usage.remote_fallback_openwebif_userid = ConfigText(default="root")
	config.usage.remote_fallback_openwebif_password = ConfigPassword(default="default")
	config.usage.remote_fallback_openwebif_port = ConfigInteger(default=80, limits=(0, 65535))
	config.usage.remote_fallback_dvbt_region = ConfigText(default="fallback DVB-T/T2 Europe")

	config.usage.show_timer_conflict_warning = ConfigYesNo(default=True)

	preferredTunerChoicesUpdate()

	config.usage.menutype = ConfigSelection(default="standard", choices=[
		("horzanim", _("Horizontal menu")),
		("horzicon", _("Horizontal icons")),
		("standard", _("Standard menu"))
	])

	config.misc.disable_background_scan = ConfigYesNo(default=False)

	def setUseCIAssignment(configElement):
		eSettings.setUseCIAssignment(configElement.value)

	config.misc.use_ci_assignment = ConfigYesNo(default=True)
	config.misc.use_ci_assignment.addNotifier(setUseCIAssignment)

	config.usage.show_event_progress_in_servicelist = ConfigSelection(default="percright", choices=[
		("barleft", _("Progress bar left")),
		("barright", _("Progress bar right")),
		("percleft", _("Percentage left")),
		("percright", _("Percentage right")),
		("no", _("No"))
	])
	config.usage.show_channel_numbers_in_servicelist = ConfigYesNo(default=True)
	config.usage.show_event_progress_in_servicelist.addNotifier(refreshServiceList)
	config.usage.show_channel_numbers_in_servicelist.addNotifier(refreshServiceList)

	if SystemInfo["7segment"]:
		config.usage.blinking_in_standby_during_recording = ConfigSelection(default="Rec", choices=[
			("Rec", _("REC")),
			("RecBlink", _("Blinking REC")),
			("Time", _("Time")),
			("Nothing", _("Nothing"))
		])
		config.usage.blinking_rec_symbol_during_recording = ConfigSelection(default="Rec", choices=[
			("Rec", _("REC")),
			("RecBlink", _("Blinking REC")),
			("Time", _("Time"))
		])
	else:
		# blink for displaytext not in 7segment
		if SystemInfo["textlcd"]:
			config.usage.blinking_rec_symbol_during_recording = ConfigSelection(default="Channel", choices=[
				("Rec", _("REC symbol")),
				("RecBlink", _("Blinking REC symbol")),
				("Channel", _("Channel name"))
			])
		else:
			config.usage.blinking_in_standby_during_recording = ConfigYesNo(default=False)
			config.usage.blinking_rec_symbol_during_recording = ConfigYesNo(default=True)

	# show/hide time in display in standby
	config.usage.show_in_standby = ConfigSelection(default="time", choices=[
		("time", _("Time")),
		("nothing", _("Nothing"))
	])

	config.usage.show_message_when_recording_starts = ConfigYesNo(default=True)

	config.usage.load_length_of_movies_in_moviellist = ConfigYesNo(default=True)
	config.usage.show_icons_in_movielist = ConfigSelection(default="i", choices=[
		("o", _("Off")),
		("p", _("Progress")),
		("s", _("Small progress")),
		("i", _("Icons"))
	])
	config.usage.movielist_unseen = ConfigYesNo(default=True)
	config.usage.movielist_servicename_mode = ConfigSelection(default="", choices=[
		("", _("None")),
		("picon", _("Picon"))
	])
	config.usage.movielist_piconwidth = ConfigSelectionNumber(default=100, stepwidth=1, min=50, max=500, wraparound=True)

	config.usage.swap_snr_on_osd = ConfigYesNo(default=False)
	config.usage.swap_time_display_on_osd = ConfigSelection(default="0", choices=[
		("0", _("Skin setting")),
		("1", _("Mins")),
		("2", _("Mins Secs")),
		("3", _("Hours Mins")),
		("4", _("Hours Mins Secs")),
		("5", _("Percentage"))
	])
	config.usage.swap_media_time_display_on_osd = ConfigSelection(default="0", choices=[
		("0", _("Skin setting")),
		("1", _("Mins")),
		("2", _("Mins Secs")),
		("3", _("Hours Mins")),
		("4", _("Hours Mins Secs")),
		("5", _("Percentage"))
	])
	config.usage.swap_time_remaining_on_osd = ConfigSelection(default="0", choices=[
		("0", _("Remaining")),
		("1", _("Elapsed")),
		("2", _("Elapsed & Remaining")),
		("3", _("Remaining & Elapsed"))
	])
	config.usage.elapsed_time_positive_osd = ConfigYesNo(default=False)
	config.usage.swap_time_display_on_vfd = ConfigSelection(default="0", choices=[
		("0", _("Skin setting")),
		("1", _("Mins")),
		("2", _("Mins Secs")),
		("3", _("Hours Mins")),
		("4", _("Hours Mins Secs")),
		("5", _("Percentage"))
	])
	config.usage.swap_media_time_display_on_vfd = ConfigSelection(default="0", choices=[
		("0", _("Skin setting")),
		("1", _("Mins")),
		("2", _("Mins Secs")),
		("3", _("Hours Mins")),
		("4", _("Hours Mins Secs")),
		("5", _("Percentage"))
	])
	config.usage.swap_time_remaining_on_vfd = ConfigSelection(default="0", choices=[
		("0", _("Remaining")),
		("1", _("Elapsed")),
		("2", _("Elapsed & Remaining")),
		("3", _("Remaining & Elapsed"))
	])
	config.usage.elapsed_time_positive_vfd = ConfigYesNo(default=False)

	config.usage.frontled_color = ConfigSelection(default="1", choices=[
		("0", _("Off")),
		("1", _("Blue")),
		("2", _("Red")),
		("3", _("Blinking blue")),
		("4", _("Blinking red"))
	])
	config.usage.frontledrec_color = ConfigSelection(default="4", choices=[
		("0", _("Off")),
		("1", _("Blue")),
		("2", _("Red")),
		("3", _("Blinking blue")),
		("4", _("Blinking red"))
	])
	config.usage.frontledstdby_color = ConfigSelection(default="2", choices=[
		("0", _("Off")),
		("1", _("Blue")),
		("2", _("Red")),
		("3", _("Blinking Violet")),
		("4", _("Blinking red"))
	])
	config.usage.frontledrecstdby_color = ConfigSelection(default="4", choices=[
		("0", _("Off")),
		("1", _("Blue")),
		("2", _("Red")),
		("3", _("Blinking blue")),
		("4", _("Blinking red"))
	])

	config.usage.lcd_scroll_delay = ConfigSelection(default="10000", choices=[
		("10000", _("%d seconds") % 10),
		("20000", _("%d seconds") % 20),
		("30000", _("%d seconds") % 30),
		("60000", _("%d minute") % 1),
		("300000", _("%d minutes") % 5),
		("noscrolling", _("Off"))
	])
	config.usage.lcd_scroll_speed = ConfigSelection(default="300", choices=[
		("500", _("Slow")),
		("300", _("Normal")),
		("100", _("Fast"))
	])

	def SpinnerOnOffChanged(configElement):
		setSpinnerOnOff(int(configElement.value))
	config.usage.show_spinner.addNotifier(SpinnerOnOffChanged)

	def EnableTtCachingChanged(configElement):
		setEnableTtCachingOnOff(int(configElement.value))
	config.usage.enable_tt_caching.addNotifier(EnableTtCachingChanged)

	def TunerTypePriorityOrderChanged(configElement):
		setTunerTypePriorityOrder(int(configElement.value))
	config.usage.alternatives_priority.addNotifier(TunerTypePriorityOrderChanged, immediate_feedback=False)

	def PreferredTunerChanged(configElement):
		setPreferredTuner(int(configElement.value))
	config.usage.frontend_priority.addNotifier(PreferredTunerChanged)

	config.skin.onlyicon = NoSave(ConfigBoolean(default=False))

	try:
		onlyIcon = parameters.get("AllowUseOnlyIcon", (0))
	except Exception as error:
		print("[UsageConfig] Error loading 'AllowUseOnlyIcon' skin parameter! (%s)" % error)
		onlyIcon = (0)
	if onlyIcon:
		config.skin.onlyicon.value = True
	else:
		config.skin.onlyicon.value = False

	config.usage.show_picon_in_display = ConfigYesNo(default=True)
	config.usage.hide_zap_errors = ConfigYesNo(default=False)
	config.usage.show_cryptoinfo = ConfigYesNo(default=True)
	config.usage.show_vcr_scart = ConfigYesNo(default=False)
	config.usage.show_update_disclaimer = ConfigYesNo(default=True)
	config.usage.pic_resolution = ConfigSelection(default=None, choices=[
		(None, _("Same resolution as skin")),
		("(720, 576)", _("720x576")),
		("(1280, 720)", _("1280x720")),
		("(1920, 1080)", _("1920x1080"))
	][:SystemInfo["HasFullHDSkinSupport"] and 4 or 3])

	config.usage.date = ConfigSubsection()
	config.usage.date.enabled = NoSave(ConfigBoolean(default=False))
	config.usage.date.enabled_display = NoSave(ConfigBoolean(default=False))
	config.usage.time = ConfigSubsection()
	config.usage.time.enabled = NoSave(ConfigBoolean(default=False))
	config.usage.time.disabled = NoSave(ConfigBoolean(default=True))
	config.usage.time.enabled_display = NoSave(ConfigBoolean(default=False))
	config.usage.time.wide = NoSave(ConfigBoolean(default=False))
	config.usage.time.wide_display = NoSave(ConfigBoolean(default=False))

	# TRANSLATORS: full date representation dayname daynum monthname year in strftime() format! See "man strftime"
	config.usage.date.dayfull = ConfigSelection(default=_("%A %-d %B %Y"), choices=[
		(_("%A %d %B %Y"), _("Dayname DD Month Year")),
		(_("%A %d. %B %Y"), _("Dayname DD. Month Year")),
		(_("%A %-d %B %Y"), _("Dayname D Month Year")),
		(_("%A %-d. %B %Y"), _("Dayname D. Month Year")),
		(_("%A %d-%B-%Y"), _("Dayname DD-Month-Year")),
		(_("%A %-d-%B-%Y"), _("Dayname D-Month-Year")),
		(_("%A %d/%m/%Y"), _("Dayname DD/MM/Year")),
		(_("%A %d.%m.%Y"), _("Dayname DD.MM.Year")),
		(_("%A %-d/%m/%Y"), _("Dayname D/MM/Year")),
		(_("%A %-d.%m.%Y"), _("Dayname D.MM.Year")),
		(_("%A %d/%-m/%Y"), _("Dayname DD/M/Year")),
		(_("%A %d.%-m.%Y"), _("Dayname DD.M.Year")),
		(_("%A %-d/%-m/%Y"), _("Dayname D/M/Year")),
		(_("%A %-d.%-m.%Y"), _("Dayname D.M.Year")),
		(_("%A %B %d %Y"), _("Dayname Month DD Year")),
		(_("%A %B %-d %Y"), _("Dayname Month D Year")),
		(_("%A %B-%d-%Y"), _("Dayname Month-DD-Year")),
		(_("%A %B-%-d-%Y"), _("Dayname Month-D-Year")),
		(_("%A %m/%d/%Y"), _("Dayname MM/DD/Year")),
		(_("%A %-m/%d/%Y"), _("Dayname M/DD/Year")),
		(_("%A %m/%-d/%Y"), _("Dayname MM/D/Year")),
		(_("%A %-m/%-d/%Y"), _("Dayname M/D/Year")),
		(_("%A %Y %B %d"), _("Dayname Year Month DD")),
		(_("%A %Y %B %-d"), _("Dayname Year Month D")),
		(_("%A %Y-%B-%d"), _("Dayname Year-Month-DD")),
		(_("%A %Y-%B-%-d"), _("Dayname Year-Month-D")),
		(_("%A %Y/%m/%d"), _("Dayname Year/MM/DD")),
		(_("%A %Y/%m/%-d"), _("Dayname Year/MM/D")),
		(_("%A %Y/%-m/%d"), _("Dayname Year/M/DD")),
		(_("%A %Y/%-m/%-d"), _("Dayname Year/M/D"))
	])

	# TRANSLATORS: long date representation short dayname daynum monthname year in strftime() format! See "man strftime"
	config.usage.date.shortdayfull = ConfigText(default=_("%a %-d %B %Y"))

	# TRANSLATORS: long date representation short dayname daynum short monthname year in strftime() format! See "man strftime"
	config.usage.date.daylong = ConfigText(default=_("%a %-d %b %Y"))

	# TRANSLATORS: short date representation dayname daynum short monthname in strftime() format! See "man strftime"
	config.usage.date.dayshortfull = ConfigText(default=_("%A %-d %B"))

	# TRANSLATORS: short date representation short dayname daynum short monthname in strftime() format! See "man strftime"
	config.usage.date.dayshort = ConfigText(default=_("%a %-d %b"))

	# TRANSLATORS: small date representation short dayname daynum in strftime() format! See "man strftime"
	config.usage.date.daysmall = ConfigText(default=_("%a %-d"))

	# TRANSLATORS: full date representation daynum monthname year in strftime() format! See "man strftime"
	config.usage.date.full = ConfigText(default=_("%-d %B %Y"))

	# TRANSLATORS: long date representation daynum short monthname year in strftime() format! See "man strftime"
	config.usage.date.long = ConfigText(default=_("%-d %b %Y"))

	# TRANSLATORS: small date representation daynum short monthname in strftime() format! See "man strftime"
	config.usage.date.short = ConfigText(default=_("%-d %b"))

	def setDateStyles(configElement):
		dateStyles = {
			# dayfull: (shortdayfull, daylong, dayshortfull, dayshort, daysmall, full, long, short)
			_("%A %d %B %Y"): (_("%a %d %B %Y"), _("%a %d %b %Y"), _("%A %d %B"), _("%a %d %b"), _("%a %d"), _("%d %B %Y"), _("%d %b %Y"), _("%d %b")),
			_("%A %d. %B %Y"): (_("%a %d. %B %Y"), _("%a %d. %b %Y"), _("%A %d. %B"), _("%a %d. %b"), _("%a %d"), _("%d. %B %Y"), _("%d. %b %Y"), _("%d. %b")),
			_("%A %-d %B %Y"): (_("%a %-d %B %Y"), _("%a %-d %b %Y"), _("%A %-d %B"), _("%a %-d %b"), _("%a %-d"), _("%-d %B %Y"), _("%-d %b %Y"), _("%-d %b")),
			_("%A %-d. %B %Y"): (_("%a %-d. %B %Y"), _("%a %-d. %b %Y"), _("%A %-d. %B"), _("%a %-d. %b"), _("%a %-d"), _("%-d. %B %Y"), _("%-d. %b %Y"), _("%-d. %b")),
			_("%A %d-%B-%Y"): (_("%a %d-%B-%Y"), _("%a %d-%b-%Y"), _("%A %d-%B"), _("%a %d-%b"), _("%a %d"), _("%d-%B-%Y"), _("%d-%b-%Y"), _("%d-%b")),
			_("%A %-d-%B-%Y"): (_("%a %-d-%B-%Y"), _("%a %-d-%b-%Y"), _("%A %-d-%B"), _("%a %-d-%b"), _("%a %-d"), _("%-d-%B-%Y"), _("%-d-%b-%Y"), _("%-d-%b")),
			_("%A %d/%m/%Y"): (_("%a %d/%m/%Y"), _("%a %d/%m/%Y"), _("%A %d/%m"), _("%a %d/%m"), _("%a %d"), _("%d/%m/%Y"), _("%d/%m/%Y"), _("%d/%m")),
			_("%A %d.%m.%Y"): (_("%a %d.%m.%Y"), _("%a %d.%m.%Y"), _("%A %d.%m"), _("%a %d.%m"), _("%a %d"), _("%d.%m.%Y"), _("%d.%m.%Y"), _("%d.%m")),
			_("%A %-d/%m/%Y"): (_("%a %-d/%m/%Y"), _("%a %-d/%m/%Y"), _("%A %-d/%m"), _("%a %-d/%m"), _("%a %-d"), _("%-d/%m/%Y"), _("%-d/%m/%Y"), _("%-d/%m")),
			_("%A %-d.%m.%Y"): (_("%a %-d.%m.%Y"), _("%a %-d.%m.%Y"), _("%A %-d.%m"), _("%a %-d.%m"), _("%a %-d"), _("%-d.%m.%Y"), _("%-d.%m.%Y"), _("%-d.%m")),
			_("%A %d/%-m/%Y"): (_("%a %d/%-m/%Y"), _("%a %d/%-m/%Y"), _("%A %d/%-m"), _("%a %d/%-m"), _("%a %d"), _("%d/%-m/%Y"), _("%d/%-m/%Y"), _("%d/%-m")),
			_("%A %d.%-m.%Y"): (_("%a %d.%-m.%Y"), _("%a %d.%-m.%Y"), _("%A %d.%-m"), _("%a %d.%-m"), _("%a %d"), _("%d.%-m.%Y"), _("%d.%-m.%Y"), _("%d.%-m")),
			_("%A %-d/%-m/%Y"): (_("%a %-d/%-m/%Y"), _("%a %-d/%-m/%Y"), _("%A %-d/%-m"), _("%a %-d/%-m"), _("%a %-d"), _("%-d/%-m/%Y"), _("%-d/%-m/%Y"), _("%-d/%-m")),
			_("%A %-d.%-m.%Y"): (_("%a %-d.%-m.%Y"), _("%a %-d.%-m.%Y"), _("%A %-d.%-m"), _("%a %-d.%-m"), _("%a %-d"), _("%-d.%-m.%Y"), _("%-d.%-m.%Y"), _("%-d.%-m")),
			_("%A %B %d %Y"): (_("%a %B %d %Y"), _("%a %b %d %Y"), _("%A %B %d"), _("%a %b %d"), _("%a %d"), _("%B %d %Y"), _("%b %d %Y"), _("%b %d")),
			_("%A %B %-d %Y"): (_("%a %B %-d %Y"), _("%a %b %-d %Y"), _("%A %B %-d"), _("%a %b %-d"), _("%a %-d"), _("%B %-d %Y"), _("%b %-d %Y"), _("%b %-d")),
			_("%A %B-%d-%Y"): (_("%a %B-%d-%Y"), _("%a %b-%d-%Y"), _("%A %B-%d"), _("%a %b-%d"), _("%a %d"), _("%B-%d-%Y"), _("%b-%d-%Y"), _("%b-%d")),
			_("%A %B-%-d-%Y"): (_("%a %B-%-d-%Y"), _("%a %b-%-d-%Y"), _("%A %B-%-d"), _("%a %b-%-d"), _("%a %-d"), _("%B-%-d-%Y"), _("%b-%-d-%Y"), _("%b-%-d")),
			_("%A %m/%d/%Y"): (_("%a %m/%d/%Y"), _("%a %m/%d/%Y"), _("%A %m/%d"), _("%a %m/%d"), _("%a %d"), _("%m/%d/%Y"), _("%m/%d/%Y"), _("%m/%d")),
			_("%A %-m/%d/%Y"): (_("%a %-m/%d/%Y"), _("%a %-m/%d/%Y"), _("%A %-m/%d"), _("%a %-m/%d"), _("%a %d"), _("%-m/%d/%Y"), _("%-m/%d/%Y"), _("%-m/%d")),
			_("%A %m/%-d/%Y"): (_("%a %m/%-d/%Y"), _("%a %m/%-d/%Y"), _("%A %m/%-d"), _("%a %m/%-d"), _("%a %-d"), _("%m/%-d/%Y"), _("%m/%-d/%Y"), _("%m/%-d")),
			_("%A %-m/%-d/%Y"): (_("%a %-m/%-d/%Y"), _("%a %-m/%-d/%Y"), _("%A %-m/%-d"), _("%a %-m/%-d"), _("%a %-d"), _("%-m/%-d/%Y"), _("%-m/%-d/%Y"), _("%-m/%-d")),
			_("%A %Y %B %d"): (_("%a %Y %B %d"), _("%a %Y %b %d"), _("%A %B %d"), _("%a %b %d"), _("%a %d"), _("%Y %B %d"), _("%Y %b %d"), _("%b %d")),
			_("%A %Y %B %-d"): (_("%a %Y %B %-d"), _("%a %Y %b %-d"), _("%A %B %-d"), _("%a %b %-d"), _("%a %-d"), _("%Y %B %-d"), _("%Y %b %-d"), _("%b %-d")),
			_("%A %Y-%B-%d"): (_("%a %Y-%B-%d"), _("%a %Y-%b-%d"), _("%A %B-%d"), _("%a %b-%d"), _("%a %d"), _("%Y-%B-%d"), _("%Y-%b-%d"), _("%b-%d")),
			_("%A %Y-%B-%-d"): (_("%a %Y-%B-%-d"), _("%a %Y-%b-%-d"), _("%A %B-%-d"), _("%a %b-%-d"), _("%a %-d"), _("%Y-%B-%-d"), _("%Y-%b-%-d"), _("%b-%-d")),
			_("%A %Y/%m/%d"): (_("%a %Y/%m/%d"), _("%a %Y/%m/%d"), _("%A %m/%d"), _("%a %m/%d"), _("%a %d"), _("%Y/%m/%d"), _("%Y/%m/%d"), _("%m/%d")),
			_("%A %Y/%m/%-d"): (_("%a %Y/%m/%-d"), _("%a %Y/%m/%-d"), _("%A %m/%-d"), _("%a %m/%-d"), _("%a %-d"), _("%Y/%m/%-d"), _("%Y/%m/%-d"), _("%m/%-d")),
			_("%A %Y/%-m/%d"): (_("%a %Y/%-m/%d"), _("%a %Y/%-m/%d"), _("%A %-m/%d"), _("%a %-m/%d"), _("%a %d"), _("%Y/%-m/%d"), _("%Y/%-m/%d"), _("%-m/%d")),
			_("%A %Y/%-m/%-d"): (_("%a %Y/%-m/%-d"), _("%a %Y/%-m/%-d"), _("%A %-m/%-d"), _("%a %-m/%-d"), _("%a %-d"), _("%Y/%-m/%-d"), _("%Y/%-m/%-d"), _("%-m/%-d"))
		}
		style = dateStyles.get(configElement.value, ((_("Invalid")) * 8))
		config.usage.date.shortdayfull.value = style[0]
		config.usage.date.shortdayfull.save()
		config.usage.date.daylong.value = style[1]
		config.usage.date.daylong.save()
		config.usage.date.dayshortfull.value = style[2]
		config.usage.date.dayshortfull.save()
		config.usage.date.dayshort.value = style[3]
		config.usage.date.dayshort.save()
		config.usage.date.daysmall.value = style[4]
		config.usage.date.daysmall.save()
		config.usage.date.full.value = style[5]
		config.usage.date.full.save()
		config.usage.date.long.value = style[6]
		config.usage.date.long.save()
		config.usage.date.short.value = style[7]
		config.usage.date.short.save()

	config.usage.date.dayfull.addNotifier(setDateStyles)

	# TRANSLATORS: full time representation hour:minute:seconds
	if nl_langinfo(AM_STR) and nl_langinfo(PM_STR):
		config.usage.time.long = ConfigSelection(default=_("%T"), choices=[
			(_("%T"), _("HH:mm:ss")),
			(_("%-H:%M:%S"), _("H:mm:ss")),
			(_("%I:%M:%S%^p"), _("hh:mm:ssAM/PM")),
			(_("%-I:%M:%S%^p"), _("h:mm:ssAM/PM")),
			(_("%I:%M:%S%P"), _("hh:mm:ssam/pm")),
			(_("%-I:%M:%S%P"), _("h:mm:ssam/pm")),
			(_("%I:%M:%S"), _("hh:mm:ss")),
			(_("%-I:%M:%S"), _("h:mm:ss"))
		])
	else:
		config.usage.time.long = ConfigSelection(default=_("%T"), choices=[
			(_("%T"), _("HH:mm:ss")),
			(_("%-H:%M:%S"), _("H:mm:ss")),
			(_("%I:%M:%S"), _("hh:mm:ss")),
			(_("%-I:%M:%S"), _("h:mm:ss"))
		])

	# TRANSLATORS: time representation hour:minute:seconds for 24 hour clock or 12 hour clock without AM/PM and hour:minute for 12 hour clocks with AM/PM
	config.usage.time.mixed = ConfigText(default=_("%T"))

	# TRANSLATORS: short time representation hour:minute (Same as "Default")
	config.usage.time.short = ConfigText(default=_("%R"))

	def setTimeStyles(configElement):
		timeStyles = {
			# long: (mixed, short)
			_("%T"): (_("%T"), _("%R")),
			_("%-H:%M:%S"): (_("%-H:%M:%S"), _("%-H:%M")),
			_("%I:%M:%S%^p"): (_("%I:%M%^p"), _("%I:%M%^p")),
			_("%-I:%M:%S%^p"): (_("%-I:%M%^p"), _("%-I:%M%^p")),
			_("%I:%M:%S%P"): (_("%I:%M%P"), _("%I:%M%P")),
			_("%-I:%M:%S%P"): (_("%-I:%M%P"), _("%-I:%M%P")),
			_("%I:%M:%S"): (_("%I:%M:%S"), _("%I:%M")),
			_("%-I:%M:%S"): (_("%-I:%M:%S"), _("%-I:%M"))
		}
		style = timeStyles.get(configElement.value, ((_("Invalid")) * 2))
		config.usage.time.mixed.value = style[0]
		config.usage.time.mixed.save()
		config.usage.time.short.value = style[1]
		config.usage.time.short.save()
		config.usage.time.wide.value = style[1].endswith(("P", "p"))

	config.usage.time.long.addNotifier(setTimeStyles)

	try:
		dateEnabled, timeEnabled = parameters.get("AllowUserDatesAndTimes", (1, 1))
	except Exception as error:
		print("[UsageConfig] Error loading 'AllowUserDatesAndTimes' skin parameter! (%s)" % error)
		dateEnabled, timeEnabled = (0, 0)
	if dateEnabled:
		config.usage.date.enabled.value = True
	else:
		config.usage.date.enabled.value = False
		config.usage.date.dayfull.value = config.usage.date.dayfull.default
	if timeEnabled:
		config.usage.time.enabled.value = True
		config.usage.time.disabled.value = not config.usage.time.enabled.value
	else:
		config.usage.time.enabled.value = False
		config.usage.time.disabled.value = not config.usage.time.enabled.value
		config.usage.time.long.value = config.usage.time.long.default

	# TRANSLATORS: compact date representation (for VFD) daynum short monthname in strftime() format! See "man strftime"
	config.usage.date.display = ConfigSelection(default=_("%-d %b"), choices=[
		("", _("Hidden / Blank")),
		(_("%d %b"), _("Day DD Mon")),
		(_("%-d %b"), _("Day D Mon")),
		(_("%d-%b"), _("Day DD-Mon")),
		(_("%-d-%b"), _("Day D-Mon")),
		(_("%d/%m"), _("Day DD/MM")),
		(_("%-d/%m"), _("Day D/MM")),
		(_("%d/%-m"), _("Day DD/M")),
		(_("%-d/%-m"), _("Day D/M")),
		(_("%b %d"), _("Day Mon DD")),
		(_("%b %-d"), _("Day Mon D")),
		(_("%b-%d"), _("Day Mon-DD")),
		(_("%b-%-d"), _("Day Mon-D")),
		(_("%m/%d"), _("Day MM/DD")),
		(_("%m/%-d"), _("Day MM/D")),
		(_("%-m/%d"), _("Day M/DD")),
		(_("%-m/%-d"), _("Day M/D"))
	])

	config.usage.date.displayday = ConfigText(default=_("%a %-d+%b_"))
	config.usage.date.display_template = ConfigText(default=_("%-d+%b_"))
	config.usage.date.compact = ConfigText(default=_("%-d+%b_"))
	config.usage.date.compressed = ConfigText(default=_("%-d+%b_"))

	timeDisplayValue = [_("%R")]

	def adjustDisplayDates():
		if timeDisplayValue[0] == "":
			if config.usage.date.display.value == "":  # If the date and time are both hidden output a space to blank the VFD display.
				config.usage.date.compact.value = " "
				config.usage.date.compressed.value = " "
			else:
				config.usage.date.compact.value = config.usage.date.displayday.value
				config.usage.date.compressed.value = config.usage.date.displayday.value
		else:
			if config.usage.time.wide_display.value:
				config.usage.date.compact.value = config.usage.date.display_template.value.replace("_", "").replace("=", "").replace("+", "")
				config.usage.date.compressed.value = config.usage.date.display_template.value.replace("_", "").replace("=", "").replace("+", "")
			else:
				config.usage.date.compact.value = config.usage.date.display_template.value.replace("_", " ").replace("=", "-").replace("+", " ")
				config.usage.date.compressed.value = config.usage.date.display_template.value.replace("_", " ").replace("=", "").replace("+", "")
		config.usage.date.compact.save()
		config.usage.date.compressed.save()

	def setDateDisplayStyles(configElement):
		dateDisplayStyles = {
			# display: (displayday, template)
			"": ("", ""),
			_("%d %b"): (_("%a %d %b"), _("%d+%b_")),
			_("%-d %b"): (_("%a %-d %b"), _("%-d+%b_")),
			_("%d-%b"): (_("%a %d-%b"), _("%d=%b_")),
			_("%-d-%b"): (_("%a %-d-%b"), _("%-d=%b_")),
			_("%d/%m"): (_("%a %d/%m"), _("%d/%m ")),
			_("%-d/%m"): (_("%a %-d/%m"), _("%-d/%m ")),
			_("%d/%-m"): (_("%a %d/%-m"), _("%d/%-m ")),
			_("%-d/%-m"): (_("%a %-d/%-m"), _("%-d/%-m ")),
			_("%b %d"): (_("%a %b %d"), _("%b+%d ")),
			_("%b %-d"): (_("%a %b %-d"), _("%b+%-d ")),
			_("%b-%d"): (_("%a %b-%d"), _("%b=%d ")),
			_("%b-%-d"): (_("%a %b-%-d"), _("%b=%-d ")),
			_("%m/%d"): (_("%a %m/%d"), _("%m/%d ")),
			_("%m/%-d"): (_("%a %m/%-d"), _("%m/%-d ")),
			_("%-m/%d"): (_("%a %-m/%d"), _("%-m/%d ")),
			_("%-m/%-d"): (_("%a %-m/%-d"), _("%-m/%-d "))
		}
		style = dateDisplayStyles.get(configElement.value, ((_("Invalid")) * 2))
		config.usage.date.displayday.value = style[0]
		config.usage.date.displayday.save()
		config.usage.date.display_template.value = style[1]
		config.usage.date.display_template.save()
		adjustDisplayDates()

	config.usage.date.display.addNotifier(setDateDisplayStyles)

	# TRANSLATORS: short time representation hour:minute (Same as "Default")
	if nl_langinfo(AM_STR) and nl_langinfo(PM_STR):
		config.usage.time.display = ConfigSelection(default=_("%R"), choices=[
			("", _("Hidden / Blank")),
			(_("%R"), _("HH:mm")),
			(_("%-H:%M"), _("H:mm")),
			(_("%I:%M%^p"), _("hh:mmAM/PM")),
			(_("%-I:%M%^p"), _("h:mmAM/PM")),
			(_("%I:%M%P"), _("hh:mmam/pm")),
			(_("%-I:%M%P"), _("h:mmam/pm")),
			(_("%I:%M"), _("hh:mm")),
			(_("%-I:%M"), _("h:mm"))
		])
	else:
		config.usage.time.display = ConfigSelection(default=_("%R"), choices=[
			("", _("Hidden / Blank")),
			(_("%R"), _("HH:mm")),
			(_("%-H:%M"), _("H:mm")),
			(_("%I:%M"), _("hh:mm")),
			(_("%-I:%M"), _("h:mm"))
		])

	def setTimeDisplayStyles(configElement):
		timeDisplayValue[0] = config.usage.time.display.value
		config.usage.time.wide_display.value = configElement.value.endswith(("P", "p"))
		adjustDisplayDates()

	config.usage.time.display.addNotifier(setTimeDisplayStyles)

	try:
		dateDisplayEnabled, timeDisplayEnabled = parameters.get("AllowUserDatesAndTimesDisplay", (0, 0))
	except Exception as error:
		print("[UsageConfig] Error loading 'AllowUserDatesAndTimesDisplay' display skin parameter! (%s)" % error)
		dateDisplayEnabled, timeDisplayEnabled = (0, 0)
	if dateDisplayEnabled:
		config.usage.date.enabled_display.value = True
	else:
		config.usage.date.enabled_display.value = False
		config.usage.date.display.value = config.usage.date.display.default
	if timeDisplayEnabled:
		config.usage.time.enabled_display.value = True
	else:
		config.usage.time.enabled_display.value = False
		config.usage.time.display.value = config.usage.time.display.default

	if SystemInfo["Fan"]:
		choicelist = [
			("off", _("Off")),
			("on", _("On")),
			("auto", _("Auto"))
		]
		if exists("/proc/stb/fp/fan_choices"):
			print("[UsageConfig] Read /proc/stb/fp/fan_choices")
			choicelist = [x for x in choicelist if x[0] in open("/proc/stb/fp/fan_choices", "r").read().strip().split(" ")]
		config.usage.fan = ConfigSelection(choicelist)

		def fanChanged(configElement):
			open(SystemInfo["Fan"], "w").write(configElement.value)
		config.usage.fan.addNotifier(fanChanged)

	if SystemInfo["FanPWM"]:
		def fanSpeedChanged(configElement):
			open(SystemInfo["FanPWM"], "w").write(hex(configElement.value)[2:])
		config.usage.fanspeed = ConfigSlider(default=127, increment=8, limits=(0, 255))
		config.usage.fanspeed.addNotifier(fanSpeedChanged)

	config.network = ConfigSubsection()
	if BoxInfo.getItem("WakeOnLAN"):
		def wakeOnLANChanged(configElement):
			fileWriteLine(BoxInfo.getItem("WakeOnLAN"), BoxInfo.getItem("WakeOnLANType")[configElement.value], source=MODULE_NAME)
		config.network.wol = ConfigYesNo(default=False)
		config.network.wol.addNotifier(wakeOnLANChanged)
	config.usage.boolean_graphic = ConfigYesNo(default=True)
	config.usage.show_slider_value = ConfigYesNo(default=True)
	config.usage.cursorscroll = ConfigSelectionNumber(min=0, max=50, stepwidth=5, default=0, wraparound=True)

	config.usage.multiboot_order = ConfigYesNo(default=True)

	config.crash = ConfigSubsection()

	config.usage.show_eit_nownext = ConfigYesNo(default=True)

	config.epg = ConfigSubsection()
	config.epg.eit = ConfigYesNo(default=True)
	config.epg.mhw = ConfigYesNo(default=False)
	config.epg.freesat = ConfigYesNo(default=False)
	config.epg.viasat = ConfigYesNo(default=False)
	config.epg.netmed = ConfigYesNo(default=False)
	config.epg.virgin = ConfigYesNo(default=False)
	config.epg.opentv = ConfigYesNo(default=False)
	config.epg.saveepg = ConfigYesNo(default=True)

	config.epg.maxdays = ConfigSelectionNumber(min=1, max=365, stepwidth=1, default=7, wraparound=True)

	def showEPGChanged(configElement):
		from enigma import eEPGCache
		eEPGCache.getInstance().setSave(configElement.value)

	config.epg.saveepg.addNotifier(showEPGChanged, immediate_feedback=False, initial_call=False)

	def EpgmaxdaysChanged(configElement):
		from enigma import eEPGCache
		eEPGCache.getInstance().setEpgmaxdays(config.epg.maxdays.getValue())
	config.epg.maxdays.addNotifier(EpgmaxdaysChanged)

	if MODEL.startswith("bey"):
		config.misc.epgratingcountry = ConfigSelection(default="AUS", choices=[
			("", _("Auto detect")),
			("ETSI", _("Generic")),
			("AUS", _("Australia"))
		])
		config.misc.epggenrecountry = ConfigSelection(default="AUS", choices=[
			("", _("Auto detect")),
			("ETSI", _("Generic")),
			("AUS", _("Australia"))
		])
	else:
		config.misc.epgratingcountry = ConfigSelection(default="", choices=[
			("", _("Auto detect")),
			("ETSI", _("Generic")),
			("AUS", _("Australia"))
		])
		config.misc.epggenrecountry = ConfigSelection(default="", choices=[
			("", _("Auto detect")),
			("ETSI", _("Generic")),
			("AUS", _("Australia"))
		])

	def EpgSettingsChanged(configElement):
		mask = 0xffffffff
		if not config.epg.eit.value:
			mask &= ~(eEPGCache.NOWNEXT | eEPGCache.SCHEDULE | eEPGCache.SCHEDULE_OTHER)
		if not config.epg.mhw.value:
			mask &= ~eEPGCache.MHW
		if not config.epg.freesat.value:
			mask &= ~(eEPGCache.FREESAT_NOWNEXT | eEPGCache.FREESAT_SCHEDULE | eEPGCache.FREESAT_SCHEDULE_OTHER)
		if not config.epg.viasat.value:
			mask &= ~eEPGCache.VIASAT
		if not config.epg.netmed.value:
			mask &= ~(eEPGCache.NETMED_SCHEDULE | eEPGCache.NETMED_SCHEDULE_OTHER)
		if not config.epg.virgin.value:
			mask &= ~(eEPGCache.VIRGIN_NOWNEXT | eEPGCache.VIRGIN_SCHEDULE)
		if not config.epg.opentv.value:
			mask &= ~eEPGCache.OPENTV
		eEPGCache.getInstance().setEpgSources(mask)
	config.epg.eit.addNotifier(EpgSettingsChanged, initial_call=False)
	config.epg.mhw.addNotifier(EpgSettingsChanged, initial_call=False)
	config.epg.freesat.addNotifier(EpgSettingsChanged, initial_call=False)
	config.epg.viasat.addNotifier(EpgSettingsChanged, initial_call=False)
	config.epg.netmed.addNotifier(EpgSettingsChanged, initial_call=False)
	config.epg.virgin.addNotifier(EpgSettingsChanged, initial_call=False)
	config.epg.opentv.addNotifier(EpgSettingsChanged)

	config.epg.histminutes = ConfigSelectionNumber(min=0, max=120, stepwidth=15, default=0, wraparound=True)

	def EpgHistorySecondsChanged(configElement):
		from enigma import eEPGCache
		eEPGCache.getInstance().setEpgHistorySeconds(config.epg.histminutes.getValue() * 60)
	config.epg.histminutes.addNotifier(EpgHistorySecondsChanged)

	choicelist = [("newline", _("new line")), ("2newlines", _("2 new lines")), ("space", _("space")), ("dot", " . "), ("dash", " - "), ("asterisk", " * "), ("nothing", _("nothing"))]
	config.epg.fulldescription_separator = ConfigSelection(default="nothing", choices=choicelist)
	choicelist = [("no", _("no")), ("nothing", _("omit")), ("space", _("space")), ("dot", ". "), ("dash", " - "), ("asterisk", " * "), ("hashtag", " # ")]
	config.epg.replace_newlines = ConfigSelection(default="space", choices=choicelist)
	config.crash.debugEPG = ConfigYesNo(default=False)
	config.epg.cacheloadsched = ConfigYesNo(default=False)
	config.epg.cachesavesched = ConfigYesNo(default=False)

	def EpgCacheLoadSchedChanged(configElement):
		from Components import EpgLoadSave
		EpgLoadSave.EpgCacheLoadCheck()

	def EpgCacheSaveSchedChanged(configElement):
		from Components import EpgLoadSave
		EpgLoadSave.EpgCacheSaveCheck()
	config.epg.cacheloadsched.addNotifier(EpgCacheLoadSchedChanged, immediate_feedback=False)
	config.epg.cachesavesched.addNotifier(EpgCacheSaveSchedChanged, immediate_feedback=False)
	config.epg.cacheloadtimer = ConfigSelectionNumber(default=24, stepwidth=1, min=1, max=24, wraparound=True)
	config.epg.cachesavetimer = ConfigSelectionNumber(default=24, stepwidth=1, min=1, max=24, wraparound=True)

	def debugEPGhanged(configElement):
		from enigma import eEPGCache
		eEPGCache.getInstance().setDebug(configElement.value)

	config.crash.debugEPG.addNotifier(debugEPGhanged, immediate_feedback=False, initial_call=False)

	hddchoises = [("/etc/enigma2/", "Internal Flash")]
	for p in harddiskmanager.getMountedPartitions():
		if exists(p.mountpoint):
			d = normpath(p.mountpoint)
			if p.mountpoint != "/":
				hddchoises.append((p.mountpoint, d))
	config.misc.epgcachepath = ConfigSelection(default=resolveFilename(SCOPE_CONFIG), choices=hddchoises)
	config.misc.epgcachefilename = ConfigText(default="epg", fixed_size=False)
	config.misc.epgcache_filename = ConfigText(default=join(config.misc.epgcachepath.value, config.misc.epgcachefilename.value + ".dat"))

	def EpgCacheChanged(configElement):
		config.misc.epgcache_filename.setValue(join(config.misc.epgcachepath.value, config.misc.epgcachefilename.value + ".dat"))
		config.misc.epgcache_filename.save()
		eEPGCache.getInstance().setCacheFile(config.misc.epgcache_filename.value)
		epgcache = eEPGCache.getInstance()
		epgcache.save()
		for partition in harddiskmanager.getMountedPartitions():  # ckeck epg.dat file
			path = normpath(partition.mountpoint)
			cacheFileName = config.misc.epgcachefilename.value + ".dat"
			if not config.misc.firstrun.value:
				try:
					if resolveFilename(SCOPE_CONFIG) not in config.misc.epgcache_filename.value + ".dat":  # delete internal flash
						if exists(join(resolveFilename(SCOPE_CONFIG, cacheFileName))):
							remove(join(resolveFilename(SCOPE_CONFIG, cacheFileName)))
						if path not in config.misc.epgcache_filename.value + ".dat":  # delete on all devices with no value in config
							if exists(join(path, cacheFileName)):
								remove(join(path, cacheFileName))
					else:  # delete in all devices except internal flash
						if exists(join(path, cacheFileName)):
							remove(join(path, cacheFileName))
				except:
					pass

	config.misc.epgcachepath.addNotifier(EpgCacheChanged, immediate_feedback=False)
	config.misc.epgcachefilename.addNotifier(EpgCacheChanged, immediate_feedback=False)

	config.misc.epgratingcountry = ConfigSelection(default="", choices=[
		("", _("Auto detect")),
		("ETSI", _("Generic")),
		("AUS", _("Australia"))
	])
	config.misc.epggenrecountry = ConfigSelection(default="", choices=[
		("", _("Auto detect")),
		("ETSI", _("Generic")),
		("AUS", _("Australia"))
	])

	config.misc.showradiopic = ConfigYesNo(default=True)

	def setHDDStandby(configElement):
		for hdd in harddiskmanager.HDDList():
			hdd[1].setIdleTime(int(configElement.value))
	config.usage.hdd_standby.addNotifier(setHDDStandby, immediate_feedback=False)

	if SystemInfo["12V_Output"]:
		def set12VOutput(configElement):
			Misc_Options.getInstance().set_12V_output(configElement.value == "on" and 1 or 0)
		config.usage.output_12V.addNotifier(set12VOutput, immediate_feedback=False)

	config.usage.keymap = ConfigText(default=eEnv.resolve("${datadir}/enigma2/keymap.xml"))
	config.usage.alternative_imagefeed = ConfigText(default="", fixed_size=False)
	config.misc.actionLeftRightToPageUpPageDown = ConfigYesNo(default=True)

	config.crash.debugDVBScan = ConfigYesNo(default=False)
	config.crash.coredump = ConfigYesNo(default=False)

	def updateStackTracePrinter(configElement):
		from Components.StackTrace import StackTracePrinter
		if configElement.value:
			if isfile("/tmp/doPythonStackTrace"):
				remove("/tmp/doPythonStackTrace")
			from threading import current_thread
			StackTracePrinter.getInstance().activate(current_thread().ident)
		else:
			StackTracePrinter.getInstance().deactivate()

	config.crash.pythonStackOnSpinner = ConfigYesNo(default=False)
	config.crash.pythonStackOnSpinner.addNotifier(updateStackTracePrinter, immediate_feedback=False, initial_call=True)
	config.crash.debugLevel = ConfigSelection(choices=[
		("3", _("No debug logs")),
		("4", _("Basic debug logs")),
		("5", _("Detailed debug logs"))
	], default="3")
	config.crash.debugLevel.save_forced = True
	# The config.crash.debugTimeFormat item is used to set ENIGMA_DEBUG_TIME environmental variable on enigma2 start from enigma2.sh.
	config.crash.debugTimeFormat = ConfigSelection(choices=[
		("0", _("None")),
		("1", _("Boot time")),
		("2", _("Local time")),
		("3", _("Boot time and local time")),
		("6", _("Local date/time")),
		("7", _("Boot time and local data/time"))
	], default="1")
	config.crash.debugTimeFormat.save_forced = True
	debugPath = [
		("/home/root/logs/", "/home/root/logs/")
	]
	for partition in harddiskmanager.getMountedPartitions():
		if exists(partition.mountpoint):
			path = normpath(partition.mountpoint)
			if partition.mountpoint != "/":
				folderunzipped = path + "/*/*.unzipped"
				for folders in glob(folderunzipped, recursive=True):
					if exists(folders):
						Console().ePopen('rm -rf ' + folders)
					break
				debugPath.append((join(partition.mountpoint, "logs", ""), path + "/logs/"))
	config.crash.debugPath = ConfigSelection(default="/home/root/logs/", choices=debugPath)

	def updateDebugPath(configElement):
		if not exists(config.crash.debugPath.value):
			makedirs(config.crash.debugPath.value, 0o755)

	config.crash.debugPath.addNotifier(updateDebugPath, immediate_feedback=False)
	config.crash.debugFileCount = ConfigSelectionNumber(min=2, max=5, stepwidth=1, default=2, wraparound=True)
	config.crash.daysloglimit = ConfigSelectionNumber(min=1, max=30, stepwidth=1, default=2, wraparound=True)
	config.crash.sizeloglimit = ConfigSelectionNumber(min=1, max=250, stepwidth=1, default=5, wraparound=True)
	config.crash.debugFileCount.save_forced = True

	config.logmanager = ConfigSubsection()
	config.logmanager.showinextensions = ConfigYesNo(default=False)
	config.logmanager.path = ConfigText(default="/")
	config.logmanager.sentfiles = ConfigLocations(default="")

	config.seek = ConfigSubsection()
	config.seek.selfdefined_13 = ConfigNumber(default=15)
	config.seek.selfdefined_46 = ConfigNumber(default=60)
	config.seek.selfdefined_79 = ConfigNumber(default=300)

	config.seek.speeds_forward = ConfigSet(default=[2, 4, 8, 16, 32, 64, 128], choices=[2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128])
	config.seek.speeds_backward = ConfigSet(default=[2, 4, 8, 16, 32, 64, 128], choices=[1, 2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128])
	config.seek.speeds_slowmotion = ConfigSet(default=[2, 4, 8], choices=[2, 4, 6, 8, 12, 16, 25])

	config.seek.enter_forward = ConfigSelection(default=2, choices=[2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128])
	config.seek.enter_backward = ConfigSelection(default=1, choices=[1, 2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128])

	config.seek.on_pause = ConfigSelection(default="play", choices=[
		("play", _("Play")),
		("step", _("Single step (GOP)")),
		("last", _("Last speed"))])

	config.usage.timerlist_finished_timer_position = ConfigSelection(default="end", choices=[
		("beginning", _("At beginning")),
		("end", _("At end"))
	])

	def updateEnterForward(configElement):
		if not configElement.value:
			configElement.value = [2]
		updateChoices(config.seek.enter_forward, configElement.value)

	config.seek.speeds_forward.addNotifier(updateEnterForward, immediate_feedback=False)

	def updateEnterBackward(configElement):
		if not configElement.value:
			configElement.value = [2]
		updateChoices(config.seek.enter_backward, configElement.value)

	config.seek.speeds_backward.addNotifier(updateEnterBackward, immediate_feedback=False)

	def updateEraseSpeed(el):
		eBackgroundFileEraser.getInstance().setEraseSpeed(int(el.value))

	def updateEraseFlags(el):
		eBackgroundFileEraser.getInstance().setEraseFlags(int(el.value))
	config.misc.erase_speed = ConfigSelection(default="20", choices=[
		("10", _("10 MB/s")),
		("20", _("20 MB/s")),
		("50", _("50 MB/s")),
		("100", _("100 MB/s"))])
	config.misc.erase_speed.addNotifier(updateEraseSpeed, immediate_feedback=False)
	config.misc.erase_flags = ConfigSelection(default="1", choices=[
		("0", _("Disable")),
		("1", _("Internal hdd only")),
		("3", _("Everywhere"))])
	config.misc.erase_flags.addNotifier(updateEraseFlags, immediate_feedback=False)

	config.misc.zapkey_delay = ConfigSelectionNumber(default=5, stepwidth=1, min=0, max=20, wraparound=True)
	config.misc.numzap_picon = ConfigYesNo(default=False)

	if SystemInfo["ZapMode"]:
		def setZapmode(el):
			open(SystemInfo["ZapMode"], "w").write(el.value)
		config.misc.zapmode = ConfigSelection(default="mute", choices=[
			("mute", _("Black screen")),
			("hold", _("Hold screen")),
			("mutetilllock", _("Black screen till locked")),
			("holdtilllock", _("Hold till locked"))
		])
		config.misc.zapmode.addNotifier(setZapmode, immediate_feedback=False)

	config.subtitles = ConfigSubsection()
	config.subtitles.show = ConfigYesNo(default=True)

	def setTTXSubtitleColors(configElement):
		eSubtitleSettings.setTTXSubtitleColors(configElement.value)

	config.subtitles.ttx_subtitle_colors = ConfigSelection(default=1, choices=[
		(0, _("Original")),
		(1, _("White")),
		(2, _("Yellow"))
	])
	config.subtitles.ttx_subtitle_colors.addNotifier(setTTXSubtitleColors)

	def setTTXSubtitleOriginalPosition(configElement):
		eSubtitleSettings.setTTXSubtitleOriginalPosition(configElement.value)

	config.subtitles.ttx_subtitle_original_position = ConfigYesNo(default=False)
	config.subtitles.ttx_subtitle_original_position.addNotifier(setTTXSubtitleOriginalPosition)

	def setSubtitlePosition(configElement):
		eSubtitleSettings.setSubtitlePosition(configElement.value)

	config.subtitles.subtitle_position = ConfigSelection(default=50, choices=[(x, _("%d Pixels") % x) for x in list(range(0, 91, 10)) + list(range(100, 451, 50))])
	config.subtitles.subtitle_position.addNotifier(setSubtitlePosition)

	def setSubtitleAligment(configElement):
		aligments = {
			"left": 1,
			"center": 4,
			"right": 2
		}
		eSubtitleSettings.setSubtitleAligment(aligments.get(configElement.value, 4))

	config.subtitles.subtitle_alignment = ConfigSelection(default="center", choices=[
		("left", _("Left")),
		("center", _("Center")),
		("right", _("Right"))
	])
	config.subtitles.subtitle_alignment.addNotifier(setSubtitleAligment)

	def setSubtitleReWrap(configElement):
		eSubtitleSettings.setSubtitleReWrap(configElement.value)

	config.subtitles.subtitle_rewrap = ConfigYesNo(default=False)
	config.subtitles.subtitle_rewrap.addNotifier(setSubtitleReWrap)

	def setSubtitleColoriseDialogs(configElement):
		eSubtitleSettings.setSubtitleColoriseDialogs(configElement.value)

	config.subtitles.colourise_dialogs = ConfigYesNo(default=False)
	config.subtitles.colourise_dialogs.addNotifier(setSubtitleColoriseDialogs)

	def setSubtitleBorderWith(configElement):
		eSubtitleSettings.setSubtitleBorderWith(configElement.value)

	config.subtitles.subtitle_borderwidth = ConfigSelection(default=3, choices=[(x, str(x)) for x in range(1, 6)])
	config.subtitles.subtitle_borderwidth.addNotifier(setSubtitleBorderWith)

	def setSubtitleFontSize(configElement):
		eSubtitleSettings.setSubtitleFontSize(configElement.value)

	config.subtitles.subtitle_fontsize = ConfigSelection(default=40, choices=[(x, str(x)) for x in range(16, 101) if not x % 2])
	config.subtitles.subtitle_fontsize.addNotifier(setSubtitleFontSize)

	def setSubtitleBacktrans(configElement):
		eSubtitleSettings.setSubtitleBacktrans(configElement.value)

	choiceList = [
		(0, _("No transparency")),
		(12, "5%"),
		(25, "10%"),
		(38, "15%"),
		(50, "20%"),
		(75, "30%"),
		(100, "40%"),
		(125, "50%"),
		(150, "60%"),
		(175, "70%"),
		(200, "80%"),
		(225, "90%"),
		(255, _("Full transparency"))]
	config.subtitles.subtitles_backtrans = ConfigSelection(default=255, choices=choiceList)
	config.subtitles.subtitles_backtrans.addNotifier(setSubtitleBacktrans)

	def setDVBSubtitleBacktrans(configElement):
		eSubtitleSettings.setDVBSubtitleBacktrans(configElement.value)

	config.subtitles.dvb_subtitles_backtrans = ConfigSelection(default=0, choices=choiceList)
	config.subtitles.dvb_subtitles_backtrans.addNotifier(setDVBSubtitleBacktrans)

	choiceList = []
	for x in range(-54000000, 54045000, 45000):
		if x == 0:
			choiceList.append((0, _("No delay")))
		else:
			choiceList.append((x, _("%2.1f Seconds") % (x / 90000.0)))

	def setSubtitleNoPTSDelay(configElement):
		eSubtitleSettings.setSubtitleNoPTSDelay(configElement.value)

	config.subtitles.subtitle_noPTSrecordingdelay = ConfigSelection(default=315000, choices=choiceList)
	config.subtitles.subtitle_noPTSrecordingdelay.addNotifier(setSubtitleNoPTSDelay)

	def setSubtitleBadTimingDelay(configElement):
		eSubtitleSettings.setSubtitleBadTimingDelay(configElement.value)

	config.subtitles.subtitle_bad_timing_delay = ConfigSelection(default=0, choices=choiceList)
	config.subtitles.subtitle_bad_timing_delay.addNotifier(setSubtitleBadTimingDelay)

	def setPangoSubtitleDelay(configElement):
		eSubtitleSettings.setPangoSubtitleDelay(configElement.value)

	config.subtitles.pango_subtitles_delay = ConfigSelection(default=0, choices=choiceList)
	config.subtitles.pango_subtitles_delay.addNotifier(setPangoSubtitleDelay)

	def setDVBSubtitleYellow(configElement):
		eSubtitleSettings.setDVBSubtitleYellow(configElement.value)

	config.subtitles.dvb_subtitles_yellow = ConfigYesNo(default=False)
	config.subtitles.dvb_subtitles_yellow.addNotifier(setDVBSubtitleYellow)

	def setDVBSubtitleOriginalPosition(configElement):
		eSubtitleSettings.setDVBSubtitleOriginalPosition(configElement.value)

	config.subtitles.dvb_subtitles_original_position = ConfigSelection(default=0, choices=[
		(0, _("Original")),
		(1, _("Fixed")),
		(2, _("Relative"))
	])
	config.subtitles.dvb_subtitles_original_position.addNotifier(setDVBSubtitleOriginalPosition)

	def setDVBSubtitleCentered(configElement):
		eSubtitleSettings.setDVBSubtitleCentered(configElement.value)

	config.subtitles.dvb_subtitles_centered = ConfigYesNo(default=False)
	config.subtitles.dvb_subtitles_centered.addNotifier(setDVBSubtitleCentered)

	def setPangoSubtitleColors(configElement):
		eSubtitleSettings.setPangoSubtitleColors(configElement.value)

	config.subtitles.pango_subtitle_colors = ConfigSelection(default=1, choices=[
		(0, _("Alternative")),
		(1, _("White")),
		(2, _("Yellow"))
	])
	config.subtitles.pango_subtitle_colors.addNotifier(setPangoSubtitleColors)

	def setPangoSubtitleFontWitch(configElement):
		eSubtitleSettings.setPangoSubtitleFontWitch(configElement.value)

	config.subtitles.pango_subtitle_fontswitch = ConfigYesNo(default=True)
	config.subtitles.pango_subtitle_fontswitch.addNotifier(setPangoSubtitleFontWitch)

	def setPangoSubtitleFPS(configElement):
		eSubtitleSettings.setPangoSubtitleFPS(configElement.value)

	config.subtitles.pango_subtitles_fps = ConfigSelection(default=1, choices=[
		(1, _("Original")),
		(23976, "23.976"),
		(24000, "24"),
		(25000, "25"),
		(29970, "29.97"),
		(30000, "30")
	])
	config.subtitles.pango_subtitles_fps.addNotifier(setPangoSubtitleFPS)

	def setPangoSubtitleRemovehi(configElement):
		eSubtitleSettings.setPangoSubtitleRemovehi(configElement.value)

	config.subtitles.pango_subtitle_removehi = ConfigYesNo(default=False)
	config.subtitles.pango_subtitle_removehi.addNotifier(setPangoSubtitleRemovehi)

	def setPangoSubtitleAutoRun(configElement):
		eSubtitleSettings.setPangoSubtitleAutoRun(configElement.value)

	config.subtitles.pango_autoturnon = ConfigYesNo(default=True)
	config.subtitles.pango_autoturnon.addNotifier(setPangoSubtitleAutoRun)

	# AI start
	if BoxInfo.getItem("AISubs"):
		LANGUAGE_AI = {
			"ar": ("Arabic", _("Arabic")),
			"bg": ("Български", _("Български")),
			"nb": ("Norsk Bokmål", _("Norsk Bokmål")),
			"ca": ("Català", _("Català")),
			"cs": ("Česky", _("Česky")),
			"zh": ("Chinese", _("Chinese")),
			"da": ("Dansk", _("Dansk")),
			"de": ("Deutsch", _("Deutsch")),
			"el": ("Ελληνικά", _("Ελληνικά")),
			"en": ("English", _("English")),
			"es": ("Español", _("Español")),
			"et": ("Eesti", _("Eesti")),
			"fa": ("Persian", _("Persian")),
			"fi": ("Suomi", _("Suomi")),
			"fr": ("Français", _("Français")),
			"fy": ("Frysk", _("Frysk")),
			"he": ("Hebrew", _("Hebrew")),
			"hr": ("Hrvatski", _("Hrvatski")),
			"hu": ("Magyar", _("Magyar")),
			"id": ("Indonesian", _("Indonesian")),
			"is": ("Íslenska", _("Íslenska")),
			"it": ("Italiano", _("Italiano")),
			"ku": ("Kurdish", _("Kurdish")),
			"lt": ("Lietuvių", _("Lietuvių")),
			"lv": ("Latviešu", _("Latviešu")),
			"nl": ("Nederlands", _("Nederlands")),
			"no": ("Norsk", _("Norsk")),
			"pl": ("Polski", _("Polski")),
			"pt": ("Portuguese", _("Portuguese")),
			"ro": ("Romanian", _("Romanian")),
			"ru": ("Русский", _("Русский")),
			"sk": ("Slovensky", _("Slovensky")),
			"sl": ("Slovenščina", _("Slovenščina")),
			"sr": ("Srpski", _("Srpski")),
			"sv": ("Svenska", _("Svenska")),
			"th": ("ภาษาไทย", _("ภาษาไทย")),
			"tr": ("Türkçe", _("Türkçe")),
			"uk": ("Українська", _("Українська")),
			"vi": ("Tiếng Việt", _("Tiếng Việt"))
		}

		def setAiEnabled(configElement):
			eSubtitleSettings.setAiEnabled(configElement.value)

		config.subtitles.ai_enabled = ConfigYesNo(default=False)
		config.subtitles.ai_enabled.addNotifier(setAiEnabled)

		def setAiSubscriptionCode(configElement):
			eSubtitleSettings.setAiSubscriptionCode(str(configElement.value))

		config.subtitles.ai_subscription_code = ConfigNumber(default=15)
		config.subtitles.ai_subscription_code.addNotifier(setAiSubscriptionCode)

		def setAiSubtitleColors(configElement):
			eSubtitleSettings.setAiSubtitleColors(configElement.value)

		config.subtitles.ai_subtitle_colors = ConfigSelection(default=1, choices=[
			(1, _("White")),
			(2, _("Yellow"))
			(3, _("Red")),
			(4, _("Green")),
			(5, _("Blue"))
		])
		config.subtitles.ai_subtitle_colors.addNotifier(setAiSubtitleColors)

		def setAiConnectionSpeed(configElement):
			eSubtitleSettings.setAiConnectionSpeed(configElement.value)

		config.subtitles.ai_connection_speed = ConfigSelection(default=1, choices=[
			(1, _("Up to 50 Mbps")),
			(2, _("50-200 Mbps")),
			(3, _("Above 200 Mbps"))
		])
		config.subtitles.ai_connection_speed.addNotifier(setAiConnectionSpeed)

		langsAI = ["ar", "bg", "nb", "ca", "cs", "zh", "da", "de", "el", "en", "es", "et", "fa", "fi", "fr", "fy", "he", "hr", "hu", "id", "is", "it", "ku", "lt", "lv", "nl", "no", "pl", "pt", "ro", "ru", "sk", "sl", "sr", "sv", "th", "tr", "uk", "vi"]
		langsAI = [(x, LANGUAGE_AI[x][1]) for x in langsAI]
		langsAI.append(("zh-CN", _("Chinese (Simplified)")))
		langsAI.append(("ceb", _("Cebuano")))
		langsAI.append(("haw", _("Hawaiian")))
		langsAI.append(("iw", _("Hebrew")))
		langsAI.append(("hmn", _("Hmong")))
		langsAI.append(("ar_eg", _("Arabic (Egyptian)")))
		langsAI.append(("ar_ma", _("Arabic (Moroccan)")))
		langsAI.append(("ar_sy", _("Arabic (Syro-Lebanese)")))
		langsAI.append(("ar_tn", _("Arabic (Tunisian)")))
		langsAI.sort(key=lambda x: x[1])

		default = config.osd.language.value
		default = default.split("_")[0] if "_" in default else default
		if default == "zh":
			default = "zh-CN"
		if default not in [x[0] for x in langsAI]:
			default = "es"

		def setAiTranslateTo(configElement):
			eSubtitleSettings.setAiTranslateTo(configElement.value)

		config.subtitles.ai_translate_to = ConfigSelection(default=default, choices=langsAI)
		config.subtitles.ai_translate_to.addNotifier(setAiTranslateTo)
		# AI end

	config.autolanguage = ConfigSubsection()
	audio_language_choices = [
		("", _("None")),
		(originalAudioTracks, _("Original")),
		("ara", _("Arabic")),
		("eus baq", _("Basque")),
		("bul", _("Bulgarian")),
		("hrv", _("Croatian")),
		("chn sgp", _("Chinese - Simplified")),
		("twn hkn", _("Chinese - Traditional")),
		("ces cze", _("Czech")),
		("dan", _("Danish")),
		("dut ndl nld", _("Dutch")),
		("eng", _("English")),
		("est", _("Estonian")),
		("fin", _("Finnish")),
		("fra fre", _("French")),
		("deu ger", _("German")),
		("ell gre grc", _("Greek")),
		("heb", _("Hebrew")),
		("hun", _("Hungarian")),
		("ind", _("Indonesian")),
		("ita", _("Italian")),
		("lav", _("Latvian")),
		("lit", _("Lithuanian")),
		("ltz", _("Luxembourgish")),
		("nor", _("Norwegian")),
		("fas per fa pes", _("Persian")),
		("pol", _("Polish")),
		("por dub Dub DUB ud1 LEG", _("Portuguese")),
		("ron rum", _("Romanian")),
		("rus", _("Russian")),
		("srp", _("Serbian")),
		("slk slo", _("Slovak")),
		("slv", _("Slovenian")),
		("spa", _("Spanish")),
		("swe", _("Swedish")),
		("tha", _("Thai")),
		("tur Audio_TUR", _("Turkish")),
		("ukr Ukr", _("Ukrainian")),
		(visuallyImpairedCommentary, _("Audio description for the visually impaired"))
	]

	epg_language_choices = audio_language_choices[:1] + audio_language_choices[2:]

	def setEpgLanguage(configElement):
		eServiceEvent.setEPGLanguage(configElement.value)

	def setEpgLanguageAlternative(configElement):
		eServiceEvent.setEPGLanguageAlternative(configElement.value)

	def epglanguage(configElement):
		config.autolanguage.audio_epglanguage.setChoices([x for x in epg_language_choices if x[0] and x[0] != config.autolanguage.audio_epglanguage_alternative.value or not x[0] and not config.autolanguage.audio_epglanguage_alternative.value])
		config.autolanguage.audio_epglanguage_alternative.setChoices([x for x in epg_language_choices if x[0] and x[0] != config.autolanguage.audio_epglanguage.value or not x[0]])
	config.autolanguage.audio_epglanguage = ConfigSelection(default="", choices=epg_language_choices)
	config.autolanguage.audio_epglanguage_alternative = ConfigSelection(default="", choices=epg_language_choices)
	config.autolanguage.audio_epglanguage.addNotifier(setEpgLanguage)
	config.autolanguage.audio_epglanguage.addNotifier(epglanguage, initial_call=False)
	config.autolanguage.audio_epglanguage_alternative.addNotifier(setEpgLanguageAlternative)
	config.autolanguage.audio_epglanguage_alternative.addNotifier(epglanguage)

	def getselectedlanguages(range):
		return [eval("config.autolanguage.audio_autoselect%x.value" % x) for x in range]

	def autolanguage(configElement):
		config.autolanguage.audio_autoselect1.setChoices([x for x in audio_language_choices if x[0] and x[0] not in getselectedlanguages((2, 3, 4)) or not x[0] and not config.autolanguage.audio_autoselect2.value])
		config.autolanguage.audio_autoselect2.setChoices([x for x in audio_language_choices if x[0] and x[0] not in getselectedlanguages((1, 3, 4)) or not x[0] and not config.autolanguage.audio_autoselect3.value])
		config.autolanguage.audio_autoselect3.setChoices([x for x in audio_language_choices if x[0] and x[0] not in getselectedlanguages((1, 2, 4)) or not x[0] and not config.autolanguage.audio_autoselect4.value])
		config.autolanguage.audio_autoselect4.setChoices([x for x in audio_language_choices if x[0] and x[0] not in getselectedlanguages((1, 2, 3)) or not x[0]])
		eSettings.setAudioLanguages(config.autolanguage.audio_autoselect1.value, config.autolanguage.audio_autoselect2.value, config.autolanguage.audio_autoselect3.value, config.autolanguage.audio_autoselect4.value)

	config.autolanguage.audio_autoselect1 = ConfigSelection(default="", choices=audio_language_choices)
	config.autolanguage.audio_autoselect2 = ConfigSelection(default="", choices=audio_language_choices)
	config.autolanguage.audio_autoselect3 = ConfigSelection(default="", choices=audio_language_choices)
	config.autolanguage.audio_autoselect4 = ConfigSelection(default="", choices=audio_language_choices)
	config.autolanguage.audio_autoselect1.addNotifier(autolanguage, initial_call=False)
	config.autolanguage.audio_autoselect2.addNotifier(autolanguage, initial_call=False)
	config.autolanguage.audio_autoselect3.addNotifier(autolanguage, initial_call=False)
	config.autolanguage.audio_autoselect4.addNotifier(autolanguage)

	def setAudioDefaultAC3(configElement):
		eSettings.setAudioDefaultAC3(configElement.value)

	config.autolanguage.audio_defaultac3 = ConfigYesNo(default=False)
	config.autolanguage.audio_defaultac3.addNotifier(setAudioDefaultAC3)

	def setAudioDefaultDDP(configElement):
		eSettings.setAudioDefaultDDP(configElement.value)

	config.autolanguage.audio_defaultddp = ConfigYesNo(default=False)
	config.autolanguage.audio_defaultddp.addNotifier(setAudioDefaultDDP)

	def setAudioUseCache(configElement):
		eSettings.setAudioUseCache(configElement.value)

	config.autolanguage.audio_usecache = ConfigYesNo(default=True)
	config.autolanguage.audio_usecache.addNotifier(setAudioUseCache)

	subtitle_language_choices = audio_language_choices[:1] + audio_language_choices[2:]

	def getselectedsublanguages(range):
		return [eval("config.autolanguage.subtitle_autoselect%x.value" % x) for x in range]

	def autolanguagesub(configElement):
		config.autolanguage.subtitle_autoselect1.setChoices([x for x in subtitle_language_choices if x[0] and x[0] not in getselectedsublanguages((2, 3, 4)) or not x[0] and not config.autolanguage.subtitle_autoselect2.value])
		config.autolanguage.subtitle_autoselect2.setChoices([x for x in subtitle_language_choices if x[0] and x[0] not in getselectedsublanguages((1, 3, 4)) or not x[0] and not config.autolanguage.subtitle_autoselect3.value])
		config.autolanguage.subtitle_autoselect3.setChoices([x for x in subtitle_language_choices if x[0] and x[0] not in getselectedsublanguages((1, 2, 4)) or not x[0] and not config.autolanguage.subtitle_autoselect4.value])
		config.autolanguage.subtitle_autoselect4.setChoices([x for x in subtitle_language_choices if x[0] and x[0] not in getselectedsublanguages((1, 2, 3)) or not x[0]])
		choicelist = [(0, _("None"))]
		for y in range(1, 15 if config.autolanguage.subtitle_autoselect4.value else (7 if config.autolanguage.subtitle_autoselect3.value else (4 if config.autolanguage.subtitle_autoselect2.value else (2 if config.autolanguage.subtitle_autoselect1.value else 0)))):
			choicelist.append((y, ", ".join([eval("config.autolanguage.subtitle_autoselect%x.getText()" % x) for x in (y & 1, y & 2, y & 4 and 3, y & 8 and 4) if x])))
		if config.autolanguage.subtitle_autoselect3.value:
			choiceList.append((y + 1, _("All")))
		config.autolanguage.equal_languages.setChoices(default=0, choices=choiceList)
		eSubtitleSettings.setSubtitleLanguages(config.autolanguage.subtitle_autoselect1.value, config.autolanguage.subtitle_autoselect2.value, config.autolanguage.subtitle_autoselect3.value, config.autolanguage.subtitle_autoselect4.value)

	def setSubtitleEqualLanguages(configElement):
		eSubtitleSettings.setSubtitleEqualLanguages(configElement.value)

	config.autolanguage.equal_languages = ConfigSelection(default=0, choices=[x for x in range(0, 16)])
	config.autolanguage.equal_languages.addNotifier(setSubtitleEqualLanguages)
	config.autolanguage.subtitle_autoselect1 = ConfigSelection(default="", choices=subtitle_language_choices)
	config.autolanguage.subtitle_autoselect2 = ConfigSelection(default="", choices=subtitle_language_choices)
	config.autolanguage.subtitle_autoselect3 = ConfigSelection(default="", choices=subtitle_language_choices)
	config.autolanguage.subtitle_autoselect4 = ConfigSelection(default="", choices=subtitle_language_choices)
	config.autolanguage.subtitle_autoselect1.addNotifier(autolanguagesub, initial_call=False)
	config.autolanguage.subtitle_autoselect2.addNotifier(autolanguagesub, initial_call=False)
	config.autolanguage.subtitle_autoselect3.addNotifier(autolanguagesub, initial_call=False)
	config.autolanguage.subtitle_autoselect4.addNotifier(autolanguagesub)

	def setSubtitleHearingImpaired(configElement):
		eSubtitleSettings.setSubtitleHearingImpaired(configElement.value)
	config.autolanguage.subtitle_hearingimpaired = ConfigYesNo(default=False)
	config.autolanguage.subtitle_hearingimpaired.addNotifier(setSubtitleHearingImpaired)

	def setSubtitleDefaultImpaired(configElement):
		eSubtitleSettings.setSubtitleDefaultImpaired(configElement.value)
	config.autolanguage.subtitle_defaultimpaired = ConfigYesNo(default=False)
	config.autolanguage.subtitle_defaultimpaired.addNotifier(setSubtitleDefaultImpaired)

	def setSubtitleDefaultDVB(configElement):
		eSubtitleSettings.setSubtitleDefaultDVB(configElement.value)
	config.autolanguage.subtitle_defaultdvb = ConfigYesNo(default=False)
	config.autolanguage.subtitle_defaultdvb.addNotifier(setSubtitleDefaultDVB)

	def setSubtitleUseCache(configElement):
		eSubtitleSettings.setSubtitleUseCache(configElement.value)
	config.autolanguage.subtitle_usecache = ConfigYesNo(default=True)
	config.autolanguage.subtitle_usecache.addNotifier(setSubtitleUseCache)

	config.oscaminfo = ConfigSubsection()
	if SystemInfo["OSCamIsActive"]:
		config.oscaminfo.showInExtensions = ConfigYesNo(default=True)
	else:
		config.oscaminfo.showInExtensions = ConfigYesNo(default=False)
	config.oscaminfo.userdatafromconf = ConfigYesNo(default=True)
	config.oscaminfo.autoupdate = ConfigYesNo(default=False)
	config.oscaminfo.username = ConfigText(default="username", fixed_size=False, visible_width=12)
	config.oscaminfo.password = ConfigPassword(default="password", fixed_size=False)
	config.oscaminfo.ip = ConfigIP(default=[127, 0, 0, 1], auto_jump=True)
	config.oscaminfo.port = ConfigInteger(default=16002, limits=(0, 65536))
	config.oscaminfo.intervall = ConfigSelectionNumber(min=1, max=600, stepwidth=1, default=10, wraparound=True)

	config.ncaminfo = ConfigSubsection()
	if SystemInfo["NCamIsActive"]:
		config.ncaminfo.showInExtensions = ConfigYesNo(default=True)
	else:
		config.ncaminfo.showInExtensions = ConfigYesNo(default=False)
	config.ncaminfo.userdatafromconf = ConfigYesNo(default=True)
	config.ncaminfo.autoupdate = ConfigYesNo(default=False)
	config.ncaminfo.username = ConfigText(default="username", fixed_size=False, visible_width=12)
	config.ncaminfo.password = ConfigPassword(default="password", fixed_size=False)
	config.ncaminfo.ip = ConfigIP(default=[127, 0, 0, 1], auto_jump=True)
	config.ncaminfo.port = ConfigInteger(default=16002, limits=(0, 65536))
	config.ncaminfo.intervall = ConfigSelectionNumber(min=1, max=600, stepwidth=1, default=10, wraparound=True)

	config.cccaminfo = ConfigSubsection()
	if SystemInfo["CCcamIsActive"]:
		config.cccaminfo.showInExtensions = ConfigYesNo(default=True)
	else:
		config.cccaminfo.showInExtensions = ConfigYesNo(default=False)
	config.cccaminfo.serverNameLength = ConfigSelectionNumber(min=10, max=100, stepwidth=1, default=22, wraparound=True)
	config.cccaminfo.name = ConfigText(default="Profile", fixed_size=False)
	config.cccaminfo.ip = ConfigText(default="192.168.2.12", fixed_size=False)
	config.cccaminfo.username = ConfigText(default="", fixed_size=False)
	config.cccaminfo.password = ConfigText(default="", fixed_size=False)
	config.cccaminfo.port = ConfigInteger(default=16001, limits=(1, 65535))
	config.cccaminfo.profile = ConfigText(default="", fixed_size=False)
	config.cccaminfo.ecmInfoEnabled = ConfigYesNo(default=True)
	config.cccaminfo.ecmInfoTime = ConfigSelectionNumber(min=1, max=10, stepwidth=1, default=5, wraparound=True)
	config.cccaminfo.ecmInfoForceHide = ConfigYesNo(default=True)
	config.cccaminfo.ecmInfoPositionX = ConfigInteger(default=50)
	config.cccaminfo.ecmInfoPositionY = ConfigInteger(default=50)
	config.cccaminfo.blacklist = ConfigText(default="/media/hdd/CCcamInfo.blacklisted", fixed_size=False)
	config.cccaminfo.profiles = ConfigText(default="/media/hdd/CCcamInfo.profiles", fixed_size=False)

	config.streaming = ConfigSubsection()
	config.streaming.stream_ecm = ConfigYesNo(default=False)
	config.streaming.descramble = ConfigYesNo(default=True)
	config.streaming.descramble_client = ConfigYesNo(default=False)
	config.streaming.stream_eit = ConfigYesNo(default=True)
	config.streaming.stream_ait = ConfigYesNo(default=True)
	config.streaming.stream_sdtbat = ConfigYesNo(default=False)
	config.streaming.authentication = ConfigYesNo(default=False)

	config.mediaplayer = ConfigSubsection()
	config.mediaplayer.useAlternateUserAgent = ConfigYesNo(default=False)
	config.mediaplayer.alternateUserAgent = ConfigText(default="")

	config.misc.softcam_setup = ConfigSubsection()
	config.misc.softcam_setup.extension_menu = ConfigYesNo(default=True)
	config.misc.softcam_streamrelay_url = ConfigIP(default=[127, 0, 0, 1], auto_jump=True)
	config.misc.softcam_streamrelay_port = ConfigInteger(default=17999, limits=(0, 65535))
	config.misc.softcam_streamrelay_delay = ConfigSelectionNumber(min=0, max=2000, stepwidth=50, default=0, wraparound=True)

	config.ntp = ConfigSubsection()
	config.ntp.server = ConfigText("pool.ntp.org", fixed_size=False)
	config.powertimerlog = ConfigSubsection()
	config.powertimerlog.actived = ConfigYesNo(default=False)

	def timesyncChanged(configElement):
		if configElement.value == "dvb" or not GetIPsFromNetworkInterfaces():
			eDVBLocalTimeHandler.getInstance().setUseDVBTime(True)
			eEPGCache.getInstance().timeUpdated()
		else:
			eDVBLocalTimeHandler.getInstance().setUseDVBTime(False)
			eEPGCache.getInstance().timeUpdated()
	config.ntp.timesync = ConfigSelection(default="auto", choices=[
		("auto", _("Auto")),
		("dvb", _("Transponder time")),
		("ntp", _("Internet time (SNTP)"))
	])
	config.ntp.timesync.addNotifier(timesyncChanged)


def updateChoices(sel, choices):
	if choices:
		defval = None
		val = int(sel.value)
		if val not in choices:
			tmp = choices[:]
			tmp.reverse()
			for x in tmp:
				if x < val:
					defval = str(x)
					break
		sel.setChoices(list(map(str, choices)), defval)


def preferredPath(path):
	if config.usage.setup_level.index < 2 or path == "<default>" or not path:
		return None	 # config.usage.default_path.value, but delay lookup until usage
	elif path == "<current>":
		return config.movielist.last_videodir.value
	elif path == "<timer>":
		return config.movielist.last_timer_videodir.value
	else:
		return path


def preferredTimerPath():
	return preferredPath(config.usage.timer_path.value)


def preferredInstantRecordPath():
	return preferredPath(config.usage.instantrec_path.value)


def defaultMoviePath():
	return defaultRecordingLocation(config.usage.default_path.value)


def showrotorpositionChoicesUpdate(update=False):
	choiceslist = [("no", _("no")), ("yes", _("yes")), ("withtext", _("with text")), ("tunername", _("with tuner name"))]
	count = 0
	for x in nimmanager.nim_slots:
		if nimmanager.getRotorSatListForNim(x.slot, only_first=True):
			choiceslist.append((str(x.slot), x.getSlotName() + _(" (auto detection)")))
			count += 1
	if count > 1:
		choiceslist.append(("all", _("all tuners") + _(" (auto detection)")))
		choiceslist.remove(("tunername", _("with tuner name")))
	if not update:
		config.misc.showrotorposition = ConfigSelection(default="no", choices=choiceslist)
	else:
		config.misc.showrotorposition.setChoices(choiceslist, "no")
	SystemInfo["isRotorTuner"] = count > 0


def preferredTunerChoicesUpdate(update=False):
	dvbs_nims = [("-2", _("disabled"))]
	dvbt_nims = [("-2", _("disabled"))]
	dvbc_nims = [("-2", _("disabled"))]
	atsc_nims = [("-2", _("disabled"))]

	nims = [("-1", _("auto"))]
	for slot in nimmanager.nim_slots:
		if hasattr(slot.config, "configMode") and slot.config.configMode.value == "nothing":
			continue
		if slot.isCompatible("DVB-S"):
			dvbs_nims.append((str(slot.slot), slot.getSlotName()))
		elif slot.isCompatible("DVB-T"):
			dvbt_nims.append((str(slot.slot), slot.getSlotName()))
		elif slot.isCompatible("DVB-C"):
			dvbc_nims.append((str(slot.slot), slot.getSlotName()))
		elif slot.isCompatible("ATSC"):
			atsc_nims.append((str(slot.slot), slot.getSlotName()))
		nims.append((str(slot.slot), slot.getSlotName()))

	if not update:
		config.usage.frontend_priority = ConfigSelection(default="-1", choices=list(nims))
	else:
		config.usage.frontend_priority.setChoices(list(nims), "-1")
	nims.insert(0, ("-2", _("disabled")))
	if not update:
		config.usage.recording_frontend_priority = ConfigSelection(default="-2", choices=nims)
	else:
		config.usage.recording_frontend_priority.setChoices(nims, "-2")
	if not update:
		config.usage.frontend_priority_dvbs = ConfigSelection(default="-2", choices=list(dvbs_nims))
	else:
		config.usage.frontend_priority_dvbs.setChoices(list(dvbs_nims), "-2")
	dvbs_nims.insert(1, ("-1", _("auto")))
	if not update:
		config.usage.recording_frontend_priority_dvbs = ConfigSelection(default="-2", choices=dvbs_nims)
	else:
		config.usage.recording_frontend_priority_dvbs.setChoices(dvbs_nims, "-2")
	if not update:
		config.usage.frontend_priority_dvbt = ConfigSelection(default="-2", choices=list(dvbt_nims))
	else:
		config.usage.frontend_priority_dvbt.setChoices(list(dvbt_nims), "-2")
	dvbt_nims.insert(1, ("-1", _("auto")))
	if not update:
		config.usage.recording_frontend_priority_dvbt = ConfigSelection(default="-2", choices=dvbt_nims)
	else:
		config.usage.recording_frontend_priority_dvbt.setChoices(dvbt_nims, "-2")
	if not update:
		config.usage.frontend_priority_dvbc = ConfigSelection(default="-2", choices=list(dvbc_nims))
	else:
		config.usage.frontend_priority_dvbc.setChoices(list(dvbc_nims), "-2")
	dvbc_nims.insert(1, ("-1", _("auto")))
	if not update:
		config.usage.recording_frontend_priority_dvbc = ConfigSelection(default="-2", choices=dvbc_nims)
	else:
		config.usage.recording_frontend_priority_dvbc.setChoices(dvbc_nims, "-2")
	if not update:
		config.usage.frontend_priority_atsc = ConfigSelection(default="-2", choices=list(atsc_nims))
	else:
		config.usage.frontend_priority_atsc.setChoices(list(atsc_nims), "-2")
	atsc_nims.insert(1, ("-1", _("auto")))
	if not update:
		config.usage.recording_frontend_priority_atsc = ConfigSelection(default="-2", choices=atsc_nims)
	else:
		config.usage.recording_frontend_priority_atsc.setChoices(atsc_nims, "-2")

	SystemInfo["DVB-S_priority_tuner_available"] = len(dvbs_nims) > 3 and any(len(i) > 2 for i in (dvbt_nims, dvbc_nims, atsc_nims))
	SystemInfo["DVB-T_priority_tuner_available"] = len(dvbt_nims) > 3 and any(len(i) > 2 for i in (dvbs_nims, dvbc_nims, atsc_nims))
	SystemInfo["DVB-C_priority_tuner_available"] = len(dvbc_nims) > 3 and any(len(i) > 2 for i in (dvbs_nims, dvbt_nims, atsc_nims))
	SystemInfo["ATSC_priority_tuner_available"] = len(atsc_nims) > 3 and any(len(i) > 2 for i in (dvbs_nims, dvbc_nims, dvbt_nims))


def patchTuxtxtConfFile(dummyConfigElement):
	print("[UsageConfig] patching tuxtxt2.conf")
	if config.usage.tuxtxt_font_and_res.value == "X11_SD":
		tuxtxt2 = [
			["UseTTF", 0],
			["TTFBold", 1],
			["TTFScreenResX", 720],
			["StartX", 50],
			["EndX", 670],
			["StartY", 30],
			["EndY", 555],
			["TTFShiftY", 0],
			["TTFShiftX", 0],
			["TTFWidthFactor16", 26],
			["TTFHeightFactor16", 14]
		]
	elif config.usage.tuxtxt_font_and_res.value == "TTF_SD":
		tuxtxt2 = [
			["UseTTF", 1],
			["TTFBold", 1],
			["TTFScreenResX", 720],
			["StartX", 50],
			["EndX", 670],
			["StartY", 30],
			["EndY", 555],
			["TTFShiftY", 2],
			["TTFShiftX", 0],
			["TTFWidthFactor16", 29],
			["TTFHeightFactor16", 14]
		]
	elif config.usage.tuxtxt_font_and_res.value == "TTF_HD":
		tuxtxt2 = [
			["UseTTF", 1],
			["TTFBold", 0],
			["TTFScreenResX", 1280],
			["StartX", 80],
			["EndX", 1200],
			["StartY", 35],
			["EndY", 685],
			["TTFShiftY", -3],
			["TTFShiftX", 0],
			["TTFWidthFactor16", 26],
			["TTFHeightFactor16", 14]
		]
	elif config.usage.tuxtxt_font_and_res.value == "TTF_FHD":
		tuxtxt2 = [
			["UseTTF", 1],
			["TTFBold", 0],
			["TTFScreenResX", 1920],
			["StartX", 140],
			["EndX", 1780],
			["StartY", 52],
			["EndY", 1027],
			["TTFShiftY", -6],
			["TTFShiftX", 0],
			["TTFWidthFactor16", 26],
			["TTFHeightFactor16", 14]
		]
	elif config.usage.tuxtxt_font_and_res.value == "expert_mode":
		tuxtxt2 = [
			["UseTTF", int(config.usage.tuxtxt_UseTTF.value)],
			["TTFBold", int(config.usage.tuxtxt_TTFBold.value)],
			["TTFScreenResX", int(config.usage.tuxtxt_TTFScreenResX.value)],
			["StartX", config.usage.tuxtxt_StartX.value],
			["EndX", config.usage.tuxtxt_EndX.value],
			["StartY", config.usage.tuxtxt_StartY.value],
			["EndY", config.usage.tuxtxt_EndY.value],
			["TTFShiftY", int(config.usage.tuxtxt_TTFShiftY.value)],
			["TTFShiftX", int(config.usage.tuxtxt_TTFShiftX.value)],
			["TTFWidthFactor16", config.usage.tuxtxt_TTFWidthFactor16.value],
			["TTFHeightFactor16", config.usage.tuxtxt_TTFHeightFactor16.value]
		]
	tuxtxt2.append(["CleanAlgo", config.usage.tuxtxt_CleanAlgo.value])

	TUXTXT_CFG_FILE = "/etc/tuxtxt/tuxtxt2.conf"
	command = "sed -i -r '"
	for f in tuxtxt2:
		# replace keyword (%s) followed by any value ([-0-9]+) by that keyword \1 and the new value %d
		command += r"s|(%s)\s+([-0-9]+)|\\1 %d|;" % (f[0], f[1])
	command += "' %s" % TUXTXT_CFG_FILE
	for f in tuxtxt2:
		# if keyword is not found in file, append keyword and value
		command += " ; if ! grep -q '%s' %s ; then echo '%s %d' >> %s ; fi" % (f[0], TUXTXT_CFG_FILE, f[0], f[1], TUXTXT_CFG_FILE)
	try:
		Console().ePopen(command)
	except:
		print("[UsageConfig] Error: failed to patch %s!" % TUXTXT_CFG_FILE)
	print("[UsageConfig] patched tuxtxt2.conf")

	config.usage.tuxtxt_ConfFileHasBeenPatched.setValue(True)


def dropEPGNewLines(text):
	if config.epg.replace_newlines.value != "no":
		text = text.replace('\x0a', replaceEPGSeparator(config.epg.replace_newlines.value))
	return text


def replaceEPGSeparator(code):
	return {"newline": "\n", "2newlines": "\n\n", "space": " ", "dash": " - ", "dot": " . ", "asterisk": " * ", "hashtag": " # ", "nothing": ""}.get(code)


def getFileUsage():
	if isfile("/etc/crontab") and isfile("/home/root/.cache/gstreamer-1.0/registry.arm.bin") and not fileContains("/etc/crontab", "registry.arm.bin"):
		Console().ePopen("sed -i '$a@reboot root rm -f /home/root/.cache/gstreamer-1.0/registry.arm.bin' /etc/crontab")
	if not isfile("/home/root/.cache/gstreamer-1.0/registry.arm.bin"):
		Console().ePopen("sed -i '/gstreamer/d' /etc/crontab")
		return False
	return True
