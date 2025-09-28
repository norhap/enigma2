from Components.Renderer.Renderer import Renderer

from enigma import eCanvas, eRect, gRGB


class Canvas(Renderer):
	GUI_WIDGET = eCanvas

	def __init__(self):
		Renderer.__init__(self)
		self.sequence = None
		self.draw_count = 0

	def pull_updates(self):
		if self.instance is None:
			return

		# do an incremental update
		list = self.source.drawlist
		if list is None:
			return

		# if the lists sequence count changed, re-start from begin
		if list[0] != self.sequence:
			self.sequence = list[0]
			self.draw_count = 0

		self.draw(list[1][self.draw_count:])
		self.draw_count = len(list[1])

	def draw(self, list):
		for L in list:
			if L[0] == 1:
				self.instance.fillRect(eRect(L[1], L[2], L[3], L[4]), gRGB(L[5]))
			elif L[0] == 2:
				self.instance.writeText(eRect(L[1], L[2], L[3], L[4]), gRGB(L[5]), gRGB(L[6]), L[7], L[8], L[9])
			elif L[0] == 3:
				self.instance.drawLine(int(L[1]), int(L[2]), int(L[3]), int(L[4]), gRGB(L[5]))
			elif L[0] == 4:
				self.instance.drawRotatedLine(int(L[1]), int(L[2]), int(L[3]), int(L[4]), int(L[5]), int(L[6]), L[7], L[8], gRGB(L[9]))
			else:
				print("[Canvas] drawlist entry:", L)
				raise RuntimeError("invalid drawlist entry")

	def changed(self, what):
		self.pull_updates()

	def postWidgetCreate(self, instance):
		self.sequence = None

		from enigma import eSize

		def parseSize(str):
			x, y = str.split(',')
			return eSize(int(x), int(y))

		for (attrib, value) in self.skinAttributes:
			if attrib == "size":
				self.instance.setSize(parseSize(value))

		self.pull_updates()
