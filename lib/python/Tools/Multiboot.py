# -*- coding: utf-8 -*-
from datetime import datetime
from Components.Console import Console
import os
import glob
import tempfile
from subprocess import check_output
from Components.SystemInfo import SystemInfo, BoxInfo as BoxInfoRunningInstance, BoxInformation
from Tools.Directories import fileContains, fileExists

if fileContains("/proc/cmdline", "kexec=1"):
	from PIL import Image
	from PIL import ImageDraw
	from PIL import ImageFont


class tmp:
	dir = None


def getMultibootStartupDevice():
	tmp.dir = tempfile.mkdtemp(prefix="Multiboot")
	bootList = ("/dev/mmcblk0p1", "/dev/mmcblk1p1", "/dev/mmcblk0p3", "/dev/mmcblk0p4", "/dev/mtdblock2", "/dev/block/by-name/bootoptions") if not SystemInfo["hasKexec"] else ("/dev/mmcblk0p4", "/dev/mmcblk0p7", "/dev/mmcblk0p9")
	for device in bootList:
		if os.path.exists(device):
			if os.path.exists("/dev/block/by-name/flag"):
				Console().ePopen('mount --bind %s %s' % (device, tmp.dir))
			else:
				Console().ePopen('mount %s %s' % (device, tmp.dir))
			if os.path.isfile(os.path.join(tmp.dir, "STARTUP")):
				print('[Multiboot] Startupdevice found:', device)
				return device
			Console().ePopen('umount %s' % tmp.dir)
	if not os.path.ismount(tmp.dir):
		os.rmdir(tmp.dir)


def getparam(line, param):
	return line.replace("userdataroot", "rootuserdata").rsplit('%s=' % param, 1)[1].split(' ', 1)[0]


def getMultibootslots():
	bootslots = {}
	mode12found = False
	SystemInfo["VuUUIDSlot"] = ""
	UUID = ""
	UUIDnum = 0
	BoxInfo = BoxInfoRunningInstance
	if SystemInfo["MultibootStartupDevice"]:
		for file in glob.glob(os.path.join(tmp.dir, 'STARTUP_*')):
			if 'MODE_' in file:
				mode12found = True
				slotnumber = file.rsplit('_', 3)[1]
			else:
				slotnumber = file.rsplit('_', 1)[1]
			if "STARTUP_RECOVERY" in file:
				SystemInfo["RecoveryMode"] = True
				slotnumber = "0"
			if slotnumber.isdigit() and slotnumber not in bootslots:
				slot = {}
				if SystemInfo["hasKexec"] and int(slotnumber) > 3:
					SystemInfo["HasKexecUSB"] = True
				print("[Multiboot][getMultibootslots] slot", slot)
				for line in open(file).readlines():
					if 'root=' in line:
						line = line.rstrip("\n")
						device = getparam(line, 'root')
						if "UUID=" in device:
							slotx = str(getUUIDtoSD(device))
							UUID = device
							UUIDnum += 1
							if slotx is not None:
								device = slotx
							slot['kernel'] = "/linuxrootfs%s/zImage" % slotnumber
						if os.path.exists(device) or device == 'ubi0:ubifs':
							slot['device'] = device
							slot["slotType"] = "eMMC" if "mmc" in slot["device"] else "USB"
							slot['startupfile'] = os.path.basename(file)
							SystemInfo["HasMultibootMTD"] = slot.get("mtd")
							if 'rootsubdir' in line:
								SystemInfo["HasRootSubdir"] = True
								slot['rootsubdir'] = getparam(line, 'rootsubdir')
								slot['kernel'] = getparam(line, 'kernel')
							elif not SystemInfo["hasKexec"] and 'sda' in line:
								slot['kernel'] = getparam(line, 'kernel')
								slot['rootsubdir'] = None
							else:
								slot['kernel'] = '%sp%s' % (device.split('p')[0], int(device.split('p')[1]) - 1)
						break
				if slot:
					bootslots[int(slotnumber)] = slot
		Console().ePopen('umount %s' % tmp.dir)
		if not os.path.ismount(tmp.dir):
			os.rmdir(tmp.dir)
		if not mode12found and SystemInfo["canMode12"]:
			# the boot device has ancient content and does not contain the correct STARTUP files
			for slot in range(1, 5):
				bootslots[slot] = {'device': '/dev/mmcblk0p%s' % (slot * 2 + 1), 'startupfile': None}
	print('[Multiboot] Bootslots found:', bootslots)
	return bootslots


