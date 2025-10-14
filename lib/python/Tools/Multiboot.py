# -*- coding: utf-8 -*-
from Components.Console import Console
from os import rename, rmdir, sep
from os.path import basename, exists, isfile, ismount, join
from re import search
from glob import glob
from tempfile import mkdtemp
from subprocess import check_output
from Components.SystemInfo import SystemInfo, BoxInfo, BoxInformation, MODEL
from Components.About import getBuildDateString


class tmp:
	dir = None


def getMultibootStartupDevice():
	tmp.dir = mkdtemp(prefix="Multiboot")
	bootList = ("/dev/mmcblk0p1", "/dev/mmcblk1p1", "/dev/mmcblk0p3", "/dev/mmcblk0p4", "/dev/mtdblock2", "/dev/block/by-name/bootoptions") if not SystemInfo["hasKexec"] else ("/dev/mmcblk0p4", "/dev/mmcblk0p7", "/dev/mmcblk0p9")
	for device in bootList:
		if exists(device):
			if exists("/dev/block/by-name/flag"):
				Console().ePopen('mount --bind %s %s' % (device, tmp.dir))
			else:
				Console().ePopen('mount %s %s' % (device, tmp.dir))
			if isfile(join(tmp.dir, "STARTUP")):
				print('[Multiboot] Startupdevice found:', device)
				return device
			Console().ePopen('umount %s' % tmp.dir)
	if not ismount(tmp.dir):
		rmdir(tmp.dir)


def getparam(line, param):
	return line.replace("userdataroot", "rootuserdata").rsplit('%s=' % param, 1)[1].split(' ', 1)[0]


def getMultibootslots():
	bootslots = {}
	mode12found = False
	SystemInfo["VuUUIDSlot"] = ""
	UUID = ""
	UUIDnum = 0
	if SystemInfo["MultibootStartupDevice"]:
		for file in glob(join(tmp.dir, 'STARTUP_*')):
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
						if exists(device) or device == 'ubi0:ubifs':
							slot['device'] = device
							slot["slotType"] = "eMMC" if "mmc" in slot["device"] else "USB"
							slot['startupfile'] = basename(file)
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
		if not ismount(tmp.dir):
			rmdir(tmp.dir)
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
	if SystemInfo["canMultiBoot"] and SystemInfo["canMode12"]:
		if (results := search(r"\bboxmode=(\d+)\b", open("/sys/firmware/devicetree/base/chosen/bootargs", "r").read())):
			return int(results.group(1))


def deleteImage(slot):
	tmp.dir = mkdtemp(prefix="Multiboot")
	Console().ePopen('mount %s %s' % (SystemInfo["canMultiBoot"][slot]['device'], tmp.dir))
	enigma2binaryfile = join(sep.join(filter(None, [tmp.dir, SystemInfo["canMultiBoot"][slot].get('rootsubdir', '')])), 'usr/bin/enigma2')
	if exists(enigma2binaryfile):
		rename(enigma2binaryfile, '%s.bak' % enigma2binaryfile)
	Console().ePopen('umount %s' % tmp.dir)
	if not ismount(tmp.dir):
		rmdir(tmp.dir)


def restoreImages():
	for slot in SystemInfo["canMultiBoot"]:
		tmp.dir = mkdtemp(prefix="Multiboot")
		Console().ePopen('mount %s %s' % (SystemInfo["canMultiBoot"][slot]['device'], tmp.dir))
		enigma2binaryfile = join(sep.join(filter(None, [tmp.dir, SystemInfo["canMultiBoot"][slot].get('rootsubdir', '')])), 'usr/bin/enigma2')
		if exists('%s.bak' % enigma2binaryfile):
			rename('%s.bak' % enigma2binaryfile, enigma2binaryfile)
		Console().ePopen('umount %s' % tmp.dir)
		if not ismount(tmp.dir):
			rmdir(tmp.dir)


