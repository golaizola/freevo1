# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# the Freevo MPlayer plug-in for audio
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:
#
# -----------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002 Krister Lagerstrom, et al.
# Please see the file freevo/Docs/CREDITS for a complete list of authors.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------
import logging
logger = logging.getLogger("freevo.audio.plugins.mplayer")


import os
import re

import config     # Configuration handler. reads config file.
import childapp   # Handle child applications

import rc
import plugin

from event import *


class PluginInterface(plugin.Plugin):
    """
    Mplayer plugin for the audio player. Use mplayer to play all audio
    files.
    """

    def __init__(self):
        # create the mplayer object
        plugin.Plugin.__init__(self)

        # register mplayer as the object to play audio
        plugin.register(MPlayer(), plugin.AUDIO_PLAYER, True)


class MPlayer:
    """
    the main class to control mplayer
    """

    def __init__(self):
        self.name     = 'mplayer'
        self.event_context = 'audio'
        self.app      = None


    def rate(self, item):
        """
        How good can this player play the file:
        2 = good
        1 = possible, but not good
        0 = unplayable
        """
        try:
            logger.log( 9, 'url=%r', item.url)
            logger.log( 9, 'mode=%r', item.mode)
            logger.log( 9, 'mimetype=%r', item.mimetype)
        except Exception, e:
            pass
        if item.url.startswith('radio://'):
            logger.debug('%r unplayable', item.url)
            return 0
        if item.url.startswith('cdda://'):
            logger.debug('%r possible', item.url)
            return 1
        logger.debug('%r good', item.url)
        return 2


    def get_demuxer(self, filename):
        DEMUXER_MP3 = 17
        DEMUXER_OGG = 18
        rest, extension     = os.path.splitext(filename)
        if extension.lower() == '.mp3':
            return "-hr-mp3-seek -demuxer " + str(DEMUXER_MP3)
        if extension.lower() == '.ogg':
            return "-demuxer " + str(DEMUXER_OGG)
        if extension.lower() == '.ac3':
            return "-ac hwac3 -rawaudio on:format=0x2000"
        else:
            return ''


    def play(self, item, playerGUI):
        """
        play a audioitem with mplayer
        """
        logger.debug('%s.play(item=%r, playerGUI=%r)', self.__module__, item, playerGUI)
        self.playerGUI = playerGUI
        filename       = item.filename

        if filename and not os.path.isfile(filename):
            self.plugins = ()
            return _('%s\nnot found!') % Unicode(item.url)

        if not filename:
            filename = item.url

        # Build the MPlayer command
        mpl = '--prio=%s %s -slave %s' % (config.MPLAYER_NICE, config.MPLAYER_CMD, config.MPLAYER_ARGS_DEF)

        if config.DEBUG_CHILDAPP:
            mpl += ' -v'
        #if not item.network_play:
        #    demux = ' %s ' % self.get_demuxer(filename)
        #else:
        #    # Don't include demuxer for network files
        #    demux = ''

        # Let mplayer determine the demuxer
        demux = ''

        extra_opts = item.mplayer_options
        ext = os.path.splitext(filename)[1]

        is_playlist = False
        if hasattr(item, 'is_playlist') and item.is_playlist:
            is_playlist = True

        if item.network_play:
            if str(ext) in ('.m3u', '.pls', '.asx'):
                is_playlist = True

        if str(filename).find(".jsp?") >= 0:
            is_playlist = True

        if item.network_play:
            extra_opts += ' -cache 100'

        if hasattr(item, 'reconnect') and item.reconnect:
            extra_opts += ' -loop 0'

        command = '%s -vo null -ao %s %s %s' % (mpl, config.MPLAYER_AO_DEV, demux, extra_opts)

        if command.find('-playlist') > 0:
            command = command.replace('-playlist', '')

        command = command.replace('\n', '').split(' ')

        if is_playlist:
            command.append('-playlist')

        command.append(filename)

        self.plugins = plugin.get('mplayer_audio')
        for p in self.plugins:
            command = p.play(command, self)

        #if plugin.getbyname('MIXER'):
            #plugin.getbyname('MIXER').reset()

        self.item = item

        self.app = MPlayerApp(command, self)
        return None


    def stop(self):
        """
        Stop mplayer
        """
        if self.app:
            self.app.stop('quit\n')

        for p in self.plugins:
            command = p.stop()
        

    def is_playing(self):
        return self.app.isAlive()


    def refresh(self):
        self.playerGUI.refresh()


    def eventhandler(self, event, menuw=None):
        """
        eventhandler for mplayer control. If an event is not bound in this
        function it will be passed over to the items eventhandler
        """
        logger.debug('%s.eventhandler=%s', self.__module__, event)
        try:
            for p in self.plugins:
                if p.eventhandler(event):
                    logger.debug('%s handled by %s', event, p)
                    return True
        except Exception, why:
            import traceback
            traceback.print_exc()
            return True

        if event == PLAY_END:
            self.app = None
            
        if event == AUDIO_SEND_MPLAYER_CMD:
            self.app.write('%s\n' % event.arg)
            return True

        if event == PLAY_END and event.arg:
            self.stop()
            if self.playerGUI.try_next_player():
                return True

        if event == STOP:
            self.playerGUI.stop(restore_menu=True)
            return self.item.eventhandler(event)

        if event in (PLAY_END, USER_END):
            self.playerGUI.stop()
            return self.item.eventhandler(event)

        elif event == PAUSE or event == PLAY:
            self.app.write('pause\n')
            self.playerGUI.pause()
            return True

        elif event == SEEK:
            self.app.write('seek %s\n' % event.arg)
            self.playerGUI.seek(event.arg)
            return True

        elif (event == PLAYLIST_NEXT) or event == NEXT:
            self.playerGUI.next()
            return self.item.eventhandler(event)

        elif (event == PLAYLIST_PREV) or event == PREV:
            self.playerGUI.prev()
            return self.item.eventhandler(event)

        else:
            # everything else: give event to the items eventhandler
            return self.item.eventhandler(event)