def getCurrentImage():
	UUID = ""
	UUIDnum = 0
	if SystemInfo["canMultiBoot"]:
		if not SystemInfo["hasKexec"]:  # No kexec kernel multiboot
			slot = [x[-1] for x in open('/sys/firmware/devicetree/base/chosen/bootargs', 'r').read().split() if x.startswith('rootsubdir')]
			if slot:
				return int(slot[0])
			else:
				device = getparam(open('/sys/firmware/devicetree/base/chosen/bootargs', 'r').read(), 'root')
				for slot in SystemInfo["canMultiBoot"].keys():
					if SystemInfo["canMultiBoot"][slot]['device'] == device:
						return slot
		else:  # kexec kernel multiboot VU+
			rootsubdir = [x for x in open('/sys/firmware/devicetree/base/chosen/bootargs', 'r').read().split() if x.startswith("rootsubdir")]
			char = "/" if "/" in rootsubdir[0] else "="
			SystemInfo["VuUUIDSlot"] = (UUID, UUIDnum) if UUIDnum != 0 else ""
			return int(rootsubdir[0].rsplit(char, 1)[1][11:])


def getCurrentImageMode():
	print("[Multiboot] Read /sys/firmware/devicetree/base/chosen/bootargs")
	return bool(SystemInfo["canMultiBoot"]) and SystemInfo["canMode12"] and int(open('/sys/firmware/devicetree/base/chosen/bootargs', 'r').read().replace('\0', '').split('=')[-1])


def deleteImage(slot):
	tmp.dir = tempfile.mkdtemp(prefix="Multiboot")
	Console().ePopen('mount %s %s' % (SystemInfo["canMultiBoot"][slot]['device'], tmp.dir))
	enigma2binaryfile = os.path.join(os.sep.join(filter(None, [tmp.dir, SystemInfo["canMultiBoot"][slot].get('rootsubdir', '')])), 'usr/bin/enigma2')
	if os.path.exists(enigma2binaryfile):
		os.rename(enigma2binaryfile, '%s.bak' % enigma2binaryfile)
	Console().ePopen('umount %s' % tmp.dir)
	if not os.path.ismount(tmp.dir):
		os.rmdir(tmp.dir)


def restoreImages():
	for slot in SystemInfo["canMultiBoot"]:
		tmp.dir = tempfile.mkdtemp(prefix="Multiboot")
		Console().ePopen('mount %s %s' % (SystemInfo["canMultiBoot"][slot]['device'], tmp.dir))
		enigma2binaryfile = os.path.join(os.sep.join(filter(None, [tmp.dir, SystemInfo["canMultiBoot"][slot].get('rootsubdir', '')])), 'usr/bin/enigma2')
		if os.path.exists('%s.bak' % enigma2binaryfile):
			os.rename('%s.bak' % enigma2binaryfile, enigma2binaryfile)
		Console().ePopen('umount %s' % tmp.dir)
		if not os.path.ismount(tmp.dir):
			os.rmdir(tmp.dir)


def getUUIDtoSD(UUID):  # returns None on failure
	check = "/sbin/blkid"
	if os.path.exists(check):
		lines = check_output([check]).decode(encoding="utf8", errors="ignore").split("\n")
		for line in lines:
			if UUID in line.replace('"', ''):
				return line.split(":")[0].strip()
	else:
		return None


