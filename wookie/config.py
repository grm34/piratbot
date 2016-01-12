#!/usr/bin/env python
# -*- coding: utf-8 -*-

__appname__ = "wookie"
__version__ = "v.3.0"
__author__ = "@c0ding, @grm34"
__date__ = "2012 - 2016"
__license__ = "Apache v2.0 License"

wookie = {
    'bot_owner': ['', ''],
    'start_bot': 'screen -dmS wookie',
    'kill_bot': 'screen -X -S wookie kill',
    'mode': 'standard'
}

network = {
    'server': '',
    'port': 6667,
    'SSL': False,
    'ipv6': False,
    'channels': ['', ''],
    'bot_nick': 'piratbot',
    'bot_name': 'wookie v.3.0 is available at '
                'https://github.com/c0ding/wookie',
    'password': ''
}

feeds = {
    'irc_delay': .5,
    'boerse_delay': 5.0,
    'xrel_delay': 5.0,
    'pre_delay': 5.0,
    'boerse_url': 'https://boerse.to/forum/filme.31/index.rss',
    'xrel_url': 'http://www.xrel.to/feeds/atom/p2p-releases.xml',
    'pre_url': 'https://pre.corrupt-net.org/rss.php?k=',
    'pre_passkey': ''
}

whitelist = {
    'boerse': ['x264', 'BDRip', 'DVDRip'],
    'xrel': ['x264', 'BDRip', 'DVDRip'],
    'pre': ['x264', 'BDRip', 'DVDRip']
}

blacklist = {
    'boerse': ['test1', 'test2', 'test3'],
    'xrel': ['test1', 'test2', 'test3'],
    'pre': ['test1', 'test2', 'test3']
}
