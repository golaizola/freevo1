#if 0 /*
# -----------------------------------------------------------------------
# mplayer.py - the Freevo MPlayer module for video
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.2  2002/11/26 20:58:44  dischi
# o Fixed bug that not only the first character of mplayer_options is used
# o added the configure stuff again (without play from stopped position
#   because the mplayer -ss option is _very_ broken)
# o Various fixes in DVD playpack
#
# Revision 1.1  2002/11/24 13:58:45  dischi
# code cleanup
#
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


import sys
import random
import time, os, glob
import string, popen2, fcntl, select, struct
import threading, signal

import config     # Configuration handler. reads config file.
import util       # Various utilities
import childapp   # Handle child applications
import menu       # The menu widget class
import mixer      # Controls the volumes for playback and recording
import osd        # The OSD class, used to communicate with the OSD daemon
import rc         # The RemoteControl class.
import skin       # Cause audio handling needs skin functions.
import fnmatch

# RegExp
import re

DEBUG = config.DEBUG

TRUE  = 1
FALSE = 0

# Setting up the default objects:
osd        = osd.get_singleton()
rc         = rc.get_singleton()
menuwidget = menu.get_singleton()
mixer      = mixer.get_singleton()
skin       = skin.get_singleton()

# Module variable that contains an initialized MPlayer() object
_singleton = None

def get_singleton():
    global _singleton

    # One-time init
    if _singleton == None:
        _singleton = MPlayer()
        
    return _singleton


