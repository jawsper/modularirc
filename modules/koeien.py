from modules import Module

import re

KOEIEN = ('boe', 'moe')
KOEIEN_TEKST = 'GEEN KOEIEN'

KOEIEN_REGEX = r'^[mb]o+e+[.?!]*$'

class koeien(Module):
	def on_privmsg(self, source, target, message):
		if message.lower() in KOEIEN or re.search(KOEIEN_REGEX, message.lower()):
			self.mgr.bot.connection.kick(target, source, KOEIEN_TEKST)
