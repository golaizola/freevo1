# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# Use PyLCD to display menus and players
# -----------------------------------------------------------------------
# $Id$
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
Plug-in to display menus and players on a LCD display

To activate, put the following line in local_conf.py::

    plugin.activate('lcd')

Todo:
    1. Use Threads. PyLCD is too blocking!
    2. Have Movie Player, TV Player and Image viewer to use LCD
    3. Better (and more) LCD screens.
"""
import logging
logger = logging.getLogger("freevo.plugins.lcd")

import string

from menu import MenuItem
import copy
import time
import plugin
from event import *
import config
import util
from util.tv_util import get_chan_displayname

if config.LCD_REMAP_TO_ASCII:
    try:
        from unidecode import unidecode
    except:
        logger.log( 9, String(_('ERROR') + ': ' + _('You need unidecode to run "lcd" plugin.')))

try:
    import pylcd
except:
    logger.log( 9, String(_('ERROR') + ': ' + _('You need pylcd to run "lcd" plugin.')))


# Configuration: (Should move to freevo_conf.py?)
sep_str = ' | ' # use as separator between two strings. Like: 'Length: 123<sep_str>Plot: ...'
sep_str_mscroll = '   ' # if string > width of lcd add this

def rjust(s, n):
    logger.log( 9, 'rjust(s, n)')
    return s[: n].rjust(n)

# menu_info: information to be shown when in menu
# Structure:
#
# menu_info = {
#     <TYPE> : [(<ATTRIBUTE>, <FORMAT_STRING>), ...],
#    }
# <ATTRIBUTE> is some valid attribute to item.getattr()
menu_info = {
    'main' : [],
    'audio' : [
        ('length', _('Length') + ': %s'),
        ('artist', _('Artist') + ': %s'),
        ('album', _('Album')   + ': %s'),
        ('year', _('Year')     + ': %s'),
    ],
    'audiocd' : [
        ('len(tracks)', _('Tracks') + ': %s'),
        ('artist', _('Artist') + ': %s'),
        ('album', _('Album')   + ': %s'),
        ('year', _('Year')     + ': %s'),
    ],
    'video' : [
        ('length', _('Length') + ': %s'),
        ('geometry', _('Resolution') + ': %s'),
        ('aspect', _('Aspect') + ': %s'),
        ('tagline', _('Tagline') + ': %s'),
        ('plot', _('Plot')       + ': %s'),
    ],
    'dir' : [
        ('plot', _('Plot') + ': %s'),
        ('tagline', _('Tagline') + ': %s'),
    ],
    'image' : [
        ('geometry', _('Geometry') + ': %s'),
        ('date', _('Date') + ': %s'),
        ('description', _('Description') + ': %s'),
    ],
    'playlist' : [
        ('len(playlist)', _('%s items')),
    ],
    'mame' : [
        ('description', _('Description') + ': %s'),
    ],
    'unknow' : []
}
# menu_strinfo: will be passed to time.strinfo() and added to the end of info (after menu_info)
menu_strinfo = {
    'main' : '%H:%M - %a, %d-%b', # I like time in main menu
    'audio' : None,
    'audiocd' : None,
    'video' : None,
    'image' : None,
    'dir' : None,
    'playlist' : None,
    'mame' : None,
    'unknow' : None
    }


# layouts: dict of layouts (screens and widgets)
# Structure:
#
# layouts = {
#     <#_OF_LINES_IN_DISPLAY> : {
#         <#_OF_CHARS_IN_LINES> : {
#             <SCREEN_NAME> :
#                 <WIDGET_NAME> : (<WIDGET_TYPE>, <WIDGET_PARAMETERS>, <PARAMETERS_VALUES>),
#                 <MORE_WIDGETS>...
#         },
#         <MORE_SCREENS>...
#     }
# }
# Note:
#    <PARAMETERS_VALUES>: will be used like this:
#       <WIDGET_PARAMETERS> % eval(<PARAMETERS_VALUES>)
#    There should be at least these screens:
#       welcome: will be the shown during the startup
#          menu: will be used in menu mode
#        player: will be used in player mode
#            tv: will be used in tv mode
# Values should match the ones supported by LCDd (man LCDd)
layouts = {
    4 : { # 4 lines display
        40 : { # 40 chars per line
            'welcome'        : {
                'title'      : ('title', 'Freevo', None),
                'calendar'   : ('scroller', '1 2 %d 2 m 3 "' + _('Today is %s.') + '%s"',
                    '(self.width, time.strftime("%A, %d-%B"), self.get_sepstrmscroll(time.strftime("%A, %d-%B")))'),
                'clock'      : ('string', '%d 3 "%s"',
                    '((self.width - len(time.strftime("%T"))) / 2 + 1, time.strftime("%T"))')
            },
            'menu'           : {
                'title_l'    : ('string', '1 1 "' + rjust(_('Menu'), 4) + ': "', None),
                'item_l'     : ('string', '1 2 "' + rjust(_('Item'), 4) + ': "', None),
                'type_l'     : ('string', '1 3 "' + rjust(_('Type'), 4) + ': "', None),
                'info_l'     : ('string', '1 4 "' + rjust(_('Information'), 4) + ': "', None),
                'title_v'    : ('scroller', '7 1 %d 1 m 3 "%s%s"',
                    '(self.width, menu.heading, self.get_sepstrmscroll(menu.heading))'),
                'item_v'     : ('scroller', '7 2 %d 2 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))'),
                'type_v'     : ('scroller', '7 3 %d 3 m 3 "%s%s"',
                    '(self.width, typeinfo, self.get_sepstrmscroll(typeinfo))'),
                'info_v'     : ('scroller', '7 4 %d 1 m 3 "%s%s"', '(self.width, info, self.get_sepstrmscroll(info))')
            },
            'audio_player'   : {
                'music_l'    : ('string', '1 1 "' + rjust(_('Music'), 5) + ': "', None),
                'album_l'    : ('string', '1 2 "' + rjust(_('Album'), 5) + ': "', None),
                'artist_l'   : ('string', '1 3 "' + rjust(_('Artist'), 5) + ': "', None),
                'music_v'    : ('scroller', '9 1 %d 1 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))'),
                'album_v'    : ('scroller', '9 2 %d 2 m 3 "%s%s"',
                    '(self.width, player.getattr("album"), self.get_sepstrmscroll(player.getattr("album")))'),
                'artist_v'   : ('scroller', '9 3 %d 3 m 3 "%s%s"',
                    '(self.width, player.getattr("artist"), self.get_sepstrmscroll(player.getattr("artist")))'),
                'time_v1'    : ('string', '2 4 "%2d:%02d"', '(int(player.length / 60), int(player.length % 60))'),
                'time_v2'    : ('string', '8 4 "%2d:%02d"', '(int(player.elapsed / 60), int(player.elapsed % 60))'),
                'time_v3'    : ('string', '14 4 "(%2d%%)"', '(int(player.elapsed * 100 / player.length))'),
                'timebar1_v' : ('string', '21 4 "["', None),
                'timebar2_v' : ('string', '40 4 "]"', None),
                'timebar3_v' : ('hbar', '22 4 "%d"', '(int(player.elapsed * 90 / player.length))'),
                'animation_v': ('string', '1 4 "%s"',
                    'self.animation_audioplayer_chars[player.elapsed % len(self.animation_audioplayer_chars)]')
            },
            'video_player'   : {
                'video_l'    : ('string', '2 1 "' + rjust(_('Video'), 5) + ': "', None),
                'tag_l'      : ('string', '2 2 "' + rjust(_('Tagline'), 5) + ': "', None),
                'genre_l'    : ('string', '1 3 "' + rjust(_('Genre'), 5) + ': "', None),
                'video_v'    : ('scroller', '9 1 %d 1 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))'),
                'tag_v'      : ('scroller', '9 2 %d 2 m 3 "%s%s"',
                    '(self.width, player.getattr("tagline"), self.get_sepstrmscroll(player.getattr("tagline")))'),
                'genre_v'    : ('scroller', '9 3 %d 3 m 3 "%s%s"',
                    '(self.width, player.getattr("genre"), self.get_sepstrmscroll(player.getattr("genre")))'),
                'time_v1'    : ('string', '2 4 "%s/"', '(length)'),
                'time_v2'    : ('string', '10 4 "%s"', '(elapsed)'),
                'time_v3'    : ('string', '18 4 "(%2d%%)"', '(int(percentage * 100))'),
                'timebar1_v' : ('string', '26 4 "["', None),
                'timebar2_v' : ('string', '40 4 "]"', None),
                'timebar3_v' : ('hbar', '27 4 "%d"', '(int(percentage * 70))'),
                'animation_v': ('string', '1 4 "%s"', 'self.animation_audioplayer_chars[' +
                    ' player.elapsed % len(self.animation_audioplayer_chars)]')
            },
            'tv'             : {
                'chan_l'     : ('string', '1 1 "' + rjust(_('Channel'), 4) + ': "', None),
                'prog_l'     : ('string', '1 2 "' + rjust(_('Program'), 4) + ': "', None),
                'time_l'     : ('string', '1 3 "' + rjust(_('Time'), 4) + ': "', None),
                'desc_l'     : ('string', '1 4 "' + rjust(_('Description'), 4) + ': "', None),
                'chan_v'     : ('scroller', '7 1 %d 1 m 3 "%s%s"',
                    '(self.width, get_chan_displayname(tv.channel_id), '+
                    'self.get_sepstrmscroll(get_chan_displayname(tv.channel_id)))'),
                'prog_v'     : ('scroller', '7 2 %d 2 m 3 "%s%s"',
                    '(self.width, tv.title, self.get_sepstrmscroll(tv.title))'),
                'time_v'     : ('scroller', '7 3 %d 3 m 3 "%s-%s%s"',
                    '(self.width, tv.start, tv.stop, self.get_sepstrmscroll(tv.start+"-"+tv.stop))'),
                'desc_v'     : ('scroller', '7 4 %d 4 m 3 "%s%s"',
                    '(self.width, tv.desc, self.get_sepstrmscroll(tv.desc))')
            }
        }, # 40 chars per line

        20 : { # 20 chars per line
            'welcome'        : {
                'title'      : ('title', 'Freevo', None),
                'calendar'   : ('scroller', '1 2 %d 2 m 3 "' + _('Today is %s.') + '%s"',
                '(self.width, time.strftime("%A, %d-%B"), self.get_sepstrmscroll(time.strftime("%A, %d-%B")))'),
                'clock'      : ('string', '%d 3 "%s"',
                '((self.width - len(time.strftime("%T"))) / 2 + 1, time.strftime("%T"))')
            },
            'menu'           : {
                'title_v'    : ('scroller', '1 1 %d 1 m 3 "%s%s"',
                    '(self.width, menu.heading, self.get_sepstrmscroll(menu.heading))'),
                'item_v'     : ('scroller', '1 2 %d 2 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))'),
                'type_v'     : ('scroller', '1 3 %d 3 m 3 "%s%s"',
                    '(self.width, typeinfo, self.get_sepstrmscroll(typeinfo))'),
                'info_v'     : ('scroller', '1 4 %d 1 m 3 "%s%s"',
                    '(self.width, info, self.get_sepstrmscroll(info))')
            },
            'audio_player'   : {
                'music_v'    : ('scroller', '1 1 %d 1 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))'),
                'album_v'    : ('scroller', '1 2 %d 2 m 3 "%s%s"',
                    '(self.width, player.getattr("album"), self.get_sepstrmscroll(player.getattr("album")))'),
                'artist_v'   : ('scroller', '1 3 %d 3 m 3 "%s%s"',
                    '(self.width, player.getattr("artist"), self.get_sepstrmscroll(player.getattr("artist")))'),
                'time_v1'    : ('string', '2 4 "% 2d:%02d/"', '(int(player.length / 60), int(player.length % 60))'),
                'time_v2'    : ('string', '8 4 "% 2d:%02d"', '(int(player.elapsed / 60), int(player.elapsed % 60))'),
                'time_v3'    : ('string', '14 4 "(%2d%%)"', '(int(player.elapsed * 100 / player.length))'),
                'animation_v': ('string', '1 4 "%s"',
                     'self.animation_audioplayer_chars[player.elapsed % len(self.animation_audioplayer_chars)]')
               #'animation_v': ('hbar', '1 4 "%d"', '(int(player.elapsed *90 / player.length))')
            },
            'video_player'   : {
                'video_v'    : ('scroller', '1 1 %d 1 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))'),
                'tag_v'      : ('scroller', '1 2 %d 2 m 3 "%s%s"',
                    '(self.width, player.getattr("tagline"), self.get_sepstrmscroll(player.getattr("tagline")))'),
                'genre_v'    : ('scroller', '1 3 %d 3 m 3 "%s%s"',
                    '(self.width, player.getattr("genre"), self.get_sepstrmscroll(player.getattr("genre")))'),
                'time_v1'    : ('string', '3 4 "%s /"', '(length)'),
                'time_v2'    : ('string', '12 4 "%s"', '(elapsed)'),
                'animation_v': ('string', '1 4 "%s"',
                    'self.animation_audioplayer_chars[player.elapsed % len(self.animation_audioplayer_chars)]')
            },
            'tv'             : {
                'chan_v'     : ('scroller', '1 1 %d 1 m 3 "%s%s"',
                    '(self.width, get_chan_displayname(tv.channel_id), '+\
                    'self.get_sepstrmscroll(get_chan_displayname(tv.channel_id)))'),
                'prog_v'     : ('scroller', '1 2 %d 2 m 3 "%s%s"',
                    '(self.width, tv.title, self.get_sepstrmscroll(tv.title))'),
                'time_v'     : ('scroller', '1 3 %d 3 m 3 "%s-%s%s"',
                    '(self.width, tv.start, tv.stop, self.get_sepstrmscroll(tv.start+"-"+tv.stop))'),
                'desc_v'     : ('scroller', '1 4 %d 4 m 3 "%s%s"',
                    '(self.width, tv.desc, self.get_sepstrmscroll(tv.desc))')
            }
        }, # 20 chars per line

        16 : { # 16 chars per line
            'welcome'        : {
                'title'      : ('title', 'Freevo', None),
                'calendar'   : ('scroller', '1 2 %d 2 m 3 "' + _('Today is %s.') + '%s"',
                    '(self.width, time.strftime("%A, %d-%B"), self.get_sepstrmscroll(time.strftime("%A, %d-%B")))'),
                'clock'      : ('string', '%d 3 "%s"',
                    '((self.width - len(time.strftime("%T"))) / 2 + 1, time.strftime("%T"))')
            },
            'menu'           : {
                'title_v'    : ('scroller', '1 1 %d 1 m 3 "%s%s"',
                    '(self.width, menu.heading, self.get_sepstrmscroll(menu.heading))'),
                'item_v'     : ('scroller', '1 2 %d 2 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))'),
                'type_v'     : ('scroller', '1 3 %d 3 m 3 "%s%s"',
                    '(self.width, typeinfo, self.get_sepstrmscroll(typeinfo))'),
                'info_v'     : ('scroller', '1 4 %d 1 m 3 "%s%s"', '(self.width, info, self.get_sepstrmscroll(info))')
            },
            'audio_player'   : {
                'music_v'    : ('scroller', '1 1 %d 1 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))'),
                'album_v'    : ('scroller', '1 2 %d 2 m 3 "%s%s"',
                    '(self.width, player.getattr("album"), self.get_sepstrmscroll(player.getattr("album")))'),
                'artist_v'   : ('scroller', '1 3 %d 3 m 3 "%s%s"',
                    '(self.width, player.getattr("artist"), self.get_sepstrmscroll(player.getattr("artist")))'),
                'time_v1'    : ('string', '2 4 "% 2d:%02d/"', '(int(player.length / 60), int(player.length % 60))'),
                'time_v2'    : ('string', '8 4 "% 2d:%02d"', '(int(player.elapsed / 60), int(player.elapsed % 60))'),
                'time_v3'    : ('string', '14 4 "(%2d%%)"', '(int(player.elapsed * 100 / player.length))'),
                'animation_v': ('string', '1 4 "%s"',
                    'self.animation_audioplayer_chars[player.elapsed % len(self.animation_audioplayer_chars)]')
            },
            'video_player'   : {
                'video_v'    : ('scroller', '1 1 %d 1 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))'),
                'time_v1'    : ('string', '9 2 "%s"', '(length)'),
                'time_v2'    : ('string', '1 2 "%s"', '(elapsed.rjust(7))'),
                'time_v3'    : ('hbar', '1 3 "%d"', '((float(player.elapsed) / float(get_lengthsecs(length))) * 80)'),
                'clock'      : ('string', '3 4 "%s"', ' time.strftime("%I:%M  %b-%d") '),
                'animation_v': ('string', '1 4 "%s"',
                    'self.animation_audioplayer_chars[player.elapsed % len(self.animation_audioplayer_chars)]')
            },
            'tv'             : {
                'chan_v'     : ('scroller', '1 1 %d 1 m 3 "%s%s"',
                    '(self.width, get_chan_displayname(tv.channel_id), '+
                    'self.get_sepstrmscroll(get_chan_displayname(tv.channel_id)))'),
                'prog_v'     : ('scroller', '1 2 %d 2 m 3 "%s%s"',
                    '(self.width, tv.title, self.get_sepstrmscroll(tv.title))'),
                'time_v'     : ('scroller', '1 3 %d 3 m 3 "%s-%s%s"',
                    '(self.width, tv.start, tv.stop, self.get_sepstrmscroll(tv.start+"-"+tv.stop))'),
                'desc_v'     : ('scroller', '1 4 %d 4 m 3 "%s%s"',
                    '(self.width, tv.desc, self.get_sepstrmscroll(tv.desc))')
            }
        } # 16 chars per line
    }, # 4 lines display

    2 : { # 2 lines display
        40 : { # 40 chars per line
            'welcome': {
                'title'      : ('title', '1 1 Freevo', None)
            },
            'menu'           : {
                'title_l'    : ('string', '1 1 "' + rjust(_('Menu'), 4) + ': "', None),
                'item_l'     : ('string', '1 2 "' + rjust(_('Item'), 4) + ': "', None),
                'title_v'    : ('scroller', '7 1 %d 1 m 3 "%s%s"',
                    '(self.width, menu.heading, self.get_sepstrmscroll(menu.heading))'),
                'item_v'     : ('scroller', '7 2 %d 2 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))')
            },
            'audio_player'   : {
                'music_l'    : ('string', '1 1 "' + rjust(_('Music'), 5) + ': "', None),
                'music_v'    : ('scroller', '8 1 %d 1 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))'),
                'time_v1'    : ('string', '2 2 "% 2d:%02d/"', '(int(player.length / 60), int(player.length % 60))'),
                'time_v2'    : ('string', '8 2 "% 2d:%02d"', '(int(player.elapsed / 60), int(player.elapsed % 60))'),
                'time_v3'    : ('string', '14 2 "(%2d%%)"', '(int(player.elapsed * 100 / player.length))'),
                'timebar1_v' : ('string', '21 2 "["', None),
                'timebar2_v' : ('string', '40 2 "]"', None),
                'timebar3_v' : ('hbar', '22 2 "%d"', '(int(player.elapsed * 90 / player.length))'),
                'animation_v': ('string', '1 2 "%s"',
                    'self.animation_audioplayer_chars[player.elapsed % len(self.animation_audioplayer_chars)]')
            },
            'video_player'   : {
                'video_l'    : ('string', '2 1 "' + rjust(_('Video'), 5) + ': "', None),
                'video_v'    : ('scroller', '9 1 %d 1 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))'),
                'time_v1'    : ('string', '2 2 "%s/"', '(length)'),
                'time_v2'    : ('string', '10 2 "%s"', '(elapsed)'),
                'time_v3'    : ('string', '18 2 "(%2d%%)"', '(int(percentage * 100))'),
                'timebar1_v' : ('string', '26 2 "["', None),
                'timebar2_v' : ('string', '40 2 "]"', None),
                'timebar3_v' : ('hbar', '27 2 "%d"', '(int(percentage * 70))'),
                'animation_v': ('string', '1 2 "%s"',
                    'self.animation_audioplayer_chars[player.elapsed % len(self.animation_audioplayer_chars)]')
            },
            'tv': {
                'chan_l'     : ('string', '1 1 "' + rjust(_('Channel'), 4) + ': "', None),
                'prog_l'     : ('string', '1 2 "' + rjust(_('Program'), 4) + ': "', None),
                'chan_v'     : ('scroller', '7 1 %d 1 m 3 "%s%s"',
                    '(self.width, get_chan_displayname(tv.channel_id), '+
                    'self.get_sepstrmscroll(get_chan_displayname(tv.channel_id)))'),
                'prog_v'     : ('scroller', '7 2 %d 2 m 3 "%s%s"',
                    '(self.width, tv.title, self.get_sepstrmscroll(tv.title))'),
                'time_v'     : ('scroller', '%d 1 %d 3 m 3 "[%s-%s%s]"',
                    '(self.width - 13, 13, tv.start, tv.stop, self.get_sepstrmscroll(tv.start+"-"+tv.stop))'),
            }
        },

        20 : { # 20 chars per line
            'welcome'        : {
                'title'      : ('title', '1 1 Freevo', None)
            },
            'menu'           : {
                'title_v'    : ('scroller', '1 1 %d 1 m 3 "%s%s"',
                    '(self.width, menu.heading, self.get_sepstrmscroll(menu.heading))'),
                'item_v'     : ('scroller', '1 2 %d 2 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))')
            },
            'audio_player'   : {
                'music_v'    : ('scroller', '1 1 %d 1 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))'),
                'time_v1'    : ('string', '2 2 "% 2d:%02d/"', '(int(player.length / 60), int(player.length % 60))'),
                'time_v2'    : ('string', '8 2 "% 2d:%02d"', '(int(player.elapsed / 60), int(player.elapsed % 60))'),
                'time_v3'    : ('string', '14 2 "(%2d%%)"', '(int(player.elapsed * 100 / player.length))'),
                'animation_v': ('string', '1 2 "%s"',
                    'self.animation_audioplayer_chars[player.elapsed % len(self.animation_audioplayer_chars)]')
            },
            'video_player'   : {
                'video_v'    : ('scroller', '1 1 %d 1 m 3 "%s%s"',
                    '(self.width, title, self.get_sepstrmscroll(title))'),
                'time_v1'    : ('string', '3 2 "%s /"', '(length)'),
                'time_v2'    : ('string', '12 2 "%s"', '(elapsed)'),
                'animation_v': ('string', '1 2 "%s"',
                    'self.animation_audioplayer_chars[player.elapsed % len(self.animation_audioplayer_chars)]')
            },
            'tv': {
                'chan_v'     : ('scroller', '1 1 %d 1 m 3 "%s%s"',
                    '(self.width, get_chan_displayname(tv.channel_id), '+
                    'self.get_sepstrmscroll(get_chan_displayname(tv.channel_id)))'),
                'prog_v'     : ('scroller', '1 2 %d 2 m 3 "%s%s"',
                    '(self.width, tv.title, self.get_sepstrmscroll(tv.title))')
            }
        },

        16 : { # 16 chars per line
            'welcome'        : {
                'title'      : ('title', '1 1 Freevo', None)
            },
            'menu'           : {
                'title_v'    : ('scroller', '1 1 %d 1 m 2 "%s%s"',
                    '(self.width, remap(menu.heading), self.get_sepstrmscroll(menu.heading))'),
                'item_v'     : ('scroller', '1 2 %d 2 m 2 "%s%s"',
                    '(self.width, remap(title), self.get_sepstrmscroll(title))')
            },
            'audio_player'   : {
                'music_v'    : ('scroller', '1 1 %d 1 m 2 "%s%s"',
                    '(self.width, remap(title), self.get_sepstrmscroll(title))'),
                'time_v1'    : ('string', '2 2 "% 2d:%02d/"', '(int(player.length / 60), int(player.length % 60))'),
                'time_v2'    : ('string', '8 2 "% 2d:%02d"', '(int(player.elapsed / 60), int(player.elapsed % 60))'),
                'animation_v': ('string', '1 2 "%s"',
                    'self.animation_audioplayer_chars[player.elapsed % len(self.animation_audioplayer_chars)]')
            },
            'video_player'   : {
                'video_v'    : ('scroller', '1 1 %d 1 m 2 "%s%s"',
                    '(self.width, remap(title), self.get_sepstrmscroll(title))'),
                'time_v2'    : ('string', '2 2 "%s"', '(elapsed)'),
                'time_v3'    : ('string', '11 2 "(%2d%%)"', '(int(percentage * 100))'),
                'animation_v': ('string', '1 2 "%s"',
                    'self.animation_audioplayer_chars[player.elapsed % len(self.animation_audioplayer_chars)]')
            },
            'tv'             : {
                'chan_v'     : ('scroller', '1 1 %d 1 m 2 "%s%s"',
                    '(self.width, remap(get_chan_displayname(tv.channel_id)), '+
                    'self.get_sepstrmscroll(get_chan_displayname(tv.channel_id)))'),
                'prog_v'     : ('scroller', '1 2 %d 2 m 2 "%s%s"',
                    '(self.width, remap(tv.title), self.get_sepstrmscroll(tv.title))')
            }
        }, # 2 lines, 16 chars per line

        100 : { # No scroller
            'welcome'        : {
                'title'      : ('title', '1 1 Freevo', None)
            },
            'menu'           : {
                'title_v'    : ('string', '1 1 "%s%s"', '(menu.heading, self.get_sepstrmscroll(menu.heading))'),
                'item_v'     : ('string', '1 2 "%s"', '(title)')
            },
            'audio_player'   : {
                'music_v'    : ('string', '1 1 "%s"', '(title)'),
                'time_v1'    : ('string', '2 2 "% 2d:%02d/"', '(int(player.length / 60), int(player.length % 60))'),
                'time_v2'    : ('string', '8 2 "% 2d:%02d"', '(int(player.elapsed / 60), int(player.elapsed % 60))'),
                'animation_v': ('string', '1 2 "%s"',
                    'self.animation_audioplayer_chars[player.elapsed % len(self.animation_audioplayer_chars)]')
            },
            'video_player'   : {
                'video_v'    : ('string', '1 1 "%s"', '(title)'),
                'time_v2'    : ('string', '2 2 "%s"', '(elapsed)'),
                'time_v3'    : ('string', '11 2 "(%2d%%)"', '(int(percentage * 100))'),
                'animation_v': ('string', '1 2 "%s"',
                    'self.animation_audioplayer_chars[player.elapsed % len(self.animation_audioplayer_chars)]')
            },
            'tv'             : {
                'chan_v'     : ('string', '1 1 "%s"', '(get_chan_displayname(tv.channel_id))'),
                'prog_v'     : ('string', '1 2 "%s"', '(tv.title)')
            }
        }, # No scroller
    } # 2 lines display
} # layouts

# poll_widgets: widgets that should be refreshed during the pool
# Structure:
#
# poll_widgets = {
#     <#_OF_LINES_IN_DISPLAY> : {
#         <#_OF_COLUMNS_IN_DISPLAY> : {
#             <SCREEN_NAME> : (<WIDGET_NAME>, ...)
#         },
#         ...,
#     }
# }
poll_widgets = {
    4 : {
        40 : { 'welcome' : ['clock'] },
        20 : { 'welcome' : ['clock'] },
    },
}

def remap(data):
    logger.log( 9, 'remap(data=%r)', data)
    
    try:
        # first we remap all non-ASCII chars to ASCII
        if config.LCD_REMAP_TO_ASCII:
            data = unidecode(data)    
        
        # now we replace double quotes with single ones, 
        # double quotes confuse LCDd
        data = data.replace('\"', '\'').strip()

    except UnicodeDecodeError, error:
        logger.warning('%s', error)

    return data
  

def get_lengthsecs(slen):
    logger.log( 9, 'get_lengthsecs(slen=%r)', slen)
    splen = slen.rsplit(':')
    m = 1
    ts = 0
    for e in reversed(splen):
        ts = ts + (int(e) * m)
        m = m * 60
    return ts


def get_info(item, list):
    logger.log( 9, 'get_info(item=%r, list=%r)', item, list)
    info = ''

    for l in list:

        v = item.getattr(l[0])
        if v:
            if info:
                info += sep_str
            info += l[1] % v

    return info


class PluginInterface(plugin.DaemonPlugin):
    """
    Display context info in LCD using lcdproc daemon.

    Requires: lcdproc installed and LCDd running. U{http://lcdproc.sourceforge.net/}
    Requires: pylcd installed U{http://www.schwarzvogel.de/software-pylcd.shtml}

    Also, your LCD dimensions must be supported. Right now it support: 4x20,
    4x40, 2x16, 2x20, 2x40. If you have one with different dimension, it will
    try to fit a smaller one, if none was find, then it will be disabled.

    To support a new dimension is just a matter of creating 'screens' to
    that dimension, which is really easy, since a 'screen' is just a set of
    python dicts telling how to display information on the LCD. You can try it
    yourself, just take a look in src/plugins/lcd.py, the variable is
    'layouts'. If you add support for your dimensions, please send a patch to
    the list freevo-devel@lists.sourceforge.net, or if you weren't able, just
    ask for it there.

    To activate this plugin, just put the following line at the end of your
    local_conf.py file:

    | plugin.activate('lcd')
    """
    __author__           = 'Gustavo Sverzut Barbieri'
    __author_email__     = 'barbieri@gmail.com'
    __maintainer__       = __author__
    __maintainer_email__ = __author_email__
    __version__          = '$Revision$'

    def __init__(self, height=None, width=None):
        """
        init the lcd
        """
        logger.log( 9, 'PluginInterface.__init__(height=%r, width=%r)', height, width)
        plugin.DaemonPlugin.__init__(self)
        try:
            self.lcd = pylcd.client()
            cm = self.lcd.connect()
        except:
            self.disable = 1
            self.reason = 'LCD plugin will not load! Maybe you don"t have LCDd (lcdproc daemon) running?'
            return

        if config.DEBUG > 0:
            logger.log( 9, 'Connecting to LCD: %s', cm)
            logger.log( 9, 'Info as known by the LCD module:')
            self.lcd.getinfo()
            logger.log( 9, '')

        self.poll_interval = 1
        self.poll_menu_only = 0
        self.disable = 0
        self.height = height or self.lcd.d_height
        self.width  = width or self.lcd.d_width
        self.playitem = None
        self.generate_screens()
        if self.disable:
            return
        else:
            self.event_listener = 1
        self.version = self.lcd.s_version
        if self.version.startswith('0.5'):
            self.prio_map = { 'high': 'foreground', 'normal': 'background', 'low': 'info' }
        elif self.version.startswith('0.4'):
            self.prio_map = { 'high': '64', 'normal': '128', 'low': '192' }

        # Animaton-Sequence used in audio playback
        # Some displays (like the CrytstalFontz) do display the \ as a /
        if self.version.startswith('0.5'):
            self.animation_audioplayer_chars = ['-', '\\\\', '|', '/']
        elif self.version.startswith('0.4'):
            self.animation_audioplayer_chars = ['-', '\\', '|', '/']
        else:
            self.disable = 1
            self.reason = 'Unsupported LCDd version: %s' % (self.version,)
            return

        plugin.register(self, 'lcd')

        # Show welcome screen:
        for w in self.screens['welcome']:
            type, param, val = self.screens['welcome'][w]
            if val: param = param % eval(val)

            try:
                self.lcd.widget_set('welcome', w, param.encode('latin1'))
            except UnicodeError:
                self.lcd.widget_set('welcome', w, param)

        self.lcd.screen_set('welcome', '-priority %s -duration 2 -heartbeat off' % (self.prio_map['low']))
        self.last_screen = 'welcome'
        self.lsv = { } # will hold last screen value (lsv)


    def close(self):
        """
        to be called before the plugin exists.
        It terminates the connection with the server
        """
        logger.log( 9, 'close()')
        #self.lcd.send('bye')


    def draw(self, (type, object), osd):
        """
        'Draw' the information on the LCD display.
        """
        logger.log( 9, 'draw(type=%r, object=%r, osd=%r)', type, object, osd)
        if self.disable: return

        # Check if audio is detached
        # When in detached mode, do not draw the player screen
        if type == 'player':
            if plugin.getbyname('audio.detachbar'):
                if plugin.getbyname('audio.detachbar').state != 1: #BAR_HIDE
                    return

        if type == 'player':
            sname = '%s_%s' % (object.type, type)
        else:
            sname = type

        if not self.screens.has_key(sname):
            sname = 'menu'

        if sname != self.last_screen:
            # recreate screen
            # This is used to handle cases where the previous screen was dirty
            # ie: played music with info and now play music without, the previous
            #     info will still be there
            self.lcd.screen_del(sname)
            self.generate_screen(sname)
            self.lsv = { } # reset last changed values

        if type == 'menu':
            try:
                menu  = object.menustack[-1]
                title = menu.selected['title']
                if isinstance(menu.selected, MenuItem):
                    title = _(title)

                typeinfo = menu.selected.type
                info = ''

                if menu.selected.getattr('type'):
                    typeinfo = menu.selected.getattr('type')

                # get info:
                if menu.selected.type and menu_info.has_key(menu.selected.type):
                    info = get_info(menu.selected, menu_info[menu.selected.type])
                    if menu_strinfo.has_key(menu.selected.type) and menu_strinfo[menu.selected.type]:
                        if info:
                            info += sep_str
                        info += time.strftime(menu_strinfo[menu.selected.type])

                # specific things related with item type
                if menu.selected.type == 'audio':
                    title = String(menu.selected.getattr('title'))
                    if not title:
                        title = String(menu.selected.getattr('name'))
                    if menu.selected.getattr('trackno'):
                        title = '%s - %s' % (String(menu.selected.getattr('trackno')), title)
            except:
                title = ''

        elif type == 'player':
            player = object
            title  = player.getattr('title')
            if not title:
                title = String(player.getattr('name'))

            if player.type == 'audio':
                if player.getattr('trackno'):
                    title = '%s - %s' % (String(player.getattr('trackno')), title)

            elif player.type == 'video':
                length = player.getattr('length')
                elapsed = player.elapsed
                if elapsed / 3600:
                    elapsed ='%d:%02d:%02d' % (elapsed / 3600, (elapsed % 3600) / 60,
                                                elapsed % 60)
                else:
                    elapsed = '%d:%02d' % (elapsed / 60, elapsed % 60)
                try:
                    percentage = float(player.elapsed / player.length)
                except:
                    percentage = None

        elif type == 'tv':
            tv = copy.copy(object.selected)

            if tv.start == 0:
                tv.start = ' 0:00'
                tv.stop  = '23:59' # could also be: '????'
            else:
                tv.start = time.localtime(tv.start)
                tv.stop  = time.localtime(tv.stop)

                tv.start = '% 2d:%02d' % (tv.start[3], tv.start[4])
                tv.stop  = '% 2d:%02d' % (tv.stop[3], tv.stop[4])


        s = self.screens[sname]
        for w in s:
            t, param, val = s[w]
            try:
                if val: param = param % eval(val)
            except:
                param = None

            k = '%s %s' % (sname, w)
            try:
                if String(self.lsv[k]) == String(param):
                    continue # nothing changed in this widget
            except KeyError:
                pass

            self.lsv[k] = param
            if param:
                try:
                    self.lcd.widget_set(sname, w, param.encode('latin1'))
                except UnicodeError:
                    self.lcd.widget_set(sname, w, param)

        if self.last_screen != sname:
            self.lcd.screen_set(self.last_screen, '-priority %s' % (self.prio_map['normal']))
            self.lcd.screen_set(sname, '-priority %s' % (self.prio_map['high']))
            self.last_screen = sname


    def poll(self):
        #_debug_('poll()', 2)
        if self.disable: return

        if self.playitem:
            self.draw(('player', self.playitem), None)

        try:
            screens = poll_widgets[self.lines][self.columns]
        except:
            return

        for s in screens:
            widgets = screens[s]

            for w in widgets:
                type, param, val = self.screens[s][w]

                if val: param = param % eval(val)
                try:
                    self.lcd.widget_set(s, w, param.encode('latin1'))
                except UnicodeError:
                    self.lcd.widget_set(s, w, param)


    def generate_screens(self):
        logger.log( 9, 'generate_screens()')
        screens = None
        l = self.height
        c = self.width
        # Find a screen with 'l' lines
        while not screens:
            try:
                screens = layouts[l]
            except KeyError:
                logger.warning('Could not find screens for %d lines LCD!', l)
                l -= 1
                if l < 1:
                    logger.error('No screens found for this LCD (%dx%d)!', self.height, self.width)
                    self.disable = 1
                    return
        # find a display with 'l' line and 'c' columns
        while not screens:
            try:
                screens = layouts[l][c]
            except KeyError:
                logger.warning('Could not find screens for %d lines and %d columns LCD!', l, c)
                c -= 1
                if c < 1:
                    logger.error('No screens found for this LCD (%dx%d)!', self.height, self.width)
                    self.disable = 1
                    return

        self.lines = l
        self.columns = c
        try:
            self.screens = screens = layouts[l][c]
        except KeyError:
            logger.warning('Could not find screens for %d lines and %d columns LCD!', self.height, self.width)

            logger.error('No screens found for this LCD (%dx%d)!', self.height, self.width)
            self.disable = 1
            return

        for s in screens:
            self.generate_screen(s)


    def generate_screen(self, s):
        logger.log( 9, 'generate_screen(s=%r)', s)
        if not self.screens.has_key(s):
            s = 'menu'
        self.lcd.screen_add(s)
        widgets = self.screens[s]
        self.lcd.screen_set(s, '-heartbeat off')

        for w in widgets:
            type, param, val = self.screens[s][w]
            logger.log( 9, 'widget_add(s=%r, w=%r, type=%r)', s, w, type)
            self.lcd.widget_add(s, w, type)


    def eventhandler(self, event, menuw=None):
        logger.log( 9, 'eventhandler(event=%r, menuw=%r)', event.name, menuw)
        if event == PLAY_START:
            self.playitem = event.arg
        elif event == PLAY_END or event == STOP:
            self.playitem = None
        return 0


    def get_sepstrmscroll(self, mscrolldata):
        """
        used for marquee scroller; returns seperator if info is wider then lcd
        """
        #_debug_('get_sepstrmscroll(mscrolldata=%r)' % (mscrolldata,), 2)
        if len(mscrolldata) > self.width:
            return sep_str_mscroll
        return ''
