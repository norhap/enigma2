from Screens.Screen import Screen
from Screens.Setup import Setup
from Screens.HelpMenu import HelpableScreen
from Components.FileList import FileList
from Components.Sources.StaticText import StaticText
from Components.config import config, ConfigYesNo, ConfigDirectory
from Components.ActionMap import ActionMap

config.mediaplayer.repeat = ConfigYesNo(default=False)
config.mediaplayer.savePlaylistOnExit = ConfigYesNo(default=True)
config.mediaplayer.saveDirOnExit = ConfigYesNo(default=False)
config.mediaplayer.defaultDir = ConfigDirectory()
config.mediaplayer.sortPlaylists = ConfigYesNo(default=False)
config.mediaplayer.alwaysHideInfoBar = ConfigYesNo(default=False)
config.mediaplayer.onMainMenu = ConfigYesNo(default=True)


class DirectoryBrowser(Screen, HelpableScreen):

	def __init__(self, session, currDir):
		Screen.__init__(self, session)
		# for the skin: first try MediaPlayerDirectoryBrowser, then FileBrowser, this allows individual skinning
		self.skinName = ["MediaPlayerDirectoryBrowser", "FileBrowser"]
		self.setTitle(_("Directory browser"))

		HelpableScreen.__init__(self)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Use"))

		self.filelist = FileList(currDir, matchingPattern="")
		self["filelist"] = self.filelist

		self["FilelistActions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"green": self.use,
				"red": self.exit,
				"ok": self.ok,
				"cancel": self.exit
		})

	def ok(self):
		if self.filelist.canDescent():
			self.filelist.descent()

	def use(self):
		if self["filelist"].getCurrentDirectory() is not None:
			if self.filelist.canDescent() and self["filelist"].getFilename() and len(self["filelist"].getFilename()) > len(self["filelist"].getCurrentDirectory()):
				self.filelist.descent()
				self.close(self["filelist"].getCurrentDirectory())
		else:
			self.close(self["filelist"].getFilename())

	def exit(self):
		self.close(False)


class MediaPlayerSettings(Setup):
	def __init__(self, session, parent):
		Setup.__init__(self, session, setup="MediaPlayer", plugin="Extensions/MediaPlayer")
		self.parent = parent

	def keySelect(self):
		if self["config"].getCurrent()[1] == config.mediaplayer.defaultDir:
			self.session.openWithCallback(self.DirectoryBrowserClosed, DirectoryBrowser, self.parent.filelist.getCurrentDirectory())
			return
		Setup.keySelect(self)

	def keySave(self):
		Setup.keySave(self)

	def DirectoryBrowserClosed(self, path):
		print("[MediaPlayer] PathBrowserClosed:" + str(path))
		if path:
			config.mediaplayer.defaultDir.setValue(path)
