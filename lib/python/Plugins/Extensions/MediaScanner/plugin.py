from os import access, remove, F_OK, R_OK
from os.path import exists, split
from enigma import eTimer
from Tools.StbHardware import getFPWasTimerWakeup
from Plugins.Plugin import PluginDescriptor
from Components.Opkg import OpkgComponent
from Components.Scanner import scanDevice
from Screens.InfoBar import InfoBar
from Components.Harddisk import harddiskmanager
from Screens.MessageBox import MessageBox
from Screens.Toast import Toast

parentScreen = None
global_session = None
DAB_USB_PACKAGE = "enigma2-plugin-systemplugins-dabusb"
dabUSBInstaller = None


class DABUSBInstaller:
	def __init__(self):
		self.opkg = None
		self.running = False

	def requestInstall(self):
		from Components.RTLSDR import hasRTLSDRRuntime, hasRTLSDRUSBHardware
		if self.running or hasRTLSDRRuntime() or not hasRTLSDRUSBHardware() or global_session is None:
			return
		self.running = True
		self.opkg = OpkgComponent()
		self.opkg.addCallback(self.opkgCallback)
		if Toast.instance:
			Toast.instance.showToast(
				_("An RTL-SDR receiver was detected. The optional DAB+ USB runtime is being installed from the feed."),
				Toast.TYPE_INFO, timeout=6)
		self.opkg.startCmd(self.opkg.CMD_INSTALL, {"package": [DAB_USB_PACKAGE], "lineMode": True})

	def opkgCallback(self, event, parameter):
		if event == self.opkg.EVENT_ERROR:
			self.finish(False)
		elif event == self.opkg.EVENT_DONE:
			from Components.RTLSDR import hasRTLSDRRuntime
			self.finish(hasRTLSDRRuntime())

	def finish(self, success):
		if not self.running:
			return
		self.running = False
		if self.opkg:
			self.opkg.removeCallback(self.opkgCallback)
			self.opkg = None
		if global_session and Toast.instance:
			Toast.instance.showToast(
				_("DAB+ USB support was installed. You can now enable the receiver in Reception settings.") if success else _("DAB+ USB support could not be installed from the feed."),
				Toast.TYPE_INFO if success else Toast.TYPE_ERROR, timeout=10)


def dabUSBHotplug(device, action):
	if action == "dab-sdr-add" and dabUSBInstaller:
		dabUSBInstaller.requestInstall()


def execute(option):
	print("[MediaScanner] execute", option)
	if option is None:
		return

	(_, scanner, files, session) = option
	scanner.open(files, session)


def mountpoint_choosen(option):
	if option is None:
		return

	from Screens.ChoiceBox import ChoiceBox

	(description, mountpoint, session) = option
	res = scanDevice(mountpoint)

	list = [(r.description, r, res[r], session) for r in res]

	if not list:
		if access(mountpoint, F_OK | R_OK):
			session.open(MessageBox, _("%s connected successfully. No playable files on this medium found!") % description, MessageBox.TYPE_INFO, simple=True, timeout=5)
		else:
			session.open(MessageBox, _("Storage device not available or not initialized."), MessageBox.TYPE_ERROR, simple=True, timeout=10)
		return

	session.openWithCallback(execute, ChoiceBox,
		title=_("%s connected successfully.\nPlayable files found.") % description,
		list=list)


def scan(session):
	from Screens.ChoiceBox import ChoiceBox
	parts = [(r.tabbedDescription(), r.mountpoint, session) for r in harddiskmanager.getMountedPartitions(onlyhotplug=False) if access(r.mountpoint, F_OK | R_OK)]
	parts.append((_("Memory") + "\t/tmp", "/tmp", session))
	session.openWithCallback(mountpoint_choosen, ChoiceBox, title=_("Please select medium to be scanned"), list=parts)


def main(session, **kwargs):
	scan(session)


def menuEntry(*args):
	mountpoint_choosen(args)


def menuHook(menuid):
	if menuid != "mainmenu":
		return []
	from Tools.BoundFunction import boundFunction
	return [(("%s (files)") % r.description, boundFunction(menuEntry, r.description, r.mountpoint), "hotplug_%s" % r.mountpoint, None) for r in harddiskmanager.getMountedPartitions(onlyhotplug=True)]


global_session = None


