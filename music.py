# ----------------------------------------------------------------------
# music.py - This is the Freevo MP3 and OGG-Vorbis module. 
# ----------------------------------------------------------------------
# $Id$
#
# Authors:     Krister Lagerstrom <krister@kmlager.com>
#              Aubin Paul <aubin@punknews.org>
#              Dirk Meyer <dmeyer@tzi.de>
#              Thomas Malt <thomas@malt.no>
# Notes:       - Functions having arg and menuw arguments in different
#                order is confusing.
# Todo:        
#
# ----------------------------------------------------------------------
# $Log$
# Revision 1.28  2002/11/01 21:52:21  outlyer
# Whoops. line.rfind returns '-1' on failure, not 0, so add a check for
# rfind > 0, not just 'true'
#
# Revision 1.27  2002/11/01 21:48:29  outlyer
# Crash fix: Remove playlist entries that point to non-existant files, URLs
# excepted.
#
# Revision 1.26  2002/10/31 21:13:09  dischi
# Improved playlist support. A playlist can contain both audio and video
# files. In most cases that will be music mp3s mixed with music videos.
#
# Revision 1.25  2002/10/24 21:19:57  outlyer
# No visible change, but now, we have a function called:
# skin.format_trackr() which takes in the array of id3 tag data and generates
# the track names for the mp3 browser. By default, it just shows the track
# name as it did before, but by editing the formatstr (currently IN the
# function) you can set it to show any combination of artist, album, year,
# track number, and title.
#
# Revision 1.24  2002/10/24 20:16:46  dischi
# bugfix
#
# Revision 1.23  2002/10/24 06:11:45  krister
# Changed debug levels for less output. Don't display length in DrawMP3 if not valid.
#
# Revision 1.22  2002/10/24 06:03:52  krister
# Fixed popup box mania
#
# Revision 1.21  2002/10/23 14:51:29  dischi
# The menu now displays id tag information instead of the filename. If all
# files are from the same artist freevo only displays the title, if we have
# different artists, freevo shows "artist - title". Since the generation
# may take a while now, freevo shows a popup box when there are more than
# 20 files (seems to be more than one album).
#
# The second change is that the auto-generated playlist will play
# imediatly without showing a menu first (this menu makes no sense, or?)
#
# Revision 1.20  2002/10/21 05:09:50  krister
# Started adding support for playing network audio files (i.e. radio stations). Added one station in freevo_config.py, seems to work. Need to fix audioinfo.py with title, time etc. Need to look at using xml files for this too.
#
# Revision 1.19  2002/10/21 02:31:38  krister
# Set DEBUG = config.DEBUG.
#
# Revision 1.18  2002/10/20 18:07:40  dischi
# Added all rom drives with identify media support to the main menu. You
# can't browse DVD, VCD and SVCD and AUDIO-CD support is still missing,
# but it works for mp3 cds.
#
# Revision 1.17  2002/10/12 22:30:45  krister
# Removed debug output.
#
# Revision 1.16  2002/10/08 04:47:47  krister
# Changed the new playlist type list to be displayed correctly. Added popup box for recursive scanning (can take a long time).
#
# Revision 1.15  2002/10/07 05:26:25  outlyer
# Added recursive playlist support from Alex Polite <m2@plusseven.com>
#
# Revision 1.14  2002/10/06 14:42:01  dischi
# log message cleanup
#
# Revision 1.13  2002/10/02 02:40:56  krister
# Applied Alex Polite's patch for using XMMS instead of MPlayer for
# music playing and visualization.
#
# Revision 1.12  2002/09/22 08:50:08  dischi
# deactivated ROM_DRIVES in main menu (crash!). Someone should make this
# identifymedia compatible.
#
# ----------------------------------------------------------------------
# 
# Copyright (C) 2002 Krister Lagerstrom
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
# ----------------------------------------------------------------------
#
"""The Freevo Audio-playing module

More documentation to be written.
"""
__date__    = "2002-07-26"
__version__ = "$Revision$"


import sys
import random
import time, os
import string
import popen2
import fcntl
import select
import struct
import fnmatch
from types import *

import config  # Configuration file object. currently executes a lot of code.
import util    # Various utilities defined for freevo.
import menu    # The menu widget class
import mplayer # Module for running mplayer.
import rc      # The remote controller class
import osd     # Yes.. we use the GUI for printing stuff.
import skin    # The skin class
import datatypes

from playlist import read_playlist

from audioinfo import AudioInfo

# Set to 1 for debug output
DEBUG = config.DEBUG

TRUE = 1
FALSE = 0

if config.MUSICPLAYER == 'XMMS':
    import xmmsaudioplayer # Module for running xmms
    musicplayer = xmmsaudioplayer.AudioPlayer.get_singleton()
elif config.MUSICPLAYER == 'MPLAYER':
    musicplayer = mplayer.get_singleton()
else:
    raise "Set MUSICPLAYER in freevo_config.py to either XMMS or MPLAYER"

rc      = rc.get_singleton()
osd     = osd.get_singleton()
skin = skin.get_singleton()

