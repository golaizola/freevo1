#if 0 /*
# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# main.py - This is the Freevo main application code
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.67  2003/08/31 14:19:11  dischi
# show splashscreen on startup
#
# Revision 1.66  2003/08/26 20:28:05  outlyer
# Black the screen on shutdown
#
# Revision 1.65  2003/08/23 12:51:41  dischi
# removed some old CVS log messages
#
# Revision 1.64  2003/08/22 18:21:24  dischi
# fix to prevent pygame from crashing
#
# Revision 1.63  2003/08/22 17:51:29  dischi
# Some changes to make freevo work when installed into the system
#
# Revision 1.62  2003/08/20 22:29:37  gsbarbieri
# UPPER CASE TEXT IS UGLY! :)
#
# Revision 1.61  2003/08/16 12:55:06  dischi
# wait when shutdown
#
# Revision 1.60  2003/08/15 19:23:20  dischi
# support --force-fs for freevo -fs
#
# Revision 1.59  2003/08/12 19:39:06  dischi
# Added event_lister to get all events
#
# Revision 1.56  2003/08/04 20:38:59  dischi
# Notice the user that pre-caching is missing
#
# Revision 1.55  2003/08/01 13:17:48  outlyer
# Added Matthew Weber's "rc repeat" patch; it requires pylirc 0.0.4 or newer (CVS)
#
# Revision 1.54  2003/07/30 15:13:00  outlyer
# Add encoding to remove some warnings from Python 2.3. Has no effect on
# Python < 2.3
#
# Revision 1.53  2003/07/13 19:35:44  rshortt
# Change osd.focused_app to a function that returns the last object in
# app_list.  Maintaining this list is helpfull for managing 'toplevel'
# GUIObject based apps (popup types).
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

# Must do this here to make sure no os.system() calls generated by module init
# code gets LD_PRELOADed
import os
os.environ['LD_PRELOAD'] = ''

import sys, time
import traceback

sys.path.append('.')

# Gentoo runtime has some python files in runtime/python
if os.path.exists('./runtime/python'):
    sys.path.append('./runtime/python')
    
import config

import util    # Various utilities
import osd     # The OSD class, used to communicate with the OSD daemon
import menu    # The menu widget class
import skin    # The skin class
import rc      # The RemoteControl class.

import signal

from item import Item
import event as em


skin    = skin.get_singleton()


DEBUG = config.DEBUG

TRUE  = 1
FALSE = 0

# Create the remote control object
rc_object = rc.get_singleton()

# Create the OSD object
osd = osd.get_singleton()

# Create the MenuWidget object
menuwidget = menu.get_singleton()


