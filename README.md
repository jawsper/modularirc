ircbot
======

Written in Python 3

======
Dependencies:
+ irc (https://pypi.python.org/pypi/irc)
+ python-dateutil (for module ns) (https://pypi.python.org/pypi/python-dateutil)
+ requests (for module url_scanner)
+ hurry.filesize (for module url_scanner)

======
Config file ircbot.conf:

<pre>
{
	"version": "1.0",
	"servers":
	[
		{
			"nickname": "",
			"host": "",
			"port": 0,
			"ssl": false,
			"ipv6": false,
			"password": "",
			"channels": [],
			"admin_channels": [],
			"global_admins": []
		}
	]
}
</pre>
