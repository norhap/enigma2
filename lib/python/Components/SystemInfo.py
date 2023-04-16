# -*- coding: utf-8 -*-
from os.path import isfile, join as pathjoin
from re import findall

from boxbranding import getDisplayType, getHaveHDMIinFHD, getHaveHDMIinHD, getHaveAVJACK, getHaveSCART, getHaveYUV, getHaveSCARTYUV, getHaveRCA, getHaveTranscoding, getHaveMultiTranscoding, getHaveHDMI, getRCIDNum, getRCName, getRCType, getHaveVFDSymbol, getSoCFamily, getMachineMtdKernel, getMachineName
from enigma import Misc_Options, eDVBCIInterfaces, eDVBResourceManager, eGetEnigmaDebugLvl, getPlatform

from Tools.Directories import SCOPE_SKINS, SCOPE_LIBDIR, fileCheck, fileExists, fileHas, fileReadLines, pathExists, resolveFilename
from Tools.StbHardware import getWakeOnLANType

SystemInfo = {}


class BoxInformation:
	def __init__(self, root=""):
		self.immutableList = []
		self.boxInfo = {}
		file = root + pathjoin(resolveFilename(SCOPE_LIBDIR), "enigma.info")
		self.boxInfo["overrideactive"] = False  # not currently used by us
		lines = fileReadLines(file)
		if lines:
			for line in lines:
				if line.startswith("#") or line.strip() == "" or line.strip().lower().startswith("checksum") or "=" not in line:
					continue
				item, value = [x.strip() for x in line.split("=", 1)]
				if item:
					self.immutableList.append(item)
					# Temporary fix: some items that look like floats are not floats and should be handled as strings, e.g. python "3.10" should not be processed as "3.1".
					if not (value.startswith("\"") or value.startswith("'")) and item in ("python", "imageversion", "imgversion"):
						value = '"' + value + '"'  # wrap it so it is treated as a string
					self.boxInfo[item] = self.processValue(value)
			# print("[SystemInfo] Enigma information file data loaded into BoxInfo.")
		else:
			print("[BoxInfo] ERROR: %s is not available!  The system is unlikely to boot or operate correctly." % file)

	def processValue(self, value):
		if value is None:
			pass
		elif (value.startswith("\"") or value.startswith("'")) and value.endswith(value[0]):
			value = value[1:-1]
		elif value.startswith("(") and value.endswith(")"):
			data = []
			for item in [x.strip() for x in value[1:-1].split(",")]:
				data.append(self.processValue(item))
			value = tuple(data)
		elif value.startswith("[") and value.endswith("]"):
			data = []
			for item in [x.strip() for x in value[1:-1].split(",")]:
				data.append(self.processValue(item))
			value = list(data)
		elif value.upper() == "NONE":
			value = None
		elif value.upper() in ("FALSE", "NO", "OFF", "DISABLED"):
			value = False
		elif value.upper() in ("TRUE", "YES", "ON", "ENABLED"):
			value = True
		elif value.isdigit() or ((value[0:1] == "-" or value[0:1] == "+") and value[1:].isdigit()):
			if value[0] != "0":  # if this is zero padded it must be a string, so skip
				value = int(value)
		elif value.startswith("0x") or value.startswith("0X"):
			value = int(value, 16)
		elif value.startswith("0o") or value.startswith("0O"):
			value = int(value, 8)
		elif value.startswith("0b") or value.startswith("0B"):
			value = int(value, 2)
		else:
			try:
				value = float(value)
			except ValueError:
				pass
		return value

	def getEnigmaInfoList(self):
		return sorted(self.immutableList)

	def getEnigmaConfList(self):  # not used by us
		return []

	def getItemsList(self):
		return sorted(list(self.boxInfo.keys()))

	def getItem(self, item, default=None):
		if item in self.boxInfo:
			value = self.boxInfo[item]
		elif item in SystemInfo:
			value = SystemInfo[item]
		else:
			value = default
		return value

	def setItem(self, item, value, immutable=False, forceOverride=False):
		if item in self.immutableList and not forceOverride:
			print("[BoxInfo] Error: Item '%s' is immutable and can not be %s!" % (item, "changed" if item in self.boxInfo else "added"))
			return False
		if immutable and item not in self.immutableList:
			self.immutableList.append(item)
		self.boxInfo[item] = value
		SystemInfo[item] = value
		return True

	def deleteItem(self, item):
		if item in self.immutableList:
			print("[BoxInfo] Error: Item '%s' is immutable and can not be deleted!" % item)
		elif item in self.boxInfo:
			del self.boxInfo[item]
			return True
		return False


