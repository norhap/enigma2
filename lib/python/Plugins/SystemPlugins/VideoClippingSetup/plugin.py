# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigSlider, getConfigListEntry

config.plugins.VideoClippingSetup = ConfigSubsection()
config.plugins.VideoClippingSetup.clip_left = ConfigInteger(default=0)
config.plugins.VideoClippingSetup.clip_width = ConfigInteger(default=720)
config.plugins.VideoClippingSetup.clip_top = ConfigInteger(default=0)
config.plugins.VideoClippingSetup.clip_height = ConfigInteger(default=576)


class VideoClippingCoordinates(ConfigListScreen, Screen):
	skin = """
	<screen position="0,0" size="e,e" title="Video clipping setup" backgroundColor="transparent">
		<widget name="config" position="c-175,c-75" size="350,150" foregroundColor="black" backgroundColor="transparent" />
		<ePixmap pixmap="buttons/green.png" position="c-145,e-100" zPosition="0" size="140,40" alphaTest="on" />
		<ePixmap pixmap="buttons/red.png" position="c+5,e-100" zPosition="0" size="140,40" alphaTest="on" />
		<widget name="ok" position="c-145,e-100" size="140,40" verticalAlignment="center" horizontalAlignment="center" zPosition="1" font="Regular;20" transparent="1" backgroundColor="green" />
		<widget name="cancel" position="c+5,e-100" size="140,40" verticalAlignment="center" horizontalAlignment="center" zPosition="1" font="Regular;20" transparent="1" backgroundColor="red" />
	</screen>"""

	def __init__(self, session):
		self.skin = VideoClippingCoordinates.skin
		Screen.__init__(self, session)

		self.setTitle(_("Video clipping setup"))

		from Components.ActionMap import ActionMap
		from Components.Button import Button

		self["ok"] = Button(_("OK"))
		self["cancel"] = Button(_("Cancel"))

		self["actions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
		{
			"ok": self.keyGo,
			"save": self.keyGo,
			"cancel": self.keyCancel,
			"green": self.keyGo,
			"red": self.keyCancel,
			"menu": self.closeRecursive,
			"left": self.keyLeft,
			"right": self.keyRight
		}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list, session=self.session)

		left = config.plugins.VideoClippingSetup.clip_left.value
		width = config.plugins.VideoClippingSetup.clip_width.value
		top = config.plugins.VideoClippingSetup.clip_top.value
		height = config.plugins.VideoClippingSetup.clip_height.value

		self.clip_step = ConfigSlider(default=1, increment=1, limits=(1, 20))
		self.clip_left = ConfigSlider(default=left, increment=self.clip_step.value, limits=(0, 720))
		self.clip_width = ConfigSlider(default=width, increment=self.clip_step.value, limits=(0, 720))
		self.clip_top = ConfigSlider(default=top, increment=self.clip_step.value, limits=(0, 576))
		self.clip_height = ConfigSlider(default=height, increment=self.clip_step.value, limits=(0, 576))
		self.list.append(getConfigListEntry(_("stepsize"), self.clip_step))
		self.list.append(getConfigListEntry(_("left"), self.clip_left))
		self.list.append(getConfigListEntry(_("width"), self.clip_width))
		self.list.append(getConfigListEntry(_("top"), self.clip_top))
		self.list.append(getConfigListEntry(_("height"), self.clip_height))
		self["config"].list = self.list

	def adjustStep(self):
		self.clip_left.increment = self.clip_step.value
		self.clip_width.increment = self.clip_step.value
		self.clip_top.increment = self.clip_step.value
		self.clip_height.increment = self.clip_step.value

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.adjustStep()
		self.setPreviewPosition()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.adjustStep()
		self.setPreviewPosition()

	def setPreviewPosition(self):
		setPosition(int(self.clip_left.value), int(self.clip_width.value), int(self.clip_top.value), int(self.clip_height.value))

	def keyGo(self):
		config.plugins.VideoClippingSetup.clip_left.value = self.clip_left.value
		config.plugins.VideoClippingSetup.clip_width.value = self.clip_width.value
		config.plugins.VideoClippingSetup.clip_top.value = self.clip_top.value
		config.plugins.VideoClippingSetup.clip_height.value = self.clip_height.value
		config.plugins.VideoClippingSetup.save()
		self.close()

	def keyCancel(self):
		setConfiguredPosition()
		self.close()


def setPosition(clip_left, clip_width, clip_top, clip_height):
	if clip_left + clip_width > 720:
		clip_width = 720 - clip_left
	if clip_top + clip_height > 576:
		clip_height = 576 - clip_top
	try:
		print("[VideoClippingSetup] Write to /proc/stb/vmpeg/0/clip_left")
		open("/proc/stb/vmpeg/0/clip_left", "w").write('%X' % clip_left)
		print("[VideoClippingSetup] Write to /proc/stb/vmpeg/0/clip_width")
		open("/proc/stb/vmpeg/0/clip_width", "w").write('%X' % clip_width)
		print("[VideoClippingSetup] Write to /proc/stb/vmpeg/0/clip_top")
		open("/proc/stb/vmpeg/0/clip_top", "w").write('%X' % clip_top)
		print("[VideoClippingSetup] Write to /proc/stb/vmpeg/0/clip_height")
		open("/proc/stb/vmpeg/0/clip_height", "w").write('%X' % clip_height)
	except:
		print("[VideoClippingSetup] Write to /proc/stb/vmpeg/0/clip_left failed.")
		print("[VideoClippingSetup] Write to /proc/stb/vmpeg/0/clip_width failed.")
		print("[VideoClippingSetup] Write to /proc/stb/vmpeg/0/clip_top failed.")
		print("[VideoClippingSetup] Write to /proc/stb/vmpeg/0/clip_height failed.")
		return


def setConfiguredPosition():
	setPosition(int(config.plugins.VideoClippingSetup.clip_left.value), int(config.plugins.VideoClippingSetup.clip_width.value), int(config.plugins.VideoClippingSetup.clip_top.value), int(config.plugins.VideoClippingSetup.clip_height.value))


def main(session, **kwargs):
	session.open(VideoClippingCoordinates)


def startup(reason, **kwargs):
	setConfiguredPosition()


def Plugins(**kwargs):
	from os import path
	if path.exists("/proc/stb/vmpeg/0/clip_left"):
		from Plugins.Plugin import PluginDescriptor
		return [PluginDescriptor(name=_("Video clipping setup"), description=_("clip overscan / letterbox borders"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
					PluginDescriptor(name=_("Video clipping setup"), description="", where=PluginDescriptor.WHERE_SESSIONSTART, fnc=startup)]
	return []
