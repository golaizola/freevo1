# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# XML reader for the skin
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
logger = logging.getLogger("freevo.skins.main.xml_skin")


# some python stuff
import os
import copy
import types
import re
import traceback

import config
import util
import osd
import plugin


osd = osd.get_singleton()

geometry = (config.CONF.width, config.CONF.height)


FXD_FORMAT_VERSION = 2

#
# Help functions
#
attr_global_dict = None

def eval_attr(attr_value):
    """
    Returns attr_value if it is not a string or evaluates it substituting max
    for 'MAX' or 'max' in the attr_value string.
    """
    global attr_global_dict

    if attr_global_dict is None:
        attr_global_dict = {}

        # Setup idlebar related values
        p = plugin.getbyname('idlebar')
        if p:
            attr_global_dict['idlebar'] = 1
            attr_global_dict['idlebar_height'] = 60
        else:
            attr_global_dict['idlebar'] = 0
            attr_global_dict['idlebar_height'] = 0

        # Setup buttonbar related values
        p = plugin.getbyname('buttonbar')
        if p:
            attr_global_dict['buttonbar'] = 1
            attr_global_dict['buttonbar_height'] = config.BUTTONBAR_HEIGHT
        else:
            attr_global_dict['buttonbar'] = 0
            attr_global_dict['buttonbar_height'] = 0
    return eval(attr_value, attr_global_dict)


def attr_int(node, attr, default, scale=0.0):
    """
    return the attribute as integer
    """
    try:
        if node.attrs.has_key(('', attr)):
            val = node.attrs[('', attr)]
            if val == 'line_height':
                return -1

            try:
                value = eval(val)
                return int(round(scale * value))
            except:
                return ('int(%s)' % str(val), scale)

    except ValueError:
        pass
    return default


def attr_float(node, attr, default):
    """
    return the attribute as integer
    """
    try:
        if node.attrs.has_key(('', attr)):
            return float(node.attrs[('', attr)])

    except ValueError:
        pass
    return default


def attr_col(node, attr, default):
    """
    return the attribute in hex as integer or str for color name
    """
    try:
        if node.attrs.has_key(('', attr)):
            if node.attrs[('', attr)][:2] == '0x':
                return long(node.attrs[('', attr)], 16)
            else:
                return node.attrs[('', attr)].encode(config.LOCALE)
    except ValueError:
        pass
    return default


def attr_visible(node, attr, default):
    """
    return True or False based in the attribute values 'yes' or 'no'
    """
    if node.attrs.has_key(('', attr)):
        if node.attrs[('', attr)] == 'no':
            return ''
        return node.attrs[('', attr)].encode(config.LOCALE)
    return default


def attr_str(node, attr, default):
    """
    return the attribute as string
    """
    if node.attrs.has_key(('', attr)):
        return node.attrs[('', attr)].encode(config.LOCALE)
    return default


def attr_font(node, attr, default):
    """
    return the attribute as font (with full path)
    """
    if node.attrs.has_key(('', attr)):
        fontext = os.path.splitext(node.attrs[('', attr)])[1]
        if fontext:
            # There is an extension (e.g. '.pfb'), use the full name
            font = os.path.join(config.FONT_DIR,
                                node.attrs[('', attr)]).encode(config.LOCALE)
        else:
            # '.ttf' is the default extension

            fontpath = config.OSD_EXTRA_FONT_PATH
            fontpath.append(config.FONT_DIR)

            for path in fontpath:
                font = os.path.join(path, node.attrs[('', attr)] +
                                    '.ttf').encode(config.LOCALE)
                if font: break
                font = os.path.join(path, node.attrs[('', attr)] +
                                        '.TTF').encode(config.LOCALE)
                if font: break

        if not font:
            logger.warning('can\'t find font "%s"', font)
            font = config.OSD_DEFAULT_FONTNAME
        return font
    return default


def search_file(file, search_dirs):
    for s_dir in search_dirs:
        dfile=os.path.join(s_dir, file)

        if vfs.isfile(dfile):
            return vfs.abspath(dfile)

        if vfs.isfile('%s.png' % dfile):
            return vfs.abspath('%s.png' % dfile)

        if vfs.isfile('%s.jpg' % dfile):
            return vfs.abspath('%s.jpg' % dfile)

    logger.warning('can\'t find image "%s"', file)
    if config.DEBUG:
        print 'image search path is:'
        for s in search_dirs:
            print s
    print
    return ''



