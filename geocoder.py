#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple geocoder for mappie

This is just a simple 'wrapper' around the `geopy` `GoogleV3` geocoder. This 
version allows for more control over which components of the returned JSON
feed are available to the user.

"""

from geopy.geocoders import GoogleV3
import geopy.util as util

from urllib import urlencode
from urllib2 import urlopen

# so that we have access to geopy directly if we want it
import geopy as geopy

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json


class Geocoder(GoogleV3):
    '''Geocoder using the Google Maps v3 API.
    
    This is just a simple 'wrapper' around the `geopy` `GoogleV3` geocoder,
    that allows for more control over which components of the geocoded 
    results are returned.
    
    '''

    def geocode_url(self, url, exactly_one=True, output='latlon'):
        '''Fetches the url and returns the result.
        
        '''

        util.logger.debug("Fetching %s..." % url)
        page = urlopen(url)

        return self.parse_json(page, exactly_one, output)

    def geocode(self, string, bounds=None, region=None, language=None, 
        sensor=False, exactly_one=True, output='latlon'):
        '''Geocode an address.

        string : str (required)
            The address that you want to geocode.

        bounds : tuple (optional)
            The bounding box of the viewport within which to bias geocode 
            results more prominently.

        region : str (optional)
            The region code, specified as a ccTLD ("top-level domain") 
            two-character value.

        language : str (optional)
            The language in which to return results. See the supported list 
            of domain languages. Note that we often update supported languages 
            so this list may not be exhaustive. If language is not supplied, 
            the geocoder will attempt to use the native language of the domain 
            from which the request is sent wherever possible.

        sensor : bool (required)
            Indicates whether or not the geocoding request comes from a device 
            with a location sensor. This value must be either True or False.
        
        output : str (optional)
            The type of output to return. Can be one of the following:
            'latlon'   - (lat, lon) tuple
            'alatlon'  - address, (lat, lon) tuple
            'bbox'     - bounding box tuple (ymin, ymax, xmin, xmax)
            'geometry' - geometry component of returned JSON as Python dict
            'all'      - entire returned JSON data as Python dict
        
        '''

        if isinstance(string, unicode):
            string = string.encode('utf-8')

        params = {
            'address': self.format_string % string,
            'sensor': str(sensor).lower()
        }

        if bounds:
            params['bounds'] = bounds
        if region:
            params['region'] = region
        if language:
            params['language'] = language

        if not self.premier:
            url = self.get_url(params)
        else:
            url = self.get_signed_url(params)

        return self.geocode_url(url, exactly_one, output)

    def parse_json(self, page, exactly_one=True, output='latlon'):
        '''Parse returned json feed of geocoded results
        
        Returns various forms of the geocoded 'location' from the JSON feed.
        Type of locations include latitude and longitude, address, bounding 
        box (viewport), geometry information, or the entire JSON feed.

        '''

        if not isinstance(page, basestring):
            page = util.decode_page(page)
        self.doc = json.loads(page)
        places = self.doc.get('results', [])
    
        if not places:
            check_status(self.doc.get('status'))
            return None
        elif exactly_one and len(places) != 1:
            raise ValueError(
                "Didn't find exactly one placemark! (Found %d)" % len(places))
        outputs = ('latlon', 'alatlon', 'bbox', 'geometry', 'all')
        if not output in outputs:
            raise ValueError(
                "Invalid `output` parameter, must be one of ('%s')" % "', '".join(outputs))
    
        def parse_place(place):
            '''Get the location, lat, lng from a single json place.'''
            location = place.get('formatted_address')
            latitude = place['geometry']['location']['lat']
            longitude = place['geometry']['location']['lng']
            if output == 'alatlon':
                return (location, (latitude, longitude))
            elif output == 'bbox':
                northeast = place['geometry']['viewport']['northeast']
                southwest = place['geometry']['viewport']['southwest']
                xmin, xmax = southwest['lng'], northeast['lng']
                ymin, ymax = southwest['lat'], northeast['lat']
                return (ymin, ymax, xmin, xmax)
            elif output == 'geometry':
                return place['geometry']
            elif output == 'all':
                return place
            else: # latlon
                return (latitude, longitude)
        
        if exactly_one:
            return parse_place(places[0])
        else:
            return [parse_place(place) for place in places]

