# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# Directory handling
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

"""
Directory handling
"""
import logging
logger = logging.getLogger("freevo.directory")

import os
import traceback
import re
import stat
import copy
import rc
from pprint import pformat

import kaa.metadata

import config
import util
import util.mediainfo as mediainfo

import menu
import skin
import plugin
import osd
import fxditem

from item import Item, FileInformation
from playlist import Playlist
from event import *
import dialog
import dialog.dialogs

from gui import InputBox


all_variables = [
    ('DIRECTORY_SORT_BY_DATE', _('Directory Sort By Date'),
        _('Sort directory by date and not by name.'), False),

    ('DIRECTORY_AUTOPLAY_SINGLE_ITEM', _('Directory Autoplay Single Item'),
        _('Don\'t show directory if only one item exists and auto-select the item.'), False),

    ('DIRECTORY_FORCE_SKIN_LAYOUT', _('Force Skin Layout'),
        _('Force skin to a specific layout. This option doesn\'t work with ' \
        'all skins and the result may differ based on the skin.'), False),

    ('DIRECTORY_SMART_SORT', _('Directory Smart Sort'),
        _('Use a smarter way to sort the items.'), False),

    ('DIRECTORY_SMART_NAMES', _('Directory Smart Names'),
        _('Use a smarter way to abbreviate the name of the items.'), True),

    ('DIRECTORY_USE_MEDIAID_TAG_NAMES', _('Use MediaID Tag Names'),
        _('Use the names from the media files tags as display name.'), False),

    ('DIRECTORY_REVERSE_SORT', _('Directory Reverse Sort'),
        _('Show the items in the list in reverse order.'), False),

    ('DIRECTORY_AUDIO_FORMAT_STRING', '', '', False),

    ('DIRECTORY_CREATE_PLAYLIST', _('Directory Create Playlist'),
        _('Handle the directory as playlist. After one file is played, the next one will be started.'), True),

    ('DIRECTORY_ADD_PLAYLIST_FILES', _('Directory Add Playlist Files'),
        _('Add playlist files to the list of items'), True) ,

    ('DIRECTORY_ADD_RANDOM_PLAYLIST', _('Directory Add Random Playlist'),
        _('Add an item for a random playlist'), True) ,

    ('DIRECTORY_AUTOPLAY_ITEMS', _('Directory Autoplay Items'),
        _('Autoplay the whole directory (as playlist) when it contains only files and no directories'), True)
]


class DirItem(Playlist):
    """
    class for handling directories
    """
    def __init__(self, directory, parent, name='', display_type=None, add_args=None, create_metainfo=True):
        logger.log( 9, '%s.__init__(directory=%r, parent=%r, name=%r, display_type=%r, add_args=%r, create_metainfo=%r)', 
self.__class__, directory, parent, name, display_type, add_args, create_metainfo)

        self.autovars = [ ('num_dir_items', 0), ('show_all_items', False) ]
        Playlist.__init__(self, parent=parent, display_type=display_type)
        self.type = 'dir'
        self.menu = None

        # store FileInformation for moving/copying
        self.files = FileInformation()
        if self.media:
            self.files.read_only = True
        self.files.append(directory)

        self.dir  = os.path.abspath(directory)
        self.info = mediainfo.get_dir(directory)

        #FIXME This should be done in the cache create
        if not self.image:
            mminfo = kaa.metadata.parse(directory)
            if mminfo:
                if mminfo['image']:
                    self.image = mminfo['image']
                if mminfo['title']:
                    self.title = mminfo['title']
                if mminfo['comment']:
                    self.comment = mminfo['comment']

        if name:
            self.name = Unicode(name)
        elif self.info['title:filename']:
            self.name = self.info['title:filename']
        elif self.info['title']:
            self.name = self.info['title']
        else:
            self.name = util.getname(directory, skip_ext=False)

        if add_args == None and hasattr(parent, 'add_args'):
            add_args = parent.add_args

        self.add_args = add_args

        if self.parent and hasattr(parent, 'skin_display_type'):
            self.skin_display_type = parent.skin_display_type
        elif parent:
            self.skin_display_type = parent.display_type
        else:
            self.skin_display_type = display_type

        if self['show_all_items']:
            self.display_type = None

        # set tv to video now
        if self.display_type == 'tv':
            display_type = 'video'

        # set directory variables to default
        global all_variables
        self.all_variables = copy.copy(all_variables)

        # Check mimetype plugins if they want to add something
        for p in plugin.mimetype(display_type):
            self.all_variables += p.dirconfig(self)

        # set the variables to the default values
        for var in self.all_variables:
            if hasattr(parent, var[0]):
                setattr(self, var[0], getattr(parent, var[0]))
            elif hasattr(config, var[0]):
                setattr(self, var[0], getattr(config, var[0]))
            else:
                setattr(self, var[0], False)

        self.modified_vars = []

        # Check for a cover in current dir
        if self.info['image']:
            image = self.info['image']
        else:
            image = util.getimage(os.path.join(directory, 'cover'))
        # if we have an image then use it
        if image:
            self.image = image
            self.files.image = image

        # Check for a folder.fxd in current dir
        self.folder_fxd = os.path.join(directory, 'folder.fxd')
        if vfs.isfile(self.folder_fxd):
            self.set_fxd_file(self.folder_fxd)

