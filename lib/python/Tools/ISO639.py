import enigma
import pickle

with open(enigma.eEnv.resolve("${datadir}/enigma2/iso-639-3.pck"), 'rb') as f:
	LanguageCodes = pickle.load(f, encoding="bytes")
