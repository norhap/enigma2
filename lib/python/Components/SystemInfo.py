#!/usr/bin/python
# -*- coding: utf-8 -*-
from os import R_OK, access
from os.path import isfile, join as pathjoin
from re import findall

from boxbranding import getDisplayType, getImageArch, getHaveHDMIinFHD, getHaveHDMIinHD, getHaveAVJACK, getHaveSCART, getHaveYUV, getHaveSCARTYUV, getHaveRCA, getHaveWOL, getHaveTranscoding, getHaveMultiTranscoding, getHaveHDMI, getMachineBuild, getRCIDNum, getRCName, getRCType, getBoxType
from enigma import Misc_Options, eDVBCIInterfaces, eDVBResourceManager, eGetEnigmaDebugLvl

from Tools.Directories import SCOPE_SKIN, fileCheck, fileExists, fileHas, pathExists, resolveFilename
from Tools.StbHardware import getBrand

SystemInfo = {}
SystemInfo["HasRootSubdir"] = False

from Tools.Multiboot import getMultibootStartupDevice, getMultibootslots  # This import needs to be here to avoid a SystemInfo load loop!

# Parse the boot commandline.
print("[SystemInfo] Read /proc/cmdline")
with open("/proc/cmdline", "r") as fd:
	cmdline = fd.read()
cmdline = {k: v.strip('"') for k, v in findall(r'(\S+)=(".*?"|\S+)', cmdline)}


def getRCFile(ext):
	filename = resolveFilename(SCOPE_SKIN, pathjoin("rc_models", "%s.%s" % (getRCName(), ext)))
	if not isfile(filename):
		filename = resolveFilename(SCOPE_SKIN, pathjoin("rc_models", "dmm1.%s" % ext))
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


model = getBoxType()
brand = getBrand()
platform = getMachineBuild()
displaytype = getDisplayType()
architecture = getImageArch()

SystemInfo["MachineBrand"] = brand
SystemInfo["MachineModel"] = model
SystemInfo["MachineBuild"] = platform

#detect remote control
SystemInfo["RCCode"] = int(getRCType())
SystemInfo["RCTypeIndex"] = int(float(2)) or int(getRCIDNum())
SystemInfo["RCName"] = getRCName()
SystemInfo["RCImage"] = getRCFile("png")
SystemInfo["RCMapping"] = getRCFile("xml")
SystemInfo["RemoteEnable"] = model in ("dm800", "azboxhd")

if model in ("maram9", "axodin"):
	repeat = 400
elif model == "azboxhd":
	repeat = 150
else:
	repeat = 100
SystemInfo["RemoteRepeat"] = repeat
SystemInfo["RemoteDelay"] = 200 if model in ("maram9", "axodin") else 700

SystemInfo["InDebugMode"] = eGetEnigmaDebugLvl() >= 4
SystemInfo["CommonInterface"] = eDVBCIInterfaces.getInstance().getNumOfSlots()
SystemInfo["CommonInterfaceCIDelay"] = fileCheck("/proc/stb/tsmux/rmx_delay")
for cislot in range(0, SystemInfo["CommonInterface"]):
	SystemInfo["CI%dSupportsHighBitrates" % cislot] = fileCheck("/proc/stb/tsmux/ci%d_tsclk" % cislot)
	SystemInfo["CI%dRelevantPidsRoutingSupport" % cislot] = fileCheck("/proc/stb/tsmux/ci%d_relevant_pids_routing" % cislot)
