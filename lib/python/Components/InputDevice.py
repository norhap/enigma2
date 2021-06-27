from Components.config import config, ConfigSlider, ConfigSubsection, ConfigYesNo, ConfigText, ConfigInteger
from enigma import getBoxType, getBoxBrand
from Components.SystemInfo import SystemInfo
import errno
import xml.etree.cElementTree
from enigma import eRCInput
from keyids import KEYIDS
from Components.RcModel import rc_model
from fcntl import ioctl
from os import O_NONBLOCK, O_RDWR, close, listdir, open, write
from os.path import isdir, isfile
from platform import machine
import struct
import platform
from Tools.Directories import pathExists

model = getBoxType()

# include/uapi/asm-generic/ioctl.h
# asm-generic/ioctl.h for HAVE_OLDE2_API
IOC_NRBITS = 8L
IOC_TYPEBITS = 8L

if SystemInfo["OLDE2API"]:
	IOC_SIZEBITS = 13L
	IOC_DIRBITS = 3L
else:
	IOC_SIZEBITS = 13L if "mips" in platform.machine() else 14L
	IOC_DIRBITS = 3L if "mips" in platform.machine() else 2L

IOC_NRSHIFT = 0L
IOC_TYPESHIFT = IOC_NRSHIFT + IOC_NRBITS
IOC_SIZESHIFT = IOC_TYPESHIFT + IOC_TYPEBITS
IOC_DIRSHIFT = IOC_SIZESHIFT + IOC_SIZEBITS

IOC_READ = 2L


def EVIOCGNAME(length):
	return (IOC_READ << IOC_DIRSHIFT) | (length << IOC_SIZESHIFT) | (0x45 << IOC_TYPESHIFT) | (0x06 << IOC_NRSHIFT)


class InputDevices:
	def __init__(self):
		self.devices = {}
		self.currentDevice = None
		for device in sorted(listdir("/dev/input/")):
			if isdir("/dev/input/%s" % device):
				continue
			try:
				buffer = b"\0" * 512
				self.fd = open("/dev/input/%s" % device, O_RDWR | O_NONBLOCK)
				self.name = ioctl(self.fd, self.EVIOCGNAME(256), buffer)
				close(self.fd)
				self.name = str(self.name[:self.name.find(b"\0")])
			except (IOError, OSError) as err:
				print("[InputDevice] Error: device='%s' getInputDevices <ERROR: ioctl(EVIOCGNAME): '%s'>" % (device, str(err)))
				self.name = None
			if self.name:
				devType = self.getInputDeviceType(self.name.lower())
				print("[InputDevice] Found device '%s' with name '%s' of type '%s'." % (device, self.name, "Unknown" if devType is None else devType.capitalize()))
				# What was this for?
				# if self.name == "aml_keypad":
				# 	print("[InputDevice] ALERT: Old code flag for 'aml_keypad'.")
				# 	self.name = "dreambox advanced remote control (native)"
				# if self.name in BLACKLIST:
				# 	print("[InputDevice] ALERT: Old code flag for device in blacklist.")
				# 	continue
				self.devices[device] = {
					"name": self.name,
					"type": devType,
					"enabled": False,
					"configuredName": None
				}
				# What was this for?
				# if model.startswith("et"):
				# 	print("[InputDevice] ALERT: Old code flag for device starting with 'et'.")
				# 	self.setDeviceDefaults(device)

	def EVIOCGNAME(self, length):
		# From include/uapi/asm-generic/ioctl.h and asm-generic/ioctl.h for HAVE_OLDE2_API
		IOC_NRBITS = 8
		IOC_TYPEBITS = 8
		if SystemInfo["OLDE2API"]:
			IOC_SIZEBITS = 13
		else:
			IOC_SIZEBITS = 13 if "mips" in machine() else 14
		IOC_NRSHIFT = 0
		IOC_TYPESHIFT = IOC_NRSHIFT + IOC_NRBITS
		IOC_SIZESHIFT = IOC_TYPESHIFT + IOC_TYPEBITS
		IOC_DIRSHIFT = IOC_SIZESHIFT + IOC_SIZEBITS
		IOC_READ = 2
		return (IOC_READ << IOC_DIRSHIFT) | (length << IOC_SIZESHIFT) | (0x45 << IOC_TYPESHIFT) | (0x06 << IOC_NRSHIFT)

	def getInputDeviceType(self, name):
		if "remote control" in str(name).lower():
			return "remote"
		elif "keyboard" in str(name).lower():
			return "keyboard"
		elif "mouse" in str(name).lower():
			return "mouse"
		else:
			print("[InputDevice] Unknown device type:",name)
			return None

	def getDeviceName(self, x):
		if x in self.devices.keys():
			return self.devices[x].get("name", x)
		else:
			return "Unknown device name"

	def getDeviceList(self):
		return sorted(self.devices.iterkeys())

	def setDeviceAttribute(self, device, attribute, value):
		#print("[InputDevice] setting for device", device, "attribute", attribute, " to value", value)
		if device in self.devices:
			self.devices[device][attribute] = value

	def getDeviceAttribute(self, device, attribute):
		if device in self.devices:
			if attribute in self.devices[device]:
				return self.devices[device][attribute]
		return None

	def setEnabled(self, device, value):
		oldval = self.getDeviceAttribute(device, 'enabled')
		#print("[InputDevice] setEnabled for device %s to %s from %s" % (device,value,oldval))
		self.setDeviceAttribute(device, 'enabled', value)
		if oldval is True and value is False:
			self.setDefaults(device)

	def setName(self, device, value):
		#print("[InputDevice] setName for device %s to %s" % (device,value))
		self.setDeviceAttribute(device, 'configuredName', value)

	#struct input_event {
	#	struct timeval time;    -> ignored
	#	__u16 type;             -> EV_REP (0x14)
	#	__u16 code;             -> REP_DELAY (0x00) or REP_PERIOD (0x01)
	#	__s32 value;            -> DEFAULTS: 700(REP_DELAY) or 100(REP_PERIOD)
	#}; -> size = 16

	def setDefaults(self, device):
		print("[InputDevice] setDefaults for device %s" % device)
		self.setDeviceAttribute(device, 'configuredName', None)
		event_repeat = struct.pack('LLHHi', 0, 0, 0x14, 0x01, 100)
		event_delay = struct.pack('LLHHi', 0, 0, 0x14, 0x00, 700)
		fd = open("/dev/input/" + device, O_RDWR)
		write(fd, event_repeat)
		write(fd, event_delay)
		close(fd)

	def setRepeat(self, device, value): #REP_PERIOD
		if self.getDeviceAttribute(device, 'enabled'):
			print("[InputDevice] setRepeat for device %s to %d ms" % (device,value))
			event = struct.pack('LLHHi', 0, 0, 0x14, 0x01, int(value))
			fd = open("/dev/input/" + device, O_RDWR)
			write(fd, event)
			close(fd)

	def setDelay(self, device, value): #REP_DELAY
		if self.getDeviceAttribute(device, 'enabled'):
			print("[InputDevice] setDelay for device %s to %d ms" % (device,value))
			event = struct.pack('LLHHi', 0, 0, 0x14, 0x00, int(value))
			fd = open("/dev/input/" + device, O_RDWR)
			write(fd, event)
			close(fd)


