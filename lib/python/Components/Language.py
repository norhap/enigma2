# -*- coding: UTF-8 -*-
import gettext
import locale
from os import listdir, environ, mkdir, path, system
from time import time, localtime, strftime
from Tools.Directories import SCOPE_LANGUAGE, resolveFilename

LPATH = resolveFilename(SCOPE_LANGUAGE, "")
Lpackagename = "enigma2-locale-"


class Language:
	def __init__(self):
		gettext.install('enigma2', resolveFilename(SCOPE_LANGUAGE, ""))
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
		self.ll = listdir(LPATH)
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
			if lang in self.ll or (lang + "_" + country) in self.ll:
				self.lang[str(lang + "_" + country)] = ((name, lang, country, encoding))
				self.langlist.append(str(lang + "_" + country))
		except:
			print("[Language] Language " + str(name) + " not found")
		self.langlistselection.append((str(lang + "_" + country), name))

	def activateLanguage_TRY(self, index):
		if index not in self.lang:
			print("[Language] Selected language %s is not installed, fallback to es_ES!" % index)
			index = "es_ES"
		lang = self.lang[index]
		print("[Language] Activating language " + lang[0])
		self.catalog = gettext.translation('enigma2', resolveFilename(SCOPE_LANGUAGE, ""), languages=[index], fallback=True)
		self.catalog.install(names=("ngettext", "pgettext"))
		self.activeLanguage = index
		self.gotLanguage = self.getLanguage()
		for x in self.callbacks:
			if x:
				x()

		# NOTE: we do not use LC_ALL, because LC_ALL will not set any of the categories, when one of the categories fails.
		# We'd rather try to set all available categories, and ignore the others
		for category in [locale.LC_CTYPE, locale.LC_COLLATE, locale.LC_TIME, locale.LC_MONETARY, locale.LC_MESSAGES, locale.LC_NUMERIC]:
			try:
				locale.setlocale(category, (self.gotLanguage, 'UTF-8'))
			except:
				pass

		# Also write a locale.conf as /home/root/.config/locale.conf to apply language to interactive shells as well:
		if not path.exists('/home/root/.config'):
			mkdir('/home/root/.config')

		localeconf = open('/home/root/.config/locale.conf', 'w')
		for category in ["LC_TIME", "LC_DATE", "LC_MONETARY", "LC_MESSAGES", "LC_NUMERIC", "LC_NAME", "LC_TELEPHONE", "LC_ADDRESS", "LC_PAPER", "LC_IDENTIFICATION", "LC_MEASUREMENT", "LANG"]:
			if category == "LANG" or (category == "LC_DATE" and path.exists('/usr/lib/locale/' + self.gotLanguage + '/LC_TIME')) or path.exists('/usr/lib/locale/' + self.gotLanguage + '/' + category):
				localeconf.write('export %s="%s.%s"\n' % (category, self.gotLanguage, "UTF-8"))
			else:
				if path.exists('/usr/lib/locale/C.UTF-8/' + category):
					localeconf.write('export %s="C.UTF-8"\n' % category)
				else:
					localeconf.write('export %s="POSIX"\n' % category)
		localeconf.close()
		# HACK: sometimes python 2.7 reverts to the LC_TIME environment value, so make sure it has the correct value
		environ["LC_TIME"] = self.gotLanguage + '.UTF-8'
		environ["LANGUAGE"] = self.gotLanguage + '.UTF-8'
		environ["LANGUAGE2"] = self.gotLanguage
		environ["GST_SUBTITLE_ENCODING"] = self.getGStreamerSubtitleEncoding()
		return True

	def activateLanguage(self, index):
		from Screens.MessageBox import MessageBox
		from Tools import Notifications
		if not self.activateLanguage_TRY(index):
			print("[Language] - retry with ", "es_ES")
			Notifications.AddNotification(MessageBox, "The selected language is unavailable - using Spanish", MessageBox.TYPE_INFO, timeout=3)
			self.activateLanguage_TRY("es_ES")

	def activateLanguageIndex(self, index):
		if index < len(self.langlist):
			self.activateLanguage(self.langlist[index])

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
			print("[Language] DELETE LANG", delLang)
			if delLang[:2] == "es":
				print("[Language] Default Language can not be deleted !!")
				return
			elif delLang == "pt_BR":
				delLang = delLang.lower()
				delLang = delLang.replace('_', '-')
				system("opkg remove --autoremove --force-depends " + Lpackagename + delLang)
			else:
				system("opkg remove --autoremove --force-depends " + Lpackagename + delLang[:2])
		else:
			lang = self.activeLanguage
			print("[Language] Delete all lang except ", lang)
			ll = listdir(LPATH)
			for x in ll:
				if len(x) > 2:
					if x != lang and x[:2] != "es":
						x = x.lower()
						x = x.replace('_', '-')
						system("opkg remove --autoremove --force-depends " + Lpackagename + x)
				else:
					if x != lang[:2] and x != "es":
						system("opkg remove --autoremove --force-depends " + Lpackagename + x)
		system("touch /etc/enigma2/.removelang")
		self.InitLang()


