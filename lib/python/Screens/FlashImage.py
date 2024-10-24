from Screens.ChoiceBox import ChoiceBox
from os import access, listdir, major, minor, mkdir, remove, rmdir, sep, stat, statvfs, walk, W_OK
from os.path import exists, isdir, isfile, islink, ismount, join, normpath, splitext
from json import load
from zipfile import ZipFile
from shutil import copyfile, rmtree
from tempfile import mkdtemp
from struct import pack
from urllib.request import urlopen, Request

from enigma import eEPGCache, eEnv
from xml.etree.ElementTree import parse
from re import sub

from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Standby import getReasons, QUIT_RESTART, TryQuitMainloop
from Components.Sources.StaticText import StaticText
from Components.ChoiceList import ChoiceList, ChoiceEntryComponent
from Components.config import config, configfile
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Console import Console
from Components.Harddisk import Harddisk
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from Components.SystemInfo import SystemInfo, MODEL
from Tools.Geolocation import geolocation
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.Downloader import DownloadWithProgress
from Tools.Multiboot import getImagelist, getCurrentImage, getCurrentImageMode, deleteImage, restoreImages
from Components.Harddisk import harddiskmanager


def checkimagefiles(files):
	return len([x for x in files if 'kernel' in x and '.bin' in x or x in ('uImage', 'rootfs.bin', 'root_cfe_auto.bin', 'root_cfe_auto.jffs2', 'oe_rootfs.bin', 'e2jffs2.img', 'rootfs.tar.bz2', 'rootfs.ubi')]) == 2


