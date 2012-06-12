# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# This is the Freevo playlist reading module.
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
This is the Freevo play list reading module.
"""
import logging
logger = logging.getLogger("freevo.playlist")

import random
import os
import re
import copy

import config
import menu
import util
import rc
import plugin

from event import *
from item import Item


class Playlist(Item):

    def __init__(self, name='', playlist=None, parent=None, display_type=None,
                 random=False, build=False, autoplay=False, repeat=False):
        """
        Init the playlist

            1. a filename to a playlist file (e.g. m3u)
            2. a list of items to play, this list can include
                - Items
                - filenames
                - a list (directoryname, recursive=0|1)

        @param build: create the playlist, this means unfold the directories
        """
        Item.__init__(self, parent)

        self.type     = 'playlist'
        self.menuw    = None
        self.name     = Unicode(name)

        if isstring(playlist) and not name:
            self.name = util.getname(playlist)

        # variables only for Playlist
        self.current_item = None
        self.playlist     = playlist or []
        self.autoplay     = autoplay
        self.repeat       = repeat
        self.display_type = display_type

        self.__build__    = False
        self.suffixlist   = []
        self.get_plugins  = []

        self.background_playlist = None
        if build:
            self.build()

        if self.name.find('Playlist') < 0:
            self.name = '%s Playlist' % self.name

        self.random = random


    def read_m3u(self, plsname):
        """
        This is the (m3u) playlist reading function.

        @param plsname: The playlist filename
        @returns: The list of interesting lines in the playlist
        """
        try:
            lines = util.readfile(plsname)
        except IOError:
            print 'Cannot open file "%s"' % plsname
            return 0

        try:
            playlist_lines_dos = map(lambda l: l.strip(), lines)
            playlist_lines = filter(lambda l: len(l) > 0, playlist_lines_dos)
        except IndexError:
            print 'Bad m3u playlist file "%s"' % plsname
            return 0

        (curdir, playlistname) = os.path.split(plsname)
        #XXX this may not work if the curdir is not accessible
        os.chdir(curdir)
        for i in range(0,len(playlist_lines)):
            if playlist_lines[i][0] == "#":
                continue
            line = playlist_lines[i]
            line = line.replace('\\', '/') # Fix MSDOS slashes
            try:
                if line.find('://') > 0:
                    if playlist_lines[i-1].find('#EXTINF') > -1 and len(playlist_lines[i-1].split(","))>1:
                        self.playlist.append((line,playlist_lines[i-1].split(",")[1]))
                    else:
                        self.playlist.append(line)
                elif os.path.isabs(line):
                    if os.path.exists(line):
                        self.playlist.append(line)
                else:
                    if os.path.exists(os.path.abspath(os.path.join(curdir, line))):
                        self.playlist.append(os.path.abspath(os.path.join(curdir, line)))
            except TypeError:
                print 'Bad m3u playlist line in "%s":%r' % (plsname, line)


    def read_pls(self, plsname):
        """
        This is the (pls) playlist reading function.

        Arguments: plsname  - the playlist filename
        Returns:   The list of interesting lines in the playlist
        """
        try:
            lines = util.readfile(plsname)
        except IOError:
            print String(_('Cannot open file "%s"')) % list
            return 0

        playlist_lines_dos = map(lambda l: l.strip(), lines)
        playlist_lines = filter(lambda l: l[0:4] == 'File', playlist_lines_dos)

        for line in playlist_lines:
            numchars=line.find("=")+1
            if numchars > 0:
                playlist_lines[playlist_lines.index(line)] = \
                                                line[numchars:]

        (curdir, playlistname) = os.path.split(plsname)
        os.chdir(curdir)
        for line in playlist_lines:
            if line.endswith('\r\n'):
                line = line.replace('\\', '/') # Fix MSDOS slashes
            if line.find('://') > 0:
                self.playlist.append(line)
            elif os.path.isabs(line):
                if os.path.exists(line):
                    self.playlist.append(line)
            else:
                if os.path.exists(os.path.abspath(os.path.join(curdir, line))):
                    self.playlist.append(os.path.abspath(os.path.join(curdir, line)))



    def read_ssr(self, ssrname):
        """
        This is the (ssr) slideshow reading function.

        File line format::

            FileName: "image file name"; Caption: "caption text"; Delay: "sec"

        The caption and delay are optional.

        @param ssrname: the slideshow filename
        @returns: the list of interesting lines in the slideshow
        """

        (curdir, playlistname) = os.path.split(ssrname)
        os.chdir(curdir)
        out_lines = []
        try:
            lines = util.readfile(ssrname)
        except IOError:
            print String(_('Cannot open file "%s"')) % list
            return 0

        playlist_lines_dos = map(lambda l: l.strip(), lines)
        playlist_lines     = filter(lambda l: l[0] != '#', lines)


        # Here's where we parse the line.  See the format above.
        for line in playlist_lines:
            tmp_list = []
            ss_name = re.findall('FileName: \"(.*?)\"', line, re.I)
            ss_caption = re.findall('Caption: \"(.*?)\"', line, re.I)
            ss_delay = re.findall('Delay: \"(.*?)\"', line, re.I)

            if ss_name != []:
                if ss_caption == []:
                    ss_caption += [""]
                if ss_delay == []:
                    ss_delay += [5]

                for p in self.get_plugins:
                    if os.path.isabs(ss_name[0]):
                        curdir = ss_name[0]
                    else:
                        curdir = os.path.abspath(os.path.join(curdir, ss_name[0]))
                    for i in p.get(self, [curdir]):
                        if i.type == 'image':
                            i.name     = Unicode(ss_caption[0])
                            i.duration = int(ss_delay[0])
                            self.playlist.append(i)
                            break
        self.autoplay = True


    def build(self):
        """
        Build the playlist. Create a list of items and filenames. This function
        will load the playlist file or expand directories
        """
        if self.suffixlist:
            # we called this function before
            return

        playlist      = self.playlist
        self.playlist = []

        for p in plugin.mimetype(self.display_type):
            #if self.display_type in p.display_type:
            # XXX self.display_type seems to be set to None
            # XXX Which prevents the str->Item from occuring
            # XXX This is a short-term fix I guess
            self.suffixlist += p.suffix()
            self.get_plugins.append(p)

        if isstring(playlist):
            # it's a filename with a playlist
            try:
                f=open(playlist, "r")
                line = f.readline()
                f.close
                if line.find("[playlist]") > -1:
                    self.read_pls(playlist)
                elif line.find("[Slides]") > -1:
                    self.read_ssr(playlist)
                else:
                    self.read_m3u(playlist)
            except (OSError, IOError), e:
                print 'playlist error: %s' % e
            self.set_url(playlist)

        # self.playlist is a list of Items or strings (filenames)
        if not isstring(playlist):
            for i in playlist:
                if isinstance(i, Item):
                    # Item object, correct parent
                    i = copy.copy(i)
                    i.parent = self
                    self.playlist.append(i)

                elif isinstance(i, list) or isinstance(i, tuple) and len(i) == 2 and vfs.isdir(i[0]):
                    # (directory, recursive=True|False)
                    if i[1]:
                        self.playlist += util.match_files_recursively(i[0], self.suffixlist,
                            skip_password=True, follow_symlinks=config.SYS_FOLLOW_SYMLINKS)
                    else:
                        self.playlist += util.match_files(i[0], self.suffixlist)
                    # set autoplay to True on such big lists
                    self.autoplay = True

                else:
                    # filename
                    self.playlist.append(i)

        self.__build__ = True


    def randomize(self):
        """
        resort the playlist by random
        """
        logger.debug('randomize playlist')
        old = self.playlist
        self.playlist = []
        while old:
            element = random.choice(old)
            old.remove(element)
            self.playlist += [ element ]


    def actions(self):
        """
        return the actions for this item: play and browse
        """
        self.build()
        items = [ ( self.browse, _('Browse Playlist') ) ]

        play_item = ( self.play, _('Play') )

        if self.autoplay:
            items = [ play_item ] + items
        else:
            items.append(play_item)

        if not self.random:
            items.append((self.random_play, _('Random play all items')))

        return items


    def browse(self, arg=None, menuw=None):
        """
        show the playlist in the menu
        """
        self.build()
        items = []
        for item in self.playlist:
            if not callable(item):
                # get a real item
                for p in self.get_plugins:
                    if isinstance(item,(tuple)):
                        mi = p.get(self, [ item[0] ])
                        if len(mi) > 0:
                            mi[0].name=item[1]
                            mi[0].description=item[1]
                        items += mi
                    else:
                        items += p.get(self, [ item ])
            else:
                items.append(item)

        self.playlist = items

        if self.random:
            self.randomize()

        moviemenu = menu.Menu(self.name, self.playlist)
        menuw.pushmenu(moviemenu)


    def random_play(self, arg=None, menuw=None):
        """
        play the playlist in random order
        """
        Playlist(playlist=self.playlist, parent=self.parent,
                 display_type=self.display_type, random=True,
                 repeat=self.repeat).play(arg, menuw)


    def play(self, arg=None, menuw=None):
        """
        play the playlist
        """
        logger.debug('%s.play(arg=%r, menuw=%r)', self.__class__, arg, menuw)
        if not self.menuw:
            self.menuw = menuw

        if not self.playlist:
            # XXX PopupBox please
            logger.debug('empty playlist')
            return False

        if not arg or arg != 'next':
            # first start
            Playlist.build(self)
            if self.random:
                self.randomize()

            if self.background_playlist:
                self.background_playlist.play()

            self.current_item = self.playlist[0]


        if not callable(self.current_item):
            # element is a string, make a correct item
            play_items = []

            # get a real item
            for p in self.get_plugins:
                for i in p.get(self, [ self.current_item ]):
                    play_items.append(i)

            if play_items:
                pos = self.playlist.index(self.current_item)
                self.current_item = play_items[0]
                self.playlist[pos] = play_items[0]


        if not hasattr(self.current_item, 'actions') or not self.current_item.actions():
            # skip item
            pos = self.playlist.index(self.current_item)
            pos = (pos+1) % len(self.playlist)

            if pos:
                self.current_item = self.playlist[pos]
                self.play(menuw=menuw, arg='next')
            else:
                # no repeat
                self.current_item = None
            return True

        if hasattr(self.current_item, 'play'):
            #print('Index=%s' % self.playlist.index(self.current_item)) #DJW
            if self.current_item == self.playlist[-1]:
                arg = 'last'
            self.current_item.play(arg=arg, menuw=menuw)
        else:
            self.current_item.actions()[0][0](menuw=menuw)


    def cache_next(self):
        """
        cache next item, usefull for image playlists
        """
        try:
            pos = self.playlist.index(self.current_item)
            pos = (pos+1) % len(self.playlist)
            if pos and hasattr(self.playlist[pos], 'cache'):
                self.playlist[pos].cache()
        except:
            return

    def stop(self):
        """
        stop playling
        """
        if self.background_playlist:
            self.background_playlist.stop()
        if self.current_item:
            self.current_item.parent = self.parent
            if hasattr(self.current_item, 'stop'):
                try:
                    self.current_item.stop()
                except OSError:
                    pass


    def eventhandler(self, event, menuw=None):
        """
        Handle playlist specific events
        """

        # That doesn't belong here! It should be part of the player!!!
        if event == PLAY_END:
            if self.current_item and self.current_item.type == 'audio':
                rc.post_event(Event(AUDIO_LOG, arg=self.current_item.filename))

        if event in (INPUT_1, INPUT_2, INPUT_3, INPUT_4, INPUT_5) and \
               event.arg and self.current_item and hasattr(self.current_item, 'type'):
            if (self.current_item.type == 'audio'):
                rc.post_event(Event(RATING, (event.arg, self.current_item.filename)))


        if not menuw:
            menuw = self.menuw

        if event == PLAYLIST_TOGGLE_REPEAT:
            self.repeat = not self.repeat
            if self.repeat:
                rc.post_event(Event(OSD_MESSAGE, arg=_('playlist repeat on')))
            else:
                rc.post_event(Event(OSD_MESSAGE, arg=_('playlist repeat off')))

        if event in (PLAYLIST_NEXT, PLAY_END, USER_END) and self.current_item and self.playlist:
            try:
                pos = self.playlist.index(self.current_item)
                pos = (pos+1) % len(self.playlist)
            except ValueError:
                return True

            if pos or self.repeat:
                if hasattr(self.current_item, 'stop'):
                    self.current_item.stop()
                self.current_item = self.playlist[pos]
                self.play(menuw=menuw, arg='next')
                return True
            elif event == PLAYLIST_NEXT:
                rc.post_event(Event(OSD_MESSAGE, arg=_('no next item in playlist')))


        # end and no next item
        if event in (PLAY_END, USER_END, STOP):
            if self.background_playlist:
                self.background_playlist.stop()
            self.current_item = None
            if menuw:
                menuw.show()
            return True


        if event == PLAYLIST_PREV and self.current_item and self.playlist:
            pos = self.playlist.index(self.current_item)
            if pos:
                if hasattr(self.current_item, 'stop'):
                    try:
                        self.current_item.stop()
                    except OSError:
                        logger.log( 9, 'ignore playlist event')
                        return True
                pos = (pos-1) % len(self.playlist)
                self.current_item = self.playlist[pos]
                self.play(menuw=menuw, arg='next')
                return True
            else:
                rc.post_event(Event(OSD_MESSAGE, arg=_('no previous item in playlist')))

        # give the event to the next eventhandler in the list
        return Item.eventhandler(self, event, menuw)

    def rename_possible(self):
        """
        Returns True if the video item can be renamed.
        """
        return self.files and not self.files.read_only



class Mimetype(plugin.MimetypePlugin):
    """
    Plugin class for playlist items
    """
    def __init__(self):
        plugin.MimetypePlugin.__init__(self)

        # register the callback
        plugin.register_callback('fxditem', [], 'playlist', self.fxdhandler)


    def suffix(self):
        """
        return the list of suffixes this class handles
        """
        return config.PLAYLIST_SUFFIX + config.IMAGE_SSHOW_SUFFIX


    def get(self, parent, files):
        """
        return a list of items based on the files
        """
        items = []
        if parent and hasattr(parent, 'display_type'):
            display_type = parent.display_type
        else:
            display_type = None

        if display_type and display_type in config.DIRECTORY_AUTOPLAY_PLAYLISTS:
            autoplay = True
            
        for filename in util.find_matches(files, self.suffix()):
            items.append(Playlist(playlist=filename, parent=parent,
                                  display_type=display_type, build=True, autoplay=autoplay))
            files.remove(filename)

        return items


    def fxdhandler(self, fxd, node):
        """
        parse audio specific stuff from fxd files::

            <?xml version="1.0" ?>
            <freevo>
                <playlist title="foo" random="1|0" repeat="1|0">
                    <cover-img>foo.jpg</cover-img>
                    <files>
                        <directory recursive="1|0">path</directory>
                        <file>filename</file>
                    </files>
                    <info>
                        <description>A nice description</description>
                    </info>
                </playlist>
            </freevo>
        """
        children = fxd.get_children(node, 'files')
        dirname  = os.path.dirname(fxd.getattr(None, 'filename', ''))
        if children:
            children = children[0].children

        items = []
        for child in children:
            fname  = os.path.join(dirname, String(fxd.gettext(child)))
            if child.name == 'directory':
                items.append((fname, fxd.getattr(child, 'recursive', 0)))

            elif child.name == 'file':
                items.append(fname)

        pl = Playlist('', items, fxd.getattr(None, 'parent', None),
                      display_type=fxd.getattr(None, 'display_type'),
                      build=True, random=fxd.getattr(node, 'random', 0),
                      repeat=fxd.getattr(node, 'repeat', 0))

        pl.name     = fxd.getattr(node, 'title')
        pl.image    = fxd.childcontent(node, 'cover-img')
        if pl.image:
            pl.image = vfs.join(vfs.dirname(fxd.filename), pl.image)

        fxd.parse_info(fxd.get_children(node, 'info', 1), pl)
        fxd.getattr(None, 'items', []).append(pl)


# load the MimetypePlugin
mimetype = Mimetype()
plugin.activate(mimetype)
