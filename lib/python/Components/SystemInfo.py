from ast import literal_eval
from os.path import isfile, join
from re import findall
from hashlib import md5
from boxbranding import getMachineName
from enigma import Misc_Options, eAVControl, eDVBCIInterfaces, eDVBResourceManager, eGetEnigmaDebugLvl, getPlatform, eDBoxLCD, getBoxType

from process import ProcessList
from Tools.Directories import SCOPE_SKINS, SCOPE_LIBDIR, scopeLCDSkin, fileCheck, fileExists, fileHas, fileReadLines, pathExists, resolveFilename
from Tools.StbHardware import getWakeOnLANType


class BoxInformation:
	def __init__(self, root=""):
		self.immutableList = []
		self.boxInfo = {}
		file = root + join(resolveFilename(SCOPE_LIBDIR), "enigma.info")
		self.boxInfo["overrideactive"] = False  # not currently used by us
		self.boxInfo["checksumerror"] = True
		lines = fileReadLines(file)
		if lines:
			for line in lines:
				if line.startswith("#") or line.strip() == "" or "=" not in line:
					continue
				item, value = [x.strip() for x in line.split("=", 1)]
				if item.lower() == "checksum":
					self.boxInfo["checksumerror"] = (i := lines.index(line)) < 1 or md5(bytearray("\n".join(lines[:i]) + "\n", "UTF-8", errors="ignore")).hexdigest() != value
				elif item:
					self.setItem(item, self.processValue(value), immutable=True)
			if self.boxInfo["checksumerror"]:
				print(f"[BoxInfo] Data integrity of {file} could not be verified.")
		else:
			print(f"[BoxInfo] ERROR: {file} is not available!  The system is unlikely to boot or operate correctly.")

	def processValue(self, value):
		try:
			return literal_eval(value)
		except Exception:
			return value

	def getEnigmaInfoList(self):
		return sorted(self.immutableList)

	def getEnigmaConfList(self):  # not used by us
		return []

	def getItemsList(self):
		return sorted(list(self.boxInfo.keys()))

	def getItem(self, item, default=None):
		return self.boxInfo.get(item, default)

	def setItem(self, item, value, immutable=False):
		if item in self.immutableList:
			print(f"[BoxInfo] Error: Item '{item}' is immutable and can not be {'changed' if item in self.boxInfo else 'added'}!")
			return False
		if immutable:
			self.immutableList.append(item)
		self.boxInfo[item] = value
		return True

	def setMutableItem(self, item, value):
		self.boxInfo[item] = value

	def deleteItem(self, item):
		if item in self.immutableList:
			print(f"[BoxInfo] Error: Item '{item}' is immutable and can not be deleted!")
		elif item in self.boxInfo:
			del self.boxInfo[item]
			return True
		return False


BoxInfo = BoxInformation()


class SystemInformation(dict):
	def __getitem__(self, item):
		return BoxInfo.boxInfo[item]

	def __setitem__(self, item, value):
		if item in BoxInfo.immutableList:
			print(f"[SystemInfo] Error: Item '{item}' is immutable and can not be {'changed' if item in BoxInfo.boxInfo else 'added'}!")
		else:
			BoxInfo.boxInfo[item] = value

	def __delitem__(self, item):
		if item in BoxInfo.immutableList:
			print(f"[SystemInfo] Error: Item '{item}' is immutable and can not be deleted!")
		else:
			del BoxInfo.boxInfo[item]

	def get(self, item, default=None):
		return BoxInfo.boxInfo[item] if item in BoxInfo.boxInfo else default


SystemInfo = SystemInformation()

MODEL = BoxInfo.getItem("model")
DISPLAYMODEL = getMachineName()
DISPLAYTYPE = BoxInfo.getItem("displaytype")
BRAND = BoxInfo.getItem("displaybrand")
PLATFORM = getPlatform()
ARCHITECTURE = BoxInfo.getItem("architecture")
MTDROOTFS = BoxInfo.getItem("mtdrootfs")
DISPLAYBRAND = BoxInfo.getItem("displaybrand")
MACHINEBUILD = BoxInfo.getItem("machinebuild")