# ======================================================================

class MPlayerApp(childapp.ChildApp2):
    """
    class controlling the in and output from the mplayer process
    """
    def __init__(self, app, player):
        self.item        = player.item
        self.player      = player
        self.elapsed     = 0
        self.stop_reason = 0 # 0 = ok, 1 = error
        self.RE_TIME     = re.compile("^A: *([0-9]+)").match
        self.RE_TIME_NEW = re.compile("^A: *([0-9]+):([0-9]+)").match
        self.RE_NEW_TRK  = re.compile("\[track\] quiet after").match

        # [0] -> start of line to check with mplayer output
        # [1] -> keyword to store info in self.item.info
        self.STREAM_KEYWORDS = [
            ("Genre  : ", "genre"),
            ("Artist : ", "artist"),
            ("Name   : ", "stream_name"),
            (" Genre: ", "genre"),
            (" Artist: ", "artist"),
            (" Name: ", "stream_name"),
            ("Demuxer info Name changed to ", "stream_name"),
            ("Demuxer info Genre changed to ", "genre"),
            ("Demuxer info Artist changed to ", "artist")
        ]


        # check for mplayer plugins
        self.stdout_plugins  = []
        self.elapsed_plugins = []
        for p in plugin.get('mplayer_audio'):
            if hasattr(p, 'stdout'):
                self.stdout_plugins.append(p)
            if hasattr(p, 'elapsed'):
                self.elapsed_plugins.append(p)
        childapp.ChildApp2.__init__(self, app, stop_osd=0)


    def stop_event(self):
        return Event(PLAY_END, self.stop_reason, handler=self.player.eventhandler)


    def stdout_cb(self, line):
        if line.startswith("A:"):         # get current time

            m = self.RE_TIME_NEW(line)
            if m:
                self.stop_reason = 0
                timestrs = m.group().split(":")
                if len(timestrs) == 5:
                    # playing for days!
                    self.item.elapsed = 86400*int(timestrs[1]) + \
                                        3600*int(timestrs[2]) + \
                                        60*int(timestrs[3]) + \
                                        int(timestrs[4])
                elif len(timestrs) == 4:
                    # playing for hours
                    self.item.elapsed = 3600*int(timestrs[1]) + \
                                        60*int(timestrs[2]) + \
                                        int(timestrs[3])
                elif len(timestrs) == 3:
                    # playing for minutes
                    self.item.elapsed = 60*int(timestrs[1]) + int(timestrs[2])
                elif len(timestrs) == 2:
                    # playing for only seconds
                    self.item.elapsed = int(timestrs[1])
            else:
                m = self.RE_TIME(line) # Convert decimal
                if m:
                    self.item.elapsed = int(m.group(1))

            if self.item.elapsed != self.elapsed:
                self.player.refresh()
            self.elapsed = self.item.elapsed

            for p in self.elapsed_plugins:
                p.elapsed(self.elapsed)

        elif not self.item.elapsed:
            for p in self.stdout_plugins:
                p.stdout(line)

        if line.startswith('[track]'):
            m = self.RE_NEW_TRK(line)
            if m:
                rc.post_event(Event('TRACK'))

        if line.startswith("ICY Info"):
            titleKey = "StreamTitle='"
            titleIndex = line.find(titleKey)
            if titleIndex != -1:
                titleStart = titleIndex + len(titleKey)
                titleEnd = line.find("';", titleStart)
                if titleEnd > titleStart:
                    breakIndex = line.find(" - ", titleStart)
                    if breakIndex != -1:
                        self.item.info['artist'] = line[titleStart:breakIndex].strip()
                        self.item.info['title'] = line[breakIndex+2:titleEnd].strip()
                        self.item.info['stream_name'] = self.item.name
                    else:
                        self.item.info['artist'] = line[titleStart:titleEnd]

        else:
            for keywords in self.STREAM_KEYWORDS:
                if line.startswith(keywords[0]):
                    logger.debug("stream keyword found: %s %s", keywords[0], keywords[1])
                    titleStart = len(keywords[0])
                    self.item.info[ keywords[1] ] = line[titleStart:]
                    break

    def stderr_cb(self, line):
        if line.startswith('Failed to open') and \
               (not self.item or not self.item.elapsed):
            self.stop_reason = line

        for p in self.stdout_plugins:
            p.stdout(line)
