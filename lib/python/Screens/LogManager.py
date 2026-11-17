# -*- coding: utf-8 -*-
from enigma import eTimer, eBackgroundFileEraser, eLabel, eEnv, gFont, fontRenderClass
from os import remove, walk, stat, fstat, rmdir, listdir
from os.path import join, getsize, isdir, isfile, exists, realpath
from glob import glob
import re
from shutil import which
from time import time
import Components.Task
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config, configfile
from Components.FileList import MultiFileSelectList
from Components.GUIComponent import GUIComponent
from Components.MenuList import MenuList
from Components.VariableText import VariableText
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Console import Console
from Tools.TextBoundary import getTextBoundarySize

_session = None
CORE_DUMP_PATTERN = r"\d+-enigma2-core\.dump(?:\.\d+)?"
CRASH_LIST_PATTERN = r"enigma2_crash_|(?:^|/)" + CORE_DUMP_PATTERN + r"$"


def get_size(start_path=None):
	total_size = 0
	if start_path:
		for dirpath, dirnames, filenames in walk(start_path):
			for f in filenames:
				fp = join(dirpath, f)
				total_size += getsize(fp)
		return total_size
	return 0


def AutoLogManager(session=None, **kwargs):
	global debuglogcheckpoller
	debuglogcheckpoller = LogManagerPoller()
	debuglogcheckpoller.start()


class LogManagerPoller:
	"""Automatically Poll LogManager"""

	def __init__(self):
		# Init Timer
		self.TrimTimer = eTimer()
		self.TrashTimer = eTimer()

	def start(self):
		if self.TrashTimerJob not in self.TrashTimer.callback:
			self.TrashTimer.callback.append(self.TrashTimerJob)
		self.TrashTimer.startLongTimer(0)

	def stop(self):
		if self.TrashTimerJob in self.TrashTimer.callback:
			self.TrashTimer.callback.remove(self.TrashTimerJob)
		self.TrashTimer.stop()

	def TrashTimerJob(self):
		print("[LogManager] Trash Poll Started")
		Components.Task.job_manager.AddJob(self.createTrashJob())

	def createTrashJob(self):
		job = Components.Task.Job(_("LogManager"))
		task = Components.Task.PythonTask(job, _("Checking Logs..."))
		task.work = self.JobTrash
		task.weighting = 1
		return job

	def openFiles(self, ctimeLimit, allowedBytes):
		ctimeLimit = ctimeLimit
		allowedBytes = allowedBytes

	def JobTrash(self):
		ctimeLimit = time() - (config.crash.daysloglimit.value * 3600 * 24)
		allowedBytes = 1024 * 1024 * int(config.crash.sizeloglimit.value)

		matches = set()
		print("[LogManager] probing folders")
		with open("/proc/mounts", "r") as f:
			for line in f:
				parts = line.strip().split()
				if len(parts) > 1 and isdir(join(parts[1], "logs")):
					matches.add(realpath(join(parts[1], "logs")))
		matches.add(realpath("/home/root/logs"))
		matches.add(realpath(config.crash.debugPath.value))

		print("[LogManager] found following log(s):", matches)
		active = set()
		for fd in (1, 2):
			try:
				st = fstat(fd)
				active.add((st.st_dev, st.st_ino))
			except OSError as e:
				print("[LogManager] Failed to inspect output descriptor %d:" % fd, e)

		folders = {}
		seen = set()
		crashes = []
		core_dumps = set()
		for logsfolder in sorted(matches, key=len):
			print("[LogManager] looking in:", logsfolder)
			entries = []
			folders[logsfolder] = entries
			for root, dirs, files in walk(logsfolder, topdown=False):
				for name in files:
					fn = join(root, name)
					path = realpath(fn)
					if path in seen:
						continue
					seen.add(path)
					try:
						st = stat(fn)
					except OSError as e:
						print("[LogManager] Failed to stat %s:" % fn, e)
						continue
					entry = (st.st_ctime, fn, st.st_size, (st.st_dev, st.st_ino))
					entries.append(entry)
					if name.startswith("enigma2_crash") and name.endswith(".log"):
						crashes.append((st.st_mtime, fn))
					elif re.fullmatch(CORE_DUMP_PATTERN, name):
						core_dumps.add(fn)
				for name in dirs:
					try:
						rmdir(join(root, name))
					except OSError:
						pass

		protected = {fn for _, fn in sorted(crashes, reverse=True)[:5]} | core_dumps
		for logsfolder, entries in folders.items():
			bytesToRemove = sum(entry[2] for entry in entries if entry[1] not in core_dumps) - allowedBytes
			for ctime, fn, size, identity in sorted(entries):
				if fn in protected or identity in active:
					continue
				if ctime < ctimeLimit or bytesToRemove > 0:
					print("[LogManager] Removing %s (bytes over limit: %d)" % (fn, bytesToRemove))
					eBackgroundFileEraser.getInstance().erase(fn)
					bytesToRemove -= size
		self.TrashTimer.startLongTimer(43200)  # twice a day


