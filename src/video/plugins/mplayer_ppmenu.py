# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# mplayer_ppmenu.py - Choose mplayer aspect ratio and postprocessing
# -----------------------------------------------------------------------
# $Id: mplayer_ppmenu.py,v 1.6 2006/02/11 16:37:00 gorka Exp $
#
# This plugin allows to override the aspect ratio and postprocessing options
# of a movie
#
# The item plugin activates automatically a DaemonPlugin that watches for
# MENU_BACK events to default the aspect option variable if the user has exited
# the submenu of the movie
#
# Activate: 
#
#   plugin.activate('video.mplayer_ppmenu.item')
#
#   The first element selects the default option of the movie
#   you can add the aspect options you find useful
#   MPLAYER_ASPECT_RATIOS =  ('Def', '16:9', '2.35:1', '4:3')
#
# -----------------------------------------------------------------------
# $Log: mplayer_ppmenu.py,v $
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

import plugin
import config
import rc
import event as em
import skin
import menu

from plugins.idlebar import IdleBarPlugin


class item(plugin.ItemPlugin):
    """
    Changes the aspect option of a Movie

    plugin.activate('video.mplayer_ppmenu.item')

    """
    def __init__(self):
        plugin.ItemPlugin.__init__(self)

        self.skin = skin.get_singleton()

        self.item = None
        self.plugin_name = 'video.mplayer_ppmenu.item'

        self.default_str = _('Default')

        if hasattr(config, 'MPLAYER_VF_PROGRESSIVE_OPTS'):
            self.vfp_opts = config.MPLAYER_VF_PROGRESSIVE_OPTS
        else:

             self.vfp_opts = [
                (self.default_str, ''),
                ('LQ', 'pp=de'),
                ('HQ', 'pp=ac/al'),
                ('HQ denoise3d', 'pp=ac/al,hqdn3d=2:2:4'),
                ('HQ denoise3d+unsharp', 'pp=ac/al,hqdn3d=2:2:4,unsharp=l3x3:0.5'),
                ('HQ denoise3d+unsharp+noise', 'pp=ac/al,hqdn3d=2:2:4,unsharp=l3x3:0.5,noise=12uah:5uah')
                ('HD content', 'pp=de -lavdopts fast:skiploopfilter=all:threads=2')
             ]

        self.vfp_opt = None

        self.vfp_args_def = config.MPLAYER_VF_PROGRESSIVE
        self.vfp_title_def = _('Video PP - %s')

        self.vfp_title = self.vfp_title_def % self.default_str


        if hasattr(config, 'MPLAYER_VF_INTERLACED_OPTS'):
            self.vfi_opts = config.MPLAYER_VF_INTERLACED_OPTS
        else:

             self.vfi_opts = [
                (self.default_str, ''),
                ('LQ', 'pp=de'),
                ('HQ', 'pp=ac/al'),
                ('HQ denoise3d', 'pp=ac/al,hqdn3d=2:2:4'),
                ('HQ denoise3d+unsharp', 'pp=ac/al,hqdn3d=2:2:4,unsharp=l3x3:0.5'),
                ('HQ denoise3d+unsharp+noise', 'pp=ac/al,hqdn3d=2:2:4,unsharp=l3x3:0.5,noise=12uah:5uah')
             ]

        self.vfi_opt = None

        self.vfi_args_def = config.MPLAYER_VF_PROGRESSIVE
        self.vfi_title_def = _('Video PP - %s')

        self.vfi_title = self.vfi_title_def % self.default_str


        # Aspect ratio properties
        #
        self.cnt  = 0
       
        if hasattr(config, 'MPLAYER_ARGS_DEF'):
            self.args_def = config.MPLAYER_ARGS_DEF
        else:
            self.args_def = ''

        self.title_def = _('Aspect Ratio - %s')
        self.title = self.title_def % self.default_str

        if hasattr(config, 'MPLAYER_ASPECT_RATIOS'):
            self.ratios = config.MPLAYER_ASPECT_RATIOS
        else:
            self.ratios = (_('Def'), '16:9', '2.35:1', '4:3')

        
        plugin.activate('video.mplayer_ppmenu.daemon')


    def vfp_opts_menu(self, menuw=None, arg=None):
        _debug_('vfp_opts_menu(self, menuw=%r, arg=%r)' % (menuw, arg), 1)

        menu_items = []
        for item in self.vfp_opts:
            menu_items += [ menu.MenuItem(item[0], action=self.select_vfp) ] 

        vfp_opts_menu = menu.Menu(_('Select Postprocessing Profile'), menu_items, item_types = 'video postprocessing menu')

        vfp_opts_menu.infoitem = self
        menuw.pushmenu(vfp_opts_menu)
        menuw.refresh()


    def vfi_opts_menu(self, menuw=None, arg=None):
        _debug_('vfi_opts_menu(self, menuw=%r, arg=%r)' % (menuw, arg), 1)

        menu_items = []
        for item in self.vfi_opts:
            menu_items += [ menu.MenuItem(item[0], action=self.select_vfi) ] 

        vfi_opts_menu = menu.Menu(_('Select Postprocessing Profile'), menu_items, item_types = 'video postprocessing menu')

        vfi_opts_menu.infoitem = self
        menuw.pushmenu(vfi_opts_menu)
        menuw.refresh()


    def select_vfp(self, arg=None, menuw=None):
        if menuw:
            item = menuw.all_items.index(menuw.menustack[-1].selected)
            self.vfp_opt = self.vfp_opts[item]

            if self.vfp_opt[0] == self.default_str:
                config.MPLAYER_VF_PROGRESSIVE = self.vfp_args_def
            else:
                config.MPLAYER_VF_PROGRESSIVE = self.vfp_opt[1]

            str = self.vfp_opt[0]

            _debug_('VF_PROGRESSIVE command string for mplayer:  %s' % config.MPLAYER_VF_PROGRESSIVE)

            self.vfp_title = self.vfp_title_def % str
            menuw.menustack[-2].selected.name = self.vfp_title

            menuw.back_one_menu(arg='reload')


    def select_vfi(self, arg=None, menuw=None):
        if menuw:
            item = menuw.all_items.index(menuw.menustack[-1].selected)
            self.vfi_opt = self.vfi_opts[item]

            if self.vfi_opt[0] == self.default_str:
                config.MPLAYER_VF_INTERLACED = self.vfi_args_def
            else:
                config.MPLAYER_VF_INTERLACED = self.vfi_opt[1]

            str = self.vfi_opt[0]

            _debug_('VF_INTERLACED command string for mplayer:  %s' % config.MPLAYER_VF_PROGRESSIVE)

            self.vfi_title = self.vfi_title_def % str
            menuw.menustack[-2].selected.name = self.vfi_title

            menuw.back_one_menu(arg='reload')

    
    def set_default_vfp_options(self):
        self.vfp_opt = None
        self.vfp_title = self.vfp_title_def % self.default_str
        config.MPLAYER_VF_PROGRESSIVE = self.vfp_args_def


    def set_default_vfi_options(self):
        self.vfi_opt = None
        self.vfi_title = self.vfi_title_def % self.default_str
        config.MPLAYER_VF_INTERLACED = self.vfi_args_def


    def aspect(self, arg=None, menuw=None):
        
        self.cnt += 1
        self.ratio = self.ratios[self.cnt % len(self.ratios)]

        if self.ratio == self.ratios[0]:
            config.MPLAYER_ARGS_DEF = self.args_def
        else:
            config.MPLAYER_ARGS_DEF = (self.args_def + ' -aspect ' + self.ratio)
        _debug_('Aspect command string for mplayer:  %s' % config.MPLAYER_ARGS_DEF)
        if self.ratio == self.ratios[0]:
            str = self.default_str
        else:
            str = self.ratio

        self.title = self.title_def % str
        
        menuw.menustack[-1].selected.name = self.title
        self.skin.force_redraw = True
        self.skin.draw('menu', menuw)


    def set_default_ratio(self):
        self.cnt = 0
        self.ratio = self.ratios[0]
        self.title = self.title_def % self.default_str
        config.MPLAYER_ARGS_DEF = self.args_def


    def actions(self, item):
        self.item = item
        myactions = []

        if item.type == 'video':
            myactions.append((self.aspect, self.title))
            if item['deinterlace']:
                myactions.append((self.vfi_opts_menu, self.vfi_title))
            else:
                myactions.append((self.vfp_opts_menu, self.vfp_title))

        return myactions


class daemon(plugin.DaemonPlugin):
    """
    Defaults the post processing string if going back on the menu
    """

    def __init__(self):
        plugin.DaemonPlugin.__init__(self)
        self.plugin_name = 'video.mplayer_ppmenu.daemon'
        self.event_listener = True


    def eventhandler(self, event, menuw=None):
        _debug_("Saw %s" % event)
        if event in (em.MENU_GOTO_MAINMENU, em.MENU_BACK_ONE_MENU):
            plug = plugin.getbyname('video.mplayer_ppmenu.item')
            if plug:
                _debug_('Changing to default post-processing and ratio options')
                plug.set_default_vfp_options()
                plug.set_default_vfi_options()
                plug.set_default_ratio()

        return False
