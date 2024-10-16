from enigma import RT_HALIGN_LEFT, RT_VALIGN_CENTER, eListboxPythonMultiContent, gFont

from skin import fonts, parameters, parseVerticalAlignment
from Components.MenuList import MenuList
from Tools.Directories import SCOPE_GUISKIN, resolveFilename
from Tools.LoadPixmap import LoadPixmap
from string import digits


def ChoiceEntryComponent(key=None, text=None):
	verticalAlignment = parseVerticalAlignment(parameters.get("ChoicelistVerticalAlignment", "top")) << 4  # This is a hack until other images fix their code.
	text = ["--"] if text is None else text
	res = [text]
	if text[0] == "--":
		x, y, w, h = parameters.get("ChoicelistDash", (0, 0, 1280, 25))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "-" * 200))
	else:
		if key:
			x, y, w, h = parameters.get("ChoicelistName", (45, 0, 1235, 25))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, text[0]))
			if key in ("dummy", "none"):
				png = None
			elif key == "expandable":
				png = LoadPixmap(resolveFilename(SCOPE_GUISKIN, "icons/expandable.png"))
			elif key == "expanded":
				png = LoadPixmap(resolveFilename(SCOPE_GUISKIN, "icons/expanded.png"))
			elif key == "verticalline":
				png = LoadPixmap(resolveFilename(SCOPE_GUISKIN, "icons/verticalline.png"))
			elif key in list(digits) + ["red", "green", "yellow", "blue", "menu"]:
				png = LoadPixmap(resolveFilename(SCOPE_GUISKIN, f"buttons/key_{key}.png"))
			if key not in list(digits) + ["red", "green", "yellow", "blue", "menu", "expandable", "expanded", "verticalline"]:
				png = LoadPixmap(resolveFilename(SCOPE_GUISKIN, "buttons/bullet.png"))
			if png:
				x, y, w, h = parameters.get("ChoicelistIcon", (5, 0, 35, 25))
				if key == "verticalline" and "ChoicelistIconVerticalline" in parameters:
					x, y, w, h = parameters.get("ChoicelistIconVerticalline", (5, 0, 35, 25))
				if key == "expanded" and "ChoicelistIconExpanded" in parameters:
					x, y, w, h = parameters.get("ChoicelistIconExpanded", (5, 0, 35, 25))
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, x, y, w, h, png))
		else:
			x, y, w, h = parameters.get("ChoicelistNameSingle", (5, 0, 1275, 25))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_HALIGN_LEFT | verticalAlignment, text[0]))
	return res


class ChoiceList(MenuList):
	def __init__(self, list, selection=0, enableWrapAround=False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		font = fonts.get("ChoiceList", ("Regular", 20, 25))
		self.l.setFont(0, gFont(font[0], font[1]))
		self.l.setItemHeight(font[2])
		self.itemHeight = font[2]
		self.selection = selection

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		self.moveToIndex(self.selection)

	def getItemHeight(self):
		return self.itemHeight
