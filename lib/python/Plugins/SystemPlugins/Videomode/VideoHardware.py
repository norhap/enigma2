from Components.config import config, ConfigSelection, ConfigSubDict, ConfigYesNo
from Components.SystemInfo import BoxInfo, BRAND, MODEL
from Tools.CList import CList
from enigma import eAVControl
from Components.About import getChipSet
# The "VideoHardware" is the interface to /proc/stb/video.
# It generates hotplug events, and gives you the list of
# available and preferred modes, as well as handling the currently
# selected mode. No other strict checking is done.

config.av.edid_override = ConfigYesNo(default=True)


class VideoHardware:
	rates = {}  # high-level, use selectable modes.
	modes = {}  # a list of (high-level) modes for a certain port.

	rates["PAL"] = {"50Hz": {50: "pal"},
							"60Hz": {60: "pal60"},
							"multi": {50: "pal", 60: "pal60"}}

	rates["NTSC"] = {"60Hz": {60: "ntsc"}}

	rates["Multi"] = {"multi": {50: "pal", 60: "ntsc"}}

	if BRAND == "Amlogic":
		rates["480i"] = {"60Hz": {60: "480i60hz"}}
		rates["576i"] = {"50Hz": {50: "576i50hz"}}
		rates["480p"] = {"60Hz": {60: "480p60hz"}}
		rates["576p"] = {"50Hz": {50: "576p50hz"}}
		rates["720p"] = {"50Hz": {50: "720p50hz"},
								"60Hz": {60: "720p60hz"},
								"auto": {60: "720p60hz"}}
		rates["1080i"] = {"50Hz": {50: "1080i50hz"},
								"60Hz": {60: "1080i60hz"},
								"auto": {60: "1080i60hz"}}
		rates["1080p"] = {"50Hz": {50: "1080p50hz"},
								"60Hz": {60: "1080p60hz"},
								"30Hz": {30: "1080p30hz"},
								"25Hz": {25: "1080p25hz"},
								"24Hz": {24: "1080p24hz"},
								"auto": {60: "1080p60hz"}}
		rates["2160p"] = {"50Hz": {50: "2160p50hz"},
								"60Hz": {60: "2160p60hz"},
								"30Hz": {30: "2160p30hz"},
								"25Hz": {25: "2160p25hz"},
								"24Hz": {24: "2160p24hz"},
								"auto": {60: "2160p60hz"}}
		rates["2160p30"] = {"25Hz": {50: "2160p25hz"},
								"30Hz": {60: "2160p30hz"},
								"auto": {60: "2160p30hz"}}
	else:
		rates["480i"] = {"60Hz": {60: "480i"}}
		rates["576i"] = {"50Hz": {50: "576i"}}
		rates["480p"] = {"60Hz": {60: "480p"}}
		rates["576p"] = {"50Hz": {50: "576p"}}
		rates["720p"] = {"50Hz": {50: "720p50"},
								"60Hz": {60: "720p"},
								"multi": {50: "720p50", 60: "720p"},
								"auto": {50: "720p50", 60: "720p", 24: "720p24"}}
		rates["1080i"] = {"50Hz": {50: "1080i50"},
								"60Hz": {60: "1080i"},
								"multi": {50: "1080i50", 60: "1080i"},
								"auto": {50: "1080i50", 60: "1080i", 24: "1080i24"}}
		rates["1080p"] = {"50Hz": {50: "1080p50"},
								"60Hz": {60: "1080p"},
								"multi": {50: "1080p50", 60: "1080p"},
								"auto": {50: "1080p50", 60: "1080p", 24: "1080p24"}}
		rates["2160p"] = {"50Hz": {50: "2160p50"},
								"60Hz": {60: "2160p"},
								"multi": {50: "2160p50", 60: "2160p"},
								"auto": {50: "2160p50", 60: "2160p", 24: "2160p24"}}
		if BRAND != "Vu+":
			rates["2160p30"] = {"25Hz": {50: "2160p25"},
									"30Hz": {60: "2160p30"},
									"multi": {50: "2160p25", 60: "2160p30"},
									"auto": {50: "2160p25", 60: "2160p30", 24: "2160p24"}}
		else:
			rates["2160p30"] = {"30Hz": {60: "2160p30"}}
	rates["smpte"] = {"50Hz": {50: "smpte50hz"},
							"60Hz": {60: "smpte60hz"},
							"30Hz": {30: "smpte30hz"},
							"25Hz": {25: "smpte25hz"},
							"24Hz": {24: "smpte24hz"},
							"auto": {60: "smpte60hz"}}

	rates["PC"] = {
		"1024x768": {60: "1024x768"},
		"800x600": {60: "800x600"},  # also not possible
		"720x480": {60: "720x480"},
		"720x576": {60: "720x576"},
		"1280x720": {60: "1280x720"},
		"1280x720 multi": {50: "1280x720_50", 60: "1280x720"},
		"1920x1080": {60: "1920x1080"},
		"1920x1080 multi": {50: "1920x1080", 60: "1920x1080_50"},
		"1280x1024": {60: "1280x1024"},
		"1366x768": {60: "1366x768"},
		"1366x768 multi": {50: "1366x768", 60: "1366x768_50"},
		"1280x768": {60: "1280x768"},
		"640x480": {60: "640x480"}
	}

	if BoxInfo.getItem("scart"):
		modes["Scart"] = ["PAL", "NTSC", "Multi"]
	if BoxInfo.getItem("rca"):
		modes["RCA"] = ["576i", "PAL", "NTSC", "Multi"]
	if BoxInfo.getItem("avjack"):
		modes["Jack"] = ["PAL", "NTSC", "Multi"]

	if getChipSet() in ("7366", "7376", "5272s", "7444", "7445", "7445s", "72604"):
		modes["HDMI"] = ["720p", "1080p", "2160p", "1080i", "576p", "576i", "480p", "480i"]
		widescreen_modes = {"720p", "1080p", "1080i", "2160p"}
	elif getChipSet() in ("7252", "7251", "7251S", "7252S", "7251s", "7252s", "7278", "7444s", "3798mv200", "3798mv200h", "3798cv200", "hi3798mv200", "hi3798mv200h", "hi3798cv200", "hi3798mv300", "3798mv300"):
		modes["HDMI"] = ["720p", "1080p", "2160p", "2160p30", "1080i", "576p", "576i", "480p", "480i"]
		widescreen_modes = {"720p", "1080p", "1080i", "2160p", "2160p30"}
	elif getChipSet() in ("7241", "7358", "7362", "73625", "7346", "7356", "73565", "7424", "7425", "7435", "7552", "7581", "7584", "75845", "7585", "pnx8493", "7162", "7111", "3716mv410", "hi3716mv410", "hi3716mv430", "3716mv430"):
		modes["HDMI"] = ["720p", "1080p", "1080i", "576p", "576i", "480p", "480i"]
		widescreen_modes = {"720p", "1080p", "1080i"}
	else:
		modes["HDMI"] = ["720p", "1080i", "576p", "576i", "480p", "480i"]
		widescreen_modes = {"720p", "1080i"}

	modes["DVI-PC"] = ["PC"]

	if BoxInfo.getItem("yuv"):
		modes["YPbPr"] = modes["HDMI"]

	if "YPbPr" in modes and not BoxInfo.getItem("yuv"):
		del modes["YPbPr"]

	if "Scart" in modes and not BoxInfo.getItem("scart") and (BoxInfo.getItem("rca") or BoxInfo.getItem("avjack")):
		modes["RCA"] = modes["Scart"]
		del modes["Scart"]

	if "Scart" in modes and not BoxInfo.getItem("rca") and not BoxInfo.getItem("scart") and not BoxInfo.getItem("avjack"):
		del modes["Scart"]

	if MODEL == "hd2400":
		rev = open("/proc/stb/info/board_revision", "r").read()
		if rev >= "2":
			del modes["YPbPr"]

	def getOutputAspect(self):
		ret = (16, 9)
		port = config.av.videoport.value
		if port not in config.av.videomode:
			print("[Videomode] VideoHardware current port not available in getOutputAspect!!! force 16:9")
		else:
			mode = config.av.videomode[port].value
			force_widescreen = self.isWidescreenMode(port, mode)
			is_widescreen = force_widescreen or config.av.aspect.value in ("16_9", "16_10")
			is_auto = config.av.aspect.value == "auto"
			if is_widescreen:
				if force_widescreen:
					pass
				else:
					aspect = {"16_9": "16:9", "16_10": "16:10"}[config.av.aspect.value]
					if aspect == "16:10":
						ret = (16, 10)
			elif is_auto:
				try:
					aspect_str = open("/proc/stb/vmpeg/0/aspect", "r").read()
					if aspect_str == "1":  # 4:3
						ret = (4, 3)
				except Exception:
					pass
			else:  # 4:3
				ret = (4, 3)
		return ret

	def __init__(self):
		self.last_modes_preferred = []
		self.on_hotplug = CList()
		self.current_mode = None
		self.current_port = None

		self.readAvailableModes()
		self.readPreferredModes()

		if "DVI-PC" in self.modes and not self.getModeList("DVI-PC"):
			print("[Videomode] VideoHardware remove DVI-PC because of not existing modes")
			del self.modes["DVI-PC"]
		if "Scart" in self.modes and not self.getModeList("Scart"):
			print("[Videomode] VideoHardware remove Scart because of not existing modes")
			del self.modes["Scart"]
		if "YPbPr" in self.modes and not BoxInfo.getItem("yuv"):
			del self.modes["YPbPr"]
		if "Scart" in self.modes and not BoxInfo.getItem("scart") and (BoxInfo.getItem("rca") or BoxInfo.getItem("avjack")):
			self.modes["RCA"] = self.modes["Scart"]
			del self.modes["Scart"]
		if "Scart" in self.modes and not BoxInfo.getItem("rca") and not BoxInfo.getItem("scart") and not BoxInfo.getItem("avjack"):
			del self.modes["Scart"]

		self.createConfig()

		# take over old AVSwitch component :)
		from Components.AVSwitch import AVSwitch
		config.av.aspectratio.notifiers = []
		config.av.tvsystem.notifiers = []
		config.av.wss.notifiers = []
		AVSwitch.getOutputAspect = self.getOutputAspect

		config.av.aspect.addNotifier(self.updateAspect)
		config.av.wss.addNotifier(self.updateAspect)
		config.av.policy_169.addNotifier(self.updateAspect)
		config.av.policy_43.addNotifier(self.updateAspect)

	def readAvailableModes(self):
		modes = eAVControl.getInstance().getAvailableModes()
		self.modes_available = modes.split()

	def readPreferredModes(self):
		if not config.av.edid_override.value:
			modes = eAVControl.getInstance().getPreferredModes(1)
			if len(modes) <= 1:
				self.modes_preferred = modes.split()
				print("[Videomode] reading preferred modes is empty")
			else:  # ports availables Jack, HDMI, RCA...
				self.modes_preferred = self.modes_available
				print("[Videomode] using all video mode availables")
		else:
			self.modes_preferred = self.modes_available
			print("[Videomode] config.av.edid_override.value, using all video modes")
		self.last_modes_preferred = self.modes_preferred

	# check if a high-level mode with a given rate is available.
	def isModeAvailable(self, port, mode, rate):
		rate = self.rates[mode][rate]
		for mode in rate.values():
			if port != "HDMI":
				if mode not in self.modes_preferred:
					return False
			else:
				if mode not in self.modes_available:
					return False
		return True

	def isWidescreenMode(self, port, mode):
		return mode in self.widescreen_modes

	def setMode(self, port, mode, rate, force=None):
		print("[Videomode] setMode - port:", port, "mode:", mode, "rate:", rate)
		# we can ignore "port"
		self.current_mode = mode
		self.current_port = port
		modes = self.rates[mode][rate]

		mode_50 = modes.get(50)
		mode_60 = modes.get(60)
		mode_24 = modes.get(24)

		if mode_50 is None or force == 60:
			mode_50 = mode_60
		if mode_60 is None or force == 50:
			mode_60 = mode_50
		if mode_24 is None or force:
			mode_24 = mode_60
			if force == 50:
				mode_24 = mode_50
		try:
			open("/proc/stb/video/videomode_50hz", "w").write(mode_50)
			open("/proc/stb/video/videomode_60hz", "w").write(mode_60)
		except OSError:
			print("[Videomode] cannot open /proc/stb/video/videomode failed.")
			try:
				# fallback if no possibility to setup 50/60 hz mode
				open("/proc/stb/video/videomode", "w").write(mode_50)
			except OSError:
				print("[Videomode] Write to /proc/stb/video/videomode failed.")

		if BoxInfo.getItem("has24hz"):
			try:
				print("[Videomode] Write to /proc/stb/video/videomode_24hz")
				open("/proc/stb/video/videomode_24hz", "w").write(mode_24)
			except OSError:
				print("[Videomode] cannot open /proc/stb/video/videomode_24hz")

		if BRAND == "GigaBlue":
			try:
				# use 50Hz mode (if available) for booting
				open("/etc/videomode", "w").write(mode_50)
			except OSError:
				print("[Videomode] Write to /etc/videomode failed.")

		self.updateAspect(None)

	def saveMode(self, port, mode, rate):
		print("[Videomode] VideoHardware saveMode", port, mode, rate)
		config.av.videoport.value = port
		config.av.videoport.save()
		if port in config.av.videomode:
			config.av.videomode[port].value = mode
			config.av.videomode[port].save()
		if mode in config.av.videorate:
			config.av.videorate[mode].value = rate
			config.av.videorate[mode].save()

	def isPortAvailable(self, port):
		# fixme
		return True

	def isPortUsed(self, port):
		if port == "HDMI":
			self.readPreferredModes()
			return len(self.modes_preferred) != 0
		else:
			return True

	def getPortList(self):
		return [port for port in self.modes if self.isPortAvailable(port)]

	# get a list with all modes, with all rates, for a given port.
	def getModeList(self, port):
		print("[Videomode] VideoHardware getModeList for port", port)
		res = []
		for mode in self.modes[port]:
			# list all rates which are completely valid
			rates = [rate for rate in self.rates[mode] if self.isModeAvailable(port, mode, rate)]

			# if at least one rate is ok, add this mode
			if len(rates):
				res.append((mode, rates))
		return res

	def createConfig(self, *args):
		lst = []

		config.av.videomode = ConfigSubDict()
		config.av.videorate = ConfigSubDict()

		# create list of output ports
		portlist = self.getPortList()
		for port in portlist:
			descr = port
			if "HDMI" in port:
				lst.insert(0, (port, descr))
			else:
				lst.append((port, descr))

			# create list of available modes
			modes = self.getModeList(port)
			if len(modes):
				config.av.videomode[port] = ConfigSelection(choices=[mode for (mode, rates) in modes])
			for (mode, rates) in modes:
				ratelist = []
				for rate in rates:
					if rate in ("auto"):
						if BoxInfo.getItem("has24hz"):
							ratelist.append((rate, mode == "2160p30" and "auto (25Hz 30Hz 24Hz)" or "auto (50Hz 60Hz 24Hz)"))
					else:
						ratelist.append((rate, rate == "multi" and (mode == "2160p30" and "multi (25Hz 30Hz)" or "multi (50Hz 60Hz)") or rate))
				config.av.videorate[mode] = ConfigSelection(choices=ratelist)
		config.av.videoport = ConfigSelection(choices=lst)

	def setConfiguredMode(self):
		port = config.av.videoport.value
		if port not in config.av.videomode:
			print("[Videomode] VideoHardware current port not available, not setting videomode")
			return

		mode = config.av.videomode[port].value

		if mode not in config.av.videorate:
			print("[Videomode] VideoHardware current mode not available, not setting videomode")
			return

		rate = config.av.videorate[mode].value
		self.setMode(port, mode, rate)

	def updateAspect(self, cfgelement):
		# determine aspect = {any,4:3,16:9,16:10}
		# determine policy = {bestfit,letterbox,panscan,nonlinear}

		# based on;
		#   config.av.videoport.value: current video output device
		#     Scart:
		#   config.av.aspect:
		#     4_3:            use policy_169
		#     16_9,16_10:     use policy_43
		#     auto            always "bestfit"
		#   config.av.policy_169
		#     letterbox       use letterbox
		#     panscan         use panscan
		#     scale           use bestfit
		#   config.av.policy_43
		#     pillarbox       use panscan
		#     panscan         use letterbox  ("panscan" is just a bad term, it's inverse-panscan)
		#     nonlinear       use nonlinear
		#     scale           use bestfit

		port = config.av.videoport.value
		if port not in config.av.videomode:
			print("[Videomode] VideoHardware current port not available, not setting videomode")
			return
		mode = config.av.videomode[port].value

		force_widescreen = self.isWidescreenMode(port, mode)

		is_widescreen = force_widescreen or config.av.aspect.value in ("16_9", "16_10")
		is_auto = config.av.aspect.value == "auto"
		policy2 = "policy"  # use main policy

		if is_widescreen:
			if force_widescreen:
				aspect = "16:9"
			else:
				aspect = {"16_9": "16:9", "16_10": "16:10"}[config.av.aspect.value]
			policy_choices = {"pillarbox": "panscan", "panscan": "letterbox", "nonlinear": "nonlinear", "scale": "bestfit", "full": "full", "auto": "auto"}
			policy = policy_choices[config.av.policy_43.value]
			policy2_choices = {"letterbox": "letterbox", "panscan": "panscan", "scale": "bestfit", "full": "full", "auto": "auto"}
			policy2 = policy2_choices[config.av.policy_169.value]
		elif is_auto:
			aspect = "any"
			if "auto" in config.av.policy_43.choices:
				policy = "auto"
			else:
				policy = "bestfit"
		else:
			aspect = "4:3"
			policy = {"letterbox": "letterbox", "panscan": "panscan", "scale": "bestfit", "full": "full", "auto": "auto"}[config.av.policy_169.value]

		if not config.av.wss.value:
			wss = "auto(4:3_off)"
		else:
			wss = "auto"

		print("[Videomode] VideoHardware -> setting aspect, policy, policy2, wss", aspect, policy, policy2, wss)
		try:
			open("/proc/stb/video/aspect", "w").write(aspect)
		except Exception:
			print("[Videomode] Write to /proc/stb/video/aspect failed.")
		try:
			open("/proc/stb/video/policy", "w").write(policy)
		except Exception:
			print("[Videomode] Write to /proc/stb/video/policy failed.")
		try:
			open("/proc/stb/denc/0/wss", "w").write(wss)
		except Exception:
			print("[Videomode] Write to /proc/stb/denc/0/wss failed.")
		try:
			open("/proc/stb/video/policy2", "w").write(policy2)
		except Exception:
			print("[Videomode] Write to /proc/stb/video/policy2 failed.")


VIDEO = VideoHardware()
VIDEO.setConfiguredMode()
