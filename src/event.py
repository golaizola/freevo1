# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# Global events for Freevo
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

"""
Global events for Freevo
"""
import kaa

class Event(kaa.Event):
    """
    an event is passed to the different eventhandlers in Freevo to
    activate some action.
    """
    def __init__(self, name, arg=None, context=None, handler=None):
        if isinstance(name, Event):
            self.name    = name.name
            self.arg     = name.arg
            self.context = name.context
            self.handler = name.handler
        else:
            self.name    = name
            self.arg     = None
            self.context = None
            self.handler = None

        if arg or arg == 0:
            self.arg = arg

        if context:
            self.context = context

        if handler:
            self.handler = handler


    def __str__(self):
        """
        return the event as string
        """
        return self.name


    def __repr__(self):
        """
        return the offical representation of the object as string
        """
        return '%s: %r' % (self.name, self.__class__)


    def __int__(self):
        """
        return the event as int (the last char of the name will be returned
        as integer value
        """
        return int(self.name[-1])


    def __cmp__(self, other):
        """
        compare function, return 0 if the objects are identical, 1 otherwise
        """
        if not other:
            return 1
        if isinstance(other, Event):
            return self.name != other.name
        return self.name != other




#
# Default actions Freevo knows
#

MIXER_VOLUP            = Event('MIXER_VOLUP', arg=5)
MIXER_VOLDOWN          = Event('MIXER_VOLDOWN', arg=5)
MIXER_MUTE             = Event('MIXER_MUTE')

FULLSCREEN_TOGGLE      = Event('FULLSCREEN_TOGGLE')
HELP_TOGGLE            = Event('HELP_TOGGLE')
SCREENSHOT             = Event('SCREENSHOT')

# Events for 6-channel audio control.
MIXER_SUR_VOLUP        = Event('MIXER_SUR_VOLUP', arg=5)
MIXER_SUR_VOLDOWN      = Event('MIXER_SUR_VOLDOWN', arg=5)
MIXER_CTR_VOLUP        = Event('MIXER_CTR_VOLUP', arg=5)
MIXER_CTR_VOLDOWN      = Event('MIXER_CTR_VOLDOWN', arg=5)
MIXER_LFE_VOLUP        = Event('MIXER_LFE_VOLUP', arg=5)
MIXER_LFE_VOLDOWN      = Event('MIXER_LFE_VOLDOWN', arg=5)

# To change the step size, put the following code in your
# local_conf.py (setting VOL+ step size to 2)
#
# EVENTS['global']['VOL+'] = Event('MIXER_VOLUP', arg=2)


PLAYLIST_NEXT          = Event('PLAYLIST_NEXT')
PLAYLIST_PREV          = Event('PLAYLIST_PREV')
PLAYLIST_TOGGLE_REPEAT = Event('PLAYLIST_TOGGLE_REPEAT')

EJECT                  = Event('EJECT')

#
# Menu
#

MENU_LEFT              = Event('MENU_LEFT')
MENU_RIGHT             = Event('MENU_RIGHT')
MENU_UP                = Event('MENU_UP')
MENU_DOWN              = Event('MENU_DOWN')
MENU_PAGEUP            = Event('MENU_PAGEUP')
MENU_PAGEDOWN          = Event('MENU_PAGEDOWN')
MENU_REBUILD           = Event('MENU_REBUILD')

MENU_GOTO_MAINMENU     = Event('MENU_GOTO_MAINMENU')
MENU_GOTO_TV           = Event('MENU_GOTO_TV')
MENU_GOTO_TVGUIDE      = Event('MENU_GOTO_TVGUIDE')
MENU_GOTO_VIDEOS       = Event('MENU_GOTO_VIDEOS')
MENU_GOTO_MUSIC        = Event('MENU_GOTO_MUSIC')
MENU_GOTO_IMAGES       = Event('MENU_GOTO_IMAGES')
MENU_GOTO_GAMES        = Event('MENU_GOTO_GAMES')
MENU_GOTO_RADIO        = Event('MENU_GOTO_RADIO')
MENU_GOTO_SHUTDOWN     = Event('MENU_GOTO_SHUTDOWN')
MENU_BACK_ONE_MENU     = Event('MENU_BACK_ONE_MENU')

