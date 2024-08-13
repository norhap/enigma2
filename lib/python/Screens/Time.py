from enigma import eConsoleAppContainer
from Components.ActionMap import ActionMap, HelpableActionMap
from os.path import isfile  # islink
from Components.config import config, getConfigListEntry, ConfigSelection
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Timezones import TIMEZONE_DATA
from Components.Sources.StaticText import StaticText
from Screens.Setup import Setup
from Screens.Screen import Screen
from Screens.HelpMenu import ShowRemoteControl
from Tools.Directories import fileContains
from Tools.Geolocation import geolocation
from requests import get


class Time(Setup):
	def __init__(self, session):
		Setup.__init__(self, session=session, setup="Time")
		self["key_yellow"] = StaticText("")
		self["geolocationActions"] = HelpableActionMap(self, ["ColorActions"], {
			"yellow": (self.useGeolocation, _("Use geolocation to set the current time zone location")),
			"green": self.keySave
		}, prio=0, description=_("Time Setup Actions"))
		if not isfile("/etc/init.d/crond") and config.ntp.timesync.value != "dvb":
			eConsoleAppContainer().execute("opkg update && opkg install cronie")
		self.selectionChanged()

	def setNTP(self):
		# cmdntp = "root /usr/bin/ntpdate-sync silent"
		# linkup = "ln -s /usr/bin/ntpdate-sync /etc/network/if-up.d/ntpdate-sync"
		# if config.ntp.timesync.value != "dvb":
		# if not fileContains("/etc/crontab", "ntpdate"):
		# eConsoleAppContainer().execute("sed -i '/ntpdate-sync/d' /etc/crontab;sed -i '$a@reboot %s'" % cmdntp + " " "/etc/crontab;sed -i '$a 30 *   *   *   * %s'" % cmdntp + " " "/etc/crontab")
		# if not islink("/etc/network/if-up.d/ntpdate-sync"):
		# eConsoleAppContainer().execute(linkup)
		# else:
		# if islink("/etc/network/if-up.d/ntpdate-sync"):
		# eConsoleAppContainer().execute("sed -i '/ntpdate-sync/d' /etc/crontab")
		if config.ntp.timesync.value != "dvb":
			eConsoleAppContainer().execute("sed -i '/sntp/d' /etc/crontab;sed -i '$a@reboot root sntp -S %s'" % config.ntp.server.value + " " "/etc/crontab;sed -i '$a 30 *   *   *   * root sntp -S %s'" % config.ntp.server.value + " " "/etc/crontab;sntp -S %s" % config.ntp.server.value)
		else:
			eConsoleAppContainer().execute("sed -i '/sntp/d' /etc/crontab")

	def keySave(self):
		if isfile("/etc/init.d/crond"):
			Setup.keySave(self)
			self.setNTP()
		else:
			if config.ntp.timesync.value != "dvb":
				if isfile("/etc/init.d/crond"):
					Setup.keySave(self)
					self.setNTP()
				else:
					self.setFootnote(_("Cronie is being installed. Time settings are being established. Save your settings with GREEN button after a few seconds."))
			else:
				Setup.keySave(self)

	def selectionChanged(self):
		if Setup.getCurrentItem(self) in (config.timezone.area, config.timezone.val):
			self["key_yellow"].setText(_("Set local time"))
			self["geolocationActions"].setEnabled(True)
		else:
			self["key_yellow"].setText("")
			self["geolocationActions"].setEnabled(False)
		Setup.selectionChanged(self)

	def useGeolocation(self):
		geolocationData = geolocation.getGeolocationData(fields="status,message,timezone,proxy")
		tz = geolocationData.get("timezone", None)
		areaItem = None
		valItem = None
		for item in self["config"].list:
			if item[1] is config.timezone.area:
				areaItem = item
			if item[1] is config.timezone.val:
				valItem = item
		if tz:
			area, zone = tz.split("/", 1)
			config.timezone.area.value = area
			if areaItem is not None:
				areaItem[1].changed()
			self["config"].invalidate(areaItem)
			config.timezone.val.value = zone
		else:
			try:
				# ip = get("https://freeipapi.com/api/json/", verify=False)  # FREE ALTERNATIVE https://freeipapi.com/api/json/
				# from json import loads
				# dictionary = loads(ip.content)
				# publicip = dictionary.get("ipAddress", "")
				# timezone = get(f"http://worldtimeapi.org/api/ip:{publicip}", verify=False)
				publicip = get("http://api.ipify.org?format=json/", verify=False)  # FREE ALTERNATIVE https://reallyfreegeoip.org/json/
				timezone = get(f"http://worldtimeapi.org/api/ip:{publicip.content}", verify=False)
				if timezone.content:
					with open(TIMEZONE_DATA + "timezone", "wb") as tz:
						tz.write(timezone.content)
					with open(TIMEZONE_DATA + "timezone", "r") as tzread:
						result = tzread.readlines()
						for timezone in result:
							if "timezone" in timezone:
								config.timezone.area.value = timezone.split('"timezone":"')[1].split('/')[0]
								break
					if areaItem is not None:
						areaItem[1].changed()
					self["config"].invalidate(areaItem)
					with open(TIMEZONE_DATA + "timezone", "r") as tzread:
						result = tzread.readlines()
						for timezone in result:
							if "timezone" in timezone:
								config.timezone.val.value = timezone.split('/')[1].split('",')[0]
								break
			except Exception:
				self.setFootnote(_("Geolocation is not available. No Internet."))
				return
		if valItem is not None:
			valItem[1].changed()
		self["config"].invalidate(valItem)
		try:
			self.setFootnote(_("Geolocation has been used to set the time zone."))
		except KeyError:
			pass
		self.setNTP()


