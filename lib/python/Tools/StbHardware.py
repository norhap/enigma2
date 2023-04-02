from os.path import isfile, join as pathjoin
from fcntl import ioctl
from struct import pack, unpack
from time import time, localtime, gmtime
from Tools.Directories import fileExists, resolveFilename, SCOPE_SKINS, fileReadLine
from boxbranding import getMachineName, getBoxType, getRCName

INFO_TYPE = "/proc/stb/info/type"
INFO_SUBTYPE = "/proc/stb/info/subtype"


def getWakeOnLANType(fileName):
	value = ""
	if fileName:
		value = fileReadLine(fileName)
	onOff = ("off", "on")
	return onOff if value in onOff else ("disable", "enable")


def getProcInfoTypeTuner():
	typetuner = ""
	if isfile(INFO_TYPE):
		with open(INFO_TYPE, "r") as fd:
			typetuner = fd.read().split('\n', 1)[0]
			fd.close()
	elif isfile(INFO_SUBTYPE):
		with open(INFO_SUBTYPE, "r") as fd:
			typetuner = fd.read().split('\n', 1)[0]
			fd.close()
	return typetuner


def getBrand():
	brandName = ""
	rcStartSwithisBrand = resolveFilename(SCOPE_SKINS, pathjoin("rc_models", "%s" % (getRCName())))  # based on remote control name start matches brand.
	try:
		if "edision" in rcStartSwithisBrand:
			brandName = "Edision"
		elif "gb" in rcStartSwithisBrand:
			brandName = "GigaBlue"
		elif "octagon" in rcStartSwithisBrand:
			brandName = "octagon"
		elif "ini" in rcStartSwithisBrand:
			brandName = "INI"
		elif "hd" in rcStartSwithisBrand:
			brandName = "Mut@nt"
		elif "ixuss" in rcStartSwithisBrand:
			brandName = "Medi@link"
		elif "vu" in rcStartSwithisBrand:
			brandName = "vuplus"
		elif "dinobot" in rcStartSwithisBrand:
			brandName = "dinobot"
		elif "dmm" in rcStartSwithisBrand:  # this check should always be the last.
			brandName = "dreambox"
		elif not brandName:
			print("[brandName] Not Exists!! add this Brand to getBrand")
	except (IOError, OSError) as err:
		print("[brandName] exception with error in Brand Name")
	return brandName


def getBrandModel():
	brandModel = None
	brand = getBrand()
	model = getMachineName()
	machine = getBoxType()
	try:
		if machine:
			brandModel = ("%s %s") % (brand, model)
	except (IOError, OSError) as err:
		print("[brandModel] No brandModel!")
	return brandModel


def getFPVersion():
	ret = None
	try:
		if isfile("/sys/firmware/devicetree/base/bolt/tag"):
			ret = open("/sys/firmware/devicetree/base/bolt/tag", "r").read().rstrip("\0")
		elif getBoxType() in ('dm7080', 'dm820', 'dm520', 'dm525', 'dm900', 'dm920'):
			ret = open("/proc/stb/fp/version", "r").read()
		else:
			ret = int(open("/proc/stb/fp/version", "r").read())
	except (IOError, OSError):
		if isfile("/dev/dbox/fp0"):
			try:
				with open("/dev/dbox/fp0") as fd:
					ret = ioctl(fd.fileno(), 0)
			except (IOError, OSError) as err:
				print("[StbHardware] %s" % err)
	return ret


def setFPWakeuptime(wutime):
	try:
		open("/proc/stb/fp/wakeup_time", "w").write(str(wutime))
	except IOError:
		try:
			fp = open("/dev/dbox/fp0")
			ioctl(fp.fileno(), 6, pack('L', wutime))  # set wake up
			fp.close()
		except IOError:
			print("[StbHardware] setFPWakeupTime failed!")


def setRTCoffset(forsleep=None):
	import time
	if time.localtime().tm_isdst == 0:
		forsleep = 7200 + time.timezone
	else:
		forsleep = 3600 - time.timezone

	t_local = time.localtime(int(time.time()))

	# Set RTC OFFSET (diff. between UTC and Local Time)
	try:
		open("/proc/stb/fp/rtc_offset", "w").write(str(forsleep))
		print("[StbHardware] set RTC offset to %s sec." % (forsleep))
	except IOError:
		print("[StbHardware] setRTCoffset failed!")


def setRTCtime(wutime):
	if fileExists("/proc/stb/fp/rtc_offset"):
		setRTCoffset()
	try:
		open("/proc/stb/fp/rtc", "w").write(str(wutime))
	except IOError:
		try:
			fp = open("/dev/dbox/fp0")
			ioctl(fp.fileno(), 0x101, pack('L', wutime))  # set wake up
			fp.close()
		except IOError:
			print("[StbHardware] setRTCtime failed!")


def getFPWakeuptime():
	ret = 0
	try:
		ret = int(open("/proc/stb/fp/wakeup_time", "r").read())
	except IOError:
		try:
			fp = open("/dev/dbox/fp0")
			ret = unpack('L', ioctl(fp.fileno(), 5, '	 '))[0]  # get wakeuptime
			fp.close()
		except IOError:
			print("[StbHardware] getFPWakeupTime failed!")
	return ret


wasTimerWakeup = None


def getFPWasTimerWakeup(check=False):
	global wasTimerWakeup
	isError = False
	if wasTimerWakeup is not None:
		if check:
			return wasTimerWakeup, isError
		return wasTimerWakeup
	wasTimerWakeup = False
	try:
		wasTimerWakeup = int(open("/proc/stb/fp/was_timer_wakeup", "r").read()) and True or False
		open("/tmp/was_timer_wakeup.txt", "w").write(str(wasTimerWakeup))
	except:
		try:
			fp = open("/dev/dbox/fp0")
			wasTimerWakeup = unpack('B', ioctl(fp.fileno(), 9, ' '))[0] and True or False
			fp.close()
		except IOError:
			print("[StbHardware] wasTimerWakeup failed!")
			isError = True
	if wasTimerWakeup:
		# clear hardware status
		clearFPWasTimerWakeup()
	if check:
		return wasTimerWakeup, isError
	return wasTimerWakeup


def clearFPWasTimerWakeup():
	try:
		open("/proc/stb/fp/was_timer_wakeup", "w").write('0')
	except:
		try:
			fp = open("/dev/dbox/fp0")
			ioctl(fp.fileno(), 10)
			fp.close()
		except IOError:
			print("clearFPWasTimerWakeup failed!")