def getImagelist(Recovery=None):
	imagelist = {}
	for slot in sorted(list(SystemInfo["canMultiBoot"].keys())):
		if slot == 0:
			if not Recovery:  # called by ImageManager
				continue
			else:  # called by FlashImage
				imagelist[slot] = {"imagename": _("Recovery Mode")}
				continue
		print("[MultiBoot] [getImagelist] slot = ", slot)
		BuildVersion = "  "
		Build = " "  # ViX Build No.
		Dev = " "  # ViX Dev No.
		Creator = " "  # Openpli Openvix Openatv etc
		Date = " "
		BuildType = " "  # release etc
		imagelist[slot] = {"imagename": _("Empty slot")}
		imagedir = "/"
		if SystemInfo["canMultiBoot"]:
			tmp.dir = tempfile.mkdtemp(prefix="Multiboot")
			try:  # Avoid problems Dev lost USB Slots Kexec
				if SystemInfo["canMultiBoot"][slot]['device'] == 'ubi0:ubifs':
					Console().ePopen('mount -t ubifs %s %s' % (SystemInfo["canMultiBoot"][slot]['device'], tmp.dir))
				else:
					Console().ePopen('mount %s %s' % (SystemInfo["canMultiBoot"][slot]['device'], tmp.dir))
			except:
				pass
			imagedir = os.sep.join(filter(None, [tmp.dir, SystemInfo["canMultiBoot"][slot].get('rootsubdir', '')]))
			if os.path.isfile(os.path.join(imagedir, 'usr/bin/enigma2')):
				if os.path.isfile(os.path.join(imagedir, "usr/lib/enigma.info")):
					print("[MultiBoot] [BoxInfo] using BoxInfo")
					BuildVersion = createInfo(slot, imagedir=imagedir)
				else:
					print("[MultiBoot] [getImagelist] 2 slot = %s imagedir = %s" % (slot, imagedir))
					Creator = open("%s/etc/issue" % imagedir).readlines()[-2].capitalize().strip()[:-6]
					print("[MultiBoot] [getImagelist] Creator = %s imagedir = %s" % (Creator, imagedir))
					if Creator.startswith("Openvix"):
						reader = boxbranding_reader(imagedir)
						BuildType = reader.getImageType()
						Build = reader.getImageBuild()
						Creator = Creator.replace("-release", " rel")
						Dev = BuildType != "release" and " %s" % reader.getImageDevBuild() or ""
						date = VerDate(imagedir)
						BuildVersion = "%s %s %s %s (%s)" % (Creator, BuildType[0:3], Build, Dev, date)
					elif SystemInfo["hasKexec"] and os.path.isfile(os.path.join(imagedir, "etc/vtiversion.info")):
						Vti = open(os.path.join(imagedir, "etc/vtiversion.info")).read()
						date = VerDate(imagedir)
						Creator = Vti[0:3]
						Build = Vti[-8:-1]
						BuildVersion = "%s %s (%s) " % (Creator, Build, date)
					else:
						date = VerDate(imagedir)
						Creator = Creator.replace("-release", " ")
						BuildVersion = "%s (%s)" % (Creator, date)
				if SystemInfo["hasKexec"] and Recovery:
					bootmviSlot(imagedir=imagedir, text=BuildVersion, slot=slot)
				imagelist[slot] = {"imagename": "%s" % BuildVersion}
			elif os.path.isfile(os.path.join(imagedir, "usr/bin/enigmax")):
				imagelist[slot] = {"imagename": _("Deleted image")}
			else:
				imagelist[slot] = {"imagename": _("Empty slot")}
			Console().ePopen('umount %s' % tmp.dir)
		if not os.path.ismount(tmp.dir):
			os.rmdir(tmp.dir)
	return imagelist