class MPlayer:
    """
    the main class to control mplayer
    """
    
    def __init__(self):
        self.thread = MPlayer_Thread()
        self.thread.start()
        self.mode = None

                         
    def play(self, filename, options, item):
        """
        play a audioitem with mplayer
        """

        mode = item.mode

        # Is the file streamed over the network?
        if filename.find('://') != -1:
            # Yes, trust the given mode
            network_play = 1
        else:
            network_play = 0
            
        self.mode = mode   # setting global var to mode.

        if DEBUG:
            print 'MPlayer.play(): mode=%s, filename=%s' % (mode, filename)

        if mode == 'file' and not os.path.isfile(filename) and not network_play:
	    skin.PopupBox('%s\nnot found!' % os.path.basename(filename))
            time.sleep(2.0) 
            menuwidget.refresh()
            # XXX We should really use return more.
            return 0
       

        # Build the MPlayer command
        mpl = '--prio=%s %s %s' % (config.MPLAYER_NICE,
                                   config.MPLAYER_CMD,
                                   config.MPLAYER_ARGS_DEF)

        # XXX find a way to enable this for AVIs with ac3, too
        if (mode == 'dvdnav' or mode == 'dvd' or os.path.splitext(filename)[1] == '.vob')\
           and config.MPLAYER_AO_HWAC3_DEV:
            mpl += ' -ao %s -ac hwac3' % config.MPLAYER_AO_HWAC3_DEV
        else:
            mpl += ' -ao %s' % config.MPLAYER_AO_DEV


        if mode == 'file':
            default_args = config.MPLAYER_ARGS_MPG
        elif mode == 'dvdnav':
            default_args = config.MPLAYER_ARGS_DVDNAV
        elif mode == 'vcd':
            default_args = config.MPLAYER_ARGS_VCD % filename  # Filename is VCD chapter
        elif mode == 'dvd':
            default_args = config.MPLAYER_ARGS_DVD % filename  # Filename is DVD title
        else:
            print "Don't know what do play!"
            print "What is:      " + str(filename)
            print "What is mode: " + mode
            print "What is:      " + mpl
            return



            
        # Mplayer command and standard arguments
        mpl += (' ' + default_args + ' -v -vo ' + config.MPLAYER_VO_DEV)
            
        # XXX Some testcode by Krister:
        if os.path.isfile('./freevo_xwin') and osd.sdl_driver == 'x11' and \
           config.MPLAYER_USE_WID:
            if DEBUG: print 'Got freevo_xwin and x11'
            os.system('rm -f /tmp/freevo.wid')
            os.system('./freevo_xwin  0 0 %s %s > /tmp/freevo.wid &' %
                      (osd.width, osd.height))
            time.sleep(1)
            if os.path.isfile('/tmp/freevo.wid'):
                if DEBUG: print 'Got freevo.wid'
                try:
                    wid = int(open('/tmp/freevo.wid').read().strip(), 16)
                    mpl += ' -wid 0x%08x -xy %s -monitoraspect 4:3' % (wid, osd.width)
                    if DEBUG: print 'Got WID = 0x%08x' % wid
                except:
                    pass


        if mode == 'file':
            command = mpl + ' "' + filename + '"'
        else:
            command = mpl

        if options:
            print options
            command += ' ' + options
                
        self.file = item

        # XXX A better place for the major part of this code would be
        # XXX mixer.py
        if config.CONTROL_ALL_AUDIO:
            mixer.setLineinVolume(0)
            mixer.setMicVolume(0)
            if config.MAJOR_AUDIO_CTRL == 'VOL':
                mixer.setPcmVolume(config.MAX_VOLUME)
            elif config.MAJOR_AUDIO_CTRL == 'PCM':
                mixer.setMainVolume(config.MAX_VOLUME)
                
        mixer.setIgainVolume(0) # SB Live input from TV Card.
        # This should _really_ be set to zero when playing other audio.

        # clear the screen for mplayer
        osd.clearscreen(color=osd.COL_BLACK)
        osd.update()

        self.thread.play_mode = self.mode
        self.thread.item  = item
        self.item  = item
        
        if DEBUG:
            print 'MPlayer.play(): Starting thread, cmd=%s' % command
            
        self.thread.mode    = 'play'

        self.thread.command = command
        self.thread.mode_flag.set()
        rc.app = self.eventhandler


    def stop(self):
        """
        Stop mplayer and set thread to idle
        """
        self.thread.mode = 'stop'
        self.thread.mode_flag.set()
        rc.app = None
        while self.thread.mode == 'stop':
            time.sleep(0.3)
            

    def eventhandler(self, event):
        """
        eventhandler for mplayer control. If an event is not bound in this
        function it will be passed over to the items eventhandler
        """
        if event == rc.STOP or event == rc.SELECT:
            if self.mode == 'dvdnav':
                self.thread.app.write('S')
            else:
                self.stop()
                self.thread.item = None
                rc.app = None
                menuwidget.refresh()
            return TRUE
        
        if event == rc.PLAY_END:
            self.stop()
            rc.app = None
            return self.item.eventhandler(event)
            

        if event == rc.MENU:
            if self.mode == 'dvdnav':
                self.thread.app.write('M')
                return TRUE

        if event == rc.DISPLAY:
            self.thread.cmd( 'info' )
            return TRUE

        if event == rc.PAUSE or event == rc.PLAY:
            self.thread.cmd('pause')
            return TRUE

        if event == rc.FFWD:
            self.thread.cmd('skip_forward')
            return TRUE

        if event == rc.UP:
            if self.mode == 'dvdnav':
                self.thread.app.write('K')
                return TRUE

        if event == rc.REW:
            self.thread.cmd('skip_back')
            return TRUE

        if event == rc.DOWN:
            if self.mode == 'dvdnav':
                self.thread.app.write('J')
                return TRUE

        if event == rc.LEFT:
            if self.mode == 'dvdnav':
                self.thread.app.write('H')
            else:
                self.thread.cmd('skip_back2')
            return TRUE

        if event == rc.RIGHT:
            if self.mode == 'dvdnav':
                self.thread.app.write('L')
            else:
                self.thread.cmd('skip_forward2')
            return TRUE

        # nothing found? Try the eventhandler of the object who called us
        return self.item.eventhandler(event)

            
# ======================================================================


