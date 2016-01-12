#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import ssl
import time
import irclib
import socket
import urllib2
import calendar
import commands
import cfscrape
import optparse
import threading
import feedparser
from irclib import SimpleIRCClient
from threading import (Thread, Event)
from BeautifulSoup import BeautifulSoup
from datetime import (datetime, timedelta)
from django.utils.encoding import smart_str
from urllib2 import (urlopen, URLError, HTTPError)
from config import (feeds, wookie, network, whitelist, blacklist)

__appname__ = "wookie"
__version__ = "v.3.0"
__author__ = "@c0ding, @grm34"
__date__ = "2012 - 2016"
__license__ = "Apache v2.0 License"


class Queue_Manager(Thread):

    def __init__(self, connection, delay=feeds['irc_delay']):
        Thread.__init__(self)
        self.setDaemon(1)
        self.connection = connection
        self.delay = delay
        self.event = Event()
        self.queue = []

    def run(self):
        while 1:
            self.event.wait()
            while self.queue:
                (msg, target) = self.queue.pop(0)
                self.connection.privmsg(target, msg)
                time.sleep(self.delay)
            self.event.clear()

    def send(self, msg, target):
        self.queue.append((msg.strip(), target))
        self.event.set()


class _wookie(SimpleIRCClient):

    def __init__(self):
        irclib.SimpleIRCClient.__init__(self)
        self.start_time = time.time()
        self.queue = Queue_Manager(self.connection)

        self.BLUE = '\x0302'
        self.RED = '\x0304'
        self.YELLOW = '\x0308'
        self.GREEN = '\x0303'
        self.PURPLE = '\x0306'
        self.PINK = '\x0313'
        self.ORANGE = '\x0307'
        self.BOLD = '\x02'
        self.ITALIC = '\x1D'
        self.UNDERLINE = '\x1F'
        self.SWAP = '\x16'
        self.END = '\x0F'

    def on_welcome(self, serv, ev):
        if network['password']:
            serv.privmsg(
                "nickserv", "IDENTIFY {}".format(network['password']))
            serv.privmsg("chanserv", "SET irc_auto_rejoin ON")
            serv.privmsg("chanserv", "SET irc_join_delay 0")
        for channel in network['channels']:
            serv.join(channel)
        try:
            self.history_manager()
            self.pre_refresh()
            self.xrel_refresh()
            self.boerse_refresh()
            time.sleep(5)
            self.queue.start()
        except (OSError, IOError) as error:
            serv.disconnect()
            print(error)
            sys.exit(1)

    def on_rss_entry(self, text):
        for channel in network['channels']:
            self.queue.send(text, channel)

    def on_kick(self, serv, ev):
        serv.join(ev.target())

    def on_invite(self, serv, ev):
        serv.join(ev.arguments()[0])

    def on_ctcp(self, serv, ev):
        if ev.arguments()[0].upper() == 'VERSION':
            serv.ctcp_reply(
                ev.source().split('!')[0], network['bot_name'])

    def history_manager(self):
        home = '{}/.wookie_logs'.format(os.environ.get('HOME'))
        self.wookie_path = os.path.dirname(os.path.realpath(__file__))
        self.boerse_entries = '{}/boerse-entries'.format(home)
        self.xrel_entries = '{}/xrel-entries'.format(home)
        self.pre_entries = '{}/pre-entries'.format(home)
        if os.path.exists(home) is False:
            os.system('mkdir {}'.format(home))
        if os.path.exists(self.boerse_entries) is False:
            os.system('touch {}'.format(self.boerse_entries))
        if os.path.exists(self.xrel_entries) is False:
            os.system('touch {}'.format(self.xrel_entries))
        if os.path.exists(self.pre_entries) is False:
            os.system('touch {}'.format(self.pre_entries))

    def restart_bot(self, serv, ev):
        serv.disconnect()
        if wookie['mode'] == 'screen':
            current_screen = self.get_current_screen()
            os.system('{0} {1}/./wookie.py run && screen -X -S {2} kill'
                      .format(wookie['start_bot'], self.wookie_path,
                              current_screen))
        else:
            os.system('{}/./wookie.py start'.format(self.wookie_path))
        sys.exit(1)

    def get_current_screen(self):
        screen_list = commands.getoutput('screen -list')
        screen_lines = smart_str(
            screen_list.replace('\t', '')).splitlines()
        for screen in screen_lines:
            if 'wookie' in screen:
                current_screen = screen.split('.')[0]
        return current_screen

    def on_privmsg(self, serv, ev):
        author = irclib.nm_to_n(ev.source())
        message = ev.arguments()[0].strip()
        arguments = message.split(' ')
        if author in wookie['bot_owner']:
            if '.say' == arguments[0] and len(arguments) > 2:
                serv.privmsg(
                    arguments[1], message.replace(arguments[0], '')
                                         .replace(arguments[1], '')[2:])
            if '.act' == arguments[0] and len(arguments) > 2:
                serv.action(
                    arguments[1], message.replace(arguments[0], '')
                                         .replace(arguments[1], '')[2:])
            if '.join' == arguments[0] and len(arguments) > 2:
                serv.join(message[3:])
            if '.part' == arguments[0] and len(arguments) > 2:
                serv.part(message[3:])

    def on_pubmsg(self, serv, ev):
        author = irclib.nm_to_n(ev.source())
        message = ev.arguments()[0].strip()
        arguments = message.split(' ')
        event_time = time.strftime('[%H:%M:%S]', time.localtime())
        print ('{0} {1}: {2}'.format(event_time, author, message))
        chan = ev.target()
        if author in wookie['bot_owner']:
            try:
                if ev.arguments()[0].lower() == '.restart':
                    self.restart_bot(serv, ev)
                if ev.arguments()[0].lower() == '.quit':
                    serv.disconnect()
                    if not wookie['mode']:
                        os.system(wookie['kill_bot'])
                    sys.exit(1)
            except OSError as error:
                serv.disconnect()
                print(error)
                sys.exit(1)

        if '.help' == arguments[0].lower():
            serv.privmsg(
                chan, '{0}Available commands are:{1} .help || '
                      '.version || .uptime || .restart || .quit'.format(
                          self.BOLD, self.END))

        if '.version' == arguments[0].lower():
            serv.privmsg(chan, network['bot_name'])

        if '.uptime' == arguments[0].lower():
            uptime_raw = round(time.time() - self.start_time)
            uptime = timedelta(seconds=uptime_raw)
            serv.privmsg(chan, '{0}Uptime:{1} {2}'.format(
                self.BOLD, self.END, uptime))

    def boerse_refresh(self):
        FILE = open(self.boerse_entries, "r")
        filetext = FILE.read()
        FILE.close()

        scraper = cfscrape.create_scraper()
        url = scraper.get(feeds['boerse_url']).content
        boerse = BeautifulSoup(url)
        for entry in boerse.findAll('item'):
            items = entry.find('title')
            title = '{}'.format(items).replace('<title>', '')\
                                      .replace('</title>', '')\
                                      .replace(' ', '.')\
                                      .replace('.-.', '')

            if title not in filetext and\
                    any([x in title for x in whitelist['boerse']]) and\
                    any([x not in title for x in blacklist['boerse']]):
                FILE = open(self.boerse_entries, "a")
                FILE.write("{}\n".format(title))
                FILE.close()
                self.on_rss_entry(
                    '{0}{1}[BOERSE]{2} {3}'.format(
                        self.BOLD, self.RED, self.END, title))

        threading.Timer(feeds['boerse_delay'], self.boerse_refresh).start()

    def xrel_refresh(self):
        FILE = open(self.xrel_entries, "r")
        filetext = FILE.read()
        FILE.close()

        xrel = feedparser.parse(feeds['xrel_url'])
        for entry in xrel.entries:
            title = smart_str(entry.title).replace('.-.', '')

            if title not in filetext and\
                    any([x in title for x in whitelist['xrel']]) and\
                    any([x not in title for x in blacklist['xrel']]):
                FILE = open(self.xrel_entries, "a")
                FILE.write("{}\n".format(title))
                FILE.close()
                self.on_rss_entry(
                    '{0}{1}[XREL]{2} {3}'.format(
                        self.BOLD, self.YELLOW, self.END, title))

        threading.Timer(feeds['xrel_delay'], self.xrel_refresh).start()

    def pre_refresh(self):
        FILE = open(self.pre_entries, "r")
        filetext = FILE.read()
        FILE.close()

        url = '{0}{1}'.format(feeds['pre_url'], feeds['pre_passkey'])
        pre = feedparser.parse(url)
        for entry in pre.entries:
            title = smart_str(entry.title)
            if title not in filetext and\
                    any([x in title for x in whitelist['pre']]) and\
                    any([x not in title for x in blacklist['pre']]):
                FILE = open(self.pre_entries, "a")
                FILE.write("{}\n".format(title))
                FILE.close()
                self.on_rss_entry(
                        '{0}{1}[PRE]{2} {3}'.format(
                            self.BOLD, self.GREEN, self.END, title))

        threading.Timer(feeds['pre_delay'], self.pre_refresh).start()


def main():

    usage = './wookie.py <start> or <screen>\n\n'\
        '<start> to run wookie in standard mode\n'\
        '<screen> to run wookie in detached screen'
    parser = optparse.OptionParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) == 1 and (
            args[0] == 'start' or
            args[0] == 'screen' or
            args[0] == 'run'):
        bot = _wookie()
    else:
        parser.print_help()
        parser.exit(1)

    try:
        if args[0] == 'screen':
            wookie['mode'] = 'screen'
            os.system('{0} {1}/./wookie.py run'.format(
                wookie['start_bot'], os.path.dirname(
                    os.path.realpath(__file__))))
            sys.exit(1)

        bot.connect(
            network['server'], network['port'],
            network['bot_nick'], network['bot_name'],
            ssl=network['SSL'], ipv6=network['ipv6'])
        bot.start()

    except OSError as error:
        print(error)
        sys.exit(1)
    except irclib.ServerConnectionError as error:
        print (error)
        sys.exit(1)

if __name__ == "__main__":
    main()
