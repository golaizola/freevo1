#if 0 /*
# -----------------------------------------------------------------------
# web_types.py - Classes useful for the web interface.
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.9  2003/07/14 19:30:36  rshortt
# Library update from Mike Ruelle.  Now you can view other media types and
# download as well.
#
# Revision 1.8  2003/05/29 23:13:26  rshortt
# The guide looked wierd squished to the right, but now I'm not sure if I like
# it taking up the entire width either.
#
# Revision 1.7  2003/05/25 21:40:53  outlyer
# Round edges for the toolbar.
#
# Revision 1.6  2003/05/23 01:09:24  rshortt
# Removing border from the freevo image/link in the header.
#
# Revision 1.5  2003/05/22 21:33:23  outlyer
# Lots of cosmetic changes:
#
# o Moved the header/logo into web_types
# o Made the error messages all use <h4> instead of <h2> so they look the same
# o Removed most <hr> tags since they don't really mesh well with the light blue
# o Moved the title into the "status bar" under the logo
#
# Revision 1.4  2003/05/20 16:15:37  rshortt
# Fixes for IE authentication and to get it to read the javascript.
#
# Revision 1.3  2003/05/12 23:34:53  rshortt
# Added index link.
#
# Revision 1.2  2003/05/12 23:02:41  rshortt
# Adding HTTP BASIC Authentication.  In order to use you must override WWW_USERS
# in local_conf.py.  This does not work for directories yet.
#
# Revision 1.1  2003/05/11 23:04:04  rshortt
# Classes used by the web interface.
#
#
#
# -----------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2003 Krister Lagerstrom, et al. 
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

import os, sys, time

import config

from twisted.web.woven import page
from twisted.web.resource import Resource

DEBUG = 1
TRUE = 1
FALSE = 0


class FreevoPage(page.Page):
    
    def __init__(self, model=None, template=None):

        if not model:
            model = {'foo': 'bar'}
        if not template:
            template = '<html><head><title>ERROR</title></head>' + \
                       '<body>ERROR: no template</body></html>'

        page.Page.__init__(self, model, template=template)

        self.addSlash = 0


class FreevoResource(Resource):

    def render(self, request):
        username = request.getUser()
        password = request.getPassword()

        if not self.auth_user(username, password):
            request.setResponseCode(401, 'Authentication needed')
            # request.setHeader('Connection', 'close')
            request.setHeader('WWW-Authenticate', 'Basic realm="unknown"')
            request.setHeader('Content-Length', str(len('401: = Authorization needed.')))
            request.setHeader('Content-Type', 'text/html')
            return '<h1>401 Authentication required</h1>'
        else:
            return self._render(request)


    def auth_user(self, username, password):
        realpass = config.WWW_USERS.get(username)
        if password == realpass:
            return TRUE
        else:
            return FALSE


class HTMLResource:

    def __init__(self):
        self.res = ''


    def printContentType(self, content_type='text/html'):
        self.res += 'Content-type: %s\n\n' % content_type


    def printHeader(self, title='unknown page', style=None, script=None):
        self.res += '<html>\n\t<head>\n'
        self.res += '<title>Freevo | '+title+'</title>\n'
        if style != None:
            self.res += '<link rel="stylesheet" href="styles/main.css" type="text/css" />\n'
        if script != None:
            self.res += '<script language="JavaScript" src="'+script+'"></script>\n'
        self.res += '</head>\n'
        self.res += '\n\n\n\n<body>\n'
        # Header
        self.res += '<!-- Header Logo and Status Line -->'
        self.tableOpen('width="100%" border="0" cellspacing="0" cellpadding="0" background="images/headerbg.png"')
        self.tableRowOpen()
        self.tableCell('<a target="_new" href="http://freevo.sf.net/"><img src="images/headerfreevo.png" width="313" height="101" border="0"/></a>')
        self.tableRowClose()
        self.tableClose()
        self.tableOpen('width="100%" border="0" cellspacing="0" cellpadding="0" background="images/headertxtbg.png"')
        self.tableRowOpen()
        self.tableCell('<center>' + title + '</center>','height=22')
        self.tableRowClose()
        self.tableClose()
        self.res += '<!-- Main Content -->'
        self.res+=('<br />')



    def tableOpen(self, opts=''):
        self.res += "<table "+opts+">\n"


    def tableClose(self):
        self.res += "</table>\n"


    def tableRowOpen(self, opts=''):
        self.res += "  <tr "+opts+">\n"


    def tableRowClose(self):
        self.res += "  </tr>\n"


    def tableCell(self, data='', opts=''):
        self.res += "    <td "+opts+">"+data+"</td>\n"


    def formValue(self, form=None, key=None):
        if not form or not key:
            return None

        try: 
            val = form[key][0]
        except: 
            val = None
    
        return val


    def printFooter(self):
        # self.res += '</ul>\n'
        self.res += "</body></html>\n"
    
    
    def printSearchForm(self):
        self.res += """
    <form name="SearchForm" action="search.rpy" METHOD="GET">
    <table>
      <tr>
        <td><font color="white"><b>Search:</b></font>&nbsp;</td>
        <td><input type="text" name="find" size="20" onBlur="document.SearchForm.submit()" /></td>
      </tr>
    </table>
    </form>
    """
    
    
    def printLinks(self):
        self.res += """
    <center>
    <table border="0" cellpadding="0" cellspacing="0">
      <tr>
        <td height="24" width="11" background="images/round_left.png">&nbsp;</td>
        <td class="tablelink" onClick="document.location=\'index.rpy\'">&nbsp;&nbsp;Home&nbsp;&nbsp;</td>
        <td class="tablelink" onClick="document.location=\'guide.rpy\'">&nbsp;&nbsp;TV Guide&nbsp;&nbsp;</td>
        <td class="tablelink" onClick="document.location=\'record.rpy\'">&nbsp;&nbsp;Scheduled Recordings&nbsp;&nbsp;</td>
        <td class="tablelink" onClick="document.location=\'favorites.rpy\'">&nbsp;&nbsp;Favorites&nbsp;&nbsp;</td>
        <td class="tablelink" onClick="document.location=\'library.rpy\'">&nbsp;&nbsp;Media Library&nbsp;&nbsp;</td>
        <td class="tablelink" onClick="document.location=\'manualrecord.rpy\'">&nbsp;&nbsp;Manually Record&nbsp;&nbsp;</td>
	<td height="24" width="11" background="images/round_right.png" cellpadding=0 cellspacing=0>&nbsp;</td>
      </tr>
    </table>
    </center>
    """

