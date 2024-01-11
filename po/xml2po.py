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


class parseXML(ContentHandler, LexicalHandler):
	def __init__(self, attrlist):
		self.isPointsElement, self.isReboundsElement = 0, 0
		self.attrlist = attrlist
		self.last_comment = None
		self.ishex = re.compile(r'#[0-9a-fA-F]+\Z')

	def comment(self, comment):
		if "TRANSLATORS:" in comment:
			self.last_comment = comment

	def startElement(self, name, attrs):
		for x in ["text", "title", "value", "caption", "description"]:
			try:
				k = str(attrs[x].encode('utf-8'))
				if k.strip() != "" and not self.ishex.match(k):
					attrlist.add((k, self.last_comment))
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
				parser.parse(join(arg, file))
	else:
		parser.parse(arg)
	attributes = list(attributes)  # noqa: F821
	attributes.sort(key=lambda x: x[0])
	for (key, value) in attributes:
		print(f"\n#: {arg}")
		key.replace("\\n", "\"\n\"")
		if value:
			for line in value.split("\n"):
				print(f"#. {line}")
		print(f"msgid \"{key}\"")
		print("msgstr \"\"")
	attributes = set()
