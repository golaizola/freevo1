# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# class and helpers for fxd/imdb generation
# -----------------------------------------------------------------------
# Notes: see http://pintje.servebeer.com/fxdimdb.html for documentation,
# Todo:
# - add support making fxds without imdb (or documenting it)
# - webradio support?
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
# -----------------------------------------------------------------------
import logging
logger = logging.getLogger("freevo.util.fxdimdb")


# python has no data hiding, but this is the intended use...
# subroutines completely in lowercase are regarded as more "private" functions
# sub-routines are regarded as public

# based on original implementation by 'den_RDC (rdc@kokosnoot.com)'
__author__           = 'den_RDC (rdc@kokosnoot.com)'
__maintainer__       = 'Maciej Mike Urbaniak'
__maintainer_email__ = 'maciej@urbaniak.org'
__version__          = 'Revision 0.2'
__license__          = 'GPL' 

# Module Imports
import re
import urllib, urllib2, urlparse
import sys
import codecs
import os
import traceback

try:
    import imdb
except:
    logger.error('It seems that you do not have imdbpy installed!')

import config
import util

import kaa.metadata as mmpython

try:
    import freevo.version as version
except:
    import version


IMDB_COPYRIGHT_MSG = "The information data in this file comes from the Internet Movie Database (IMDb). " + \
                     "Please visit http://www.imdb.com for more information.\n"

imdb_ctitle     = '/tmp/imdb-movies.list'
imdb_ctitle_url = 'ftp://ftp.funet.fi/pub/mirrors/ftp.imdb.com/pub/movies.list.gz'
imdb_titles     = None
imdb_info_tags  = ('year', 'genre', 'tagline', 'plot', 'rating', 'runtime', 'mpaa');

# headers for urllib2
txdata    = None
txheaders = {
    'User-Agent': 'freevo %s (%s)' % (version, sys.platform),
    'Accept-Language': 'en-us',
}