# ======================================================================

#
# data structures
#


# ======================================================================

class MainMenuItem:
    def __init__(self):
        self.label   = ''
        self.name    = ''
        self.icon    = ''
        self.image   = ''
        self.outicon = ''

    def parse(self, node, scale, c_dir=''):
        self.label    = attr_str(node, 'label', self.label)
        self.name     = attr_str(node, 'name',  self.name)
        self.icon     = attr_str(node, 'icon',  self.icon)
        self.image    = attr_str(node, 'image', self.image)
        self.outicon  = attr_str(node, 'outicon',  self.outicon)

    def prepare(self, search_dirs, image_names):
        if self.image:
            self.image = search_file(self.image, search_dirs)


# ======================================================================

class MainMenu:
    def __init__(self):
        self.items    = {}
        self.imagedir = ''

    def parse(self, menu_node, scale, c_dir=''):
        self.imagedir = attr_str(menu_node, 'imagedir', self.imagedir)
        for node in menu_node.children:
            if node.name == u'item':
                item = MainMenuItem()
                item.parse(node, scale, c_dir)
                self.items[item.label] = item

    def prepare(self, search_dirs, image_names):
        self.imagedir = os.path.join(config.IMAGE_DIR, self.imagedir)
        for i in self.items:
            self.items[i].prepare(search_dirs, image_names)

# ======================================================================
# ======================================================================

XML_types = {
    'x'        : ('int',  1),
    'y'        : ('int',  2),
    'width'    : ('int',  1),
    'height'   : ('int',  2),
    'spacing'  : ('int',  3),
    'hours_per_page': ('int',  3),
    'color'    : ('col',  0),
    'bgcolor'  : ('col',  0),
    'size'     : ('int',  3),
    'radius'   : ('int',  3),
    'label'    : ('str',  0),
    'font'     : ('str',  0),
    'layout'   : ('str',  0),
    'type'     : ('str',  0),
    'align'    : ('str',  0),
    'valign'   : ('str',  0),
    'filename' : ('str', 0),
    'image'    : ('str', 0),
    'name'     : ('font',  0),
    'visible'  : ('visible', 0),
    'border'   : ('visible', 0),
    'icon'     : ('str', 0),
    'ellipses' : ('str', 0),
    'dim'      : ('visible', 0),
}

class XML_data:
    """
    a basic data element for parsing the attributes
    """

    def __init__(self, content):
        """
        create all object variables for this type
        """
        self.content = content
        self.ints_to_prepare = []

        for c in content:
            if XML_types[c][0] in ('str', 'file', 'font'):
                setattr(self, c, '')
            elif XML_types[c][0] in ('visible',):
                setattr(self, c, 'yes')
            else:
                setattr(self, c, 0)


    def parse(self, node, scale, current_dir):
        """
        parse the node
        """
        for attr in node.attrs:
            c = attr[1].encode(config.LOCALE)

            if c in self.content:
                this_scale = 0
                if XML_types[c][1] == 1: this_scale = scale[0]
                if XML_types[c][1] == 2: this_scale = scale[1]
                if XML_types[c][1] == 3: this_scale = min(scale[0], scale[1])

                if this_scale:
                    value = eval('attr_int(node, "%s", self.%s, %s)' % (c, c, this_scale))
                    if isinstance(value, types.TupleType):
                        self.ints_to_prepare.append(c)
                else:
                    value = eval('attr_%s(node, "%s", self.%s)' % (XML_types[c][0], c, c))
                setattr(self, c, value)


    def prepare(self):
        """
        basic prepare function
        """
        try:
            for c in self.ints_to_prepare:
                try:
                    value,scale = getattr(self, c)
                    result = int(round(scale * eval_attr(value)))
                    setattr(self, c,  result)
                except:
                    pass

            if self.visible not in ('', 'yes'):
                if len(self.visible) > 4 and self.visible[:4] == 'not ':
                    p = plugin.getbyname(self.visible[4:])
                else:
                    p = plugin.getbyname(self.visible)
                if hasattr(p, 'visible'):
                    p = p.visible
                if len(self.visible) > 4 and self.visible[:4] == 'not ':
                    self.visible = not p
                else:
                    self.visible = p
        except (TypeError, AttributeError):
            pass



