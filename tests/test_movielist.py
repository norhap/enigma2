import importlib.util
import posixpath
import struct
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class ServiceReference:
	mustDescent = 1
	flagDirectory = 1
	idUser = 100

	def __init__(self, path, flags=0):
		self.path = path.split(":", 10)[-1]
		self.flags = flags
		self.type = 0

	def getPath(self):
		return self.path

	def valid(self):
		return bool(self.path)


class ServiceInfo:
	def __init__(self, name, begin=0, description="", length=0):
		self.name = name
		self.begin = begin
		self.description = description
		self.length = length

	def getName(self, ref):
		return self.name

	def getInfo(self, ref, what):
		return self.begin

	def getInfoString(self, ref, what):
		return self.description if what == 2 else ""

	def getLength(self, ref):
		return self.length


def loadMovieList():
	def module(name, **attributes):
		result = types.ModuleType(name)
		result.__dict__.update(attributes)
		return result

	enigma = module("enigma", eServiceReference=ServiceReference,
		iServiceInformation=types.SimpleNamespace(sTimeCreate=1, sDescription=2, sTags=3))
	for name in ("eListboxPythonMultiContent", "eListbox", "gFont", "eSize", "loadPNG", "RT_HALIGN_LEFT", "RT_HALIGN_RIGHT", "RT_VALIGN_CENTER", "BT_SCALE", "BT_KEEP_ASPECT_RATIO", "BT_HALIGN_CENTER", "BT_VALIGN_CENTER", "eServiceCenter", "eTimer", "getDesktop"):
		setattr(enigma, name, None)
	modules = {
		"enigma": enigma,
		"Components.GUIComponent": module("Components.GUIComponent", GUIComponent=object),
		"Tools.FuzzyDate": module("Tools.FuzzyDate", FuzzyTime=None),
		"Components.MultiContent": module("Components.MultiContent", MultiContentEntryText=None, MultiContentEntryPixmapAlphaTest=None, MultiContentEntryProgress=None),
		"Components.config": module("Components.config", config=None),
		"Components.Renderer.Picon": module("Components.Renderer.Picon", getPiconName=None),
		"Tools.LoadPixmap": module("Tools.LoadPixmap", LoadPixmap=None),
		"Tools.Directories": module("Tools.Directories", SCOPE_GUISKIN=None, resolveFilename=None),
		"Screens.LocationBox": module("Screens.LocationBox", defaultInhibitDirs=["/bin"]),
		"Tools.Trashcan": module("Tools.Trashcan", getTrashFolder=None),
		"NavigationInstance": module("NavigationInstance"),
		"skin": module("skin"),
	}
	path = Path(__file__).resolve().parents[1] / "lib" / "python" / "Components" / "MovieList.py"
	spec = importlib.util.spec_from_file_location("movielist_under_test", path)
	result = importlib.util.module_from_spec(spec)
	with patch.dict(sys.modules, modules):
		spec.loader.exec_module(result)
	result.os = types.SimpleNamespace(path=posixpath)
	return result


class MovieListTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.module = loadMovieList()

	def makeList(self, entries, sort_type, root="/movie/sub", temp_sort=None):
		module = self.module
		value = lambda x: types.SimpleNamespace(value=x)
		module.config = types.SimpleNamespace(
			movielist=types.SimpleNamespace(root=value("/movie")),
			usage=types.SimpleNamespace(movielist_trashcan=value(False)),
			ParentalControl=types.SimpleNamespace(servicepinactive=value(False)),
		)
		infos = {ref: info for ref, info in entries}

		class ServiceList:
			def __init__(self):
				self.refs = iter(infos)

			def getNext(self):
				return next(self.refs, ServiceReference(""))

		handler = types.SimpleNamespace(list=lambda root: ServiceList(), info=lambda ref: infos[ref])
		module.eServiceCenter = types.SimpleNamespace(getInstance=lambda: handler)
		result = module.MovieList.__new__(module.MovieList)
		result.list = []
		result.root = None
		result.sort_type = sort_type
		if temp_sort is not None:
			result.temp_sort = temp_sort
		result.load(ServiceReference(root), None)
		return result

	def test_directory_names_and_parent_in_all_alphabetic_modes(self):
		m = self.module.MovieList
		entries = [
			(ServiceReference("/movie/sub/A!/", 1), ServiceInfo("/movie/sub/A!/", 2)),
			(ServiceReference("/movie/sub/A/", 1), ServiceInfo("/movie/sub/A/", 1)),
			(ServiceReference("/movie/sub/.Trash/", 1), ServiceInfo("/movie/sub/.Trash/", 3)),
			(ServiceReference("/movie/sub/Film.ts"), ServiceInfo("Film", 4)),
		]
		for mode, expected in (
			(m.SORT_ALPHANUMERIC, ["A", "A!"]),
			(m.SORT_ALPHA_DATE_OLDEST_FIRST, ["A", "A!"]),
			(m.SORT_ALPHANUMERIC_REVERSE, ["A!", "A"]),
			(m.SORT_ALPHAREV_DATE_NEWEST_FIRST, ["A!", "A"]),
			(m.SORT_ALPHANUMERIC_FLAT, ["A", "A!"]),
			(m.SORT_ALPHANUMERIC_FLAT_REVERSE, ["A!", "A"]),
		):
			with self.subTest(mode=mode):
				result = self.makeList(entries, mode)
				self.assertIsNone(result.list[0][1])
				self.assertEqual(result.list[1][1].name, "/movie/sub/.Trash/")
				dirs = [posixpath.basename(posixpath.normpath(x[1].name)) for x in result.list if x[1] and x[1].name.endswith("/") and ".Trash" not in x[1].name]
				self.assertEqual(dirs, expected)

	def test_description_sort_and_temporary_override(self):
		m = self.module.MovieList
		entries = [
			(ServiceReference("/movie/sub/A.ts"), ServiceInfo("A", 100, "Zebra", 30)),
			(ServiceReference("/movie/sub/B.ts"), ServiceInfo("B", 50, "Alpha", 90)),
			(ServiceReference("/movie/sub/Dir/", 1), ServiceInfo("/movie/sub/Dir/", 1)),
		]
		for mode, temp in ((m.SORT_DESCRIPTION_ALPHA, None), (m.SORT_RECORDED, m.SORT_DESCRIPTION_ALPHA)):
			result = self.makeList(entries, mode, temp_sort=temp)
			self.assertIsNone(result.list[0][1])
			self.assertEqual([x[1].name for x in result.list[1:]], ["/movie/sub/Dir/", "B", "A"])
		result = self.makeList(entries, m.SORT_DESCRIPTION_ALPHA, temp_sort=m.SORT_DURATIONREV_ALPHA)
		self.assertEqual([x[1].name for x in result.list[2:]], ["B", "A"])

	def test_split_recordings_and_no_parent(self):
		m = self.module.MovieList
		entries = [
			(ServiceReference("/movie/film_002.ts"), ServiceInfo("Film", 2)),
			(ServiceReference("/movie/film_001.ts"), ServiceInfo("Film", 1)),
			(ServiceReference("/movie/A/", 1), ServiceInfo("/movie/A/", 3)),
		]
		result = self.makeList(entries, m.SORT_ALPHANUMERIC, root="/movie")
		self.assertEqual([x[0].getPath() for x in result.list], ["/movie/A/", "/movie/film_001.ts", "/movie/film_002.ts"])

	def test_play_state_reads_cuts_and_prefers_cache(self):
		module = self.module
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "film.cuts"
			path.write_bytes(struct.pack(">QI", 90000, 1) + struct.pack(">QI", 4500000, 3))
			with patch.object(module, "lastPlayPosFromCache", return_value=None):
				self.assertEqual(module.moviePlayState(str(path), object(), 100), 50)
				self.assertEqual(module.moviePlayState(str(path), object(), 0), 50)
			with patch.object(module, "lastPlayPosFromCache", return_value=(None, 1800000, 9000000)):
				self.assertEqual(module.moviePlayState(str(path), object(), 100), 20)
				self.assertEqual(module.moviePlayState(str(path) + ".missing", object(), 100), 20)
			with patch.object(module, "lastPlayPosFromCache", return_value=(None, 1800000, 0)):
				self.assertEqual(module.moviePlayState(str(path), object(), 100), 20)
				self.assertEqual(module.moviePlayState(str(path) + ".missing", object(), 100), 20)
				self.assertEqual(module.moviePlayState(str(path), object(), 0), 50)
			path.write_bytes(struct.pack(">QI", 90000, 1))
			with patch.object(module, "lastPlayPosFromCache", return_value=None):
				self.assertIsNone(module.moviePlayState(str(path), object(), 100))


if __name__ == "__main__":
	unittest.main()