#Begin class
class FxdImdb:
    """Class for creating fxd files and fetching imdb information"""

    def __init__(self):
        """Initialise class instance"""

        # these are considered as private variables - don't mess with them unless
        # no other choice is given
        # FYI, the other choice always exists : add a subroutine or ask :)
        self.title = ''    # Full title that will be written to the FXD file
        self.ctitle         = []    # Contains parsed from filename title, and if exist season, episode
        self.id             = None  # IMDB ID of the movie
        self.isdiscset      = False
        self.info           = {}    # Full movie info

        self.image          = None  # full path image filename
        self.image_urls     = []    # possible image url list
        self.image_url      = None  # final image url

        self.fxdfile        = None  # filename, full path, WITHOUT extension

        self.append         = False
        self.device         = None
        self.regexp         = None
        self.mpl_global_opt = None
        self.media_id       = None
        self.file_opts      = []
        self.video          = []
        self.variant        = []
        self.parts          = []

        #initialize self.info
        for t in imdb_info_tags:
            self.info[t] = ""

        #image_url_handler stuff
        self.image_url_handler = {}
        self.image_url_handler['www.impawards.com'] = self.impawards

        self.str2XML = self.fmt_str_xml

    def parseTitle(self, filename, label=False):
        """
        Parse the title
        Return tuple of title, season and episode (if exist)
        """
        logger.debug('parseTitle(filename=%r, label=%r)', filename, label)

        # Special name rule for the encoding server
        m = re.compile('DVD \[([^]]*).*')
        res = m.search(filename)
        if res:
            name = res.group(1)
        else:
            name = filename

        # is this a series with season and episode number?
        # if so we will remember season and episode but will take it off from name
        season  = ''
        episode = ''

        if config.VIDEO_SHOW_REGEXP_MATCH(name):
            show_name = config.VIDEO_SHOW_REGEXP_SPLIT(name)
            if show_name[0] and show_name[1] and show_name[2]:
                name    = show_name[0]
                season  = show_name[1]
                episode = show_name[2]
                logger.debug('name=%s season=%s episode=%s', name, season, episode)
           
        if label:
            for r in config.IMDB_REMOVE_FROM_LABEL:
                try:
                    name = re.sub(r, '', name)
                except Exception, exc:
                    logger.warning('Exception', exc_info=True)
        else:
            for r in config.IMDB_REMOVE_FROM_NAME:
                try:
                    name = re.sub(r, '', name)
                except Exception, exc:
                    logger.warning('Exception', exc_info=True)

        return tuple([name, season, episode])


    def guessImdb(self, filename, label=False):
        """
        Guess possible titles from file name
        Return tuple of title, season and episode (if exist)
        """
        logger.debug('guessImdb(filename=%r, label=%r)', filename, label)
        self.ctitle = self.parseTitle(filename, label)
        return self.searchImdb(self.ctitle[0], self.ctitle[1], self.ctitle[2])

    def searchImdb(self, title, season=None, episode=None):
        """
        Search IMBD for a title
        """

        try:
            # Look up possible movie matches directly at IMDB.
            # NOTE:
            # imdb does support advanced search for titles of the series but unfortunately 
            # imdbpy does not so we have do this the hard way, present the user with a list
            # to choose from. If we could search for a series title directly we'd have a great 
            # propability for a unique hit and thus would not need to present the selection menu.
            # We try to reduce the search result by filtering initial result for tv (mini) series only.
            imdbpy  = imdb.IMDb()
            results = imdbpy.search_movie(title)
            logger.debug('Searched IMDB for %s, found %s items', title, len(results))
            
            # if series we remove all non series objects to narrow down the search results
            if season and episode:
                for item in results[:]:
                    if len(item.keys()) == 0 or  item['kind'] == 'video game' or \
                                                (item['kind'] != 'tv series' and 
                                                 item['kind'] != 'tv mini series'):
                        results.remove(item)
            # else if not series we remove all series objects to narrow down the search results
            else:
                for item in results[:]:
                    if len(item.keys()) == 0 or (item['kind'] == 'video game' or 
                                                 item['kind'] == 'tv series' or 
                                                 item['kind'] == 'tv mini series'):
                        results.remove(item)

        except imdb.IMDbError, error:
            logger.warning('Exception', exc_info=True)
            raise FxdImdb_Error(str(error))

        return results


    def retrieveImdbData(self, id, season=None, episode=None):
        """
        Given IMDB ID retrieves full info about the Title directly from IMDB via HTTP
        using imdbpy.
        """

        try:
            # Get a Movie object with the data about the movie identified by the given movieID.
            self.id = id
            imdbpy  = imdb.IMDb()
            movie   = imdbpy.get_movie(id)

            if not movie:
                logger.warning('It seems that there\'s no movie with MovieId "%s"', arg[0])
                raise FxdImdb_Error('No movie with MovieId "%s"' % arg[0])

            logger.debug('movie title=%r season=%r, episode=%r', movie['title'], season, episode)
            self.ctitle = tuple([movie['title'], season, episode])

            # check if we have a series episode
            if self.ctitle[2] and (movie['kind'] == 'tv series' or movie['kind'] == 'tv mini series'):
                # retrieve episode info
                imdbpy.update(movie, 'taglines')
                imdbpy.update(movie, 'episodes')
                logger.info('Retrieved movie data:\n%s', movie.summary())
                
                episode = movie['episodes'][int(self.ctitle[1])][int(self.ctitle[2])]
                imdbpy.update(episode)
                logger.info('Retrieved episode data:\n%s', episode.summary())

                logger.debug('movie title=%r episode title=%r', movie['title'], episode['title'])
                self.imdb_retrieve_movie_data(movie, episode)
                return episode.movieID
            else:
                imdbpy.update(movie, 'taglines')
                self.imdb_retrieve_movie_data(movie)
                return movie.movieID

        except imdb.IMDbError, error:
            logger.warning('Exception', exc_info=True)
            raise FxdImdb_Error(str(error))


    def retrieveImdbBulkSeriesData(self, id, items):
        """
        Given IMDB ID retrieves full info about the series and episodes 
        directly from IMDB via HTTP using imdbpy. Used by imbdpy helper.
        """

        fxds = []

        try:
            # Get a Movie object with the data about the movie identified by the given movieID.
            imdbpy = imdb.IMDb()
            movie  = imdbpy.get_movie(id)

            if not movie:
                logger.warning('It seems that there\'s no movie with MovieId "%s"', id)
                raise FxdImdb_Error('No movie with MovieId "%s"' % id)

            if (movie['kind'] != 'tv series' and movie['kind'] != 'tv mini series'):
                logger.warning('It seems that supplied MovieId "%s" is not a TV Series ID. Aborting.', id)
                raise FxdImdb_Error('No a TV Series. MovieId "%s"' % id)
                
            imdbpy.update(movie, 'episodes')
            imdbpy.update(movie, 'taglines')

            for item in items:
            
                fxd = FxdImdb()

                try:
                    # parse the name to get title, season and episode numbers
                    fxd.ctitle = fxd.parseTitle(item[2])
                    episode = movie['episodes'][int(fxd.ctitle[1])][int(fxd.ctitle[2])]
                    imdbpy.update(episode)
                    fxd.imdb_retrieve_movie_data(movie, episode)

                except FxdImdb_Error, error:
                    logger.warning('Exception', exc_info=True)
                    return

                video = makeVideo('file', 'f1', os.path.basename(item[0]), device=None)
                fxd.setVideo(video)
                fxd.setFxdFile(os.path.splitext(item[0])[0])

                fxds.append(fxd)

        except imdb.IMDbError, error:
            logger.warning('Exception', exc_info=True)
            raise FxdImdb_Error(str(error))

        return fxds


    def setFxdFile(self, fxdfilename=None, overwrite=False):
        """
        fxdfilename (string, full path)
        Set fxd file to write to, may be omitted, may be an existing file
        (data will be added) unless overwrite = True
        """

        if fxdfilename:
            if vfs.splitext(fxdfilename)[1] == '.fxd':
                self.fxdfile = vfs.splitext(fxdfilename)[0]
            else: self.fxdfile = fxdfilename

        else:
            if self.isdiscset == True:
                self.fxdfile = vfs.join(config.OVERLAY_DIR, 'disc-set', self.getmedia_id(self.device))
            else:
                self.fxdfile = vfs.splitext(file)[0]

        if overwrite == False:
            try:
                vfs.open(self.fxdfile + '.fxd')
                self.append = True
            except:
                pass
        else:
            self.append = False

        # XXX: add this back in without using parseMovieFile
        # if self.append == True and parseMovieFile(self.fxdfile + '.fxd', None, []) == []:
        #     raise FxdImdb_XML_Error("FXD file to be updated is invalid, please correct it.")

        if not vfs.isdir(vfs.dirname(self.fxdfile)):
            if vfs.dirname(self.fxdfile):
                os.makedirs(vfs.dirname(self.fxdfile))


    def setVideo(self, *videos, **mplayer_opt):
        """
        videos (tuple (type, id-ref, device, mplayer-opts, file/param) (multiple allowed),
        global_mplayer_opts
        Set media file(s) for fxd
        """
        if self.isdiscset == True:
            raise FxdImdb_XML_Error("<disc-set> already used, can't use both "+
                                    "<movie> and <disc-set>")

        if videos:
            for video in videos:
                self.video += [ video ]
        if mplayer_opt and 'mplayer_opt' in mpl_global_opt:
            self.mpl_global_opt = mplayer_opt['mplayer_opt']


    def setVariants(self, *parts, **mplayer_opt):
        """
        variants/parts (tuple (name, ref, mpl_opts, sub, s_dev, audio, a_dev)),
        var_mplayer_opts
        Set Variants & parts
        """
        if self.isdiscset == True:
            raise FxdImdb_XML_Error("<disc-set> already used, can't use both "+
                                    "<movie> and <disc-set>")

        if mplayer_opt and 'mplayer_opt' in mpl_global_opt:
            self.varmpl_opt = (mplayer_opt['mplayer_opt'])
        for part in parts:
            self.variant += [ part ]


    def writeFxd(self):
        """Write fxd file"""
        #if fxdfile is empty, set it yourself
        if not self.fxdfile:
            self.setFxdFile()

        try:
            self.fetch_image()
            #should we write a disc-set ?
            self.fxd_write(self.fxdfile)

            #check fxd
            # XXX: add this back in without using parseMovieFile
            # if parseMovieFile(self.fxdfile + '.fxd', None, []) == []:
            #     raise FxdImdb_XML_Error("""FXD file generated is invalid, please "+
            #                             "post bugreport, tracebacks and fxd file.""")

        except (IOError, FxdImdb_IO_Error), error:
            raise FxdImdb_IO_Error('error saving the file: %s' % str(error))


    def setDiscset(self, device, regexp, *file_opts, **mpl_global_opt):
        """
        device (string), regexp (string), file_opts (tuple (mplayer-opts,file)),
        mpl_global_opt (string)
        Set media is dvd/vcd,
        """
        if len(self.video) != 0 or len(self.variant) != 0:
            raise FxdImdb_XML_Error("<movie> already used, can't use both "+
                                    "<movie> and <disc-set>")

        self.isdiscset = True
        if (not device and not regexp) or (device and regexp):
            raise FxdImdb_XML_Error("Can't use both media-id and regexp")

        self.device = device
        self.regexp = regexp

        for opts in file_opts:
            self.file_opts += [ opts ]

        if mpl_global_opt and 'mplayer_opt' in mpl_global_opt:
            self.mpl_global_opt = (mpl_global_opt['mplayer_opt'])


    def isDiscset(self):
        """
        Check if fxd file describes a disc-set, returns 1 for True, 0 for false
        None for invalid file
        """
        
        try:
            file = vfs.open(self.fxdfile + '.fxd')
        except IOError:
            return None

        content = file.read()
        file.close()
        if content.find('</disc-set>') != -1:
            return 1
        return 0


