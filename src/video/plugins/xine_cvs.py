#if 0 /*
# -----------------------------------------------------------------------
# xine.py - the Freevo XINE module for video
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
#
# Activate this plugin by putting plugin.activate('video.xine_cvs') in your
# local_conf.py. Than xine will be used for DVDs when you SELECT the item.
# When you select a title directly in the menu, this plugin won't be used
# and the default player (mplayer) will be used. You need the current xine
# CVS version to use this.
#
# This plugin can also be used for VCD playback with menus. Install
# xine-vcdnav and set the second parameter to TRUE (the first is use-for-dvd)
# plugin.activate('video.xine_cvs', args=(TRUE, TRUE))
#
# WARNING:
# xine-vcdnav has some problems. Some VCDs won't play at all, some one
# in some drives. It also can take up to 10 secs until the video
# starts. When nothing happens and you press STOP, it can also take up
# to 10 secs until xine dies (better: xine will be killed). This could
# also crash Freevo (python segfault). 
#
#
# Todo:        
#
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.2  2003/07/29 19:08:35  dischi
# o new notes
# o VCD support (vcdnav)
# o deinterlacing with tvtime or -D paramter
# o VIDEO_NEXT_AUDIOLANG warp around
#
# Revision 1.1  2003/07/27 19:16:25  dischi
# New version of the xine plugin for DVD. You need the current xine cvs
# to get it working. 
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
# ----------------------------------------------------------------------- */
#endif


import time, os
import threading, signal

import config     # Configuration handler. reads config file.
import util       # Various utilities
import childapp   # Handle child applications
import rc         # The RemoteControl class.
import skin

from event import *
import plugin

# RegExp
import re

DEBUG = config.DEBUG

TRUE  = 1
FALSE = 0

# contains an initialized Xine() object
xine = None

class PluginInterface(plugin.Plugin):
    """
    Xine plugin for the video player. Use xine to play all video
    files.
    """
    def __init__(self, dvd=TRUE, vcd=FALSE):
        global xine
        # create the xine object
        plugin.Plugin.__init__(self)
        try:
            command = config.XINE_COMMAND
        except:
            print '***********************************************************'
            print 'loading xine plugin failed, please set XINE_COMMAND in your'
            print 'local_config.py. Possible good values are'
            print '"xine -V xv -g -f" for using xine while running X'
            print '"fbxine -V vidix"  for using xine on the framebuffer'
            print 'Please read the notes in src/video/plugins/xine.py'
            print '***********************************************************'
            return
        
        xine = util.SynchronizedObject(Xine(command))

        # register it as the object to play
        if dvd:
            plugin.register(xine, plugin.DVD_PLAYER)
        if vcd:
            plugin.register(xine, plugin.VCD_PLAYER)