def getUUIDtoSD(UUID):  # returns None on failure
	check = "/sbin/blkid"
	if exists(check):
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
		imagelist[slot] = {"imagename": _("Empty slot")}
		imagedir = "/"
		draw_bootlogo_norhap = f"{BoxInfo.getItem('distro')} {BoxInfo.getItem('imageversion')} {BoxInfo.getItem('imgrevision')} ({getBuildDateString()})"  # try draw all models distro norhap.
		modelsdraw = MODEL not in ("osmio4kplus", "osmio4k")
		if SystemInfo["canMultiBoot"]:
			tmp.dir = mkdtemp(prefix="Multiboot")
			try:  # Avoid problems Dev lost USB Slots Kexec
				if SystemInfo["canMultiBoot"][slot]['device'] == 'ubi0:ubifs':
					Console().ePopen('mount -t ubifs %s %s' % (SystemInfo["canMultiBoot"][slot]['device'], tmp.dir))
				else:
					Console().ePopen('mount %s %s' % (SystemInfo["canMultiBoot"][slot]['device'], tmp.dir))
			except:
				pass
			imagedir = sep.join(filter(None, [tmp.dir, SystemInfo["canMultiBoot"][slot].get('rootsubdir', '')]))
			if isfile(join(imagedir, 'usr/bin/enigma2')):
				imagelist[slot] = {'imagename': getSlotImageInfo(slot, imagedir=imagedir)}
				if not isfile(join(imagedir, "usr/share/enigma2/.bootlogotxt")) and not isfile("/usr/share/enigma2/.bootlogotxt") and SystemInfo["hasKexec"]:
					bootmviSlot(imagedir=imagedir, text=getSlotImageInfo(slot, imagedir=imagedir), slot=slot)
				if not isfile(join(imagedir, "usr/lib/enigma.info")):
					print("[MultiBoot] [getImagelist] 2 slot = %s imagedir = %s" % (slot, imagedir))
					creator = open("%s/etc/issue" % imagedir).readlines()[-2].capitalize().strip()[:-6]
					print("[MultiBoot] [getImagelist] creator = %s imagedir = %s" % (creator, imagedir))
					if SystemInfo["hasKexec"] and isfile(join(imagedir, "etc/vtiversion.info")):
						VTI = open(join(imagedir, "etc/vtiversion.info")).read()
						date = getSlotCompileDate(imagedir)
						creator = VTI[0:3]
						build = VTI[-8:-1]
						imagelist[slot] = f"{creator} {build} ({date})"
					else:
						date = getSlotCompileDate(imagedir)
						creator = creator.replace("-release", " ")
						imagelist[slot] = f"{creator} ({date})"
			elif isfile(join(imagedir, "usr/bin/enigma2.bak")):
				imagelist[slot] = {"imagename": _("Deleted image")}
			else:
				imagelist[slot] = {"imagename": _("Empty slot")}
			Console().ePopen('umount %s' % tmp.dir)
			if not isfile("/usr/share/enigma2/.bootlogotxt") and modelsdraw:
				bootmviSlot(imagedir=imagedir, text=draw_bootlogo_norhap, slot=slot)
		if not ismount(tmp.dir):
			rmdir(tmp.dir)
	return imagelist


def getSlotImageInfo(slot, imagedir="/"):
	BoxInfoInstance = BoxInformation(root=imagedir) if getCurrentImage() != slot else BoxInfo
	Creator = BoxInfoInstance.getItem("distro", " ").capitalize()
	BuildImgVersion = BoxInfoInstance.getItem("imageversion")
	BuildType = BoxInfoInstance.getItem("imagetype")
	BuildDate = getSlotCompileDate(imagedir)
	return " ".join([x for x in (Creator, BuildImgVersion, BuildType, "(%s)" % BuildDate) if x])


def bootmviSlot(imagedir="/", text="", slot=""):
	if not isfile(join(imagedir, "usr/share/enigma2/bootlogo.mvi")):
		slot = getCurrentImage()
		dirusr = "/usr"
	else:
		dirusr = "usr"
	inmvipath = join(imagedir, f"{dirusr}/share/enigma2/bootlogo.mvi")
	outmvipath = join(imagedir, f"{dirusr}/share/enigma2/bootlogo.mvi")
	txtpath = join(imagedir, f"{dirusr}/share/enigma2/.bootlogotxt")
	text = _("Booting in slot %s %s") % (slot, text)
	tmp = join(imagedir, "tmp") if isfile(join(imagedir, "usr/share/enigma2/bootlogo.mvi")) else "/tmp"
	print("[MultiBoot][bootmviSlot] inPath, outpath ", inmvipath, " ", outmvipath)
	from PIL import Image, ImageDraw, ImageFont
	print(f"[MultiBoot][bootmviSlot] Copy usr/share/enigma2/bootlogo.mvi to {tmp}/bootlogo.m1v and Dump iframe to png")
	Console(binary=True).ePopen(f"cp {inmvipath} {tmp}/bootlogo.m1v ; ffmpeg -skip_frame nokey -i {tmp}/bootlogo.m1v -vsync 0 -y {tmp}/drawbootlogo.png 2>/dev/null")
	if exists(f"{tmp}/drawbootlogo.png"):
		img = Image.open(f"{tmp}/drawbootlogo.png")  # Open an Image
	else:
		print("[MultiBoot][bootmviSlot] unable to create new bootlogo cannot open drawbootlogo.png")
		return
	draw = ImageDraw.Draw(img)  # Call draw Method to add 2D graphics in an image
	myFont = ImageFont.truetype("/usr/share/fonts/DejaVuSansCondensed-Bold.ttf", 30)  # Custom font style and font size
	print("[MultiBoot][bootmviSlot] Write text to png")
	draw.text((50, 25), text, font=myFont, fill=(255, 255, 255))
	img.save(f"{tmp}/drawbootlogo.png")  # Save the edited image
	print("[MultiBoot][bootmviSlot] Repack bootlogo")
	Console(binary=True).ePopen(f"ffmpeg -i {tmp}/drawbootlogo.png -r 25 -b 20000 -y {tmp}/mypicture.m1v 2>/dev/null ; mv {tmp}/mypicture.m1v {inmvipath} ; rm -f {tmp}/drawbootlogo.png {tmp}/bootlogo.m1v")
	with open(txtpath, "w") as f:
		f.write(text)


def getSlotCompileDate(imagedir):
	if isfile(join(imagedir, "usr/lib/enigma.info")):
		date = ""
		enigmainfo = join(imagedir, "usr/lib/enigma.info")
		with open(enigmainfo, "r") as f:
			for compiledate in f.readlines():
				if "compiledate" in compiledate:
					fulldate = compiledate.split("compiledate='")[1].split("'")[0]
					date = fulldate[6:8] + '-' + fulldate[4:6] + '-' + fulldate[0:4]
					break
		return date