# ======================================================================


class Menu:
    """
    the menu style definitions
    """
    def __init__(self):
        self.style = []
        pass

    def parse(self, node, scale, current_dir):
        for subnode in node.children:
            if subnode.name == 'style':
                self.style += [ [ attr_str(subnode, 'image', ''),
                                  attr_str(subnode, 'text', '') ] ]

    def prepare(self, menuset, layout):
        for s in self.style:
            for i in range(2):
                if s[i]:
                    s[i] = copy.deepcopy(menuset[s[i]])
                    s[i].prepare(layout)
                else:
                    s[i] = None



class MenuSet:
    """
    the complete menu with the areas screen, title, subtitle, view, listing and info in it
    """
    def __init__(self):
        self.content = ('screen', 'title', 'subtitle', 'view', 'listing', 'info')
        for c in self.content:
            setattr(self, c, Area(c))


    def parse(self, node, scale, current_dir):
        for subnode in node.children:
            for c in self.content:
                if subnode.name == c:
                    getattr(self, c).parse(subnode, scale, current_dir)


    def prepare(self, layout):
        for c in self.content:
            getattr(self, c).prepare(layout)


class Area(XML_data):
    """
    area class (inside menu)
    """
    def __init__(self, name):
        XML_data.__init__(self, ('visible', 'layout', 'x', 'y', 'width', 'height'))
        self.name = name
        if name in ('listing', 'scrollabletext'):
            self.images = {}
        self.x = -1
        self.y = -1
        self.visible = False

    def parse(self, node, scale, current_dir):
        if self.x == -1:
            self.visible = True

        x = self.x
        y = self.y
        XML_data.parse(self, node, scale, current_dir)
        if x != self.x:
            try:
                self.x += config.OSD_OVERSCAN_LEFT
            except TypeError:
                pass
        if y != self.y:
            try:
                self.y += config.OSD_OVERSCAN_TOP
            except TypeError:
                pass
        for subnode in node.children:
            if subnode.name == u'image' and self.name in ('listing', 'scrollabletext'):
                label = attr_str(subnode, 'label', '')
                if label:
                    if not label in self.images:
                        self.images[label] = Image()
                    x,y = self.images[label].x, self.images[label].y
                    self.images[label].parse(subnode, scale, current_dir)
                    if x != self.images[label].x:
                        try:
                            self.images[label].x += config.OSD_OVERSCAN_LEFT
                        except TypeError:
                            pass
                    if y != self.images[label].y:
                        try:
                            self.images[label].y += config.OSD_OVERSCAN_TOP
                        except TypeError:
                            pass

    def prepare(self, layout):
        XML_data.prepare(self)
        if self.visible:
            self.layout = layout[self.layout]
        else:
            self.layout = None

    def rect(self, type):
        if type == 'screen':
            return (self.x - config.OSD_OVERSCAN_LEFT, self.y - config.OSD_OVERSCAN_TOP,
                    self.width + (config.OSD_OVERSCAN_LEFT+config.OSD_OVERSCAN_RIGHT),
                    self.height + (config.OSD_OVERSCAN_TOP+config.OSD_OVERSCAN_BOTTOM))
        return (self.x, self.y, self.width, self.height)

    def pos(self, type):
        if type == 'screen':
            return (self.x - config.OSD_OVERSCAN_LEFT, self.y - config.OSD_OVERSCAN_TOP)
        return (self.x, self.y)


# ======================================================================

class Layout:
    """
    layout tag
    """
    def __init__(self, label):
        self.label = label
        self.background = ()
        self.content = Content()

    def parse(self, node, scale, current_dir):
        for subnode in node.children:
            if subnode.name == u'background':
                self.background = []
                for bg in subnode.children:
                    if bg.name == 'image':
                        b = Image()
                    elif bg.name == 'rectangle':
                        b = Rectangle()
                    else:
                        continue
                    b.parse(bg, scale, current_dir)
                    self.background += [ b ]

            if subnode.name == u'content':
                self.content.parse(subnode, scale, current_dir)

    def prepare(self, font, color, search_dirs, image_names):
        self.content.prepare(font, color, search_dirs)
        for b in self.background:
            b.prepare(color, search_dirs, image_names)



