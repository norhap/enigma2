from os import stat
from os.path import isfile
from urllib.request import urlopen, Request
from sys import maxsize, modules, version_info
from gettext import ngettext
import time
from re import search
from socket import socket, AF_INET, inet_ntoa, SOCK_DGRAM
from fcntl import ioctl
from struct import pack, unpack
from subprocess import PIPE, Popen
from Components.SystemInfo import SystemInfo
from Tools.HardwareInfo import HardwareInfo


def getFeeds():
	if isfile("/etc/opkg/all-feed.conf"):
		with open("/etc/opkg/all-feed.conf", "r") as fr:
			feeds = "http://" + fr.read().split('//')[1].split('/')[0]
			try:
				urlopen(Request(feeds))
			except Exception:
				return False
		return True


def _ifinfo(sock, addr, ifname):
	iface = pack('256s', bytes(ifname[:15], encoding="UTF-8"))
	info = ioctl(sock.fileno(), addr, iface)
	if addr == 0x8927:
		return ''.join(['%02x:' % ord(chr(char)) for char in info[18:24]])[:-1].upper()
	else:
		return inet_ntoa(info[20:24])


def getIfConfig(ifname):
	ifreq = {'ifname': ifname}
	infos = {}
	sock = socket(AF_INET, SOCK_DGRAM)
	# offsets defined in /usr/include/linux/sockios.h on linux 2.6
	infos['addr'] = 0x8915  # SIOCGIFADDR
	infos['brdaddr'] = 0x8919  # SIOCGIFBRDADDR
	infos['hwaddr'] = 0x8927  # SIOCSIFHWADDR
	infos['netmask'] = 0x891b  # SIOCGIFNETMASK
	try:
		for k, v in infos.items():
			ifreq[k] = _ifinfo(sock, v, ifname)
	except Exception as ex:
		print("[About] getIfConfig Ex: %s" % str(ex))
		pass
	sock.close()
	return ifreq


def getIfTransferredData(ifname):
	f = open('/proc/net/dev', 'r')
	for line in f:
		if ifname in line:
			data = line.split('%s:' % ifname)[1].split()
			rx_bytes, tx_bytes = (data[0], data[8])
			f.close()
			return rx_bytes, tx_bytes


def getVersionString():
	return getImageVersionString()


def getImageVersionString():
	try:
		if isfile('/var/lib/opkg/status'):
			st = stat('/var/lib/opkg/status')
		tm = time.localtime(st.st_mtime)
		if tm.tm_year >= 2011:
			return time.strftime("%Y-%m-%d %H:%M:%S", tm)
	except:
		pass
	return _("unavailable")

# WW -placeholder for BC purposes, commented out for the moment in the Screen


def getFlashDateString():
	return _("unknown")


def getBuildDateString():
	try:
		if isfile('/etc/version'):
			version = open("/etc/version", "r").read()
			return "%s-%s-%s" % (version[:4], version[4:6], version[6:8])
	except:
		pass
	return _("unknown")


def getEnigmaVersionString():
	import enigma
	enigma_version = enigma.getEnigmaVersionString()
	if '-(no branch)' in enigma_version:
		enigma_version = enigma_version[:-12]
	return enigma_version


def getGStreamerVersionString():
	from glob import glob
	try:
		gst = [x.split("Version: ") for x in open(glob("/var/lib/opkg/info/gstreamer[0-9].[0-9].control")[0], "r") if x.startswith("Version:")][0]
		return "%s" % gst[1].split("+")[0].replace("\n", "")
	except:
		try:
			from glob import glob
			print("[About] Read /var/lib/opkg/info/gstreamer.control")
			gst = [x.split("Version: ") for x in open(glob("/var/lib/opkg/info/gstreamer?.[0-9].control")[0], "r") if x.startswith("Version:")][0]
			return "%s" % gst[1].split("+")[0].replace("\n", "")
		except:
			return _("Not installed")


def getFFmpegVersionString():
	try:
		from glob import glob
		ffmpeg = [x.split("Version: ") for x in open(glob("/var/lib/opkg/info/ffmpeg.control")[0], "r") if x.startswith("Version:")][0]
		return "%s" % ffmpeg[1].split("-")[0].replace("\n", "")
	except:
		return _("Not installed")


def getKernelVersionString():
	kernelversion = "unknown"
	try:
		with open("/proc/version", "r") as f:
			kernelversion = f.read().split(" ", 4)[2].split("-", 2)[0]
			return kernelversion
	except:
		return kernelversion


def getHardwareTypeString():
	return HardwareInfo().get_device_string()


def getImageTypeString():
	try:
		image_type = open("/etc/issue").readlines()[-2].strip()[:-6]
		return image_type.capitalize()
	except:
		return _("unknown")