class Xine:
    """
    the main class to control xine
    """
    
    def __init__(self, command):
        self.thread = Xine_Thread()
        self.thread.setDaemon(1)
        self.thread.start()
        self.mode = None
        self.app_mode = ''
        self.command = command
            
    def play(self, item):
        """
        play a dvd with xine
        """

        self.app_mode = item.mode       # dvd or vcd keymap

        if plugin.getbyname('MIXER'):
            plugin.getbyname('MIXER').reset()

        self.item = item
        self.thread.item = item
        
        if DEBUG:
            print 'Xine.play(): Starting thread, cmd=%s' % command
        rc.app(self)

        command = '%s --no-lirc --stdctl' % self.command
        if item.deinterlace:
            if self.command.find('vidix') > 0 or self.command.find('fbxine') >= 0:
                command = '%s --post tvtime' % command
            else:
                command = '%s -D' % command

        self.max_audio = 0
        self.current_audio = -1

        if item.mode == 'dvd':
            for track in item.info['tracks']:
                self.max_audio = max(self.max_audio, len(track['audio']))

        skin.get_singleton().clear()
        self.thread.mode    = 'play'
        if item.mode == 'dvd':
            self.thread.command = '%s dvd://' % command
        else:
            self.thread.command = '%s vcdx:/%s:' % (command, item.media.devicename)
        self.thread.mode_flag.set()
        return None
    

    def stop(self):
        """
        Stop xine and set thread to idle
        """
        self.thread.mode = 'stop'
        self.thread.mode_flag.set()
        self.thread.item = None
        rc.app(None)
        while self.thread.mode == 'stop':
            time.sleep(0.3)
            

    def eventhandler(self, event):
        """
        eventhandler for xine control. If an event is not bound in this
        function it will be passed over to the items eventhandler
        """
        if event == PAUSE or event == PLAY:
            self.thread.app.write('pause\n')
            return TRUE

        if event == STOP:
            self.thread.app.write('quit\n')
            for i in range(10):
                if self.thread.mode == 'idle':
                    break
                time.sleep(0.3)
            else:
                # sometimes xine refuses to die
                self.stop()
            return TRUE

        if event == SEEK:
            pos = int(event.arg)
            if pos < 0:
                action='SeekRelative-'
                pos = 0 - pos
            else:
                action='SeekRelative+'
            if pos <= 15:
                pos = 15
            elif pos <= 30:
                pos = 30
            else:
                pos = 30
            self.thread.app.write('%s%s\n' % (action, pos))
            return TRUE

        # DVD NAVIGATION
        if event == DVDNAV_LEFT:
            self.thread.app.write('EventLeft\n')
            return TRUE
            
        if event == DVDNAV_RIGHT:
            self.thread.app.write('EventRight\n')
            return TRUE
            
        if event == DVDNAV_UP:
            self.thread.app.write('EventUp\n')
            return TRUE
            
        if event == DVDNAV_DOWN:
            self.thread.app.write('EventDown\n')
            return TRUE
            
        if event == DVDNAV_SELECT:
            self.thread.app.write('EventSelect\n')
            return TRUE
            
        if event == DVDNAV_TITLEMENU:
            self.thread.app.write('TitleMenu\n')
            return TRUE
            
        if event == DVDNAV_MENU:
            self.thread.app.write('Menu\n')
            return TRUE


        # VCD NAVIGATION
        if event in INPUT_ALL_NUMBERS:
            self.thread.app.write('Number%s\n' % event.arg)
            time.sleep(0.1)
            self.thread.app.write('EventSelect\n')
            return TRUE
        
        if event == MENU:
            self.thread.app.write('TitleMenu\n')
            return TRUE


        if event == VIDEO_NEXT_AUDIOLANG and self.max_audio:
            if self.current_audio < self.max_audio - 1:
                self.thread.app.write('AudioChannelNext\n')
                self.current_audio += 1
                # wait until the stream is changed
                time.sleep(0.1)
            else:
                # bad hack to warp around
                if self.command.find('fbxine'):
                    self.thread.app.write('AudioChannelDefault\n')
                    time.sleep(0.1)
                for i in range(self.max_audio):
                    self.thread.app.write('AudioChannelPrior\n')
                    time.sleep(0.1)
                self.current_audio = -1
            return TRUE
            
        if event in ( PLAY_END, USER_END ):
            self.stop()
            return self.item.eventhandler(event)

        # nothing found? Try the eventhandler of the object who called us
        return self.item.eventhandler(event)

        

# ======================================================================

class XineApp(childapp.ChildApp):
    """
    class controlling the in and output from the xine process
    """

    def __init__(self, app, item):
        self.item = item
        childapp.ChildApp.__init__(self, app)
        self.exit_type = None
        
    def kill(self):
        # Use SIGINT instead of SIGKILL to make sure Xine shuts
        # down properly and releases all resources before it gets
        # reaped by childapp.kill().wait()
        childapp.ChildApp.kill(self, signal.SIGINT)


# ======================================================================

class Xine_Thread(threading.Thread):
    """
    Thread to wait for a xine command to play
    """

    def __init__(self):
        threading.Thread.__init__(self)
        
        self.mode      = 'idle'
        self.mode_flag = threading.Event()
        self.command   = ''
        self.app       = None
        self.item  = None

        
    def run(self):
        while 1:
            if self.mode == 'idle':
                self.mode_flag.wait()
                self.mode_flag.clear()

            elif self.mode == 'play':
                if DEBUG:
                    print 'Xine_Thread.run(): Started, cmd=%s' % self.command
                    
                self.app = XineApp(self.command, self.item)

                while self.mode == 'play' and self.app.isAlive():
                    time.sleep(0.1)

                self.app.kill()

                if self.mode == 'play':
                    if self.app.exit_type == "End of file":
                        rc.post_event(PLAY_END)
                    elif self.app.exit_type == "Quit":
                        rc.post_event(USER_END)
                    else:
                        rc.post_event(PLAY_END)
                        
                if DEBUG:
                    print 'Xine_Thread.run(): Stopped'

                self.mode = 'idle'
                skin.get_singleton().redraw()
                
            else:
                self.mode = 'idle'