class SelectImage(Screen):
	def __init__(self, session, *args):
		Screen.__init__(self, session)
		self.jsonlist = {}
		self.imagesList = {}
		self.setIndex = 0
		self.expanded = []
		self.url_feeds = parse(eEnv.resolve("${datadir}/enigma2/imagefeeds.xml")).getroot()
		self.selectedImage = self.getSelectedImageFeed("OpenPLi")
		self.setTitle(_("Multiboot image selector"))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText()
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText(_("Other Images"))
		self["description"] = StaticText()
		self["list"] = ChoiceList(list=[ChoiceEntryComponent('', ((_("Retrieving image list - Please wait...")), "Waiter"))])

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "KeyboardInputActions", "MenuActions"],
		{
			"ok": self.keyOk,
			"cancel": boundFunction(self.close, None),
			"red": boundFunction(self.close, None),
			"green": self.keyOk,
			"yellow": self.keyDelete,
			"blue": self.otherImages,
			"up": self.keyUp,
			"down": self.keyDown,
			"left": self.keyLeft,
			"right": self.keyRight,
			"upUp": self.doNothing,
			"downUp": self.doNothing,
			"rightUp": self.doNothing,
			"leftUp": self.doNothing,
			"upRepeated": self.keyUp,
			"downRepeated": self.keyDown,
			"leftRepeated": self.keyUp,
			"rightRepeated": self.keyDown,
			"menu": boundFunction(self.close, True),
		}, -1)

		self.callLater(self.getImagesList)

	def getSelectedImageFeed(self, selectedImage):
		for feed_info in self.url_feeds:
			if feed_info.tag == "ImageFeed" and feed_info.attrib["name"] == selectedImage:
				return feed_info.attrib

	def getImagesList(self):

		def getImages(path, files):
			for file in [x for x in files if splitext(x)[1] == ".zip" and MODEL in x]:
				try:
					if checkimagefiles([x.split(sep)[-1] for x in ZipFile(file).namelist()]):
						imagetyp = _("Downloaded Images")
						if 'backup' in file.split(sep)[-1]:
							imagetyp = _("Fullbackup Images")
						if imagetyp not in self.imagesList:
							self.imagesList[imagetyp] = {}
						self.imagesList[imagetyp][file] = {'link': file, 'name': file.split(sep)[-1]}
				except:
					pass

		if not self.imagesList:
			if not self.jsonlist:
				if "MODEL" in self.selectedImage:
					for expression in eval(self.url_feeds.find(self.selectedImage["MODEL"]).text):
						model = sub(expression[0], expression[1], MODEL)
						url = f'{self.selectedImage["url"]}{model}'
				else:
					url = f'{self.selectedImage["url"]}{MODEL}'
				try:
					req = Request(url, None, {"User-agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5"})
					self.jsonlist.update(load(urlopen(req, timeout=3)))
				except:
					print("[FlashImage] getImagesList Error: Unable to load json data from URL '%s'!" % url)
			self.imagesList = dict(self.jsonlist)
			for mountdir in ["/media", "/media/net", "/media/autofs"]:
				for media in [f"{mountdir}/{x}" for x in listdir(mountdir)] if isdir(mountdir) else []:
					if ismount(media):
						try:
							getImages(media, [join(media, x) for x in listdir(media) if splitext(x)[1] == ".zip" and MODEL in x])
						except Exception:
							break
						for folder in ["images", "downloaded_images", "imagebackups"]:
							if folder in listdir(media):
								subfolder = join(media, folder)
								if isdir(subfolder) and not islink(subfolder) and not ismount(subfolder):
									getImages(subfolder, [join(subfolder, x) for x in listdir(subfolder) if splitext(x)[1] == ".zip" and MODEL in x])
									for directory in [directory for directory in [join(subfolder, directory) for directory in listdir(subfolder)] if isdir(directory) and splitext(directory)[1] == ".unzipped"]:
										rmtree(directory)
										break
		list = []
		for catagorie in reversed(sorted(self.imagesList.keys())):
			if catagorie in self.expanded:
				list.append(ChoiceEntryComponent('expanded', ((str(catagorie)), "Expander")))
				for image in reversed(sorted(self.imagesList[catagorie].keys())):
					list.append(ChoiceEntryComponent('verticalline', ((str(self.imagesList[catagorie][image]['name'])), str(self.imagesList[catagorie][image]['link']))))
			else:
				for image in self.imagesList[catagorie].keys():
					list.append(ChoiceEntryComponent('expandable', ((str(catagorie)), "Expander")))
					break
		if not hasattr(self, "list") and list:
			self["list"].setList(list)
			if self.setIndex:
				self["list"].moveToIndex(self.setIndex if self.setIndex < len(list) else len(list) - 1)
				if self["list"].l.getCurrentSelection()[0][1] == "Expander":
					self.setIndex -= 1
					if self.setIndex:
						self["list"].moveToIndex(self.setIndex if self.setIndex < len(list) else len(list) - 1)
				self.setIndex = 0
			self.selectionChanged()
		else:
			self["list"].setList([ChoiceEntryComponent('', ((_("Cannot find images - please try later or select an alternate image")), "Waiter"))])

	def keyOk(self):
		currentSelected = self["list"].l.getCurrentSelection()
		if currentSelected[0][1] == "Expander":
			if currentSelected[0][0] in self.expanded:
				self.expanded.remove(currentSelected[0][0])
			else:
				self.expanded.append(currentSelected[0][0])
			self.getImagesList()
		elif currentSelected[0][1] != "Waiter":
			self.session.openWithCallback(self.reloadImagesList, FlashImage, currentSelected[0][0], currentSelected[0][1])

	def reloadImagesList(self):
		self["list"].setList([ChoiceEntryComponent('', ((_("Retrieving image list - Please wait...")), "Waiter"))])
		self["list"].moveToIndex(0)
		self.selectionChanged()
		self.imagesList = {}
		self.callLater(self.getImagesList)

	def keyDelete(self):
		currentSelected = self["list"].l.getCurrentSelection()[0][1]
		if not ("://" in currentSelected or currentSelected in ["Expander", "Waiter"]):
			try:
				remove(currentSelected)
				currentSelected = ".".join([currentSelected[:-4], "unzipped"])
				if isdir(currentSelected):
					rmtree(currentSelected)
				self.setIndex = self["list"].getSelectedIndex()
				self.imagesList = []
				self.getImagesList()
			except:
				self.session.open(MessageBox, _("Cannot delete downloaded image"), MessageBox.TYPE_ERROR, timeout=3)

	def otherImages(self):
		self.session.openWithCallback(self.otherImagesCallback, ChoiceBox, list=sorted([(feedinfo.attrib["name"], feedinfo.attrib) for feedinfo in self.url_feeds if feedinfo.tag == "ImageFeed" and "OpenPLi" not in feedinfo.attrib["name"]]), windowTitle=_("Select Image"))

	def otherImagesCallback(self, image):
		if image:
			self.selectedImage = image[1]
			self.jsonlist = {}
			self.expanded = []
			self.reloadImagesList()

	def selectionChanged(self):
		currentSelected = self["list"].l.getCurrentSelection()
		if "://" in currentSelected[0][1] or currentSelected[0][1] in ["Expander", "Waiter"]:
			self["key_yellow"].setText("")
		else:
			self["key_yellow"].setText(_("Delete image"))
		if currentSelected[0][1] == "Waiter":
			self["key_green"].setText("")
		else:
			if currentSelected[0][1] == "Expander":
				self["key_green"].setText(_("Compress") if currentSelected[0][0] in self.expanded else _("Expand"))
				self["description"].setText("")
			else:
				self["key_green"].setText(_("Flash Image"))
				self["description"].setText(currentSelected[0][1])

	def keyLeft(self):
		self["list"].instance.moveSelection(self["list"].instance.pageUp)
		self.selectionChanged()

	def keyRight(self):
		self["list"].instance.moveSelection(self["list"].instance.pageDown)
		self.selectionChanged()

	def keyUp(self):
		self["list"].instance.moveSelection(self["list"].instance.moveUp)
		self.selectionChanged()

	def keyDown(self):
		self["list"].instance.moveSelection(self["list"].instance.moveDown)
		self.selectionChanged()

	def doNothing(self):
		pass


