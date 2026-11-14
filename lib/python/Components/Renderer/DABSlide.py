from os import stat
from os.path import isfile

from enigma import ePixmap, eServiceReference, getDesktop, iPlayableService, iServiceInformation

from Components.config import config
from Components.Renderer.Renderer import Renderer
from Tools.LoadPixmap import LoadPixmap


class DABSlide(Renderer):
	GUI_WIDGET = ePixmap

	def __init__(self):
		Renderer.__init__(self)
		self.signature = None
		config.dab.slideshow.addNotifier(self.slideshowChanged, initial_call=False)

	def destroy(self):
		config.dab.slideshow.removeNotifier(self.slideshowChanged)
		Renderer.destroy(self)

	def slideshowChanged(self, configElement):
		self.changed((self.CHANGED_DEFAULT,))

	def applySkin(self, desktop, parent):
		result = Renderer.applySkin(self, desktop, parent)
		self.changed((self.CHANGED_DEFAULT,))
		return result

	def changed(self, what):
		if self.instance is None:
			return
		reference = self.source and self.source.serviceref
		if what[0] == self.CHANGED_CLEAR or (what[0] == self.CHANGED_SPECIFIC and what[1] == iPlayableService.evEnd) or not reference or reference.type != eServiceReference.idServiceDAB:
			self.signature = None
			self.instance.hide()
			return
		service = self.source.service
		info = service and service.info()
		path = info and config.dab.slideshow.value and info.getInfoString(iServiceInformation.sTagPreviewImage) or ""
		if not path or not isfile(path):
			path = info and info.getInfoString(iServiceInformation.sTagImage) or ""
		if not path or not isfile(path):
			self.signature = None
			self.instance.hide()
			return
		try:
			status = stat(path)
		except OSError as error:
			print(f"[DABSlide] Unable to read '{path}': {error}")
			self.signature = None
			self.instance.hide()
			return
		signature = (path, status.st_mtime_ns, status.st_size)
		if signature != self.signature:
			pixmap = LoadPixmap(path, desktop=getDesktop(0), cached=False, autoDetect=True)
			if pixmap is None:
				print(f"[DABSlide] Unable to decode '{path}'.")
				self.signature = None
				self.instance.hide()
				return
			self.instance.setPixmap(pixmap)
			self.signature = signature
		self.instance.show()
