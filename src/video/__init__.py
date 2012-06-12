# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# __init__.py - interface between mediamenu and video
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
Interface between media menu and video items.
"""
import logging
logger = logging.getLogger("freevo.video")

import os
import copy
import re
import string

import config
import util
import util.videothumb
import plugin

from videoitem import VideoItem, FileInformation

# variables for the hashing function
fxd_database        = {}
discset_information = {}
tv_show_information = {}


class PluginInterface(plugin.MimetypePlugin):
    """
    Plugin to handle all kinds of video items
    """

    def __init__(self):
        plugin.MimetypePlugin.__init__(self)
        self.display_type = [ 'video' ]
        if config.AUDIO_SHOW_VIDEOFILES:
            self.display_type = [ 'video', 'audio' ]

        # load the fxd part of video
        import fxdhandler

        plugin.register_callback('fxditem', ['video'], 'movie',    fxdhandler.parse_movie)
        plugin.register_callback('fxditem', ['video'], 'disc-set', fxdhandler.parse_disc_set)

        # activate the mediamenu for video
        plugin.activate('mediamenu', level=plugin.is_active('video')[2], args='video')


    def suffix(self):
        """
        return the list of suffixes this class handles
        """
        return config.VIDEO_SUFFIX


    def get(self, parent, files):
        """
        return a list of items based on the files
        """
        items = []

        all_files = util.find_matches(files, config.VIDEO_SUFFIX)
        # sort all files to make sure 1 is before 2 for auto-join
        all_files.sort(lambda l, o: cmp(l.upper(), o.upper()))

        hidden_files = []

        pat = re.compile(config.VIDEO_AUTOJOIN_REGEX)
        for file in all_files:
            if parent and parent.type == 'dir' and \
                   hasattr(parent, 'VIDEO_DIRECTORY_AUTOBUILD_THUMBNAILS') and \
                   parent.VIDEO_DIRECTORY_AUTOBUILD_THUMBNAILS:
                util.videothumb.snapshot(file, update=False, popup=True)

            if file in hidden_files:
                files.remove(file)
                continue

            x = VideoItem(file, parent)

            # join video files
            if config.VIDEO_AUTOJOIN:
                mat = pat.search(file)
                if mat is not None:
                    add_file = []
                    start = file.find(mat.group(1), mat.start())
                    end = start + len(mat.group(1))
                    stem = file[:start]
                    tail = file[end:]
                    next = 2
                    for f in all_files:
                        next_str = '%0*d' % (end-start, next)
                        filename = stem+next_str+tail
                        if filename in all_files:
                            add_file.append(filename)
                        else:
                            break
                        next += 1
                    if len(add_file) > 0:
                        name = stem+tail
                        x = VideoItem(name, parent)
                        x.files = FileInformation()
                        x.subitems.append(VideoItem(file, x))
                        x.set_url(file, True)
                        for filename in add_file:
                            x.files.append(filename)
                            x.subitems.append(VideoItem(filename, x))
                            hidden_files.append(filename)

            if parent and parent.media:
                file_id = String(parent.media.id) + file[len(os.path.join(parent.media.mountdir, '')):]
                try:
                    x.mplayer_options = discset_information[file_id]
                    logger.debug('x.mplayer_options=%r', x.mplayer_options)
                except KeyError:
                    pass
            items.append(x)
            files.remove(file)

        for i in copy.copy(files):
            if os.path.isdir(i+'/VIDEO_TS'):
                # DVD Image, trailing slash is important for Xine
                items.append(VideoItem('dvd://' + i[1:] + '/VIDEO_TS/', parent))
                files.remove(i)

        return items


    def dirinfo(self, diritem):
        """
        set information for a diritem based on the content, etc.
        """
        global tv_show_information
        if not diritem.image and config.VIDEO_SHOW_DATA_DIR:
            diritem.image = util.getimage(vfs.join(config.VIDEO_SHOW_DATA_DIR, vfs.basename(diritem.dir).lower()))

        if tv_show_information.has_key(vfs.basename(diritem.dir).lower()):
            tvinfo = tv_show_information[vfs.basename(diritem.dir).lower()]
            diritem.info.set_variables(tvinfo[1])
            if not diritem.image:
                diritem.image = tvinfo[0]
            if not diritem.skin_fxd:
                diritem.skin_fxd = tvinfo[3]


    def dirconfig(self, diritem):
        """
        adds configure variables to the directory
        """
        return [
            ('VIDEO_DIRECTORY_AUTOBUILD_THUMBNAILS', _('Directory Autobuild Thumbnails '),
            _('Build video thumbnails for all items (may take a while when entering).'),
            False)
        ]



def hash_fxd_movie_database():
    """
    hash fxd movie files in some directories. This is used e.g. by the
    rom drive plugin, but also for a directory and a videoitem.
    """
    import fxditem

    global tv_show_information
    global discset_information
    global fxd_database

    fxd_database['id']    = {}
    fxd_database['label'] = []
    discset_information  = {}
    tv_show_information  = {}

    rebuild_file = os.path.join(config.FREEVO_CACHEDIR, 'freevo-rebuild-database')
    if vfs.exists(rebuild_file):
        try:
            os.remove(rebuild_file)
        except OSError:
            print '*********************************************************'
            print
            print '*********************************************************'
            print 'ERROR: unable to remove %s' % rebuild_file
            print 'please fix permissions'
            print '*********************************************************'
            print
            return 0

    logger.log( 9, "Building the xml hash database...")

    files = []
    if not config.VIDEO_ONLY_SCAN_DATADIR:
        if len(config.VIDEO_ITEMS) == 2:
            for name, dir in config.VIDEO_ITEMS:
                files += util.recursefolders(dir, 1, '*.fxd', 1)

    for subdir in ('disc', 'disc-set'):
        files += util.recursefolders(vfs.join(config.OVERLAY_DIR, subdir), 1, '*.fxd', 1)

    for info in fxditem.mimetype.parse(None, files, display_type='video'):
        if hasattr(info, '__fxd_rom_info__'):
            for i in info.__fxd_rom_id__:
                fxd_database['id'][i] = info
            for l in info.__fxd_rom_label__:
                fxd_database['label'].append((re.compile(l), info))
            for fo in info.__fxd_files_options__:
                discset_information[fo['file-id']] = fo['mplayer-options']

    if config.VIDEO_SHOW_DATA_DIR:
        files = util.recursefolders(config.VIDEO_SHOW_DATA_DIR, 1, '*.fxd', 1)
        for info in fxditem.mimetype.parse(None, files, display_type='video'):
            if info.type != 'video':
                continue
            k = vfs.splitext(vfs.basename(info.files.fxd_file))[0]
            tv_show_information[k] = (info.image, info.info, info.mplayer_options, info.skin_fxd)
            if hasattr(info, '__fxd_rom_info__'):
                for fo in info.__fxd_files_options__:
                    discset_information[fo['file-id']] = fo['mplayer-options']

    logger.log( 9, 'done')
    return 1