class InitInputDevices:

	def __init__(self):
		self.currentDevice = ""
		self.createConfig()

	def createConfig(self, *args):
		config.InputDevices = ConfigSubsection()
		for device in sorted(iInputDevices.devices.iterkeys()):
			self.currentDevice = device
			#print("[InitInputDevices] creating config entry for device: %s -> %s  " % (self.currentDevice, iInputDevices.Devices[device]["name"]))
			self.setupConfigEntries(self.currentDevice)
			self.currentDevice = ""

	def InputDevicesEnabledChanged(self,configElement):
		if self.currentDevice != "" and iInputDevices.currentDevice == "":
			iInputDevices.setEnabled(self.currentDevice, configElement.value)
		elif iInputDevices.currentDevice != "":
			iInputDevices.setEnabled(iInputDevices.currentDevice, configElement.value)

	def InputDevicesNameChanged(self,configElement):
		if self.currentDevice != "" and iInputDevices.currentDevice == "":
			iInputDevices.setName(self.currentDevice, configElement.value)
			if configElement.value != "":
				devname = iInputDevices.getDeviceAttribute(self.currentDevice, 'name')
				if devname != configElement.value:
					cmd = "config.InputDevices." + self.currentDevice + ".enabled.value = False"
					exec(cmd)
					cmd = "config.InputDevices." + self.currentDevice + ".enabled.save()"
					exec(cmd)
		elif iInputDevices.currentDevice != "":
			iInputDevices.setName(iInputDevices.currentDevice, configElement.value)

	def InputDevicesRepeatChanged(self,configElement):
		if self.currentDevice != "" and iInputDevices.currentDevice == "":
			iInputDevices.setRepeat(self.currentDevice, configElement.value)
		elif iInputDevices.currentDevice != "":
			iInputDevices.setRepeat(iInputDevices.currentDevice, configElement.value)

	def InputDevicesDelayChanged(self,configElement):
		if self.currentDevice != "" and iInputDevices.currentDevice == "":
			iInputDevices.setDelay(self.currentDevice, configElement.value)
		elif iInputDevices.currentDevice != "":
			iInputDevices.setDelay(iInputDevices.currentDevice, configElement.value)

	def setupConfigEntries(self,device):
		cmd = "config.InputDevices." + device + " = ConfigSubsection()"
		exec(cmd)
		if model in ("dm800","azboxhd"):
			cmd = "config.InputDevices." + device + ".enabled = ConfigYesNo(default = True)"
		else:
			cmd = "config.InputDevices." + device + ".enabled = ConfigYesNo(default = False)"
		exec(cmd)
		cmd = "config.InputDevices." + device + ".enabled.addNotifier(self.InputDevicesEnabledChanged,config.InputDevices." + device + ".enabled)"
		exec(cmd)
		cmd = "config.InputDevices." + device + '.name = ConfigText(default="")'
		exec(cmd)
		cmd = "config.InputDevices." + device + ".name.addNotifier(self.InputDevicesNameChanged,config.InputDevices." + device + ".name)"
		exec(cmd)
		if model in ("maram9", "axodin"):
			cmd = "config.InputDevices." + device + ".repeat = ConfigSlider(default=400, increment = 10, limits=(0, 500))"
		elif model == "azboxhd":
			cmd = "config.InputDevices." + device + ".repeat = ConfigSlider(default=150, increment = 10, limits=(0, 500))"
		else:
			cmd = "config.InputDevices." + device + ".repeat = ConfigSlider(default=100, increment = 10, limits=(0, 500))"
		exec(cmd)
		cmd = "config.InputDevices." + device + ".repeat.addNotifier(self.InputDevicesRepeatChanged,config.InputDevices." + device + ".repeat)"
		exec(cmd)
		cmd = "config.InputDevices." + device + ".delay = ConfigSlider(default=700, increment = 100, limits=(0, 5000))"
		exec(cmd)
		cmd = "config.InputDevices." + device + ".delay.addNotifier(self.InputDevicesDelayChanged,config.InputDevices." + device + ".delay)"
		exec(cmd)