class FlashImage(Screen):
	skin = """<screen position="center,center" size="640,200" flags="wfNoBorder" backgroundColor="#54242424">
		<widget name="header" position="5,10" size="e-10,50" font="Regular;40" backgroundColor="#54242424"/>
		<widget name="info" position="5,60" size="e-10,130" font="Regular;24" backgroundColor="#54242424"/>
		<widget name="progress" position="5,145" size="e-10,24" backgroundColor="#54242424"/>
		<widget name="progress_counter" position="5,175" size="e-10,24" font="Regular;24" backgroundColor="#54242424"/>
	</screen>"""

	BACKUP_SCRIPT = resolveFilename(SCOPE_PLUGINS, "Extensions/AutoBackup/settings-backup.sh")

	def __init__(self, session, imagename, source):
		Screen.__init__(self, session)
		self.containerbackup = None
		self.containerofgwrite = None
		self.getImageList = None
		self.downloader = None
		self.source = source
		self.imagename = imagename
		self.reasons = getReasons(session)
		self.path = None
		self.folderunzipped = None
		self["header"] = Label(_("Backup settings"))
		self["info"] = Label(_("Save settings and EPG data"))
		self["progress"] = ProgressBar()
		self["progress"].setRange((0, 100))
		self["progress"].setValue(0)
		self["progress_counter"] = Label("")
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"cancel": self.abort,
			"red": self.abort,
			"ok": self.ok,
			"green": self.ok,
		}, -1)
		try:
			for partition in harddiskmanager.getMountedPartitions():
				self.path = normpath(partition.mountpoint)
				if self.path != "/":
					self.folderunzipped = join(self.path, self.imagename + ".unzipeed")
					folderunzipped = self.path + '/' + self.folderunzipped
					if exists(folderunzipped):
						Console().ePopen('rm -rf ' + folderunzipped)
		except Exception as err:
			print(str(err))
		self.callLater(self.confirmation)

	def confirmation(self):
		if self.reasons:
			self.message = f"{self.reasons}\n" + _("Do you still want to flash image?\n") + f"{self.imagename}"
		else:
			self.message = _("Do you want to flash image\n") + f"{self.imagename}" if not SystemInfo["canKexec"] else _("Unable to complete - Kexec Multiboot files missing!")
		if SystemInfo["canMultiBoot"] and SystemInfo["HasUsbhdd"]:
			imagesList = getImagelist()
			currentimageslot = getCurrentImage()
			choices = []
			slotdict = {k: v for k, v in SystemInfo["canMultiBoot"].items() if not v['device'].startswith('/dev/sda')} if not SystemInfo["HasKexecUSB"] else {k: v for k, v in SystemInfo["canMultiBoot"].items()}
			numberSlots = len(slotdict) + 1 if not SystemInfo["hasKexec"] else len(slotdict)
			for x in range(1, numberSlots):
				choices.append(((f"slot{x} - {imagesList[x]['imagename']} " + _("(current image) with, backup") if x == currentimageslot else f"slot{x} - {imagesList[x]['imagename']} " + _("with backup"), (x, "with backup"))))
			for x in range(1, numberSlots):
				choices.append(((f"slot{x} - {imagesList[x]['imagename']} " + _("(current image), without backup") if x == currentimageslot else f"slot{x} - {imagesList[x]['imagename']} " + _("without backup"), (x, "without backup"))))
			if "://" in self.source:
				choices.append((_("No, only image download"), (1, "only download")))
			choices.append((_("No, do not flash image"), False))
			self.session.openWithCallback(self.checkMedia, MessageBox, self.message, list=choices, default=currentimageslot, simple=True)
		else:
			choices = [(_("Yes, with backup"), "with backup"), (_("Yes, without backup"), "without backup")] if not SystemInfo["canKexec"] else []
			if "://" in self.source:
				choices.append((_("No, only image download"), "only download"))
			choices.append((_("No, do not flash image"), False))
			self.session.openWithCallback(self.checkMedia, MessageBox, self.message, list=choices, default=False, simple=True)

	def checkMedia(self, retval):
		if retval:
			if SystemInfo["canMultiBoot"]:
				self.multibootslot = retval[0]
				doBackup = retval[1] == "with backup"
				self.onlyDownload = retval[1] == "only download"
			else:
				doBackup = retval == "with backup"
				self.onlyDownload = retval == "only download"

			def findmedia(path):
				def avail(path):
					if not path.startswith('/mmc') and isdir(path) and access(path, W_OK):
						try:
							statvfspath = statvfs(path)
							return (statvfspath.f_bavail * statvfspath.f_frsize) / (1 << 20)
						except:
							pass

				def checkIfDevice(path, diskstats):
					st_dev = stat(path).st_dev
					return (major(st_dev), minor(st_dev)) in diskstats

				print("[FlashImage] Read /proc/diskstats")
				diskstats = [(int(x[0]), int(x[1])) for x in [x.split()[0:3] for x in open('/proc/diskstats').readlines()] if x[2].startswith("sd")]
				if isdir(path) and checkIfDevice(path, diskstats) and avail(path) > 500:
					return (path, True)
				mounts = []
				devices = []
				for mountdir in ["/media", "/media/net", "/media/autofs"]:
					for path in [f"{mountdir}/{x}" for x in listdir(mountdir)] if isdir(mountdir) else []:
						if ismount(path):
							if checkIfDevice(path, diskstats):
								devices.append((path, avail(path)))
							else:
								mounts.append((path, avail(path)))
				devices.sort(key=lambda x: x[1], reverse=True)
				mounts.sort(key=lambda x: x[1], reverse=True)
				return ((devices[0][1] > 500 and (devices[0][0], True)) if devices else mounts and mounts[0][1] > 500 and (mounts[0][0], False)) or (None, None)
			try:
				self.destination, isDevice = findmedia(isfile(self.BACKUP_SCRIPT) and hasattr(config.plugins, "autobackup") and config.plugins.autobackup.where.value or "/media/hdd")
			except:
				self.session.openWithCallback(self.abort, MessageBox, _("No storage devices found"), type=MessageBox.TYPE_ERROR, simple=True)
				return
			if self.destination:
				destination = join(self.destination, 'downloaded_images')
				self.zippedimage = "://" in self.source and join(destination, self.imagename) or self.source
				self.unzippedimage = join(destination, f'{self.imagename[:-4]}'".unzipped")
				try:
					if isfile(destination):
						remove(destination)
					if not isdir(destination):
						mkdir(destination)
					if doBackup:
						if isDevice:
							self.startBackupsettings(True)
						else:
							self.session.openWithCallback(self.startBackupsettings, MessageBox, _("Can only find a network drive to store the backup this means after the flash the autorestore will not work. Alternativaly you can mount the network drive after the flash and perform a manufacurer reset to autorestore"), simple=True)
					else:
						self.startDownload()
				except:
					pass
			else:
				self.session.openWithCallback(self.abort, MessageBox, _("Could not find suitable media - Please remove some downloaded images or insert a media (e.g. USB stick) with sufficiant free space and try again!"), type=MessageBox.TYPE_ERROR, simple=True)
		else:
			self.abort()

	def startBackupsettings(self, retval):
		if retval:
			if isfile(self.BACKUP_SCRIPT):
				self["info"].setText(_("Backing up to: %s") % self.destination)
				configfile.save()
				if config.plugins.autobackup.epgcache.value:
					eEPGCache.getInstance().save()
				self.containerbackup = Console()
				self.containerbackup.ePopen("%s%s'%s' %s" % (self.BACKUP_SCRIPT, config.plugins.autobackup.autoinstall.value and " -a " or " ", self.destination, int(config.plugins.autobackup.prevbackup.value)), self.backupsettingsDone)
			else:
				self.session.openWithCallback(self.startDownload, MessageBox, _("Unable to backup settings as the AutoBackup plugin is missing, do you want to continue?"), default=False, simple=True)
		else:
			self.abort()

	def backupsettingsDone(self, data, retval, extra_args):
		self.containerbackup = None
		if retval == 0:
			self.startDownload()
		else:
			self.session.openWithCallback(self.abort, MessageBox, _("Error during backup settings\n") + f"{retval}", type=MessageBox.TYPE_ERROR, simple=True)

	def startDownload(self, reply=True):
		self.show()
		if reply:
			geolocationData = geolocation.getGeolocationData(fields="status")
			if not geolocationData.get("status", None):
				self.session.openWithCallback(self.abort, MessageBox, _("Your internet connection is not working."), type=MessageBox.TYPE_ERROR, simple=True)
				return
			if "://" in self.source:
				self["header"].setText(_("Downloading Image"))
				self["info"].setText(self.imagename)
				self.downloader = DownloadWithProgress(self.source.replace(" ", "%20"), self.zippedimage)
				self.downloader.addProgress(self.downloadProgress)
				self.downloader.addEnd(self.downloadEnd)
				self.downloader.addError(self.downloadError)
				self.downloader.start()
			else:
				self.unzip()
		else:
			self.abort()

	def downloadProgress(self, current, total):
		self["progress"].setValue(int(100 * current / total))
		self.progressCounter = int(100 * current / total)
		self["progress_counter"].setText(str(self.progressCounter) + " %")

	def downloadError(self, reason, status):
		self.downloader.stop()
		self.session.openWithCallback(self.abort, MessageBox, _("Error during downloading image\n") + f"{self.imagename}\n" + f"{reason}", type=MessageBox.TYPE_ERROR, simple=True)

	def downloadEnd(self, outputFile):
		self.downloader.stop()
		self["progress_counter"].hide()
		self.unzip()

	def unzip(self):
		if self.onlyDownload:
			self.session.openWithCallback(self.abort, MessageBox, _("Download successfully\n") + f"{self.imagename}", type=MessageBox.TYPE_INFO, simple=True)
		else:
			self["header"].setText(_("Unzipping Image"))
			self["info"].setText(f"{self.imagename}\n" + _("Please wait"))
			self["progress"].hide()
			self.callLater(self.doUnzip)

	def doUnzip(self):
		try:
			ZipFile(self.zippedimage, 'r').extractall(self.unzippedimage)
			self.flashimage()
		except:
			self.session.openWithCallback(self.abort, MessageBox, _("Error during unzipping image\n") + f"{self.imagename}", type=MessageBox.TYPE_ERROR, simple=True)

	def flashimage(self):
		self["header"].setText(_("Flashing Image"))

		def findimagefiles(path):
			for path, subdirs, files in walk(path):
				if not subdirs and files:
					return checkimagefiles(files) and path
		imagefiles = findimagefiles(self.unzippedimage)
		mtd = SystemInfo["canMultiBoot"][self.multibootslot]["device"].split("/")[2]  # USB get mtd root fs slot kexec
		if imagefiles:
			if SystemInfo["canMultiBoot"] and not SystemInfo["hasKexec"]:
				command = f"/usr/bin/ofgwrite -k -r -m{self.multibootslot} '{imagefiles}'"
			elif not SystemInfo["canMultiBoot"]:
				command = f"/usr/bin/ofgwrite -k -r '{imagefiles}'"
			else:  # kexec
				if self.multibootslot == 0:
					from boxbranding import getMachineMtdKernel, getMachineMtdRoot
					kz0 = getMachineMtdKernel()
					rz0 = getMachineMtdRoot()
					command = f"/usr/bin/ofgwrite -kkz0 -rrz0 '{imagefiles}'"  # slot0 treat as kernel/root only multiboot receiver
				if SystemInfo["HasKexecUSB"] and mtd and "mmcblk" not in mtd:
					command = f"/usr/bin/ofgwrite -r{mtd} -kzImage -s'{MODEL[2:]}/linuxrootfs' -m{self.multibootslot} '{imagefiles}'"  # USB flash slot kexec
				else:
					command = f"/usr/bin/ofgwrite -k -r -m{self.multibootslot} '{imagefiles}'"  # eMMC flash slot kexec
			self.containerofgwrite = Console()
			self.containerofgwrite.ePopen(command, self.FlashimageDone)
		else:
			self.session.openWithCallback(self.abort, MessageBox, _("Image to install is invalid\n") + f"{self.imagename}", type=MessageBox.TYPE_ERROR, simple=True)

	def FlashimageDone(self, data, retval, extra_args):
		try:
			if exists(self.unzippedimage):
				Console().ePopen('rm -r -f ' + self.unzippedimage)
		except Exception as err:
			print(str(err))
		self.containerofgwrite = None
		if retval == 0:
			self["header"].setText(_("Flashing image successful"))
			self["info"].setText(f"{self.imagename}\n" + _("Press ok for multiboot selection\nPress exit to close"))
		else:
			self.session.openWithCallback(self.abort, MessageBox, _("Flashing image was not successful\n") + f"{self.imagename}", type=MessageBox.TYPE_ERROR, simple=True)

	def abort(self, reply=None):
		if self.getImageList or self.containerofgwrite:
			return 0
		if self.downloader:
			self.downloader.stop()
		if self.containerbackup:
			self.containerbackup.killAll()
		self.close()

	def ok(self):
		if self["header"].text == _("Flashing image successful"):
			self.session.openWithCallback(self.abort, MultibootSelection)
		else:
			return 0