BoxInfo = BoxInformation()

MODEL = BoxInfo.getItem("model")
DISPLAYMODEL = getMachineName()
BRAND = BoxInfo.getItem("displaybrand")
PLATFORM = getPlatform()
ARCHITECTURE = BoxInfo.getItem("architecture")
SOC_FAMILY = BoxInfo.getItem("socfamily")
DISPLAYTYPE = BoxInfo.getItem("displaytype")
MTDROOTFS = BoxInfo.getItem("mtdrootfs")
DISPLAYBRAND = BoxInfo.getItem("displaybrand")
MACHINEBUILD = BoxInfo.getItem("machinebuild")


SystemInfo["HasUsbhdd"] = {}
SystemInfo["HasRootSubdir"] = False
SystemInfo["HasMultibootMTD"] = False
SystemInfo["HasKexecUSB"] = False
SystemInfo["RecoveryMode"] = False
from Tools.Multiboot import getMultibootStartupDevice, getMultibootslots  # This import needs to be here to avoid a SystemInfo load loop!


def getBoxDisplayName():  # This function returns a tuple like ("BRANDNAME", "BOXNAME")
	return (DISPLAYBRAND, DISPLAYMODEL)


# Parse the boot commandline.
from os.path import isfile
if (isfile("/proc/cmdline")):
	with open("/proc/cmdline", "r") as fd:
		cmdline = fd.read()
	cmdline = {k: v.strip('"') for k, v in findall(r'(\S+)=(".*?"|\S+)', cmdline)}


def getRCFile(ext):
	filename = resolveFilename(SCOPE_SKINS, pathjoin("rc_models", "%s.%s" % (getRCName(), ext)))
	if not isfile(filename):
		filename = resolveFilename(SCOPE_SKINS, pathjoin("rc_models", "dmm1.%s" % ext))
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
SystemInfo["RCIDNum"] = int(float(2)) or int(getRCIDNum())
SystemInfo["RCName"] = getRCName()
SystemInfo["RCImage"] = getRCFile("png")
SystemInfo["RCMapping"] = getRCFile("xml")
SystemInfo["RemoteEnable"] = MODEL in ("dm800",)

if MODEL in ("maram9", "axodin"):
	repeat = 400
else:
	repeat = 100
SystemInfo["RemoteRepeat"] = repeat
SystemInfo["RemoteDelay"] = 200 if MODEL in ("maram9", "axodin") else 700

SystemInfo["InDebugMode"] = eGetEnigmaDebugLvl() >= 4
SystemInfo["CommonInterface"] = MODEL in ("h9combo", "h9combose", "h10", "pulse4kmini") and 1 or eDVBCIInterfaces.getInstance().getNumOfSlots()
SystemInfo["CommonInterfaceCIDelay"] = fileCheck("/proc/stb/tsmux/rmx_delay")
for cislot in range(0, SystemInfo["CommonInterface"]):
	SystemInfo["CI%dSupportsHighBitrates" % cislot] = fileCheck("/proc/stb/tsmux/ci%d_tsclk" % cislot)
	SystemInfo["CI%dRelevantPidsRoutingSupport" % cislot] = fileCheck("/proc/stb/tsmux/ci%d_relevant_pids_routing" % cislot)
