from sys import maxsize

from enigma import eActionMap

from Components.InputDevice import remoteControl
from Components.ActionMap import ActionMap
from Components.HelpMenuList import HelpMenuList
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Screens.Rc import Rc
from Screens.Screen import Screen


class HelpableScreen:
	def __init__(self):
		self["helpActions"] = ActionMap(["HelpActions"], {
			"displayHelp": self.showHelp
		}, prio=0)
		self["key_help"] = StaticText(_("HELP"))

	def showHelp(self):
		# try:
		# 	if self.secondInfoBarScreen and self.secondInfoBarScreen.shown:
		# 		self.secondInfoBarScreen.hide()
		# except Exception:
		# 	pass
		self.session.openWithCallback(self.callHelpAction, HelpMenu, self.helpList)

	def callHelpAction(self, *args):
		if args:
			(actionmap, context, action) = args
			actionmap.action(context, action)


class HelpMenu(Screen, Rc):
	def __init__(self, session, helpList):
		Screen.__init__(self, session)
		Rc.__init__(self)
		self.setTitle(_("Help"))
		self["list"] = HelpMenuList(helpList, self.close)
		self["list"].onSelectionChanged.append(self.selectionChanged)
		self["buttonlist"] = Label("")
		self["description"] = Label("")
		self["key_help"] = StaticText(_("HELP"))
		self["helpActions"] = ActionMap(["HelpActions", "OkCancelActions"], {
			"cancel": self.close,  # self.closeHelp,
			"ok": self.enterItem,
			"displayHelp": self.showHelp,
			"displayHelpLong": self.showButtons
		}, prio=-1)
		# Wildcard binding with slightly higher priority than the
		# wildcard bindings in InfoBarGenerics.InfoBarUnhandledKey,
		# but with a gap so that other wildcards can be interposed
		# if needed.
		eActionMap.getInstance().bindAction("", maxsize - 100, self["list"].handleButton)
		# Ignore keypress breaks for the keys in the ListboxActions context.
		self["listboxFilterActions"] = ActionMap(["HelpMenuListboxActions"], {
			"ignore": lambda: 1
		}, prio=1)
		self.onClose.append(self.closeHelp)
		self.onLayoutFinish.append(self.selectionChanged)

	def enterItem(self):
		self["list"].enterItem() # def enterItem(self) HelpMenuList.

	def closeHelp(self):
		eActionMap.getInstance().unbindAction("", self["list"].handleButton)
		self["list"].onSelectionChanged.remove(self.selectionChanged)

	def selectionChanged(self):
		self.clearSelectedKeys()
		selection = self["list"].getCurrent()
		if selection:
			baseButtons = []
			longButtons = []
			shiftButtons = []
			buttonList = []
			for button in selection[3]:
				label = remoteControl.getRemoteControlKeyLabel(button[0])
				if label is None:
					label = _("Note: No button defined for this action!")
				if len(button) > 1:
					if button[1] == "SHIFT":
						self.selectKey(KEYIDS.get("KEY_SHIFT"))
						shiftButtons.append(label)
					elif button[1] == "LONG":
						longButtons.append(label)
				else:
					baseButtons.append(label)
				self.selectKey(button[0])
			if baseButtons:
				buttonList.append(pgettext("Text list separator", ", ").join(sorted(baseButtons)))
			if longButtons:
				buttonList.append(_("Long press: %s") % pgettext("Text list separator", ", ").join(sorted(longButtons)))
			if shiftButtons:
				buttonList.append(_("Shift: %s") % pgettext("Text list separator", ", ").join(sorted(shiftButtons)))
			self["buttonlist"].setText("; ".join(buttonList))
			helpText = selection[4]
			self["description"].setText(isinstance(helpText, (list, tuple)) and len(helpText) > 1 and helpText[1] or "")

	def showHelp(self):
		# MessageBox import deferred so that MessageBox's import of HelpMenu doesn't cause an import loop.
		from Screens.MessageBox import MessageBox
		helpText = "\n\n".join([
			_("HELP provides brief information for buttons in your current context."),
			_("Navigate up/down with UP/DOWN buttons and page up/down with LEFT/RIGHT. OK to perform the action described in the currently highlighted help."),
			_("Other buttons will jump to the help information for that button, if there is help available."),
			_("If an action is user-configurable, its help entry will be flagged with a '(C)' suffix."),
			_("A highlight on the remote control image shows which button the help refers to. If more than one button performs the indicated function, more than one highlight will be shown. Text below the list lists the active buttons and whether the function requires a long press or SHIFT of the button(s)."),
			_("Configuration options for the HELP screen can be found in 'MENU > Setup > User Interface > User Interface Setup'."),
			_("Press EXIT to return to the help screen.")
		])
		self.session.open(MessageBox, helpText, type=MessageBox.TYPE_INFO, title=_("Help Screen Information"))

	def showButtons(self):
		self.testHighlights(self.selectionChanged)