#        self.skin_fxd = util.getskinfxd(self.dir)
#        logger.debug('dir %s has skin fxd %s', self.dir, self.skin_fxd)
#        if self.skin_fxd:
#            self.skin_settings = skin.load(self.skin_fxd, False)

        # Check mimetype plugins if they want to add something
        for p in plugin.mimetype(display_type):
            p.dirinfo(self)

        if self.DIRECTORY_SORT_BY_DATE == 2 and self.display_type != 'tv':
            self.DIRECTORY_SORT_BY_DATE = 0

        # create some extra info
        if create_metainfo:
            self.create_metainfo()

        self.title = self.name
        self.name  = self.format_name(self.name)


    def __str__(self):
        s = pformat(self, depth=2)
        return s


    def __repr__(self):
        if hasattr(self, 'name'):
            return '<%s: %r>' % (self.name, self.__class__)
        return '<%r>' % (self.__class__)


    def set_fxd_file(self, file):
        """
        Set self.folder_fxd and parse it
        """
        logger.log( 9, 'set_fxd_file(file=%r)', file)
        self.folder_fxd = file
        if self.folder_fxd and vfs.isfile(self.folder_fxd):
            if self.display_type == 'tv':
                display_type = 'video'
            try:
                parser = util.fxdparser.FXD(self.folder_fxd)
                parser.set_handler('folder', self.read_folder_fxd)
                parser.set_handler('skin', self.read_folder_fxd)
                parser.parse()
            except:
                logger.warning('fxd file %r corrupt, removed', self.folder_fxd)
                try:
                    os.remove(self.folder_fxd)
                except OSError, why:
                    logger.info('fxd file %r not removed', self.folder_fxd)
                traceback.print_exc()


    def read_folder_fxd(self, fxd, node):
        """
        parse the xml file for directory settings::

            <?xml version="1.0" ?>
            <freevo>
                <folder title="Incoming TV Shows" cover-img="foo.jpg">
                    <setvar name="directory_autoplay_single_item" val="0"/>
                    <info>
                        <content>Episodes for current tv shows not seen yet</content>
                    </info>
                </folder>
            </freevo>
        """
        logger.log( 9, 'read_folder_fxd(fxd=%r, node=%r)', fxd, node)
        if node.name == 'skin':
            self.skin_fxd = self.folder_fxd
            if config.SKIN_LOAD_FXD_FOR_ITEMS:
                self.skin_settings = skin.load(self.skin_fxd, False)
            return

        # read attributes
        self.name = Unicode(fxd.getattr(node, 'title', self.name))

        image = fxd.getattr(node, 'cover-img')
        if image and vfs.isfile(os.path.join(self.dir, image)):
            self.image = os.path.join(self.dir, image)
        else:
            image = fxd.childcontent(node, 'cover-img')
            if image and vfs.isfile(os.path.join(self.dir, image)):
                self.image = os.path.join(self.dir, image)

        self.display_type = fxd.getattr(node, 'display-type', None)

        # parse <info> tag
        fxd.parse_info(fxd.get_children(node, 'info', 1), self, {'description': 'content', 'content': 'content' })

        for child in fxd.get_children(node, 'setvar', 1):
            # <setvar name="directory_smart_sort" val="1"/>
            for v, n, d, type_list in self.all_variables:
                if child.attrs[('', 'name')].upper() == v.upper():
                    if type_list:
                        if int(child.attrs[('', 'val')]):
                            setattr(self, v, [self.display_type])
                        else:
                            setattr(self, v, [])
                    else:
                        try:
                            setattr(self, v, int(child.attrs[('', 'val')]))
                        except ValueError:
                            setattr(self, v, child.attrs[('', 'val')])
                    self.modified_vars.append(v)


    def __is_type_list_var__(self, var):
        """
        return if this variable to be saved is a type_list
        """
        logger.log( 9, '__is_type_list_var__(var=%r)', var)
        for v, n, d, type_list in self.all_variables:
            if v == var:
                return type_list
        return False


    def write_folder_fxd(self, fxd, node):
        """
        callback to save the modified fxd file
        """
        logger.log( 9, 'write_folder_fxd(fxd=%r, node=%r)', fxd, node)
        # remove old setvar
        for child in copy.copy(node.children):
            if child.name == 'setvar':
                node.children.remove(child)

        fxd.setattr(node, 'title', self['title'])
        
        if self.display_type:
            fxd.setattr(node, 'display-type', self.display_type)

        # add current vars as setvar
        for v in self.modified_vars:
            if self.__is_type_list_var__(v):
                if getattr(self, v):
                    val = 1
                else:
                    val = 0
            else:
                val = getattr(self, v)
            fxd.add(fxd.XMLnode('setvar', (('name', v.lower()), ('val', val))), node, 0)


    def __getitem__(self, key):
        """
        return the specific attribute
        """
        if key == 'display_type':
            display_type = None

            if hasattr(self, 'display_type') and self.display_type:
                display_type = self.display_type

            if display_type == 'tv':
                display_type = 'video'

            return display_type

        if key == 'canonical_display_type':
            display_type = 'all'

            if hasattr(self, 'display_type') and self.display_type:
                display_type = self.display_type

            return display_type

        if key == 'skin_display_type':
            display_type = 'default'

            if hasattr(self, 'skin_display_type') and self.skin_display_type:
                display_type = self.skin_display_type
            else:
                display_type = self['canonical_display_type']

            return display_type

        if key == 'type':
            if self.media and hasattr(self.media, 'label'):
                return _('Directory on disc [%s]') % self.media.label
            return _('Directory')

        if key == 'num_items':
            display_type = self.display_type or 'all'
            if self.display_type == 'tv':
                display_type = 'video'
            return self['num_%s_items' % display_type] + self['num_dir_items']

        if key == 'num_play_items':
            display_type = self.display_type
            if self.display_type == 'tv':
                display_type = 'video'
            return self['num_%s_items' % display_type]

        if key == 'num_total_items':
            display_type = self.display_type
            if self.display_type == 'tv':
                display_type = 'video'
            return self['num_%s_total_items' % display_type]

        if key in ('freespace', 'totalspace'):
            if self.media:
                return None

            space = getattr(util, key)(self.dir) / 1000000

            return util.human_size(space)

        if key == 'usage':
            f = util.freespace(self.dir)
            t = util.totalspace(self.dir)
            return _('%(freespace)s of %(totalspace)s free' % ({
                        'freespace' : util.human_size(f),
                        'totalspace': util.human_size(t)}))

        return Item.__getitem__(self, key)


    def __setitem__(self, key, value):
        """
        Set the attribute of an Directory
        @param key: name of attribute
        @param value: new value of the attribute
        """
        # force the setting of the url item through the function set_url
        if key=='title':
            self.title = value
            self.name  = self.format_name(value)
        else:
            Item.__setitem__(self, key, value)


    def eventhandler(self, event, menuw=None):
        logger.log( 9, 'eventhandler(event=%r, menuw=%r)', event, menuw)
        if event == DIRECTORY_CHANGE_DISPLAY_TYPE and menuw.menustack[-1] == self.menu:
            possible_display_types = [ ]

            for p in plugin.get('mimetype'):
                for t in p.display_type:
                    if not t in possible_display_types:
                        possible_display_types.append(t)

            try:
                pos = possible_display_types.index(self.display_type)
                type = possible_display_types[(pos+1) % len(possible_display_types)]

                menuw.delete_menu(allow_reload = False)

                newdir = DirItem(self.dir, self.parent, self.name, type, self.add_args)
                newdir.DIRECTORY_AUTOPLAY_SINGLE_ITEM = False
                newdir.cwd(menuw=menuw)

                menuw.menustack[-2].selected = newdir
                pos = menuw.menustack[-2].choices.index(self)
                menuw.menustack[-2].choices[pos] = newdir
                rc.post_event(Event(OSD_MESSAGE, arg='%s view' % type))
                return True
            except (IndexError, ValueError):
                pass

        return Playlist.eventhandler(self, event, menuw)


    def get_play_items_recursive(self, display_type):
        types = [ 'video', 'audio', 'image', 'games' ]
        items = []
        num_total_play_items = 0
        
        if display_type == 'tv':
            display_type = 'video'
            
        if display_type == 'all':
            for display_type in types:
                for p in plugin.mimetype(display_type):
                    items += p.suffix()
        else:
            for p in plugin.mimetype(display_type):
                items += p.suffix()

        if items.count('fxd'):
            items.remove('fxd')
            
        files = util.match_files_recursively(self.dir, items)
        num_total_play_items = len(files)
            
        logger.log(9, 'recursive total playable files %d for dir=%r', num_total_play_items, self.dir)
        return num_total_play_items


    def format_name(self, name):
        """ Return a formatted string for use in item.py """
        # Since we can't specify the length of the integer in the
        # format string (Python doesn't seem to recognize it) we
        # strip it out first, when we see the only thing that can be
        # a number.

        if name and hasattr(self, 'display_type') and self.display_type and config.DIRECTORY_DIR_MENU_TABLE:
            display_type = self.display_type
            if not display_type:
                display_type = 'all'
                
            type_map   = { 'video': 'Videos', 'tv': 'Episodes', 'audio': 'Tracks', 'image': 'Images', 'games': 'Games', 'all': 'Items' }
            video_info = {  'n'  : name,
                            't'  : self['title'],
                            'e'  : '%s %s' % (self.format(self['num_total_items'], 0, '%d'), type_map[display_type]),
                            'f'  : self['name'],
                         }

            if hasattr(self.parent, 'DIRECTORY_DIR_FORMAT_STRING'):
                formatstring = unicode(self.parent.DIRECTORY_DIR_FORMAT_STRING)
            else:
                formatstring = unicode(config.DIRECTORY_DIR_FORMAT_STRING)
 
            formatted_info = formatstring % video_info

            logger.log(9, 'formatted_info=%r', formatted_info)
 
            # check if the video info was not empty
            if formatted_info != (formatstring % { 'n' : '', 't' : '', 'e' : '', 'f' : '' }):
                return formatted_info.strip()

        # fallback to current video name
        if self.name:
            return self.name

        # last fallback: return filename
        return os.path.split(self.filename)[1]


    def format(self, src, alt, fmt=None):
        if src:
            return fmt % src if fmt else src
        return alt


    # ======================================================================
    # metainfo
    # ======================================================================

    def create_metainfo(self):
        """
        create some metainfo for the directory
        """
        display_type = self.display_type
        if display_type == 'tv':
            display_type = 'video'
        name = display_type or 'all'

        # check autovars
        for var, val in self.autovars:
            if var == 'num_%s_timestamp' % name:
                break
        else:
            self.autovars += [ ('num_%s_timestamp' % name, 0), ('num_%s_items' % name, 0), ('num_%s_total_items' % name, 0) ]

        try:
            timestamp = os.stat(self.dir)[stat.ST_MTIME]
        except OSError:
            return

        num_timestamp = self.info['num_%s_timestamp' % name]

        if not num_timestamp or num_timestamp < timestamp:
            logger.debug('create metainfo for %s', self.dir)
            if self.media:
                self.media.mount()

            num_dir_items  = 0
            num_play_items = 0
            files = vfs.listdir(self.dir, include_overlay=True)

            # play items and playlists
            for p in plugin.mimetype(display_type):
                num_play_items += p.count(self, files)

            # normal DirItems
            for filename in files:
                if os.path.isdir(filename):
                    num_dir_items += 1

            # store info
            self['num_dir_items'] = num_dir_items
            self['num_%s_items' % name] = num_play_items
            self['num_%s_timestamp' % name] = timestamp
            total_play_items = self.get_play_items_recursive(name)

            # some items such as archives are not walkable, hence no way to 
            # calculate total number of playable items in the directory tree.
            logger.debug('self.name=%r, display_type=%r, total_play_items=%r, num_play_items=%r, num_dir_items=%r', 
                    self.name, name, total_play_items, num_play_items, num_dir_items)
            if total_play_items < num_play_items + num_dir_items:
                total_play_items = num_play_items + num_dir_items
            self['num_%s_total_items' % name] = total_play_items

            if self.media:
                self.media.umount()


    # ======================================================================
    # actions
    # ======================================================================

    def actions(self):
        """
        return a list of actions for this item
        """
        logger.log( 9, 'actions()')
        if self.media:
            self.media.mount()

        display_type = self['display_type']

        items = [ (self.cwd, _('Browse directory')) ]

        if self['num_%s_items' % display_type]:
            items.append((self.play, _('Play all files in directory')))

        if display_type in self.DIRECTORY_AUTOPLAY_ITEMS and not self['num_dir_items']:
            items.reverse()

        if self['num_%s_items' % display_type]:
            items.append((self.play_random, _('Random play all items')))

        if self['num_dir_items']:
            items.append((self.play_random_recursive, _('Recursive random play all items')))
            items.append((self.play_recursive, _('Recursive play all items')))

        items.append((self.configure, _('Configure directory'), 'configure'))

        if hasattr(self, 'self.folder_fxd'):
            items += fxditem.mimetype.get(self, [self.folder_fxd])

        if self.media:
            self.media.umount()

        return items


    def cwd(self, arg=None, menuw=None):
        """
        browse directory
        """
        logger.log( 9, 'cwd(arg=%r, menuw=%r)', arg, menuw)
        self.check_password_and_build(arg=None, menuw=menuw)


    def play(self, arg=None, menuw=None):
        """
        play directory
        """
        logger.debug('%s.play(arg=%r, menuw=%r)', self.__module__, arg, menuw)
        if arg == 'next':
            Playlist.play(self, arg=arg, menuw=menuw)
        else:
            self.check_password_and_build(arg='play', menuw=menuw)


    def play_random(self, arg=None, menuw=None):
        """
        play in random order
        """
        logger.debug('play_random(arg=%r, menuw=%r)', arg, menuw)
        self.check_password_and_build(arg='playlist:random', menuw=menuw)


    def play_recursive(self, arg=None, menuw=None):
        """
        play recursive
        """
        logger.debug('play_recursive(arg=%r, menuw=%r)', arg, menuw)
        self.check_password_and_build(arg='playlist:recursive', menuw=menuw)


    def play_random_recursive(self, arg=None, menuw=None):
        """
        play recursive in random order
        """
        logger.debug('play_random_recursive(arg=%r, menuw=%r)', arg, menuw)
        self.check_password_and_build(arg='playlist:random_recursive', menuw=menuw)


    def check_password_and_build(self, arg=None, menuw=None):
        """
        password checker
        """
        logger.debug('check_password_and_build(arg=%r, menuw=%r)', arg, menuw)
        if not self.menuw:
            self.menuw = menuw

        if self.media:
            self.media.mount()

        if vfs.isfile(os.path.join(self.dir, '.password')):
            logger.info('password protected dir')
            try:
                pwfile = vfs.open(os.path.join(self.dir, '.password'))
                line = pwfile.readline()
                pwfile.close()
            except IOError, e:
                logger.warning('error reading password file for %s : %s', self.dir, str(e))
                dialog.show_alert(_('Error reading password file:') + str(e))
                if self.media:
                    self.media.umount()
                return

            if self.media:
                self.media.umount()

            self.arg   = (arg, line.strip())
            self.menuw = menuw
            pb = InputBox(text=_('Enter Password'), handler=self.pass_cmp_cb, type='password')
            pb.show()
        else:
            if self.media:
                self.media.umount()
            self.build(arg=arg, menuw=menuw)


    def pass_cmp_cb(self, word=None):
        """
        read the contents of self.dir/.passwd and compare to word
        callback for check_password_and_build
        """
        logger.log( 9, 'pass_cmp_cb(word=%r)', word)
        (arg,password) = self.arg
        if word == password:
            self.build(arg, self.menuw)
        else:
            dialog.show_alert(_('Password incorrect'))
            return


    def build(self, arg=None, menuw=None):
        if self.media:
            self.media.mount()
        self.__build(arg,menuw)
        if self.media:
            self.media.umount()


    def __build(self, arg=None, menuw=None):
        """
        build the items for the directory
        """
        logger.log( 9, 'build(arg=%r, menuw=%r)', arg, menuw)
        self.menuw      = menuw
        self.playlist   = []
        self.play_items = []
        self.dir_items  = []
        self.pl_items   = []

        if hasattr(self, '__dirwatcher_last_time__'):
            del self.__dirwatcher_last_time__

        if arg == 'update':
            if not self.menu.choices:
                selected_pos = -1
            else:
                # store the current selected item
                selected_id  = self.menu.selected.id()
                selected_pos = self.menu.choices.index(self.menu.selected)
            if hasattr(self.menu, 'skin_default_has_description'):
                del self.menu.skin_default_has_description
            if hasattr(self.menu, 'skin_default_no_images'):
                del self.menu.skin_default_no_images
            if hasattr(self.menu, 'skin_force_text_view'):
                del self.menu.skin_force_text_view
        elif not os.path.exists(self.dir):
            dialog.show_alert(_('Directory %r does not exist' % (self.dir)))
            return

        display_type = self.display_type
        if self.display_type == 'tv':
            display_type = 'video'

        if arg and arg.startswith('playlist:'):
            if arg.endswith(':random'):
                Playlist(playlist = [ (self.dir, 0) ], parent = self,
                    display_type=display_type, random=True).play(menuw=menuw)
            elif arg.endswith(':recursive'):
                Playlist(playlist = [ (self.dir, 1) ], parent = self,
                    display_type=display_type, random=False).play(menuw=menuw)
            elif arg.endswith(':random_recursive'):
                Playlist(playlist = [ (self.dir, 1) ], parent = self,
                    display_type=display_type, random=True).play(menuw=menuw)
            return

        osd.get_singleton().busyicon.wait(config.OSD_BUSYICON_TIMER[0])

        files       = vfs.listdir(self.dir, include_overlay=True)
        num_changes = mediainfo.check_cache(self.dir)

        pop = None
        callback = None
        if skin.active():
            if (num_changes > 10) or (num_changes and self.media):
                if self.media:
                    pop = CacheProgressDialog(_('Scanning disc, be patient...'), num_changes)
                else:
                    pop = CacheProgressDialog(_('Scanning directory, be patient...'), num_changes)
                pop.show()
                callback=pop.processed_file

        elif len(files) > config.OSD_BUSYICON_TIMER[1]:
            # many files, just show the busy icon now
            osd.get_singleton().busyicon.wait(0)

        if num_changes > 0:
            mediainfo.cache_dir(self.dir, callback=callback)

        #
        # build items
        #

        # build play_items, pl_items and dir_items
        for p in plugin.mimetype(display_type):
            for i in p.get(self, files):
                if i.type == 'playlist':
                    self.pl_items.append(i)
                elif i.type == 'dir':
                    self.dir_items.append(i)
                else:
                    self.play_items.append(i)

        # normal DirItems
        for filename in files:
            if os.path.isdir(filename):
                d = DirItem(filename, self, display_type=self.display_type)
                self.dir_items.append(d)

        # remove same beginning from all play_items
        if self.DIRECTORY_SMART_NAMES:
            substr = ''
            if len(self.play_items) > 4 and len(self.play_items[0].name) > 5:
                substr = self.play_items[0].name[:-5].lower()
                for i in self.play_items[1:]:
                    if len(i.name) > 5:
                        substr = util.find_start_string(i.name.lower(), substr)
                        if not substr or len(substr) < 10:
                            break
                    else:
                        break
                else:
                    for i in self.play_items:
                        i.name = util.remove_start_string(i.name, substr)

        #
        # sort all items
        #

        # sort directories
        if self.DIRECTORY_SMART_SORT:
            self.dir_items.sort(lambda l, o: util.smartsort(l.dir, o.dir))
        else:
            self.dir_items.sort(lambda l, o: cmp(l.dir.upper(), o.dir.upper()))

        # sort playlist
        self.pl_items.sort(lambda l, o: cmp(l.name.upper(), o.name.upper()))

        # sort normal items
        if self.DIRECTORY_SORT_BY_DATE:
            self.play_items.sort(lambda l, o: cmp(l.sort('date').upper(), o.sort('date').upper()))
        elif self['%s_advanced_sort' % display_type]:
            self.play_items.sort(lambda l, o: cmp(l.sort('advanced').upper(), o.sort('advanced').upper()))
        else:
            self.play_items.sort(lambda l, o: cmp(l.sort().upper(), o.sort().upper()))

        self['num_dir_items'] = len(self.dir_items)
        self['num_%s_items' % display_type] = len(self.play_items) + len(self.pl_items)

        if self.DIRECTORY_REVERSE_SORT:
            self.dir_items.reverse()
            self.play_items.reverse()
            self.pl_items.reverse()

        # delete pl_items if they should not be displayed
        if self.display_type and not self.display_type in self.DIRECTORY_ADD_PLAYLIST_FILES:
            self.pl_items = []

        # add all playable items to the playlist of the directory
        # to play one files after the other
        if not self.display_type or self.display_type in self.DIRECTORY_CREATE_PLAYLIST:
            self.playlist = self.play_items

        # build a list of all items
        items = self.dir_items + self.pl_items + self.play_items

        # random playlist (only active for audio)
        if self.display_type and self.display_type in self.DIRECTORY_ADD_RANDOM_PLAYLIST and len(self.play_items) > 1:
            pl = Playlist(_('Random Playlist'), self.play_items, self, random=True)
            pl.autoplay = True
            items = [ pl ] + items

        if pop:
            pop.hide()

        # stop the timer. If the icons is drawn, it will stay there
        # until the osd is redrawn, if not, we don't need it to pop
        # up the next milliseconds
        osd.get_singleton().busyicon.stop()


        #
        # action
        #

        if arg == 'update':
            # update because of dirwatcher changes
            self.menu.choices = items

            if selected_pos != -1:
                for i in items:
                    if Unicode(i.id()) == Unicode(selected_id):
                        self.menu.selected = i
                        break
                else:
                    # item is gone now, try to the selection close
                    # to the old item
                    pos = max(0, min(selected_pos-1, len(items)-1))
                    if items:
                        self.menu.selected = items[pos]
                    else:
                        self.menu.selected = None
            if self.menuw and self.menuw.menustack[-1] == self.menu:
                if self.menu.selected and selected_pos != -1:
                    self.menuw.rebuild_page()
                else:
                    self.menuw.init_page()
                self.menuw.refresh()

        elif len(items) == 1 and items[0].actions() and self.DIRECTORY_AUTOPLAY_SINGLE_ITEM:
            # autoplay
            items[0].actions()[0][0](menuw=menuw)

        elif arg == 'play' and self.play_items:
            # called by play function
            self.playlist = self.play_items
            Playlist.play(self, menuw=menuw)

        else:
            # normal menu build
            item_menu = menu.Menu(self.name, items, reload_func=self.reload,
                item_types=self['skin_display_type'], force_skin_layout=self.DIRECTORY_FORCE_SKIN_LAYOUT)

            # a special case for audio items, this allows to display righ aligned track length (for example)
            if self.display_type == 'audio' and config.DIRECTORY_AUDIO_MENU_TABLE:
                item_menu.table = config.DIRECTORY_AUDIO_MENU_TABLE
    
            # a special case for video items, this allows to display righ aligned track length (for example)
            elif self.display_type in ['video', 'tv'] and config.DIRECTORY_VIDEO_MENU_TABLE:
                item_menu.table = config.DIRECTORY_VIDEO_MENU_TABLE

            # a special case for audio items, this allows to display righ aligned track length (for example)
            elif self.display_type == 'image' and config.DIRECTORY_IMAGE_MENU_TABLE:
                item_menu.table = config.DIRECTORY_IMAGE_MENU_TABLE

            elif config.DIRECTORY_DIR_MENU_TABLE:
                item_menu.table = config.DIRECTORY_DIR_MENU_TABLE
                logger.debug('self.display_type=%r, table=%r', self.display_type, item_menu.table)

            if self.skin_fxd:
                item_menu.skin_settings = skin.load(self.skin_fxd, False)

            menuw.pushmenu(item_menu)

            dirwatcher.cwd(menuw, self, item_menu, self.dir, self.media)
            self.menu  = item_menu
            self.menuw = menuw


    def reload(self):
        """
        called when we return to this menu
        """
        dirwatcher.cwd(self.menuw, self, self.menu, self.dir, self.media)
        dirwatcher.scan()

        # we changed the menu, don't build a new one
        return None


    # ======================================================================
    # configure submenu
    # ======================================================================


    def configure_set_name(self, name):
        """
        return name for the configure menu
        """
        logger.log( 9, 'configure_set_name(name=%r)', name)
        if name in self.modified_vars:
            if name == 'DIRECTORY_FORCE_SKIN_LAYOUT':
                return 'ICON_RIGHT_%s_%s' % (str(getattr(self, name)),
                                             str(getattr(self, name)))
            elif getattr(self, name):
                return 'ICON_RIGHT_ON_' + _('on')
            else:
                return 'ICON_RIGHT_OFF_' + _('off')
        else:
            if name == 'DIRECTORY_FORCE_SKIN_LAYOUT':
                return 'ICON_RIGHT_OFF_' + _('off')
            else:
                return 'ICON_RIGHT_AUTO_' + _('auto')


    def configure_set_var(self, arg=None, menuw=None):
        """
        Update the variable in arg and change the menu. This function is used by
        'configure'
        """
        logger.debug('configure_set_var(arg=%r, menuw=%r)', arg, menuw)

        # get current value, None == no special settings
        if arg in self.modified_vars:
            if self.__is_type_list_var__(arg):
                if getattr(self, arg):
                    current = 1
                else:
                    current = 0
            else:
                current = getattr(self, arg)
        else:
            current = None

        # get the max value for toggle
        max = 1

        display_type = self.display_type
        if display_type and display_type == 'tv':
            display_type = 'video'

        # for DIRECTORY_FORCE_SKIN_LAYOUT max = number of styles in the menu
        if arg == 'DIRECTORY_FORCE_SKIN_LAYOUT':
            if display_type and skin.get_settings()._menu.has_key(display_type):
                area = skin.get_settings()._menu[display_type]
            else:
                area = skin.get_settings()._menu['default']
            max = len(area.style) - 1
            logger.debug('max=%r', max)

        # switch from no settings to 0
        if current == None:
            self.modified_vars.append(arg)
            if self.__is_type_list_var__(arg):
                setattr(self, arg, [])
            else:
                setattr(self, arg, 0)

        # inc variable
        elif current < max:
            if self.__is_type_list_var__(arg):
                setattr(self, arg, [display_type])
            else:
                setattr(self, arg, current+1)

        # back to no special settings
        elif current == max:
            if self.parent and hasattr(self.parent, arg):
                setattr(self, arg, getattr(self.parent, arg))
            if hasattr(config, arg):
                setattr(self, arg, getattr(config, arg))
            else:
                setattr(self, arg, False)
            self.modified_vars.remove(arg)

        # create new item with updated name
        item = copy.copy(menuw.menustack[-1].selected)
        item.name = item.name[:item.name.find(u'\t') + 1] + self.configure_set_name(arg)

        try:
            parser = util.fxdparser.FXD(self.folder_fxd)
            parser.set_handler('folder', self.write_folder_fxd, 'w', True)
            parser.save()
        except:
            logger.warning('fxd file %s corrupt', self.folder_fxd)
            traceback.print_exc()

        # rebuild menu
        menuw.menustack[-1].choices[menuw.menustack[-1].choices.index(menuw.menustack[-1].selected)] = item
        menuw.menustack[-1].selected = item
        menuw.refresh(reload=1)


    def configure_set_display_type(self, arg=None, menuw=None):
        """
        change display type from specific to all
        """
        logger.debug('configure_set_display_type(arg=%r, menuw=%r)', arg, menuw)

        display_types = [ 'default', 'video', 'tv', 'audio', 'image', 'games', 'all' ]
        display_type  = display_types[(display_types.index(arg) + 1) % len(display_types)]

        if display_type == 'all':
            self['show_all_items'] = True
            self.display_type      = None
        elif display_type == 'default':
            self['show_all_items'] = False
            self.display_type      = self.parent.display_type
        else:
            self['show_all_items'] = False
            self.display_type      = display_type

        name = u'\tICON_RIGHT_NOICON_' + _(display_type)

        # create new item with updated name
        item = copy.copy(menuw.menustack[-1].selected)
        item.name = item.name[:item.name.find(u'\t')]  + name
        item.arg  = display_type

        try:
            parser = util.fxdparser.FXD(self.folder_fxd)
            parser.set_handler('folder', self.write_folder_fxd, 'w', True)
            parser.save()
        except:
            logger.warning('fxd file %s corrupt', self.folder_fxd)
            traceback.print_exc()

        # rebuild menu
        menuw.menustack[-1].choices[menuw.menustack[-1].choices.index(menuw.menustack[-1].selected)] = item
        menuw.menustack[-1].selected = item
        menuw.refresh(reload=1)


    def configure(self, arg=None, menuw=None):
        """
        show the configure dialog for folder specific settings in folder.fxd
        """
        logger.log( 9, 'configure(arg=%r, menuw=%r)', arg, menuw)
        items = []
        for i, name, descr, type_list in self.all_variables:
            if name == '':
                continue
            name += '\t' + self.configure_set_name(i)
            mi = menu.MenuItem(name, self.configure_set_var, i)
            mi.description = descr
            items.append(mi)

        if self.parent and self.parent.display_type:
            name = u'\tICON_RIGHT_NOICON_' + _(self['canonical_display_type'])
            mi = menu.MenuItem(_('Show all kinds of items') + name, 
                self.configure_set_display_type, self['canonical_display_type'])
            mi.description = _('Show video, audio and image items in this directory')
            items.append(mi)

        m = menu.Menu(_('Configure'), items, fxd_file=self.skin_fxd)
        m.table         = config.DIRECTORY_DIR_MENU_TABLE
        m.back_one_menu = config.DIRECTORY_MENU_BACK_STEPS
        m.item_types    = '%s default' % self['skin_display_type']
        menuw.pushmenu(m)


    def rename_possible(self):
        return self.files and not self.files.read_only


    def rename(self, newname):
        """
        Try and rename the directory item.
        If there is a .fxd file associated, the title is renamed inside.
        If there is no .fxd file, the directory and cover img if any are renamed.
        """
        if not os.path.exists(self.folder_fxd):
            # no .fxd file
            # do not rename the cover file !
            if self.files.rename(newname, False, False, False):
                self.name=newname
                return True
            return False
        else:
            # change the title in the .fxd file
            self.fxd_rename_newname = newname
            try:
                parser = util.fxdparser.FXD(self.folder_fxd)
                parser.set_handler('folder', self.fxd_rename, mode='w')
                parser.parse()
                parser.save()
            except Exception, e:
                return False
            return True
      

    def fxd_rename(self, fxd, node):
        fxd.setattr(node, 'title', self.fxd_rename_newname)
        self.name=self.fxd_rename_newname
   
