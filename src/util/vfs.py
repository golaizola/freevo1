# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# Virtual filesystem
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
#
# This is a virtual filesystem for Freevo. It uses the structure in
# config.OVERLAY_DIR to store files that should be in the normal
# directory, but the user has no write access to it. It's meant to
# store fxd and image files (covers).
#
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
logger = logging.getLogger("freevo.util.vfs")

import os
import copy
import traceback
import codecs
from stat import *

import config

def www_link_cachedir():
    '''returns the www link cache directory name
    if the directory does not exist it is created
    '''
    cache_dir = '%s/link_cache' % (config.WEBSERVER_CACHEDIR)
    cache_dir_mode = S_IMODE(os.stat(config.WEBSERVER_CACHEDIR)[ST_MODE])
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir, cache_dir_mode)
    return cache_dir


def www_image_cachedir():
    '''returns the www image cache directory name
    if the directory does not exist it is created
    '''
    cache_dir = '%s/image_cache' % (config.WEBSERVER_CACHEDIR)
    cache_dir_mode = S_IMODE(os.stat(config.WEBSERVER_CACHEDIR)[ST_MODE])
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir, cache_dir_mode)
    return cache_dir


def getoverlay(directory):
    if not directory.startswith('/'):
        directory = os.path.abspath(directory)
    if directory.startswith(config.OVERLAY_DIR):
        return directory
    for media in config.REMOVABLE_MEDIA:
        if directory.startswith(media.mountdir):
            directory = directory[len(media.mountdir):]
            return '%s/disc/%s%s' % (config.OVERLAY_DIR, String(media.id), directory)
    return config.OVERLAY_DIR + directory


def getwwwoverlay(directory):
    if not directory.startswith('/'):
        directory = os.path.abspath(directory)
    if directory.startswith(www_image_cachedir()):
        return directory
    return www_image_cachedir() + directory


def abspath(name):
    """
    return the complete filename (including OVERLAY_DIR)
    """
    if os.path.exists(name):
        if not name.startswith('/'):
            return os.path.abspath(name)
        return name
    overlay = getoverlay(name)
    if overlay and os.path.isfile(overlay):
        return overlay
    return ''


def isfile(name):
    """
    return if the given name is a file
    """
    if os.path.isfile(name):
        return True
    overlay = getoverlay(name)
    return overlay and os.path.isfile(overlay)


def isdir(name):
    """
    return if the given name is a file
    """
    if os.path.isdir(name):
        return True
    overlay = getoverlay(name)
    return overlay and os.path.isfile(overlay)


def unlink(name):
    absname = abspath(name)
    if not absname:
        raise IOError, 'file %s not found' % name
    os.unlink(absname)


def stat(name):
    absname = abspath(name)
    if not absname:
        raise IOError, 'file %s not found' % name
    return os.stat(absname)


def mtime(name):
    """
    Return the modification time of the file. If the files also exists
    in OVERLAY_DIR, return the max of both. If the file does not exist
    in the normal directory, OSError is raised.
    """
    t = os.stat(name)[ST_MTIME]
    try:
        return max(os.stat(getoverlay(name))[ST_MTIME], t)
    except (OSError, IOError):
        return t


def open(name, mode='r'):
    """
    open the file
    """
    try:
        return file(name, mode)
    except:
        overlay = os.path.abspath(getoverlay(name))
        if not overlay:
            raise OSError
        try:
            if not os.path.isdir(os.path.dirname(overlay)):
                os.makedirs(os.path.dirname(overlay), mode=04775)
        except IOError:
            logger.warning('error creating dir %s', os.path.dirname(overlay))
            raise IOError
        try:
            return file(overlay, mode)
        except IOError:
            logger.warning('error opening file %s', overlay)
            raise IOError


def codecs_open(name, mode, encoding):
    """
    use codecs.open to open the file
    """
    try:
        return codecs.open(name, mode, encoding=encoding)
    except:
        overlay = os.path.abspath(getoverlay(name))
        if not overlay:
            raise OSError
        try:
            if not os.path.isdir(os.path.dirname(overlay)):
                os.makedirs(os.path.dirname(overlay))
        except IOError:
            logger.warning('error creating dir %s', os.path.dirname(overlay))
            raise IOError
        try:
            return codecs.open(overlay, mode, encoding=encoding)
        except IOError, e:
            logger.warning('error opening file %s', overlay)
            raise IOError, e


def listdir(directory, handle_exception=True, include_dot_files=False, include_overlay=False):
    """
    get a directory listing (including OVERLAY_DIR)
    """
    try:
        files = []

        if include_dot_files:
            for f in os.listdir(directory):
                if not f in ('.svn', '.xvpics', '.thumbnails', '.pics', 'folder.fxd', 'lost+found'):
                    files.append(os.path.join(directory, f))
        else:
            for f in os.listdir(directory):
                if not f.startswith('.') and not f in ('folder.fxd', 'lost+found'):
                    files.append(os.path.join(directory, f))

        if not include_overlay:
            return files

        overlay = getoverlay(directory)
        if overlay and overlay != directory and os.path.isdir(overlay):
            for fname in os.listdir(overlay):
                if fname.endswith('.raw') or fname.startswith('.') or fname in ('folder.fxd', 'lost+found') or \
                    fname.find('.thumb.') > 0:
                    continue
                f = os.path.join(overlay, fname)
                if not os.path.isdir(f):
                    files.append(f)
        return files

    except OSError, why:
        logger.warning('Cannot list dir %r: %s', directory, why)
        traceback.print_exc()
        if not handle_exception:
            raise OSError
        return []


def isoverlay(name):
    """
    return if the name is in the overlay dir
    """
    return name.startswith(config.OVERLAY_DIR)


def normalize(name):
    """
    remove OVERLAY_DIR if it's in the path
    """
    if isoverlay(name):
        name = name[len(config.OVERLAY_DIR):]
        if name.startswith('disc-set'):
            # revert it, disc-sets have no real dir
            return os.path.join(config.OVERLAY_DIR, name)
        if name.startswith('disc'):
            name = name[5:]
            id = name[:name.find('/')]
            name = name[name.find('/')+1:]
            for media in config.REMOVABLE_MEDIA:
                if media.id == id:
                    name = os.path.join(media.mountdir, name)
        return name
    return name


# some other os functions (you don't need to use them)
basename = os.path.basename
join     = os.path.join
splitext = os.path.splitext
basename = os.path.basename
dirname  = os.path.dirname
exists   = os.path.exists
isdir    = os.path.isdir
islink   = os.path.islink
