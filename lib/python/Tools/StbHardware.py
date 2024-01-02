from os.path import isfile
from fcntl import ioctl
from struct import pack, unpack
from time import time, localtime, timezone
from Tools.Directories import fileExists, fileReadLine
from boxbranding import getMachineBuild

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
	elif isfile(INFO_SUBTYPE):
		with open(INFO_SUBTYPE, "r") as fd:
			typetuner = fd.read().split('\n', 1)[0]
	return typetuner


def getFPVersion():
	ret = None
	try:
		if isfile("/sys/firmware/devicetree/base/bolt/tag"):
			ret = open("/sys/firmware/devicetree/base/bolt/tag", "r").read().rstrip("\0")
		elif getMachineBuild() in ('dm7080', 'dm820', 'dm520', 'dm525', 'dm900', 'dm920'):
			ret = open("/proc/stb/fp/version", "r").read()
		else:
			ret = int(open("/proc/stb/fp/version", "r").read())
	except OSError:
		if isfile("/dev/dbox/fp0"):
			try:
				with open("/dev/dbox/fp0") as fd:
					ret = ioctl(fd.fileno(), 0)
			except OSError as err:
				print("[StbHardware] %s" % err)
	return ret


def setFPWakeuptime(wutime):
	try:
		open("/proc/stb/fp/wakeup_time", "w").write(str(wutime))
	except OSError:
		try:
			fp = open("/dev/dbox/fp0")
			ioctl(fp.fileno(), 6, pack('L', wutime))  # set wake up
			fp.close()
		except OSError:
			print("[StbHardware] setFPWakeupTime failed!")


def setRTCoffset(forsleep=None):
	if localtime().tm_isdst == 0:
		forsleep = 7200 + timezone
	else:
		forsleep = 3600 - timezone

	t_local = localtime(int(time()))

	# Set RTC OFFSET (diff. between UTC and Local Time)
	try:
		open("/proc/stb/fp/rtc_offset", "w").write(str(forsleep))
		print("[StbHardware] set RTC offset to %s sec." % (forsleep))
	except OSError:
		print("[StbHardware] setRTCoffset failed!")


def setRTCtime(wutime):
	if fileExists("/proc/stb/fp/rtc_offset"):
		setRTCoffset()
	try:
		open("/proc/stb/fp/rtc", "w").write(str(wutime))
	except OSError:
		try:
			fp = open("/dev/dbox/fp0")
			ioctl(fp.fileno(), 0x101, pack('L', wutime))  # set wake up
			fp.close()
		except OSError:
			print("[StbHardware] setRTCtime failed!")


def getFPWakeuptime():
	ret = 0
	try:
		ret = int(open("/proc/stb/fp/wakeup_time", "r").read())
	except OSError:
		try:
			fp = open("/dev/dbox/fp0")
			ret = unpack('L', ioctl(fp.fileno(), 5, '	 '))[0]  # get wakeuptime
			fp.close()
		except OSError:
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
		except OSError:
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
		except OSError:
			print("clearFPWasTimerWakeup failed!")