class MultibootSelection(SelectImage, HelpableScreen):
	def __init__(self, session, *args):
		SelectImage.__init__(self, session)
		HelpableScreen.__init__(self)
		self.skinName = ["MultibootSelection", "SelectImage"]
		self.expanded = []
		self.tmp_dir = None
		self.setTitle(_("Multiboot image selector"))
		usbIn = SystemInfo["HasUsbhdd"].keys() and SystemInfo["hasKexec"]
		self["key_red"] = StaticText(_("Cancel") if not usbIn else _("Add USB slots"))
		self["key_green"] = StaticText(_("Reboot"))
		self["description"] = StaticText()
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText()
		self["list"] = ChoiceList([])
		self["actions"] = HelpableActionMap(self, ["OkCancelActions", "ColorActions", "DirectionActions", "KeyboardInputActions", "MenuActions"],
		{
			"ok": self.keyOk,
			"cancel": (self.cancel, _("Cancel the image selection and exit")),
			"red": (self.cancel, _("Cancel")) if not usbIn else (self.KexecMount, _("Add USB slots (require receiver Vu+ 4k)")),
			"green": (self.keyOk, _("Select image and reboot")),
			"yellow": (self.deleteImage, _("Select image and delete")),
			"blue": (self.order, _("Orde image per modes and slots (require receiver with mode slot 12)")),
			"up": self.keyUp,
			"down": self.keyDown,
			"left": self.keyLeft,
			"right": self.keyRight,
			"upRepeated": self.keyUp,
			"downRepeated": self.keyDown,
			"leftRepeated": self.keyUp,
			"rightRepeated": self.keyDown,
			"upUp": self.doNothing,
			"downUp": self.doNothing,
			"rightUp": self.doNothing,
			"leftUp": self.doNothing,
			"menu": boundFunction(self.cancel, True),
		}, -1)

		self.blue = False
		self.currentimageslot = getCurrentImage()
		self.tmp_dir = mkdtemp(prefix="MultibootSelection")
		Console().ePopen(f'mount {SystemInfo["MultibootStartupDevice"]} {self.tmp_dir}')
		self.getImagesList()

	def cancel(self, value=None):
		Console().ePopen(f'umount {self.tmp_dir}')
		if not ismount(self.tmp_dir) and exists(self.tmp_dir):
			rmdir(self.tmp_dir)
		if value == 2 and not exists(self.tmp_dir):
			self.session.open(TryQuitMainloop, 2)
		else:
			self.close(value)

	def getImagesList(self):
		list = []
		list12 = []
		imagesList = getImagelist()
		mode = getCurrentImageMode() or 0
		self.deletedImagesExists = False
		if imagesList:
			for index, x in enumerate(imagesList):
				if SystemInfo["hasKexec"] and x == 1:
					self["description"].setText(_("Select slot image and press OK or GREEN button to reboot."))
					if not self.currentimageslot:  # Slot0
						list.append(ChoiceEntryComponent('', ((_(f'slot0 {SystemInfo["canMultiBoot"][x]["slotType"]} ' + _("- Recovery mode image (current)"))), "Recovery")))
					else:
						list.append(ChoiceEntryComponent('', ((_(f'slot0 {SystemInfo["canMultiBoot"][x]["slotType"]} ' + _("- Recovery mode image"))), "Recovery")))
				if imagesList[x]["imagename"] == _("Deleted image"):
					self.deletedImagesExists = True
				elif imagesList[x]["imagename"] != _("Empty slot"):
					if SystemInfo["canMode12"]:
						list.insert(index, ChoiceEntryComponent('', ((f'slot{x} {SystemInfo["canMultiBoot"][x]["slotType"]} - {imagesList[x]["imagename"]} ' + _("mode 1 (current image)") if x == self.currentimageslot and mode != 12 else f'slot{x} {SystemInfo["canMultiBoot"][x]["slotType"]} - {imagesList[x]["imagename"]} ' + _("mode 1"), (x, 1)))))
						list12.insert(index, ChoiceEntryComponent('', ((f'slot{x} {SystemInfo["canMultiBoot"][x]["slotType"]} - {imagesList[x]["imagename"]} ' + _("mode 12 (current image)") if x == self.currentimageslot and mode == 12 else f'slot{x} {SystemInfo["canMultiBoot"][x]["slotType"]} - {imagesList[x]["imagename"]} ' + _("mode 12"), (x, 12)))))
					else:
						if not SystemInfo["hasKexec"]:
							list.append(ChoiceEntryComponent('', ((f'slot{x} {SystemInfo["canMultiBoot"][x]["slotType"]} - {imagesList[x]["imagename"]} ' + _("(current image)") if x == self.currentimageslot and mode != 12 else f'slot{x} {SystemInfo["canMultiBoot"][x]["slotType"]} {imagesList[x]["imagename"]}', (x, 1)))))
						else:
							if x != self.currentimageslot:
								list.append(ChoiceEntryComponent('', ((f'slot{x} {SystemInfo["canMultiBoot"][x]["slotType"]} - {imagesList[x]["imagename"]}', (x, 1)))))  # list USB eMMC slots not current
							else:
								list.append(ChoiceEntryComponent('', ((f'slot{x} {SystemInfo["canMultiBoot"][x]["slotType"]} - {imagesList[x]["imagename"]} ' + _("(current image)"), (x, 1)))))  # Slot current != Slot0
		if list12:
			self.blue = True
			self["key_blue"].setText(_("Order by modes") if config.usage.multiboot_order.value else _("Order by slots"))
			list += list12
			list = sorted(list) if config.usage.multiboot_order.value else list
		if isfile(join(self.tmp_dir, "STARTUP_RECOVERY")) and not SystemInfo["hasKexec"]:
			list.append(ChoiceEntryComponent('', ((_("Boot to Recovery menu")), "Recovery")))
			self["description"].setText(_("Select image or boot to recovery menu and press OK or GREEN button for reboot."))
		if isfile(join(self.tmp_dir, "STARTUP_ANDROID")):
			list.append(ChoiceEntryComponent('', ((_("Boot to Android image")), "Android")))
			self["description"].setText(_("Select image or boot to Android image and press OK or GREEN button for reboot."))
		if list12 or list:
			if not isfile(join(self.tmp_dir, "STARTUP_RECOVERY")) and not isfile(join(self.tmp_dir, "STARTUP_ANDROID")):
				self["description"].setText(_("Select image and press OK or GREEN button for reboot."))
		if not list:
			list.append(ChoiceEntryComponent('', ((_("No images found")), "Waiter")))
		self["list"].setList(list)
		self.selectionChanged()

	def deleteImage(self):
		if self["key_yellow"].text == _("Restore deleted images"):
			self.session.openWithCallback(self.deleteImageCallback, MessageBox, _("Want to restore all deleted images?"), simple=True)
		elif self["key_yellow"].text == _("Delete Image"):
			self.session.openWithCallback(self.deleteImageCallback, MessageBox, _("Are you sure to delete image:\n") + f"{self.currentSelected[0][0]}", simple=True)

	def deleteImageCallback(self, answer):
		if answer:
			if self["key_yellow"].text == _("Restore deleted images"):
				restoreImages()
			else:
				deleteImage(self.currentSelected[0][1][0])
			self.getImagesList()

	def order(self):
		if self.blue:
			self["list"].setList([])
			config.usage.multiboot_order.value = not config.usage.multiboot_order.value
			config.usage.multiboot_order.save()
			self.getImagesList()

	def keyOk(self):
		self.session.openWithCallback(self.doReboot, MessageBox, _("Are you sure to reboot to:\n") + f"{self.currentSelected[0][0]}", simple=True)

	def doReboot(self, answer):
		if answer:
			slot = self.currentSelected[0][1]
			if slot == "Recovery" and isfile(join(self.tmp_dir, "STARTUP_RECOVERY")):
				copyfile(join(self.tmp_dir, "STARTUP_RECOVERY"), join(self.tmp_dir, "STARTUP"))
			elif slot == "Android" and isfile(join(self.tmp_dir, "STARTUP_ANDROID")):
				copyfile(join(self.tmp_dir, "STARTUP_ANDROID"), join(self.tmp_dir, "STARTUP"))
			elif SystemInfo["canMultiBoot"][slot[0]]['startupfile']:
				if SystemInfo["canMode12"]:
					startupfile = join(self.tmp_dir, f"{SystemInfo['canMultiBoot'][slot[0]]['startupfile'].rsplit('_', 1)[0]}_{slot[1]}")
				else:
					startupfile = join(self.tmp_dir, f"{SystemInfo['canMultiBoot'][slot[0]]['startupfile']}")
				if SystemInfo["canDualBoot"]:
					with open('/dev/block/by-name/flag', 'wb') as f:
						f.write(pack("B", int(slot[0])))
					startupfile = join(f"/boot, {SystemInfo['canMultiBoot'][slot[0]]['startupfile']}")
					if isfile(startupfile):
						copyfile(startupfile, join("/boot", "STARTUP"))
				else:
					if isfile(startupfile):
						copyfile(startupfile, join(self.tmp_dir, "STARTUP"))
			else:
				if slot[1] == 1:
					startupFileContents = f"boot emmcflash0.kernel{slot[0]} 'root=/dev/mmcblk0p{slot[0] * 2 + 1} rw rootwait {MODEL}_4.boxmode=1'\n"
				else:
					startupFileContents = f"boot emmcflash0.kernel{slot[0]} 'brcm_cma=520M@248M brcm_cma={SystemInfo['canMode12']}@768M root=/dev/mmcblk0p{slot[0] * 2 + 1} rw rootwait {MODEL}_4.boxmode=12'\n"
				with open(join(self.tmp_dir, "STARTUP", "w")) as f:
					f.write(startupFileContents)
			self.cancel(2)

	def selectionChanged(self):
		self.currentSelected = self["list"].l.getCurrentSelection()
		if isinstance(self.currentSelected[0][1], tuple) and self.currentimageslot != self.currentSelected[0][1][0]:
			self["key_yellow"].setText(_("Delete Image"))
		elif self.deletedImagesExists:
			self["key_yellow"].setText(_("Restore deleted images"))
		else:
			self["key_yellow"].setText("")

	def KexecMount(self):
		hdd = []
		usblist = list(SystemInfo["HasUsbhdd"].keys())
		print("[MultibootSelection] usblist=", usblist)
		if not SystemInfo["VuUUIDSlot"]:
			with open("/proc/mounts", "r") as fd:
				xlines = fd.readlines()
				for hddkey in range(len(usblist)):
					for xline in xlines:
						print("[MultibootSelection] xline, usblist", xline, "   ", usblist[hddkey])
						if xline.find(usblist[hddkey]) != -1 and "ext4" in xline:
							index = xline.find(usblist[hddkey])
							print("[MultibootSelection] key, line ", usblist[hddkey], "   ", xline)
							hdd.append(xline[index:index + 4])
						else:
							continue
			print("[MultibootSelection] hdd available ", hdd)
			if not hdd:
				self.session.open(MessageBox, _("FlashImage: Add USB STARTUP slots - No EXT4 USB attached."), MessageBox.TYPE_INFO, timeout=10)
				self.cancel()
			else:
				usb = hdd[0][0:3]
				free = Harddisk(usb).Totalfree()
				print("[MultibootSelection] USB free space", free)
				if free < 1024:
					des = str(round((float(free)), 2)) + _("MB")
					print("[MultibootSelection][add USB STARTUP slot] limited free space", des)
					self.session.open(MessageBox, _("FlashImage: Add USB STARTUP slots - USB") + f" ({usb}) " + _("only has") + f" {des} " + _("free. At least 1024MB is required."), MessageBox.TYPE_INFO, timeout=30)
					self.cancel()
					return
				Console().ePopen("/sbin/blkid | grep " + "/dev/" + hdd[0], self.KexecMountRet)
		else:
			hiKey = sorted(SystemInfo["canMultiBoot"].keys(), reverse=True)[0]
			self.session.openWithCallback(self.addSTARTUPs, MessageBox, _("Add 4 more Vu+ Multiboot USB slots after slot %s ?") % hiKey, MessageBox.TYPE_YESNO, timeout=30)

	def addSTARTUPs(self, answer):
		hiKey = sorted(SystemInfo["canMultiBoot"].keys(), reverse=True)[0]
		hiUUIDkey = SystemInfo["VuUUIDSlot"][1]
		print("[MultibootSelection]1 answer, hiKey,  hiUUIDkey", answer, "   ", hiKey, "   ", hiUUIDkey)
		if answer is False:
			self.close()
		else:
			boxmodel = MODEL[2:]
			for usbslot in range(hiKey + 1, hiKey + 5):
				STARTUP_usbslot = f'kernel={boxmodel}/linuxrootfs{usbslot}/zImage root={SystemInfo["VuUUIDSlot"][0]} rootsubdir={boxmodel}/linuxrootfs{usbslot}'  # /STARTUP_<n>
				if boxmodel in ("duo4k"):
					STARTUP_usbslot += " rootwait=40"
				elif boxmodel in ("duo4kse"):
					STARTUP_usbslot += " rootwait=35"
				with open(f"/{self.tmp_dir}/STARTUP_{usbslot}", 'w') as f:
					f.write(STARTUP_usbslot)
				print(f"[MultibootSelection] STARTUP_{usbslot} --> {STARTUP_usbslot}, self.tmp_dir: {self.tmp_dir}")
			self.session.open(TryQuitMainloop, QUIT_RESTART)

	def KexecMountRet(self, result=None, retval=None, extra_args=None):
		self.device_uuid = "UUID=" + result.split("UUID=")[1].split(" ")[0].replace('"', '')
		usb = result.split(":")[0]
		boxmodel = MODEL[2:]
		for usbslot in range(4, 8):
			STARTUP_usbslot = f"kernel={boxmodel}/linuxrootfs{usbslot}/zImage root={self.device_uuid} rootsubdir={boxmodel}/linuxrootfs{usbslot}"  # /STARTUP_<n>
			if boxmodel in ("duo4k"):
				STARTUP_usbslot += " rootwait=40"
			elif boxmodel in ("duo4kse"):
				STARTUP_usbslot += " rootwait=35"
			print(f"[MultibootSelection] STARTUP_{usbslot} --> {STARTUP_usbslot}, self.tmp_dir: {self.tmp_dir}")
			with open(f"/{self.tmp_dir}/STARTUP_{usbslot}", 'w') as f:
				f.write(STARTUP_usbslot)

		SystemInfo["HasKexecUSB"] = True
		self.session.open(TryQuitMainloop, QUIT_RESTART)
