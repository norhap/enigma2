from os import access, remove, F_OK, R_OK
from os.path import exists, split
from Tools.StbHardware import getFPWasTimerWakeup
from Plugins.Plugin import PluginDescriptor
from Components.Scanner import scanDevice
from Components.config import config
from Screens.InfoBar import InfoBar
from Components.Harddisk import harddiskmanager
from Screens.MessageBox import MessageBox
from Screens.Toast import Toast

global_session = None


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
	text = _("%s connected successfully.\nPlayable files found.") % description if access(mountpoint, F_OK | R_OK) else _("Storage device not available or not initialized.")
	icon = "\uF003"
	toast_type = Toast.TYPE_INFO if access(mountpoint, F_OK | R_OK) else Toast.TYPE_ERROR
	text_list = _("%s connected successfully.\nPlayable files found.") % description
	type_messagebox = MessageBox.TYPE_ERROR if access(mountpoint, F_OK | R_OK) else MessageBox.TYPE_INFO
	if not list:
		if not config.usage.show_fading_message.value:
			session.open(MessageBox, text % description, type_messagebox, simple=True, timeout=10)
		else:
			Toast.instance.showToast(text=text, toasttype=toast_type, timeout=10, customIcon=icon)
		return
	if not config.usage.show_fading_message.value:
		session.openWithCallback(execute, ChoiceBox,
			title=text_list % description,
			list=list)
	else:
		Toast.instance.showToast(text=text_list, toasttype=toast_type, timeout=10, customIcon=icon)


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
	global global_session
	global_session = session


def autostart(reason, **kwargs):
	global global_session
	if reason == 0:
		if exists("/tmp/.listtoscanchoicebox"):
			remove("/tmp/.listtoscanchoicebox")
		harddiskmanager.on_partition_list_change.append(partitionListChanged)
	elif reason == 1:
		harddiskmanager.on_partition_list_change.remove(partitionListChanged)
		global_session = None


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
