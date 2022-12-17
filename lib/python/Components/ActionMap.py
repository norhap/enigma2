from enigma import eActionMap
from Components.config import config

keyBindings = {}


def addKeyBinding(filename, keyId, context, mapto, flags):
	keyBindings.setdefault((context, mapto), []).append((keyId, filename, flags))


def queryKeyBinding(context, mapto):  # Returns a list of (keyId, flags) for a specified mapto action in a context.
	if (context, mapto) in keyBindings:
		return [(x[0], x[2]) for x in keyBindings[(context, mapto)]]
	return []


class ActionMap:
	def __init__(self, contexts=None, actions=None, prio=0):
		self.contexts = contexts or []
		self.actions = actions or {}
		self.prio = prio
		self.p = eActionMap.getInstance()
		self.bound = False
		self.exec_active = False
		self.enabled = True
		unknown = list(self.actions.keys())
		for action in unknown[:]:
			for context in self.contexts:
				if queryKeyBinding(context, action):
					unknown.remove(action)
					break
		if unknown:
			print(_("[ActionMap] Missing actions in keymap, missing context in this list ->'%s' for mapto='%s'.") % ("', '".join(sorted(self.contexts)), "', '".join(sorted(list(self.actions.keys())))))

	def setEnabled(self, enabled):
		self.enabled = enabled
		self.checkBind()

	def doBind(self):
		if not self.bound:
			for context in self.contexts:
				self.p.bindAction(context, self.prio, self.action)
			self.bound = True

	def doUnbind(self):
		if self.bound:
			for context in self.contexts:
				self.p.unbindAction(context, self.action)
			self.bound = False

	def checkBind(self):
		if self.exec_active and self.enabled:
			self.doBind()
		else:
			self.doUnbind()

	def execBegin(self):
		self.exec_active = True
		self.checkBind()

	def execEnd(self):
		self.exec_active = False
		self.checkBind()

	def action(self, context, action):
		if action in self.actions:
			print("[ActionMap] Keymap '%s' -> Action mapto='%s'." % (context, action))
			res = self.actions[action]()
			if res is not None:
				return res
			return 1
		else:
			print(_("[ActionMap] in this context list -> '%s' -> mapto='%s' it is not defined in this code 'missing'.") % (context, action))
			return 0

	def destroy(self):
		pass


class NumberActionMap(ActionMap):
	def action(self, contexts, action):
		if action in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9") and action in self.actions:
			res = self.actions[action](int(action))
			if res is not None:
				return res
			return 1
		else:
			return ActionMap.action(self, contexts, action)


class HelpableActionMap(ActionMap):
	# An Actionmap which automatically puts the actions into the helpList.
	#
	# A context list is allowed, and for backward compatibility, a single
	# string context name also is allowed.
	#
	# Sorry for this complicated code.  It's not more than converting a
	# "documented" actionmap (where the values are possibly (function,
	# help)-tuples) into a "classic" actionmap, where values are just
	# functions.  The classic actionmap is then passed to the
	# ActionMapconstructor,	the collected helpstrings (with correct
	# context, action) is added to the screen's "helpList", which will
	# be picked up by the "HelpableScreen".
	def __init__(self, parent, contexts, actions=None, prio=0, description=None):
		def exists(record):
			for context in parent.helpList:
				if context[1] != "NavigationActions":
					if record in context[2]:
						print("[ActionMap] removed duplicity: %s %s" % (context[1], record))
						return True
			return False

		if isinstance(contexts, str):
			contexts = [contexts]
		actions = actions or {}
		self.description = description
		adict = {}
		for context in contexts:
			if config.usage.actionLeftRightToPageUpPageDown.value and context == "DirectionActions":
				copyLeft = "left" not in actions and "pageUp" in actions
				copyRight = "right" not in actions and "pageDown" in actions
			else:
				copyLeft = False
				copyRight = False
			alist = []
			for (action, funchelp) in actions.items():
				# Check if this is a tuple.
				if isinstance(funchelp, tuple):
					if queryKeyBinding(context, action):
						if not exists((action, funchelp[1])):
							alist.append((action, funchelp[1]))
					adict[action] = funchelp[0]
				else:
					if queryKeyBinding(context, action):
						if not exists((action, None)):
							alist.append((action, None))
					adict[action] = funchelp
				if copyLeft and action == "pageUp":
					alist.append(("left", funchelp[1]))
					adict["left"] = funchelp[0]
				if copyRight and action == "pageDown":
					alist.append(("right", funchelp[1]))
					adict["right"] = funchelp[0]
			parent.helpList.append((self, context, alist))
		ActionMap.__init__(self, contexts, adict, prio)


class HelpableNumberActionMap(NumberActionMap, HelpableActionMap):
	def __init__(self, parent, contexts, actions=None, prio=0, description=None):
		# Initialise NumberActionMap with empty context and actions
		# so that the underlying ActionMap is only initialised with
		# these once, via the HelpableActionMap.
		NumberActionMap.__init__(self, [], {})
		HelpableActionMap.__init__(self, parent, contexts, actions, prio, description)