def createInfo(slot, imagedir="/"):
	BoxInfo = BoxInformation(root=imagedir) if getCurrentImage() != slot else BoxInfoRunningInstance
	Creator = BoxInfo.getItem("distro", " ").capitalize()
	BuildImgVersion = BoxInfo.getItem("imageversion")
	BuildType = BoxInfo.getItem("imagetype")
	BuildVer = BoxInfo.getItem("imagebuild")
	BuildDate = VerDate(imagedir)
	BuildDev = str(BoxInfo.getItem("imagedevbuild")).zfill(3) if BuildType != "rel" else ""
	return "%s %s %s %s %s (%s)" % (Creator, BuildImgVersion, BuildType, BuildVer, BuildDev, BuildDate)


def bootmviSlot(imagedir="/", text=" ", slot=0):
	inmviPath = os.path.join(imagedir, "usr/share/bootlogo.mvi")
	outmviPath = os.path.join(imagedir, "usr/share/enigma2/bootlogo.mvi")
	txtPath = os.path.join(imagedir, "usr/share/enigma2/bootlogo.txt")
	text = "booting slot %s %s" % (slot, text)
	print("[MultiBoot][bootmviSlot] inPath, outpath ", inmviPath, "   ", outmviPath)
	if os.path.exists(inmviPath):
		if os.path.exists(outmviPath) and os.path.exists(txtPath) and open(txtPath).read() == text:
			return
		print("[MultiBoot][bootmviSlot] Copy /usr/share/bootlogo.mvi to /tmp/bootlogo.m1v")
		Console(binary=True).ePopen("cp %s /tmp/bootlogo.m1v" % inmviPath)
		print("[MultiBoot][bootmviSlot] Dump iframe to png")
		Console(binary=True).ePopen("ffmpeg -skip_frame nokey -i /tmp/bootlogo.m1v -vsync 0  -y  /tmp/out1.png 2>/dev/null")
		Console(binary=True).ePopen("rm -f /tmp/mypicture.m1v")
		if os.path.exists("/tmp/out1.png"):
			img = Image.open("/tmp/out1.png")						# Open an Image
		else:
			print("[MultiBoot][bootmviSlot] unable to create new bootlogo cannot open out1.png")
			return
		I1 = ImageDraw.Draw(img)									# Call draw Method to add 2D graphics in an image
		myFont = ImageFont.truetype("/usr/share/fonts/OpenSans-Regular.ttf", 65)		# Custom font style and font size
		print("[MultiBoot][bootmviSlot] Write text to png")
		text = "booting slot %s %s" % (slot, text)
		I1.text((52, 12), text, font=myFont, fill=(255, 0, 0))		# Add Text to an image
		I1.text((50, 10), text, font=myFont, fill=(255, 255, 255))
		img.save("/tmp/out1.png")									# Save the edited image
		print("[MultiBoot][bootmviSlot] Repack bootlogo")
		Console(binary=True).ePopen("ffmpeg -i /tmp/out1.png -r 25 -b 20000 -y /tmp/mypicture.m1v  2>/dev/null")
		Console(binary=True).ePopen("cp /tmp/mypicture.m1v %s" % outmviPath)
		with open(txtPath, "w") as f:
			f.write(text)


def VerDate(imagedir):
	date3 = "00000000"
	date1 = datetime.fromtimestamp(os.stat(os.path.join(imagedir, "var/lib/opkg/status")).st_mtime).strftime("%Y-%m-%d")
	date2 = datetime.fromtimestamp(os.stat(os.path.join(imagedir, "usr/bin/enigma2")).st_mtime).strftime("%Y-%m-%d")
	if fileExists(os.path.join(imagedir, "usr/share/bootlogo.mvi")):
		date3 = datetime.fromtimestamp(os.stat(os.path.join(imagedir, "usr/share/bootlogo.mvi")).st_mtime).strftime("%Y-%m-%d")
	print("[MultiBoot][VerDate]1 date1, date2, date3", date1, "   ", date2, "   ", date3)
	date = max(date1, date2, date3)
	print("[MultiBoot][VerDate]2 date = %s" % date)
	date = datetime.strptime(date, '%Y-%m-%d').strftime("%d-%m-%Y")
	return date
