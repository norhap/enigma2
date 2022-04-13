from Components.Converter.Converter import Converter
from sys import version_info


class SensorToText(Converter):
	def __init__(self, arguments):
		Converter.__init__(self, arguments)

	def getText(self):
		if self.source.getValue() is None:
			return ""
		mark = " "
		unit = self.source.getUnit()
		if unit in ('C', 'F'):
			mark = str('\xb0')
			markPython2 = str('\xc2\xb0')
		return "%d%s%s" % (self.source.getValue(), mark, unit) if version_info.major >= 3 else "%d%s%s" % (self.source.getValue(), markPython2, unit)

	text = property(getText)
