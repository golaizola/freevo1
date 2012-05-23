# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# A plugin to obtain detailed weather forecast information
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
#   There are two ways to get the radar map:
#     - parse the link http://www.weather.com/outlook/travel/businesstraveler/map/<zip>?from=LAPmaps&bypassredirect=true
#     - look in the http://cgi.weather.com/looper/archive/ directory for the latest image
#
# Todo:
#   - i18n support
#
# activate:
#
#    plugin.activate('oneclick', level=45)
#    ONECLICK_LOCATIONS = [
#      ("27560", False, "http://image.weather.com/web/radar/us_phl_metroradar_plus_usen.jpg", "Home sweet home"),
#      ("UKXX0054", True),
#    ]
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
logger = logging.getLogger("freevo.plugins.oneclick")

#python modules
import os, stat, re, copy
import sys

# date/time
import time

#regular expression
import re

# rdf modules
import urllib, urllib2

#freevo modules
import config, menu, rc, plugin, skin, osd, util
from gui.PopupBox import PopupBox
from item import Item

from weatherdata import WeatherData

GUI = True
if __name__ == '__main__':
    GUI = False

#get the singletons so we get skin info and access the osd
#skin = skin.get_singleton()
osd = osd.get_singleton()

#check every 1 hour
WEATHER_AGE = 3600
WEATHER_DIR = os.path.join(config.SHARE_DIR, 'images', 'weather')
if os.path.isdir(os.path.join(WEATHER_DIR, config.SKIN_XML_FILE)):
    WEATHER_SKIN_DIR = os.path.join(WEATHER_DIR, config.SKIN_XML_FILE)
else:
    WEATHER_SKIN_DIR = WEATHER_DIR
logger.debug('WEATHER_AGE=%d', WEATHER_AGE)
logger.debug('WEATHER_DIR=%r', WEATHER_DIR)
logger.debug('WEATHER_SKIN_DIR=%r', WEATHER_SKIN_DIR)

#From the Yahoo! weather
WEATHER_ICONS = {
#  icon     image                            fallback            twc.com
     '0': ('tornado.png',                   'thunshowers.png',  'twc/0.png'),
     '1': ('tropical_storm.png',            'thunshowers.png',  'twc/1.png'),
     '2': ('hurricane.png',                 'thunshowers.png',  'twc/2.png'),
     '3': ('severe_thunderstorms.png',      'thunshowers.png',  'twc/3.png'),
     '4': ('thunderstorms.png',             'thunshowers.png',  'twc/4.png'),
     '5': ('mixed_rain_and_snow.png',       'rainsnow.png',     'twc/5.png'),
     '6': ('mixed_rain_and_sleet.png',      'rainsnow.png',     'twc/6.png'),
     '7': ('mixed_snow_and_sleet.png',      'rainsnow.png',     'twc/7.png'),
     '8': ('freezing_drizzle.png',          'rainsnow.png',     'twc/8.png'),
     '9': ('drizzle.png',                   'lshowers.png',     'twc/9.png'),
    '10': ('freezing_rain.png',             'rainsnow.png',     'twc/10.png'),
    '11': ('light_showers.png',             'lshowers.png',     'twc/11.png'),
    '12': ('showers.png',                   'lshowers.png',     'twc/12.png'),
    '13': ('snow_flurries.png',             'flurries.png',     'twc/13.png'),
    '14': ('light_snow_showers.png',        'flurries.png',     'twc/14.png'),
    '15': ('blowing_snow.png',              'flurries.png',     'twc/15.png'),
    '16': ('snow.png',                      'snowshow.png',     'twc/16.png'),
    '17': ('hail.png',                      'showers.png',      'twc/17.png'),
    '18': ('sleet.png',                     'rainsnow.png',     'twc/18.png'),
    '19': ('dust.png',                      'fog.png',          'twc/19.png'),
    '20': ('foggy.png',                     'fog.png',          'twc/20.png'),
    '21': ('haze.png',                      'fog.png',          'twc/21.png'),
    '22': ('smoke.png',                     'fog.png',          'twc/22.png'),
    '23': ('blustery.png',                  'fair.png',         'twc/23.png'),
    '24': ('wind.png',                      'fair.png',         'twc/24.png'),
    '25': ('cold.png',                      'fair.png',         'twc/25.png'),
    '26': ('cloudy.png',                    'cloudy.png',       'twc/26.png'),
    '27': ('mostly_cloudy_night.png',       'mcloudy.png',      'twc/27.png'),
    '28': ('mostly_cloudy_day.png',         'mcloudy.png',      'twc/28.png'),
    '29': ('partly_cloudy_night.png',       'pcloudy.png',      'twc/29.png'),
    '30': ('partly_cloudy_day.png',         'pcloudy.png',      'twc/30.png'),
    '31': ('clear_night.png',               'sunny.png',        'twc/31.png'),
    '32': ('sunny.png',                     'sunny.png',        'twc/32.png'),
    '33': ('fair_night.png',                'fair.png',         'twc/33.png'),
    '34': ('fair_day.png',                  'fair.png',         'twc/34.png'),
    '35': ('mixed_rain_and_hail.png',       'rainsnow.png',     'twc/35.png'),
    '36': ('hot.png',                       'sunny.png',        'twc/36.png'),
    '37': ('isolated_thunderstorms.png',    'thunshowers.png',  'twc/37.png'),
    '38': ('scattered_thunderstorms.png',   'thunshowers.png',  'twc/38.png'),
    '39': ('scattered_showers.png',         'showers.png',      'twc/39.png'),
    '40': ('showers.png',                   'showers.png',      'twc/40.png'),
    '41': ('scattered_snow_showers.png',    'snowshow.png',     'twc/41.png'),
    '42': ('heavy_snow.png',                'snowshow.png',     'twc/42.png'),
    '43': ('heavy_snow.png',                'snowshow.png',     'twc/43.png'),
    '44': ('na.png',                        'unknown.png',      'twc/44.png'),
    '45': ('thundershowers_night.png',      'thunshowers.png',  'twc/45.png'),
    '46': ('scattered_snow_showers_n.png',  'snowshow.png',     'twc/46.png'),
    '47': ('isolated_thundershowers_n.png', 'thunshowers.png',  'twc/47.png'),
    'na': ('na.png',                        'unknown.png',      'twc/na.png'),
}


