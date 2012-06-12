# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# Freevo default skin
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
Freevo default skin
"""
import logging
logger = logging.getLogger("freevo.skins.main.main")

import os, copy
import stat
import traceback

import config
import util
import osd

from area import Skin_Area
from gui  import GUIObject

import xml_skin
import screen

from animation import render, Transition
import pygame

import kaa

from skin import TRANSITION_IN,TRANSITION_OUT,TRANSITION_PAGE,TRANSITION_NONE

# Create the OSD object
osd = osd.get_singleton()
render = render.get_singleton()
TRANSITION_STEPS=20
###############################################################################
# Skin main functions
###############################################################################


class Skin:
    """
    main skin class
    """
    Rectange = xml_skin.Rectangle
    Image    = xml_skin.Image
    Area     = Skin_Area

    def __init__(self):
        """
        init the skin engine
        """
        global skin_engine
        skin_engine = self

        self.display_style = { 'menu' : 0 }
        self.force_redraw  = True
        self.last_draw     = None, None, None
        self.screen        = screen.get_singleton()
        self.areas         = {}
        self.suspended     = False
        self.transitioning = False
        self.current_screen= None
        self.next_screen   = None
        self.timer         = None

        # load default areas
        from listing_area   import Listing_Area
        from tvlisting_area import TVListing_Area
        from view_area      import View_Area
        from info_area      import Info_Area
        from default_areas  import Screen_Area, Title_Area, Subtitle_Area, Plugin_Area
        from scrollabletext_area import Scrollabletext_Area
        from textentry_area import Textentry_Area
        from buttongroup_area import Buttongroup_Area

        for a in ('screen', 'title', 'subtitle', 'view', 'listing', 'info',
                'plugin', 'scrollabletext', 'textentry',  'buttongroup'):
            self.areas[a] = eval('%s_Area()' % a.capitalize())
        self.areas['tvlisting'] = TVListing_Area()

        self.storage_file = os.path.join(config.FREEVO_CACHEDIR, 'skin-%s' % os.getuid())
        self.storage = util.read_pickle(self.storage_file)
        if self.storage:
            if not config.SKIN_XML_FILE:
                config.SKIN_XML_FILE = self.storage['SKIN_XML_FILE']
            else:
                logger.log( 9, 'skin forced to %s', config.SKIN_XML_FILE)
        else:
            if not config.SKIN_XML_FILE:
                config.SKIN_XML_FILE = config.SKIN_DEFAULT_XML_FILE
            self.storage = {}

        # load the fxd file
        self.settings = xml_skin.XMLSkin()
        self.set_base_fxd(config.SKIN_XML_FILE)

        if config.SKIN_SCREEN_TRANSITION == 'blend':
            self.do_transition = self.do_blend_transition
        elif config.SKIN_SCREEN_TRANSITION == 'slide':
            self.do_transition = self.do_slide_transition
        else:
            print 'WARNING: Unknown screen transition, disabling transitions'
            config.SKIN_USE_SCREEN_TRANSITIONS = False
            config.SKIN_USE_PAGE_TRANSITIONS = False


    def cachename(self, filename):
        """
        create cache name
        """
        geo  = '%sx%s-%s-%s' % (osd.width, osd.height, config.OSD_OVERSCAN_LEFT, config.OSD_OVERSCAN_TOP)
        return vfs.getoverlay('%s.skin-%s-%s' % (filename, config.SKIN_XML_FILE, geo))


    def save_cache(self, settings, filename):
        """
        cache the fxd skin settings in 'settings' to the OVERLAY_DIR cachfile
        for filename and this resolution
        """
        cache = self.cachename(filename)
        if cache:
            # delete font object, because it can't be pickled
            for f in settings.font:
                del settings.font[f].font
            # save object and version information
            util.save_pickle((xml_skin.FXD_FORMAT_VERSION, settings), cache)
            # restore font object
            for f in settings.font:
                settings.font[f].font = osd.getfont(settings.font[f].name, settings.font[f].size)


    def load_cache(self, filename):
        """
        load a skin cache file
        """
        if hasattr(self, '__last_load_cache__') and self.__last_load_cache__[0] == filename:
            return self.__last_load_cache__[1]

        if not os.path.isfile(filename):
            return None

        cache = self.cachename(filename)
        if not cache:
            return None

        if not os.path.isfile(cache):
            return None

        version, settings = util.read_pickle(cache)
        if not settings or version != xml_skin.FXD_FORMAT_VERSION:
            return None

        pdir = os.path.join(config.SHARE_DIR, 'skins/plugins')
        if os.path.isdir(pdir):
            ffiles = util.match_files(pdir, [ 'fxd' ])
        else:
            ffiles = []

        for f in settings.fxd_files:
            if not os.path.dirname(f).endswith(pdir):
                ffiles.append(f)

        # check if all files used by the skin are not newer than
        # the cache file
        ftime = os.stat(cache)[stat.ST_MTIME]
        for f in ffiles:
            if os.stat(f)[stat.ST_MTIME] > ftime:
                return None

        # restore the font objects
        for f in settings.font:
            settings.font[f].font = osd.getfont(settings.font[f].name, settings.font[f].size)
        self.__last_load_cache__ = filename, settings
        return settings


    def register(self, type, areas):
        """
        register a new type objects to the skin
        """
        setattr(self, '%s_areas' % type, [])
        for a in areas:
            if isinstance(a, str):
                getattr(self, '%s_areas' % type).append(self.areas[a])
            else:
                getattr(self, '%s_areas' % type).append(a)


    def delete(self, type):
        """
        delete information about a special skin type
        """
        exec('del self.%s_areas' % type)
        self.last_draw = None, None, None


    def change_area(self, name, module, object):
        """
        replace an area with the code from module.object() from skins/plugins
        """
        exec('import skins.plugins.%s' % module)
        self.areas[name] = eval('skins.plugins.%s.%s()' % (module, object))


    def set_base_fxd(self, name):
        """
        set the basic skin fxd file
        """
        config.SKIN_XML_FILE = os.path.splitext(os.path.basename(name))[0]
        logger.debug('load basic skin settings: %s', config.SKIN_XML_FILE)

        # try to find the skin xml file
        if not self.settings.load(name, clear=True):
            print "skin not found, using fallback skin"
            self.settings.load('basic.fxd', clear=True)

        for dir in config.cfgfilepath:
            local_skin = '%s/local_skin.fxd' % dir
            if os.path.isfile(local_skin):
                logger.log( 9, 'Skin: Add local config %s to skin', local_skin)
                self.settings.load(local_skin)
                break

        self.storage['SKIN_XML_FILE'] = config.SKIN_XML_FILE
        util.save_pickle(self.storage, self.storage_file)

        if self.storage.has_key(config.SKIN_XML_FILE):
            self.display_style['menu'] = self.storage[config.SKIN_XML_FILE]
        else:
            self.display_style['menu'] = 0


    def load(self, filename, copy_content = 1):
        """
        return an object with new skin settings
        """
        logger.debug('load additional skin info: %s', filename)
        if filename and vfs.isfile(vfs.join(filename, 'folder.fxd')):
            filename = vfs.abspath(os.path.join(filename, 'folder.fxd'))

        elif filename and vfs.isfile(filename):
            filename = vfs.abspath(filename)

        else:
            return None

        settings = self.load_cache(filename)
        if settings:
            return settings

        if copy_content:
            settings = copy.copy(self.settings)
        else:
            settings = xml_skin.XMLSkin()

        if not settings.load(filename, clear=True):
            return None

        self.save_cache(settings, filename)
        return settings



    def get_skins(self):
        """
        return a list of all possible skins with name, image and filename
        """
        ret = []
        skin_files = util.match_files(os.path.join(config.SKIN_DIR, 'xbmc'), ['fxd'])

        # image is not usable stand alone
        skin_files.remove(os.path.join(config.SKIN_DIR, 'xbmc/image.fxd'))
        skin_files.remove(os.path.join(config.SKIN_DIR, 'xbmc/basic.fxd'))

        for skin in skin_files:
            name  = os.path.splitext(os.path.basename(skin))[0]
            if os.path.isfile('%s.png' % os.path.splitext(skin)[0]):
                image = '%s.png' % os.path.splitext(skin)[0]
            elif os.path.isfile('%s.jpg' % os.path.splitext(skin)[0]):
                image = '%s.jpg' % os.path.splitext(skin)[0]
            else:
                image = None
            ret += [ (name, image, skin) ]
        return ret


    def get_settings(self):
        """
        return the current loaded settings
        """
        return self.settings


    def toggle_display_style(self, menu):
        """
        Toggle display style
        """
        if isinstance(menu, str):
            if not self.display_style.has_key(menu):
                self.display_style[menu] = 0
            self.display_style[menu] = (self.display_style[menu] + 1) % len(self.settings.sets[menu].style)
            return 1

        if menu.force_skin_layout != -1:
            return 0

        if menu and menu.skin_settings:
            settings = menu.skin_settings
        else:
            settings = self.settings

        if settings.special_menu.has_key(menu.item_types):
            area = settings.special_menu[menu.item_types]
        else:
            area = settings.default_menu['default']

        if self.display_style['menu'] >=  len(area.style):
            self.display_style['menu'] = 0
        self.display_style['menu'] = (self.display_style['menu'] + 1) % len(area.style)

        self.storage[config.SKIN_XML_FILE] = self.display_style['menu']
        util.save_pickle(self.storage, self.storage_file)
        return 1


    def get_display_style(self, menu=None):
        """
        return current display style
        """
        if isinstance(menu, str):
            if not self.display_style.has_key(menu):
                self.display_style[menu] = 0
            return self.display_style[menu]

        if menu:
            if menu.force_skin_layout != -1:
                return menu.force_skin_layout
        return self.display_style['menu']


    def __find_current_menu__(self, widget):
        if not widget:
            return None
        if not hasattr(widget, 'menustack'):
            return self.__find_current_menu__(widget.parent)
        return widget.menustack[-1]


    def get_popupbox_style(self, widget=None):
        """
        This function returns style information for drawing a popup box.

        @returns: backround, spacing, color, font, button_default, button_selected
        background is ('image', Image) or ('rectangle', Rectangle)

        Image attributes: filename

        Rectangle attributes: color (of the border), size (of the border), bgcolor
        (fill color), radius (round box for the border). There are also x, y, width and
        height as attributes, but they may not be needed for the popup box

        button_default, button_selected are XML_item attributes: font, rectangle
        (Rectangle)

        All fonts are Font objects attributes: name, size, color, shadow shadow
        attributes: visible, color, x, y
        """
        menu = self.__find_current_menu__(widget)

        if menu and hasattr(menu, 'skin_settings') and menu.skin_settings:
            settings = menu.skin_settings
        else:
            settings = self.settings

        layout = settings.popup

        background = []
        for bg in layout.background:
            if isinstance(bg, xml_skin.Image):
                background.append(('image', bg))
            elif isinstance(bg, xml_skin.Rectangle):
                background.append(('rectangle', bg))

        return layout.content, background


    def get_font(self, name):
        """
        Get the skin font object 'name'. Return the default object if
        a font with this name doesn't exists.
        """
        try:
            return self.settings.font[name]
        except:
            return self.settings.font['default']


    def get_image(self, name):
        """
        Get the skin image object 'name'. Return None if
        an image with this name doesn't exists.
        """
        try:
            return self.settings.images[name]
        except:
            return None


    def get_icon(self, name):
        """
        Get the icon object 'name'. Return the icon in the theme dir if it
        exists, else try the normal image dir. If not found, return ''
        """
        icon = util.getimage(os.path.join(self.settings.icon_dir, name))
        if icon:
            return icon
        return util.getimage(os.path.join(config.ICON_DIR, name), '')


    def items_per_page(self, (type, object)):
        """
        Get the number of items per menu page
        (cols, rows) for normal menu and
        rows         for the tv menu
        """
        if type == 'tv':
            info = self.areas['tvlisting']
            info = info.get_items_geometry(self.settings, object, self.get_display_style('tv'))
            return (info[4], info[-1])

        if object.skin_settings:
            settings = object.skin_settings
        else:
            settings = self.settings

        menu = None
        if type == 'menu':
            menu = object

        info = self.areas['listing']
        rows, cols = info.get_items_geometry(settings, object, self.get_display_style(menu))[:2]
        # Prevent problems when trying to draw menus that have no rows or columns.
        # Always better to draw something and then fix the skin rather than going
        # into an infinite loop in MenuWidget when trying to rebuild the page.
        if rows == 0:
            row = 1
        if cols == 0:
            cols = 1
        return (cols, rows)


    def clear(self, osd_update=True):
        """
        Clean the screen
        """
        logger.debug('Skin.clear(osd_update=%r)', osd_update)
        self.force_redraw = True
        osd.clearscreen(osd.COL_BLACK)
        if osd_update:
            osd.update()


    def suspend(self):
        logger.debug('Skin.suspend()')
        if not self.suspended:
            self.suspended = True
            if self.timer:
                self.timer.stop()


    def resume(self):
        logger.debug('Skin.resume()')
        if self.suspended:
            self.suspended = False


    def redraw(self):
        """
        Redraw the current screen
        """
        logger.log( 8, 'Skin.redraw()')
        if self.last_draw[0] and self.last_draw[1]:
            self.draw(self.last_draw[0], self.last_draw[1], self.last_draw[2])


    def prepare(self):
        """
        Prepare the skin
        """
        self.settings.prepare()


    def draw(self, type, object, menu=None, transition=TRANSITION_NONE):
        """
        Draw the object.  object may be a menu widget, a table for the tv menu
        or an audio item for the audio player.
        """
        logger.log( 9, 'Skin.draw(type=%r, object=%r, menu=%r)', type, object, menu)
        if self.suspended:
            return

        if isinstance(object, GUIObject):
            # handling for gui objects: are they visible? what about children?
            if not object.visible:
                return

            draw_allowed = True
            for child in object.children:
                draw_allowed = draw_allowed and not child.visible

            if not draw_allowed:
                self.force_redraw = True
                return

        settings = self.settings

        old_screen = None


        if type == 'menu':
            if menu is None:
                menu = object.menustack[-1]
            if menu.selected and hasattr(menu.selected, 'skin_settings') and menu.selected.skin_settings:
                settings = menu.selected.skin_settings
            elif menu.skin_settings:
                settings = menu.skin_settings
            # XXX FIXME
            if len(object.menustack) == 1:
                menu.item_types = 'main'
            style = self.get_display_style(menu)
        else:
            try:
                if not object.visible:
                    return
            except AttributeError:
                pass
            if hasattr(object, 'skin_settings') and object.skin_settings:
                settings = object.skin_settings
            style = self.get_display_style(type)

        if self.last_draw[0] != type:
            self.force_redraw = True
            self.all_areas    = getattr(self, '%s_areas' % type)

        self.last_draw = type, object, menu

        try:
            self.screen.clear()
            for a in self.all_areas:
                a.draw(settings, object, menu, style, type, self.force_redraw)

            if self.transitioning:
                ml = osd.main_layer
                osd.main_layer = self.next_screen
                self.screen.show(self.force_redraw)
                osd.main_layer = ml
            else:
                if not config.SKIN_USE_PAGE_TRANSITIONS and transition == TRANSITION_PAGE:
                    transition = TRANSITION_NONE

                if transition and config.SKIN_USE_SCREEN_TRANSITIONS:
                    self.do_transition(transition)
                else:
                    osd.update([self.screen.show(self.force_redraw)])

            self.force_redraw = False
        except UnicodeError, e:
            print '******************************************************************'
            print 'Unicode Error: %s' % e
            print 'Please report the following lines to the freevo users mailing list'
            print 'https://lists.sourceforge.net/lists/listinfo/freevo-users'
            print
            print traceback.print_exc()
            print
            print type, object
            if type == 'menu':
                for i in object.menustack[-1].choices:
                    print i
            print
            raise UnicodeError, e


    def do_blend_transition(self, transition):
        self.current_screen = osd.main_layer.convert()
        self.screen.show(True)
        self.next_screen = osd.main_layer.convert()

        self.transitioning = True
        self.steps = 0
        self.timer = kaa.Timer(self.do_blend_step, transition)
        self.do_blend_step(transition)
        self.timer.start(0.01)

    def do_blend_step(self, transition):
        self.steps += 1
        if self.steps == TRANSITION_STEPS:
            self.timer.stop()
            self.timer = None
            self.next_screen.set_alpha(255)
            osd.main_layer.blit(self.next_screen, (0,0))
            osd.update()
            self.transitioning = False
            return
        osd.main_layer.blit(self.current_screen, (0,0))
        self.next_screen.set_alpha((255 * self.steps) / TRANSITION_STEPS)
        osd.main_layer.blit(self.next_screen, (0,0))
        osd.update()

    def do_slide_transition(self, transition):
        if transition == TRANSITION_PAGE:
            self.do_blend_transition(transition)
            return

        self.current_screen = osd.main_layer.convert()
        self.screen.show(True)
        self.next_screen = osd.main_layer.convert()

        self.transitioning = True
        self.steps = 0
        self.timer = kaa.Timer(self.do_slide_step, transition)
        self.do_slide_step(transition)
        self.timer.start(0.01)

    def do_slide_step(self, transition):
        self.steps += 1
        if self.steps == TRANSITION_STEPS:
            self.timer.stop()
            self.timer = None
            self.next_screen.set_alpha(255)
            osd.main_layer.blit(self.next_screen, (0,0))
            osd.update()
            self.transitioning = False
            return
        
        osd.main_layer.fill(0)
        if transition == TRANSITION_IN:
            r = self.current_screen.get_rect()
            self.current_screen.set_alpha((255 * (TRANSITION_STEPS - self.steps) / TRANSITION_STEPS))
            osd.main_layer.blit(self.current_screen, (0,0), r)
            r = self.next_screen.get_rect()            
            r.width = (r.width * self.steps) / TRANSITION_STEPS
            osd.main_layer.blit(self.next_screen, (self.next_screen.get_width() - r.width,0), r)
        else:
            self.next_screen.set_alpha((255 * self.steps)/TRANSITION_STEPS)
            r = self.next_screen.get_rect()
            osd.main_layer.blit(self.next_screen, (0,0), r)
            r = self.current_screen.get_rect()
            r.width = (r.width * (TRANSITION_STEPS - self.steps)) / TRANSITION_STEPS
            osd.main_layer.blit(self.current_screen, (self.current_screen.get_width() - r.width,0), r)

        osd.update()
