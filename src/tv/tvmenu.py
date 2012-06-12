# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# tv.py - This is the Freevo TV module.
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


import time

# Configuration file. Determines where to look for AVI/MP3 files, etc
import config

# The menu widget class
import menu

import plugin

import util.tv_util as tv_util

from item import Item

from tv.tvguide import TVGuide

import tv.epg
import dialog


def get_tunerid(channel_id):
    tuner_id = None
    for vals in config.TV_CHANNELS:
        tv_channel_id, tv_display_name, tv_tuner_id = vals[:3]
        if tv_channel_id == channel_id:
            return tv_tuner_id
    dialog.show_alert(_('Could not find TV channel %s') % channel_id)
    return None


def get_friendly_channel(channel_id):
    channel_name = tv_util.get_chan_displayname(channel_id)
    if not channel_name:
        dialog.show_alert(_('Could not find TV channel %s') % channel_id)
    return channel_name


def start_tv(mode=None, channel_id=None):
    tuner_id = get_tunerid(channel_id)
    p = plugin.getbyname(plugin.TV)
    if p is None:
        dialog.show_alert(_('Cannot get TV plug-in'))
        return
    p.Play(mode, tuner_id)



#
# The TV menu
#
class TVMenu(Item):

    def __init__(self):
        Item.__init__(self)
        self.type = 'tv'


    def main_menu(self, arg, menuw):
        items = []
        if config.TV_CHANNELS:
            items.append(menu.MenuItem(_('TV Guide'), action=self.start_tvguide))

        plugins_list = plugin.get('mainmenu_tv')
        for p in plugins_list:
            items += p.items(self)

        menuw.pushmenu(menu.Menu(_('TV Main Menu'), items, item_types='tv main menu'))


    def get_start_time(self):
        ttime = time.localtime()
        stime = [ ]
        for i in ttime:
            stime += [i]
        stime[5] = 0 # zero seconds
        if stime[4] >= 30:
            stime[4] = 30
        else:
            stime[4] = 0

        return time.mktime(stime)


    def start_tvguide(self, arg, menuw):

        # Check that the TV channel list is not None
        if not config.TV_CHANNELS:
            msg = _('The list of TV channels is invalid!\n')
            msg += _('Please check the config file.')
            dialog.show_alert(msg)
            return

        if arg == 'record':
            start_tv(None, ('record', None))
            return

        guide = plugin.getbyname('tvguide')
        if guide:
            guide.start(self.get_start_time(), start_tv, menuw)
        else:
            TVGuide(tv.epg.channels, self.get_start_time(), start_tv, menuw)
