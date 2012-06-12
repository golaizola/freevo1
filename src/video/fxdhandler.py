# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# Handler for <movie> and <disc-set> tags in a fxd file
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
Handle FXD (Freevo Extended Data) files.
"""
import logging
logger = logging.getLogger("freevo.video.fxdhandler")

from videoitem import VideoItem
from item import FileInformation
import os
import skin

def parse_movie(fxd, node):
    """
    Callback for VideoItem <movie>::

        <movie title>
            <cover-img>file</cover-img>
            <video mplayer-options>
                <dvd|vcd|file id name media_id mplayer-options>file</>+
            <variants>
                <variant>
                    <part ref mplayer-options>
                        <subtitle media_id>file</subtitle>
                        <audio media_id>file</audio>
                    </part>+
                </variant>+
            </variants>
            <info/>
        </movie>
    """

    files = []

    def parse_video_child(fxd, node, dirname):
        """
        parse a subitem from <video>
        """
        filename   = String(fxd.gettext(node))
        media_id   = fxd.getattr(node, 'media-id')
        mode       = node.name
        id         = fxd.getattr(node, 'id')
        options    = fxd.getattr(node, 'mplayer-options')
        player     = fxd.childcontent(node, 'player')
        playlist   = fxd.get_children(node, 'playlist') and True or False

        if mode == 'file':
            if not media_id:
                filename = os.path.join(dirname, filename)
                if vfs.isoverlay(filename):
                    filename = vfs.normalize(filename)
            if filename and not filename in files:
                files.append(filename)
        if mode == 'url':
            return id, filename, media_id, options, player, playlist
        return id, String('%s://%s' % (String(mode), String(filename))), \
               media_id, options, player, playlist


    item       = VideoItem('', fxd.getattr(None, 'parent', None), parse=False)
    title      = name=fxd.getattr(node, 'title')
    item.name  = title
    dirname    = os.path.dirname(fxd.filename)
    image      = ''
    item.image = fxd.childcontent(node, 'cover-img')

    if item.image:
        try:
            item.image = vfs.abspath(os.path.join(dirname, str(item.image)))
        except UnicodeEncodeError:
            logger.debug('os.path.join(dirname=%r, item.image=%r)', dirname, item.image)
            raise
        image = item.image

    fxd.parse_info(node, item, {'runtime': 'length'})

    video = fxd.get_children(node, 'video')
    if video:
        mplayer_options = fxd.getattr(video[0], 'mplayer-options')
        video = fxd.get_children(video[0], 'file') + \
                fxd.get_children(video[0], 'vcd') + \
                fxd.get_children(video[0], 'dvd') + \
                fxd.get_children(video[0], 'url')

    variants = fxd.get_children(node, 'variants')
    if variants:
        variants = fxd.get_children(variants[0], 'variant')

    if variants:
        # a list of variants
        id = {}
        for v in video:
            video_child = parse_video_child(fxd, v, dirname)
            id[video_child[0]] = video_child

        for variant in variants:
            mplayer_options += " " + fxd.getattr(variant, 'mplayer-options');
            parts = fxd.get_children(variant, 'part')
            if len(parts) == 1:
                # a variant with one file
                ref = fxd.getattr(parts[0] ,'ref')
                v = VideoItem(id[ref][1], parent=item, info=item.info, parse=False)
                v.files = None
                v.media_id, v.mplayer_options, player, is_playlist = id[ref][2:]
                if player:
                    v.force_player = player
                if is_playlist:
                    v.is_playlist  = True

                audio = fxd.get_children(parts[0], 'audio')
                if audio:
                    audio = { 'media_id': fxd.getattr(audio[0], 'media-id'),
                              'file'    : fxd.gettext(audio[0]) }
                    if not audio['media_id']:
                        audio['file'] = os.path.join(dirname, audio['file'])
                else:
                    audio = {}
                v.audio_file = audio

                subtitle = fxd.get_children(parts[0], 'subtitle')
                if subtitle:
                    subtitle = { 'media_id': fxd.getattr(subtitle[0], 'media-id'),
                                 'file'    : fxd.gettext(subtitle[0]) }
                    if not subtitle['media_id']:
                        subtitle['file'] = os.path.join(dirname, subtitle['file'])
                else:
                    subtitle = {}
                v.subtitle_file = subtitle

                # global <video> mplayer_options
                if mplayer_options:
                    v.mplayer_options += mplayer_options
            else:
                # a variant with a list of files
                v = VideoItem('', parent=item, info=item.info, parse=False)
                for p in parts:
                    ref = fxd.getattr(p ,'ref')
                    audio    = fxd.get_children(p, 'audio')
                    subtitle = fxd.get_children(p, 'subtitle')

                    if audio:
                        audio = { 'media_id': fxd.getattr(audio[0], 'media-id'),
                                  'file'    : fxd.gettext(audio[0]) }
                        if not audio['media_id']:
                            audio['file'] = os.path.join(dirname, audio['file'])
                    else:
                        audio = {}

                    if subtitle:
                        subtitle = { 'media_id': fxd.getattr(subtitle[0], 'media-id'),
                                     'file'    : fxd.gettext(subtitle[0]) }
                        if not subtitle['media_id']:
                            subtitle['file'] = os.path.join(dirname, subtitle['file'])
                    else:
                        subtitle = {}

                    sub = VideoItem(id[ref][1], parent=v, info=item.info, parse=False)
                    sub.files = None
                    sub.media_id, sub.mplayer_options, player, is_playlist = id[ref][2:]
                    sub.subtitle_file = subtitle
                    sub.audio_file    = audio
                    # global <video> mplayer_options
                    if mplayer_options:
                        sub.mplayer_options += mplayer_options
                    v.subitems.append(sub)

            v.name = fxd.getattr(variant, 'name')
            item.variants.append(v)

    else:
        # one or more files, this is directly for the item

        try:
            id, url, item.media_id, item.mplayer_options, player, is_playlist = parse_video_child(
                fxd, video[0], dirname)
        except (IndexError, TypeError), why:
            logger.warning('%r is corrupt', fxd.filename)
            raise
        if url.startswith('file://') and os.path.isfile(url[7:]):
            variables = item.info.get_variables()
            item.set_url(url, info=True)
            item.info.set_variables(variables)
        elif url.startswith('file://') and os.path.isdir(url[7:]):
            # dvd dir
            variables = item.info.get_variables()
            item.set_url(url.replace('file://', 'dvd:/')+ '/VIDEO_TS/', info=True)
            item.info.set_variables(variables)
        else:
            item.set_url(url, info=False)
#        if title:
#            item.name = title
        if player:
            item.force_player = player
        if is_playlist:
            item.is_playlist  = True
        if len(video) == 1:
            # global <video> mplayer_options
            if mplayer_options:
                item.mplayer_options += mplayer_options

        # if there is more than one item add them to subitems
        if len(video) > 1:
            # a list of files
            subitem_matched = False
            for s in video:
                #id, url, item.media_id, mplayer_options, player, is_playlist = parse_video_child(fxd, s, dirname)
                video_child = parse_video_child(fxd, s, dirname)
                url = video_child[1]

                v = VideoItem(url, parent=item, info=item.info, parse=False)

                if url.startswith('file://'):
                    v.files = FileInformation()

                    v.files.append(url[7:])
                    if url == item.url and not subitem_matched:
                        subitem_matched = True
                        v.files.fxd_file  = fxd.filename
                        if item.image:
                            v.files.image = item.image
                else:
                    v.files = None

                v.media_id, v.mplayer_options, player, is_playlist = video_child[2:]
                if player:
                    v.force_player = player
                if is_playlist:
                    item.is_playlist = True
                # global <movie> mplayer_options
                if mplayer_options:
                    v.mplayer_options += ' ' + mplayer_options
                item.subitems.append(v)

    if not hasattr(item, 'files') or not item.files:
        item.files = FileInformation()
    item.files.files     = files

    item.files.fxd_file  = fxd.filename
    if image:
        item.files.image = image

    # remove them from the filelist (if given)
    duplicates = fxd.getattr(None, 'duplicate_check', [])
    for f in files:
        try:
            duplicates.remove(f)
        except:
            pass

    item.name = item.parse_name(title)
    fxd.getattr(None, 'items', []).append(item)


def parse_disc_set(fxd, node):
    """
    Callback for VideoItem <disc-set>
    """
    item = VideoItem('', fxd.getattr(None, 'parent', None), parse=False)

    dirname  = os.path.dirname(fxd.filename)

    item.name  = fxd.getattr(node, 'title')
    item.image = fxd.childcontent(node, 'cover-img')
    if item.image:
        item.image = vfs.abspath(os.path.join(dirname, item.image))

    fxd.parse_info(node, item, {'runtime': 'length'})
    item.__fxd_rom_info__      = True
    item.__fxd_rom_label__     = []
    item.__fxd_rom_id__        = []
    item.__fxd_files_options__ = []
    for disc in fxd.get_children(node, 'disc'):
        id = fxd.getattr(disc, 'media-id')
        if id:
            item.__fxd_rom_id__.append(id)

        label = fxd.getattr(disc, 'label-regexp')
        if label:
            item.__fxd_rom_label__.append(label)

        # what to do with the mplayer_options? We can't use them for
        # one disc, or can we? And file_ops? Also only on a per disc base.
        # Answer: it applies to all the files of the disc, unless there
        #         are <file-opt> which specify to what files the
        #         mplayer_options apply. <file-opt> is not such a good
        #         name,  though.
        # So I ignore that we are in a disc right now and use the 'item'
        item.mplayer_options = fxd.getattr(disc, 'mplayer_options')
        there_are_file_opts = 0
        for f in fxd.get_children(disc, 'file-opt'):
            there_are_file_opts = 1
            file_media_id = fxd.getattr(f, 'media-id')
            if not file_media_id:
                file_media_id = id
            mpl_opts = item.mplayer_options + ' ' + fxd.getattr(f, 'mplayer-options')
            opt = { 'file-id' : file_media_id + fxd.gettext(f),
                    'mplayer_options': mpl_opts }
            item.__fxd_files_options__.append(opt)
        if there_are_file_opts:
            # in this case, the disc/@mplayer_options is retricted to the set
            # of files defined in the file-opt elements
            item.mplayer_options = ''

    if not item.files:
        item.files = FileInformation()
    item.files.fxd_file  = fxd.filename
    if fxd.is_skin_fxd:
        item.skin_fxd = fxd.filename
    fxd.getattr(None, 'items', []).append(item)


def parse_mplayer_add_option(fxd, node):
    """
    """
    pass


def parse_mplayer_options(fxd, node):
    """
    Callback for VideoItem <mplayer-options>::

        <freevo>
          <movie title="Batman: Dead End">
            <cover-img>foo.jpg</cover-img>
            <video>
              <file id="f1">Batman_Dead_End.mpg
                <mplayer>
                  <option name="vf" crop="704:272:8:102"/>
                  <option name="vf" scale="720:576"/>
                </mplayer>
              </file>
            </video>
          </movie>
        </freevo>

    @returns: a dictionary of mplayer options
    """
    mplayer_options = {}
    logger.log( 9, 'parse_mplayer_mplayer_options(fxd=%r, node=%r)', fxd, node)
    item = VideoItem('', fxd.getattr(None, 'parent', None), parse=False)
    print 'item=%r' % (item.__dict__)

    dirname  = os.path.dirname(fxd.filename)

    print fxd.get_children(node, '*')
    video_nodes = fxd.get_children(node, 'video')
    for video_node in fxd.get_children(node, 'video'):
        for file_node in fxd.get_children(video_node, 'file'):
            for mplayer_node in fxd.get_children(file_node, 'mplayer'):
                for option_node in fxd.get_children(mplayer_node, 'option'):
                    name = option_node.attrs[('', 'name')]
                    value = option_node.attrs[('', 'value')]
                    if mplayer_options.has_key(name):
                        mplayer_options[name].append(value)
                    else:
                        mplayer_options[name] = [value]
    print 'mplayer_options=%r' % (mplayer_options)
    return mplayer_options