MENU_SELECT            = Event('MENU_SELECT')
MENU_PLAY_ITEM         = Event('MENU_PLAY_ITEM')
MENU_SUBMENU           = Event('MENU_SUBMENU')
MENU_CALL_ITEM_ACTION  = Event('MENU_CALL_ITEM_ACTION')
MENU_CHANGE_STYLE      = Event('MENU_CHANGE_STYLE')

DIRECTORY_CHANGE_DISPLAY_TYPE = Event('DIRECTORY_CHANGE_DISPLAY_TYPE')

#
# Dialog
#
DIALOG_SHOW = Event('DIALOG_SHOW')
DIALOG_STOP = Event('DIALOG_STOP')
DIALOG_HIDE = Event('DIALOG_HIDE')

#
# TV module
#

TV_START_RECORDING     = Event('TV_START_RECORDING')
TV_CHANNEL_UP          = Event('TV_CHANNEL_UP')
TV_CHANNEL_DOWN        = Event('TV_CHANNEL_DOWN')
TV_CHANNEL_LAST        = Event('TV_CHANNEL_LAST')
TV_SEND_TVTIME_CMD     = Event('TV_SEND_TVTIME_CMD')
TV_SEND_MPLAYER_CMD    = Event('TV_SEND_MPLAYER_CMD')
TV_GOTO_LIVE_PLAY      = Event('TV_GOTO_LIVE_PLAY')
VIDEO_NEXT_FILLMODE    = Event('VIDEO_NEXT_FILLMODE')
VIDEO_NEXT_AUDIOMODE   = Event('VIDEO_NEXT_AUDIOMODE')

#
# Global playing events
#

SEEK                   = Event('SEEK')
PLAY                   = Event('PLAY')
PAUSE                  = Event('PAUSE')
STOP                   = Event('STOP')
TOGGLE_OSD             = Event('TOGGLE_OSD')

#
# Video module
VIDEO_ASPECT           = Event('VIDEO_ASPECT')
#

VIDEO_SEND_MPLAYER_CMD = Event('VIDEO_SEND_MPLAYER_CMD')
VIDEO_SEND_XINE_CMD    = Event('VIDEO_SEND_XINE_CMD')
VIDEO_MANUAL_SEEK      = Event('VIDEO_MANUAL_SEEK')
VIDEO_NEXT_AUDIOLANG   = Event('VIDEO_NEXT_AUDIOLANG')
VIDEO_NEXT_SUBTITLE    = Event('VIDEO_NEXT_SUBTITLE')
VIDEO_TOGGLE_INTERLACE = Event('VIDEO_TOGGLE_INTERLACE')
VIDEO_NEXT_ANGLE       = Event('VIDEO_NEXT_ANGLE')
VIDEO_AVSYNC           = Event('VIDEO_AVSYNC')
VIDEO_SUBSYNC          = Event('VIDEO_SUBSYNC')
STORE_BOOKMARK         = Event('STORE_BOOKMARK')
MENU                   = Event('MENU')

DVDNAV_LEFT            = Event('DVDNAV_LEFT')
DVDNAV_RIGHT           = Event('DVDNAV_RIGHT')
DVDNAV_UP              = Event('DVDNAV_UP')
DVDNAV_DOWN            = Event('DVDNAV_DOWN')
DVDNAV_SELECT          = Event('DVDNAV_SELECT')
DVDNAV_TITLEMENU       = Event('DVDNAV_TITLEMENU')
DVDNAV_MENU            = Event('DVDNAV_MENU')
NEXT                   = Event('NEXT')
PREV                   = Event('PREV')


#
# Audio module
#

AUDIO_SEND_MPLAYER_CMD = Event('AUDIO_SEND_MPLAYER_CMD')
AUDIO_LOG              = Event('AUDIO_LOG')