class Content(XML_data):
    """
    content inside a layout
    """
    def __init__(self):
        XML_data.__init__(self, ('type', 'spacing', 'x', 'y', 'width',
                                 'height', 'font', 'align', 'valign', 'color',
                                 'hours_per_page'))
        self.types = {}
        self.cdata = ''
        self.hours_per_page = 2

    def parse(self, node, scale, current_dir):
        XML_data.parse(self, node, scale, current_dir)
        self.cdata = node.textof()
        for subnode in node.children:
            if subnode.name == u'item':
                type = attr_str(subnode, 'type', '')
                if type and not self.types.has_key(type):
                    self.types[type] = XML_data(('font', 'align', 'valign', 'height',
                                                 'width', 'icon'))
                    self.types[type].rectangle = None
                    self.types[type].shadow    = None
                    self.types[type].cdata     = ''
                if type:
                    self.types[type].parse(subnode, scale, current_dir)
                    self.types[type].cdata = subnode.textof()
                    delete_fcontent = True
                    for rnode in subnode.children:
                        if rnode.name == u'rectangle':
                            self.types[type].rectangle = Rectangle()
                            self.types[type].rectangle.parse(rnode, scale, current_dir)
                        if rnode.name == u'shadow':
                            self.types[type].shadow = XML_data(('visible', 'color', 'x', 'y'))
                            self.types[type].shadow.parse(rnode, scale, current_dir)

                        elif rnode.name in (u'if', u'text', u'newline',
                                             u'goto_pos', u'img'):
                            if (not hasattr(self.types[ type ], 'fcontent')) or \
                                   delete_fcontent:
                                self.types[ type ].fcontent = [ ]
                            delete_fcontent = False
                            child = None
                            if rnode.name == u'if':
                                child = FormatIf()
                            elif rnode.name == u'text':
                                child = FormatText()
                            elif rnode.name == u'newline':
                                child = FormatNewline()
                            elif rnode.name == u'goto_pos':
                                child = FormatGotopos()
                            elif rnode.name == u'img':
                                child = FormatImg()

                            child.align = self.types[type].align
                            child.valign = self.types[type].valign

                            self.types[ type ].fcontent += [ child ]
                            self.types[ type ].fcontent[-1].parse(rnode, scale, current_dir)

        if not self.types.has_key('default'):
            self.types['default'] = XML_data(('font',))
            self.types['default'].rectangle = None
            self.types['default'].shadow    = None
            self.types['default'].cdata     = ''


    def prepare(self, font, color, search_dirs):
        XML_data.prepare(self)
        if self.font:
            if font.has_key(self.font):
                self.font = font[self.font]
            else:
                logger.warning('can\'t find font "%s"', self.font)
                self.font = font['default']
        else:
            self.font = font['default']

        if color.has_key(self.color):
            self.color = color[self.color]

        for type in self.types:
            if self.types[type].font:
                self.types[type].font = font[self.types[type].font]
            else:
                self.types[type].font = None
            if self.types[type].rectangle:
                self.types[type].rectangle.prepare(color)

            if hasattr(self.types[type], 'fcontent'):
                for i in self.types[type].fcontent:
                    i.prepare(font, color, search_dirs)



