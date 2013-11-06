ircbot
======

Written in Python 3

======
Dependencies:
python3-dateutil

======
Config file ircbot.ini:

<pre>
[main]
server=$host[:$port]
[password=$password]
channel=$channel
nickname=$nickname
admin=$admin([;$other_admin)*
admin_channels=$channel[;$channel ...]
</pre>
