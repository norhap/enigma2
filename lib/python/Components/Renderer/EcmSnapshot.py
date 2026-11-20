from time import monotonic
from weakref import WeakSet

from twisted.internet.threads import deferToThread

from Tools.Directories import fileReadLines


class EcmSnapshot:
	def __init__(self):
		self._listeners = WeakSet()
		self._snapshot = None
		self._processes = None
		self._process_time = 0
		self._next_refresh = 0
		self._pending = False

	def get(self, listener):
		self._listeners.add(listener)
		now = monotonic()
		if not self._pending and now >= self._next_refresh:
			self._pending = True
			refresh_processes = self._processes is None or now - self._process_time >= 5
			deferred = deferToThread(self._read, refresh_processes)
			deferred.addCallbacks(self._ready, self._failed)
		return self._snapshot

	def _read(self, refresh_processes):
		processes = None
		if refresh_processes:
			from process import ProcessList
			process_list = ProcessList()
			processes = (
				bool(str(process_list.named("mgcamd_1.38")).strip("[]")),
				bool(str(process_list.named("CCcam")).strip("[]")),
				bool(str(process_list.named("ncam")).strip("[]")))
		lines = fileReadLines("/tmp/ecm.info", [], source="EcmSnapshot")
		return processes, lines

	def _ready(self, result):
		processes, lines = result
		now = monotonic()
		if processes is not None:
			self._processes = processes
			self._process_time = now
		self._snapshot = self._processes, lines
		self._next_refresh = now + 1
		self._pending = False
		for listener in tuple(self._listeners):
			if getattr(listener, "instance", None) and getattr(listener, "source", None) and not listener.suspended:
				listener.changed((listener.CHANGED_POLL,))

	def _failed(self, failure):
		self._pending = False
		self._next_refresh = monotonic() + 1
		print("[EcmSnapshot] Unable to refresh ECM data: %s" % failure.type.__name__)


ecmSnapshot = EcmSnapshot()
