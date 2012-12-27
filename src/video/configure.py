# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# Configure video playing
# -----------------------------------------------------------------------
# $Id$
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
# -----------------------------------------------------------------------

"""
Process actions for a video item's configuration menu.

A collection of menu items and actions.
"""

import re
import copy

# The menu widget class
import config
import menu
import plugin


def play_movie(arg=None, menuw=None):
    """
    Dummy for playing the movie
    """
    menuw.delete_menu()
    arg[0].delete_info('autobookmark_resume')
    arg[0].play(menuw=menuw, arg=arg[1])


def audio_selection(arg=None, menuw=None):
    """
    Audio selection menu action
    """
    arg[0].selected_audio = arg[1]
    menuw.back_one_menu()


def audio_selection_menu(arg=None, menuw=None):
    """
    Audio selection menu list
    """
    item       = arg
    menu_items = []

    for i in range(len(item.info['audio'])):
        a = copy.copy(item.info['audio'][i])
        # set reasonable defaults when attributes are missing or not set

        if not a.has_key('id') or a['id'] is None:
            # workaround for kaa.metadata not having audio ids for ogm and avi files
            a['id'] = i
            if item.info.has_key('mime') and item.info['mime'] == 'video/avi':
                a['id'] += 1

        if not a.has_key('title') or a['title'] is None:
            a['title'] = ''

        if not a.has_key('language') or a['language'] is None:
            a['language'] = _('Stream %s') % a['id']

        if not a.has_key('channels') or a['channels'] is None:
            a['channels'] = 2 # wild guess :-)

        if not a.has_key('codec') or a['codec'] is None:
            a['codec'] = _('Unknown')

        txt = '%(language)s %(title)s (channels=%(channels)s:%(codec)s)' % a
        menu_items.append(menu.MenuItem(txt, audio_selection, (item, a['id'])))

    moviemenu = menu.Menu(_('Audio Menu'), menu_items, fxd_file=item.skin_fxd, item_types = 'video default')
    menuw.pushmenu(moviemenu)


def subtitle_selection(arg=None, menuw=None):
    """
    Subtitle selection menu action
    """
    arg[0].selected_subtitle = arg[1]
    menuw.back_one_menu()


def subtitle_selection_menu(arg=None, menuw=None):
    """
    Subtitle selection menu list
    """
    item = arg

    menu_items = [ menu.MenuItem(_('no subtitles'), subtitle_selection, (item, -1)) ]

    for subtitle in item.info['subtitles']:
        s = copy.copy(subtitle)

        if not s.has_key('id') or not s['id']:
            s['id'] = item.info['subtitles'].index(subtitle)

        if not s.has_key('language') or not s['language']:
            s['language'] = _('Stream %s') % s['id']

        if not s.has_key('title') or not s['title']:
            s['title'] = ''
        if s['title'] == 'Undefined':
            s['title'] = ''

        if s['title'] != '':
            s['title'] = ' (%s)' % s['title']

        txt = '%(language)s%(title)s' % s
        menu_items.append(menu.MenuItem(txt, subtitle_selection, (item, s['id'])))

    moviemenu = menu.Menu(_('Subtitle Menu'), menu_items, fxd_file=item.skin_fxd, item_types = 'video default')
    menuw.pushmenu(moviemenu)


def chapter_selection(menuw=None, arg=None):
    """
    Chapter selection menu action
    """
    menuw.delete_menu()
    play_movie(menuw=menuw, arg=arg)


def chapter_selection_menu(arg=None, menuw=None):
    """
    Chapter selection menu list
    """
    item = arg
    menu_items = []
    if isinstance(arg.info['chapters'], int):
        for c in range(1, arg.info['chapters']):
            menu_items += [ menu.MenuItem(_('Play chapter %s') % c, chapter_selection, (arg, ' -chapter %s' % c)) ]
    elif arg.info['chapters']:
        for chapter in arg.info['chapters']:
            c = copy.copy(chapter)

            if not c.has_key('id') or not c['id']:
                c['id'] = item.info['chapters'].index(chapter)

            if not c.has_key('name') or not c['name']:
                c['name'] = ''

            if not c.has_key('pos') or not c['pos']:
                c['pos'] = 0

            if c['name']:
                txt = '%(name)s (%(pos)s)' % c
            else:
                txt = '%(id)s (%(pos)s)' % c

            menu_items.append(menu.MenuItem(txt, chapter_selection, (item, ' -ss %s' % c['pos'])))

    moviemenu = menu.Menu(_('Chapter Menu'), menu_items, fxd_file=item.skin_fxd, item_types = 'video default')
    menuw.pushmenu(moviemenu)


def subitem_selection(menuw=None, arg=None):
    """
    Sub-item selection menu action
    """
    item, pos = arg
    item.conf_select_this_item = item.subitems[pos]
    menuw.delete_menu()
    play_movie(menuw=menuw, arg=(item, None))


def subitem_selection_menu(arg=None, menuw=None):
    """
    Sub-item selection menu list
    """
    item  = arg
    menu_items = []

    for pos in range(len(item.subitems)):
        menu_items += [ menu.MenuItem(_('Play chapter %s') % (pos+1), subitem_selection, (arg, pos)) ]

    moviemenu = menu.Menu(_('Chapter Menu'), menu_items, fxd_file=item.skin_fxd, item_types = 'video default')
    menuw.pushmenu(moviemenu)