iInputDevices = InputDevices()


config.plugins.remotecontroltype = ConfigSubsection()
config.plugins.remotecontroltype.rctype = ConfigInteger(default = 0)


class RcTypeControl():
	def __init__(self):
		if SystemInfo["RcTypeChangable"] and pathExists('/proc/stb/info/boxtype') and getBoxBrand() not in ("gigablue","odin","ini","entwopia","tripledot"):
			self.isSupported = True
			self.boxType = open('/proc/stb/info/boxtype', 'r').read().strip()
			if config.plugins.remotecontroltype.rctype.value != 0:
				self.writeRcType(config.plugins.remotecontroltype.rctype.value)
		else:
			self.isSupported = False

	def multipleRcSupported(self):
		return self.isSupported

	def getBoxType(self):
		return self.boxType

	def writeRcType(self, rctype):
		if self.isSupported and rctype > 0:
			open('/proc/stb/ir/rc/type', 'w').write('%d' % rctype)

	def readRcType(self):
		rc = 0
		if self.isSupported:
			rc = open('/proc/stb/ir/rc/type', 'r').read().strip()
		return int(rc)


class Keyboard:
	def __init__(self):
		self.keyboardMaps = []
		for keyboardMapInfo in sorted(listdir(resolveFilename(SCOPE_KEYMAPS))):
			if keyboardMapInfo.endswith(".info"):
				lines = []
				lines = fileReadLines(resolveFilename(SCOPE_KEYMAPS, keyboardMapInfo), lines, source=MODULE_NAME)
				keyboardMapFile = None
				keyboardMapName = None
				for line in lines:
					key, val = [x.strip() for x in line.split("=", 1)]
					if key == "kmap":
						keyboardMapFile = val
					elif key == "name":
						keyboardMapName = val
				if keyboardMapFile and keyboardMapName:
					keyboardMapPath = resolveFilename(SCOPE_KEYMAPS, keyboardMapFile)
					if isfile(keyboardMapPath):
						if config.crash.debugKeyboards.value:
							print("[InputDevice] Adding keyboard keymap '%s' in '%s'." % (keyboardMapName, keyboardMapFile))
						self.keyboardMaps.append((keyboardMapFile, keyboardMapName))
					else:
						print("[InputDevice] Error: Keyboard keymap file '%s' doesn't exist!" % keyboardMapPath)
				else:
					print("[InputDevice] Error: Invalid keyboard keymap information file '%s'!" % keyboardMapInfo)
		config.inputDevices.keyboardMap = ConfigSelection(choices=self.keyboardMaps, default=self.getDefaultKeyboardMap())

	def getDefaultKeyboardMap(self):
		# locale = international.getLocale()
		locale = "en_US"  # language.getLanguage()
		if locale:
			for keyboardMap in self.keyboardMaps:  # See if there is a keyboard keymap specific to the current locale.
				if keyboardMap[0].startswith(locale):
					return keyboardMap[0]
		# language = international.getLanguage()
		language = locale.split("_")[0]
		if language:
			for keyboardMap in self.keyboardMaps:  # See if there is a keyboard keymap specific to the current language.
				if keyboardMap[0].startswith(language):
					return keyboardMap[0]
		return "default.kmap"


iRcTypeControl = RcTypeControl()