LANG_TEXT = {
	"de_DE": {
		"T1": "Für Sprachauswahl Hoch/Runter-Tasten nutzen. Danach OK drücken.",
		"T2": "Sprachauswahl",
		"T3": "Abbrechen",
		"T4": "Speichern",
		"T5": "Sprache hinzufügen",
		"T6": "Sprache löschen(n)",
	},
	"ar_AE": {
		"T1": "من فضلك أستخدم ذر السهم العلوى أو السفلى لإختيار اللغه. ثم أضغط موافق .",
		"T2": "إختيار اللغـه",
		"T3": "إلغاء",
		"T4": "حفظ",
		"T5": "إضافة لغة",
		"T6": "حذف اللغة (اللغات)",
	},
	"bg_BG": {
		"T1": "Използвайте UP и DOWN бутони за избор на вашия език. След това натиснете ОК",
		"T2": "Избор Език",
		"T3": "Отказ",
		"T4": "Запази",
		"T5": "Добавяне на език",
		"T6": "Изтриване на език(и)",
	},
	"ca_AD": {
		"T1": "Utilitzeu les tecles UP i DOWN per seleccionar o Menú per instal·lar el vostre idioma. A continuació, premeu la tecla D'acord.",
		"T2": "Selecció d'idioma",
		"T3": "Cancel·lar",
		"T4": "Desa",
		"T5": "Afegeix llenguatge",
		"T6": "Suprimir lenguaje(s)",
	},
	"cs_CZ": {
		"T1": "Použijte tlačítka Nahoru a Dolů k výběru Vašeho jazyka. Poté stiskněte OK.",
		"T2": "Výběr jazyka",
		"T3": "Zavřít",
		"T4": "Uložit",
		"T5": "Přidat jazyk",
		"T6": "Odstranit jazyk(y)",
	},
	"da_DK": {
		"T1": "Benyt venligst OP og NED tasten til at vælge sprog. Tryk bagefter på OK knappen.",
		"T2": "Valg af sprog",
		"T3": "Fortryd",
		"T4": "Gem",
		"T5": "Tilføj sprog",
		"T6": "Slet sprog(e)",
	},
	"el_GR": {
		"T1": "Χρησιμοποιήστε τα πλήκτρα ΠΑΝΩ και ΚΑΤΩ για επιλογή γλώσσας. Μετά πιέστε το ΟΚ.",
		"T2": "Επιλογή γλώσσας",
		"T3": "Άκυρο ",
		"T4": "Αποθήκευση",
		"T5": "Προσθήκη γλώσσας",
		"T6": "Διαγραφή γλώσσας(ων)",
	},
	"en_AU": {
		"T1": "Use the UP and DOWN keys to select or Menu to install your language. Then press the OK key.",
		"T2": "Language selection",
		"T3": "Cancel",
		"T4": "Save",
		"T5": "Add Language",
		"T6": "Delete Language(s)",
	},
	"en_US": {
		"T1": "Use the UP and DOWN keys to select or Menu to install your language. Then press the OK key.",
		"T2": "Language selection",
		"T3": "Cancel",
		"T4": "Save",
		"T5": "Add Language",
		"T6": "Delete Language(s)",
	},
	"en_GB": {
		"T1": "Use the UP and DOWN keys to select or Menu to set your language. Then press the OK key.",
		"T2": "Language selection",
		"T3": "Cancel",
		"T4": "Save",
		"T5": "Add Language",
		"T6": "Delete Language(s)",
	},
	"es_ES": {
		"T1": "Use las teclas ARRIBA y ABAJO para seleccionar el idioma, luego pulse botón OK. Pulsando MENU podrá instalar un nuevo idioma.",
		"T2": "Selección de idioma",
		"T3": "Cancelar",
		"T4": "Guardar",
		"T5": "Añadir lenguaje",
		"T6": "Eliminar lenguaje(s)",
	},
	"et_EE": {
		"T1": "Kasuta keele valimiseks 'ÜLES' ja 'ALLA' nuppe, seejärel vajuta OK.",
		"T2": "Keele valik",
		"T3": "Tühista",
		"T4": "Salvesta",
		"T5": "Keele lisamine",
		"T6": "Kustuta keel(ed)",
	},
	"fa_IR": {
		"T1": "من فضلك أستخدم ذر السهم العلوى أو السفلى لإختيار اللغه. ثم أضغط موافق .",
		"T2": "انتخاب زبان",
		"T3": "انصراف",
		"T4": "ذخیره",
		"T5": "إضافة لغة",
		"T6": "حذف اللغة (اللغات)",
	},
	"fi_FI": {
		"T1": "Valitse kieli ylös/alas näppäimillä ja paina OK-näppäintä.",
		"T2": "Kielivalinta",
		"T3": "Peruuta",
		"T4": "Tallenna",
		"T5": "Lisää kieli",
		"T6": "Poista kieli(t)",
	},
	"fr_FR": {
		"T1": "Veuillez utiliser les touches HAUT et BAS pour choisir votre langue. Ensuite pressez le bouton OK.",
		"T2": "Sélection de la langue",
		"T3": "Annuler",
		"T4": "Sauver",
		"T5": "Ajouter une langue",
		"T6": "Supprimer la/les langue(s)",
	},
	"fy_NL": {
		"T1": "Brúk de op en del toets om jo taal te kiezen. Dernei druk op OK",
		"T2": "Taal Kieze",
		"T3": "Ôfbrekke",
		"T4": "Opslaan",
		"T5": "Taal toevoegen",
		"T6": "Taal verwijderen",
	},
	"he_IL": {
		"T1": "من فضلك أستخدم ذر السهم العلوى أو السفلى لإختيار اللغه. ثم أضغط موافق .",
		"T2": "انتخاب زبان",
		"T3": "انصراف",
		"T4": "ذخیره",
		"T5": "إضافة لغة",
		"T6": "حذف اللغة (اللغات)",
	},
	"hk_HK": {
		"T1": "按 上/下 鍵選擇語言, 選定後按 OK.",
		"T2": "語言選擇",
		"T3": "取消",
		"T4": "保存",
		"T5": "添加语言",
		"T6": "删除语言",
	},
	"hr_HR": {
		"T1": "Za izbiro jezika uporabite tipki UP in DOWN. Nato pritisnite tipko OK.",
		"T2": "Odaberite Jezik",
		"T3": "Odustani",
		"T4": "Save",
		"T5": "Dodajanje jezika",
		"T6": "Izbriši jezik(e)",
	},
	"hu_HU": {
		"T1": "Kérem, használja a FEL és LE gombokat a nyelv kiválasztásához. Ez után nyomja le az OK gombot.",
		"T2": "Nyelvválasztás",
		"T3": "Mégse",
		"T4": "Mentés",
		"T5": "Nyelv hozzáadása",
		"T6": "Nyelv(ek) törlése",
	},
	"is_IS": {
		"T1": "Vinsamlega notið UP og NIÐUR takka til að velja tungumál. Ýttu svo á OK til að nota.",
		"T2": "Val tungumáls",
		"T3": "Hætta við",
		"T4": "Vista",
		"T5": "Keele lisamine",
		"T6": "Kustuta keel(ed)",
	},
	"it_IT": {
		"T1": "Selezionare la propria lingua utilizzando i tasti Sù/Giù. Premere OK per confermare.",
		"T2": "Selezione lingua",
		"T3": "Annull.",
		"T4": "Salvare",
		"T5": "Aggiungi lingua",
		"T6": "Cancellare la lingua",
	},
	"ku_KU": {
		"T1": "按 上/下 鍵選擇語言, 選定後按 OK.",
		"T2": "語言選擇",
		"T3": "取消",
		"T4": "保存",
		"T5": "添加语言",
		"T6": "删除语言",
	},
	"lt_LT": {
		"T1": "Prašome naudoti AUKŠTYN IR ŽEMYN mygtukus, kad išsirinktumėte savo kalbą. Po to spauskite OK mygtuką.",
		"T2": "Kalbos pasirinkimas",
		"T3": "Atšaukti",
		"T4": "Saugoti",
		"T5": "Pridėti kalbą",
		"T6": "Ištrinti kalbą (-as)",
	},
	"lv_LV": {
		"T1": "Lūdzu lietojiet UP un DOWN taustiņus, lai izvēlētos valodu. Pēc tam spiediet OK.",
		"T2": "Valodas izvēle",
		"T3": "Atcelt",
		"T4": "Saglabāt",
		"T5": "Pievienot valodu",
		"T6": "Dzēst valodu(-as)",
	},
	"nl_NL": {
		"T1": "Gebruik de omhoog/omlaag toetsen om de gewenste taal te selecteren. Druk daarna op OK.",
		"T2": "Taalkeuze",
		"T3": "Annuleren",
		"T4": "Opslaan",
		"T5": "Taal toevoegen",
		"T6": "Taal verwijderen",
	},
	"nb_NO": {
		"T1": "Bruk tastene OPP og NED for å velge språk. Trykk deretter på OK-knappen.",
		"T2": "Språkvalg",
		"T3": "Avbryt",
		"T4": "Lagre",
		"T5": "Legg til språk",
		"T6": "Slett språk(er)",
	},
	"no_NO": {
		"T1": "Bruk tastene OPP og NED for å velge språk. Trykk deretter på OK-knappen.",
		"T2": "Språkvalg",
		"T3": "Avbryt",
		"T4": "Lagre",
		"T5": "Legg til språk",
		"T6": "Slett språk(er)",
	},
	"pl_PL": {
		"T1": "W celu wyboru języka użyj klawiszy GÓRA i DÓŁ. Nastepnie nacisnij przycisk OK.",
		"T2": "Wybór języka",
		"T3": "Anuluj",
		"T4": "Zapisz",
		"T5": "Dodaj język",
		"T6": "Usuń języki",
	},
	"pt_PT": {
		"T1": "Utilize as teclas UP e DOWN para selecionar ou Menu para instalar o seu idioma. Em seguida, prima a tecla OK.",
		"T2": "Seleção do Idioma",
		"T3": "Cancelar",
		"T4": "Guardar",
		"T5": "Adicionar idioma",
		"T6": "Eliminar língua(s)",
	},
	"pt_BR": {
		"T1": "Use as teclas UP e DOWN para selecionar ou Menu para instalar seu idioma. Em seguida, pressione a tecla OK.",
		"T2": "Seleção do idioma",
		"T3": "Cancelar",
		"T4": "Guardar",
		"T5": "Adicionar idioma",
		"T6": "Excluir idioma(s)",
	},
	"ro_RO": {
		"T1": "Utilizați tastele UP și DOWN pentru a selecta sau Menu pentru a vă instala limba. Apoi apăsați tasta OK.",
		"T2": "Selectare limba",
		"T3": "Anuleaza",
		"T4": "Salvare",
		"T5": "Adaugă o limbă",
		"T6": "Ștergeți limba (limbile)",
	},
	"ru_RU": {
		"T1": "С помощью кнопок ВВЕРХ и ВНИЗ выберите или Меню, чтобы установить язык. Затем нажмите кнопку OK.",
		"T2": "Выбор языка",
		"T3": "Отмена",
		"T4": "Сохранить",
		"T5": "Добавить язык",
		"T6": "Удалить язык(и)",
	},
	"sk_SK": {
		"T1": "Pomocou tlačidiel NAHORU a DOLEVA vyberte alebo Menu nainštalujte svoj jazyk. Potom stlačte tlačidlo OK.",
		"T2": "Voľba jazyka",
		"T3": "Zrušiť",
		"T4": "Uložiť",
		"T5": "Pridať jazyk",
		"T6": "Odstrániť jazyk(y)",
	},
	"sl_SI": {
		"T1": "S tipkama UP in DOWN izberite ali Meni za namestitev jezika. Nato pritisnite tipko OK.",
		"T2": "Izbira jezik",
		"T3": "Izhod",
		"T4": "Potrditev",
		"T5": "Dodajanje jezika",
		"T6": "Izbriši jezik(e)",
	},
	"sr_YU": {
		"T1": "S tipkama UP in DOWN izberite ali Meni za namestitev jezika. Nato pritisnite tipko OK.",
		"T2": "Izbor jezika",
		"T3": "Odustani",
		"T4": "Sačuvajte",
		"T5": "Dodajanje jezika",
		"T6": "Izbriši jezik(e)",
	},
	"sv_SE": {
		"T1": "Vänligen använd UPP och NER pil för att välja språk. Efter val tryck på OK knappen.",
		"T2": "Välj språk",
		"T3": "Avbryt",
		"T4": "Spara",
		"T5": "Lägg till språk",
		"T6": "Radera språk(en)",
	},
	"th_TH": {
		"T1": "ใช้ปุ่มขึ้นและลงเพื่อเลือกหรือเมนูเพื่อติดตั้งภาษาของคุณ จากนั้นกดปุ่ม OK เลิก",
		"T2": "เลือกภาษา",
		"T3": "ยกเลิก",
		"T4": "บันทึก",
		"T5": "เพิ่มภาษา",
		"T6": "ลบภาษา",
	},
	"tr_TR": {
		"T1": "Lütfen dil seçiminizi yapmak için YUKARI ve AŞAĞI tuşlarını kullanın, sonrasında OK'a basın.",
		"T2": "Dil seçimi",
		"T3": "İptal",
		"T4": "Kaydet",
		"T5": "Dil Ekleme",
		"T6": "Dil(ler)i Sil",
	},
	"uk_UA": {
		"T1": "Використовуйте кнопки ВВЕРХ і ВНИЗ, щоб вибрати Вашу мову. Після вибору натисніть OK.",
		"T2": "Вибір мови",
		"T3": "Відмінити",
		"T4": "Зберегти",
		"T5": "Додати мову",
		"T6": "Видалити мову(и)",
	},
	"zh_CN": {
		"T1": "按 上/下 鍵選擇語言, 選定後按 OK.",
		"T2": "語言選擇",
		"T3": "取消",
		"T4": "保存",
		"T5": "添加语言",
		"T6": "删除语言",
	},
}

language = Language()
