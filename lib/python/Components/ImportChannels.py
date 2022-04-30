from __future__ import print_function
import threading
import os
import re
import shutil
import tempfile
from json import loads
from enigma import eDVBDB, eEPGCache
from Screens.MessageBox import MessageBox
from Components.config import config, ConfigText
from Tools.Notifications import AddNotificationWithID
from time import sleep
from sys import version_info
from six.moves.urllib.error import URLError
from six.moves.urllib.parse import quote
import xml.etree.ElementTree as et
if version_info.major >= 3:
	from six.moves.urllib.request import Request, urlopen
	from base64 import encodebytes
	encodecommand = encodebytes
else: # Python 2
	from urllib2 import Request, urlopen
	from base64 import encodestring
	encodecommand = encodestring

supportfiles = ('lamedb', 'blacklist', 'whitelist', 'alternatives.')

channelslistpath = "/etc/enigma2"


class ImportChannels():

	def __init__(self):
		if config.usage.remote_fallback_enabled.value and config.usage.remote_fallback_import.value and config.usage.remote_fallback.value and not "ChannelsImport" in [x.name for x in threading.enumerate()]:
			self.header = None
			if config.usage.remote_fallback_enabled.value and config.usage.remote_fallback_import.value and config.usage.remote_fallback_import_url.value != "same" and config.usage.remote_fallback_import_url.value:
				self.url = config.usage.remote_fallback_import_url.value.rsplit(":", 1)[0]
			else:
				self.url = config.usage.remote_fallback.value.rsplit(":", 1)[0]
			if config.usage.remote_fallback_openwebif_customize.value:
				self.url = "%s:%s" % (self.url, config.usage.remote_fallback_openwebif_port.value)
				if config.usage.remote_fallback_openwebif_userid.value and config.usage.remote_fallback_openwebif_password.value:
					self.header = "Basic %s" % encodecommand(("%s:%s" % (config.usage.remote_fallback_openwebif_userid.value, config.usage.remote_fallback_openwebif_password.value)).encode("UTF-8")).strip()
			self.remote_fallback_import = config.usage.remote_fallback_import.value
			self.thread = threading.Thread(target=self.threaded_function, name="ChannelsImport")
			self.thread.start()

	def getUrl(self, url, timeout=5):
		request = Request(url)
		if self.header:
			request.add_header("Authorization", self.header)
		try:
			result = urlopen(request, timeout=timeout)
		except URLError as err:
			print("[ImportChannels] %s" % err)
			if "[Errno -3]" in str(err.reason):
				try:
					print("[ImportChannels] Network is not up yet, delay 5 seconds")
					# network not up yet
					sleep(5)
					return self.getUrl(url, timeout)
				except URLError as err:
					print("[ImportChannels] %s" % err)
				return result

	def getTerrestrialUrl(self):
		url = config.usage.remote_fallback_dvb_t.value
		return url[:url.rfind(":")] if url else self.url

	def getFallbackSettings(self):
		if not URLError:  # currently disabled, we get syntax errors when we try to load settings from the server.
			return (str(self.getUrl("%s/web/settings" % self.getTerrestrialUrl())))

	def getFallbackSettingsValue(self, settings, e2settingname):
		if settings:
			root = et.fromstring(settings)
			for e2setting in root:
				if e2settingname in e2setting[0].text:
					return e2setting[1].text
			return ""

	def getTerrestrialRegion(self, settings):
		if settings:
			description = ""
			descr = self.getFallbackSettingsValue(settings, ".terrestrial")
			if "Europe" in descr:
				description = "fallback DVB-T/T2 Europe"
			if "Australia" in descr:
				description = "fallback DVB-T/T2 Australia"
			config.usage.remote_fallback_dvbt_region.value = description

	def threaded_function(self):
		settings = self.getFallbackSettings()
		self.getTerrestrialRegion(settings)
		self.tmp_dir = tempfile.mkdtemp(prefix="ImportChannels_")

		if "epg" in self.remote_fallback_import:
			print("[ImportChannels] Starting to load epg.dat files and channels from server box")
			try:
				self.getUrl("%s/web/saveepg" % self.url, timeout=5)
			except Exception as err:
				print("[ImportChannels] %s" % err)
				return self.ImportChannelsDone(False, _("Fallback tuner not available")) if config.usage.remote_fallback_nok.value else None
			print("[ImportChannels] Get EPG Location")
			try:
				epgdatfile = self.getFallbackSettingsValue(settings, "config.misc.epgcache_filename") or "/media/hdd/epg.dat" or "/media/usb/epg.dat" or "/etc/enigma2/epg.dat"
				files = [file for file in loads(urlopen("%s/file?dir=%s" % (self.url, os.path.dirname(epgdatfile)), timeout=5).read())["files"] if os.path.basename(file).startswith("epg.dat")]
				epg_location = files[0] if files else None
			except Exception as err:
				print("[ImportChannels] %s" % err)
				return self.ImportChannelsDone(False, _("Error retrieving EPG from server, wearing EPG and channels from this receiver")) if config.usage.remote_fallback_nok.value else None
			if epg_location:
				print("[ImportChannels] Copy EPG file...")
				try:
					try:
						os.mkdir("/tmp/epgdat")
					except:
						print("[ImportChannels] epgdat folder exists in tmp")
					epgdattmp = "/tmp/epgdat"
					epgdatserver = "/tmp/epgdat/epg.dat"
					open("%s/%s" % (epgdattmp, os.path.basename(epg_location)), "wb").write(urlopen("%s/file?file=%s" % (self.url, epg_location), timeout=5).read())
					shutil.move("%s" % epgdatserver, "%s" % (config.misc.epgcache_filename.value))
					eEPGCache.getInstance().load()
					shutil.rmtree(epgdattmp)
					self.ImportChannelsDone(False, _("EPG imported successfully from %s") % self.url) if config.usage.remote_fallback_ok.value else None
				except Exception as err:
					print("[ImportChannels] cannot save EPG %s" % err)
					return self.ImportChannelsDone(False, _("Error retrieving EPG from server, wearing EPG and channels from this receiver")) if config.usage.remote_fallback_nok.value else None
			else:
				self.ImportChannelsDone(False, _("No epg.dat file found server")) if config.usage.remote_fallback_nok.value else None
		if "channels" in self.remote_fallback_import and not config.clientmode.enabled.value:
			channelslist = ('lamedb', 'bouquets.', 'userbouquet.', 'blacklist', 'whitelist', 'alternatives.')
			try:
				try:
					os.mkdir("/tmp/channelslist")
				except:
					print("[ImportChannels] channelslist folder exists in tmp")
				channelslistserver = "/tmp/channelslist"
				files = [file for file in loads(urlopen("%s/file?dir=%s" % (self.url, channelslistpath), timeout=5).read())["files"] if os.path.basename(file).startswith(channelslist)]
				count = 0
				for file in files:
					count += 1
					file = file if version_info.major >= 3 else file.encode("UTF-8")
					print("[ImportChannels] Downloading %s" % file)
					try:
						open("%s/%s" % (channelslistserver, os.path.basename(file)), "wb").write(urlopen("%s/file?file=%s" % (self.url, file), timeout=5).read())
					except:
						return self.ImportChannelsDone(False, _("ERROR downloading file %s") % file) if config.usage.remote_fallback_nok.value else None
			except:
				return self.ImportChannelsDone(False, _("Using channels of this receiver, error import channels from %s") % self.url) if config.usage.remote_fallback_nok.value else None

			print("[ImportChannels] Removing files...")
			files = [file for file in os.listdir("%s" % channelslistpath) if file.startswith(channelslist)]
			for file in files:
				os.remove("%s/%s" % (channelslistpath, file))
			print("[ImportChannels] copying files...")
			files = [x for x in os.listdir(channelslistserver) if x.startswith(channelslist)]
			for file in files:
				shutil.move("%s/%s" % (channelslistserver, file), "%s/%s" % (channelslistpath, file))
			shutil.rmtree(channelslistserver)
			eDVBDB.getInstance().reloadBouquets()
			eDVBDB.getInstance().reloadServicelist()
			return self.ImportChannelsDone(False, _("Channels imported successfully from %s") % self.url) if config.usage.remote_fallback_ok.value else None

		#self.ImportChannelsDone(True, {"channels": _("Channels"), "epg": _("EPG"), "channels_epg": _("Channels and EPG")}[self.remote_fallback_import])

	def ImportChannelsDone(self, flag, message=None):
		shutil.rmtree(self.tmp_dir, True)
		if config.usage.remote_fallback_ok.value:
			AddNotificationWithID("ChannelsImportOK", MessageBox, _("%s") % message, type=MessageBox.TYPE_INFO, timeout=5)
		elif config.usage.remote_fallback_nok.value:
			AddNotificationWithID("ChannelsImportNOK", MessageBox, _("%s") % message, type=MessageBox.TYPE_ERROR, timeout=5)
