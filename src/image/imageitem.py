#if 0 /*
# -----------------------------------------------------------------------
# imageitem.py - Item for image files
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.11  2003/07/23 07:12:12  gsbarbieri
# Added support for 'geometry' attribute ( getattr() now returns 'widthxheight', like videoitem )
#
# Revision 1.10  2003/07/02 20:10:28  dischi
# added to mmpython support, removed old stuff
#
# Revision 1.9  2003/04/06 21:12:57  dischi
# o Switched to the new main skin
# o some cleanups (removed unneeded inports)
#
# Revision 1.8  2003/03/16 19:28:04  dischi
# Item has a function getattr to get the attribute as string
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

import util
import os

import viewer
import mmpython

from item import Item


class ImageItem(Item):
    def __init__(self, filename, parent, name = None, duration = 0):
        if parent and parent.media:
            url = 'cd://%s:%s:%s' % (parent.media.devicename, parent.media.mountdir,
                                     filename[len(parent.media.mountdir)+1:])
        else:
            url = filename

        Item.__init__(self, parent, mmpython.parse(url))
        self.type     = 'image'
        self.filename = filename
        self.image    = filename
        self.duration = duration
        
        # set name
        if name:
            self.name = name
        elif not self.name:
            self.name = util.getname(filename)

        self.image_viewer = viewer.get_singleton()

    def getattr(self, attr):
        """
        return the specific attribute as string or an empty string
        """
        if attr in [ "geometry" ]:
            try:
                image = self.info
                if attr == 'geometry':
                    print "geometry=%sx%s" % (image.width, image.height)
                    return '%sx%s' % (image.width, image.height)
            except:
                pass
            
        return Item.getattr(self, attr)
        

    def copy(self, obj):
        """
        Special copy value VideoItems
        """
        Item.copy(self, obj)
        if obj.type == 'image':
            self.duration = obj.duration
            

    def sort(self, mode=None):
        """
        Returns the string how to sort this item
        """
        if mode == 'date':
            return '%s%s' % (os.stat(self.filename).st_ctime, self.filename)
        return self.filename


    def actions(self):
        """
        return a list of possible actions on this item.
        """
        return [ ( self.view, 'View Image' ) ]


    def cache(self):
        """
        caches (loads) the next image
        """
        self.image_viewer.cache(self)


    def view(self, arg=None, menuw=None):
        """
        view the image
        """
        if not self.menuw:
            self.menuw = menuw
        self.parent.current_item = self

        if self.menuw.visible:
            self.menuw.hide()

        self.image_viewer.view(self)

        if self.parent and hasattr(self.parent, 'cache_next'):
            self.parent.cache_next()


