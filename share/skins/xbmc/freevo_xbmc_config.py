# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# XBMC Skin configuration
# -----------------------------------------------------------------------
# Notes:
#    This file contains the Freevo's XBMC skin specific variables that
#    this skin needs to have configured to function properly
#    Same rules as for freevo_config.py or local_config.py.
#    Read description and instructions there.
#    You can edit this file, or better, put a file named local_xbmc_config.py
#    in the same directory as local_config.py and add your changes there but 
#    this is hightly not recommended as it's almnost guaranteed that it'll
#    break the skin code.
#
# How config files are loaded:
#
# 1. This file is loaded after freevo_config.py and local_config.py 
#    to make sure we override a varialbles that user could have altered 
#    in local_config.py
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
import config
import plugin
#import logging
#logger = logging.getLogger("freevo.skin.xbmc.config")

# failsafe
if config.SKIN_XML_FILE == 'xbmc':

    if plugin.is_active('audio.detachbar'):
        plugin.remove('audio.detachbar')
        
    if not plugin.is_active('audio.detachdialog'):
        plugin.activate('audio.detachdialog')

    # ======================================================================
    # Freevo SKIN settings:
    # ======================================================================
    #
    # Skin file that contains the actual skin code. This is imported
    # from skin.py
    #
    SKIN_MODULE = 'xbmc'

    #
    # XML file used for the dialog skins.
    #
    DIALOG_SKIN_XML_FILE = 'xbmc'

    # Select a way when to switch to text view even if a image menu is there
    #
    # 1 = Force text view when all items have the same image and there are no
    #     directories
    # 2 = Ignore the directories, always switch to text view when all images
    #     are the same
    #
    SKIN_FORCE_TEXTVIEW_STYLE = 2

    # Loads skin fxd for individual items such as videoitems or audio items.
    # By default this is disabled as performance is poor (skin gets reloaded 
    # for each item in the dir) as well as there are issues with style switching
    # Will be dealt with with subsequent release.
    #
    SKIN_LOAD_FXD_FOR_ITEMS = False

    # Some items like videoitem displays screen for movie detais and hardcodes 
    # a lot of details.This tell the item that skin does handle all. In the future
    # oneclick weathger will be converted to use this variable thius making the 
    # dialogs fully skinnable.
    #
    #
    SKIN_HANDLES_DETAILS = True

    # If enabled sends 'info' state to the OSD dialog, otherwise will send 'play'
    # or 'pause' (depending on current state. Somne skins (like xbmc) do not use 'info'
    # state. Default value is True for backward compatibility.
    #
    OSD_TOGGLE_STATE_INFO = False

    # The following settings determine which features are available for
    # which media types.
    #
    # If you set this variable in a folder.fxd, the value is 1 (enabled)
    # or 0 (disabled).
    #
    # Examples:
    # To enable autoplay for audio and image files:
    DIRECTORY_AUTOPLAY_PLAYLISTS  = [ 'image', 'audio' ]
    
    # Use media id tags to generate the name of the item. This should be
    # enabled all the time. It should only be disabled for directories with
    # broken tags.
    #
    DIRECTORY_USE_MEDIAID_TAG_NAMES = 1

    # Format string for the directory listing
    #
    # Possible strings:
    # n=name, t=title, e=num of items, f=filename
    #
    # This will display track number, title and right aligned length
    # Requires DIRECTORY_AUDIO_MENU_TABLE to be set to (85, 15) for example
    #
    DIRECTORY_DIR_FORMAT_STRING = '%(t)s\tICON_RIGHT_NOICON_%(e)s'
    DIRECTORY_DIR_MENU_TABLE    = (80, 20)

    # Format string for the audio item names.
    #
    # Possible strings:
    # a=artist, l=album, n=tracknumber, t=title, y=year, f=filename, r=length
    #
    # This will display track number, title and right aligned length
    # Requires DIRECTORY_AUDIO_MENU_TABLE to be set to (85, 15) for example
    #
    DIRECTORY_AUDIO_FORMAT_STRING = '%(n)s  %(t)s\tICON_RIGHT_NOICON_%(r)s'

    # Sets table for audio menu items, useful for displaying track lenght for example
    #
    DIRECTORY_AUDIO_MENU_TABLE = (80, 20)

    # Format string for the video item names.
    #
    # Possible strings:
    # n=name, t=title, e=episode, s=season, f=filename, r=length
    #
    # This will display track number, title and right aligned length
    # Requires DIRECTORY_AUDIO_MENU_TABLE to be set to (85, 15) for example
    #
    DIRECTORY_VIDEO_FORMAT_STRING = '%(e)s  %(t)s\tICON_RIGHT_NOICON_%(r)s'

    # Sets table for video menu items, useful for displaying track lenght for example
    #
    DIRECTORY_VIDEO_MENU_TABLE    = (70, 30)

    # Format string for the image item names.
    #
    # Possible strings:
    # n=name, t=title, e=num of items, f=filename
    #
    # This will display track number, title and right aligned length
    # Requires DIRECTORY_AUDIO_MENU_TABLE to be set to (85, 15) for example
    #
    DIRECTORY_IMAGE_FORMAT_STRING = '%(t)s\tICON_RIGHT_NOICON_%(e)s'

    # Sets table for image menu items, useful for displaying number of images etc.
    #
    DIRECTORY_IMAGE_MENU_TABLE    = (75, 25)

    # How many steps back to take when exit the dir config menu, i.e. natural is 
    # to go back one menu but Freevo does not apply the changes until you reenter 
    # the directory again, hence the default is to go back one more level and reenter
    # the directory for changes to be applied.
    #
    DIRECTORY_MENU_BACK_STEPS     = 2
                          
                          