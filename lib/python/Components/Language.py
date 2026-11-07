# -*- coding: UTF-8 -*-
import gettext
from locale import LC_CTYPE, LC_COLLATE, LC_TIME, LC_MONETARY, LC_MESSAGES, LC_NUMERIC, setlocale
from os import listdir, environ, system
from Tools.Directories import SCOPE_LANGUAGE, resolveFilename

DATADIR_PO = resolveFilename(SCOPE_LANGUAGE)
packageprefix = "enigma2-locale-"
_ = gettext.gettext


class Language:
	LANG_NAME = 0
	LANG_MAX = 6

	LANGUAGE_DATA = {
		"aa": ("Afar", _("Afar"), "Afaraf", "", "", ("DJ", "ER", "ET")),
		"ab": ("Abkhazian", _("Abkhazian"), "Аҧсуа Бызшәа / Аҧсшәа", "", "", ()),
		"ae": ("Avestan", _("Avestan"), "Avesta", "", "", ()),
		"af": ("Afrikaans", _("Afrikaans"), "Afrikaans", "", "", ("ZA",)),
		"ak": ("Akan", _("Akan"), "Akan", "", "", ("GH",)),
		"am": ("Amharic", _("Amharic"), "አማርኛ", "", "", ("ET",)),
		"an": ("Aragonese", _("Aragonese"), "Aragonés", "", "", ("ES",)),
		"ar": ("Arabic", _("Arabic"), "العربية", "", "", ("EG", "AE", "BH", "DJ", "DZ", "EH", "ER", "IL", "IQ", "JO", "KM", "KW", "LB", "LY", "MA", "MR", "OM", "PS", "QA", "SA", "SD", "SO", "SS", "SY", "TD", "TN", "YE")),
		"as": ("Assamese", _("Assamese"), "অসমীয়া", "", "", ("IN",)),
		"av": ("Avaric", _("Avaric"), "Авар мацӀ / МагӀарул мацӀ", "", "", ()),
		"ay": ("Aymara", _("Aymara"), "Aymar Aru", "", "", ("PE",)),
		"az": ("Azerbaijani", _("Azerbaijani"), "Azərbaycan Dili", "", "", ("AZ", "IR")),
		"ba": ("Bashkir", _("Bashkir"), "башҡорт теле", "", "", ()),
		"be": ("Belarusian", _("Belarusian"), "беларуская мова", "", "", ("BY",)),
		"bg": ("Bulgarian", _("Bulgarian"), "български език", "", "", ("BG",)),
		"bh": ("Bihari languages", _("Bihari languages"), "भोजपुरी", "", "", ()),
		"bi": ("Bislama", _("Bislama"), "Bislama", "", "", ("TV", "VU")),
		"bm": ("Bambara", _("Bambara"), "Bamanankan", "", "", ("ML",)),
		"bn": ("Bengali", _("Bengali"), "বাংলা", "", "", ("BD", "IN")),
		"bo": ("Tibetan", _("Tibetan"), "བོད་ཡིག", "", "", ("CN", "IN")),
		"br": ("Breton", _("Breton"), "Brezhoneg", "", "", ("FR",)),
		"bs": ("Bosnian", _("Bosnian"), "Bosanski Jezik", "", "", ("BA",)),
		"ca": ("Catalan / Valencian", _("Catalan / Valencian"), "Català / Valencià", "", "", ("AD", "ES", "FR", "IT")),
		"ce": ("Chechen", _("Chechen"), "Нохчийн Мотт", "", "", ("RU",)),
		"ch": ("Chamorro", _("Chamorro"), "Chamoru", "", "", ()),
		"co": ("Corsican", _("Corsican"), "Corsu, Lingua Corsa", "", "", ()),
		"cr": ("Cree", _("Cree"), "ᓀᐦᐃᔭᐍᐏᐣ", "", "", ()),
		"cs": ("Czech", _("Czech"), "Čeština / Český Jazyk", "", "qwertz", ("CZ",)),
		"cu": ("Church Slavic", _("Church Slavic"), "Ѩзыкъ Словѣньскъ", "", "", ()),
		"cv": ("Chuvash", _("Chuvash"), "Чӑваш Чӗлхи", "", "", ("RU",)),
		"cy": ("Welsh", _("Welsh"), "Cymraeg", "", "", ("GB",)),
		"da": ("Danish", _("Danish"), "Dansk", "", "", ("DK",)),
		"de": ("German", _("German"), "Deutsch", "", "qwertz", ("DE", "AT", "BE", "CH", "IT", "LI", "LU")),
		"dv": ("Divehi / Dhivehi / Maldivian", _("Divehi / Dhivehi / Maldivian"), "ދިވެހި", "", "", ("MV",)),
		"dz": ("Dzongkha", _("Dzongkha"), "རྫོང་ཁ", "", "", ("BT",)),
		"ee": ("Ewe", _("Ewe"), "Eʋegbe", "", "", ()),
		"el": ("Greek", _("Greek"), "Ελληνικά", "", "", ("GR", "CY")),
		"en": ("English", _("English"), "English", "", "", ("US", "AG", "AU", "BW", "BZ", "CA", "DK", "GB", "HK", "IE", "IL", "IN", "JM", "KH", "NG", "NZ", "PH", "SC", "SG", "TT", "ZA", "ZM", "ZW")),
		"eo": ("Esperanto", _("Esperanto"), "Esperanto", "", "", ()),
		"es": ("Spanish / Castilian", _("Spanish / Castilian"), "Español", "", "", ("ES", "AR", "BO", "CL", "CO", "CR", "CU", "DO", "EC", "GT", "HN", "MX", "NI", "PA", "PE", "PR", "PY", "SV", "US", "UY", "VE")),
		"et": ("Estonian", _("Estonian"), "Eesti / Eesti keel", "", "", ("EE",)),
		"eu": ("Basque", _("Basque"), "Euskara / Euskera", "", "", ("ES",)),
		"fa": ("Farsi / Persian", _("Farsi / Persian"), "فارسی", "", "", ("IR",)),
		"ff": ("Fulah", _("Fulah"), "Fulfulde / Pulaar / Pular", "", "", ("SN",)),
		"fi": ("Finnish", _("Finnish"), "Suomi / Suomen kieli", "", "", ("FI",)),
		"fj": ("Fijian", _("Fijian"), "Vosa Vakaviti", "", "", ()),
		"fo": ("Faroese", _("Faroese"), "Føroyskt", "", "", ("FO",)),
		"fr": ("French", _("French"), "Français", "", "azerty", ("FR", "AG", "AI", "BE", "BB", "BS", "CA", "CG", "CH", "CI", "CM", "CU", "DO", "DM", "GD", "GY", "HT", "JM", "KN", "LC", "LU", "MA", "MC", "ML", "MQ", "PR", "SN", "SR", "SX", "TT", "VC", "VI")),
		"fy": ("Western Frisian", _("Western Frisian"), "Frysk", "", "", ("NL", "DE")),
		"ga": ("Irish", _("Irish"), "Gaeilge", "", "", ("IE",)),
		"gd": ("Gaelic", _("Gaelic"), "Gàidhlig", "", "", ("GB",)),
		"gl": ("Galician", _("Galician"), "Galego", "", "", ("ES",)),
		"gn": ("Guarani", _("Guarani"), "Avañe'ẽ", "", "", ("PY",)),
		"gu": ("Gujarati", _("Gujarati"), "ગુજરાતી", "", "", ("IN",)),
		"gv": ("Manx", _("Manx"), "Gaelg / Gailck", "", "", ("GB",)),
		"ha": ("Hausa", _("Hausa"), "هَوُسَ", "", "", ("NG",)),
		"he": ("Hebrew", _("Hebrew"), "עברית‎", "", "", ("IL",)),
		"hi": ("Hindi", _("Hindi"), "हिन्दी / हिंदी", "", "", ("IN",)),
		"ho": ("Hiri Motu", _("Hiri Motu"), "Hiri Motu", "", "", ()),
		"hr": ("Croatian", _("Croatian"), "Hrvatski Jezik", "", "", ("HR",)),
		"ht": ("Haitian / Haitian Creole", _("Haitian / Haitian Creole"), "Kreyòl ayisyen", "", "", ("HT",)),
		"hu": ("Hungarian", _("Hungarian"), "Magyar", "", "qwertz", ("HU",)),
		"hy": ("Armenian", _("Armenian"), "Հայերեն", "", "", ("AM",)),
		"hz": ("Herero", _("Herero"), "Otjiherero", "", "", ()),
		"ia": ("Interlingua", _("Interlingua"), "Interlingua", "", "", ("FR",)),
		"id": ("Indonesian", _("Indonesian"), "Bahasa Indonesia", "", "", ("ID",)),
		"ie": ("Interlingue / Occidental", _("Interlingue / Occidental"), "Interlingue", "", "", ()),
		"ig": ("Igbo", _("Igbo"), "Asụsụ Igbo", "", "", ("NG",)),
		"ii": ("Sichuan Yi / Nuosu", _("Sichuan Yi / Nuosu"), "ꆈꌠ꒿ Nuosuhxop", "", "", ()),
		"ik": ("Inupiaq", _("Inupiaq"), "Iñupiaq / Iñupiatun", "", "", ("CA",)),
		"io": ("Ido", _("Ido"), "Ido", "", "", ()),
		"is": ("Icelandic", _("Icelandic"), "Íslenska", "", "", ("IS",)),
		"it": ("Italian", _("Italian"), "Italiano", "", "", ("IT", "CH")),
		"iu": ("Inuktitut", _("Inuktitut"), "ᐃᓄᒃᑎᑐᑦ", "", "", ("CA",)),
		"ja": ("Japanese", _("Japanese"), "日本語 (にほんご)", "", "", ("JP",)),
		"jv": ("Javanese", _("Javanese"), "ꦧꦱꦗꦮ / Basa Jawa", "", "", ()),
		"ka": ("Georgian", _("Georgian"), "ქართული", "", "", ("GE",)),
		"kg": ("Kongo", _("Kongo"), "Kikongo", "", "", ()),
		"ki": ("Kikuyu / Gikuyu", _("Kikuyu / Gikuyu"), "Gĩkũyũ", "", "", ()),
		"kj": ("Kuanyama / Kwanyama", _("Kuanyama / Kwanyama"), "Kuanyama", "", "", ()),
		"kk": ("Kazakh", _("Kazakh"), "Қазақ тілі", "", "", ("KZ",)),
		"kl": ("Kalaallisut / Greenlandic", _("Kalaallisut / Greenlandic"), "Kalaallisut / Kalaallit oqaasii", "", "", ("GL",)),
		"km": ("Central Khmer", _("Central Khmer"), "ខ្មែរ, ខេមរភាសា, ភាសាខ្មែរ", "", "", ("KH",)),
		"kn": ("Kannada", _("Kannada"), "ಕನ್ನಡ", "", "", ("IN",)),
		"ko": ("Korean", _("Korean"), "한국어", "", "", ("KR",)),
		"kr": ("Kanuri", _("Kanuri"), "Kanuri", "", "", ()),
		"ks": ("Kashmiri", _("Kashmiri"), "कश्मीरी / كشميري", "", "", ("IN",)),
		"ku": ("Kurdish", _("Kurdish"), "Kurdî / کوردی", "", "", ("TR", "IQ", "IR", "SY")),
		"kv": ("Komi", _("Komi"), "Коми кыв", "", "", ()),
		"kw": ("Cornish", _("Cornish"), "Kernewek", "", "", ("GB",)),
		"ky": ("Kirghiz / Kyrgyz", _("Kirghiz / Kyrgyz"), "Кыргызча, Кыргыз тили", "", "", ("KG",)),
		"la": ("Latin", _("Latin"), "Latine / Lingua Latina", "", "", ()),
		"lb": ("Luxembourgish / Letzeburgesch", _("Luxembourgish / Letzeburgesch"), "Lëtzebuergesch", "", "", ("LU",)),
		"lg": ("Ganda", _("Ganda"), "Luganda", "", "", ("UG",)),
		"li": ("Limburgan / Limburger / Limburgish", _("Limburgan / Limburger / Limburgish"), "Limburgs", "", "", ("BE", "NL")),
		"ln": ("Lingala", _("Lingala"), "Lingála", "", "", ("CD",)),
		"lo": ("Lao", _("Lao"), "ພາສາລາວ", "", "", ("LA",)),
		"lt": ("Lithuanian", _("Lithuanian"), "Lietuvių Kalba", "", "", ("LT",)),
		"lu": ("Luba-Katanga", _("Luba-Katanga"), "Kiluba", "", "", ()),
		"lv": ("Latvian", _("Latvian"), "Latviešu Valoda", "", "", ("LV",)),
		"mg": ("Malagasy", _("Malagasy"), "Fiteny Malagasy", "", "", ("MG",)),
		"mh": ("Marshallese", _("Marshallese"), "Kajin M̧ajeļ", "", "", ("MH",)),
		"mi": ("Maori", _("Maori"), "te reo Māori", "", "", ("NZ",)),
		"mk": ("Macedonian", _("Macedonian"), "Македонски Јазик", "", "", ("MK",)),
		"ml": ("Malayalam", _("Malayalam"), "മലയാളം", "", "", ("IN",)),
		"mn": ("Mongolian", _("Mongolian"), "Монгол хэл", "", "", ("MN",)),
		"mr": ("Marathi", _("Marathi"), "मराठी", "", "", ("IN",)),
		"ms": ("Malay", _("Malay"), "Bahasa Melayu, بهاس ملايو", "", "", ("MY",)),
		"mt": ("Maltese", _("Maltese"), "Malti", "", "", ("MT",)),
		"my": ("Burmese", _("Burmese"), "ဗမာစာ", "", "", ("MM",)),
		"na": ("Nauru", _("Nauru"), "Dorerin Naoero", "", "", ()),
		"nb": ("Norwegian Bokmål", _("Norwegian Bokmål"), "Norsk Bokmål", "", "", ("NO",)),
		"nd": ("North Ndebele", _("North Ndebele"), "isiNdebele", "", "", ()),
		"ne": ("Nepali", _("Nepali"), "नेपाली", "", "", ("NP",)),
		"ng": ("Ndonga", _("Ndonga"), "Owambo", "", "", ()),
		"nl": ("Dutch / Flemish", _("Dutch / Flemish"), "Nederlands / Vlaams", "", "", ("NL", "AW", "BE")),
		"nn": ("Norwegian Nynorsk", _("Norwegian Nynorsk"), "Norsk Nynorsk", "", "", ("NO",)),
		"no": ("Norwegian", _("Norwegian"), "Norsk", "", "", ("NO",)),
		"nr": ("South Ndebele", _("South Ndebele"), "isiNdebele", "", "", ("ZA",)),
		"nv": ("Navajo / Navaho", _("Navajo / Navaho"), "Diné bizaad", "", "", ()),
		"ny": ("Chichewa / Chewa / Nyanja", _("Chichewa / Chewa / Nyanja"), "ChiCheŵa / Chinyanja", "", "", ()),
		"oc": ("Occitan", _("Occitan"), "Occitan / Lenga D'òc", "", "", ("FR",)),
		"oj": ("Ojibwa", _("Ojibwa"), "ᐊᓂᔑᓈᐯᒧᐎᓐ", "", "", ()),
		"om": ("Oromo", _("Oromo"), "Afaan Oromoo", "", "", ("ET", "KE")),
		"or": ("Oriya", _("Oriya"), "ଓଡ଼ିଆ", "", "", ("IN",)),
		"os": ("Ossetian / Ossetic", _("Ossetian / Ossetic"), "Ирон Æвзаг", "", "", ("RU",)),
		"pa": ("Panjabi / Punjabi", _("Panjabi / Punjabi"), "ਪੰਜਾਬੀ, پنجابی", "", "", ("IN", "PK")),
		"pi": ("Pali", _("Pali"), "पालि, पाळि", "", "", ()),
		"pl": ("Polish", _("Polish"), "Język Polski, Polszczyzna", "", "qwertz", ("PL",)),
		"ps": ("Pushto / Pashto", _("Pushto / Pashto"), "پښتو", "", "", ("AF",)),
		"pt": ("Portuguese", _("Portuguese"), "Português", "", "", ("PT", "BR")),
		"qu": ("Quechua", _("Quechua"), "Runa Simi, Kichwa", "", "", ()),
		"rm": ("Romansh", _("Romansh"), "Rumantsch Grischun", "", "", ()),
		"rn": ("Rundi", _("Rundi"), "Ikirundi", "", "", ()),
		"ro": ("Romanian", _("Romanian"), "Română", "", "qwertz", ("RO",)),
		"ru": ("Russian", _("Russian"), "Русский", "", "", ("RU", "UA")),
		"rw": ("Kinyarwanda", _("Kinyarwanda"), "Ikinyarwanda", "", "", ("RW",)),
		"sa": ("Sanskrit", _("Sanskrit"), "संस्कृतम्", "", "", ("IN",)),
		"sb": ("Sorbian", _("Sorbian"), "Sorbian", "", "", ()),
		"sc": ("Sardinian", _("Sardinian"), "Sardu", "", "", ("IT",)),
		"sd": ("Sindhi", _("Sindhi"), "सिन्धी, سنڌي، سندھی", "", "", ("IN",)),
		"se": ("Northern Sami", _("Northern Sami"), "Davvisámegiella", "", "", ("NO",)),
		"sg": ("Sango", _("Sango"), "Yângâ tî sängö", "", "", ()),
		"si": ("Sinhala / Sinhalese", _("Sinhala / Sinhalese"), "සිංහල", "", "", ("LK",)),
		"sk": ("Slovak", _("Slovak"), "Slovenčina / Slovenský Jazyk", "", "qwertz", ("SK",)),
		"sl": ("Slovenian", _("Slovenian"), "Slovenski Jezik / Slovenščina", "", "qwertz", ("SI",)),
		"sm": ("Samoan", _("Samoan"), "Gagana Fa'a Samoa", "", "", ("WS",)),
		"sn": ("Shona", _("Shona"), "chiShona", "", "", ()),
		"so": ("Somali", _("Somali"), "Soomaaliga, af Soomaali", "", "", ("DJ", "ET", "KE", "SO")),
		"sq": ("Albanian", _("Albanian"), "Shqip", "", "", ("AL", "KV", "MK")),
		"sr": ("Serbian", _("Serbian"), "Српски Језик", "", "qwertz", ("RS", "ME")),
		"ss": ("Swati", _("Swati"), "SiSwati", "", "", ("ZA",)),
		"st": ("Sotho, Southern", _("Sotho, Southern"), "Sesotho", "", "", ("ZA",)),
		"su": ("Sundanese", _("Sundanese"), "Basa Sunda", "", "", ("ID",)),
		"sv": ("Swedish", _("Swedish"), "Svenska", "", "", ("SE", "FI")),
		"sw": ("Swahili", _("Swahili"), "Kiswahili", "", "", ("KE", "TZ")),
		"ta": ("Tamil", _("Tamil"), "தமிழ்", "", "", ("IN", "LK")),
		"te": ("Telugu", _("Telugu"), "తెలుగు", "", "", ("IN",)),
		"tg": ("Tajik", _("Tajik"), "тоҷикӣ, toçikī, تاجیکی", "", "", ("TJ",)),
		"th": ("Thai", _("Thai"), "ไทย", "", "", ("TH",)),
		"ti": ("Tigrinya", _("Tigrinya"), "ትግርኛ", "", "", ("ER", "ET")),
		"tk": ("Turkmen", _("Turkmen"), "Türkmen, Түркмен", "", "", ("TM",)),
		"tl": ("Tagalog", _("Tagalog"), "Wikang Tagalog", "", "", ("PH",)),
		"tn": ("Tswana", _("Tswana"), "Setswana", "", "", ("ZA",)),
		"to": ("Tonga", _("Tonga"), "Faka Tonga", "", "", ("TO",)),
		"tr": ("Turkish", _("Turkish"), "Türkçe", "", "", ("TR", "CY")),
		"ts": ("Tsonga", _("Tsonga"), "Xitsonga", "", "", ("ZA",)),
		"tt": ("Tatar", _("Tatar"), "Татар теле, Tatar tele", "", "", ("RU",)),
		"tw": ("Twi", _("Twi"), "Twi", "", "", ()),
		"ty": ("Tahitian", _("Tahitian"), "Reo Tahiti", "", "", ()),
		"ug": ("Uighur / Uyghur", _("Uighur / Uyghur"), "ئۇيغۇرچە‎ / Uyghurche", "", "", ("CN",)),
		"uk": ("Ukrainian", _("Ukrainian"), "Українська", "", "", ("UA",)),
		"ur": ("Urdu", _("Urdu"), "اردو", "", "", ("IN", "PK")),
		"uz": ("Uzbek", _("Uzbek"), "Oʻzbek, Ўзбек, أۇزبېك", "", "", ("UZ",)),
		"ve": ("Venda", _("Venda"), "Tshivenḓa", "", "", ("ZA",)),
		"vi": ("Vietnamese", _("Vietnamese"), "Tiếng Việt", "", "", ("VN",)),
		"vo": ("Volapük", _("Volapük"), "Volapük", "", "", ()),
		"wa": ("Walloon", _("Walloon"), "Walon", "", "", ("BE",)),
		"wo": ("Wolof", _("Wolof"), "Wollof", "", "", ("SN",)),
		"xh": ("Xhosa", _("Xhosa"), "isiXhosa", "", "", ("ZA",)),
		"yi": ("Yiddish", _("Yiddish"), "ייִדיש", "", "", ("US",)),
		"yo": ("Yoruba", _("Yoruba"), "Yorùbá", "", "", ("NG",)),
		"za": ("Zhuang / Chuang", _("Zhuang / Chuang"), "Saɯ cueŋƅ / Saw cuengh", "", "", ()),
		"zh": ("Chinese", _("Chinese"), "中文", "", "", ("CN", "HK", "MO", "SG", "TW")),
		"zu": ("Zulu", _("Zulu"), "isiZulu", "", "", ("ZA",)),
	}

	def __init__(self):
		gettext.install('enigma2', resolveFilename(SCOPE_LANGUAGE))
		gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
		gettext.textdomain("enigma2")
		self.activeLanguage = 0
		self.catalog = None
		self.lang = {}
		self.InitLang()
		self.callbacks = []

	def InitLang(self):
		self.langlist = []
		self.langlistselection = []
		self.languageDirectory = listdir(DATADIR_PO)
		# FIXME make list dynamically
		# name, iso-639 language, iso-3166 country. Please don't mix language&country!
		self.addLanguage("Arabic", "ar", "AE", "ISO-8859-15")
		self.addLanguage("Български", "bg", "BG", "ISO-8859-15")
		self.addLanguage("Bokmål", "nb", "NO", "ISO-8859-15")
		self.addLanguage("Català", "ca", "AD", "ISO-8859-15")
		self.addLanguage("Česky", "cs", "CZ", "ISO-8859-15")
		self.addLanguage("SChinese", "zh", "CN", "UTF-8")
		self.addLanguage("TChinese", "zh", "HK", "UTF-8")
		self.addLanguage("Dansk", "da", "DK", "ISO-8859-15")
		self.addLanguage("Deutsch", "de", "DE", "ISO-8859-15")
		self.addLanguage("Ελληνικά", "el", "GR", "ISO-8859-7")
		self.addLanguage("English (AU)", "en", "AU", "ISO-8859-1")
		self.addLanguage("English (UK)", "en", "GB", "ISO-8859-15")
		self.addLanguage("English (US)", "en", "US", "ISO-8859-15")
		self.addLanguage("Español", "es", "ES", "ISO-8859-15")
		self.addLanguage("Eesti", "et", "EE", "ISO-8859-15")
		self.addLanguage("Persian", "fa", "IR", "ISO-8859-15")
		self.addLanguage("Suomi", "fi", "FI", "ISO-8859-15")
		self.addLanguage("Français", "fr", "FR", "ISO-8859-15")
		self.addLanguage("Frysk", "fy", "NL", "ISO-8859-15")
		self.addLanguage("Hebrew", "he", "IL", "ISO-8859-15")
		self.addLanguage("Hrvatski", "hr", "HR", "ISO-8859-15")
		self.addLanguage("Magyar", "hu", "HU", "ISO-8859-15")
		self.addLanguage("Indonesian", "id", "ID", "ISO-8859-15")
		self.addLanguage("Íslenska", "is", "IS", "ISO-8859-15")
		self.addLanguage("Italiano", "it", "IT", "ISO-8859-15")
		self.addLanguage("Kurdish", "ku", "KU", "ISO-8859-15")
		self.addLanguage("Lietuvių", "lt", "LT", "ISO-8859-15")
		self.addLanguage("Latviešu", "lv", "LV", "ISO-8859-15")
		self.addLanguage("Nederlands", "nl", "NL", "ISO-8859-15")
		self.addLanguage("Norsk Bokmål", "nb", "NO", "ISO-8859-15")
		self.addLanguage("Norsk", "no", "NO", "ISO-8859-15")
		self.addLanguage("Polski", "pl", "PL", "ISO-8859-15")
		self.addLanguage("Português", "pt", "PT", "ISO-8859-15")
		self.addLanguage("Português do Brasil", "pt", "BR", "ISO-8859-15")
		self.addLanguage("Romanian", "ro", "RO", "ISO-8859-15")
		self.addLanguage("Русский", "ru", "RU", "ISO-8859-15")
		self.addLanguage("Slovensky", "sk", "SK", "ISO-8859-15")
		self.addLanguage("Slovenščina", "sl", "SI", "ISO-8859-15")
		self.addLanguage("Srpski", "sr", "YU", "ISO-8859-15")
		self.addLanguage("Svenska", "sv", "SE", "ISO-8859-15")
		self.addLanguage("ภาษาไทย", "th", "TH", "ISO-8859-15")
		self.addLanguage("Türkçe", "tr", "TR", "ISO-8859-15")
		self.addLanguage("Українська", "uk", "UA", "ISO-8859-15")
		self.addLanguage("Tiếng Việt", "vi", "VN", "UTF-8")

	def addLanguage(self, name, lang, country, encoding):
		try:
			if lang in self.languageDirectory or (lang + "_" + country) in self.languageDirectory:
				self.lang[str(lang + "_" + country)] = ((name, lang, country, encoding))
				self.langlist.append(str(lang + "_" + country))
		except:
			print(f"[Language] Language {str(name)} not found")
		self.langlistselection.append((str(lang + "_" + country), name))

	def activateLanguage_TRY(self, locale):
		if locale not in self.lang:
			print(f"[Language] Selected language {locale} is not installed, fallback to es_ES!")
			locale = "es_ES"
		lang = self.lang[locale]
		print(f"[Language] Activating language {lang[0]}")
		self.catalog = gettext.translation('enigma2', resolveFilename(SCOPE_LANGUAGE), languages=[locale], fallback=True)
		self.catalog.install(names=("ngettext", "pgettext"))
		self.activeLanguage = locale
		# LC_ALL use default (C) locale = getlocale() then don't include it in this for.
		for category in [LC_CTYPE, LC_COLLATE, LC_TIME, LC_MONETARY, LC_MESSAGES, LC_NUMERIC]:
			try:
				setlocale(category, locale)
			except Exception:  # Second resort to unsupported locale setting.
				try:
					if category in [LC_TIME, LC_MESSAGES]:
						setlocale(category, locale)
				except Exception:  # Last resort to unsupported locale setting.
					try:
						setlocale(LC_TIME, locale)
					except Exception:
						pass  # TRY to establish it more times.
		environ["LC_TIME"] = f"{locale}'.UTF-8'"
		environ["LANGUAGE"] = f"{locale}'.UTF-8'"
		environ["LANGUAGE2"] = locale
		environ["GST_SUBTITLE_ENCODING"] = self.getGStreamerSubtitleEncoding()
		return True

	def activateLanguage(self, locale):
		if not self.activateLanguage_TRY(locale):
			print("[Language] - retry with ", "es_ES")
			self.activateLanguage_TRY("es_ES")

	def activateLanguageIndex(self, locale):
		if locale < len(self.langlist):
			self.activateLanguage(self.langlist[locale])

	def getLanguageList(self):
		return [(x, self.lang[x]) for x in self.langlist]

	def getLanguageListSelection(self):
		return self.langlistselection

	def getActiveLanguage(self):
		return self.activeLanguage

	def getActiveCatalog(self):
		return self.catalog

	def getActiveLanguageIndex(self):
		idx = 0
		for x in self.langlist:
			if x == self.activeLanguage:
				return idx
			idx += 1
		return None

	def getLanguage(self):
		return self.lang[self.activeLanguage][1] + "_" + self.lang[self.activeLanguage][2] if self.activeLanguage != 0 else ""

	def getGStreamerSubtitleEncoding(self):
		return self.lang[self.activeLanguage][3] if self.activeLanguage != 0 else 'ISO-8859-15'

	def addCallback(self, callback):
		self.callbacks.append(callback)

	def delLanguage(self, delLang=None):
		from Components.config import config
		if delLang:
			lang = config.osd.language.value
			print(f"[Language] DELETE LANG, {delLang}")
			if delLang[:2] == "es":
				print("[Language] Default Language can not be deleted !!")
				return
			elif delLang == "pt_BR":
				delLang = delLang.lower()
				delLang = delLang.replace('_', '-')
				system("opkg remove --autoremove --force-depends " + packageprefix + delLang)
			else:
				system("opkg remove --autoremove --force-depends " + packageprefix + delLang[:2])
		else:
			lang = self.activeLanguage
			print(f"[Language] Delete all lang except, {lang}")
			for x in self.languageDirectory:
				if len(x) > 2:
					if x != lang and x[:2] != "es":
						x = x.lower()
						x = x.replace('_', '-')
						system("opkg remove --autoremove --force-depends " + packageprefix + x)
				else:
					if x != lang[:2] and x != "es":
						system("opkg remove --autoremove --force-depends " + packageprefix + x)
		system("touch /etc/enigma2/.removelang")
		self.InitLang()


language = Language()