class TimeWizard(ConfigListScreen, Screen, ShowRemoteControl):
	skin = """
	<screen name="TimeWizard" position="center,60" size="980,635" resolution="1280,720">
		<widget name="text" position="10,10" size="e-20,25" font="Regular;16" transparent="1" verticalAlignment="center" />
		<widget name="config" position="10,40" size="e-20,260" enableWrapAround="1" entryFont="Regular;18" valueFont="Regular;18" itemHeight="35" scrollbarMode="showOnDemand" />
		<widget source="key_red" render="Label" objectTypes="key_red,StaticText" position="180,e-50" size="180,40" backgroundColor="key_red" conditional="key_red" font="Regular;18" foregroundColor="key_text" horizontalAlignment="center" verticalAlignment="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="key_yellow" render="Label" objectTypes="key_yellow,StaticText" position="390,e-50" size="180,40" backgroundColor="key_yellow" conditional="key_yellow" font="Regular;18" foregroundColor="key_text" horizontalAlignment="center" verticalAlignment="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="global.CurrentTime" font="Regular;20" position="680,e-40" render="Label" size="140,30" transparent="1">
			<convert type="ClockToText">Mixed</convert>
		</widget>
		<widget name="label" conditional="label" position="0,0" size="0,0" />
		<widget name="HelpWindow" position="0,0" size="0,0" alphaTest="blend" conditional="HelpWindow" transparent="1" zPosition="+1" />
		<widget name="rc" conditional="rc" alphaTest="blend" position="10,300" size="100,360" />
		<widget name="wizard" conditional="wizard" pixmap="picon_default.png" position="740,400" size="220,132" alphaTest="blend" />
		<widget name="indicatorU0" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU1" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU2" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU3" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU4" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU5" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU6" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU7" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU8" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU9" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU10" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU11" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU12" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU13" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU14" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorU15" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL0" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL1" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL2" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL3" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL4" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL5" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL6" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL7" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL8" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL9" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL10" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL11" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL12" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL13" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL14" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
		<widget name="indicatorL15" pixmap="rc_circle.png" position="0,0" size="23,23" alphaTest="blend" offset="11,11" zPosition="11" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		ShowRemoteControl.__init__(self)
		self.skinName = ["TimeWizard"]
		self.setTitle(_("Time Wizard"))
		self.list = []
		ConfigListScreen.__init__(self, self.list)
		self["text"] = Label()
		self["text"].setText(_("Press YELLOW button if your time zone is not set or press \"OK\" to continue wizard."))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_yellow"] = StaticText(_("Set local time"))
		self["wizard"] = Pixmap()
		self["lab1"] = StaticText(_("norhap"))
		self["lab2"] = StaticText(_("Report problems to:"))
		self["lab3"] = StaticText(_("telegram @norhap"))
		self["lab4"] = StaticText(_("Sources are available at:"))
		self["lab5"] = StaticText(_("https://github.com/norhap"))
		self["actions"] = ActionMap(["WizardActions", "ColorActions"], {
			"yellow": self.keyGeolocation,
			"ok": self.keySave,
			"red": self.keySave,
			"back": self.keySave,
			"left": self.keyLeft,
			"right": self.keyRight,
			"up": self.moveUp,
			"down": self.moveDown
		}, -2)
		self.onLayoutFinish.append(self.selectKeys)
		self.getTimeList()

	def selectKeys(self):
		self.geolocationWizard()
		self.clearSelectedKeys()
		self.selectKey("UP")
		self.selectKey("DOWN")
		self.selectKey("LEFT")
		self.selectKey("RIGHT")
		self.selectKey("RED")
		self.selectKey("YELLOW")
		self.selectKey("OK")

	def getTimeList(self):
		config.ntp.timesync = ConfigSelection(default="ntp", choices=[
			("auto", _("Auto")),
			("dvb", _("Transponder time")),
			("ntp", _("Internet time (SNTP)"))
		])
		self.list = []
		self.list.append(getConfigListEntry(_("Time zone area"), config.timezone.area))
		self.list.append(getConfigListEntry(_("Time zone"), config.timezone.val))
		self.list.append(getConfigListEntry(_("Date style"), config.usage.date.dayfull))
		self.list.append(getConfigListEntry(_("Time style"), config.usage.time.long))
		self.list.append(getConfigListEntry(_("Time synchronization method"), config.ntp.timesync))
		self.list.append(getConfigListEntry(_("NTP Hostname"), config.ntp.server))
		self["config"].list = self.list
		self["config"].setList(self.list)

	def geolocationWizard(self):
		geolocationData = geolocation.getGeolocationData(fields="status,message,timezone,proxy")
		tz = geolocationData.get("timezone", None)
		areaItem = None
		valItem = None
		for item in self["config"].list:
			if item[1] is config.timezone.area:
				areaItem = item
			if item[1] is config.timezone.val:
				valItem = item
		if not fileContains(TIMEZONE_DATA + "timezone", "timezone"):
			if tz:
				area, zone = tz.split("/", 1)
				config.timezone.area.value = area
				if areaItem is not None:
					areaItem[1].changed()
				self["config"].invalidate(areaItem)
				config.timezone.val.value = zone
			else:
				self["text"].setText(_("Geolocation is not available. No Internet."))
				return
		else:
			with open(TIMEZONE_DATA + "timezone", "r") as tzread:
				result = tzread.readlines()
				for timezone in result:
					if "timezone" in timezone:
						config.timezone.area.value = timezone.split('"timezone":"')[1].split('/')[0]
						break
			if areaItem is not None:
				areaItem[1].changed()
			self["config"].invalidate(areaItem)
			with open(TIMEZONE_DATA + "timezone", "r") as tzread:
				result = tzread.readlines()
				for timezone in result:
					if "timezone" in timezone:
						config.timezone.val.value = timezone.split('/')[1].split('",')[0]
						break
		if valItem is not None:
			valItem[1].changed()
		self["config"].invalidate(valItem)
		self["text"].setText(_("Your zone and local time has been set successfully.\n\nPress \"OK\" to continue wizard."))
		Time.setNTP(self)

	def keySave(self):
		ConfigListScreen.keySave(self)
		Time.setNTP(self)
		self.close(True)

	def keyGeolocation(self):
		self.geolocationWizard()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	def moveUp(self):
		self["config"].moveUp()

	def moveDown(self):
		self["config"].moveDown()