#
# Image module
#
IMAGE_ZOOM_LEVEL_1     = Event('IMAGE_ZOOM_LEVEL_1')
IMAGE_ZOOM_LEVEL_2     = Event('IMAGE_ZOOM_LEVEL_2')
IMAGE_ZOOM_LEVEL_3     = Event('IMAGE_ZOOM_LEVEL_3')
IMAGE_ZOOM_LEVEL_4     = Event('IMAGE_ZOOM_LEVEL_4')
IMAGE_ZOOM_LEVEL_5     = Event('IMAGE_ZOOM_LEVEL_5')
IMAGE_ZOOM_LEVEL_6     = Event('IMAGE_ZOOM_LEVEL_6')
IMAGE_ZOOM_LEVEL_7     = Event('IMAGE_ZOOM_LEVEL_7')
IMAGE_ZOOM_LEVEL_8     = Event('IMAGE_ZOOM_LEVEL_8')
IMAGE_ZOOM_LEVEL_9     = Event('IMAGE_ZOOM_LEVEL_9')
IMAGE_ZOOM_BEST_FIT    = Event('IMAGE_ZOOM_BEST_FIT')
IMAGE_ZOOM_NO_ZOOM     = Event('IMAGE_ZOOM_NO_ZOOM')
IMAGE_ZOOM_LEVEL_UP    = Event('IMAGE_ZOOM_LEVEL_UP')
IMAGE_ZOOM_LEVEL_DOWN  = Event('IMAGE_ZOOM_LEVEL_DOWN')

IMAGE_ROTATE           = Event('IMAGE_ROTATE')
IMAGE_SAVE             = Event('IMAGE_SAVE')

IMAGE_MOVE             = Event('IMAGE_MOVE')
IMAGE_TAG              = Event('IMAGE_TAG')

#
# Games module
#

GAMES_CONFIG           = Event('GAMES_CONFIG')
GAMES_RESET            = Event('GAMES_RESET')
GAMES_SNAPSHOT         = Event('GAMES_SNAPSHOT')


#
# Input boxes
#

INPUT_EXIT             = Event('INPUT_EXIT')
INPUT_ENTER            = Event('INPUT_ENTER')
INPUT_LEFT             = Event('INPUT_LEFT')
INPUT_RIGHT            = Event('INPUT_RIGHT')
INPUT_UP               = Event('INPUT_UP')
INPUT_DOWN             = Event('INPUT_DOWN')
INPUT_1                = Event('INPUT_1', arg=1)
INPUT_2                = Event('INPUT_2', arg=2)
INPUT_3                = Event('INPUT_3', arg=3)
INPUT_4                = Event('INPUT_4', arg=4)
INPUT_5                = Event('INPUT_5', arg=5)
INPUT_6                = Event('INPUT_6', arg=6)
INPUT_7                = Event('INPUT_7', arg=7)
INPUT_8                = Event('INPUT_8', arg=8)
INPUT_9                = Event('INPUT_9', arg=9)
INPUT_0                = Event('INPUT_0', arg=0)

INPUT_ALL_NUMBERS = (INPUT_0, INPUT_1, INPUT_2, INPUT_3, INPUT_4, INPUT_5, INPUT_6, INPUT_7, INPUT_8, INPUT_9)


# Call the function specified in event.arg
FUNCTION_CALL          = Event('FUNCTION_CALL')

# All buttons which are not mapped to an event will be send as
# BOTTON event with the pressed button as arg
BUTTON                 = Event('BUTTON')
RATING                 = Event('RATING')



#
# Default key-event map
#

MENU_EVENTS = {
    'LEFT'      : MENU_LEFT,
    'RIGHT'     : MENU_RIGHT,
    'UP'        : MENU_UP,
    'DOWN'      : MENU_DOWN,
    'CH+'       : MENU_PAGEUP,
    'CH-'       : MENU_PAGEDOWN,
    'MENU'      : MENU_GOTO_MAINMENU,
    'TV'        : MENU_GOTO_TV,
    'MUSIC'     : MENU_GOTO_MUSIC,
    'VIDEOS'    : MENU_GOTO_VIDEOS,
    'PICTURES'  : MENU_GOTO_IMAGES,
    'SHUTDOWN'  : MENU_GOTO_SHUTDOWN,
    'EXIT'      : MENU_BACK_ONE_MENU,
    'SELECT'    : MENU_SELECT,
    'PLAY'      : MENU_PLAY_ITEM,
    'ENTER'     : MENU_SUBMENU,
    'DISPLAY'   : MENU_CHANGE_STYLE,
    'EJECT'     : EJECT
    }