def partitionListChanged(action, device):
	if InfoBar.instance:
		if InfoBar.instance.execing:
			if action == 'add' and device.is_hotplug:
				if getFPWasTimerWakeup():  # norhap Avoid being unable to go into standby mode due to having an open instance of ChoiceBox.
					with open("/tmp/.listtoscanchoicebox", "w") as f:
						f.write("")
				print("[MediaScanner] mountpoint", device.mountpoint)
				print("[MediaScanner] description", device.description)
				print("[MediaScanner] force_mounted", device.force_mounted)
				print("[MediaScanner] scanning", device.description, device.mountpoint)
				mountpoint_choosen((device.description, device.mountpoint, global_session))
		else:
			print("[MediaScanner] main infobar is not execing... so we ignore hotplug event!")
	else:
		print("[MediaScanner] hotplug event.. but no infobar")


def sessionstart(reason, session):
	global global_session, dabUSBInstaller
	global_session = session
	if dabUSBInstaller is None:
		dabUSBInstaller = DABUSBInstaller()
	# A receiver can already be present before Enigma2 opens the hotplug socket.
	bootProbe = eTimer()
	bootProbe.callback.append(dabUSBInstaller.requestInstall)
	bootProbe.start(2000, True)
	dabUSBInstaller.bootProbe = bootProbe


def autostart(reason, **kwargs):
	global global_session, dabUSBInstaller
	from Plugins.SystemPlugins.Hotplug.plugin import hotplugNotifier
	if reason == 0:
		if exists("/tmp/.listtoscanchoicebox"):
			remove("/tmp/.listtoscanchoicebox")
		harddiskmanager.on_partition_list_change.append(partitionListChanged)
		if dabUSBHotplug not in hotplugNotifier:
			hotplugNotifier.append(dabUSBHotplug)
	elif reason == 1:
		harddiskmanager.on_partition_list_change.remove(partitionListChanged)
		if dabUSBHotplug in hotplugNotifier:
			hotplugNotifier.remove(dabUSBHotplug)
		global_session = None
		dabUSBInstaller = None


def movielist_open(list, session, **kwargs):
	from Components.config import config
	if not list:
		# sanity
		return
	from enigma import eServiceReference
	from Screens.InfoBar import InfoBar
	f = list[0]
	if f.mimetype == "video/MP2T":
		stype = 1
	else:
		stype = 4097
	if InfoBar.instance:
		path = split(f.path)[0]
		if not path.endswith('/'):
			path += '/'
		config.movielist.last_videodir.value = path
		InfoBar.instance.showMovies(eServiceReference(stype, 0, f.path))


def filescan_open(list, session, **kwargs):
	filelist = [x.path for x in list]
	from Plugins.SystemPlugins.Hotplug import OpkgInstaller
	session.open(OpkgInstaller, filelist)  # list


def filescan(**kwargs):
	from Components.Scanner import Scanner, ScanPath
	return [
		Scanner(mimetypes=["video/mpeg", "video/MP2T", "video/x-msvideo", "video/mkv", "video/avi"],
			paths_to_scan=[
				ScanPath(path="", with_subdirs=False),
				ScanPath(path="movie", with_subdirs=False),],
			name="Movie",
			description=_("View Movies..."),
			openfnc=movielist_open,),
		Scanner(mimetypes=["video/x-vcd"],
			paths_to_scan=[
				ScanPath(path="mpegav", with_subdirs=False),
				ScanPath(path="MPEGAV", with_subdirs=False),],
			name="Video CD",
			description=_("View Video CD..."),
			openfnc=movielist_open,),
		Scanner(mimetypes=["audio/mpeg", "audio/x-wav", "application/ogg", "audio/x-flac"],
			paths_to_scan=[
				ScanPath(path="", with_subdirs=False),],
			name="Music",
			description=_("Play Music..."),
			openfnc=movielist_open,),
		Scanner(mimetypes=["audio/x-cda"],
			paths_to_scan=[
				ScanPath(path="", with_subdirs=False),],
			name="Audio-CD",
			description=_("Play Audio-CD..."),
			openfnc=movielist_open,),]


def Plugins(**kwargs):
	return [
		PluginDescriptor(name=_("Media scanner"), description=_("Scan files..."), where=PluginDescriptor.WHERE_PLUGINMENU, icon="MediaScanner.png", needsRestart=True, fnc=main),
		# PluginDescriptor(where = PluginDescriptor.WHERE_MENU, fnc=menuHook),
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, needsRestart=True, fnc=sessionstart),
		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, needsRestart=True, fnc=autostart)]