# ======================================================================
# Formating
class FormatText(XML_data):
    def __init__(self):
        XML_data.__init__(self, ('align', 'valign', 'font', 'width', 'height',
                                   'ellipses', 'dim'))
        self.mode     = 'hard'
        self.align    = 'left'
        self.ellipses = '...'
        self.dim      = True
        self.height   = -1
        self.text     = ''
        self.expression = None
        self.expression_analized = 0
        self.x = 0
        self.y = 0

    def __str__(self):
        str = "FormatText(Text: '%s', Expression: '%s', "+\
              "Expression Analized: %s, Mode: %s, Font: %s, Width: %s, "+\
              "Height: %s, x: %s, y: %s) "
        str = str % (self.text, self.expression, self.expression_analized,
                      self.mode, self.font, self.width, self.height, self.x, self.y)
        return str


    def parse(self, node, scale, c_dir=''):
        XML_data.parse(self, node, scale, c_dir)
        self.text = node.textof()
        self.mode = attr_str(node, 'mode', self.mode)
        if self.mode != 'hard' and self.mode != 'soft':
            self.mode = 'hard'
        self.expression = attr_str(node, 'expression', self.expression)
        if self.expression: self.expression = self.expression.strip()


    def prepare(self, font, color, search_dirs):
        if self.font:
            if font.has_key(self.font):
                self.font = font[self.font]
            else:
                logger.warning('can\'t find font "%s"', self.font)
                self.font = font['default']
        else:
            self.font = font['default']




class FormatGotopos(XML_data):
    def __init__(self):
        XML_data.__init__(self, ('x', 'y'))
        self.mode = 'relative'
        self.x = None
        self.y = None

    def parse(self, node, scale, c_dir=''):
        XML_data.parse(self, node, scale, c_dir)
        self.mode = attr_str(node, 'mode', self.mode)
        if self.mode != 'relative' and self.mode != 'absolute':
            self.mode = 'relative'

    def prepare(self, font, color, search_dirs):
        pass


class FormatNewline:
    def __init__(self):
        pass

    def parse(self, node, scale, c_dir=''):
        pass

    def prepare(self, font, color, search_dirs):
        pass


class FormatImg(XML_data):
    def __init__(self):
        XML_data.__init__(self, ('x', 'y', 'width', 'height'))
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.src = ''
        self.srcexpr = None
        self.search_dirs = None

    def parse(self, node, scale, c_dir=''):
        XML_data.parse(self, node, scale, c_dir)
        self.src = attr_str(node, 'src', self.src)
        self.srcexpr = attr_str(node, 'srcexpr', self.srcexpr)

    def prepare(self, font, color, search_dirs):
        if len(self.src):
            self.src = search_file(self.src, search_dirs)
        else:
            self.search_dirs = search_dirs


class FormatIf:
    def __init__(self):
        self.expression = ''
        self.content = [ ]
        self.expression_analized = 0

    def parse(self, node, scale, c_dir=''):
        self.expression = attr_str(node, 'expression', self.expression)
        for subnode in node.children:
            if subnode.name == u'if':
                child = FormatIf()
            elif subnode.name == u'text':
                child = FormatText()
            elif subnode.name == u'newline':
                child = FormatNewline()
            elif subnode.name == u'goto_pos':
                child = FormatGotopos()
            elif subnode.name == u'img':
                child = FormatImg()

            child.parse(subnode, scale, c_dir)
            self.content += [ child ]

    def prepare(self, font, color, search_dirs):
        for i in self.content:
            i.prepare(font, color, search_dirs)






# ======================================================================

class Image(XML_data):
    """
    an image
    """
    def __init__(self):
        XML_data.__init__(self, ('x', 'y', 'width', 'height', 'image', 'filename',
                                 'label', 'visible'))

    def prepare(self, color, search_dirs, image_names):
        """
        try to guess the image localtion
        """
        XML_data.prepare(self)
        if self.image:
            if image_names.has_key(self.image):
                self.filename = image_names[self.image]
            else:
                logger.warning('can\'t find image definition "%s"', self.image)

        if self.filename:
            self.filename = search_file(self.filename, search_dirs)



class Rectangle(XML_data):
    """
    a Rectangle
    """
    def __init__(self, color=None, bgcolor=None, size=None, radius=None):
        XML_data.__init__(self, ('x', 'y', 'width', 'height', 'color', 'bgcolor', 'size', 'radius'))
        if not color == None:
            self.color = color
        if not bgcolor == None:
            self.bgcolor = bgcolor
        if not size == None:
            self.size = size
        if not radius == None:
            self.radius = radius

    def prepare(self, color, search_dirs=None, image_names=None):
        XML_data.prepare(self)
        if color.has_key(self.color):
            self.color = color[self.color]
        if color.has_key(self.bgcolor):
            self.bgcolor = color[self.bgcolor]