TVMENU_EVENTS = {
    'LEFT'      : MENU_LEFT,
    'RIGHT'     : MENU_RIGHT,
    'UP'        : MENU_UP,
    'DOWN'      : MENU_DOWN,
    'CH+'       : MENU_PAGEUP,
    'CH-'       : MENU_PAGEDOWN,
    'MENU'      : MENU_GOTO_MAINMENU,
    'SHUTDOWN'  : MENU_GOTO_SHUTDOWN,
    'EXIT'      : MENU_BACK_ONE_MENU,
    'SELECT'    : MENU_SELECT,
    'ENTER'     : MENU_SUBMENU,
    'DISPLAY'   : MENU_CHANGE_STYLE,
    'PLAY'      : PLAY,
    'REC'       : TV_START_RECORDING
    }

INPUT_EVENTS = {
    'EXIT'      : INPUT_EXIT,
    'ENTER'     : INPUT_ENTER,
    'SELECT'    : INPUT_ENTER,
    'LEFT'      : INPUT_LEFT,
    'RIGHT'     : INPUT_RIGHT,
    'UP'        : INPUT_UP,
    'DOWN'      : INPUT_DOWN,
    '1'         : INPUT_1,
    '2'         : INPUT_2,
    '3'         : INPUT_3,
    '4'         : INPUT_4,
    '5'         : INPUT_5,
    '6'         : INPUT_6,
    '7'         : INPUT_7,
    '8'         : INPUT_8,
    '9'         : INPUT_9,
    '0'         : INPUT_0,
    'CH+'       : MENU_PAGEUP,
    'CH-'       : MENU_PAGEDOWN
    }

TV_EVENTS = {
    'STOP'      : STOP,
    'MENU'      : STOP,
    'EXIT'      : STOP,
    'SELECT'    : STOP,
    'PAUSE'     : PAUSE,
    'CH+'       : TV_CHANNEL_UP,
    'CH-'       : TV_CHANNEL_DOWN,
    'PREV_CH'   : TV_CHANNEL_LAST,
    'LEFT'      : Event(SEEK, arg=-60),
    'RIGHT'     : Event(SEEK, arg=60),
    'REW'       : Event(SEEK, arg=-10),
    'FFWD'      : Event(SEEK, arg=10),
    'DISPLAY'   : TOGGLE_OSD,
    'REC'       : TV_START_RECORDING,
    '0'         : INPUT_0,
    '1'         : INPUT_1,
    '2'         : INPUT_2,
    '3'         : INPUT_3,
    '4'         : INPUT_4,
    '5'         : INPUT_5,
    '6'         : INPUT_6,
    '7'         : INPUT_7,
    '8'         : INPUT_8,
    '9'         : INPUT_9,
    }

VIDEO_EVENTS = {
    'PLAY'      : PLAY,
    'PAUSE'     : PAUSE,
    'STOP'      : STOP,
    'EXIT'      : STOP,
    'UP'        : PLAYLIST_PREV,
    'DOWN'      : PLAYLIST_NEXT,
    'CH+'       : PLAYLIST_PREV,
    'CH-'       : PLAYLIST_NEXT,
    'LEFT'      : Event(SEEK, arg=-60),
    'RIGHT'     : Event(SEEK, arg=60),
    'REW'       : Event(SEEK, arg=-10),
    'FFWD'      : Event(SEEK, arg=10),
    'NEXT'      : NEXT,
    'PREV'      : PREV,
    'MENU'      : MENU,
    'DISPLAY'   : TOGGLE_OSD,
    'REC'       : STORE_BOOKMARK,
    '0'         : VIDEO_MANUAL_SEEK,
    'LANG'      : VIDEO_NEXT_AUDIOLANG,
    'SUBTITLE'  : VIDEO_NEXT_SUBTITLE,
    'AVSYNC+'   : Event(VIDEO_AVSYNC, arg=0.100),
    'AVSYNC-'   : Event(VIDEO_AVSYNC, arg=-0.100),
    'ASPECT'    : VIDEO_ASPECT,
    }

DVD_EVENTS = {
    'PLAY'      : PLAY,
    'PAUSE'     : PAUSE,
    'STOP'      : STOP,
    'EXIT'      : STOP,
    'UP'        : DVDNAV_UP,
    'DOWN'      : DVDNAV_DOWN,
    'LEFT'      : DVDNAV_LEFT,
    'RIGHT'     : DVDNAV_RIGHT,
    'ENTER'     : DVDNAV_SELECT,
    'SELECT'    : DVDNAV_SELECT,
    'DISPLAY'   : TOGGLE_OSD,
    'REW'       : Event(SEEK, arg=-10),
    'FFWD'      : Event(SEEK, arg=10),
    'GUIDE'     : DVDNAV_TITLEMENU,
    'MENU'      : DVDNAV_MENU,
    'LANG'      : VIDEO_NEXT_AUDIOLANG,
    'SUBTITLE'  : VIDEO_NEXT_SUBTITLE,
    'ANGLE'     : VIDEO_NEXT_ANGLE,
    'NEXT'      : NEXT,
    'PREV'      : PREV,
    'CH+'       : NEXT,
    'CH-'       : PREV
    }

