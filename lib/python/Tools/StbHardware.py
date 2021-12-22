from __future__ import print_function
from os.path import join as pathjoin
from fcntl import ioctl
from struct import pack, unpack
from time import time, localtime, gmtime
from Tools.Directories import fileExists, resolveFilename, SCOPE_SKINS
from boxbranding import getMachineName, getBoxType, getRCName


def getBrand():
	brandName = ""
	brandStartSwith = resolveFilename(SCOPE_SKINS, pathjoin("rc_models", "%s" % (getRCName())))
	try:
		if "edision" in brandStartSwith:
			brandName = "Edision"
		elif "gb" in brandStartSwith:
			brandName = "GigaBlue"
		elif "octagon" in brandStartSwith:
			brandName = "octagon"
		elif "ini" in brandStartSwith:
			brandName = "INI"
		elif "hd" in brandStartSwith:
			brandName = "Mut@nt"
		elif "dmm" in brandStartSwith:
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
		ret = int(open("/proc/stb/fp/version", "r").read())
	except IOError:
		try:
			fp = open("/dev/dbox/fp0")
			ret = ioctl(fp.fileno(),0)
		except IOError:
			try:
				ret = open("/sys/firmware/devicetree/base/bolt/tag", "r").read().rstrip("\0")
			except:
				print("getFPVersion failed!")
	return ret

def setFPWakeuptime(wutime):
	try:
		open("/proc/stb/fp/wakeup_time", "w").write(str(wutime))
	except IOError:
		try:
			fp = open("/dev/dbox/fp0")
			ioctl(fp.fileno(), 6, pack('L', wutime)) # set wake up
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
			ioctl(fp.fileno(), 0x101, pack('L', wutime)) # set wake up
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
			ret = unpack('L', ioctl(fp.fileno(), 5, '	 '))[0] # get wakeuptime
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