def wget(url):
    """ get a file from the url """
    logger.log( 9, 'wget(%s)', url)
    txdata = None
    txheaders = {
        'User-Agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.10) Gecko/2009042316 Firefox/3.0.10'
    }
    logger.info('getting url %r...', url)
    req = urllib2.Request(url, txdata, txheaders)
    try:
        t1 = time.time()
        response = urllib2.urlopen(req)
        try:
            data = response.read()
        finally:
            response.close()
            t2 = time.time()
        if response.msg == 'OK':
            return data
        logger.debug('Downloaded "%s" in %.1f seconds', url, t2 - t1)
    except urllib2.HTTPError, why:
        logger.warning('Download of %r failed: %s', url, why)
    except ValueError, why:
        try:
            fd = open(url)
            data = fd.read()
            fd.close()
            return data
        except:
            logger.warning('invalid url %r failed: %s', url, why)
    return None


def toCelcius(fTemp):
    logger.log( 9, 'toCelcius(fTemp)')
    try:
        tTemp = float (fTemp )
    except ValueError:
        tTemp = 0.0
    nTemp = (5.0/9.0)*(tTemp - 32.0)
    return "%d" % (nTemp,)

def toKilometers(miles):
    logger.log( 9, 'toKilometers(miles)')
    try:
        tTemp = float(miles)
    except ValueError:
        tTemp = 0.0
    nTemp = tTemp*1.6
    return "%d" % (int(nTemp),)

def toBarometer(baro):
    logger.log( 9, 'toBarometer(baro)')
    try:
        tTemp = float(baro)
    except ValueError:
        tTemp = 0.0
    nTemp = tTemp*3.386
    return "%.1f" % (nTemp,)


class PluginInterface(plugin.MainMenuPlugin):
    """
    A plugin to obtain more detailed weather forecast information

    To activate, put the following lines in local_conf.py:

    | plugin.activate('oneclick', level=45)
    | ONECLICK_LOCATIONS = [
    |   ("<loc>", [metric], [mapuri], [location name]),
    |   ("<loc>", [metric], [mapuri], [location name]),
    | ...
    | ]

    where:
    <loc> is a zipcode or an airport code
    [metric] (1 == convert to SI Units; 0 == do not convert)
    [mapuri] is the map's url, doesn't parse the page for a map url
    [location name] is a custom name you wish to use for this location
    """

    def __init__(self):
        """
        """
        logger.log( 9, 'PluginInterface.__init__()')
        if not config.SYS_USE_NETWORK:
            self.reason = 'SYS_USE_NETWORK not enabled'
            return
        if not config.ONECLICK_LOCATIONS:
            self.reason = 'ONECLICK_LOCATIONS not defined'
            return
        plugin.MainMenuPlugin.__init__(self)

    def config(self):
        """
        """
        logger.log( 9, 'config()')
        return [
            ('ONECLICK_LOCATIONS', None, 'Location codes for current conditions and forecasts'),
            ('ONECLICK_URL_CURC', 'http://ff.1click.weather.com/weather/local/%s?cc=*%s', 'Current Conditions URL'),
            ('ONECLICK_URL_DAYF', 'http://ff.1click.weather.com/weather/local/%s?dayf=5%s', 'Day Forecast URL'),
            ('ONECLICK_URL_ELOC', 'http://ff.1click.weather.com/weather/local/%s?eloc=st', 'Extended Location URL'),
            ('ONECLICK_URL_MAP',  'http://www.weather.com/weather/map/%s?from=LAPmaps&bypassredirect=true', 'Radar Map URL')
        ]

    def items(self, parent):
        """
        """
        logger.log( 9, 'items(self, parent)')
        return [ WeatherMainMenu(parent) ]