# ======================================================================

class Dirwatcher(plugin.DaemonPlugin):
    """
    Directory handling
    """
    def __init__(self):
        logger.log( 9, 'Dirwatcher.__init__()')
        plugin.DaemonPlugin.__init__(self)
        self.item          = None
        self.menuw         = None
        self.item_menu     = None
        self.dir           = None
        self.files         = None
        self.media         = None
        self.poll_interval = 1 # 1 sec

        plugin.register(self, 'Dirwatcher')


    def listoverlay(self):
        """
        Get listing of overlay dir for change checking.
        Do not count *.cache, directories and *.raw (except videofiles.raw)
        """
        logger.log( 9, 'listoverlay()')
        if not os.path.isdir(vfs.getoverlay(self.dir)):
            # dir does not exist. Strange, there should be at least an
            # kaa.metadata cache file in there
            return []
        ret = []
        for f in os.listdir(vfs.getoverlay(self.dir)):
            if f.endswith('.raw'):
                if f[f[:-4].rfind('.')+1:-4].lower() in config.VIDEO_SUFFIX:
                    ret.append(f)
            else:
                if not f.endswith('.cache')  and not os.path.isdir(os.path.join(self.dir, f)):
                    ret.append(f)
        return ret


    def cwd(self, menuw, item, item_menu, dir, media=None):
        logger.log( 9, 'cwd(menuw=%r, item=%r, item_menu=%r, dir=%r, media=%r)', menuw, item, item_menu, dir, media)
        self.menuw     = menuw
        self.item      = item
        self.item_menu = item_menu
        self.dir       = dir
        if self.media and self.media != media:
            self.media.umount()
        try:
            self.last_time = item.__dirwatcher_last_time__
            self.files     = item.__dirwatcher_last_files__
        except AttributeError:
            self.last_time = vfs.mtime(self.dir)
            self.files     = self.listoverlay()
            self.item.__dirwatcher_last_time__  = self.last_time
            self.item.__dirwatcher_last_files__ = self.files
        if media and self.media != media:
            media.mount()
        self.media = media


    def scan(self):
        if not self.dir:
            return
        try:
            if vfs.mtime(self.dir) <= self.last_time:
                return True
        except (OSError, IOError):
            # the directory is gone
            logger.debug('Dirwatcher: unable to read directory %s', self.dir)

            # send EXIT to go one menu up:
            rc.post_event(MENU_BACK_ONE_MENU)
            self.dir = None
            return

        changed = False
        if os.stat(self.dir)[stat.ST_MTIME] <= self.last_time:
            # changes are in overlay dir, just check for new/deleted files,
            logger.debug('overlay change')
            new_files = self.listoverlay()
            for f in self.files:
                if not f in new_files:
                    changed = True
                    break
            else:
                for f in new_files:
                    if not f in self.files:
                        changed = True
                        break
        else:
            changed = True

        if changed:
            logger.debug('directory has changed')
            self.item.build(menuw=self.menuw, arg='update')
        self.last_time = vfs.mtime(self.dir)
        self.item.__dirwatcher_last_time__  = self.last_time
        self.files = self.listoverlay()
        self.item.__dirwatcher_last_files__ = self.files


    def poll(self):
        if self.dir and self.menuw and self.menuw.menustack[-1] == self.item_menu and \
                isinstance(rc.focused_app(), menu.MenuWidget):
            self.scan()

class CacheProgressDialog(dialog.dialogs.ProgressDialog):
    def __init__(self, message, total):
        super(CacheProgressDialog, self).__init__(message, '0/%d' % total, 0.0)
        self.total = total
        self.count = 0

    def processed_file(self):
        self.count += 1
        self.update_progress('%d/%d' % (self.count , self.total), float(self.count) / float(self.total))

# and activate that DaemonPlugin
dirwatcher = Dirwatcher()
plugin.activate(dirwatcher)