class Font(XML_data):
    """
    font tag
    """
    def __init__(self, label):
        XML_data.__init__(self, ('name', 'size', 'color', 'bgcolor'))
        self.label  = label
        self.shadow = XML_data(('visible', 'color', 'x', 'y', 'border'))
        self.shadow.visible = False
        self.shadow.border  = False

    def __repr__(self):
        s = '<%s %s>' % (self.__class__, self.label)
        return s

    def parse(self, node, scale, current_dir):
        XML_data.parse(self, node, scale, current_dir)
        for subnode in node.children:
            if subnode.name == u'shadow':
                self.shadow.parse(subnode, scale, current_dir)

    def stringsize(self, text):
        size = self.font.stringsize(text)
        if self.shadow.visible:
            if self.shadow.border:
                return size + (self.size / 10) * 2
            else:
                return size + abs(self.shadow.x)
        return size

    def prepare(self, color, search_dirs=None, image_names=None, scale=1.0):
        if color.has_key(self.color):
            self.color = color[self.color]
        self.size   = int(float(self.size) * scale)
        self.font   = osd.getfont(self.name, self.size)
        self.h      = self.font.height
        if self.shadow.visible:
            if color.has_key(self.shadow.color):
                self.shadow.color = color[self.shadow.color]
            if self.shadow.border:
                self.h += (self.size / 10) * 2
            else:
                self.h += abs(self.shadow.y)
        self.height = self.h



# ======================================================================


class AreaSet:
    """
    A tag with different area pointer in it, e.g. used for <player>
    """
    def __init__(self):
        self.areas = {}

    def parse(self, node, scale, current_dir):
        for subnode in node.children:
            if not self.areas.has_key(subnode.name):
                self.areas[subnode.name] = Area(subnode.name)
                self.areas[subnode.name].visible = True
            self.areas[subnode.name].parse(subnode, scale, current_dir)

    def prepare(self, layout):
        for c in self.areas:
            self.areas[c].prepare(layout)


# ======================================================================