# remember the position of the selected item in the main menu
main_menu_selected = -1

def play(arg=None, menuw=None, fileinfo=None):
    """
    calls the play function of mplayer to play audio.

    The argument is a tuple containing the file to
    be played and a list of the entire playlist so that the player can
    start on the next one.

    menuw is unused.

    fileinfo is used in place of the 'arg' argument if supplied.

    Arguments: mode - mode of playing audio for music, video, dvd etc.
               file - filename to play.
               list - is playlist, ie rest of files in directory.
    Returns:   None
    """

    if fileinfo:
        musicplayer.play(fileinfo.mode, fileinfo, None)
    else:
        if not arg:
            return

        (mode, file, list) = arg

        musicplayer.play(mode, file, list)
    

#
# EJECT handling
#
def eventhandler(event = None, menuw=None, arg=None):

    global main_menu_selected
    if event == rc.IDENTIFY_MEDIA:
        if menuw.menustack[1] == menuw.menustack[-1]:
            main_menu_selected = menuw.all_items.index(menuw.menustack[1].selected)

        menuw.menustack[1].choices = main_menu_generate()

        menuw.menustack[1].selected = menuw.menustack[1].choices[main_menu_selected]

        if menuw.menustack[1] == menuw.menustack[-1]:
            menuw.init_page()
            menuw.refresh()

    if event == rc.EJECT:

        print 'EJECT1: Arg=%s' % arg

        # Was the handler called for a specific drive?
        if not arg:
            print 'Arg was none'
            if not config.REMOVABLE_MEDIA:
                print 'No removable media defined'
                return # Do nothing if no media defined
            # Otherwise open/close the first drive in the list
            media = config.REMOVABLE_MEDIA[0]
            print 'Selecting first device'
        else:
            media = arg

        print media    
        print dir(media)
        media.move_tray(dir='toggle')

    # Done
    return


# ======================================================================

#
# The Music module main menu
#
def main_menu_generate():
    items = []    

    for vals in config.DIR_AUDIO:
        title, dir = vals[:2]

        if dir.find('://') != -1:
            file_type = None
        else:
            file_type = 'dir'
            
        # The mplayer_opts field is optional, pack it into a tuple with
        # directory name if present.
        if len(vals) > 2:
            mplayer_opts = vals[2]
            dir = (dir, mplayer_opts)

        items += [menu.MenuItem(title, parse_entry, (title, dir), eventhandler,
                                type = file_type)]

    for media in config.REMOVABLE_MEDIA:
        if media.info:

            if not media.info.label:
                print "WARNING: no title for %s given, setting to default" % media.mountdir
                media.info.label = media.mountdir
                
            if media.info.type:
                if media.info.type == 'AUDIO-CD':
                    m = menu.MenuItem('Drive %s (Audio CD)' % media.drivename, None,
                                      None, eventhandler, media)
                    print "Audio cd, not implemented yet"

                elif media.info.type == 'DVD' or media.info.type == 'VCD' or \
                     media.info.type == 'SVCD':

                    m = menu.MenuItem('%s (%s)' % (media.info.label, media.info.type),
                                      None, None, eventhandler, media)
                    m.setImage(('movie', media.info.image))
                    
                else:
                    image_type = 'music'
                    label = media.info.label
                    
                    if media.info.type == 'VIDEO':
                        image_type = 'movie'
                        label += ' (Video CD)' 
                    
                    m = menu.MenuItem(label, parse_entry,
                                      (label, media.mountdir), eventhandler, media)
                    m.setImage((image_type, media.info.image))
                    
        else:
            m = menu.MenuItem('Drive %s (no disc)' % media.drivename, None,
                              None, eventhandler, media)
        items += [m]

    return items


def main_menu(arg=None, menuw=None):
    """
    The music module main menu.

    Arguments:
    Returns:   None
    """

    moviemenu = menu.Menu('MUSIC MAIN MENU', main_menu_generate(), umount_all=1)
    menuw.pushmenu(moviemenu)
            