#------ private functions below .....

    def imdb_retrieve_movie_data(self, movie, episode=None):
        """
        Retrives all movie data (including Episode's if TV Series)
        """
        self.title = self.get_title(movie, episode)
        self.info['genre'] = self.get_genre(movie)
        self.info['tagline'] = self.get_tagline(movie)
        self.info['year'] = self.get_year(movie, episode)
        self.info['rating'] = self.get_rating(movie, episode)
        self.info['plot'] = self.get_plot(movie, episode)
        self.info['mpaa'] = self.get_mpaa(movie)

        if config.IMDB_USE_IMDB_RUNTIME:
            self.info['runtime'] = self.get_runtimes(movie, episode)

        # try to retrieve movie poster urls, first from impawards.com, then from IMDB
        self.impawardsimages(movie['title'], self.info['year'], episode)

        if movie.has_key('full-size cover url'):
            self.image_urls += [ movie['full-size cover url'] ]


    def get_tagline(self, movie):
        """
        Returns first tagline of the movie
        """
        if movie.has_key('taglines'):
            return movie.get('taglines')[0]

        return ''


    def get_genre(self, movie):
        """
        Returns concatenated string of movie genres
        """
        if movie.has_key('genres'):
            return '%s' % ' '.join(movie.get('genres'))

        return ''
    

    def get_title(self, movie, episode):
        """
        Builds a movie/episode title
        """
        if episode and episode.has_key('title'):
            ep = config.IMDB_SEASON_EPISODE_FORMAT % (int(self.ctitle[1]), int(self.ctitle[2]))
            return '%s %s %s' % (movie['title'], ep, episode['title'])
      
        return movie.get('title')


    def get_year(self, movie, episode):
        """
        Returns the year of the movie or the original air date of the series episode
        """
        if episode and episode.has_key('original air date'):
            return episode['original air date']
        
        return movie.get('year')


    def get_mpaa(self, movie):
        """
        Retrieves MPAA rating or formatted certificate data
        """
        if movie.has_key('mpaa'):
            #If it exists, this key from imdbpy is the best way to get MPAA movie rating
            #rating_match = re.search(r"Rated (?P<rating>[a-zA-Z0-9-]+)", movie['mpaa'])
            #if rating_match:
            #    rating = rating_match.group('rating')
            #    return rating
            return movie['mpaa']
            
        if movie.has_key('certificates'):
            #IMDB lists all the certifications a movie has gotten the world over.
            #Each movie often has multiple certifications per country since it
            #will often get re-rated for different releases (theater and
            #then DVD for example).
 
            #for movies with multiple certificates, we pick the 'lowest' one since
            #MPAA ratings are more permissive the more recent they were given.
            #A movie that was rated R in the 70s may be rated PG-13 now but will
            #probably never be rerated NC-17 .
            ratings_list_ordered = config.IMDB_MPAA_RATINGS
            ratings_list_extinfo = config.IMDB_MPAA_EXTINFO
            ratings_mappings     = config.IMDB_MPAA_RATEMAP 
            
            certs = movie['certificates']
            good_ratings = []
            for cert in certs:
                if 'usa' in cert.lower():
                    rating_match = re.match(r"USA:(?P<rating>[ a-zA-Z0-9-]+)", cert)
                    if rating_match:
                        rating = rating_match.group('rating')
                        if rating in ratings_list_ordered:
                            index = ratings_list_ordered.index(rating)
                            if index not in good_ratings:
                                good_ratings.append(index)
                        elif rating in ratings_mappings:
                            index = ratings_list_ordered.index(ratings_mappings[rating])
                            if index not in good_ratings:
                                good_ratings.append(index)

            if good_ratings:
                best_rating = ratings_list_ordered[min(good_ratings)]
                best_rating_extinfo = ratings_list_extinfo[min(good_ratings)]
                return '%s (%s)' % (best_rating, best_rating_extinfo)

        return 'MPAA or Certification information not available'


    def get_runtimes(self, movie, episode=None):
        """
        Returns a formatted string listing all runtimes 
        """
        runtimes = []

        if episode and episode.has_key('runtimes'):
            runtimes = episode['runtimes']

        elif movie.has_key('runtimes'):
            runtimes = movie['runtimes']

        times = []
        for runtime in runtimes:
            try:
                #imdbpy usually returns a runtime with no country or notes, so we'll catch that instance
                time = int(runtime)
                times.append('%s min' % time)
            except ValueError:
                splitted = [x for x in runtime.split(":") if x != '']
                val = None
                notes = None
                country = None
                for split in splitted:
                    try:
                        time = int(split)
                        continue
                    except:
                        if split[0] == "(" and split[-1] == ")":
                            notes = split[1:-1]
                            continue
                        if re.match("\w+", split):
                            country = split
                if country and notes:
                    val = '%s: %s min (%s)' % (country, time, notes)
                elif country:
                    val = '%s: %s min' % (country, time)
                elif notes:
                    val = '%s min (%s)' % (time, notes)
                else:
                    val = '%s min' % (time)

                times.append(val)
 
        return ', '.join(times)


    def get_rating(self, movie, episode=None):
        """ 
        Retrieves user ratings for given movie or if available, for individual episodes
        """
        if episode and (episode.has_key('rating') and episode.has_key('votes')):
            return '%s (%s votes)' % (episode['rating'], episode['votes'])
        elif movie.has_key('rating') and movie.has_key('votes'):
            return '%s (%s votes)' % (movie['rating'], movie['votes'])

        return 'Awaiting 5 votes'


    def get_plot(self, movie, episode=None):
        """
        Retrieves the plot or or if not available, plot outline
        """
        # need a hack here to check if plot is a list or a string.
        # this is a buggy implementation of imdbpy as it should always return list.
        if episode and episode.has_key('plot'):
            plot = episode['plot']
        elif movie.has_key('plot'): 
            plot = movie['plot']
        elif movie.has_key('plot outline'):
            plot = movie['plot outline']
        else: 
            return ''
        
        if isinstance(plot, list):
            return plot[0].split("::")[0]
        else:
            return plot.split("::")[0]


    def fxd_write(self, fxdfile):
        """
        Create or update fxd file for a disc set
        """
        try:
            fxd = util.fxdparser.FXD(fxdfile +'.fxd')
            fxd.set_handler('copyright', self.fxd_set_copyright, 'w', True)
            if self.isdiscset:
                fxd.set_handler('disc-set', self.fxd_set_discset, 'w', True)
            else:
                fxd.set_handler('movie', self.fxd_set_movie, 'w', True)

            fxd.save()
            util.touch(os.path.join(config.FREEVO_CACHEDIR, 'freevo-rebuild-database'))
        
        except (Exception) as error:
            logger.error('Error creating/updating fxd file ' + fxdfile + '.fxd, skipping. Error=\'%s\'', error)

        # now we need to rebuild the cache
        util.touch(os.path.join(config.FREEVO_CACHEDIR, 'freevo-rebuild-database'))


    def fxd_set_copyright(self, fxd, node):
        """return info part for FXD writing"""
        logger.log(9, 'fxd_set_copyright(fxd=%r, node=%r)', fxd, node)
        try:
            fxd.setcdata(node, IMDB_COPYRIGHT_MSG)
            if self.id:
                self.fxd_del_node(node, 'source')
                fxd.add(fxd.XMLnode('source', [('url', 'http://www.imdb.com/title/tt%s' % self.id)]), node)
            
        except (Exception) as error:
            logger.warning('Error creating <copyright> node, skipping this node. Error=\'%s\'', error)

        return node


    def fxd_set_movie(self, fxd, node):
        """
        Build <movie> node
        """
        logger.log(9, 'fxd_set_movie(fxd=%r, node=%r)', fxd, node)
        try:
            # check if title is set, if not or title <> self.title we add/update it
            self.fxd_set_attr(fxd, node, 'title', self.title)

            # check if image is set, if not or <> self.image we add/update it
            if self.image:
                img  = fxd.get_or_create_child(node, 'cover-img')
                self.fxd_set_attr(fxd, img, 'source', self.image_url)

            self.fxd_set_video(fxd, node)
            self.fxd_set_variants(fxd, node)
            self.fxd_set_info(fxd, node)

        except (Exception) as error:
            logger.warning('Error creating <movie> node, skipping this node. Error=\'%s\'', error)
             
        return node


    def fxd_set_discset(self, fxd, node):
        """
        Build <discset> node
        """
        logger.log(9, 'fxd_set_discset(fxd=%r, node=%r)', fxd, node)
        try:
            # check if title is set, if not or title <> self.title we add/update it
            self.fxd_set_attr(fxd, node, 'title', self.title)

            # check if image is set, if not or <> self.image we add/update it
            if self.image:
                img  = fxd.get_or_create_child(node, 'cover-img')
                self.fxd_set_attr(fxd, img, 'source', self.image_url)
           
            self.fxd_set_disc(fxd, node)
            self.fxd_set_info(fxd, node)

        except (Exception) as error:
            logger.warning('Error creating <discset> node, skipping this node. Error=\'%s\'', error)
             
        return node


    def fxd_set_video(self, fxd, parent=None):
        """
        Build <video> node
        """
        logger.log(9, 'fxd_set_video(fxd=%r, parent=%r)', fxd, parent)
        node = None

        try:
            if not self.append:
                self.fxd_del_node(parent, 'video')
            node = fxd.get_or_create_child(parent, 'video')
                
            if self.mpl_global_opt:
                self.fxd_set_attr(fxd, node, 'mplayer-options', self.mpl_global_opt)

            for vid in self.video:
                type, idref, device, mpl_opts, fname = vid

                n_type = fxd.get_or_create_child(node, self.fmt_str_xml(type))
                self.fxd_set_attr(fxd, n_type, 'id', idref)
                fxd.setcdata(n_type, self.fmt_str_xml(fname))
               
                if device:
                    self.fxd_set_attr(fxd, n_type, 'media-id', self.getmedia_id(device))
                if mpl_opts:
                    self.fxd_set_attr(fxd, n_type, 'mplayer-options', mpl_opts)

        except (Exception) as error:
            logger.warning('Error creating <video> node, skipping this node. Error=\'%s\'', error)
            
        return node


    def fxd_set_disc(self, fxd, parent=None):
        """
        Build <disc> node
        """
        logger.log(9, 'fxd_set_disc(fxd=%r, parent=%r)', fxd, parent)
        node = None

        try:
            if not self.append:
                self.fxd_del_node(parent, 'disc')
            node = fxd.get_or_create_child(parent, 'disc')

            if self.device:
                self.fxd_set_attr(fxd, node, 'media-id',        self.getmedia_id(device))
            if self.mpl_global_opts:
                self.fxd_set_attr(fxd, node, 'mplayer-options', self.mpl_global_opts)
            if self.regexp:
                self.fxd_set_attr(fxd, node, 'label-regexp',    self.self.regexp)

            if self.file_opts:
                if not self.append:
                    self.fxd_del_node(node, 'file-opt', all=True)
                for opts in self.file_opts:
                    mplopts, fname = opts
                    node = fxd.get_or_create_child(parent, 'file-opt')
                    self.fxd_set_attr(fxd, node, 'mplayer-options', mplopts)
                    fxd.setcdata(node, fname)
                    
        except (Exception) as error:
            logger.warning('Error creating <disc> node, skipping this node. Error=\'%s\'', error)
            
        return node


    def fxd_set_variants(self, fxd, parent=None, overwrite=True):
        """
        Build <variants> node
        """
        logger.log(9, 'fxd_set_variants(fxd=%r, parent=%r)', fxd, parent)
        node = None

        # node <variants>
        if len(self.variant) != 0:
            try:
                if not self.append:
                    self.fxd_del_node(parent, 'variants')
                node = fxd.get_or_create_child(parent, 'variants')

                for x in range(len(self.variant)):
                    name, idref, mpl_opts, sub, s_dev, audio, a_dev = self.variant[x]

                    # subnode <variant>
                    variant = fxd.get_or_create_child(node, 'variant')
                    self.fxd_set_attr(fxd, variant, 'name', name)
                    if self.varmpl_opt:
                        self.fxd_set_attr(fxd, variant, 'mplayer-options', self.varmpl_opt)

                    #     subnode <part>
                    n_part = fxd.get_or_create_child(variant, 'part')
                    self.fxd_set_attr(fxd, n_part, 'ref', idref)
                    if mpl_opts: 
                        self.fxd_set_attr(fxd, n_part, 'mplayer-options', mpl_opts)

                    #         subnode <subtitle>
                    if sub: 
                        n_sub = fxd.get_or_create_child(part, 'subtitle')
                        if s_dev: 
                            self.fxd_set_attr(fxd, n_sub, 'media-id', self.getmedia_id(s_dev))
                        fxd.setcdata(n_sub, sub)
                    #         subnode </subtitle>
                    #         subnode <audio>
                    if audio:
                        n_audio = fxd.get_or_create_child(part, 'audio')
                        if a_dev: 
                            self.fxd_set_attr(fxd, n_audio, 'media-id', self.getmedia_id(a_dev))
                        fxd.setcdata(n_audio, audio)

                    #        subnode </audio>
                    #     subnode </part>
                    # subnode </variant>
            except (Exception) as error:
                logger.warning('Error creating <variants> node, skipping this node. Error=\'%s\'', error)

        return node


    def fxd_set_info(self, fxd, parent=None, overwrite=True):
        """
        Build <info> node
        """
        logger.log(9, 'fxd_set_info(fxd=%r, parent=%r)', fxd, parent)
        node = None

        try:        
            # self.fxd_del_node(parent, 'info')
            node = fxd.get_or_create_child(parent, 'info')

            if self.info:
                for k in self.info.keys():
                    n_info = fxd.get_or_create_child(node, k)
                    fxd.setcdata(n_info, self.info[k])

        except (Exception) as error:
            logger.warning('Error creating <info> node, skipping this node. Error=\'%s\'', error)

        return node


    def fxd_del_node(self, node, name, all=True):
        """
        Deletes the child 'name' of the node
        """
        try:
            for child in copy.copy(node.children):
                if child.name == name:
                    node.children.remove(child)
                    if not all:
                        return node

        except (Exception) as error:
            logger.warning('Error deleting \'%s\' node. Error=\'%s\'', error)
                          
        return node


    def fxd_set_attr(self, fxd, node, name, val):
        """
        Adds or updates the existing node's attribute
        """
        try:
            val = self.fmt_str_xml(val)
            attr = fxd.getattr(node, name)
            if not attr == val:
                if len(attr):    
                    node.attrs.remove(name) 
                fxd.setattr(node, name, val)

        except (Exception) as error:
            logger.warning('Error deleting \'%s\' node. Error=\'%s\'', error)


    def impawardsimages(self, title, year, series=None):
        """Generate URLs to the impawards movie posters and add them to the
        global image_urls array."""

        # Format of an impawards.com image URL:
        #     http://www.impawards.com/<year>/posters/<title>.jpg
        #
        # Some special characters like: blanks, ticks, ':', ','... have to be replaced
        imp_image_name = title.lower()
        imp_image_name = imp_image_name.replace(u' ', u'_')
        imp_image_name = imp_image_name.replace(u"'", u'')
        imp_image_name = imp_image_name.replace(u':', u'')
        imp_image_name = imp_image_name.replace(u',', u'')
        imp_image_name = imp_image_name.replace(u';', u'')
        imp_image_name = imp_image_name.replace(u'.', u'')

        imp_image_urls = [ ]
        
        if series:
            # build up an array with all kind of image urls
            imp_base_url    = 'http://www.impawards.com/tv/posters'

        else:
            # build up an array with all kind of image urls
            imp_base_url    = 'http://www.impawards.com/%s/posters' % year

        # add the normal poster URL to image_urls
        imp_image_url   = '%s/%s.jpg' % (imp_base_url, imp_image_name)
        imp_image_urls += [ imp_image_url ]

        # add the xxl poster URL to image_urls
        imp_image_url   = '%s/%s_xlg.jpg' % (imp_base_url, imp_image_name)
        imp_image_urls += [ imp_image_url ]

        # add the ver1 poster URL in case no normal version exists
        imp_image_url   = '%s/%s_ver1.jpg' % (imp_base_url, imp_image_name)
        imp_image_urls += [ imp_image_url ]

        # add the xxl ver1 poster URL
        imp_image_url   = '%s/%s_ver1_xlg.jpg' % (imp_base_url, imp_image_name)
        imp_image_urls += [ imp_image_url ]

        # check for valid URLs and add them to self.image_urls
        for imp_image_url in imp_image_urls:

            logger.debug('IMPAWARDS: Checking image URL %s', imp_image_url)
            try:
                imp_req = urllib2.Request(imp_image_url, txdata, txheaders)

                # an url is valid if the returned content-type is 'image/jpeg'
                imp_r     = urllib2.urlopen(imp_req)
                imp_ctype = imp_r.info()['Content-Type']
                imp_r.close()

                logger.debug('IMPAWARDS: Found content-type %s for url %s', imp_ctype, imp_image_url)
                if (imp_ctype == 'image/jpeg'):
                    self.image_urls += [ imp_image_url ]

            except:
                pass


    def impawards(self, host, path):
        """ parser for posters from www.impawards.com. 
            TODO: check for licences of each poster and add all posters
        """

        path = '%s/posters/%s.jpg' % (path[:path.rfind('/')], path[path.rfind('/')+1:path.rfind('.')])
        return [ 'http://%s%s' % (host, path) ]


    def fetch_image(self):
        """Fetch the best image"""
        
        logger.debug('fetch_image=%s', self.image_urls)

        image_len = 0
        if len(self.image_urls) == 0: # No images
            return

        for image in self.image_urls:
            try:
                logger.debug('image=%s', image)
                # get sizes of images
                req = urllib2.Request(image, txdata, txheaders)
                r = urllib2.urlopen(req)
                length = int(r.info()['Content-Length'])
                r.close()
                if length > image_len:
                    image_len = length
                    self.image_url = image
            except:
                pass
        if not self.image_url:
            print "Image downloading failed"
            return

        self.image = (self.fxdfile + '.jpg')

        req = urllib2.Request(self.image_url, txdata, txheaders)
        r = urllib2.urlopen(req)
        i = vfs.open(self.image, 'w')
        i.write(r.read())
        i.close()
        r.close()

        # try to crop the image to avoid borders by imdb
        try:
            import kaa.imlib2 as Image
            image = Image.open(filename)
            width, height = image.size
            image.crop((2,2,width-4, height-4)).save(filename)
        except:
            pass

        self.image = vfs.basename(self.image)

        logger.debug('Downloaded cover image from %s', self.image_url)
        print "Freevo knows nothing about the copyright of this image, please go to"
        print "%s to check for more information about private use of this image." % self.image_url


    def fmt_str_xml(self, line):
        """return a valid XML string"""
        try:
            s = Unicode(line)
            # remove leading and trailing spaces
            s = s.strip()
            # remove leading and trailing quotes
            #s = s.strip('\'"')
            # remove quotes
            s = re.sub('"', '', s)

            if s[:5] == u'&#34;':
                s = s[5:]
            if s[-5:] == u'&#34;':
                s = s[:-5]
            if s[:6] == u'&quot;':
                s = s[6:]
            if s[-6:] == u'&quot;':
                s = s[:-6]
            # replace all & to &amp; ...
            s = s.replace(u"&", u"&amp;")
            # ... but this is wrong for &#
            s = s.replace(u"&amp;#", u"&#")

            return s
        except:
            return Unicode(line)


    def getmedia_id(self, drive):
        """drive (device string)
        return a unique identifier for the disc"""

        if not vfs.exists(drive):
            return drive
        (type, id) = mmpython.cdrom.status(drive)
        return id


