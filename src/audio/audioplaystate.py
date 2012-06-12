# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# audio play state dialogs 
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
# ----------------------------------------------------------------------- */
"""
"""
import logging
logger = logging.getLogger("freevo.audio.audioplaystate")
import time
import string
import config 
import util
from dialog.dialogs import PlayStateDialog


class AudioPlayStateDialog(PlayStateDialog):
    """
    Low priority dialog to display play state and time information.
    """

    UPDATE_INTERVAL = 0.25

    def __init__(self, state, item, get_time_info=None, type='play_state'):
        """
        Creates a new instance.

        @param state: The play state can be one of the following:
         - play
         - pause
         - rewind
         - fastforward
         - seekback
         - seekforward
         - slow
         - fast
         - info
         - stop

        @param type: Either full or mini play state dialog. Default is full.
         - play_state          - full size dialog, default
         - play_state_mini     - used by detached audio player for example

        @param get_time_info: A function to call to retrieve information about the
        current position and total play time, or None if not available. The function
        will return a tuple of elapsed time, total time and percent through the file.
        Both total time and percent position are optional.
        """
        super(AudioPlayStateDialog, self).__init__(state, item, get_time_info, type)
        self.update_interval = AudioPlayStateDialog.UPDATE_INTERVAL
        self.duration = 0
        self.mode     = 'audio'
           

    def get_info_dict(self):

        current_time = 0
        current_time_str = ''
        total_time = 0
        total_time_str = ''
        percent_pos = 0.0
        percent_str = ''

        if self.get_time_info:
            time_info = self.get_time_info()

        if time_info:
            
            current_time = time_info[0]
            current_time_hours = current_time / (60 * 60)
            current_time_minutes = (current_time / 60) - (current_time_hours * 60)
            current_time_seconds = current_time - (((current_time_hours * 60) + current_time_minutes) * 60)
            current_time_str = '%02d:%02d:%02d' % (current_time_hours, current_time_minutes, current_time_seconds)

            if len(time_info) > 1:
                total_time = time_info[1]
                total_time_hours = total_time / (60 * 60)
                total_time_minutes = (total_time / 60) - (total_time_hours * 60)
                total_time_seconds = total_time - (((total_time_hours * 60) + total_time_minutes) * 60)

                total_time_str   = '%02d:%02d:%02d' % (total_time_hours, total_time_minutes, total_time_seconds)

                if len(time_info) > 2:
                    percent_pos = time_info[2]
                else:
                    if total_time > 0:
                        percent_pos = float(current_time) / float(total_time)
                    else:
                        percent_pos = 0.0
                percent_str = '%d%%' % (percent_pos * 100)

        attr = {}
        attr['image'] = self.item.image
        # Skip thumbnails
        if attr['image'] and attr['image'].endswith('.raw'):
            attr['image'] = None
        if not attr['image']:
            attr['image'] = self.item.parent.image
        if not attr['image']:   
            attr['image'] = "nocover_audio.png" 

        attributes = ['date', 'artist', 'album', 'title', 'name', 'audio_codec', 'trackno', 'trackof']
        for attribute in attributes:
            attr[attribute] = self.item.getattr(attribute)
            if not attr[attribute] and self.item.parent.type == 'audio':
                attr[attribute] = self.item.parent.getattr(attribute)
            if not attr[attribute]:
                attr[attribute] = ""
            # attr[attribute] = attribute.title() + ": " + attr[attribute]

        now = time.localtime()
        if config.CLOCK_FORMAT:
            format = config.CLOCK_FORMAT
        else:
            format ='%a %d %H:%M'

        time_str = time.strftime(format, now)
        date_str = time.strftime("%Y/%m/%y", now)

        return {'state': self.state,
                'mode': self.mode,
                'title': attr['title'],
                'image': attr['image'],
                'artist': attr['artist'],
                'year': attr['date'],
                'album': attr['album'],
                'name': attr['name'],
                'audio_codec': attr['audio_codec'],
                'trackno': str(attr['trackno']),
                'trackof': str(attr['trackof']),
                'time_raw': now,
                'time': time_str,
                'date': date_str,
                'current_time': current_time,
                'total_time': total_time,
                'current_time_str': current_time_str,
                'total_time_str': total_time_str,
                'percent': percent_pos,
                'percent_str': percent_str
                }