VCD_EVENTS = {
    'PLAY'      : PLAY,
    'PAUSE'     : PAUSE,
    'STOP'      : STOP,
    'EXIT'      : STOP,
    'LEFT'      : Event(SEEK, arg=-60),
    'RIGHT'     : Event(SEEK, arg=60),
    'REW'       : Event(SEEK, arg=-10),
    'FFWD'      : Event(SEEK, arg=10),
    'NEXT'      : NEXT,
    'PREV'      : PREV,
    'MENU'      : MENU,
    'DISPLAY'   : TOGGLE_OSD,
    'LANG'      : VIDEO_NEXT_AUDIOLANG,
    'SUBTITLE'  : VIDEO_NEXT_SUBTITLE,
    'ANGLE'     : VIDEO_NEXT_ANGLE,
    '1'         : INPUT_1,
    '2'         : INPUT_2,
    '3'         : INPUT_3,
    '4'         : INPUT_4,
    '5'         : INPUT_5,
    '6'         : INPUT_6,
    '7'         : INPUT_7,
    '8'         : INPUT_8,
    '9'         : INPUT_9
    }

AUDIO_EVENTS = {
    'STOP'      : STOP,
    'EXIT'      : STOP,
    'PLAY'      : PLAY,
    'PAUSE'     : PAUSE,
    'LEFT'      : Event(SEEK, arg=-60),
    'RIGHT'     : Event(SEEK, arg=60),
    'REW'       : Event(SEEK, arg=-10),
    'FFWD'      : Event(SEEK, arg=10),
    'UP'        : PLAYLIST_PREV,
    'DOWN'      : PLAYLIST_NEXT,
    'CH+'       : PLAYLIST_PREV,
    'CH-'       : PLAYLIST_NEXT,
    '1'         : INPUT_1,
    '2'         : INPUT_2,
    '3'         : INPUT_3,
    '4'         : INPUT_4,
    '5'         : INPUT_5,
    '6'         : INPUT_6,
    '7'         : INPUT_7,
    '8'         : INPUT_8,
    '9'         : INPUT_9,
    }

IMAGE_EVENTS = {
    'STOP'      : STOP,
    'EXIT'      : STOP,
    'PLAY'      : PLAY,
    'PAUSE'     : PAUSE,
    'LEFT'      : Event(IMAGE_ROTATE, arg='left'),
    'RIGHT'     : Event(IMAGE_ROTATE, arg='right'),
    'UP'        : PLAYLIST_PREV,
    'DOWN'      : PLAYLIST_NEXT,
    '1'         : IMAGE_ZOOM_NO_ZOOM,
    '2'         : IMAGE_ZOOM_LEVEL_2,
    '3'         : IMAGE_ZOOM_LEVEL_3,
    '4'         : IMAGE_ZOOM_LEVEL_4,
    '5'         : IMAGE_ZOOM_LEVEL_5,
    '6'         : IMAGE_ZOOM_LEVEL_6,
    '7'         : IMAGE_ZOOM_LEVEL_7,
    '8'         : IMAGE_ZOOM_LEVEL_8,
    '9'         : IMAGE_ZOOM_LEVEL_9,
    '0'         : IMAGE_ZOOM_BEST_FIT,
    'PREV'      : IMAGE_ZOOM_LEVEL_DOWN,
    'NEXT'      : IMAGE_ZOOM_LEVEL_UP,
    'DISPLAY'   : TOGGLE_OSD,
    'REC'       : IMAGE_SAVE,
    'ENTER'     : IMAGE_TAG,
    'CH+'       : PLAYLIST_PREV,
    'CH-'       : PLAYLIST_NEXT
    }

