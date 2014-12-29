from ._module import _module

KOEIEN = ('boe', 'moe')
KOEIEN_TEKST = 'GEEN KOEIEN'

class koeien(_module):
	def on_privmsg(self, source, target, message):
		if message.lower() in KOEIEN:
			self.mgr.bot.connection.kick(target, source, KOEIEN_TEKST)
