#if 0
# -----------------------------------------------------------------------
# listing_area.py - A listing area for the Freevo skin
# -----------------------------------------------------------------------
# $Id$
#
# Notes: WIP
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.9  2003/03/14 19:38:50  dischi
# some cosmetic fixes
#
# Revision 1.8  2003/03/13 21:03:51  dischi
# only load it when necessary
#
# Revision 1.7  2003/03/13 21:02:05  dischi
# misc cleanups
#
# Revision 1.6  2003/03/07 22:54:11  dischi
# First version of the extended menu with image support. Try the music menu
# and press DISPLAY
#
# Revision 1.5  2003/03/07 17:28:19  dischi
# small fixes
#
# Revision 1.4  2003/03/05 21:56:10  dischi
# Small changes to integrate the audio player
#
# Revision 1.3  2003/03/02 19:03:42  dischi
# Add [] for directories
#
# Revision 1.2  2003/03/01 00:12:18  dischi
# Some bug fixes, some speed-ups. blue_round2 has a correct main menu,
# but on the main menu the idle bar still flickers (stupid watermarks),
# on other menus it's ok.
#
# Revision 1.1  2003/02/27 22:39:50  dischi
# The view area is working, still no extended menu/info area. The
# blue_round1 skin looks like with the old skin, blue_round2 is the
# beginning of recreating aubin_round1. tv and music player aren't
# implemented yet.
#
# Revision 1.5  2003/02/26 21:21:11  dischi
# blue_round1.xml working
#
# Revision 1.4  2003/02/26 19:59:26  dischi
# title area in area visible=(yes|no) is working
#
# Revision 1.3  2003/02/26 19:18:53  dischi
# Added blue1_small and changed the coordinates. Now there is no overscan
# inside the skin, it's only done via config.OVERSCAN_[XY]. The background
# images for the screen area should have a label "background" to override
# the OVERSCAN resizes.
#
# Revision 1.2  2003/02/25 23:27:36  dischi
# changed max usage
#
# Revision 1.1  2003/02/25 22:56:00  dischi
# New version of the new skin. It still looks the same (except that icons
# are working now), but the internal structure has changed. Now it will
# be easier to do the next steps.
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
#endif


import copy

import osd
import pygame

osd = osd.get_singleton()

from area import Skin_Area
from skin_utils import *


# Set to 1 for debug output
DEBUG = 1

TRUE = 1
FALSE = 0


