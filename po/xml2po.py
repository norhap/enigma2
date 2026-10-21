#!/usr/bin/python
import sys
from os import listdir
from os.path import isdir, join
import re
from xml.sax import make_parser
from xml.sax.handler import ContentHandler, property_lexical_handler
try:
	from _xmlplus.sax.saxlib import LexicalHandler
	no_comments = False
except ImportError:
	class LexicalHandler:
		pass
	no_comments = True


def escape_po(s):
	s = s.replace('\\n', '\x00')
	s = s.replace('\\', '\\\\')
	s = s.replace('"', '\\"')
	s = s.replace('\x00', '\\n')
	return s


class parseXML(ContentHandler, LexicalHandler):
	def __init__(self, attrlist):
		self.isPointsElement, self.isReboundsElement = 0, 0
		self.attrlist = attrlist
		self.last_comment = None
		self.current_file = None
		self.ishex = re.compile(r'#[0-9a-fA-F]+\Z')

	def comment(self, comment):
		if "TRANSLATORS:" in comment:
			self.last_comment = comment

	def startElement(self, name, attrs):
		for x in ["text", "title", "value", "caption", "description"]:
			try:
				k = attrs[x]
				if k.strip() == "" or self.ishex.match(k):
					continue
				limpio = k.strip().replace(',', '').replace(' ', '')
				if limpio.isdigit():
					continue
				if re.match(r'^[\d,.\s]+$', k.strip()):
					continue
				if k.strip() in ('e', 'w', 'c', 'center', 'left', 'right', 'top', 'bottom', '0', '1'):
					continue
				self.attrlist.add((k, self.last_comment, self.current_file))
				self.last_comment = None
			except KeyError:
				pass


parser = make_parser()

attrlist = set()

contentHandler = parseXML(attrlist)
parser.setContentHandler(contentHandler)
if not no_comments:
	parser.setProperty(property_lexical_handler, contentHandler)

for arg in sys.argv[1:]:
	if isdir(arg):
		for file in listdir(arg):
			if file.endswith(".xml"):
				contentHandler.current_file = join(arg, file)
				parser.parse(join(arg, file))
	else:
		try:
			contentHandler.current_file = arg
			parser.parse(arg)
		except Exception:
			pass

attrlist = list(attrlist)
attrlist.sort(key=lambda x: x[0])
for (key, value, filepath) in attrlist:
	key_esc = escape_po(key)
	if filepath:
		print(f"#: {filepath[2:] if filepath.startswith('./') else filepath}")
	if value:
		for line in value.split("\n"):
			print(f"#. {line.strip()}")
	print(f'msgid "{key_esc}"')
	print('msgstr ""')
	print()
