# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# file_ops.py - Small file operations (currently only delete)
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
logger = logging.getLogger("freevo.plugins.file_ops")


import os
import config
import plugin
import util

import dialog
from dialog.dialogs import ProgressDialog
from skin.widgets import TextEntryScreen
from gui.AlertBox import AlertBox

class PluginInterface(plugin.ItemPlugin):
    """
    small plugin to delete files
    """
    def config(self):
        return [ ('FILE_OPS_ALLOW_DELETE_IMAGE', True,
                  'Add delete image to the menu.'),
                 ('FILE_OPS_ALLOW_DELETE_EDL', True,
                  'Add delete edl to the menu.'),
                 ('FILE_OPS_ALLOW_DELETE_INFO', True,
                  'Add delete info to the menu.') ]


    def actions(self, item):
        """
        create list of possible actions
        """
        if not item.parent or not item.parent.type == 'dir':
            # only activate this for directory listings
            return []

        self.item = item

        items = []

        if hasattr(item, 'files') and item.files:
            if item.files.fxd_file and config.FILE_OPS_ALLOW_DELETE_INFO and \
                    not getattr(item, 'file_ops_no_delete_info', False) and \
                    self.can_delete_info(item.files.fxd_file):
                items.append((self.confirm_info_delete, _('Delete Info'), 'delete_info'))
            if item.files.edl_file and config.FILE_OPS_ALLOW_DELETE_EDL and \
                    not getattr(item, 'file_ops_no_delete_edl', False):
                items.append((self.confirm_edl_delete, _('Delete edl'), 'delete_edl'))
            if item.files.image and config.FILE_OPS_ALLOW_DELETE_IMAGE and \
                    not getattr(item, 'file_ops_no_delete_image', False):
                items.append((self.confirm_image_delete, _('Delete Image'), 'delete_image'))
            if item.files.delete_possible():
                items.append((self.confirm_delete, _('Delete'), 'delete'))
            if item.rename_possible():
                items.append((self.rename_box, _('Rename'), 'rename'))
        return items


    def confirm_delete(self, arg=None, menuw=None):
        self.menuw = menuw
        dialog.show_confirmation(_('Do you wish to delete\n \'%s\'?') % self.item['title'],
                   self.delete_file, proceed_text=_('Delete'))


    def confirm_info_delete(self, arg=None, menuw=None):
        self.menuw = menuw
        dialog.show_confirmation(_('Delete info about\n \'%s\'?') % self.item['title'],
                   self.delete_info, proceed_text=_('Delete info'))


    def confirm_edl_delete(self, arg=None, menuw=None):
        self.menuw = menuw
        dialog.show_confirmation(_('Delete edl about\n \'%s\'?') % self.item['title'],
                   self.delete_edl, proceed_text=_('Delete edl'))


    def confirm_image_delete(self, arg=None, menuw=None):
        self.menuw = menuw
        dialog.show_confirmation(_('Delete image about\n \'%s\'?') % self.item['title'],
                   self.delete_image, proceed_text=_('Delete image'))


    def safe_unlink(self, filename):
        try:
            os.unlink(filename)
        except Exception, why:
            print 'can\'t delete %r: %s' % (filename, why)


    def delete_file(self):
        dialog = ProgressDialog(_('Deleting...'), indeterminate=True)
        dialog.show()
        self.item.files.delete()
        dialog.hide()
        if self.menuw:
            self.menuw.delete_submenu(True, True)


    def delete_info(self):
        self.safe_unlink(self.item.files.image)
        self.safe_unlink(self.item.files.edl_file)
        #now let's handle the fxd file, we will preserve the file if there is a skin definition
        # within and delete nodes but the skin one. Otherwise we will unlink the file
        if vfs.isfile(self.item.files.fxd_file):
            try:
                self.handled = False    
                fxd = util.fxdparser.FXD(self.item.files.fxd_file)
                fxd.set_handler('skin', self.handle_fxd_file)
                fxd.parse()
                if self.handled == False: 
                    self.safe_unlink(self.item.files.fxd_file)
            except:
                logger.warning('fxd file %r corrupt, deleting', self.item.files.fxd_file)
                self.safe_unlink(self.item.files.fxd_file)

        if self.menuw:
            self.menuw.delete_submenu(True, True)


    def can_delete_info(self, fxd_file):
        """
        This methods checks if the fxd file can be deleted, either is a skin fxd
        and has more than a skin node (any info node) or is not a skin fxd at all
        @return:    True if can be deleted, False otherwise
        """
        logger.log(9, 'can_delete_info(fxd_file=%r)', fxd_file)

        # Sanity check, should never really fail this condition
        if vfs.isfile(fxd_file):
            try:
                fxd = util.fxdparser.FXD(fxd_file)
                fxd.parse()
                logger.log(9, '%r chidren nodes in %r, is %r skin fxd', len(fxd.get_children(fxd.get_root_node())), fxd_file, fxd.is_skin_fxd)
                if fxd.is_skin_fxd and len(fxd.get_children(fxd.get_root_node())) == 1:
                    # we only have one child node/element and it is a skin one
                    # we cannot delete this file
                    return False
            except Exception, e:
                logger.warning('fxd file %r corrupt, error=%s', fxd_file, e)
                #self.safe_unlink(fxd_file)

            return True
        # Sanity, should never ever be here, but if the file does not exists, 
        # we should never present user with a menu to delete it.
        return False


    def handle_fxd_file(self, fxd, node):
        """
        This methods checks if the fxd file can be deleted, either is a skin fxd
        and has more than skin node (any info node) or is not a skin fxd at all
        @return:    True if can be deleted, False otherwise
        """
        logger.debug('handle_fxd_file(fxd=%r, node=%r)', fxd, node)
        # we can safely delete the file now, we will rewrite it later on 
        # as the current implementation of the FXD class does not support 
        # manipulation of the data beyond simple node addition
        self.safe_unlink(fxd.filename)
        if node.name != 'skin':
            return
        # create new fxd file, add the node and simply save it
        fxd = util.fxdparser.FXD(fxd.filename)
        fxd.add(node)
        fxd.save()
        self.handled = True


    def delete_edl(self):
        self.safe_unlink(self.item.files.edl_file)
        if self.menuw:
            self.menuw.delete_submenu(True, True)


    def delete_image(self):
        self.safe_unlink(self.item.files.image)
        if self.item.parent:
            self.item.image = self.item.parent.image
        else:
            self.item.image = None
        if self.menuw:
            self.menuw.delete_submenu(True, True)


    def rename_box(self, arg=None, menuw=None):
        """
        shows rename interface
        """
        txt = TextEntryScreen((_('Rename'), self.rename), _('Rename'), self.item['title'])
        txt.show(menuw)


    def rename(self, menuw, newname=''):
        """
        renames the item
        """
        logger.log( 9, 'rename %s to %s', self.item['title'], newname)
        oldname = self.item['title']
        if self.item.rename(newname):
            AlertBox(text=_('Rename %s to %s.') % (oldname, newname)).show()
        else:
            AlertBox(text=_('Rename %s to %s, failed.') % (oldname, newname)).show()
        menuw.delete_menu()
        menuw.refresh()