IMAGE_ZOOM_EVENTS = {
    'STOP'      : STOP,
    'EXIT'      : STOP,
    'PLAY'      : PLAY,
    'PAUSE'     : PAUSE,
    'LEFT'      : Event(IMAGE_MOVE, arg=( -10,   0)),
    'RIGHT'     : Event(IMAGE_MOVE, arg=(  10,   0)),
    'UP'        : Event(IMAGE_MOVE, arg=(   0, -10)),
    'DOWN'      : Event(IMAGE_MOVE, arg=(   0,  10)),
    '1'         : IMAGE_ZOOM_NO_ZOOM,
    '2'         : IMAGE_ZOOM_LEVEL_2,
    '3'         : IMAGE_ZOOM_LEVEL_3,
    '4'         : IMAGE_ZOOM_LEVEL_4,
    '5'         : IMAGE_ZOOM_LEVEL_5,
    '6'         : IMAGE_ZOOM_LEVEL_6,
    '7'         : IMAGE_ZOOM_LEVEL_7,
    '8'         : IMAGE_ZOOM_LEVEL_8,
    '9'         : IMAGE_ZOOM_LEVEL_9,
    '0'         : IMAGE_ZOOM_BEST_FIT,
    'PREV'      : IMAGE_ZOOM_LEVEL_DOWN,
    'NEXT'      : IMAGE_ZOOM_LEVEL_UP,
    'DISPLAY'   : TOGGLE_OSD,
    'REC'       : IMAGE_SAVE,
    'CH+'       : PLAYLIST_PREV,
    'CH-'       : PLAYLIST_NEXT
    }

GAMES_EVENTS = {
    'STOP'      : STOP,
    'SELECT'    : STOP,
    'MENU'      : MENU,
    'DISPLAY'   : GAMES_CONFIG,
    'ENTER'     : GAMES_RESET
}

GLOBAL_EVENTS = {
    'VOL+'      : MIXER_VOLUP,
    'VOL-'      : MIXER_VOLDOWN,
    'MUTE'      : MIXER_MUTE,
    'HELP'      : HELP_TOGGLE,
    'FULLSCREEN': FULLSCREEN_TOGGLE,
    'SCREENSHOT': SCREENSHOT
    }


import pygame.locals as key

DEFAULT_KEYMAP = {
    key.K_F1          : 'SLEEP',
    key.K_HOME        : 'MENU',
    key.K_g           : 'GUIDE',
    key.K_ESCAPE      : 'EXIT',
    key.K_UP          : 'UP',
    key.K_DOWN        : 'DOWN',
    key.K_LEFT        : 'LEFT',
    key.K_RIGHT       : 'RIGHT',
    key.K_SPACE       : 'SELECT',
    key.K_RETURN      : 'SELECT',
    key.K_F2          : 'POWER',
    key.K_F3          : 'MUTE',
    key.K_KP_MINUS    : 'VOL-',
    key.K_n           : 'VOL-',
    key.K_KP_PLUS     : 'VOL+',
    key.K_m           : 'VOL+',
    key.K_c           : 'CH+',
    key.K_v           : 'CH-',
    key.K_1           : '1',
    key.K_2           : '2',
    key.K_3           : '3',
    key.K_4           : '4',
    key.K_5           : '5',
    key.K_6           : '6',
    key.K_7           : '7',
    key.K_8           : '8',
    key.K_9           : '9',
    key.K_0           : '0',
    key.K_d           : 'DISPLAY',
    key.K_e           : 'ENTER',
    key.K_UNDERSCORE  : 'PREV_CH',
    key.K_o           : 'PIP_ONOFF',
    key.K_w           : 'PIP_SWAP',
    key.K_i           : 'PIP_MOVE',
    key.K_F4          : 'TV_VCR',
    key.K_r           : 'REW',
    key.K_p           : 'PLAY',
    key.K_f           : 'FFWD',
    key.K_u           : 'PAUSE',
    key.K_s           : 'STOP',
    key.K_F6          : 'REC',
    key.K_PERIOD      : 'EJECT',
    key.K_l           : 'SUBTITLE',
    key.K_a           : 'LANG',
    key.K_RIGHTBRACKET: 'NEXT',
    key.K_LEFTBRACKET : 'PREV',
    key.K_z           : 'FULLSCREEN',
    key.K_h           : 'HELP',
    key.K_F10         : 'SCREENSHOT'
    }