class Listing_Area(Skin_Area):
    """
    this call defines the listing area
    """

    def __init__(self, parent, screen):
        Skin_Area.__init__(self, 'listing', screen)
        self.last_choices = ( None, None )


    def get_items_geometry(self, settings, menu, display_style):
        """
        get the geometry of the items. How many items per row/col, spaces
        between each item, etc
        """

        # store the old values in case we are called by ItemsPerMenuPage
        backup = ( self.area_val, self.layout)

        self.display_style = display_style
        self.init_vars(settings, menu.item_types)

        layout    = self.layout
        area      = self.area_val
        content   = self.calc_geometry(layout.content, copy_object=TRUE)

        if content.type == 'text':
            items_w = content.width
            items_h = 0
        elif content.type == 'image':
            items_w = 0
            items_h = 0

        possible_types = {}

        hskip = 0
        vskip = 0
        for i in menu.choices:
            if hasattr(i, 'display_type') and i.display_type and \
               content.types.has_key(i.display_type):
                possible_types[i.display_type] = content.types[i.display_type]
            else:
                possible_types['default'] = content.types['default']

            if hasattr(i, 'display_type') and i.display_type and \
               content.types.has_key('%s selected' % i.display_type):
                possible_types['%s selected' % i.display_type] = \
                                   content.types['%s selected' % i.display_type]
            else:
                possible_types['selected'] = content.types['selected']
                
        # get the max height of a text item
        if content.type == 'text':
            for t in possible_types:
                ct = possible_types[t]
                font = self.get_font(ct.font)

                rh = 0
                rw = 0
                if ct.rectangle:
                    rw, rh, r = self.get_item_rectangle(ct.rectangle, content.width, font.h)
                    hskip = min(hskip, r.x)
                    vskip = min(vskip, r.y)

                items_h = max(items_h, font.h, rh)

        elif content.type == 'image':
            for t in possible_types:
                ct = possible_types[t]
                rh = 0
                rw = 0
                if ct.rectangle:
                    rw, rh, r = self.get_item_rectangle(ct.rectangle, ct.width, ct.height)
                    hskip = min(hskip, r.x)
                    vskip = min(vskip, r.y)

                items_h = max(items_h, ct.height, rh)
                items_w = max(items_w, ct.width, rw)
            
        # restore
        self.area_val, self.layout = backup

        # shrink width for text menus
        # FIXME
        width = content.width

        if items_w > width:
            width, items_w = width - (items_w - width), width 

        cols = 0
        rows = 0

        while (cols + 1) * (items_w + content.spacing) - \
              content.spacing <= content.width:
            cols += 1

        while (rows + 1) * (items_h + content.spacing) - \
              content.spacing <= content.height:
            rows += 1

        # return cols, rows, item_w, item_h, content.width
        return (cols, rows, items_w + content.spacing,
                items_h + content.spacing, -hskip, -vskip, width)



    def update_content_needed(self):
        """
        check if the content needs an update
        """
        if self.last_choices[0] != self.menu.selected:
            return TRUE

        i = 0
        for choice in self.menuw.menu_items:
            if self.last_choices[1][i] != choice:
                return TRUE
            i += 1

        
    def update_content(self):
        """
        update the listing area
        """

        menuw     = self.menuw
        menu      = self.menu
        settings  = self.settings
        layout    = self.layout
        area      = self.area_val
        content   = self.calc_geometry(layout.content, copy_object=TRUE)

        cols, rows, hspace, vspace, hskip, vskip, width = \
              self.get_items_geometry(settings, menu, self.display_style)

        x0 = content.x
        y0 = content.y

        current_col = 1
        
        if content.type == 'image':
            width  = hspace - content.spacing
            height = vspace - content.spacing
            
        for choice in menuw.menu_items:
            if choice == menu.selected:
                if content.types.has_key('% selected' % choice.type):
                    val = content.types['% selected' % choice.type]
                else:
                    val = content.types['selected']
            else:
                if content.types.has_key(choice.type):
                    val = content.types[choice.type]
                else:
                    val = content.types['default']
                
            text = choice.name
            if not text:
                text = "unknown"

            if choice.type == 'playlist':
                text = 'PL: %s' % text

            if choice.type == 'dir' and choice.parent and \
               choice.parent.type != 'mediamenu':
                text = '[%s]' % text

            if content.type == 'text':
                font = self.get_font(val.font)

                if choice.icon:
                    image = osd.loadbitmap(choice.icon)
                    if image:
                        image = pygame.transform.scale(image, (vspace-content.spacing,
                                                               vspace-content.spacing))
                        self.draw_image(image, (x0, y0))
                        icon_x = vspace
                else:
                    icon_x = 0

                if val.rectangle:
                    r = self.get_item_rectangle(val.rectangle, width, font.h)[2]
                    self.drawroundbox(x0 + hskip + r.x + icon_x, y0 + vskip + r.y,
                                      r.width - icon_x, r.height, r)

                if content.type == 'text':
                    self.write_text(text, font, content, x=x0 + hskip + icon_x,
                                    y=y0 + vskip, width=width-icon_x, height=-1,
                                    align_h=val.align, mode='hard')


            elif content.type == 'image':
                if val.rectangle:
                    r = self.get_item_rectangle(val.rectangle, val.width, val.height)[2]
                    self.drawroundbox(x0 + hskip + r.x, y0 + vskip + r.y,
                                      r.width, r.height, r)


                image = format_image(settings, choice, val.width, val.height, force=TRUE)
                if image:
                    i_w, i_h = image.get_size()

                    addx = 0
                    addy = 0
                    if content.align == 'center' and i_w < val.width:
                        addx = (val.width - i_w) / 2

                    if content.align == 'right' and i_w < val.width:
                        addx = val.width - i_w
            
                    if content.valign == 'center' and i_h < val.height:
                        addy = (val.height - i_h) / 2

                    if content.valign == 'bottom' and i_h < val.height:
                        addy = val.height - i_h

                    self.draw_image(image, (x0 + hskip + addx, y0 + vskip + addy))
                    
            else:
                print 'no support for content type %s' % content.type

            if current_col == cols:
                x0 = content.x
                y0 += vspace
                current_col = 1
            else:
                x0 += hspace
                current_col += 1
                
        self.last_choices = (menu.selected, copy.copy(menuw.menu_items))