class WeatherItem(Item):
    """
    Item for the menu for one feed
    """
    def __init__(self, parent, location):
        logger.log( 9, 'WeatherItem.__init__(parent=%r, location=%r)', parent, location)
        Item.__init__(self, parent)

        self.parent = parent

        # Flag to indicate whether this item is able to be displayed
        self.error = 0

        self.location = None
        self.ismetric = False
        self.name = None
        self.city = None
        self.state = None
        self.tm = None
        self.latitude = None
        self.longitude = None
        self.sunrise = None
        self.sunset = None

        self.unit_t = None
        self.unit_d = None
        self.unit_s = None
        self.unit_p = None
        self.unit_r = None
        self.country = None

        self.updated = 0.0
        self.observation_station = None
        self.temperature = None
        self.feeling = None
        self.current_conditions = None
        self.day_icon = None
        self.pressure = None
        self.pressure_change = None
        self.wind_speed = None
        self.wind_direction = None
        self.humidity = None
        self.visibility = None
        self.uv_index = None
        self.uv_type = None
        self.dew_point = None
        self.moon_icon = None
        self.moon_phase = None

        self.description = None
        self.forecastData = None
        self.pastTime = 0
        self.date = []
        self.weatherIcon = []
        self.lowTemp = []
        self.highTemp = []
        self.ppcp = []
        self.hmid = []
        self.weatherType = []
        self.wdata = []
        self.popupParam = None
        self.mapuri = None

        if isinstance(location, tuple):
            self.location = location[0]
            if len(location) > 1 and location[1]:
                self.ismetric = bool(location[1])
            if len(location) > 2 and location[2]:
                self.mapuri = str(location[2])
            if len(location) > 3 and location[3]:
                self.name = Unicode(location[3])
        else:
            self.location = location
            self.ismetric = False

        self.popupParam = self.location
        if self.name:
            self.popupParam = self.name

        self.units = self.ismetric and '&unit=m' or ''
        self.url_curc = config.ONECLICK_URL_CURC % (urllib.quote(self.location), self.units)
        self.url_dayf = config.ONECLICK_URL_DAYF % (urllib.quote(self.location), self.units)
        self.url_eloc = config.ONECLICK_URL_ELOC % (urllib.quote(self.location))
        self.mapurl = config.ONECLICK_URL_MAP % (self.location,)
        self.weatherData = None
        self.weatherMapData = None

        self.cacheDir = '%s/weather_%s' % (config.FREEVO_CACHEDIR, self.location)
        self.cacheElocation = '%s/location.pickle' % (self.cacheDir)
        self.cacheCurrent = '%s/current.pickle' % (self.cacheDir)
        self.cacheForecast = '%s/forecast.pickle' % (self.cacheDir)
        self.mapFile = '%s/map.jpeg' % (self.cacheDir)
        self.mapPage = '%s/mappage.html' % (self.cacheDir)
        if not os.path.isdir(self.cacheDir):
            os.mkdir(self.cacheDir, stat.S_IMODE(os.stat(config.FREEVO_CACHEDIR)[stat.ST_MODE]))
        self.last_update = 0

        #get forecast data
        self.getForecast()

    def getForecast(self, force=0):
        """grab the forecast, updating for the website if needed"""
        logger.log( 9, 'getForecast(force=%s)', force)

        # check cache
        try:
            if force or self.needsRefresh():
                self.updateData()
                self.updateMap()
            else:
                self.loadFromCache()
        except IOError, e:
            self.error = 1
            logger.warning("failed to update data for '%s': %s", self.location, e)
        else:
            # set the last update timestamp
            self.last_update = os.path.getmtime(self.cacheCurrent)

            # now convert the self.weatherData structure to parsable information
            try:
                self.convertWeatherData()
            except Exception, why:
                logger.warning('Failed to convert data for %s: %s', self.location, why)


    def needsRefresh(self):
        """is the cache too old?"""
        logger.log( 9, 'needsRefresh()')
        if (os.path.isfile(self.cacheCurrent) == 0 or \
            (abs(time.time() - os.path.getmtime(self.cacheCurrent)) > WEATHER_AGE)):
            return 1
        else:
            return 0

    def updateData(self):
        """update the cache data from the 1click service
        @note: the elocation is not updated as it is static
        """
        logger.log( 9, 'updateData()')
        if GUI:
            popup = PopupBox(text=_('Fetching Weather for %s...') % self.popupParam)
            popup.show()

        if not os.path.isfile(self.cacheElocation):
            try:
                elocationData = wget(self.url_eloc)
                self.elocationData = elocationData
            except Exception, why:
                logger.warning('Failed to get extended location data for %s: %s', self.location, why)
        else:
            self.elocationData = util.read_pickle(self.cacheElocation)

        try:
            self.currentData = wget(self.url_curc)
            #print 'currentData:', self.currentData
        except Exception, why:
            logger.warning('Failed to get the current conditions data for %s: %s', self.location, why)
            if os.path.isfile(self.cacheCurrent):
                self.currentData = util.read_pickle(self.cacheCurrent)
            else:
                self.currentData = None
        try:
            self.forecastData = wget(self.url_dayf)
            #print 'forecastData:', self.forecastData
        except Exception, why:
            logger.warning('Failed to get the forecast data for %s: %s', self.location, why)
            if os.path.isfile(self.cacheForecast):
                self.forecastData = util.read_pickle(self.cacheForecast)
            else:
                self.forecastData = None

        if GUI:
            popup.destroy()

        if not self.currentData or not self.forecastData:
            # raise an error
            return

        self.saveToCache()
        return


    def updateMap(self):
        """ Update the weather map """
        logger.log( 9, 'updateMap()')
        # obtain radar map
        if self.mapuri:
            try:
                if GUI:
                    popup = PopupBox(text=_('Fetching Radar Map for %s...') % self.popupParam)
                    popup.show()
                try:
                    self.weatherMapData = wget(self.mapuri)
                    self.saveMapToCache()
                except Exception, why:
                    logger.warning('Cannot download the map for "%s" from %s: %s', self.location, self.mapuri, why)

                return
            finally:
                if GUI:
                    popup.destroy()

        try:
            if GUI:
                popup = PopupBox(text=_('Fetching Radar Map for %s...') % self.popupParam)
                popup.show()
            # get the first web page
            weatherPage = wget(self.mapurl)
            if config.DEBUG and weatherPage:
                f = open(self.mapPage, 'w')
                f.write(weatherPage)
                f.close()
            try:
                # find link to map page
                regexp = re.compile('NAME="mapImg"\s*SRC="([^"]*)"', re.IGNORECASE|re.MULTILINE)
                results = regexp.search(weatherPage)
                self.mapuri = results.groups()[0]
                self.weatherMapData = wget(self.mapuri)
                self.saveMapToCache()
                return
            except Exception, why:
                logger.warning('Cannot download the map for "%s" from %s: %s', self.location, self.mapurl, why)

        finally:
            if GUI:
                popup.destroy()

    def saveToCache(self):
        logger.log( 9, 'saveToCache()')
        util.save_pickle(self.elocationData, self.cacheElocation)
        util.save_pickle(self.currentData, self.cacheCurrent)
        util.save_pickle(self.forecastData, self.cacheForecast)

    def saveMapToCache(self):
        """ save weather map to the cache """
        try:
            if self.weatherMapData is not None:
                imgfd = os.open(self.mapFile, os.O_CREAT|os.W_OK)
                os.write(imgfd, self.weatherMapData)
                os.close(imgfd)
        except Exception, why:
            logger.warning('failed saving weather map to cache "%s": %s', self.mapFile, why)

    def loadFromCache(self):
        """ load the data and the map from the cache """
        logger.log( 9, 'loadFromCache()')
        self.elocationData = util.read_pickle(self.cacheElocation)
        self.currentData = util.read_pickle(self.cacheCurrent)
        self.forecastData = util.read_pickle(self.cacheForecast)

        try:
            size = int(os.stat(self.mapFile)[6])
        except Exception, why:
            logger.warning('failed loading weather map for "%s" from cache: %s', self.location, why)
            pass
        else:
            imgfd = os.open(self.mapFile, os.R_OK)
            self.weatherMapData = os.read(imgfd, size)
            os.close(imgfd)

    def actions(self):
        """ return a list of actions for this item """
        logger.log( 9, 'actions()')
        return [ (self.start_detailed_interface, _('Show Weather Details')) ]

    def start_detailed_interface(self, arg=None, menuw=None):
        """ detail handler """
        logger.log( 9, 'start_detailed_interface(arg=%r, menuw=%r)', arg, menuw)
        WeatherDetailHandler(arg, menuw, self)

    def isValid(self):
        """ reports is an error was detected """
        logger.log( 9, 'isValid()')
        return not self.error

    def getLastUpdated(self):
        """ parse the lsup time
        @note: there seems to be a problem with AM/PM not parsing correctly
        """
        logger.log( 9, 'getLastUpdated() "%s"', self.updated)
        if self.zone < 0:
            return '%s  (GMT%s)' % (self.updated, self.zone)
        elif self.zone > 0:
            return '%s  (GMT+%s)' % (self.updated, self.zone)
        else:
            return '%s  (GMT)' % (self.updated)

        #this was a silly idea but the dates are very american
        am = re.compile('(.*) AM.*')
        if am.match(self.updated):
            value = time.strptime(am.match(self.updated).groups()[0], '%m/%d/%y %H:%M')
            return time.strftime("%c", time.localtime(time.mktime(value)))
        else:
            pm = re.compile('(.*) PM.*')
            if pm.match(self.updated):
                value = time.strptime(pm.match(self.updated).groups()[0], '%m/%d/%y %H:%M')
                (year, mon, day, hour, min, sec, weekday, yearday, saving) = value
                value = (year, mon, day, hour+12, min, sec, weekday, yearday, saving)
                return time.strftime("%c", time.localtime(time.mktime(value)))
            else:
                return self.updated.replace(' Local Time', '')

    def getObservationStation(self):
        """ get the observation station """
        logger.log( 9, 'getObservationStation()')
        return "%s" % (self.observation_station)

    def getTemperature(self):
        logger.log( 9, 'getTemperature()')
        return u"%s\xb0%s" % (self.temperature, self.unit_t)

    def getFeeling(self):
        logger.log( 9, 'getFeeling()')
        return u"%s\xb0%s" % (self.feeling, self.unit_t)

    def getCurrentCondition(self):
        """ gets the current conditions """
        logger.log( 9, 'getCurrentCondition()')
        return "%s" % (self.current_conditions)

    def getIcon(self):
        """ gets the current conditions icon """
        logger.log( 9, 'getIcon()')
        return "%s" % (self.day_icon)

    def getPressure(self):
        logger.log( 9, 'getPressure()')
        if self.pressure_change == 'N/A':
            return "%s %s" % (self.pressure, self.unit_p)
        return "%s %s %s %s" % (self.pressure, self.unit_p, _('and'), self.pressure_change)

    def getPressureValue(self):
        logger.log( 9, 'getPressureValue()')
        return "%s %s" % (self.pressure, self.unit_p)

    def getPressureChange(self):
        logger.log( 9, 'getPressureChange()')
        return "%s" % (_(self.pressure_change))

    def getWind(self):
        logger.log( 9, 'getWind()')
        if self.wind_direction == 'CALM':
            return "%s" % (self.wind_speed)
        elif self.wind_direction == 'VAR':
            return "%s %s %s %s" % (_('Variable'), _('at a rate of'), self.wind_speed, self.unit_s)
        return "%s %s %s %s" % (_(self.wind_direction), _('at a rate of'), self.wind_speed, self.unit_s)

    def getWindDir(self):
        logger.log( 9, 'getWindDir()')
        return "%s" % (self.wind_direction)

    def getWindSpeed(self):
        logger.log( 9, 'getWindSpeed()')
        return "%s %s" % (self.wind_speed, self.unit_s)

    def getHumidity(self):
        logger.log( 9, 'getHumidity()')
        return "%s%%" % (self.humidity)

    def getVisibility(self):
        logger.log( 9, 'getVisibility()')
        return "%s %s" % (self.visibility, self.unit_d)

    def getUvIndex(self):
        logger.log( 9, 'getUvIndex()')
        return "%s" % (_(self.uv_index))

    def getUvType(self):
        logger.log( 9, 'getUvType()')
        return "%s" % (_(self.uv_type))

    def getDewPoint(self):
        logger.log( 9, 'getDewPoint()')
        return u"%s\xb0%s" % (self.dew_point, self.unit_t)

    def getMoonIcon(self):
        logger.log( 9, 'getMoonIcon()')
        return "%s" % (self.moon_icon)

    def getMoonPhase(self):
        logger.log( 9, 'getMoonPhase()')
        return "%s" % (_(self.moon_phase))

    def getSunrise(self):
        logger.log( 9, 'getSunrise()')
        return "%s" % (self.sunrise)

    def getSunset(self):
        logger.log( 9, 'getSunset()')
        return "%s" % (self.sunset)


    def convertWeatherData(self):
        """
        convert the xml weather information for the skin
        """
        logger.log( 9, 'convertWeatherData()')
        #print self.elocationData
        #print self.currentData
        #print self.forecastData
        elocation = WeatherData(self.elocationData)
        current = WeatherData(self.currentData)
        forecast = WeatherData(self.forecastData)

        if not self.name:
            self.name = elocation.loc.dnam

        dnam = elocation.loc.dnam.split(', ')
        ctry = elocation.eloc.ctry
        if ctry in ('US'):
            self.city = dnam[0]
            self.state = dnam[1]
            self.country = ctry
        else:
            self.city = dnam[0]
            self.state = ''
            self.country = dnam[1]
        logger.info('city=%s, state=%s, country=%s', self.city, self.state, self.country)

        # reset variables
        self.date = []
        self.weatherIcon = []
        self.lowTemp = []
        self.highTemp = []
        self.ppcp = []
        self.hmid = []
        self.weatherType = []

        self.unit_t = current.head.ut
        self.unit_d = current.head.ud
        self.unit_s = current.head.us
        self.unit_p = current.head.up
        self.unit_r = current.head.ur

        self.tm = current.loc.tm
        self.latitude = current.loc.lat
        self.longitude = current.loc.lon
        self.sunrise = current.loc.sunr
        self.sunset = current.loc.suns
        self.zone = int(current.loc.zone)

        self.updated = current.cc.lsup
        self.observation_station = current.cc.obst
        self.temperature = current.cc.tmp
        self.feeling = current.cc.flik
        self.current_conditions = _(current.cc.t)
        self.day_icon = current.cc.icon
        self.pressure = current.cc.bar.r
        self.pressure_change = current.cc.bar.d
        self.wind_speed = current.cc.wind.s
        self.wind_direction = current.cc.wind.t
        self.humidity = current.cc.hmid
        self.visibility = current.cc.vis
        self.uv_index = current.cc.uv.i
        self.uv_type = current.cc.uv.t
        self.dew_point = current.cc.dewp
        self.moon_icon = current.cc.moon.icon
        self.moon_phase = current.cc.moon.t

        self.description = '%s %s %s' % (self.current_conditions, _("at"), self.getTemperature())
        self.image = self.getDayImage(self.day_icon)

        # skip today in the days
        for day in forecast.dayf.days[1:]:
            self.date.append(day.t)
            self.lowTemp.append(day.low)
            self.highTemp.append(day.hi)
            for part in day.parts:
                if part.p == 'd':
                    self.weatherIcon.append(self.getDayImage(part.icon))
                    self.weatherType.append(part.t)
                    self.ppcp.append(part.ppcp)
                    self.hmid.append(part.hmid)


    def getDayImage(self, num):
        """obtain the weather icons for multiple day forecast"""
        logger.log( 9, 'getDayImage()')

        if not WEATHER_ICONS.has_key(num):
            num = 'na'

        icon = os.path.join(WEATHER_SKIN_DIR, WEATHER_ICONS[num][0])
        if not os.path.isfile(icon):
            icon = os.path.join(WEATHER_SKIN_DIR, WEATHER_ICONS[num][1])
            if not os.path.isfile(icon):
                icon = os.path.join(WEATHER_DIR, WEATHER_ICONS[num][2])
        if not os.path.isfile(icon):
            icon = os.path.join(WEATHER_DIR, WEATHER_ICONS['na'][0])
        logger.debug('%s: %s %s', num, icon, os.path.split(WEATHER_ICONS[num][0])[1])
        return icon


    def getMoonImage(self, num):
        """obtain the weather icons for multiple day forecast"""
        logger.log( 9, 'getMoonImage()')

        icon = os.path.join(WEATHER_DIR, 'moons', '%s.png' % (num))
        logger.info('%s: %s', num, icon)
        return icon


