# -*- coding: utf-8 -*-
from enigma import checkInternetAccess

from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Converter.Poll import Poll

sucess_internet = False
INTERNET_TIMEOUT = 2
FEED_SERVER = "google.com"


class RouteInfo(Poll, Converter):
	Info = 0
	Lan = 1
	Wifi = 2
	Modem = 3
	Internet = 4
	Inet = 5

	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)
		self.type = type
		self.poll_interval = 2000
		self.poll_enabled = True
		if type == "Info":
			self.type = self.Info
		elif type == "Lan":
			self.type = self.Lan
		elif type == "Wifi":
			self.type = self.Wifi
		elif type == "Modem":
			self.type = self.Modem
		elif type == "Inet":
			self.type = self.Inet
		elif type == "Internet":
			self.type = self.Internet

	@cached
	def getBoolean(self):
		global sucess_internet
		match checkInternetAccess(FEED_SERVER, INTERNET_TIMEOUT):
			case 0:
				info = True
				sucess_internet = True
			case _:
				info = False
				sucess_internet = False
		print("[RouteInfo] Read /proc/net/route")
		for line in open("/proc/net/route"):
			if self.type == self.Lan and line.split()[0] == "eth0" and line.split()[3] == "0003":
				info = True
			elif self.type == self.Wifi and (line.split()[0] == "wlan0" or line.split()[0] == "ra0") and line.split()[3] == "0003":
				info = True
			elif self.type == self.Modem and line.split()[0] == "ppp0" and line.split()[3] == "0003":
				info = True
		return info

	boolean = property(getBoolean)

	@cached
	def getText(self):
		global sucess_internet
		info = ""
		print("[RouteInfo] Read /proc/net/route")
		for line in open("/proc/net/route"):
			if self.type == self.Inet:
				if sucess_internet:
					from Components.About import about  # noqa: E402
					try:
						if about.getIfConfig('eth0')['addr']:
							info = f"IP: {about.getIfConfig('eth0')['addr']}"
					except Exception:
						try:
							if about.getIfConfig('wlan0')['addr']:
								info = f"IP: {about.getIfConfig('wlan0')['addr']}"
						except Exception:
							try:
								if about.getIfConfig('wlan3')['addr']:
									info = f"IP: {about.getIfConfig('wlan3')['addr']}"
							except Exception:
								sucess_internet = False
								return _("Your internet connection is not working.")
				else:
					sucess_internet = False
					return _("Your internet connection is not working.")
			elif self.type == self.Internet and sucess_internet:
				from Tools.Geolocation import geolocation  # noqa: E402
				geolocationData = geolocation.getGeolocationData(fields="isp,org,mobile,proxy,query", useCache=True)
				ipv4address = geolocationData.get("query", None)
				info = f"{_("IPv4 public address:")} {ipv4address}"
			elif self.type == self.Info and line.split()[0] == "eth0" and line.split()[3] == "0003":
				info = "lan"
			elif self.type == self.Info and (line.split()[0] == "wlan0" or line.split()[0] == "ra0") and line.split()[3] == "0003":
				info = "wifi"
			elif self.type == self.Info and line.split()[0] == "ppp0" and line.split()[3] == "0003":
				info = "3g"
		return info

	text = property(getText)

	def changed(self, what):
		if what[0] == self.CHANGED_POLL:
			Converter.changed(self, what)
