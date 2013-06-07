ircbot
======
Dependencies:
python3-dateutil

======
Config file ~/.ircbot:

<pre>
[main]
server=$host[:$port]
[password=$password]
channel=$channel
nickname=$nickname
admin=$admin([;$other_admin)*
admin_channels=$channel[;$channel ...]
</pre>