class WeatherMainMenu(Item):
    """
    this is the item for the main menu and creates the list
    of Weather Locations in a submenu.
    """
    def __init__(self, parent):
        logger.log( 9, 'WeatherMainMenu.__init__(parent=%r)', parent)
        Item.__init__(self, parent, skin_type='weather')
        self.parent = parent
        #self.name = _('Weather')

    def actions(self):
        """ return a list of actions for this item """
        logger.log( 9, 'actions()')
        items = [ (self.create_locations_menu , _('Locations')) ]
        return items

    def __call__(self, arg=None, menuw=None):
        """ call first action in the actions list """
        logger.log( 9, '__call__(arg=%r, menuw=%r)', arg, menuw)
        if self.actions():
            return self.actions()[0][0](arg=arg, menuw=menuw)

    def create_locations_menu(self, arg=None, menuw=None):
        """ """
        logger.log( 9, 'create_locations_menu(arg=%r, menuw=%r)', arg, menuw)
        locations = []
        autoselect = 0
        # create menu items
        for location in config.ONECLICK_LOCATIONS:
            weather_item = WeatherItem(self, location)
            # Only display this entry if no errors were found
            if weather_item.isValid():
                locations.append (weather_item)

        # if only 1 valid location, autoselect it and go right to the detail screen
        if locations.__len__() == 1:
            autoselect = 1
            menuw.hide(clear=False)

        # if no locations were found, add a menu entry indicating that
        if not locations:
            nolocation = menu.MenuItem(_('No locations specified'), menuw.back_one_menu, 0)
            locations.append(nolocation)

        # if only 1 valid menu entry present, autoselect it
        if autoselect:
            locations[0](menuw=menuw)
        else:
            # create menu
            weather_site_menu = menu.Menu(_('Locations'), locations, item_types = 'weather')
            menuw.pushmenu(weather_site_menu)
            menuw.refresh()