def shutdown(menuw=None, arg=None, allow_sys_shutdown=1):
    """
    function to shut down freevo or the whole system
    """
    import plugin

    osd.clearscreen(color=osd.COL_BLACK)
    osd.drawstring('shutting down...', osd.width/2 - 90, osd.height/2 - 10,
                   fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
    osd.update()

    time.sleep(0.5)

    if arg == None:
        sys_shutdown = allow_sys_shutdown and 'ENABLE_SHUTDOWN_SYS' in dir(config)
    else:
        sys_shutdown = arg

    # XXX temporary kludge so it won't break on old config files
    if sys_shutdown:  
        if config.ENABLE_SHUTDOWN_SYS:
            # shutdown dual head for mga
            if config.CONF.display == 'mga':
                os.system('%s runapp matroxset -f /dev/fb1 -m 0' % \
                          os.environ['FREEVO_SCRIPT'])
                time.sleep(1)
                os.system('%s runapp matroxset -f /dev/fb0 -m 1' % \
                          os.environ['FREEVO_SCRIPT'])
                time.sleep(1)

            osd.shutdown()
            plugin.shutdown()

            os.system(config.SHUTDOWN_SYS_CMD)
            # let freevo be killed by init, looks nicer for mga
            while 1:
                time.sleep(1)
            return

    # SDL must be shutdown to restore video modes etc
    osd.shutdown()

    #
    # Exit Freevo
    #
    
    # Shutdown any daemon plugins that need it.
    plugin.shutdown()
    osd.clearscreen(color=osd.COL_BLACK)
    osd.shutdown()
    os.system('%s stop' % os.environ['FREEVO_SCRIPT'])

    # Just wait until we're dead. SDL cannot be polled here anyway.
    while 1:
        time.sleep(1)
        


def get_main_menu(parent):
    """
    function to get the items on the main menu based on the settings
    in the skin
    """

    import plugin

    items = []
    for p in plugin.get('mainmenu'):
        items += p.items(parent)
        
    return items
    

class SkinSelectItem(Item):
    """
    Item for the skin selector
    """
    def __init__(self, parent, name, image, skin):
        Item.__init__(self, parent)
        self.name  = name
        self.image = image
        self.skin  = skin
        
    def actions(self):
        return [ ( self.select, '' ) ]

    def select(self, arg=None, menuw=None):
        """
        Load the new skin and rebuild the main menu
        """
        skin.settings = skin.LoadSettings(self.skin, copy_content = FALSE)
        pos = menuw.menustack[0].choices.index(menuw.menustack[0].selected)
        menuw.menustack[0].choices = get_main_menu(self.parent)
        menuw.menustack[0].selected = menuw.menustack[0].choices[pos]
        menuw.back_one_menu()

        
class MainMenu(Item):
    """
    this class handles the main menu
    """
    
    def getcmd(self):
        """
        Setup the main menu and handle events (remote control, etc)
        """
        
        items = get_main_menu(self)

        mainmenu = menu.Menu('Freevo Main Menu', items, item_types='main', umount_all = 1)
        menuwidget.pushmenu(mainmenu)
        osd.add_app(menuwidget)

    def eventhandler(self, event = None, menuw=None, arg=None):
        """
        Automatically perform actions depending on the event, e.g. play DVD
        """

        # pressing DISPLAY on the main menu will open a skin selector
        # (only for the new skin code)
        if event == em.MENU_CHANGE_STYLE:
            items = []
            for name, image, skinfile in skin.GetSkins():
                items += [ SkinSelectItem(self, name, image, skinfile) ]

            menuwidget.pushmenu(menu.Menu('SKIN SELECTOR', items))
            return TRUE

        # give the event to the next eventhandler in the list
        return Item.eventhandler(self, event, menuw)
        
    

def signal_handler(sig, frame):
    import plugin
    if sig in (signal.SIGTERM, signal.SIGINT):
        osd.clearscreen(color=osd.COL_BLACK)
        osd.shutdown() # SDL must be shutdown to restore video modes etc

        # Shutdown any daemon plugins that need it.
        plugin.shutdown()
        os.system('%s stop' % os.environ['FREEVO_SCRIPT'])


#
# Main init
#
def main_func():
    import plugin

    if hasattr(skin, 'Splashscreen'):
        plugin.init(skin.Splashscreen().progress)
    else:
        plugin.init()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    main = MainMenu()
    main.getcmd()

    poll_plugins = plugin.get('daemon_poll')
    eventhandler_plugins  = []
    eventlistener_plugins = []

    for p in plugin.get('daemon_eventhandler'):
        if hasattr(p, 'event_listener') and p.event_listener:
            eventlistener_plugins.append(p)
        else:
            eventhandler_plugins.append(p)
    
    # Kick off the main menu loop
    if config.DEBUG: print 'Main loop starting...'

    while 1:

        # Get next command
        while 1:

            event, event_repeat_count = rc_object.poll()
            # OK, now we have a repeat_count... to whom could we give it?
            if event:
                break

            for p in poll_plugins:
                if not (rc_object.app and p.poll_menu_only):
                    p.poll_counter += 1
                    if p.poll_counter == p.poll_interval:
                        p.poll_counter = 0
                        p.poll()

            time.sleep(0.01)

        for p in poll_plugins:
            if not (rc_object.app and p.poll_menu_only):
                p.poll_counter += 1
                if p.poll_counter == p.poll_interval:
                    p.poll_counter = 0
                    p.poll()

        for p in eventlistener_plugins:
            p.eventhandler(event=event)

        if event == em.FUNCTION_CALL:
            event.arg()

        # Send events to either the current app or the menu handler
        elif rc_object.app:
            if not rc_object.app(event):
                for p in eventhandler_plugins:
                    if p.eventhandler(event=event):
                        break
                else:
                    if DEBUG: print 'no eventhandler for event %s' % event

        else:
            app = osd.focused_app()
            if app:
                app.eventhandler(event)
            else:
                if DEBUG: print 'no target for events given'
                
#
# Main function
#
if __name__ == "__main__":
    def tracefunc(frame, event, arg, _indent=[0]):
        if event == 'call':
            filename = frame.f_code.co_filename
            funcname = frame.f_code.co_name
            lineno = frame.f_code.co_firstlineno
            if 'self' in frame.f_locals:
                try:
                    classinst = frame.f_locals['self']
                    classname = repr(classinst).split()[0].split('(')[0][1:]
                    funcname = '%s.%s' % (classname, funcname)
                except:
                    pass
            here = '%s:%s:%s()' % (filename, lineno, funcname)
            _indent[0] += 1
            tracefd.write('%4s %s%s\n' % (_indent[0], ' ' * _indent[0], here))
            tracefd.flush()
        elif event == 'return':
            _indent[0] -= 1

        return tracefunc

    if len(sys.argv) >= 2 and sys.argv[1] == '--force-fs':
        config.START_FULLSCREEN_X = 1
        
    if len(sys.argv) >= 2 and sys.argv[1] == '--trace':
        tracefd = open(os.path.join(os.environ['FREEVO_STARTDIR'],
                                    'trace.txt'), 'w')
        sys.settrace(tracefunc)

    if len(sys.argv) >= 2 and sys.argv[1] == '--doc':
        import pydoc
        import re
        sys.path.append('src/gui')
        for file in util.match_files_recursively('src/', ['py', ]):
            # doesn't work for everything :-(
            if file not in ( 'src/tv/record_server.py', ) and file.find('src/www'):
                file = re.sub('/', '.', file)
                pydoc.writedoc(file[4:-3])
        # now copy the files to Docs/api
        try:
            os.mkdir('Docs/api')
        except:
            pass
        for file in util.match_files('.', ['html', ]):
            print 'moving %s' % file
            os.rename(file, 'Docs/api/%s' % file)
        shutdown(allow_sys_shutdown=0)

    import mmpython
    mmcache = '%s/mmpython' % config.FREEVO_CACHEDIR
    if not os.path.isdir(mmcache):
        os.mkdir(mmcache)
    mmpython.use_cache(mmcache)
    mmpython.mediainfo.DEBUG = DEBUG
    mmpython.factory.DEBUG = DEBUG

    if not os.path.isfile(os.path.join(mmcache, 'VERSION')):
        print '\nWARNING: no pre-cached data'
        print 'Freevo will cache each directory when you first enter it. This can'
        print 'be slow. Start "./freevo cache" to pre-cache all directories to speed'
        print 'up usage of freevo'
        print
    try:
        main_func()
    except KeyboardInterrupt:
        print 'Shutdown by keyboard interrupt'
        # Shutdown the application
        shutdown(allow_sys_shutdown=0)

    except:
        print 'Crash!'
        try:
            tb = sys.exc_info()[2]
            fname, lineno, funcname, text = traceback.extract_tb(tb)[-1]
            
            for i in range(1, 0, -1):
                osd.clearscreen(color=osd.COL_BLACK)
                osd.drawstring('Freevo crashed!', 70, 70,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring('Filename: %s' % fname, 70, 130,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring('Lineno: %s' % lineno, 70, 160,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring('Function: %s' % funcname, 70, 190,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring('Text: %s' % text, 70, 220,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring('Please see the logfiles for more info', 70, 280,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                
                osd.drawstring('Exit in %s seconds' % i, 70, 340,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.update()
                time.sleep(1)
                
        except:
            pass
        traceback.print_exc()

        # Shutdown the application, but not the system even if that is
        # enabled
        shutdown(allow_sys_shutdown=0)