def player_selection(menuw=None, arg=None):
    """
    Player selection menu action
    """
    item, player = arg
    item.player = player[1]
    item.player_rating= player[0]
    menuw.delete_menu()
    play_movie(menuw=menuw, arg=(item, None))


def player_selection_menu(arg=None, menuw=None):
    """
    Player selection menu list
    """
    item  = arg
    menu_items = []

    for player in item.possible_players:
        menu_items += [ menu.MenuItem(_('Play with "%s"') % (player[1].name), player_selection, (arg, player))]

    moviemenu = menu.Menu(_('Player Menu'), menu_items, fxd_file=item.skin_fxd, item_types = 'video default')
    menuw.pushmenu(moviemenu)


def toggle(arg=None, menuw=None):
    """
    Toggle a menu item over two choices action
    """
    arg[1][arg[2]] = not arg[1][arg[2]]

    old = menuw.menustack[-1].selected
    pos = menuw.menustack[-1].choices.index(menuw.menustack[-1].selected)

    new = add_toogle(arg[0], arg[1], arg[2])
    new.image = old.image

    if hasattr(old, 'display_type'):
        new.display_type = old.display_type

    menuw.menustack[-1].choices[pos] = new
    menuw.menustack[-1].selected = menuw.menustack[-1].choices[pos]

    menuw.init_page()
    menuw.refresh()


def add_toogle(name, item, var):
    """
    Toggle a menu item over two choices menu
    """
    if item[var]:
        return menu.MenuItem(_('Turn off %s') % name, toggle, (name, item, var))
    return menu.MenuItem(_('Turn on %s') % name, toggle, (name, item, var))


def toggle3(arg=None, menuw=None):
    """
    Toggle a menu item over three choices
    """
    arg[1][arg[2]] += 1
    if arg[1][arg[2]] > 1:
        arg[1][arg[2]] = -1

    old = menuw.menustack[-1].selected
    pos = menuw.menustack[-1].choices.index(menuw.menustack[-1].selected)

    new = add_toogle3(arg[0], arg[1], arg[2])
    new.image = old.image

    if hasattr(old, 'display_type'):
        new.display_type = old.display_type

    menuw.menustack[-1].choices[pos] = new
    menuw.menustack[-1].selected = menuw.menustack[-1].choices[pos]

    menuw.init_page()
    menuw.refresh()


def add_toogle3(name, item, var):
    """
    Toggle a menu item over three choices field dominance
    """
    if item[var] == -1:
        return menu.MenuItem(_('Activate TOP field first'), toggle3, (name, item, var))
    elif item[var] == 0:
        return menu.MenuItem(_('Activate BOTTOM field first'), toggle3, (name, item, var))
    else:
        return menu.MenuItem(_('Activate AUTO field first'), toggle3, (name, item, var))


def get_items(item):
    """
    Build a list of menu items for a video item

    @returns: a list of menu items
    """
    next_start = 0
    items = []

    if len(item.possible_players) > 1:
        items.append(menu.MenuItem(_('Play with alternate player'), player_selection_menu, item))

    if item.filename or (item.mode in ('dvd', 'vcd') and item.player_rating >= 20):
        if item.info.has_key('audio') and len(item.info['audio']) > 1:
            items.append(menu.MenuItem(_('Audio selection'), audio_selection_menu, item))
        if item.info.has_key('subtitles') and len(item.info['subtitles']) >= 1:
            items.append(menu.MenuItem(_('Subtitle selection'), subtitle_selection_menu, item))
        if item.info.has_key('chapters') and item.info['chapters'] > 1:
            items.append(menu.MenuItem(_('Chapter selection'), chapter_selection_menu, item))

    if item.subitems:
        # show subitems as chapter
        items.append(menu.MenuItem(_('Chapter selection'), subitem_selection_menu, item))

    if item.mode in ('dvd', 'vcd') or \
           (item.filename and item.info.has_key('type') and \
            item.info['type'] and item.info['type'].lower().find('mpeg') != -1):

        if hasattr(config, 'VIDEO_DEINTERLACE') and config.VIDEO_DEINTERLACE != None:
            items += [ add_toogle(_('de-interlacing'), item, 'deinterlace') ]

        if hasattr(config, 'VIDEO_USE_XVMC') and config.VIDEO_USE_XVMC != None:
            items += [ add_toogle(_('X-Video Motion Compensation (xvmc)'), item, 'xvmc') ]

        if hasattr(config, 'VIDEO_FIELD_DOMINANCE') and config.VIDEO_FIELD_DOMINANCE != None:
            items += [ add_toogle3(_('Activate BOTTOM field first'), item, 'field-dominance') ]
    return items


def get_menu(item, menuw):
    """
    Build a menu for video items

    @returns: a list of menu items
    """
    items = get_items(item) + [ menu.MenuItem(_('Play'), play_movie, (item, '')) ]
    return menu.Menu(_('Config Menu'), items, fxd_file=item.skin_fxd, item_types = 'video default')