class WeatherDetailHandler:
    """
    A handler class to display several detailed forecast screens and catch events
    """
    def __init__(self, arg=None, menu=None, weather=None):
        """ """
        logger.log( 9, 'WeatherDetailHandler.__init__(arg=%r, menu=%r, weather=%r)', arg, menu, weather)
        self.arg = arg
        self.menuw = menu
        self.weather = weather
        self.menuw.hide(clear=False)
        rc.add_app(self)

        self.skins = ('day', 'forecast', 'week', 'map')

        self.skin_num = 0
        self.subtitles = (_('Current Conditions'), _('Today\'s Forecast'),
                          _('Extended Forecast'), _('Radar Map'))

        self.title = ''
        self.subtitle = self.getSubtitle(self.skin_num)

        # Fire up splashscreen and load the plugins
        skin.draw('oneclick', self, transition=skin.TRANSITION_IN)

    def prevSkin(self):
        """decrements the skin number round to the last skin"""
        logger.log( 9, 'prevSkin()')
        self.skin_num -= 1

        # out of bounds check, reset to size of skins array
        if self.skin_num < 0:
            self.skin_num = len(self.skins)-1
        self.subtitle = self.getSubtitle(self.skin_num)

    def nextSkin(self):
        """increment the skin number round to the first skin"""
        logger.log( 9, 'nextSkin()')
        self.skin_num += 1

        # out of bounds check, reset to 0
        if self.skin_num >= len(self.skins):
            self.skin_num = 0
        self.subtitle = self.getSubtitle(self.skin_num)

    def getSubtitle(self, num):
        """ returns the subtitle for a skin number """
        logger.log( 9, 'getSubtitle(num=%s)', num)
        return '%s %s %s' % (self.subtitles[num], _('for'), self.weather.name)

    def eventhandler(self, event, menuw=None):
        """eventhandler"""
        logger.log( 9, 'eventhandler(event=%s, menuw=%r)', event, menuw)
        if event == 'MENU_BACK_ONE_MENU':
            rc.remove_app(self)
            self.menuw.show()
            return True

        elif event == 'MENU_SELECT':
            self.weather.getForecast(force=1)
            skin.clear()
            skin.draw('oneclick', self, transition=skin.TRANSITION_IN)
            return True

        elif event in ('MENU_DOWN', 'MENU_RIGHT'):
            self.nextSkin()
            skin.draw('oneclick', self, transition=skin.TRANSITION_PAGE)
            return True

        elif event in ('MENU_UP', 'MENU_LEFT'):
            self.prevSkin()
            skin.draw('oneclick', self, transition=skin.TRANSITION_PAGE)
            return True

        return False


