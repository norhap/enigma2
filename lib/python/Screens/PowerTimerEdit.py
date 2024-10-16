from time import time
from timer import TimerEntry as RealTimerEntry

from PowerTimer import PowerTimerEntry, AFTEREVENT
from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
from Components.PowerTimerList import PowerTimerList
from Components.Sources.StaticText import StaticText
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.PowerTimerEntry import TimerEntry
from Screens.Screen import Screen
from Screens.TimerEntry import TimerLog
from Tools.BoundFunction import boundFunction
from Tools.FuzzyDate import FuzzyTime


class PowerTimerEditList(Screen):
	EMPTY = 0
	ENABLE = 1
	DISABLE = 2
	CLEANUP = 3
	DELETE = 4

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "TimerEditList"
		Screen.setTitle(self, _("PowerTimer List"))
		self.onChangedEntry = []
		list = []
		self.list = list
		self.fillTimerList()
		self["timerlist"] = PowerTimerList(list)
		self.key_red_choice = self.EMPTY
		self.key_yellow_choice = self.EMPTY
		self.key_blue_choice = self.EMPTY
		self["key_red"] = StaticText("")
		self["key_green"] = StaticText(_("Add"))
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText("")
		self["key_info"] = StaticText("")
		self["description"] = Label()
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ShortcutActions", "TimerEditActions"],
			{
			"ok": self.openEdit,
			"cancel": self.leave,
			"green": self.addCurrentTimer,
			"blue": self.enableDisableTimerLog,
			"log": self.showLog,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down
		}, -1)
		self.session.nav.PowerTimer.on_state_change.append(self.onStateChange)
		self.onShown.append(self.updateState)

	def enableDisableTimerLog(self):
		config.powertimerlog.actived.value = False if config.powertimerlog.actived.value else True
		text = _("Enable log") if not config.powertimerlog.actived.value else _("Disable log")
		self["key_blue"].setText(text)
		config.powertimerlog.actived.save()

	def up(self):
		self["timerlist"].instance.moveSelection(self["timerlist"].instance.moveUp)
		self.updateState()

	def down(self):
		self["timerlist"].instance.moveSelection(self["timerlist"].instance.moveDown)
		self.updateState()

	def left(self):
		self["timerlist"].instance.moveSelection(self["timerlist"].instance.pageUp)
		self.updateState()

	def right(self):
		self["timerlist"].instance.moveSelection(self["timerlist"].instance.pageDown)
		self.updateState()

	def toggleDisabledState(self):
		cur = self["timerlist"].getCurrent()
		if cur:
			t = cur
			if t.disabled:
				print("[PowerTimerEdit] try to enable timer")
				t.enable()
			else:
				if t.isRunning():
					if t.repeated:
						list = (
							(_("Stop current event but not future events"), "stoponlycurrent"),
							(_("Stop current event and disable future events"), "stopall"),
							(_("Don't stop current event but disable future events"), "stoponlycoming")
						)
						self.session.openWithCallback(boundFunction(self.runningEventCallback, t), ChoiceBox, title=_("Repeating the event currently recording... What do you want to do?"), list=list)
				else:
					t.disable()
			self.session.nav.PowerTimer.timeChanged(t)
			self.refill()
			self.updateState()

	def runningEventCallback(self, t, result):
		if result is not None:
			if result[1] == "stoponlycurrent" or result[1] == "stopall":
				t.enable()
				t.processRepeated(findRunningEvent=False)
				self.session.nav.PowerTimer.doActivate(t)
			if result[1] == "stoponlycoming" or result[1] == "stopall":
				t.disable()
			self.session.nav.PowerTimer.timeChanged(t)
			self.refill()
			self.updateState()

	def removeAction(self, descr):
		actions = self["actions"].actions
		if descr in actions:
			del actions[descr]

	def updateState(self):
		cur = self["timerlist"].getCurrent()
		if cur:
			if self.key_red_choice != self.DELETE:
				self["actions"].actions.update({"red": self.removeTimerQuestion})
				self["key_red"].setText(_("Delete"))
				self.key_red_choice = self.DELETE

			if cur.disabled and (self.key_yellow_choice != self.ENABLE):
				self["actions"].actions.update({"yellow": self.toggleDisabledState})
				self["key_yellow"].setText(_("Enable"))
				self.key_yellow_choice = self.ENABLE
				self["key_info"].setText("Info")
			elif cur.isRunning() and not cur.repeated and (self.key_yellow_choice != self.EMPTY):
				self.removeAction("yellow")
				self["key_yellow"].setText("")
				self.key_yellow_choice = self.EMPTY
				self["key_info"].setText("")
			elif ((not cur.isRunning()) or cur.repeated) and (not cur.disabled) and (self.key_yellow_choice != self.DISABLE):
				self["actions"].actions.update({"yellow": self.toggleDisabledState})
				self["key_yellow"].setText(_("Disable"))
				text = _("Enable log") if not config.powertimerlog.actived.value else _("Disable log")
				self["key_blue"].setText(text)
				self.key_yellow_choice = self.DISABLE
				self["key_info"].setText("Info")
		else:
			if self.key_red_choice != self.EMPTY:
				self.removeAction("red")
				self["key_red"].setText("")
				self.key_red_choice = self.EMPTY
			if self.key_yellow_choice != self.EMPTY:
				self.removeAction("yellow")
				self["key_yellow"].setText("")
				self.key_yellow_choice = self.EMPTY

		showCleanup = True
		for x in self.list:
			if not x[0].disabled and x[1]:
				break
		else:
			showCleanup = False

		if showCleanup and (self.key_blue_choice != self.CLEANUP):
			self["actions"].actions.update({"blue": self.cleanupQuestion})
			self["key_blue"].setText(_("Cleanup"))
			self.key_blue_choice = self.CLEANUP
		elif (not showCleanup) and (self.key_blue_choice != self.EMPTY):
			self.removeAction("blue")
			self["key_blue"].setText("")
			self.key_blue_choice = self.EMPTY
		if len(self.list) == 0:
			return
		timer = self['timerlist'].getCurrent()

		if timer:
			time = "%s %s ... %s" % (FuzzyTime(timer.begin)[0], FuzzyTime(timer.begin)[1], FuzzyTime(timer.end)[1])
			duration = ("(%d " + _("mins") + ")") % ((timer.end - timer.begin) / 60)

			if timer.state == RealTimerEntry.StateWaiting:
				state = _("waiting")
			elif timer.state == RealTimerEntry.StatePrepared:
				state = _("about to start")
			elif timer.state == RealTimerEntry.StateRunning:
				state = _("running...")
			elif timer.state == RealTimerEntry.StateEnded:
				state = _("done!")
			else:
				state = _("<unknown>")
		else:
			time = ""
			duration = ""
			state = ""
		for cb in self.onChangedEntry:
			cb(time, duration, state)

	def fillTimerList(self):
		from functools import cmp_to_key
		# helper function to move finished timers to end of list

		def eol_compare(x, y):
			if x[0].state != y[0].state and x[0].state == RealTimerEntry.StateEnded or y[0].state == RealTimerEntry.StateEnded:
				return (x[0].state > y[0].state) - (x[0].state < y[0].state)
			return (x[0].begin > y[0].begin) - (x[0].begin < y[0].begin)

		list = self.list
		del list[:]
		list.extend([(timer, False) for timer in self.session.nav.PowerTimer.timer_list])
		list.extend([(timer, True) for timer in self.session.nav.PowerTimer.processed_timers])
		if config.usage.timerlist_finished_timer_position.index:  # end of list
			list.sort(key=cmp_to_key(eol_compare))
		else:
			list.sort(key=lambda x: x[0].begin)

	def showLog(self):
		cur = self["timerlist"].getCurrent()
		if cur:
			self.session.openWithCallback(self.finishedEdit, TimerLog, cur)

	def openEdit(self):
		cur = self["timerlist"].getCurrent()
		if cur:
			self.session.openWithCallback(self.finishedEdit, TimerEntry, cur)

	def cleanupQuestion(self):
		self.session.openWithCallback(self.cleanupTimer, MessageBox, _("Really delete completed timers?"))

	def cleanupTimer(self, delete):
		if delete:
			self.session.nav.PowerTimer.cleanup()
			self.refill()
			self.updateState()

	def removeTimerQuestion(self):
		cur = self["timerlist"].getCurrent()
		if not cur:
			return

		self.session.openWithCallback(self.removeTimer, MessageBox, _("Do you really want to delete this timer?"), default=False)

	def removeTimer(self, result):
		if not result:
			return
		list = self["timerlist"]
		cur = list.getCurrent()
		if cur:
			timer = cur
			timer.afterEvent = AFTEREVENT.NONE
			self.session.nav.PowerTimer.removeEntry(timer)
			self.refill()
			self.updateState()

	def refill(self):
		oldsize = len(self.list)
		self.fillTimerList()
		lst = self["timerlist"]
		newsize = len(self.list)
		if oldsize and oldsize != newsize:
			idx = lst.getCurrentIndex()
			lst.entryRemoved(idx)
		else:
			lst.invalidate()

	def addCurrentTimer(self):
		data = (int(time() + 60), int(time() + 120))
		self.addTimer(PowerTimerEntry(checkOldTimers=True, *data))

	def addTimer(self, timer):
		self.session.openWithCallback(self.finishedAdd, TimerEntry, timer)

	def finishedEdit(self, answer):
		if answer[0]:
			entry = answer[1]
			self.session.nav.PowerTimer.timeChanged(entry)
			self.fillTimerList()
			self.updateState()
		else:
			print("[PowerTimerEdit] PowerTimerEdit aborted")

	def finishedAdd(self, answer):
		if answer[0]:
			entry = answer[1]
			simulTimerList = self.session.nav.PowerTimer.record(entry)
			self.fillTimerList()
			self.updateState()
		else:
			print("[PowerTimerEdit] TimerEdit aborted")

	def finishSanityCorrection(self, answer):
		self.finishedAdd(answer)

	def leave(self):
		self.session.nav.PowerTimer.on_state_change.remove(self.onStateChange)
		self.close()

	def onStateChange(self, entry):
		self.refill()
		self.updateState()