SystemInfo["HasUsbhdd"] = {}
SystemInfo["HasRootSubdir"] = False
SystemInfo["HasMultibootMTD"] = False
SystemInfo["HasKexecUSB"] = False
SystemInfo["RecoveryMode"] = False
SystemInfo["SeekStatePlay"] = False
SystemInfo["StatePlayPause"] = False
SystemInfo["StandbyState"] = False
SystemInfo["FCCactive"] = False
from Tools.Multiboot import getMultibootStartupDevice, getMultibootslots  # noqa: E402 module level import not at top of file


def getBoxDisplayName():  # This function returns a tuple like ("BRANDNAME", "BOXNAME")
	return (DISPLAYBRAND, DISPLAYMODEL)


# Parse the boot commandline.
if (isfile("/proc/cmdline")):
	with open("/proc/cmdline", "r") as fd:
		cmdline = fd.read()
	cmdline = {k: v.strip('"') for k, v in findall(r'(\S+)=(".*?"|\S+)', cmdline)}


def getRCFile(ext):
	filename = resolveFilename(SCOPE_SKINS, join("rc_models", "%s.%s" % (BoxInfo.getItem("rcname"), ext)))
	if not isfile(filename):
		filename = resolveFilename(SCOPE_SKINS, join("rc_models", "dmm1.%s" % ext))
	return filename


def getNumVideoDecoders():
	numVideoDecoders = 0
	while fileExists("/dev/dvb/adapter0/video%d" % numVideoDecoders, "f"):
		numVideoDecoders += 1
	return numVideoDecoders


def countFrontpanelLEDs():
	numLeds = fileExists("/proc/stb/fp/led_set_pattern") and 1 or 0
	while fileExists("/proc/stb/fp/led%d_pattern" % numLeds):
		numLeds += 1
	return numLeds


def hassoftcaminstalled():
	softcams = fileExists("/etc/init.d/softcam") or fileExists("/etc/init.d/cardserver")
	return softcams


def getBootdevice():
	dev = ("root" in cmdline and cmdline["root"].startswith("/dev/")) and cmdline["root"][5:]
	while dev and not fileExists("/sys/block/%s" % dev):
		dev = dev[:-1]
	return dev


SystemInfo["ArchIsARM"] = ARCHITECTURE.startswith(("arm", "cortex"))
SystemInfo["ArchIsARM64"] = "64" in ARCHITECTURE

# detect remote control
# SystemInfo["RCType"] = getRCType() detect from boxbranding
# SystemInfo["RCIDNum"] = int(float(2)) or int(BoxInfo.getItem("rcidnum"))
BoxInfo.setItem("RCImage", getRCFile("png"))
BoxInfo.setItem("RCMapping", getRCFile("xml"))
BoxInfo.setItem("RemoteEnable", MODEL == "dm800")
BoxInfo.setItem("RemoteRepeat", 100)
BoxInfo.setItem("RemoteDelay", 700)
BoxInfo.setItem("have24hz", eAVControl.getInstance().has24hz())
BoxInfo.setItem("hashdmiin", BoxInfo.getItem("hdmifhdin") or BoxInfo.getItem("hdmihdin"))
BoxInfo.setItem("MiniTV", fileCheck("/proc/stb/fb/sd_detach") or fileCheck("/proc/stb/lcd/live_enable"))
BoxInfo.setItem("StreamRelay", False)
BoxInfo.setItem("WakeOnLAN", fileCheck("/proc/stb/power/wol") or fileCheck("/proc/stb/fp/wol"))
BoxInfo.setItem("WakeOnLANType", getWakeOnLANType(BoxInfo.getItem("WakeOnLAN")) if BoxInfo.getItem("WakeOnLAN") else None)
BoxInfo.setItem("AISubs", fileExists("/etc/init.d/aisocket"))