if __name__ == '__main__':
    for location in config.ONECLICK_LOCATIONS:
        print location
        weather_item = WeatherItem(None, location)
        print weather_item
    import sys
    sys.exit(1)


class WeatherBaseScreen(skin.Area):
    """ A base class for weather screens to inherit from, provides common members+methods """
    def __init__(self):
        logger.log( 9, 'WeatherBaseScreen.__init__()')
        skin.Area.__init__(self, 'content')

        # Weather display fonts
        self.key_font = skin.get_font('medium0')
        self.val_font = skin.get_font('medium1')
        self.small_font = skin.get_font('small0')
        self.big_font = skin.get_font('huge0')

        # set the multiplier to be used in all screen drawing
        self.xmult = float(osd.width  - (config.OSD_OVERSCAN_LEFT+config.OSD_OVERSCAN_RIGHT)) / 800
        self.ymult = float(osd.height - (config.OSD_OVERSCAN_TOP+config.OSD_OVERSCAN_BOTTOM)) / 600

        self.xscale = lambda x: int(x * self.xmult)
        self.yscale = lambda y: int(y * self.ymult)

        self.update_functions = (self.update_day, self.update_forecast, self.update_week, self.update_map)

    def day_item(self, x1, text, x2, value, y, align='left'):
        """ This is helper function for update_day
        """
        self.write_text(text, self.key_font, self.content, x=x1, y=y, height=-1, align_h=align)
        self.write_text(value, self.val_font, self.content, x=x2, y=y, height=-1, align_h=align)

    def update_day(self):
        """ Update the day screen
        """
        logger.log( 9, 'update_day()')
        # display data

        x_col1 = self.content.x + self.xscale(50)
        x_col2 = self.content.x + self.xscale(250)
        y_start = self.content.y + self.yscale(60)
        y_inc = self.yscale(40)

        y = y_start
        self.day_item(x_col1, _('Humidity'), x_col2, self.parent.weather.getHumidity(), y)
        y += y_inc
        self.day_item(x_col1, _('Pressure'), x_col2, self.parent.weather.getPressure(), y)
        y += y_inc
        self.day_item(x_col1, _('Wind'), x_col2, self.parent.weather.getWind(), y)
        y += y_inc
        self.day_item(x_col1, _('Wind Chill'), x_col2, self.parent.weather.getFeeling(), y)
        y += y_inc
        self.day_item(x_col1, _('Visibility'), x_col2, self.parent.weather.getVisibility(), y)
        y += y_inc
        self.day_item(x_col1, _('UV Index'), x_col2, self.parent.weather.getUvType(), y)

        # draw current condition image
        x_start = self.content.x + self.xscale(480)
        y_start = self.content.y + self.yscale(40)
        self.draw_image(self.parent.weather.image,
            (x_start, y_start, self.xscale(200), self.yscale(150)))

        y_start = self.content.y + self.yscale(200)
        self.write_text(self.parent.weather.getCurrentCondition(), self.key_font, self.content,
            x=x_start, y=y_start, width=self.xscale(200), height=-1, align_h='center')
        y_start = self.content.y + self.yscale(250)
        self.write_text(self.parent.weather.getTemperature(), self.big_font, self.content,
            x=x_start, y=y_start, width=self.xscale(200), height=-1, align_h='center')

        x_start = self.content.x + self.xscale(40)
        y_start = self.content.y + self.yscale(380)
        self.write_text(self.parent.weather.getLastUpdated(), self.small_font, self.content,
            x=x_start, y=y_start, width=self.content.width, height=-1, align_h='left')


    def update_forecast(self):
        """ this screen is taken from the 1click weather forecast of the firefox plug-in.
        TODO Switch to night after sunset
        """
        logger.log( 9, 'update_forecast()')
        x_start = self.content.x + self.xscale(20)
        y_start = self.content.y + self.yscale(30)
        weather = self.parent.weather

        lines = []
        try:
            lines.append('%s: %s' % (_('As of'), weather.getLastUpdated()))
            lines.append('%s: %s' % (_('at'), weather.getObservationStation()))
            lines.append('  %s' % (weather.getCurrentCondition()))
            lines.append('  %s: %s' % (_('Temperature'), weather.getTemperature()))
            lines.append('  %s: %s' % (_('Dew Point'), weather.getDewPoint()))
            lines.append('  %s: %s' % (_('Humidity'), weather.getHumidity()))
            lines.append('  %s: %s' % (_('Visibility'), weather.getVisibility()))
            lines.append('  %s: %s' % (_('Pressure'), weather.getPressure()))
            lines.append('  %s: %s' % (_('Winds'), weather.getWind()))
            lines.append('%s:' % (_('Tonight')))
            lines.append('  %s: %s' % (_('Sunset'), weather.getSunset()))
            lines.append('  %s: %s' % (_('Moon Phase'), weather.getMoonPhase()))
        except Exception, why:
            logger.warning(why)
            import traceback, sys
            output = apply(traceback.format_exception, sys.exc_info())
            output = ''.join(output)
            output = urllib.unquote(output)
            _debug(output)

        y = y_start
        for line in lines:
            self.write_text(line, self.key_font, self.content,
            x=x_start, y=y, height=-1, align_h='left')
            y += self.yscale(30)

        try:
            x_start = self.content.x + self.xscale(500)
            y_start = self.content.y + self.yscale(300)
            #self.draw_image(weather.getMoonImage(weather.getMoonIcon()),
            #(x_start, y_start, self.xscale(90), self.yscale(90)))
        except Exception, why:
            logger.warning(why)


    def week_item(self, x, y, text, font, width=90, align='center'):
        """ This is helper function for update_week """
        self.write_text(text, font, self.content, x=x, y=y, width=self.xscale(width), height=-1, align_h=align)

    def update_week(self):
        """ update the weeks forecast
        TODO this can be improved
        """
        logger.log( 9, 'update_week()')

        x_start = self.content.x + self.xscale(10)
        y_start = self.content.y + self.yscale(20)

        day = 0
        for pos in (0, 180, 360, 540):

            x = x_start + self.xscale(pos)
            y = y_start

            self.week_item(x, y, _(Unicode(self.parent.weather.date[day])), self.key_font, 160)

            self.draw_image(self.parent.weather.weatherIcon[day],
                (x, y + self.yscale(50), self.xscale(160), self.yscale(120)))

            y = y_start + self.yscale(200)
            self.week_item(x, y, _(Unicode(self.parent.weather.weatherType[day])), self.small_font, 160)

            y = y_start + self.yscale(240)
            self.week_item(x, y, _("LO"), self.val_font)

            y = y_start + self.yscale(270)
            self.week_item(x, y, self.parent.weather.lowTemp[day], self.key_font)

            y = y_start + self.yscale(240)
            self.week_item(x+self.xscale(70), y, _("HI"), self.val_font)

            y = y_start + self.yscale(270)
            self.week_item(x+self.xscale(70), y, self.parent.weather.highTemp[day], self.key_font)

            y = y_start + self.yscale(300)
            self.week_item(x, y, '%s%%' % self.parent.weather.ppcp[day], self.key_font, 160)

            day += 1


    def update_map(self):
        """ update the contents of the skin's doppler weather map """
        logger.log( 9, 'update_map()')
        if not self.parent.weather.weatherMapData:
            x_start = self.content.x + self.xscale(10)
            y_start = self.content.y + self.yscale(10)
            self.write_text(_("Error encountered while trying to download weather map"),
                self.key_font, self.content, x=x_start, y=y_start,
                width=self.content.width, height=-1, align_h='left')
        elif self.parent.weather.mapFile:
            self.draw_image(self.parent.weather.mapFile,
                (self.content.x-self.xscale(2), self.content.y+self.xscale(10),
                self.content.width, self.content.height))

    def update_content(self):
        """ update the contents of the skin """
        logger.log( 9, 'update_content()')
        self.parent = self.menu
        self.content = self.calc_geometry(self.layout.content, copy_object=True)
        self.update_functions[self.menu.skin_num]()