DEFAULT_EVENTMAP = {
    'KEY_F1'          : 'SLEEP',
    'KEY_HOME'        : 'MENU',
    'KEY_G'           : 'GUIDE',
    'KEY_ESC'         : 'EXIT',
    'KEY_UP'          : 'UP',
    'KEY_DOWN'        : 'DOWN',
    'KEY_LEFT'        : 'LEFT',
    'KEY_RIGHT'       : 'RIGHT',
    'KEY_OK'          : 'SELECT',
    'KEY_SPACE'       : 'SELECT',
    'KEY_ENTER'       : 'SELECT',
    'KEY_KPENTER'     : 'SELECT',
    'KEY_POWER'       : 'POWER',
    'KEY_F2'          : 'POWER',
    'KEY_MUTE'        : 'MUTE',
    'KEY_F3'          : 'MUTE',
    'KEY_VOLUMEDOWN'  : 'VOL-',
    'KEY_KPMINUS'     : 'VOL-',
    'KEY_N'           : 'VOL-',
    'KEY_VOLUMEUP'    : 'VOL+',
    'KEY_KPPLUS'      : 'VOL+',
    'KEY_M'           : 'VOL+',
    'KEY_CHANNELUP'   : 'CH+',
    'KEY_C'           : 'CH+',
    'KEY_CHANNELDOWN' : 'CH-',
    'KEY_V'           : 'CH-',
    'KEY_1'           : '1',
    'KEY_2'           : '2',
    'KEY_3'           : '3',
    'KEY_4'           : '4',
    'KEY_5'           : '5',
    'KEY_6'           : '6',
    'KEY_7'           : '7',
    'KEY_8'           : '8',
    'KEY_9'           : '9',
    'KEY_0'           : '0',
    'KEY_VENDOR'      : 'DISPLAY',
    'KEY_D'           : 'DISPLAY',
    'KEY_MENU'        : 'ENTER',
    'KEY_E'           : 'ENTER',
    'KEY_MINUS'       : 'PREV_CH',
    'KEY_O'           : 'PIP_ONOFF',
    'KEY_W'           : 'PIP_SWAP',
    'KEY_I'           : 'PIP_MOVE',
    'KEY_F4'          : 'TV_VCR',
    'KEY_REWIND'      : 'REW',
    'KEY_R'           : 'REW',
    'KEY_PLAY'        : 'PLAY',
    'KEY_P'           : 'PLAY',
    'KEY_FORWARD'     : 'FFWD',
    'KEY_F'           : 'FFWD',
    'KEY_PAUSE'       : 'PAUSE',
    'KEY_U'           : 'PAUSE',
    'KEY_STOP'        : 'STOP',
    'KEY_S'           : 'STOP',
    'KEY_RECORD'      : 'RECORD',
    'KEY_F6'          : 'REC',
    'KEY_PERIOD'      : 'EJECT',
    'KEY_L'           : 'SUBTITLE',
    'KEY_A'           : 'LANG',

    'REL_X'           : ('LEFT', 'RIGHT'),
    'REL_Y'           : ('UP', 'DOWN'),

    'BTN_LEFT'        : 'SELECT',
    'BTN_RIGHT'       : 'EXIT',
    }



#
# Internal events, don't map any button on them
#

FREEVO_READY     = Event('FREEVO_READY')

VIDEO_START      = Event('VIDEO_START')
VIDEO_END        = Event('VIDEO_END')
PLAY_START       = Event('PLAY_START')
PLAY_END         = Event('PLAY_END')
USER_END         = Event('USER_END')

DVD_PROTECTED    = Event('DVD_PROTECTED')

OSD_MESSAGE      = Event('OSD_MESSAGE')

OS_EVENT_POPEN2  = Event('OS_EVENT_POPEN2')
OS_EVENT_WAITPID = Event('OS_EVENT_WAITPID')
OS_EVENT_KILL    = Event('OS_EVENT_KILL')

RECORD_START     = Event('RECORD_START')
RECORD_STOP      = Event('RECORD_STOP')

MENU_PROCESS_END = Event('MENU_PROCESS_END')

MOUSE_BTN_PRESS  = Event('MOUSE_BTN_PRESS')
MOUSE_BTN_RELEASE= Event('MOUSE_BTN_RELEASE')
MOUSE_MOTION     = Event('MOUSE_MOTION')
