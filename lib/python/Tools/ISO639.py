from sys import version_info
if version_info.major >= 3:
	import pickle
else:
	import cPickle as pickle
import enigma

with open(enigma.eEnv.resolve("${datadir}/enigma2/iso-639-3.pck"), 'rb') as f:
	if version_info.major >= 3:
		LanguageCodes = pickle.load(f, encoding="bytes")
	else:
		LanguageCodes = pickle.load(f)
