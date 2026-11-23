import os
import shutil
import struct
import tempfile

from Components.Task import Job, PythonTask, job_manager
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Tools.Notifications import AddNotification
from enigma import eServiceCenter, eServiceReference


class PrepareStreamTask(PythonTask):
	def __init__(self, job, source, directory, target, offline):
		PythonTask.__init__(self, job, _("Preparing the recording for cutting"))
		self.source = source
		self.directory = directory
		self.target = target
		self.offline = offline

	def work(self):
		created = [self.target, self.target + ".ap", self.target + ".sc", self.target + ".meta", os.path.splitext(self.target)[0] + ".eit"]
		try:
			with open(self.source, "rb") as source:
				initial = os.fstat(source.fileno())
				header = source.read(188 * 5)
				if len(header) < 188 * 5 or any(header[offset] != 0x47 for offset in range(0, 188 * 5, 188)):
					raise ValueError(_("This recording is not a supported MPEG transport stream."))
				source.seek(0)
				with open(self.target, "xb") as target:
					while True:
						if self.aborted:
							raise InterruptedError(_("Preparation was cancelled."))
						data = source.read(1024 * 1024)
						if not data:
							break
						target.write(data)
						if initial.st_size:
							self.pos = min(90, target.tell() * 90 // initial.st_size)
				final = os.fstat(source.fileno())
				current = os.stat(self.source)
				if (initial.st_size, initial.st_mtime_ns, initial.st_ino, initial.st_dev) != (final.st_size, final.st_mtime_ns, final.st_ino, final.st_dev) or (final.st_size, final.st_mtime_ns, final.st_ino, final.st_dev) != (current.st_size, current.st_mtime_ns, current.st_ino, current.st_dev):
					raise ValueError(_("The source recording changed during copying. Stop the recording and try again."))
			for src, dst in ((self.source + ".meta", self.target + ".meta"), (os.path.splitext(self.source)[0] + ".eit", os.path.splitext(self.target)[0] + ".eit")):
				try:
					with open(src, "rb") as source, open(dst, "xb") as target:
						shutil.copyfileobj(source, target)
				except FileNotFoundError:
					if os.path.exists(src):
						raise
			if self.aborted:
				raise InterruptedError(_("Preparation was cancelled."))
			if self.offline.reindex() != 0:
				raise ValueError(_("The transport stream could not be indexed."))
			if self.aborted:
				raise InterruptedError(_("Preparation was cancelled."))
			try:
				with open(self.target + ".ap", "rb") as index:
					first = index.read(32)
			except FileNotFoundError:
				raise ValueError(_("The recording does not have enough access points for MovieCut."))
			if len(first) != 32:
				raise ValueError(_("The recording does not have enough access points for MovieCut."))
			offset1, offset2 = struct.unpack(">q8xq8x", first)
			if not 0 <= offset1 < offset2 < initial.st_size or not os.path.isfile(self.target + ".sc"):
				raise ValueError(_("The recording has an invalid access-point index."))
			self.pos = 100
		except Exception:
			for filename in created:
				try:
					os.unlink(filename)
				except FileNotFoundError:
					pass
				except OSError as error:
					print("[CutListEditor] Cannot remove temporary file %s: %s" % (filename, error))
			try:
				os.rmdir(self.directory)
			except OSError as error:
				print("[CutListEditor] Cannot remove temporary directory %s: %s" % (self.directory, error))
			raise


def prepareStream(session, service, confirmed):
	if not confirmed:
		return
	source = service.getPath()
	directory = None
	try:
		directory = tempfile.mkdtemp(prefix="CutList-", dir=os.path.dirname(source))
		target = os.path.join(directory, os.path.basename(source)[:-7] + ".ts")
		ref = eServiceReference(eServiceReference.idDVB, 0, target)
		offline = eServiceCenter.getInstance().offlineOperations(ref)
		if offline is None:
			raise ValueError(_("Cannot index the copied recording."))
		job = Job(_("Preparing the recording for cutting"))
		PrepareStreamTask(job, source, directory, target, offline)
	except (OSError, ValueError) as error:
		if directory:
			try:
				os.rmdir(directory)
			except OSError as cleanup_error:
				print("[CutListEditor] Cannot remove temporary directory %s: %s" % (directory, cleanup_error))
		session.open(MessageBox, str(error), type=MessageBox.TYPE_ERROR)
		return

	def complete(job):
		AddNotification(MessageBox, _("The copy is ready for cutting:\n%s\n\nOpen this recording in the cutlist editor and create new cut marks. The original was not changed.") % target, type=MessageBox.TYPE_INFO)

	job_manager.AddJob(job, onSuccess=complete)
	session.open(MessageBox, _("The recording is being copied and indexed in the background. This requires free disk space and may take some time."), type=MessageBox.TYPE_INFO, timeout=10)


def CutListEditor(session, service=None):
	from . import ui
	return ui.CutListEditor(session, service)


def main(session, service, **kwargs):
	if service and service.getPath().lower().endswith(".stream"):
		session.openWithCallback(lambda answer: prepareStream(session, service, answer), MessageBox,
			_("Create an editable copy of this recording? Only MPEG transport streams are supported. The original will not be changed. The copy requires disk space and new cut marks."),
			type=MessageBox.TYPE_YESNO, default=False)
		return
	session.open(CutListEditor, service)


def Plugins(**kwargs):
	return PluginDescriptor(name=_("Cutlist editor"), description=_("Cutlist editor..."),
		where=PluginDescriptor.WHERE_MOVIELIST, needsRestart=False, fnc=main)
