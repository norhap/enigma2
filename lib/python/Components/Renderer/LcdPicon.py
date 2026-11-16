import os
from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, ePicLoad
from Tools.Directories import pathExists, SCOPE_GUISKIN, resolveFilename
from boxbranding import getDisplayType
from Components.config import config
from Components.Renderer.Picon import PiconLocator, getDABCachedImage


def useLcdPicons():
	return getDisplayType() in ("bwlcd255", "bwlcd140", "bwlcd128") or config.lcd.picon_pack.value


lcdPiconLocator = None


def initPiconPaths(_=None):
	global lcdPiconLocator
	lcdPiconLocator = PiconLocator(['lcd_picon', 'piconlcd']) if useLcdPicons() else PiconLocator()


config.lcd.picon_pack.addNotifier(initPiconPaths)


class LcdPicon(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.PicLoad = ePicLoad()
		self.PicLoad.PictureData.get().append(self.updatePicon)
		self.piconsize = (0, 0)
		self.requestedPicon = None
		self.loadingPicon = None
		config.lcd.picon_pack.addNotifier(self.configChanged)

	def configChanged(self, _):
		self.pngname = None
		serviceName = "lcd_picon_default" if useLcdPicons() else "picon_default"
		pngname = lcdPiconLocator.findPicon(serviceName)
		if not pngname:
			pngname = resolveFilename(SCOPE_GUISKIN, serviceName + ".png")
		self.defaultpngname = pngname if os.path.getsize(pngname) else None
		self.changed((self.CHANGED_DEFAULT,))

	def destroy(self):
		# remove the notifier before properties get destroyed
		config.lcd.picon_pack.removeNotifier(self.configChanged)
		self.PicLoad.PictureData.get().remove(self.updatePicon)
		Renderer.destroy(self)

	def applySkin(self, desktop, parent):
		attribs = self.skinAttributes[:]
		for (attrib, value) in self.skinAttributes:
			if attrib == "path":
				lcdPiconLocator.addSearchPath(value)
				attribs.remove((attrib, value))
			elif attrib == "size":
				self.piconsize = value
		self.skinAttributes = attribs
		rc = Renderer.applySkin(self, desktop, parent)
		self.changed((self.CHANGED_DEFAULT,))
		return rc

	GUI_WIDGET = ePixmap

	def updatePicon(self, picInfo=None):
		ptr = self.PicLoad.getData()
		loaded = self.loadingPicon
		self.loadingPicon = None
		if self.instance and loaded and loaded == self.requestedPicon:
			if ptr is not None:
				self.instance.setPixmap(ptr.__deref__())
				self.instance.show()
			else:
				print(f"[LcdPicon] Unable to decode '{loaded[0]}'.")
				self.pngname = None
				self.instance.hide()
		elif self.instance and self.requestedPicon:
			self.loadPicon()

	def loadPicon(self):
		self.loadingPicon = self.requestedPicon
		pngname = self.loadingPicon[0]
		self.PicLoad.setPara((self.piconsize[0], self.piconsize[1], 0, 0, 1, 1, "#FF000000"))
		if self.PicLoad.startDecode(pngname):
			print(f"[LcdPicon] Unable to start decoding '{pngname}'.")
			self.loadingPicon = None
			self.pngname = None
			self.instance.hide()

	def changed(self, what):
		if self.instance and self.source:
			if what[0] in (self.CHANGED_DEFAULT, self.CHANGED_ALL, self.CHANGED_SPECIFIC):
				dabImage = getDABCachedImage(self.source.text)
				pngname = dabImage or lcdPiconLocator.getPiconName(self.source.text)
				if not pathExists(pngname):  # no picon for service found
					pngname = self.defaultpngname
				pngkey = pngname
				if dabImage and pngname == dabImage:
					try:
						status = os.stat(pngname)
						pngkey = (pngname, status.st_mtime_ns, status.st_size)
					except OSError as error:
						print(f"[LcdPicon] Unable to read DAB logo '{pngname}': {error}")
						pngname = self.defaultpngname
						pngkey = pngname
				if self.pngname != pngkey:
					self.pngname = pngkey
					self.requestedPicon = (pngname, pngkey) if pngname else None
					self.instance.hide()
					if self.requestedPicon and self.loadingPicon is None:
						self.loadPicon()
			elif what[0] == self.CHANGED_CLEAR:
				self.pngname = None
				self.requestedPicon = None
				self.instance.hide()