SystemInfo["HasSoftcamInstalled"] = hassoftcaminstalled()
SystemInfo["NumVideoDecoders"] = getNumVideoDecoders()
SystemInfo["Udev"] = not fileExists("/dev/.devfsd")
SystemInfo["PIPAvailable"] = MODEL != "i55plus" and SystemInfo["NumVideoDecoders"] > 1
SystemInfo["CanMeasureFrontendInputPower"] = eDVBResourceManager.getInstance().canMeasureFrontendInputPower()
SystemInfo["12V_Output"] = Misc_Options.getInstance().detected_12V_output()
SystemInfo["ZapMode"] = fileCheck("/proc/stb/video/zapmode") or fileCheck("/proc/stb/video/zapping_mode")
SystemInfo["NumFrontpanelLEDs"] = countFrontpanelLEDs()
SystemInfo["FrontpanelDisplay"] = fileExists("/dev/dbox/oled0") or fileExists("/dev/dbox/lcd0")
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
SystemInfo["ConfigDisplay"] = SystemInfo["FrontpanelDisplay"] and "7segment" not in getDisplayType()
SystemInfo["7segment"] = "7segment" in getDisplayType()
SystemInfo["textlcd"] = "textlcd" in getDisplayType() and "7segment" not in getDisplayType()
SystemInfo["VFDRepeats"] = BRAND != "ixuss" and "textlcd 7segment" not in getDisplayType()
SystemInfo["VFD_scroll_repeats"] = MODEL != "et8500" and fileCheck("/proc/stb/lcd/scroll_repeats")
SystemInfo["VFD_scroll_delay"] = MODEL != "et8500" and fileCheck("/proc/stb/lcd/scroll_delay")
SystemInfo["VFD_initial_scroll_delay"] = MODEL != "et8500" and fileCheck("/proc/stb/lcd/initial_scroll_delay")
SystemInfo["VFD_final_scroll_delay"] = MODEL != "et8500" and fileCheck("/proc/stb/lcd/final_scroll_delay")
SystemInfo["VFDSymbols"] = getHaveVFDSymbol() == "True"
SystemInfo["LcdLiveTV"] = fileCheck("/proc/stb/fb/sd_detach") or fileCheck("/proc/stb/lcd/live_enable")
SystemInfo["LcdLiveTVMode"] = fileCheck("/proc/stb/lcd/mode")
SystemInfo["LcdLiveDecoder"] = fileCheck("/proc/stb/lcd/live_decoder")
SystemInfo["LedPowerColor"] = fileCheck("/proc/stb/fp/ledpowercolor")
SystemInfo["LedStandbyColor"] = fileCheck("/proc/stb/fp/ledstandbycolor")
SystemInfo["LedSuspendColor"] = fileCheck("/proc/stb/fp/ledsuspendledcolor")
SystemInfo["Power4x7On"] = fileCheck("/proc/stb/fp/power4x7on")
SystemInfo["Power4x7Standby"] = fileCheck("/proc/stb/fp/power4x7standby")
SystemInfo["Power4x7Suspend"] = fileCheck("/proc/stb/fp/power4x7suspend")
SystemInfo["MaxPIPSize"] = MODEL in ("hd51", "h7", "vs1500", "e4hdultra") and (360, 288) or (540, 432)
SystemInfo["WakeOnLAN"] = fileCheck("/proc/stb/power/wol") or fileCheck("/proc/stb/fp/wol")
SystemInfo["WakeOnLANType"] = getWakeOnLANType(SystemInfo["WakeOnLAN"]) if SystemInfo["WakeOnLAN"] else False
SystemInfo["HasExternalPIP"] = PLATFORM != "1genxt" and fileCheck("/proc/stb/vmpeg/1/external")
SystemInfo["VideoDestinationConfigurable"] = fileExists("/proc/stb/vmpeg/0/dst_left")
SystemInfo["hasPIPVisibleProc"] = fileCheck("/proc/stb/vmpeg/1/visible")
SystemInfo["FastChannelChange"] = False
SystemInfo["3DMode"] = fileCheck("/proc/stb/fb/3dmode") or fileCheck("/proc/stb/fb/primary/3d")
SystemInfo["3DZNorm"] = fileCheck("/proc/stb/fb/znorm") or fileCheck("/proc/stb/fb/primary/zoffset")
SystemInfo["HasMMC"] = "root" in cmdline and cmdline["root"].startswith("/dev/mmcblk") if (isfile("/proc/cmdline")) else "mmcblk" in getMachineMtdKernel()
SystemInfo["Blindscan_t2_available"] = fileCheck("/proc/stb/info/vumodel") and MODEL.startswith("vu")
SystemInfo["CanProc"] = SystemInfo["HasMMC"] and BRAND != "vuplus"
SystemInfo["RcTypeChangable"] = not (MODEL in ("gbquad4k", "gbue4k", "et8500") or MODEL.startswith("et7")) and pathExists("/proc/stb/ir/rc/type")
SystemInfo["HasFullHDSkinSupport"] = MODEL not in ("et4000", "et5000", "sh1", "hd500c", "hd1100", "xp1000", "lc")
SystemInfo["HasTranscoding"] = getHaveTranscoding() == "True" or getHaveMultiTranscoding() == "True" or pathExists("/proc/stb/encoder/0") or fileCheck("/dev/bcm_enc0")
SystemInfo["HasH265Encoder"] = fileHas("/proc/stb/encoder/0/vcodec_choices", "h265")
SystemInfo["CanNotDoSimultaneousTranscodeAndPIP"] = MODEL in ("vusolo4k", "gbquad4k", "gbue4k")
SystemInfo["HasFrontDisplayPicon"] = MODEL in ("et8500", "vusolo4k", "vuuno4kse", "vuduo4k", "vuduo4kse", "vuultimo4k", "gbquad4k", "gbue4k")
SystemInfo["Has24hz"] = fileCheck("/proc/stb/video/videomode_24hz")
SystemInfo["HDMICEC"] = fileExists("/dev/cec0") or fileExists("/dev/hdmi_cec") or fileExists("/dev/misc/hdmi_cec0")
SystemInfo["HasHDMIHDin"] = getHaveHDMIinHD() == "True"
SystemInfo["HasHDMIFHDin"] = getHaveHDMIinFHD() == "True"
SystemInfo["HasHDMIin"] = SystemInfo["HasHDMIHDin"] or SystemInfo["HasHDMIFHDin"]
SystemInfo["HasComposite"] = getHaveRCA() == "True"
SystemInfo["HasJack"] = getHaveAVJACK() == "True"
SystemInfo["HasScart"] = getHaveSCART() == "True"
SystemInfo["HasScartYUV"] = getHaveSCARTYUV() == "True"
SystemInfo["HasSVideo"] = MODEL in ("dm8000")
SystemInfo["HasYPbPr"] = getHaveYUV() == "True"
SystemInfo["CanAutoVolume"] = fileHas("/proc/stb/audio/avl_choices", "none") or fileHas("/proc/stb/audio/avl_choices", "hdmi")
SystemInfo["CanAutoVolumeLevel"] = fileExists("/proc/stb/audio/autovolumelevel_choices") and fileCheck("/proc/stb/audio/autovolumelevel")
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
SystemInfo["canFlashWithOfgwrite"] = BRAND != "dreambox"
SystemInfo["BootDevice"] = getBootdevice()
SystemInfo["FbcTunerPowerAlwaysOn"] = MODEL in ("vusolo4k", "vuduo4k", "vuduo4kse", "vuultimo4k", "vuuno4k", "vuuno4kse")
SystemInfo["HasPhysicalLoopthrough"] = ["Vuplus DVB-S NIM(AVL2108)", "GIGA DVB-S2 NIM (Internal)"]
SystemInfo["HasFBCtuner"] = ["Vuplus DVB-C NIM(BCM3158)", "Vuplus DVB-C NIM(BCM3148)", "Vuplus DVB-S NIM(7376 FBC)", "Vuplus DVB-S NIM(45308X FBC)", "Vuplus DVB-S NIM(45208 FBC)", "DVB-S2 NIM(45208 FBC)", "DVB-S2X NIM(45308X FBC)", "DVB-S2 NIM(45308 FBC)", "DVB-C NIM(3128 FBC)", "BCM45208", "BCM45308X", "BCM3158"]
SystemInfo["HaveCISSL"] = fileCheck("/etc/ssl/certs/customer.pem") and fileCheck("/etc/ssl/certs/device.pem")
SystemInfo["CanChangeOsdAlpha"] = fileCheck("/proc/stb/video/alpha")
SystemInfo["ScalerSharpness"] = fileExists("/proc/stb/vmpeg/0/pep_scaler_sharpness")
SystemInfo["OScamInstalled"] = fileExists("/usr/bin/oscam") or fileExists("/usr/bin/oscam-emu") or fileExists("/usr/bin/oscam-trunk")
SystemInfo["OScamIsActive"] = fileExists("/var/tmp/.oscam")
SystemInfo["NCamInstalled"] = fileExists("/usr/bin/ncam")
SystemInfo["NCamIsActive"] = fileExists("/var/tmp/.ncam")
SystemInfo["CCcamIsActive"] = fileHas("/tmp/ecm.info", "CCcam-s2s") or fileHas("/tmp/ecm.info", "fta")
SystemInfo["HiSilicon"] = pathExists("/proc/hisi") or fileExists("/usr/bin/hihalt")
SystemInfo["DefineSat"] = MODEL in ("ustym4kpro", "beyonwizv2", "viper4k", "sf8008", "gbtrio4k", "gbtrio4kplus", "gbip4k", "qviart5")
SystemInfo["RecoveryMode"] = fileCheck("/proc/stb/fp/boot_mode") and MODEL not in ("hd51", "h7") or getSoCFamily() in ("hisi3798mv200",)
SystemInfo["AndroidMode"] = SystemInfo["RecoveryMode"] and MODEL == "multibox" or BRAND in ("wetek", "dreambox")
SystemInfo["grautec"] = fileExists("/tmp/usbtft")
SystemInfo["GraphicLCD"] = MODEL in ("vuultimo", "xpeedlx3", "et10000", "hd2400", "sezammarvel", "atemionemesis", "mbultra", "beyonwizt4", "osmio4kplus")
SystemInfo["LCDMiniTV"] = fileExists("/proc/stb/lcd/mode")
SystemInfo["LCDMiniTVPiP"] = SystemInfo["LCDMiniTV"] and MODEL not in ("gb800ueplus", "gbquad4k", "gbue4k")
SystemInfo["DefaultDisplayBrightness"] = PLATFORM == "dm4kgen" and 8 or 5
SystemInfo["DreamBoxAudio"] = PLATFORM == "dm4kgen" or MODEL in ("dm7080", "dm800")
SystemInfo["VFDDelay"] = MODEL in ("sf4008", "beyonwizu4")
SystemInfo["FirstCheckModel"] = MODEL in ("tmtwin4k", "mbmicrov2", "revo4k", "force3uhd", "mbmicro", "e4hd", "e4hdhybrid", "valalinux", "lunix", "tmnanom3", "purehd", "force2nano", "purehdse") or BRAND in ("linkdroid", "wetek")
SystemInfo["SecondCheckModel"] = MODEL in ("osninopro", "osnino", "osninoplus", "dm7020hd", "dm7020hdv2", "9910lx", "9911lx", "9920lx", "tmnanose", "tmnanoseplus", "tmnanosem2", "tmnanosem2plus", "tmnanosecombo", "force2plus", "force2", "force2se", "optimussos", "fusionhd", "fusionhdse", "force2plushv") or BRAND == "ixuss"
SystemInfo["DifferentLCDSettings"] = MODEL in ("spycat4kmini", "osmega")
SystemInfo["ArchIsARM64"] = ARCHITECTURE == "aarch64" or "64" in ARCHITECTURE
SystemInfo["ArchIsARM"] = ARCHITECTURE.startswith(("arm", "cortex"))
SystemInfo["SeekStatePlay"] = False
SystemInfo["StatePlayPause"] = False
SystemInfo["StandbyState"] = False
SystemInfo["LEDButtons"] = False
SystemInfo["HasH9SD"] = MODEL in ("h9", "i55plus") and pathExists("/dev/mmcblk0p1")
SystemInfo["HasSDnomount"] = MODEL in ("h9", "h3", "i55plus") and (False, "none") or MODEL in ("multibox", "h9combo", "h3") and (True, "mmcblk0")
SystemInfo["canBackupEMC"] = MODEL in ("hd51", "vs1500", "h7", "8100s") and ("disk.img", "%s" % SystemInfo["MultibootStartupDevice"]) or MODEL in ("xc7439", "osmio4k", "osmio4kplus", "osmini4k") and ("emmc.img", "%s" % SystemInfo["MultibootStartupDevice"]) or SystemInfo["DefineSat"] and ("usb_update.bin", "none") or MODEL in ("cc1", "sx988", "ip8", "ustym4kottpremium", "og2ott4k", "sx88v2") and ("usb_update.bin", "none")
SystemInfo["FrontpanelLEDBlinkControl"] = fileExists("/proc/stb/fp/led_blink")
SystemInfo["FrontpanelLEDBrightnessControl"] = fileExists("/proc/stb/fp/led_brightness")
SystemInfo["FrontpanelLEDColorControl"] = fileExists("/proc/stb/fp/led_color")
SystemInfo["FrontpanelLEDFadeControl"] = fileExists("/proc/stb/fp/led_fade")
SystemInfo["FCCactive"] = False