def parse_entry(arg=None, menuw=None):
    """
    The music module change directory handling function
    formerly known as cwd

    Arguments: Array of arguments - Since that's the way it is done.
    Todo:      Should do a test on dir to see if it is a playlist I open
               for it in main_menu, but it shouldn't be a problem.
               Got crash on playlist handling.
    """

    new_title, mdir = arg

    # mdir can be either a string with the dir/filename, or it
    # is a tuple with the dir/filename and extra mplayer options.
    if type(mdir) == tuple:
        mplayer_opts = mdir[1]
        mdir = mdir[0]
        if DEBUG:
            args = new_title, mdir, mplayer_opts
            print 'music: new_title = %s, mdir = %s, mplayer_opts = %s' % args
    else:
        mplayer_opts = None

    # If the dir is on a removable media it needs to be mounted
    for media in config.REMOVABLE_MEDIA:
        if mdir.find(media.mountdir) == 0:
            media.mount()
            break

    items = []
    files = []
    
    if os.path.isdir(mdir):
        dirnames  = util.getdirnames(mdir)
        playlists = util.match_files(mdir, config.SUFFIX_AUDIO_PLAYLISTS)
        files     = util.match_files(mdir, config.SUFFIX_AUDIO_FILES)

        if DEBUG > 1:
            print 'music:parse_entry(): d="%s"' % dirnames
            print 'music:parse_entry(): p="%s"' % playlists
            print 'music:parse_entry(): f="%s"' % files

	    
        # Add recursive playlist
        if dirnames and config.RECURSIVE_PLAYLIST:
            skin.PopupBox('Creating recursive playlist, please be patient...')
	    playlist = config.FREEVO_CACHEDIR + '/freevo-recursiveplaylist.m3u'
            recursive_files = util.match_files_recursively(
                mdir, config.SUFFIX_AUDIO_FILES)
            #write_playlist(recursive_files, playlist)
            create_randomized_playlist(recursive_files, playlist)
            title = 'PL: Random playlist with songs here and below'
            items += [menu.MenuItem(title, parse_entry, (title, playlist),
                                    eventhandler, None, 'list')]

            
        for dirname in dirnames:
            title = '[' + os.path.basename(dirname) + ']'
        
            # XXX Should I do '_' to ' ' translation here and stuff?
            # Yes recursive stupid.
            m = menu.MenuItem( title, parse_entry, (title, dirname),
                               eventhandler, None, 'dir',
                               None, None, None )
            
            if os.path.isfile(dirname+'/cover.png'): 
                m.setImage(('music', (dirname+'/cover.png')))
            if os.path.isfile(dirname+'/cover.jpg'): 
                m.setImage(('music', (dirname+'/cover.jpg')))
            items += [m]

        # If we have more than 20 files this seems to be more than
        # one album. To load all id tags may take a while, warn the user
        # if there is not a popup already
        if (len(files) > 20) and not (dirnames and config.RECURSIVE_PLAYLIST):
            skin.PopupBox('Creating menu, please wait...')

        # Add autogenerated playlist
        if files and config.RANDOM_PLAYLIST:        	
            playlist = config.FREEVO_CACHEDIR + '/freevo-autoplaylist.m3u'
            path_files = []
            create_randomized_playlist(files, playlist)
            title = 'PL: Random playlist with all songs here'
            items += [menu.MenuItem(title, parse_entry, (title, playlist),
                                    eventhandler, None, 'list')]
    
        for playlist in playlists:
            title = 'PL: ' + os.path.basename(playlist)[:-4]
            
            items += [menu.MenuItem(title, parse_entry, (title, playlist),
                                    eventhandler, None, 'list')]
            

    for pl_type in config.SUFFIX_AUDIO_PLAYLISTS:
        if fnmatch.fnmatchcase(mdir, pl_type):
            files = read_playlist(mdir)
            if mdir.find(config.FREEVO_CACHEDIR) == 0:
                # this is a autoplaylist, start playing it right now
                play(('audio', files[0], files))
                return
            
    if files or os.path.isdir(mdir):

        artist = None
        alist = []

        # check if all files have the same artist
        for fname in files:
            if DEBUG > 1:
                print 'music: getting info for "%s"' % fname
	    if os.path.exists(fname) or (fname.find("://") > 0):
                a = AudioInfo(fname)
                if a.artist and artist == None:
                    artist = a.artist
                elif a.artist and artist != a.artist:
                    artist = ''
                alist += [a]
	    else:
	        print 'music: %s is missing, removing from playlist' % fname

        for a in alist:

            # if the files have different artists and we have
            # artist informations, display it in the title
            if a.artist and a.title and not artist:
                title = skin.format_track(a) # "%s - %s" % (a.artist, a.title)

            # display the title as menu item title
            elif a.title:
                title = skin.format_track(a) #a.title

            # take the filename
            else:
                title = os.path.splitext(os.path.basename(a.filename))[0]

            file_type = 'music'
            for v_type in config.SUFFIX_MPLAYER_FILES:
                if fnmatch.fnmatchcase(a.filename, v_type):
                    file_type = 'movie'
                    
            m = menu.MenuItem( title, play, (None, a.filename, files))

            m.setImage((file_type, a.image))
            items += [ m ]
                
        mp3menu = menu.Menu('MUSIC MENU', items, xml_file=mdir)
        menuw.pushmenu(mp3menu)

    else:
        """ Note:
        What happens here if the user specifies a file directly?
        We should be able to handle that. that opens for a more
        generic function..
        """

        if DEBUG:
            print 'music: got file entry in main menu'

        else:
            # Set up a FileInformation object if mplayer_opts was specified
            if mplayer_opts:
                fileinfo = datatypes.FileInformation('audio', mdir, mplayer_opts)
                play(fileinfo=fileinfo)
            else:
                play(arg=['audio', mdir, None], menuw=None)

        
#
# Autogenerated randomized playlist with all MP3 files in this directory
#
def create_randomized_playlist(files, fname):
    templist = open(fname, 'w')

    # Do not modify the list that was passed
    flist = files[:]
    
    while flist:
        element = random.choice(flist)
        flist.remove(element)
        templist.write(element + '\n')