SystemInfo["HasSoftcamInstalled"] = hassoftcaminstalled()
SystemInfo["NumVideoDecoders"] = getNumVideoDecoders()
SystemInfo["Udev"] = not fileExists("/dev/.devfsd")
SystemInfo["PIPAvailable"] = model != "i55plus" and SystemInfo["NumVideoDecoders"] > 1
SystemInfo["CanMeasureFrontendInputPower"] = eDVBResourceManager.getInstance().canMeasureFrontendInputPower()
SystemInfo["12V_Output"] = Misc_Options.getInstance().detected_12V_output()
SystemInfo["ZapMode"] = fileCheck("/proc/stb/video/zapmode") or fileCheck("/proc/stb/video/zapping_mode")
SystemInfo["NumFrontpanelLEDs"] = countFrontpanelLEDs()
SystemInfo["FrontpanelDisplay"] = fileExists("/dev/dbox/oled0") or fileExists("/dev/dbox/lcd0")
SystemInfo["LCDsymbol_circle_recording"] = fileCheck("/proc/stb/lcd/symbol_circle") or model in ("hd51","vs1500") and fileCheck("/proc/stb/lcd/symbol_recording")
SystemInfo["LCDsymbol_timeshift"] = fileCheck("/proc/stb/lcd/symbol_timeshift")
SystemInfo["LCDshow_symbols"] = model in ("et9x00","hd51","vs1500") and fileCheck("/proc/stb/lcd/show_symbols")
SystemInfo["LCDsymbol_hdd"] = model in ("hd51","vs1500") and fileCheck("/proc/stb/lcd/symbol_hdd")
SystemInfo["FrontpanelDisplayGrayscale"] = fileExists("/dev/dbox/oled0")
SystemInfo["DeepstandbySupport"] = model != "dm800"
SystemInfo["Fan"] = fileCheck("/proc/stb/fp/fan")
SystemInfo["FanPWM"] = SystemInfo["Fan"] and fileCheck("/proc/stb/fp/fan_pwm")
SystemInfo["PowerLED"] = fileCheck("/proc/stb/power/powerled")
SystemInfo["PowerLED2"] = fileCheck("/proc/stb/power/powerled2")
SystemInfo["StandbyLED"] = fileCheck("/proc/stb/power/standbyled")
SystemInfo["SuspendLED"] = fileCheck("/proc/stb/power/suspendled")
SystemInfo["Display"] = SystemInfo["FrontpanelDisplay"] or SystemInfo["StandbyLED"]
SystemInfo["LedPowerColor"] = fileCheck("/proc/stb/fp/ledpowercolor")
SystemInfo["LedStandbyColor"] = fileCheck("/proc/stb/fp/ledstandbycolor")
SystemInfo["LedSuspendColor"] = fileCheck("/proc/stb/fp/ledsuspendledcolor")
SystemInfo["Power4x7On"] = fileCheck("/proc/stb/fp/power4x7on")
SystemInfo["Power4x7Standby"] = fileCheck("/proc/stb/fp/power4x7standby")
SystemInfo["Power4x7Suspend"] = fileCheck("/proc/stb/fp/power4x7suspend")
SystemInfo["WakeOnLAN"] = fileCheck("/proc/stb/power/wol") or fileCheck("/proc/stb/fp/wol")
SystemInfo["HasExternalPIP"] = platform != "1genxt" and fileCheck("/proc/stb/vmpeg/1/external")
SystemInfo["VideoDestinationConfigurable"] = fileExists("/proc/stb/vmpeg/0/dst_left")
SystemInfo["hasPIPVisibleProc"] = fileCheck("/proc/stb/vmpeg/1/visible")
SystemInfo["MaxPIPSize"] = model in ("hd51","h7","vs1500","e4hdultra") and (360, 288) or (540, 432)
SystemInfo["VFD_scroll_repeats"] = model != "et8500" and fileCheck("/proc/stb/lcd/scroll_repeats")
SystemInfo["VFD_scroll_delay"] = model != "et8500" and fileCheck("/proc/stb/lcd/scroll_delay")
SystemInfo["VFD_initial_scroll_delay"] = model != "et8500" and fileCheck("/proc/stb/lcd/initial_scroll_delay")
SystemInfo["VFD_final_scroll_delay"] = model != "et8500" and fileCheck("/proc/stb/lcd/final_scroll_delay")
SystemInfo["LcdLiveTV"] = fileCheck("/proc/stb/fb/sd_detach") or fileCheck("/proc/stb/lcd/live_enable")
SystemInfo["LcdLiveTVMode"] = fileCheck("/proc/stb/lcd/mode")
SystemInfo["LcdLiveDecoder"] = fileCheck("/proc/stb/lcd/live_decoder")
SystemInfo["FastChannelChange"] = False
SystemInfo["3DMode"] = fileCheck("/proc/stb/fb/3dmode") or fileCheck("/proc/stb/fb/primary/3d")
SystemInfo["3DZNorm"] = fileCheck("/proc/stb/fb/znorm") or fileCheck("/proc/stb/fb/primary/zoffset")
SystemInfo["Blindscan_t2_available"] = fileCheck("/proc/stb/info/vumodel") and model.startswith("vu")
SystemInfo["RcTypeChangable"] = not(model.startswith("et8500") or model.startswith("et7")) and pathExists("/proc/stb/ir/rc/type")
SystemInfo["HasFullHDSkinSupport"] = model not in ("et4000", "et5000", "sh1", "hd500c", "hd1100", "xp1000", "lc")
SystemInfo["HasBypassEdidChecking"] = fileCheck("/proc/stb/hdmi/bypass_edid_checking")
SystemInfo["HasColorspace"] = fileCheck("/proc/stb/video/hdmi_colorspace")
SystemInfo["HasColorspaceSimple"] = SystemInfo["HasColorspace"] and model in ("vusolo4k","vuuno4k","vuuno4kse","vuultimo4k","vuduo4k","vuduo4kse")
SystemInfo["HasMultichannelPCM"] = fileCheck("/proc/stb/audio/multichannel_pcm")
SystemInfo["HasMMC"] = "root" in cmdline and cmdline["root"].startswith("/dev/mmcblk")
SystemInfo["HasTranscoding"] = getHaveTranscoding() == "True" or getHaveMultiTranscoding() == "True" or pathExists("/proc/stb/encoder/0") or fileCheck("/dev/bcm_enc0")
SystemInfo["HasH265Encoder"] = fileHas("/proc/stb/encoder/0/vcodec_choices","h265")
SystemInfo["CanNotDoSimultaneousTranscodeAndPIP"] = model in ("vusolo4k","gbquad4k")
SystemInfo["HasColordepth"] = fileCheck("/proc/stb/video/hdmi_colordepth")
SystemInfo["HasFrontDisplayPicon"] = model in ("et8500", "vusolo4k", "vuuno4kse", "vuduo4k", "vuduo4kse", "vuultimo4k")
SystemInfo["Has24hz"] = fileCheck("/proc/stb/video/videomode_24hz")
SystemInfo["HasHDMIpreemphasis"] = fileCheck("/proc/stb/hdmi/preemphasis")
SystemInfo["HasColorimetry"] = fileCheck("/proc/stb/video/hdmi_colorimetry")
SystemInfo["HasHdrType"] = fileCheck("/proc/stb/video/hdmi_hdrtype")
SystemInfo["HasHDMI-CEC"] = getHaveHDMI() == "True" or fileExists("/dev/cec0") or fileExists("/dev/hdmi_cec") or fileExists("/dev/misc/hdmi_cec0")
SystemInfo["HasHDMIHDin"] = getHaveHDMIinHD() == "True"
SystemInfo["HasHDMIFHDin"] = getHaveHDMIinFHD() == "True"
SystemInfo["HasHDMIin"] = SystemInfo["HasHDMIHDin"] or SystemInfo["HasHDMIFHDin"]
SystemInfo["HasComposite"] = getHaveRCA() == "True"
SystemInfo["HasJack"] = getHaveAVJACK() == "True"
SystemInfo["HasScart"] = getHaveSCART() == "True"
SystemInfo["HasScartYUV"] = getHaveSCARTYUV() == "True"
SystemInfo["HasSVideo"] = model in ("dm8000")
SystemInfo["HasYPbPr"] = getHaveYUV() == "True"
SystemInfo["HasAutoVolume"] = fileExists("/proc/stb/audio/avl_choices") and fileCheck("/proc/stb/audio/avl")
SystemInfo["HasAutoVolumeLevel"] = fileExists("/proc/stb/audio/autovolumelevel_choices") and fileCheck("/proc/stb/audio/autovolumelevel")
SystemInfo["Has3DSurround"] = fileExists("/proc/stb/audio/3d_surround_choices") and fileCheck("/proc/stb/audio/3d_surround")
SystemInfo["Has3DSpeaker"] = fileExists("/proc/stb/audio/3d_surround_speaker_position_choices") and fileCheck("/proc/stb/audio/3d_surround_speaker_position")
SystemInfo["Has3DSurroundSpeaker"] = fileExists("/proc/stb/audio/3dsurround_choices") and fileCheck("/proc/stb/audio/3dsurround")
SystemInfo["Has3DSurroundSoftLimiter"] = fileExists("/proc/stb/audio/3dsurround_softlimiter_choices") and fileCheck("/proc/stb/audio/3dsurround_softlimiter")
SystemInfo["hasXcoreVFD"] = model == "osmega" or platform == "4kspycat" and fileCheck("/sys/module/brcmstb_%s/parameters/pt6302_cgram" % model)
SystemInfo["HasOfflineDecoding"] = model not in ("osmini","osminiplus","et7000mini","et11000","mbmicro","mbtwinplus","mbmicrov2","et7x00","et8500")
SystemInfo["MultibootStartupDevice"] = getMultibootStartupDevice()
SystemInfo["canMode12"] = "%s_4.boxmode" % model in cmdline and cmdline["%s_4.boxmode" % model] in ("1","12") and "192M"
SystemInfo["canMultiBoot"] = getMultibootslots()
SystemInfo["canFlashWithOfgwrite"] = brand != "dreambox"
SystemInfo["HDRSupport"] = fileExists("/proc/stb/hdmi/hlg_support_choices") or fileCheck("/proc/stb/hdmi/hlg_support")
SystemInfo["CanDownmixAC3"] = fileHas("/proc/stb/audio/ac3_choices", "downmix")
SystemInfo["CanDownmixDTS"] = fileHas("/proc/stb/audio/dts_choices", "downmix")
SystemInfo["CanDownmixAAC"] = fileHas("/proc/stb/audio/aac_choices", "downmix")
SystemInfo["HDMIAudioSource"] = fileCheck("/proc/stb/hdmi/audio_source")
SystemInfo["BootDevice"] = getBootdevice()
SystemInfo["FbcTunerPowerAlwaysOn"] = model in ("vusolo4k","vuduo4k","vuduo4kse","vuultimo4k","vuuno4k","vuuno4kse", "gbquad4k", "gbue4k")
SystemInfo["HasPhysicalLoopthrough"] = ["Vuplus DVB-S NIM(AVL2108)", "GIGA DVB-S2 NIM (Internal)"]
SystemInfo["HasFBCtuner"] = ["Vuplus DVB-C NIM(BCM3158)", "Vuplus DVB-C NIM(BCM3148)", "Vuplus DVB-S NIM(7376 FBC)", "Vuplus DVB-S NIM(45308X FBC)", "Vuplus DVB-S NIM(45208 FBC)", "DVB-S NIM(45208 FBC)", "DVB-S2X NIM(45308X FBC)", "DVB-S2 NIM(45308 FBC)", "DVB-C NIM(3128 FBC)", "BCM45208", "BCM45308X", "BCM3158"]
SystemInfo["HaveCISSL"] = fileCheck("/etc/ssl/certs/customer.pem") and fileCheck("/etc/ssl/certs/device.pem")
SystemInfo["CanChangeOsdAlpha"] = access("/proc/stb/video/alpha", R_OK) and True or False
SystemInfo["ScalerSharpness"] = fileExists("/proc/stb/vmpeg/0/pep_scaler_sharpness")
SystemInfo["OScamInstalled"] = fileExists("/usr/bin/oscam") or fileExists("/usr/bin/oscam-emu") or fileExists("/usr/bin/oscam-trunk")
SystemInfo["OScamIsActive"] = fileExists("/var/tmp/.oscam")
SystemInfo["NCamInstalled"] = fileExists("/usr/bin/ncam")
SystemInfo["NCamIsActive"] = fileExists("/var/tmp/.ncam")
SystemInfo["CCcamIsActive"] = fileHas("/tmp/ecm.info","CCcam-s2s") or fileHas("/tmp/ecm.info","fta")
SystemInfo["OLDE2API"] = model in ("dm800","su980")
SystemInfo["7segment"] = getDisplayType() == "textolcd 7segmentos"
SystemInfo["textlcd"] = getDisplayType() == "textolcd"
SystemInfo["HiSilicon"] = pathExists("/proc/hisi") or fileExists("/usr/bin/hihalt")
SystemInfo["DefineSat"] = model in ("ustym4kpro","beyonwizv2","viper4k","sf8008","sf8008m","gbtrio4k","gbip4k","qviart5")
SystemInfo["CanFadeOut"] = brand not in ("linkdroid","mecool","minix","wetek","hardkernel","dinobot","maxytec","azbox") and not (SystemInfo["HiSilicon"])
SystemInfo["OSDAnimation"] = fileCheck("/proc/stb/fb/animation_mode")
SystemInfo["RecoveryMode"] = fileCheck("/proc/stb/fp/boot_mode") and model not in ("hd51", "h7")
SystemInfo["AndroidMode"] = SystemInfo["RecoveryMode"] and model == "multibox" or brand in ("hypercube", "linkdroid", "mecool", "wetek")
SystemInfo["grautec"] = fileExists("/tmp/usbtft")
SystemInfo["CanAC3plusTranscode"] = fileExists("/proc/stb/audio/ac3plus_choices")
SystemInfo["CanDTSHD"] = fileExists("/proc/stb/audio/dtshd_choices")
SystemInfo["CanWMAPRO"] = fileExists("/proc/stb/audio/wmapro")
SystemInfo["CanDownmixAACPlus"] = fileExists("/proc/stb/audio/aacplus_choices")
SystemInfo["CanAACTranscode"] = fileExists("/proc/stb/audio/aac_transcode_choices")
SystemInfo["GraphicLCD"] = model in ("vuultimo","xpeedlx3","et10000","hd2400","sezammarvel","atemionemesis","mbultra","beyonwizt4","osmio4kplus")
SystemInfo["LCDMiniTV"] = fileExists("/proc/stb/lcd/mode")
SystemInfo["LCDMiniTVPiP"] = SystemInfo["LCDMiniTV"] and model not in ("gb800ueplus","gbquad4k","gbue4k")
SystemInfo["DefaultDisplayBrightness"] = platform == "dm4kgen" and 8 or 5
SystemInfo["ConfigDisplay"] = SystemInfo["FrontpanelDisplay"] and getDisplayType() != "textolcd 7segmentos"
SystemInfo["DreamBoxAudio"] = platform == "dm4kgen" or model in ("dm7080","dm800")
SystemInfo["AmlogicFamily"] = fileExists("/proc/device-tree/amlogic-dt-id") or fileExists("/usr/bin/amlhalt") or pathExists("/sys/module/amports")
SystemInfo["VFDDelay"] = model in ("sf4008","beyonwizu4")
SystemInfo["VFDRepeats"] = brand != "ixuss" and getDisplayType() != "textolcd 7segmentos"
SystemInfo["FirstCheckModel"] = model in ("tmtwin4k","mbmicrov2","revo4k","force3uhd","mbmicro","e4hd","e4hdhybrid","valalinux","lunix","tmnanom3","purehd","force2nano","purehdse") or brand in ("linkdroid","wetek")
SystemInfo["SecondCheckModel"] = model in ("osninopro","osnino","osninoplus","dm7020hd","dm7020hdv2","9910lx","9911lx","9920lx","tmnanose","tmnanoseplus","tmnanosem2","tmnanosem2plus","tmnanosecombo","force2plus","force2","force2se","optimussos","fusionhd","fusionhdse","force2plushv") or brand == "ixuss"
SystemInfo["DifferentLCDSettings"] = model in ("spycat4kmini","osmega")
SystemInfo["CanBTAudio"] = fileCheck("/proc/stb/audio/btaudio")
SystemInfo["CanBTAudioDelay"] = fileCheck("/proc/stb/audio/btaudio_delay")
SystemInfo["ArchIsARM64"] = architecture == "aarch64" or "64" in architecture
SystemInfo["ArchIsARM"] = architecture.startswith(("arm", "cortex"))
SystemInfo["SeekStatePlay"] = False
SystemInfo["StatePlayPause"] = False
SystemInfo["StandbyState"] = False
SystemInfo["LEDButtons"] = False
SystemInfo["HasH9SD"] = model in ("h9","i55plus") and pathExists("/dev/mmcblk0p1")
SystemInfo["HasSDnomount"] = model in ("h9","h3","i55plus") and (False, "none") or model in ("multibox","h9combo","h3") and (True, "mmcblk0")
SystemInfo["canBackupEMC"] = model in ("hd51","h7") and ("disk.img", "%s" % SystemInfo["MultibootStartupDevice"]) or platform == "edision4k" and ("emmc.img", "%s" % SystemInfo["MultibootStartupDevice"]) or SystemInfo["DefineSat"] and ("usb_update.bin", "none")
SystemInfo["CanSyncMode"] = fileExists("/proc/stb/video/sync_mode_choices")
SystemInfo["FrontpanelLEDBlinkControl"] = fileExists("/proc/stb/fp/led_blink")
SystemInfo["FrontpanelLEDBrightnessControl"] = fileExists("/proc/stb/fp/led_brightness")
SystemInfo["FrontpanelLEDColorControl"] = fileExists("/proc/stb/fp/led_color")
SystemInfo["FrontpanelLEDFadeControl"] = fileExists("/proc/stb/fp/led_fade")
