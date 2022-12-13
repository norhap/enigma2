# -*- coding: utf-8 -*-
from os.path import exists
from Tools.Directories import SCOPE_SKINS, resolveFilename
from boxbranding import getRCName


class RcModel:
	def __init__(self):
		pass

	def getRcFile(self, ext):
		remote = getRCName()
		f = resolveFilename(SCOPE_SKINS, 'rc_models/' + remote + '.' + ext)
		if not exists(f):
			f = resolveFilename(SCOPE_SKINS, 'rc_models/dmm1.' + ext)
		return f

	def getRcImg(self):
		return self.getRcFile('png')

	def getRcPositions(self):
		return self.getRcFile('xml')


rc_model = RcModel()