SystemInfo["InDebugMode"] = eGetEnigmaDebugLvl() >= 4
SystemInfo["CommonInterface"] = MODEL in ("h9combo", "h9combose", "h10", "pulse4kmini") and 1 or eDVBCIInterfaces.getInstance().getNumOfSlots()
SystemInfo["CommonInterfaceCIDelay"] = fileCheck("/proc/stb/tsmux/rmx_delay")
for cislot in range(0, SystemInfo["CommonInterface"]):
	SystemInfo["CI%dSupportsHighBitrates" % cislot] = fileCheck("/proc/stb/tsmux/ci%d_tsclk" % cislot)
	SystemInfo["CI%dRelevantPidsRoutingSupport" % cislot] = fileCheck("/proc/stb/tsmux/ci%d_relevant_pids_routing" % cislot)
SystemInfo["HasSVideo"] = MODEL in ("dm8000")
SystemInfo["NimExceptionVuDuo2"] = MODEL == "vuduo2"
SystemInfo["NimExceptionDMM8000"] = SystemInfo["HasSVideo"]
SystemInfo["FbcTunerPowerAlwaysOn"] = MODEL in ("vusolo4k", "vuduo4k", "vuduo4kse", "vuultimo4k", "vuuno4k", "vuuno4kse")
SystemInfo["HasPhysicalLoopthrough"] = ["Vuplus DVB-S NIM(AVL2108)", "GIGA DVB-S2 NIM (Internal)"]
SystemInfo["HasFBCtuner"] = ["Vuplus DVB-C NIM(BCM3158)", "Vuplus DVB-C NIM(BCM3148)", "Vuplus DVB-S NIM(7376 FBC)", "Vuplus DVB-S NIM(45308X FBC)", "Vuplus DVB-S NIM(45208 FBC)", "DVB-S2 NIM(45208 FBC)", "DVB-S2X NIM(45308X FBC)", "DVB-S2 NIM(45308 FBC)", "DVB-C NIM(3128 FBC)", "BCM45208", "BCM45308X", "BCM3158"]
SystemInfo["HasSoftcamInstalled"] = hassoftcaminstalled()
SystemInfo["NumVideoDecoders"] = getNumVideoDecoders()
SystemInfo["Udev"] = not fileExists("/dev/.devfsd")
SystemInfo["PIPAvailable"] = MODEL != "i55plus" and SystemInfo["NumVideoDecoders"] > 1
SystemInfo["CanMeasureFrontendInputPower"] = eDVBResourceManager.getInstance().canMeasureFrontendInputPower()
SystemInfo["12V_Output"] = Misc_Options.getInstance().detected_12V_output()
SystemInfo["ZapMode"] = fileCheck("/proc/stb/video/zapmode") or fileCheck("/proc/stb/video/zapping_mode")
SystemInfo["NumFrontpanelLEDs"] = countFrontpanelLEDs()
SystemInfo["FrontpanelDisplay"] = fileExists(scopeLCDSkin) and fileExists("/dev/dbox/oled0") or fileExists(scopeLCDSkin) and fileExists("/dev/dbox/lcd0")
SystemInfo["DisplayLED"] = SystemInfo["FrontpanelDisplay"] and MODEL not in ("vusolo4k", "vuduo4k", "vuduo4kse", "vuultimo4k", "vuuno4k", "vuuno4kse", "atemionemesis")
SystemInfo["NoHaveFrontpanelDisplay"] = not fileExists(scopeLCDSkin)
SystemInfo["LCDsymbol_circle_recording"] = fileCheck("/proc/stb/lcd/symbol_circle") or MODEL in ("hd51", "vs1500") and fileCheck("/proc/stb/lcd/symbol_recording")
SystemInfo["LCDsymbol_timeshift"] = fileCheck("/proc/stb/lcd/symbol_timeshift")
SystemInfo["LCDshow_symbols"] = MODEL in ("et9x00", "hd51", "vs1500") and fileCheck("/proc/stb/lcd/show_symbols")
SystemInfo["LCDsymbol_hdd"] = MODEL in ("hd51", "vs1500") and fileCheck("/proc/stb/lcd/symbol_hdd")
SystemInfo["FrontpanelDisplayGrayscale"] = fileExists("/dev/dbox/oled0")
SystemInfo["DeepstandbySupport"] = MODEL != "dm800"
SystemInfo["Fan"] = fileCheck("/proc/stb/fp/fan")
SystemInfo["FanPWM"] = SystemInfo["Fan"] and fileCheck("/proc/stb/fp/fan_pwm")
SystemInfo["PowerLED"] = fileCheck("/proc/stb/power/powerled")
SystemInfo["PowerLED2"] = fileCheck("/proc/stb/power/powerled2")
SystemInfo["StandbyLED"] = fileCheck("/proc/stb/power/standbyled")
SystemInfo["SuspendLED"] = fileCheck("/proc/stb/power/suspendled")
SystemInfo["Display"] = SystemInfo["FrontpanelDisplay"] or SystemInfo["StandbyLED"]
SystemInfo["ConfigDisplay"] = SystemInfo["FrontpanelDisplay"] and "7segment" not in DISPLAYTYPE
SystemInfo["7segment"] = "7segment" in DISPLAYTYPE
SystemInfo["textlcd"] = "textlcd" in DISPLAYTYPE and "7segment" not in DISPLAYTYPE
SystemInfo["VFD_scroll_repeats"] = eDBoxLCD.getInstance().get_VFD_scroll_repeats()
SystemInfo["VFD_scroll_delay"] = eDBoxLCD.getInstance().get_VFD_scroll_delay()
SystemInfo["VFD_initial_scroll_delay"] = eDBoxLCD.getInstance().get_VFD_initial_scroll_delay()
SystemInfo["VFD_final_scroll_delay"] = eDBoxLCD.getInstance().get_VFD_final_scroll_delay()
SystemInfo["LcdLiveDecoder"] = fileCheck("/proc/stb/lcd/live_decoder")
SystemInfo["LedPowerColor"] = fileCheck("/proc/stb/fp/ledpowercolor")
SystemInfo["LedStandbyColor"] = fileCheck("/proc/stb/fp/ledstandbycolor")
SystemInfo["LedSuspendColor"] = fileCheck("/proc/stb/fp/ledsuspendledcolor")
SystemInfo["Power4x7On"] = fileCheck("/proc/stb/fp/power4x7on")
SystemInfo["Power4x7Standby"] = fileCheck("/proc/stb/fp/power4x7standby")
SystemInfo["Power4x7Suspend"] = fileCheck("/proc/stb/fp/power4x7suspend")
SystemInfo["MaxPIPSize"] = MODEL in ("hd51", "h7", "vs1500", "e4hdultra") and (360, 288) or (540, 432)
SystemInfo["HasExternalPIP"] = PLATFORM != "1genxt" and fileCheck("/proc/stb/vmpeg/1/external")
SystemInfo["VideoDestinationConfigurable"] = fileExists("/proc/stb/vmpeg/0/dst_left")
SystemInfo["hasPIPVisibleProc"] = fileCheck("/proc/stb/vmpeg/1/visible")
SystemInfo["3DMode"] = fileCheck("/proc/stb/fb/3dmode") or fileCheck("/proc/stb/fb/primary/3d")
SystemInfo["3DZNorm"] = fileCheck("/proc/stb/fb/znorm") or fileCheck("/proc/stb/fb/primary/zoffset")
SystemInfo["HasMMC"] = "root" in cmdline and cmdline["root"].startswith("/dev/mmcblk") if (isfile("/proc/cmdline")) else "mmcblk" in BoxInfo.getItem("mtdkernel")
SystemInfo["Blindscan_t2_available"] = fileCheck("/proc/stb/info/vumodel") and BRAND == "Vu+"
SystemInfo["RcTypeChangable"] = not (MODEL in ("gbquad4k", "gbue4k", "et8500") or MODEL.startswith("et7")) and pathExists("/proc/stb/ir/rc/type")
SystemInfo["HasFullHDSkinSupport"] = MODEL not in ("et4000", "et5000", "sh1", "hd500c", "hd1100", "xp1000", "lc")
SystemInfo["HasH265Encoder"] = fileHas("/proc/stb/encoder/0/vcodec_choices", "h265")
SystemInfo["CanNotDoSimultaneousTranscodeAndPIP"] = MODEL in ("vusolo4k", "gbquad4k", "gbue4k")
SystemInfo["HasFrontDisplayPicon"] = MODEL in ("et8500", "vusolo4k", "vuuno4kse", "vuduo4k", "vuduo4kse", "vuultimo4k", "gbquad4k", "gbue4k")
SystemInfo["HDMICEC"] = fileExists("/dev/cec0") or fileExists("/dev/hdmi_cec") or fileExists("/dev/misc/hdmi_cec0")
SystemInfo["CanAutoVolumeLevel"] = fileHas("/proc/stb/audio/avl_choices", "none") or fileHas("/proc/stb/audio/avl_choices", "hdmi")
SystemInfo["Can3DSurround"] = fileExists("/proc/stb/audio/3d_surround_choices") and fileCheck("/proc/stb/audio/3d_surround")
SystemInfo["Can3DSpeaker"] = fileExists("/proc/stb/audio/3d_surround_speaker_position_choices") and fileCheck("/proc/stb/audio/3d_surround_speaker_position")
SystemInfo["Can3DSurroundSpeaker"] = fileExists("/proc/stb/audio/3dsurround_choices") and fileCheck("/proc/stb/audio/3dsurround")
SystemInfo["Can3DSurroundSoftLimiter"] = fileExists("/proc/stb/audio/3dsurround_softlimiter_choices") and fileCheck("/proc/stb/audio/3dsurround_softlimiter")
SystemInfo["CanDownmixAC3"] = fileHas("/proc/stb/audio/ac3_choices", "downmix")
SystemInfo["CanDownmixDTS"] = fileHas("/proc/stb/audio/dts_choices", "downmix")
SystemInfo["CanDownmixAAC"] = fileHas("/proc/stb/audio/aac_choices", "downmix")
SystemInfo["CanAC3PlusTranscode"] = fileHas("/proc/stb/audio/ac3plus_choices", "force_ac3")
SystemInfo["CanAACTranscode"] = fileExists("/proc/stb/audio/aac_transcode_choices")
SystemInfo["CanDTSHD"] = fileExists("/proc/stb/audio/dtshd_choices")
SystemInfo["CanWMAPRO"] = fileExists("/proc/stb/audio/wmapro")
SystemInfo["CanDownmixAACPlus"] = fileExists("/proc/stb/audio/aacplus_choices")
SystemInfo["CanBTAudio"] = fileCheck("/proc/stb/audio/btaudio")
SystemInfo["CanBTAudioDelay"] = fileCheck("/proc/stb/audio/btaudio_delay") or fileCheck("/proc/stb/audio/btaudio_delay_pcm")
SystemInfo["HDMIAudioSource"] = fileCheck("/proc/stb/hdmi/audio_source")
SystemInfo["CanSyncMode"] = fileExists("/proc/stb/video/sync_mode_choices")
SystemInfo["HDRSupport"] = fileExists("/proc/stb/hdmi/hlg_support_choices") or fileCheck("/proc/stb/hdmi/hlg_support")
SystemInfo["Canedidchecking"] = fileCheck("/proc/stb/hdmi/bypass_edid_checking")
SystemInfo["havehdmicolorspace"] = fileCheck("/proc/stb/video/hdmi_colorspace")
SystemInfo["havehdmicolorspacechoices"] = fileCheck("/proc/stb/video/hdmi_colorspace_choices")
SystemInfo["havehdmicolorspacesimple"] = SystemInfo["havehdmicolorspace"] and MODEL in ("vusolo4k", "vuuno4k", "vuuno4kse", "vuultimo4k", "vuduo4k", "vuduo4kse")
SystemInfo["havehdmicolordepth"] = fileCheck("/proc/stb/video/hdmi_colordepth")
SystemInfo["havehdmicolordepthchoices"] = fileCheck("/proc/stb/video/hdmi_colordepth_choices")
SystemInfo["havehdmicolorimetry"] = fileCheck("/proc/stb/video/hdmi_colorimetry")
SystemInfo["havehdmicolorimetrychoices"] = fileCheck("/proc/stb/video/hdmi_colorimetry_choices")
SystemInfo["havehdmihdrtype"] = fileCheck("/proc/stb/video/hdmi_hdrtype")
SystemInfo["havehdmipreemphasis"] = fileCheck("/proc/stb/hdmi/preemphasis")
SystemInfo["supportPcmMultichannel"] = fileCheck("/proc/stb/audio/multichannel_pcm")
SystemInfo["hasXcoreVFD"] = MODEL == "osmega" or PLATFORM == "4kspycat" and fileCheck("/sys/module/brcmstb_%s/parameters/pt6302_cgram" % MODEL)
SystemInfo["HasOfflineDecoding"] = MODEL not in ("osmini", "osminiplus", "et7000mini", "et11000", "mbmicro", "mbtwinplus", "mbmicrov2", "et7x00", "et8500")
SystemInfo["hasKexec"] = fileHas("/proc/cmdline", "kexec=1")
SystemInfo["canKexec"] = MODEL in ("vusolo4k", "vuduo4k", "vuduo4kse", "vuultimo4k", "vuuno4k", "vuuno4kse", "vuzero4k") and not SystemInfo["hasKexec"] and fileExists("/usr/bin/kernel_auto.bin") and fileExists("/usr/bin/STARTUP.cpio.gz")
SystemInfo["MultibootStartupDevice"] = getMultibootStartupDevice()
SystemInfo["canMode12"] = "%s_4.boxmode" % MODEL in cmdline and cmdline["%s_4.boxmode" % MODEL] in ("1", "12") and "192M"
SystemInfo["canMultiBoot"] = getMultibootslots()
SystemInfo["canDualBoot"] = fileExists("/dev/block/by-name/flag")
SystemInfo["BootDevice"] = getBootdevice()
SystemInfo["HaveCISSL"] = fileCheck("/etc/ssl/certs/customer.pem") and fileCheck("/etc/ssl/certs/device.pem")
SystemInfo["CanChangeOsdAlpha"] = fileCheck("/proc/stb/video/alpha")
SystemInfo["ScalerSharpness"] = fileExists("/proc/stb/vmpeg/0/pep_scaler_sharpness")
SystemInfo["OSCamIsActive"] = str(ProcessList().named("oscam")).strip("[]") or str(ProcessList().named("oscam-emu")).strip("[]")
SystemInfo["NCamIsActive"] = str(ProcessList().named("ncam")).strip("[]")
SystemInfo["CCcamIsActive"] = str(ProcessList().named("CCcam")).strip("[]")
SystemInfo["HiSilicon"] = pathExists("/proc/hisi") or fileExists("/usr/bin/hihalt")
SystemInfo["DefineSat"] = MODEL in ("ustym4kpro", "beyonwizv2", "viper4k", "gbtrio4k", "gbtrio4kplus", "gbip4k", "qviart5") or getBoxType() in ("sf8008")
SystemInfo["RecoveryMode"] = fileCheck("/proc/stb/fp/boot_mode") and MODEL not in ("hd51", "h7")
SystemInfo["AndroidMode"] = SystemInfo["RecoveryMode"] and MODEL == "multibox" or BRAND in ("wetek", "dreambox")
SystemInfo["grautec"] = fileExists("/tmp/usbtft")
SystemInfo["GraphicLCD"] = MODEL in ("vuultimo", "xpeedlx3", "et10000", "hd2400", "sezammarvel", "atemionemesis", "mbultra", "beyonwizt4", "osmio4kplus")
SystemInfo["LcdLiveTV"] = fileCheck("/proc/stb/fb/sd_detach") or fileCheck("/proc/stb/lcd/live_enable")
SystemInfo["LCDMiniTV"] = fileExists("/proc/stb/lcd/mode")
SystemInfo["LCDMiniTVPiP"] = SystemInfo["LCDMiniTV"] and MODEL not in ("gb800ueplus", "gbquad4k", "gbue4k")
SystemInfo["DefaultDisplayBrightness"] = MODEL in ("dm900", "dm920") and 8 or 5
SystemInfo["DreamBoxAudio"] = MODEL in ("dm900", "dm920", "dm7080", "dm800")
SystemInfo["VFDDelay"] = MODEL in ("sf4008", "beyonwizu4")
SystemInfo["FirstCheckModel"] = MODEL in ("tmtwin4k", "mbmicrov2", "revo4k", "force3uhd", "mbmicro", "e4hd", "e4hdhybrid", "valalinux", "lunix", "tmnanom3", "purehd", "force2nano", "purehdse") or BRAND in ("linkdroid", "wetek")
SystemInfo["SecondCheckModel"] = MODEL in ("osninopro", "osnino", "osninoplus", "dm7020hd", "dm7020hdv2", "9910lx", "9911lx", "9920lx", "tmnanose", "tmnanoseplus", "tmnanosem2", "tmnanosem2plus", "tmnanosecombo", "force2plus", "force2", "force2se", "optimussos", "fusionhd", "fusionhdse", "force2plushv") or BRAND == "ixuss"
SystemInfo["DifferentLCDSettings"] = MODEL in ("spycat4kmini", "osmega")
SystemInfo["ArchIsARM64"] = ARCHITECTURE == "aarch64" or "64" in ARCHITECTURE
SystemInfo["ArchIsARM"] = ARCHITECTURE.startswith(("arm", "cortex"))
SystemInfo["HasH9SD"] = MODEL in ("h9", "i55plus") and pathExists("/dev/mmcblk0p1")
SystemInfo["HasSDnomount"] = MODEL in ("h9", "h3", "i55plus") and (False, "none") or MODEL in ("multibox", "h9combo", "h3") and (True, "mmcblk0")
SystemInfo["canBackupEMC"] = MODEL in ("hd51", "vs1500", "h7", "8100s") and ("disk.img", "%s" % SystemInfo["MultibootStartupDevice"]) or MODEL in ("xc7439", "osmio4k", "osmio4kplus", "osmini4k") and ("emmc.img", "%s" % SystemInfo["MultibootStartupDevice"]) or SystemInfo["DefineSat"] and ("usb_update.bin", "none") or MODEL in ("cc1", "sx988", "ip8", "ustym4kottpremium", "og2ott4k", "og2s4k", "sx88v2") and ("usb_update.bin", "none")
SystemInfo["FrontpanelLEDBlinkControl"] = fileExists("/proc/stb/fp/led_blink")
SystemInfo["FrontpanelLEDBrightnessControl"] = fileExists("/proc/stb/fp/led_brightness")
SystemInfo["FrontpanelLEDColorControl"] = fileExists("/proc/stb/fp/led_color")
SystemInfo["FrontpanelLEDFadeControl"] = fileExists("/proc/stb/fp/led_fade")