# create one instance of the WeatherType class
skin.register ('oneclick', ('screen', 'subtitle', 'title', 'plugin', WeatherBaseScreen()))

TRANLATIONS = [
    _('Mostly Cloudy'),
    _('Partly Cloudy'),
    _('Light Rain'),
    _('Showers'),
    _('Rain'),
    _('Fog'),
    _('Few Showers'),
    _('Mostly Sunny'),
    _('Sunny'),
    _('Scattered Flurries'),
    _('Isolated T-Storms'),
    _('Scattered Thunderstorms'),
    _('Snow Showers'),
    _('Few Snow Showers'),
    _('Flurries'),
    _('Thunder'),
    _('Heavy Snow'),
    _('Drizzle'),
    _('Sct Flurries'),
    _('Sct Strong Storms'),
    _('Thunderstorms'),
    _('Iso T-Storms'),
    _('Sct T-Storms'),
    _('Sct Snow Showers'),
    _('to'),
    _('Ice'),
    _('Light Snow'),
    _('Wintry Mix'),
    _('Hvy Rain'),
    _('Freezing Rain'),
    _('T-Storms'),
    _('Heavy Rain'),
    _('Light Wintry Mix'),
    _('Snow Shower'),
    _('Strong Storms'),
    _('Light Rain Shower'),
    _('Light Rain with Thunder'),
    _('Light Drizzle'),
    _('Mist'),
    _('Smoke'),
    _('Haze'),
    _('Light Snow Shower'),
    _('Clear'),
    _('A Few Clouds'),
    _('Fair'),
    _('Last updated: %s'),
    _('Unlimited'),
    _('%s (day: %s)'),
    _('%s (type: %s)'),
    _('Today, a high of %s degrees'),
    _('and a low of %s degrees.'),
    _('Currently, there is a humidity of'),
    _('the winds are calm'),
    _('Visibility will be unlimited today'),
    _('There will be a visibility of'),
    _('Error encountered while trying to download Radar map'),
    _('Display program'),
    _('Scheduling Failed'),
    _('getFavorites failed: %s'),
    _('Display favorite'),
    _('Modify duplicate flag'),
    _('Modify episodes flag'),
    _('Modify Duplicate Flag'),
    _('Save Failed, favorite was lost'),
    _('Save Failed'),
    _('Currently recording'),
    _('Next recordings'),
    _('Recordserver not found'),
    _('Clear / Wind'),
    _('Clouds Early / Clearing Late'),
    _('Cloudy'),
    _('Cloudy / Wind'),
    _('Cloudy and Windy'),
    _('Drifting Snow'),
    _('Drizzle / Fog'),
    _('Drizzle Late'),
    _('E'),
    _('ENE'),
    _('ENE_short'),
    _('ESE'),
    _('ESE_short'),
    _('E_short'),
    _('Extreme'),
    _('Few Showers / Wind'),
    _('Few Snow'),
    _('Few Snow Showers / Wind'),
    _('First Quarter'),
    _('Fog Early / Clouds Late'),
    _('Fog Late'),
    _('Foggy'),
    _('Freezing Drizzle'),
    _('Full'),
    _('Heavy Rain / Wind'),
    _('High'),
    _('Isolated T-Storms / Wind'),
    _('Last Quarter'),
    _('Lawn and Garden Weather'),
    _('Light Freezing Rain'),
    _('Light Rain / Fog'),
    _('Light Rain / Wind'),
    _('Light Rain / Wind Late'),
    _('Light Rain Early'),
    _('Light Rain Late'),
    _('Light Rain and Freezing Rain'),
    _('Light Rain and Shower'),
    _('Light Rain and Windy'),
    _('Light Snow / Fog'),
    _('Light Snow / Wind'),
    _('Light Snow Early'),
    _('Light Snow Late'),
    _('Low'),
    _('Mostly Clear'),
    _('Mostly Cloudy / Wind'),
    _('Mostly Cloudy and Windy'),
    _('N'),
    _('N/A'),
    _('NE'),
    _('NE_short'),
    _('NNE'),
    _('NNE_short'),
    _('NNW'),
    _('NNW_short'),
    _('NW'),
    _('NW_short'),
    _('N_short'),
    _('New'),
    _('Overcast'),
    _('PM Fog'),
    _('PM Light Rain'),
    _('PM Light Rain / Wind'),
    _('PM Light Snow'),
    _('PM Rain'),
    _('PM Rain / Snow'),
    _('PM Rain / Wind'),
    _('PM Showers'),
    _('PM Showers / Wind'),
    _('PM Snow Showers'),
    _('PM T-Storms'),
    _('Partly Cloudy / Wind'),
    _('Partly Cloudy and Windy'),
    _('Rain / Freezing Rain'),
    _('Rain / Snow'),
    _('Rain / Snow / Wind'),
    _('Rain / Snow Early'),
    _('Rain / Snow Late'),
    _('Rain / Snow Showers'),
    _('Rain / Snow Showers / Wind'),
    _('Rain / Snow Showers Late'),
    _('Rain / Thunder'),
    _('Rain / Wind'),
    _('Rain / Wind Early'),
    _('Rain Early'),
    _('Rain Late'),
    _('Rain Shower'),
    _('Rain Shower and Windy'),
    _('Rain and Snow'),
    _('Rain to Wintry Mix'),
    _('Rain to Wintry Mix / Wind'),
    _('S'),
    _('SE'),
    _('SE_short'),
    _('SSE'),
    _('SSE_short'),
    _('SSW'),
    _('SSW_short'),
    _('SW'),
    _('SW_short'),
    _('S_short'),
    _('Scattered Showers'),
    _('Scattered Snow'),
    _('Scattered Snow Showers'),
    _('Scattered T-Storms'),
    _('Showers / Wind'),
    _('Showers / Wind Early'),
    _('Showers Early'),
    _('Showers Late'),
    _('Showers in the Vicinity'),
    _('Snow'),
    _('Snow / Wind'),
    _('Snow Shower / Wind'),
    _('Snow Showers / Wind Early'),
    _('Snow Showers Early'),
    _('Snow Showers Late'),
    _('Snow and Freezing Rain'),
    _('Snow to Rain'),
    _('Snow to Wintry Mix'),
    _('Snow to Wintry Mix / Wind'),
    _('Storm'),
    _('Sunny / Wind'),
    _('T-Showers'),
    _('T-Storms Early'),
    _('Very High'),
    _('W'),
    _('WNW'),
    _('WNW_short'),
    _('WSW'),
    _('WSW_short'),
    _('W_short'),
    _('Waning Crescent'),
    _('Waning Gibbous'),
    _('Waxing Crescent'),
    _('Waxing Gibbous'),
    _('Wintry Mix / Wind'),
    _('Wintry Mix / Wind Early'),
    _('Wintry Mix to Snow'),
    _('rising'),
    _('steady'),
]
