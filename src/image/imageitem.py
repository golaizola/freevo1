# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# imageitem.py - Item for image files
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
import logging
logger = logging.getLogger("freevo.image.imageitem")


import util
import os
import time
import datetime
import kaa.metadata as mmpython

import config
import viewer

from item import Item
from event import *


class ImageItem(Item):
    def __init__(self, url, parent, name=None, duration=config.IMAGEVIEWER_DURATION):
        """
        Default constructor for an image item
        """
        #_debug_("imageitem.ImageItem.__init__(url, parent, name=%s, duration=%s)" % (name, duration), 2)
        self.type = 'image'
        self.autovars = [ ( 'rotation', 0 ) ]
        Item.__init__(self, parent)

        if name:
            self.name = name

        self.set_url(url, search_image=False)

        if self.mode == 'file':
            self.image = self.filename
        self.duration = duration
        self.exif_thumbnail = config.IMAGE_USE_EXIF_THUMBNAIL


    def __getitem__(self, key):
        """
        returns the specific attribute as string or an empty string
        """
        #_debug_("__getitem__(self=%s, key=%s)" % (self.filename, key), 2)
        if key == "geometry":
            if self['width'] and self['height']:
                return config.IMAGE_GEOMETRY_FORMAT % (self['width'], self['height'])
            return ''

        if key == "date":
            try:
                t = str(Item.__getitem__(self, key))
                if t and t != '':
                    return time.strftime(config.IMAGE_DATETIME_FORMAT,
                                         time.strptime(str(t), '%Y:%m:%d %H:%M:%S'))
                else:
                    # last resort, try timestamp
                    t = Item.__getitem__(self, 'timestamp')
                    return datetime.datetime.fromtimestamp(t)
            except:
                pass

        logger.log( 9, "__getitem__(self=%s, key=%s, res=%r)", self.filename, key, Item.__getitem__(self, key))
        return Item.__getitem__(self, key)


    def sort(self, mode=None):
        """
        Returns the string how to sort this item
        """
        logger.log( 9, "sort(self, mode=%s)", mode)
        if mode == 'date':
            return u'%s%s' % (os.stat(self.filename).st_ctime, Unicode(self.filename))
        return Unicode(self.filename)


    def actions(self):
        """
        return a list of possible actions on this item.
        """
        logger.log( 9, "actions(self)")
        return [ ( self.view, _('View Image') ) ]


    def cache(self):
        """
        caches (loads) the next image
        """
        logger.log( 9, "cache(self)")
        viewer.get_singleton().cache(self)


    def view(self, arg=None, menuw=None):
        """
        view the image
        """
        logger.log( 9, "view(self, arg=%s, menuw=%s)", arg, menuw)
        if not self.menuw:
            self.menuw = menuw
        self.parent.current_item = self

        if self.menuw.visible:
            self.menuw.hide()

        viewer.get_singleton().view(self, rotation=self['rotation'])

        if self.parent and hasattr(self.parent, 'cache_next'):
            self.parent.cache_next()


    def rename_possible(self):
        """
        Returns True if the image item can be renamed.
        """
        try:
            if self.info and self.parent.DIRECTORY_USE_MEDIAID_TAG_NAMES and self.info['title']:
                # sorry, unable to edit media tag info
                return False
        except:
            pass
        return self.files and not self.files.read_only
