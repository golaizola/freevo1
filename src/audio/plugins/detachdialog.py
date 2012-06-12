# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# Audio DetachBar plug-in
# -----------------------------------------------------------------------
# $Id: detachbar.py 11408 2009-04-11 14:58:01Z duncan $
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

__author__           = 'Maciej Urbaniak'
__author_email__     = 'maciej@urbaniak.org'
__maintainer__       = __author__
__maintainer_email__ = __author_email__
__version__          = '$Revision$'
__license__          = 'GPL'

"""
Audio DetachDialog plug-in
Based on original plugin DetachBar by Viggo Fredriksen <viggo@katatonic.org>
"""

import logging
logger = logging.getLogger("freevo.audio.plugins.detachdialog")

# python specific
import time

# freevo specific
import config
import dialog
import skin
import audio
import audio.player
import plugin
import rc
from event import *
from kaa import EventHandler 

# barstates
DIALOG_NOTSET = 0    # state not set
DIALOG_HIDE   = 1    # timedout, reset and change poll interval
DIALOG_SHOW   = 2    # show the dialog
DIALOG_WAIT   = 3    # wait for new track

def formatstate(state):
    """
    returns state formatted as a string
    """
    return state is None     and 'BAR_NONE' \
        or state == DIALOG_HIDE and 'DIALOG_HIDE' \
        or state == DIALOG_SHOW and 'DIALOG_SHOW' \
        or state == DIALOG_WAIT and 'DIALOG_WAIT' \
        or 'DIALOG_NOTSET'


class PluginInterface(plugin.DaemonPlugin):
    """
    This plugin enables a small bar showing information about audio being played
    when detached with the detach plugin.

    If the idlebar is loaded and there is enough space left there, this plugin
    will draw itself there, otherwise it will draw at the right bottom of the
    screen.
    """
    detached = False

    def __init__(self):
        """initialise the DaemonPlugin interface"""
        logger.log(9, 'detachbar.PluginInterface.__init__()')
        plugin.DaemonPlugin.__init__(self)
        self.plugin_name = 'audio.detachbar'
        self.player      = None
        self.event       = EventHandler(self._event_handler)
        self.event.register()
        self.state       = DIALOG_NOTSET
        self.dialog      = None
        self.update(DIALOG_HIDE)
        

    def _event_handler(self, event):
        logger.log(9, '_event_handler(event=%s), event.arg=%r, event.context=%r, PluginInterface.detached=%r', 
            event, event.arg, event.context, PluginInterface.detached)
        
        player = audio.player.get()
        
        if plugin.isevent(event) == 'DETACH':
            PluginInterface.detached = True
            self.update(DIALOG_SHOW)
        elif plugin.isevent(event) == 'ATTACH':
            PluginInterface.detached = False
            self.update(DIALOG_HIDE)
        elif event == BUTTON and event.arg == 'STOP':
            PluginInterface.detached = False
            self.update(DIALOG_HIDE)
        elif PluginInterface.detached:
            # this event can only happen if video or game starts playing
            # hide the dialog now
            if event == VIDEO_START:
                PluginInterface.detached = False
                self.update(DIALOG_HIDE)
            elif event == PLAY_START and not player.visible:
                self.update(DIALOG_SHOW)


    def update(self, state=None):
        """
        update the Dialog according to dialog state
        """
        logger.log(9, 'state=%s', formatstate(state))

        if state == DIALOG_SHOW:
            self.show()
        
        elif state == DIALOG_HIDE:
            # the dialog is visible, let's hide it
            self.stop()
            
        self.state = state


    def show(self):
        """
        Used when showing the dialog
        """
        logger.log(9, 'show()')
        self.player = audio.player.get()
        
        if self.player and self.detached:
            self.dialog = audio.show_play_state(dialog.PLAY_STATE_PLAY, 
                              self.player.item, self.get_time_info, type='play_state_mini')
            self.dialog.show()


    def hide(self):
        """
        Used when hiding the dialog
        """
        logger.log(9, 'hide()')
        self.player = None

        if self.dialog:
            self.dialog.hide()


    def stop(self):
        """
        Stops the dialog
        """
        logger.debug('stop()')

        if self.dialog and self.player and not self.detached:
            self.hide()
            self.dialog = None


    def get_time_info(self):
        """
        Callback for PlayStateDialog
        @return:    an array of audio info to be rendered on the dialog
        """
        if self.player is None:
            return None

        try:
            if self.player.item.length:
                return (self.player.item.elapsed, self.player.item.length)
            else:
                return (self.player.item.elapsed)
        except AttributeError:
            return None

