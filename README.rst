==========
modularirc
==========

Written in Python 3

Dependencies:

+ irc (https://pypi.python.org/pypi/irc)

Config file at ~/.config/ircbot.conf

Example:

.. code:: json

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

Also have a look at `modularirc-basemodules <https://github.com/jawsper/modularirc-basemodules>`_ for some somewhat useful modules.