class MPlayerApp(childapp.ChildApp):
    """
    class controlling the in and output from the mplayer process
    """

    def __init__(self, app, item):
        self.item = item
        self.RE_AUDIO = re.compile("^\[open\] audio stream: [0-9] audio format:"+\
                                   "(.*)aid: ([0-9]*)").match
        self.RE_SUBTITLE = re.compile("^\[open\] subtitle.*: ([0-9]) language: "+\
                                      "([a-z][a-z])").match
        self.RE_CHAPTER = re.compile("^There are ([0-9]*) chapters in this DVD title.").match
        childapp.ChildApp.__init__(self, app)


    def kill(self):
        # Use SIGINT instead of SIGKILL to make sure MPlayer shuts
        # down properly and releases all resources before it gets
        # reaped by childapp.kill().wait()
        childapp.ChildApp.kill(self, signal.SIGINT)

        # XXX Krister testcode for proper X11 video
        if DEBUG: print 'Killing mplayer'
        os.system('killall -9 freevo_xwin 2&> /dev/null')
        os.system('rm -f /tmp/freevo.wid')



    def parse(self, str):
        m = self.RE_AUDIO(str)
        if m:
            self.item.available_audio_tracks += [ (m.group(2), m.group(1)) ]

        m = self.RE_SUBTITLE(str)
        if m:
            self.item.available_subtitles += [ (m.group(1), m.group(2)) ]

        m = self.RE_CHAPTER(str)
        if m:
            self.item.available_chapters = int(m.group(1))
        

    def stdout_cb(self, str):

        if config.MPLAYER_DEBUG:
            fd = open('./mplayer_stdout.log', 'a')
            fd.write(str + '\n')
            fd.close()
                     
        if str.find("A:") == 0:
            self.item.elapsed = str

        # this is the first start of the movie, parse infos
        elif not self.item.elapsed:
            self.parse(str)


    def stderr_cb(self, str):

        if config.MPLAYER_DEBUG:
            fd = open('./mplayer_stderr.log', 'a')
            fd.write(str + '\n')
            fd.close()
                     

# ======================================================================

class MPlayer_Thread(threading.Thread):
    """
    Thread to wait for a mplayer command to play
    """

    def __init__(self):
        threading.Thread.__init__(self)
        
        self.play_mode = ''
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

                # The DXR3 device cannot be shared between our SDL session
                # and MPlayer.
                if (osd.sdl_driver == 'dxr3'):
                    if DEBUG:
		        print "Stopping Display for Video Playback on DXR3"
                    osd.stopdisplay()
                
                if DEBUG:
                    print 'MPlayer_Thread.run(): Started, cmd=%s' % self.command
                    
                self.app = MPlayerApp(self.command, self.item)

                while self.mode == 'play' and self.app.isAlive():
                    time.sleep(0.1)

                self.app.kill()

                # Ok, we can use the OSD again.
                if osd.sdl_driver == 'dxr3':
                    osd.restartdisplay()
		    osd.update()
		    print "Display back online"

                if self.mode == 'play':
                    rc.post_event(rc.PLAY_END)

                self.mode = 'idle'
                
            else:
                self.mode = 'idle'


    def cmd(self, command):
        #print "In cmd going to do: " + command
        str = ''
        if command == 'info':
            str = mplayerKey('INFO')
        elif command == 'next':
            str = mplayerKey('NEXT')
        elif command == 'pause':
            str = mplayerKey('PAUSE')
        elif command == 'prev':
            str = mplayerKey('PREV')
        elif command == 'stop':
            str = mplayerKey('STOP')
        elif command == 'skip_forward':
            str = mplayerKey('RIGHT')
        elif command == 'skip_forward2':
            str = mplayerKey('UP')
        elif command == 'skip_forward3':
            str = mplayerKey('PAGEUP')
        elif command == 'skip_back':
            str = mplayerKey('LEFT')
        elif command == 'skip_back2':
            str = mplayerKey('DOWN')
        elif command == 'skip_back3':
            str = mplayerKey('PAGEDOWN')

        #print "In cmd going to write: " + str
        self.app.write(str) 


#
# Translate an abstract remote control command to an mplayer
# command key
#
def mplayerKey(rcCommand):
    mplayerKeys = {
        'DOWN'           : '\x1bOB',
        'INFO'           : 'o',
        'KEY_1'          : '+',
        'KEY_7'          : '-',
        'LEFT'           : '\x1bOD',
        'NONE'           : '',
        'NEXT'           : '>',
        'QUIT'           : 'q',
        'PAGEUP'         : '\x1b[5~',
        'PAGEDOWN'       : '\x1b[6~',
        'PAUSE'          : ' ',
        'PLAY'           : ' ',
        'PREV'           : '<',
        'RIGHT'          : '\x1bOC',
        'STOP'           : 'q',
        'UP'             : '\x1bOA',
        'VOLUMEUP'       : '*',
        'VOLUMEDOWN'     : '/',
        'DISPLAY'        : 'o'
        }
    
    key = mplayerKeys.get(rcCommand, '')

    return key