def getCPUInfoString():
	try:
		cpu_count = 0
		cpu_speed = 0
		processor = ""
		for line in open("/proc/cpuinfo").readlines():
			line = [x.strip() for x in line.strip().split(":")]
			if not processor and line[0] in ("system type", "model name", "Processor"):
				processor = line[1].split()[0]
			elif not cpu_speed and line[0] == "cpu MHz":
				cpu_speed = "%1.0f" % float(line[1])
			elif line[0] == "processor":
				cpu_count += 1

		if processor.startswith("ARM") and isfile("/proc/stb/info/chipset"):
			processor = "%s (%s)" % (open("/proc/stb/info/chipset").readline().strip().upper(), processor)

		if not cpu_speed:
			try:
				cpu_speed = int(open("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq").read()) / 1000
			except:
				try:
					import binascii
					cpu_speed = int(int(binascii.hexlify(open('/sys/firmware/devicetree/base/cpus/cpu@0/clock-frequency', 'rb').read()), 16) / 100000000) * 100
				except:
					cpu_speed = "-"

		temperature = None
		if isfile('/proc/stb/fp/temp_sensor_avs'):
			temperature = open("/proc/stb/fp/temp_sensor_avs").readline().replace('\n', '')
		elif isfile('/proc/stb/power/avs'):
			temperature = open("/proc/stb/power/avs").readline().replace('\n', '')
		elif isfile('/proc/stb/fp/temp_sensor'):
			temperature = open("/proc/stb/fp/temp_sensor").readline().replace('\n', '')
		elif isfile('/proc/stb/sensors/temp0/value'):
			temperature = open("/proc/stb/sensors/temp0/value").readline().replace('\n', '')
		elif isfile('/proc/stb/sensors/temp/value'):
			temperature = open("/proc/stb/sensors/temp/value").readline().replace('\n', '')
		elif isfile("/sys/devices/virtual/thermal/thermal_zone0/temp"):
			try:
				temperature = int(open("/sys/devices/virtual/thermal/thermal_zone0/temp").read().strip()) // 1000
			except:
				pass
		elif isfile("/proc/hisi/msp/pm_cpu"):
			try:
				temperature = search(r'temperature = (\d+) degree', open("/proc/hisi/msp/pm_cpu").read()).group(1)
			except:
				pass
		if temperature:
			degree = "\u00B0"
			if not isinstance(degree, str):
				degree = degree.encode("UTF-8", errors="ignore")
			return "%s %s MHz (%s) %s%sC" % (processor, cpu_speed, ngettext("%d core", "%d cores", cpu_count) % cpu_count, temperature, degree)
		return "%s %s MHz (%s)" % (processor, cpu_speed, ngettext("%d core", "%d cores", cpu_count) % cpu_count)
	except:
		return _("undefined")


def getChipSetString():
	try:
		chipset = open("/proc/stb/info/chipset", "r").read()
		return str(chipset.lower().replace('\n', ''))
	except OSError:
		return _("undefined")


def getChipSet():
	try:
		f = open('/proc/stb/info/chipset', 'r')
		chipset = f.read()
		f.close()
		return str(chipset.lower().replace('\n', '').replace('brcm', '').replace('bcm', ''))
	except OSError:
		return _("unavailable")


def getCPUBrand():
	if SystemInfo["HiSilicon"]:
		return _("HiSilicon")
	else:
		return _("Broadcom")


def getCPUArch():
	if SystemInfo["ArchIsARM64"]:
		return _("ARM64")
	elif SystemInfo["ArchIsARM"]:
		return _("ARM")
	else:
		return _("Mipsel")


def getDriverInstalledDate():
	from glob import glob
	try:
		try:
			driver = [x.split("-")[-2:-1][0][-8:] for x in open(glob("/var/lib/opkg/info/*-dvb-modules-*.control")[0], "r") if x.startswith("Version:")][0]
			return "%s-%s-%s" % (driver[:4], driver[4:6], driver[6:])
		except:
			try:
				driver = [x.split("Version:") for x in open(glob("/var/lib/opkg/info/*-dvb-proxy-*.control")[0], "r") if x.startswith("Version:")][0]
				return "%s" % driver[1].replace("\n", "")
			except:
				driver = [x.split("Version:") for x in open(glob("/var/lib/opkg/info/*-platform-util-*.control")[0], "r") if x.startswith("Version:")][0]
				return "%s" % driver[1].replace("\n", "")
	except:
		return _("unknown")


def getPythonVersionString():
	return "%s.%s.%s" % (version_info.major, version_info.minor, version_info.micro)


def GetIPsFromNetworkInterfaces():
	from array import array
	is_64bits = maxsize > 2**32
	struct_size = 40 if is_64bits else 32
	s = socket(AF_INET, SOCK_DGRAM)
	max_possible = 8  # initial value
	while True:
		_bytes = max_possible * struct_size
		names = array('B')
		for i in range(0, _bytes):
			names.append(0)
		outbytes = unpack('iL', ioctl(
			s.fileno(),
			0x8912,  # SIOCGIFCONF
			pack('iL', _bytes, names.buffer_info()[0])
		))[0]
		if outbytes == _bytes:
			max_possible *= 2
		else:
			break

	namestr = names.tobytes()
	ifaces = []
	for i in range(0, outbytes, struct_size):
		iface_name = str(namestr[i:i + 16]).split('\0', 1)[0]
		if iface_name != 'lo':
			iface_addr = inet_ntoa(namestr[i + 20:i + 24])
			ifaces.append((iface_name, iface_addr))
	return ifaces


def getBoxUptime():
	try:
		time = ''
		f = open("/proc/uptime", "r")
		secs = int(f.readline().split('.')[0])
		f.close()
		if secs > 86400:
			days = secs / 86400
			secs = secs % 86400
			time = ngettext("%d day", "%d days", days) % days + " "
		h = secs // 3600
		m = (secs % 3600) // 60
		time += ngettext("%d hour", "%d hours", h) % h + " " if h > 1 else ngettext("%d hour", "%d hour", h) % h + " "
		time += ngettext("%d minute", "%d minutes", m) % m if m > 1 else ngettext("%d minute", "%d minute", m) % m
		return "%s" % time
	except:
		return '-'


def getGccVersion():
	process = Popen(("/lib/libc.so.6"), stdout=PIPE, stderr=PIPE, universal_newlines=True)
	stdout, stderr = process.communicate()
	if process.returncode == 0:
		for line in stdout.split("\n"):
			if line.startswith("Compiled by GNU CC version"):
				data = line.split()[-1]
				if data.endswith("."):
					data = data[0:-1]
				return data
	print("[About] Get gcc version failed.")
	return _("Unknown")


# def getModel():
	# return HardwareInfo().get_machine_name()
# For modules that do "from About import about"
about = modules[__name__]