class LogManager(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.logs = listdir(config.crash.debugPath.value)
		self.logtype = "crashlogs"
		self["myactions"] = ActionMap(["ColorActions", "OkCancelActions", "DirectionActions"], {
			"ok": self.changeSelectionState,
			"cancel": self.close,
			"red": self.changelogtype,
			"green": self.showLog,
			"yellow": self.deletelog,
			"blue": self.deleteAllLogs,
			"left": self.left,
			"right": self.right,
			"down": self.down,
			"up": self.up
		}, -1)
		if self.logs:
			self["key_red"] = StaticText(_("Debug Logs"))
			self["key_green"] = StaticText(_("View"))
			self["key_yellow"] = StaticText(_("Delete"))
			self["key_blue"] = StaticText(_("Delete all"))
		else:
			self["key_red"] = StaticText("")
			self["key_green"] = StaticText("")
			self["key_yellow"] = StaticText("")
			self["key_blue"] = StaticText("")
		self.onChangedEntry = []
		self.sentsingle = ""
		self.selectedFiles = config.logmanager.sentfiles.value
		self.defaultDir = config.crash.debugPath.value
		self.matchingPattern = CRASH_LIST_PATTERN
		self.filelist = MultiFileSelectList(self.selectedFiles, self.defaultDir, showDirectories=False, matchingPattern=self.matchingPattern)
		self["list"] = self.filelist
		self["LogsSize"] = self.logsinfo = LogInfo(config.crash.debugPath.value, LogInfo.USED, update=False)
		self.onLayoutFinish.append(self.layoutFinished)
		if self.selectionChanged not in self["list"].onSelectionChanged:
			self["list"].onSelectionChanged.append(self.selectionChanged)

	def createSummary(self):
		from Screens.PluginBrowser import PluginBrowserSummary
		return PluginBrowserSummary

	def selectionChanged(self):
		item = self["list"].getCurrent()
		desc = ""
		if item:
			name = str(item[0][0])
		else:
			name = ""
		for cb in self.onChangedEntry:
			cb(name, desc)

	def layoutFinished(self):
		self["LogsSize"].update(config.crash.debugPath.value)
		idx = 0
		self["list"].moveToIndex(idx)
		self.setWindowTitle()

	def setWindowTitle(self):
		self.setTitle(self.defaultDir)

	def up(self):
		self["list"].up()

	def down(self):
		self["list"].down()

	def left(self):
		self["list"].pageUp()

	def right(self):
		self["list"].pageDown()

	def saveSelection(self):
		self.selectedFiles = self["list"].getSelectedList()
		config.logmanager.sentfiles.setValue(self.selectedFiles)
		config.logmanager.sentfiles.save()
		configfile.save()

	def exit(self):
		self.close(None)

	def changeSelectionState(self):
		try:
			self.sel = self["list"].getCurrent()[0]
		except:
			self.sel = None
		if self.sel:
			self["list"].changeSelectionState()
			self.selectedFiles = self["list"].getSelectedList()

	def changelogtype(self):
		self["LogsSize"].update(config.crash.debugPath.value)
		if self.logtype == "crashlogs":
			self["key_red"].setText(_("Crash Logs"))
			self.logtype = "debuglogs"
			self.matchingPattern = "enigma2_debug_"
		else:
			self["key_red"].setText(_("Debug Logs"))
			self.logtype = "crashlogs"
			self.matchingPattern = CRASH_LIST_PATTERN
		self["list"].matchingPattern = re.compile(self.matchingPattern)
		self["list"].changeDir(self.defaultDir)
		if not listdir(config.crash.debugPath.value):
			self["key_red"].setText("")
			self["key_green"].setText("")
			self["key_yellow"].setText("")
			self["key_blue"].setText("")

	def showLog(self):
		if self.logs:
			try:
				self.sel = self["list"].getCurrent()[0]
			except:
				self.sel = None
			if self.sel:
				if re.fullmatch(CORE_DUMP_PATTERN, self.sel[0]):
					self.analyzeCoreDump(self.sel[0])
				else:
					self.session.open(LogManagerViewLog, self.sel[0])
			else:
				self.session.open(MessageBox, _("You have not selected any logs to view."), MessageBox.TYPE_INFO, timeout=10)

	def analyzeCoreDump(self, name):
		path = join(self.defaultDir, name)
		try:
			with open(path, "rb") as dump:
				header = dump.read(18)
		except OSError as e:
			self.session.open(MessageBox, _("Cannot read core dump: %s") % str(e), MessageBox.TYPE_ERROR)
			return
		if len(header) < 18 or header[:4] != b"\x7fELF" or header[4] not in (1, 2) or header[5] not in (1, 2) or int.from_bytes(header[16:18], "little" if header[5] == 1 else "big") != 4:
			self.session.open(MessageBox, _("This file is not a valid ELF core dump."), MessageBox.TYPE_ERROR)
			return
		gdb = which("gdb")
		if not gdb:
			self.session.open(MessageBox, _("GDB is not installed. Install a compatible GDB on the receiver to analyze core dumps."), MessageBox.TYPE_ERROR)
			return
		executable = eEnv.resolve("${bindir}/enigma2")
		if not isfile(executable):
			self.session.open(MessageBox, _("Enigma2 executable not found: %s") % executable, MessageBox.TYPE_ERROR)
			return
		command = (gdb, "--batch", "--nx", "--quiet", "-iex", "set auto-load off", "-ex", "set pagination off", "-ex", "thread apply all bt 30", "--exec", executable, "--core", path)
		self.session.open(CoreDumpConsole, title=_("Core dump analysis"), cmdlist=[command], showScripts=False)

	def deletelog(self):
		if self.logs:
			try:
				self.sel = self["list"].getCurrent()[0]
			except:
				self.sel = None
			self.selectedFiles = self["list"].getSelectedList()
			if self.selectedFiles:
				message = _("Do you want to delete all the selected files?\n\nchoose \"No\" to only delete the currently selected file.")
				ybox = self.session.openWithCallback(self.doDelete1, MessageBox, message, MessageBox.TYPE_YESNO)
				ybox.setTitle(_("Delete Confirmation"))
			elif self.sel:
				message = _("You want to delete this log?\n\n") + str(self.sel[0])
				ybox = self.session.openWithCallback(self.doDelete3, MessageBox, message, MessageBox.TYPE_YESNO)
				ybox.setTitle(_("Delete Confirmation"))
			else:
				self.session.open(MessageBox, _("You have not selected any logs to delete."), MessageBox.TYPE_INFO, timeout=10)

	def deleteAllLogs(self):
		self.logs = [name for name in listdir(self.defaultDir) if not name.startswith(".")]
		if self.logs:
			allfiles = "\n".join(self.logs)
			message = _("You want to delete all files, including core dumps?\n\n") + allfiles
			self.session.openWithCallback(self.doDeleteAllLogs, MessageBox, message, MessageBox.TYPE_YESNO)

	def doDeleteAllLogs(self, answer):
		if answer:
			failed = []
			for name in self.logs:
				try:
					remove(join(self.defaultDir, name))
				except OSError as e:
					print("[LogManager] Failed to remove %s: %s" % (name, e))
					failed.append("%s: %s" % (name, e))
			self.logs = listdir(self.defaultDir)
			self["list"].changeDir(self.defaultDir)
			self["LogsSize"].update(config.crash.debugPath.value)
			if not self.logs:
				self["key_red"].setText("")
				self["key_green"].setText("")
				self["key_yellow"].setText("")
				self["key_blue"].setText("")
			if failed:
				self.session.open(MessageBox, _("Could not delete the following files:\n\n") + "\n".join(failed), MessageBox.TYPE_ERROR)

	def doDelete1(self, answer):
		self.selectedFiles = self["list"].getSelectedList()
		self.selectedFiles = ",".join(self.selectedFiles).replace(",", "\n").replace(config.crash.debugPath.value, "")
		self.sel = self["list"].getCurrent()[0]
		if answer is True:
			message = _("You want to delete all the selected logs?\n\n") + self.selectedFiles
			ybox = self.session.openWithCallback(self.doDelete2, MessageBox, message, MessageBox.TYPE_YESNO)
			ybox.setTitle(_("Delete Confirmation"))
		else:
			message = _("You want to delete this log?\n\n") + str(self.sel[0])
			ybox = self.session.openWithCallback(self.doDelete3, MessageBox, message, MessageBox.TYPE_YESNO)
			ybox.setTitle(_("Delete Confirmation"))

	def doDelete2(self, answer):
		if answer is True:
			self.selectedFiles = self["list"].getSelectedList()
			self["list"].instance.moveSelectionTo(0)
			for file in self.selectedFiles:
				if exists(file):
					remove(file)
					self.changelogtype()
			config.logmanager.sentfiles.setValue("")
			config.logmanager.sentfiles.save()
			configfile.save()
			self["list"].changeDir(self.defaultDir)

	def doDelete3(self, answer):
		if answer is True:
			self.sel = self["list"].getCurrent()[0]
			self["list"].instance.moveSelectionTo(0)
			if exists(self.defaultDir + self.sel[0]):
				remove(self.defaultDir + self.sel[0])
				self.changelogtype()
			self["list"].changeDir(self.defaultDir)
			self["LogsSize"].update(config.crash.debugPath.value)


class CoreDumpConsole(Console):
	def runFinished(self, retVal):
		if retVal:
			self["text"].appendText("\n" + _("GDB analysis failed (exit code %d). Check the output above.") % retVal + "\n")
		else:
			self["text"].appendText("\n" + _("Debug symbols matching the crashed Enigma2 version are needed for a detailed backtrace.") + "\n")
		Console.runFinished(self, retVal)


class LogManagerViewLog(Screen):
	def __init__(self, session, selected):
		Screen.__init__(self, session)
		self.session = session
		self.setTitle(selected)
		self.logfile = config.crash.debugPath.value + selected
		self.log = []
		self["list"] = MenuList(self.log)
		self["setupActions"] = ActionMap(["ColorActions", "OkCancelActions", "DirectionActions"], {
			"ok": self.gotoFirstPage,
			"cancel": self.cancel,
			"red": self.gotoFirstPage,
			"green": self["list"].pageDown,
			"yellow": self["list"].pageUp,
			"blue": self.gotoLastPage,
			"up": self["list"].up,
			"down": self["list"].down,
			"right": self["list"].pageDown,
			"left": self["list"].pageUp
		}, -2)
		self["key_red"] = StaticText(_("First page"))
		self["key_green"] = StaticText(_("Page forward"))
		self["key_yellow"] = StaticText(_("Page back"))
		self["key_blue"] = StaticText(_("Last page"))
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		font = gFont("Console", 23)
		if not int(fontRenderClass.getInstance().getLineHeight(font)):
			font = gFont("Regular")
		self["list"].instance.setFont(font)
		fontwidth = getTextBoundarySize(self.instance, font, self["list"].instance.size(), " ").width()
		listwidth = int(self["list"].instance.size().width() / fontwidth) - 2
		if exists(self.logfile):
			try:
				for line in open(self.logfile).readlines():
					line = line.replace("\t", " " * 9)
					if len(line) > listwidth:
						pos = 0
						offset = 0
						readyline = True
						while readyline:
							a = " " * offset + line[pos:pos + listwidth - offset]
							self.log.append(a)
							if len(line[pos + listwidth - offset:]):
								pos += listwidth - offset
								offset = 19
							else:
								readyline = False
					else:
						self.log.append(line)
			except UnicodeDecodeError:
				for line in open(self.logfile, encoding="ISO 8859-1").readlines():
					line = line.replace("\t", " " * 9)
					if len(line) > listwidth:
						pos = 0
						offset = 0
						readyline = True
						while readyline:
							a = " " * offset + line[pos:pos + listwidth - offset]
							self.log.append(a)
							if len(line[pos + listwidth - offset:]):
								pos += listwidth - offset
								offset = 19
							else:
								readyline = False
					else:
						self.log.append(line)
		else:
			self.log = [_("File can not displayed - File not found")]
		self["list"].setList(self.log)

	def gotoFirstPage(self):
		self["list"].moveToIndex(0)

	def gotoLastPage(self):
		self["list"].moveToIndex(len(self.log) - 1)

	def cancel(self):
		self.close()


class LogInfo(VariableText, GUIComponent):
	FREE = 0
	USED = 1
	SIZE = 2

	def __init__(self, path, type, update=True):
		GUIComponent.__init__(self)
		VariableText.__init__(self)
		self.logs = listdir(path)
		self.type = type
# 		self.path = config.crash.debugPath.value
		if update:
			self.update(path)

	def update(self, path):
		try:
			total_size = get_size(path)
		except OSError:
			return -1

		if self.type == self.USED:
			try:
				if total_size < 10000000:
					total_size = "%d kB" % (total_size >> 10)
				elif total_size < 10000000000:
					total_size = "%d MB" % (total_size >> 20)
				else:
					total_size = "%d GB" % (total_size >> 30)
				if self.logs and get_size(path) > 0:
					self.setText(_("Exist are debug files.\nSpace used:") + " " + total_size) if not glob(config.crash.debugPath.value + '*crash*') else self.setText(_("Space used:") + " " + total_size)
				else:
					self.setText(_("Exist are no debug files or crash."))
			except:
				# occurs when f_blocks is 0 or a similar error
				self.setText("-?-")

	GUI_WIDGET = eLabel