class XMLSkin:
    """
    skin main settings class
    """
    def __init__(self):

        self._layout   = {}
        self._font     = {}
        self._color    = {}
        self._images   = {}
        self._menuset  = {}
        self._menu     = {}
        self._popup    = ''
        self._sets     = {}
        self._mainmenu = MainMenu()
        self.skindirs  = []
        self.icon_dir  = ""
        self.files     = []
        self.fxd_files = []

        # variables set by set_var
        self.all_variables    = ('box_under_icon', 'anamorphic',)
        self.box_under_icon   = 0
        self.anamorphic       = 0


    def __getattribute__(self, name):
        global attr_global_dict
        print '__getattribute__(name=%r)' % name
        pass


    def parse(self, freevo_type, scale, c_dir):
        for node in freevo_type.children:
            if node.name == u'main':
                self._mainmenu.parse(node, scale, c_dir)

            elif node.name == u'menu':
                type = attr_str(node, 'type', 'default')

                if type == 'all':
                    # if type is all, all types except default are deleted and
                    # the settings will be loaded for default
                    self._menu = {}
                    type       = 'default'

                self._menu[type] = Menu()
                self._menu[type].parse(node, scale, c_dir)


            elif node.name == u'menuset':
                label   = attr_str(node, 'label', '')
                inherit = attr_str(node, 'inherits', '')
                if inherit:
                    self._menuset[label] = copy.deepcopy(self._menuset[inherit])
                elif not self._menuset.has_key(label):
                    self._menuset[label] = MenuSet()
                self._menuset[label].parse(node, scale, c_dir)

            elif node.name == u'layout':
                label = attr_str(node, 'label', '')
                if label:
                    if not self._layout.has_key(label):
                        self._layout[label] = Layout(label)
                    self._layout[label].parse(node, scale, c_dir)

            elif node.name == u'file':
                file = None
                src = attr_str(node, 'src', '')
                if src and src not in self.files:
                    self.files.append(src)

            elif node.name == u'font':
                label = attr_str(node, 'label', '')
                if label:
                    if not self._font.has_key(label):
                        self._font[label] = Font(label)
                    self._font[label].parse(node, scale, c_dir)

            elif node.name == u'color':
                label = attr_str(node, 'label', '')
                if label:
                    value = attr_col(node, 'value', '')
                    self._color[label] = value

            elif node.name == u'image':
                label = attr_str(node, 'label', '')
                if label:
                    value = attr_col(node, 'filename', '')
                    self._images[label] = value

            elif node.name == u'iconset':
                self.icon_dir = attr_str(node, 'theme', self.icon_dir)

            elif node.name == u'popup':
                self._popup = attr_str(node, 'layout', self._popup)

            elif node.name == u'setvar':
                for v in self.all_variables:
                    if node.attrs[('', 'name')].upper() == v.upper():
                        try:
                            setattr(self, v, int(node.attrs[('', 'val')]))
                        except ValueError:
                            setattr(self, v, node.attrs[('', 'val')])

            else:
                if node.children and node.children[0].name == 'style':
                    self._sets[node.name] = Menu()
                elif not self._sets.has_key(node.name):
                    self._sets[node.name] = AreaSet()
                self._sets[node.name].parse(node, scale, c_dir)


    def prepare(self):
        global attr_global_dict
        attr_global_dict = None
        self.prepared = True
        self.sets     = copy.deepcopy(self._sets)

        self.font     = copy.deepcopy(self._font)
        layout        = copy.deepcopy(self._layout)

        """
        .
        share/icons/themes/<skin>
        share/images
        share/skins/main
        share/skins/plugins
        """
        if not os.path.isdir(self.icon_dir):
            self.icon_dir = os.path.join(config.ICON_DIR, 'themes', self.icon_dir)
        search_dirs = [ '.', self.icon_dir, config.IMAGE_DIR, ] + self.skindirs

        for f in self.font:
            self.font[f].prepare(self._color, scale=self.font_scale)

        for l in layout:
            layout[l].prepare(self.font, self._color, search_dirs, self._images)

        all_menus = copy.deepcopy(self._menu)
        for menu in all_menus:
            all_menus[menu].prepare(self._menuset, layout)

            # prepare listing area images
            for s in all_menus[menu].style:
                for i in range(2):
                    if s[i] and hasattr(s[i], 'listing'):
                        for image in s[i].listing.images:
                            s[i].listing.images[image].prepare(None, search_dirs,
                                                               self._images)


        self.default_menu = {}
        self.special_menu = {}
        for k in all_menus:
            if k.startswith('default'):
                self.default_menu[k] = all_menus[k]
            else:
                self.special_menu[k] = all_menus[k]

        types = []
        for k in self.special_menu:
            if k.find('main menu') == -1:
                types.append(k)

        for t in types:
            if not self.special_menu.has_key(t + ' main menu'):
                self.special_menu[t + ' main menu'] = self.special_menu[t]

        for t in ('default no image', 'default description'):
            if not self.default_menu.has_key(t):
                self.default_menu[t] = self.default_menu['default']

        t = 'default description'
        if not self.default_menu.has_key(t + ' no image'):
            self.default_menu[t + ' no image'] = self.default_menu[t]

        for s in self.sets:
            if isinstance(self.sets[s], AreaSet):
                # prepare an areaset
                self.sets[s].prepare(layout)
                for area in self.sets[s].areas.values():
                    if hasattr(area, 'images'):
                        for image in area.images.values():
                            image.prepare(None, search_dirs, self._images)

            else:
                # prepare a menu
                self.sets[s].prepare(self._menuset, layout)
                for s in self.sets[s].style:
                    for i in range(2):
                        if s[i] and hasattr(s[i], 'listing'):
                            for image in s[i].listing.images:
                                s[i].listing.images[image].prepare(None, search_dirs,
                                                                   self._images)

        self.popup = layout[self._popup]

        self.mainmenu = copy.deepcopy(self._mainmenu)
        self.mainmenu.prepare(search_dirs, self._images)

        self.images = {}
        for name in self._images:
            self.images[name] = search_file(self._images[name], search_dirs)
        return 1


    def fxd_callback(self, fxd, node):
        """
        callback for the 'skin' tag
        """
        # get args back
        (clear, file, prepare) = fxd.getattr(None, 'args')

        font_scale    = attr_float(node, 'fontscale', 1.0)
        file_geometry = attr_str(node, 'geometry', '')

        if file_geometry:
            w, h = file_geometry.split('x')
        else:
            w = config.CONF.width
            h = config.CONF.height

        scale = (float(config.CONF.width-(config.OSD_OVERSCAN_LEFT+config.OSD_OVERSCAN_RIGHT))/float(w),
                 float(config.CONF.height-(config.OSD_OVERSCAN_TOP+config.OSD_OVERSCAN_BOTTOM))/float(h))

        include  = attr_str(node, 'include', '')

        if include:
            self.load(include, prepare=False)

        self.parse(node, scale, os.path.dirname(file))
        if not os.path.dirname(file) in self.skindirs:
            self.skindirs = [ os.path.dirname(file) ] + self.skindirs
        if not prepare:
            return

        self.font_scale = font_scale
        self.prepare()
        self.prepared = False
        return


    def include_callback(self, fxd, node):
        """
        callback for the 'include' tag
        <include>
            <file src="skin1.fxd/>
            <file src="skin2.fxd/>
            ...
        </include>

        """
        # get args back
        (clear, file, prepare) = fxd.getattr(None, 'args')

        font_scale    = attr_float(node, 'fontscale', 1.0)
        file_geometry = attr_str(node, 'geometry', '')

        if file_geometry:
            w, h = file_geometry.split('x')
        else:
            w = config.CONF.width
            h = config.CONF.height

        scale = (float(config.CONF.width-(config.OSD_OVERSCAN_LEFT+config.OSD_OVERSCAN_RIGHT))/float(w),
                 float(config.CONF.height-(config.OSD_OVERSCAN_TOP+config.OSD_OVERSCAN_BOTTOM))/float(h))

        scale = (float(config.CONF.width-(config.OSD_OVERSCAN_LEFT+config.OSD_OVERSCAN_RIGHT))/float(w),
                 float(config.CONF.height-(config.OSD_OVERSCAN_TOP+config.OSD_OVERSCAN_BOTTOM))/float(h))

        self.parse(node, scale, os.path.dirname(file))

        for f in self.files:
            logger.debug('loading \"%s\" fxd file now', f)
            self.load(f, prepare=False)
            self.parse(node, scale, os.path.dirname(file))
        
            if not os.path.dirname(file) in self.skindirs:
                self.skindirs = [ os.path.dirname(file) ] + self.skindirs

        return


    def load(self, file, prepare=True, clear=False):
        """
        load and parse the skin file
        """
        if file in self.fxd_files:
            return

        if clear:
            self._layout   = {}
            self._font     = {}
            self._color    = {}
            self._images   = {}
            self._menuset  = {}
            self._menu     = {}
            self._popup    = ''
            self._sets     = {}
            self._mainmenu = MainMenu()
            self.skindirs  = []
            self.fxd_files = []

            # load plugin skin files:
            pdir = os.path.join(config.SHARE_DIR, 'skins/plugins')
            if os.path.isdir(pdir):
                for p in util.match_files(pdir, [ 'fxd' ]):
                    self.load(p, prepare=False)

        self.prepared = False

        if not vfs.isfile(file):
            if vfs.isfile(file+'.fxd'):
                file += '.fxd'

            elif vfs.isfile(vfs.join(config.SKIN_DIR, '%s/%s.fxd' % (file, file))):
                file = vfs.join(config.SKIN_DIR, '%s/%s.fxd' % (file, file))

            else:
                file = vfs.join(config.SKIN_DIR, 'xbmc/%s' % file)
                if vfs.isfile(file+'.fxd'):
                    file += '.fxd'

        if not vfs.isfile(file):
            return 0

        try:
            parser = util.fxdparser.FXD(file)
            parser.setattr(None, 'args', (clear, file, prepare))
            parser.set_handler('include', self.include_callback)
            parser.set_handler('skin', self.fxd_callback)
            parser.parse()
            self.fxd_files.append(file)
            return 1

        except:
            logger.error('XML file "%s" corrupt', file)
            traceback.print_exc()
            return 0