#--------- Exception class

class Error(Exception):
    """Base class for exceptions in Imdb_Fxd"""
    def __str__(self):
        return self.message
    def __init__(self, message):
        self.message = message

class FxdImdb_Error(Error):
    """used to raise exceptions"""
    pass

class FxdImdb_XML_Error(Error):
    """used to raise exceptions"""
    pass

class FxdImdb_IO_Error(Error):
    """used to raise exceptions"""
    pass

class FxdImdb_Net_Error(Error):
    """used to raise exceptions"""
    pass

#------- Helper functions for creating tuples - these functions are classless

def makeVideo(type, id_ref, file, **values):
    """Create a video tuple"""
    device = mplayer_opt = None
    types = ['dvd', 'file', 'vcd']
    if type == None or id_ref == None or file == None:
        raise FxdImdb_XML_Error("Required values missing for tuple creation")

    if type not in types:
        raise FxdImdb_XML_Error("Invalid type passed to makeVideo")

    if values:
        #print values
        if 'device' in values: device = values['device']
        if 'mplayer_opt' in values: mplayer_opt = values['mplayer_opt']

    file = relative_path(file)
    t = type, id_ref, device, mplayer_opt, file
    return t

def makePart(name, id_ref, **values):
    """Create a part tuple"""
    mplayer_opt = sub = s_dev = audio = a_dev = None

    if id_ref == None or name == None:
        raise FxdImdb_XML_Error("Required values missing for tuple creation")

    if values:
        if 'mplayer_opt' in values: mplayer_opt = values['mplayer_opt']
        if 'sub' in values: sub = values['sub']
        if 's_dev' in values: s_dev = values['s_dev']
        if 'audio' in values: audio = values['audio']
        if 'a_dev' in values: a_dev = values['a_dev']
    if a_dev: audio = relative_path(audio)
    if s_dev: sub = relative_path(sub)
    t = name, id_ref, mplayer_opt, sub, s_dev, audio, a_dev
    return t

def makeFile_opt(mplayer_opt, file):
    """Create a file_opt tuple"""
    if mplayer_opt == None or file == None:
        raise FxdImdb_XML_Error("Required values missing for tuple creation")
    file = relative_path(file)
    t = mplayer_opt, file

    return t

#--------- classless private functions

def relative_path(filename):
    """return the relative path to a mount point for a file on a removable disc"""
    from os.path import isabs, ismount, split, join

    if not isabs(filename) and not ismount(filename): return filename
    drivepaths = []
    for item in config.REMOVABLE_MEDIA:
        drivepaths.append(item.mountdir)
    for path in drivepaths:
        if filename.find(path) != -1:
            head = filename
            tail = ''
            while (head != path):
                x = split(head)
                head = x[0]
                if x[0] == '/' and x[1] == '' : return filename
                elif tail == '': tail = x[1]
                else: tail = join(x[1], tail)

            if head == path: return tail

    return filename


def point_maker(matching):
    return '%s.%s' % (matching.groups()[0], matching.groups()[1])

