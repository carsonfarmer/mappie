#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Map manager classes for mappie

Various classes for downloading, managing, and storing webmap images from 
various webmap servers. Currently, mappie contains classes for downloading
and playing with OpenStreetMap map tiles, 3 types of Stamen map tiles, and 
4 types of Google map tiles.

"""

# Basic imports
import math
import urllib
import hashlib
import os.path as path
import os

# Local import
from mappie.adjust import XYToLL

class ImageManager(object):
    """Create and manipulate images
    
    Simple abstract interface for creating and manipulating images, to be used
    by an MapManager object.
    
    This is a direct copy of an 'ImageManager' from 'osmviz'.

    """

    def __init__(self):
        self.image = None

    def paste_image(self, img, xy):
        """Paste image into internal image at specified top-left coordinate.
        To be overridden.

        """

        raise NotImplementedError("Subclasses should implement this!")

    def load_image_file(self,imagef):
        """Loads specified image file into image object and returns it.
        To be overridden.

        """

        raise NotImplementedError("Subclasses should implement this!")

    def create_image(self,width,height):
        """Create and return image with specified dimensions.
        To be overridden.

        """

        raise NotImplementedError("Subclasses should implement this!")

    def prepare_image(self,width,height,overwrite=True):
        """Create and internally store an image
        
        Parameters
        ----------
        width : int
            Width of image to create in pixels.

        height : int
            Height of image to create in pixels.

        overwrite : bool
            Whether the image be re-created if it has already been created in a
            previous call
        
        """

        if self.image and not overwrite:
            raise Exception("Image already prepared. Set 'overwrite' to True "
            "if you want to create a new image.")
        self.image = self.create_image(width, height)

    def destroy_image(self):
        """Destroys internal representation of the image.

        """

        if self.image:
            del self.image
        self.image = None

    def paste_image_file(self, imagef, xy):
        """Pastes input image file into internal image at specified location.
        
        Given the filename of an image, and the x,y coordinates of the 
        location at which to place the top left corner of the contents
        of that image, pastes the image into this object's internal image.
        
        Parameters
        ----------
        
        imagef : str
            Filename of the input image to be pasted into the internal image.
        
        xy : bool
            x,y coordinates of the location at which to place the top 
            left corner of the input image

        """

        if not self.image:
            raise Exception ("Image not prepared!")

        try:
            img = self.load_image_file(imagef)
        except Exception, e:
            raise Exception("Could not load image "+str(imagef)+"\n"+str(e))

        self.paste_image(img, xy)
        del img

    def get_image(self):
        """ Return the internal image.

        Returns some representation of the internal image. The returned value 
        is not for use by the MapManager.

        """

        return self.image
        
class PILImageManager(ImageManager):
    """An ImageManager which works with PIL images.
    
    This is a direct copy of an 'PILImageManager' from 'osmviz'.

    """

    def __init__(self, mode="RGBA"):
        """Constructs a PIL Image Manager.
        
        Parameters
        ----------
        mode : str
            The PIL mode in which to create the image.

        """

        ImageManager.__init__(self);
        self.mode = mode
        try: import PIL.Image
        except: raise Exception, "PIL could not be imported!"
        self.pil_image = PIL.Image

    def create_image(self,width,height):
        return self.pil_image.new(self.mode, (width, height))

    def load_image_file(self,imagef):
        return self.pil_image.open(imagef)
   
    def paste_image(self,img,xy):
        self.get_image().paste(img, xy)
        
class MapManager(object):
    """A MapManager manages the retrieval and storage of webmap images.

    The basic utility is the `create_map()` method which
    automatically gets all the images needed, and tiles them together 
    into one big image.

    """

    def __init__(self, **kwargs):
        """Creates an MapManager.

        Parameters
        ----------
        cache : str
            Path (relative or absolute) to directory where tiles downloaded
            from map server should be saved. Default "/tmp".
                     
        server : str
            URL of map server from which to retrieve map tiles. This
            should be fully qualified, including the protocol.
            This may be ignored for some manager subclasses.

        image_manager : ImageManager
            Instance of an ImageManager which will be used to do all
            image manipulation. This is currently ignored if provided.

        """

        cache = kwargs.get('cache')
        #mgr = kwargs.get('image_manager')
        server = kwargs.get('server')
        
        self.cache = None
        
        if cache: 
            if not os.path.isdir(cache):
                try:
                    os.makedirs(cache, 0766)
                    self.cache = cache
                    print "Created cache dir",cache
                except:
                    print "Could not make cache dir",cache
            elif not os.access(cache, os.R_OK | os.W_OK):
                print "Insufficient privileges on cache dir",cache
            else:
                self.cache = cache

        if not self.cache:
            self.cache = ( os.getenv("TMPDIR")
                                         or os.getenv("TMP")
                                         or os.getenv("TEMP")
                                         or "/tmp" )
            print "Using %s to cache maptiles." % self.cache
            if not os.access(self.cache, os.R_OK | os.W_OK):
                print "Insufficient access to %s." % self.cache
                raise Exception, "Unable to find/create/use maptile cache directory."
            
        if server: 
            self.server = server
        else:            
            self.server = "http://tile.openstreetmap.org"
        
        # Make a hash of the server URL to use in cached tile filenames.
        md5 = hashlib.md5()
        md5.update(self.server)
        self.cache_prefix =    'mappie-%s-' % md5.hexdigest()[:5]

        self.manager = PILImageManager("RGBA") # use RGBA by default
        
    def get_tile_coord(self, lon_deg, lat_deg, zoom):
        """Get x, y coordinates of map tile based on lat, lon coordinates.
        
        Given lon,lat coords in DEGREES, and a zoom level,
        returns the (x,y) coordinate of the corresponding tile #.
        (http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Python)
        
        Parameters
        ----------
        lon_deg : float
            Longitude in degrees.
            
        lat_deg : float
            Latitude in degress.
            
        zoom : int
            Zoom level at which to download map.
            
        Returns
        ----------
        (xtile, ytile) : tuple
            Tuple containing the x, y coordinates of the required map tile.

        """

        lat_rad = lat_deg * math.pi / 180.0
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + 
            (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return(xtile, ytile)
        
    def get_tile_url(self, tile_coord, zoom):
        """Get appropriately formatted url for retrieving a map from the server.

        Given x,y coord of the tile to download, and the zoom level,
        returns the URL from which to download the image.
        
        Parameters
        ----------
        tile_coord : tuple
            Tuple containing the x, y coordinates of the required map tile

        zoom : int
            Zoom level at which to download map.
            
        Returns
        ----------
        tile_url : str
            URL string which specifies which map tile to download from server.

        """

        params = (self.maptype,zoom,tile_coord[0],tile_coord[1])
        return self.server+"/%s/%d/%d/%d.png" % params

    def get_local_filename(self, tile_coord, zoom):
        """Get appropriately named local filename for downloaded map.

        Given x,y coord of the tile, and the zoom level,
        returns the filename to which the file would be saved
        if it was downloaded. That way we don't have to kill
        the map server every time the thing runs.
        
        Parameters
        ----------
        tile_coord : tuple
            Tuple containing the x, y coords of the tile to be downloaded.
        
        zoom : int
            Zoom level at which to download map.
        
        Returns
        ----------
        filename : str
            Local file path of file that would be saved if it were downloaded.

        """

        params = (self.cache_prefix,self.maptype,zoom,tile_coord[0],tile_coord[1])
        return path.join(self.cache, "%s%s_%d_%d_%d.png" % params)
        
    def retrieve_tile_image(self, tile_coord, zoom):
        """Get the actual tile image from the map server.

        Given x,y coord of the tile, and the zoom level,
        retrieves the file to disk if necessary and 
        returns the local filename.

        """

        filename = self.get_local_filename(tile_coord,zoom)
        if not path.isfile(filename):
            url = self.get_tile_url(tile_coord,zoom)
            try:
                urllib.urlretrieve(url, filename=filename);
            except Exception, e:
                raise Exception, "Unable to retrieve URL: "+url+"\n"+str(e)
        return filename
        
    def tile_nw_latlon(self, tile_coord, zoom):
        """
        Given x,y coord of the tile, and the zoom level,
        returns the (lat,lon) coordinates of the upper
        left corner of the tile.
        """
        xtile, ytile = tile_coord
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = lat_rad * 180.0 / math.pi
        return(lat_deg, lon_deg)
        
    def create_map(self, (minlat, maxlat, minlon, maxlon), zoom, **kwargs):
        """Main map creation function.

        Given bounding latlons (in degrees), and a zoom level,
        creates an image constructed from map tiles.
        
        Parameters
        ----------
        bbox : tuple (minlat, maxlat, minlon, maxlon) [required]
            Bounding box lat/lons (in degrees) of the requested map area.

        zoom : int [required]
            Zoom level at which to download map.
        
        color : str [optional]
            Whether to return a color ('color') or black-and-white ('bw') 
            version of the requested map. This parameter controls the 'mode'
            of the internal image manager.
            
        overwrite : bool [optional]
            Whether previously downloaded/created map images should 
            be overwritten.
        
        Returns
        ----------
        (img, bounds) : (PILImage, tuple)
            The constructed image (as returned by the image manager's 
            "get_image()" method), and bounding box (latmin,latmax,lonmin,lonmax)
            which the tiles covers. The returned bounding box may not be the 
            same as the requested bounding box.

        """
        
        if not self.manager:
            raise Exception("No ImageManager was specified, cannot create image.")
            
        color = kwargs.get('color')
        if color:
                if not isinstance(color, str) or not color in ('color', 'bw'):
                        print "Wrong color specification, must be 'color' or 'bw'."
                        print "Defaulting to 'color'"
                        color = 'color'
        if color == 'bw': mode = "L"
        else: mode = "RGBA"
        self.manager.mode = mode
        
        overwrite = kwargs.get('overwrite')
        if overwrite is None:
                overwrite = True
        if not isinstance(overwrite, bool):
            raise Exception("Invalid 'overwrite' argument, must be True/False.")

        topleft = minX, minY = self.get_tile_coord(minlon, maxlat, zoom);
        bottomright = maxX, maxY = self.get_tile_coord(maxlon, minlat, zoom);
        new_maxlat, new_minlon = self.tile_nw_latlon( topleft, zoom )
        new_minlat, new_maxlon = self.tile_nw_latlon( (maxX+1,maxY+1), zoom )
        # tiles are 256x256
        pix_width = (maxX-minX+1)*256
        pix_height = (maxY-minY+1)*256
        
        self.manager.prepare_image(pix_width, pix_height, overwrite)
        #print "Retrieving %d tiles..." % ( (1+maxX-minX)*(1+maxY-minY) ,)

        for x in range(minX,maxX+1):
            for y in range(minY,maxY+1):
                fname = self.retrieve_tile_image((x,y),zoom)
                x_off = 256*(x-minX)
                y_off = 256*(y-minY)
                self.manager.paste_image_file( fname, (x_off,y_off) )
        #print "... done."
        return (self.manager.get_image(), 
            (new_minlat, new_maxlat, new_minlon, new_maxlon))

class StamenManager(MapManager):
    """A StamenManager manages the retrieval and storage of Stamen Map images.

    """
    
    def __init__(self, **kwargs):
        """Creates a StamenManager.
        
        Parameters
        ----------
        cache : str 
            Path (relative or absolute) to directory where tiles downloaded
            from Stamen server should be saved. Default "/tmp".
                     
        image_manager : ImageManager
            Instance of an ImageManager which will be used to do all
            image manipulation. This is currently ignored if provided.

        """
        
        MapManager.__init__(self, **kwargs)
        self.server = "http://tile.stamen.com"

    def create_map(self, (minlat, maxlat, minlon, maxlon), zoom, **kwargs):
        """Stamen specific map creation function.

        Given bounding latlons (in degrees), and an OSM zoom level,
        creates an image constructed from OSM tiles.
        
        Parameters
        ----------
        bbox : tuple (minlat, maxlat, minlon, maxlon) [required]
            Bounding box lat/lons (in degrees) of the requested map area.

        zoom : int [required]
            Zoom level at which to download map.
            3 (continent) to 18 (building) with default value of 10 (city).
            Actual min and max values vary by maptype.
        
        color : str [optional]
            Whether to return a color ('color') or black-and-white ('bw') 
            version of the requested map. This parameter controls the 'mode'
            of the internal image manager.
            
        maptype : str [optional]
            Type of map to return. This can be one of 'terrain' (default),
            'watercolor', or 'toner'.
            
        overwrite : bool [optional]
            Whether previously downloaded/created map images should 
            be overwritten.
        
        Returns
        ----------
        (img, bounds) : (PILImage, tuple)
            The constructed image (as returned by the image manager's 
            "get_image()" method), and bounding box (latmin,latmax,lonmin,lonmax)
            which the tiles covers. The returned bounding box may not be the 
            same as the requested bounding box.

        """
        
        maptype = kwargs.get('maptype')
        maptypes = ("terrain", "watercolor", "toner")
        if maptype:
            if not isinstance(maptype, str) or \
                 not maptype in maptypes:
                raise ValueError, "Invalid maptype specified, must be '%s', '%s', or '%s'." % maptypes
        else:
            maptype = 'terrain'
        self.maptype = maptype
        return MapManager.create_map(self, (minlat, maxlat, minlon, maxlon), 
            zoom, **kwargs)
        
class OSMManager(MapManager):
    """An OSMManager manages the retrieval and storage of OpenStreetMap images.

    """

    def create_map(self, (minlat, maxlat, minlon, maxlon), zoom, **kwargs):
        """ Create a webmap image using OpenStreetMap tiles.

        Given bounding latlons (in degrees), and an OSM zoom level,
        creates an image constructed from OSM tiles.
        
        Parameters
        ----------
        bbox : tuple (minlat, maxlat, minlon, maxlon) [required]
            Bounding box lat/lons (in degrees) of the requested map area.

        zoom : int [required]
            Zoom level at which to download map.
            3 (continent) to 18 (building) with default value of 10 (city).
        
        color : str [optional]
            Whether to return a color ('color') or black-and-white ('bw') 
            version of the requested map. This parameter controls the 'mode'
            of the internal image manager.
            
        overwrite : bool [optional]
            Whether previously downloaded/created map images should 
            be overwritten.
        
        Returns
        ----------
        (img, bounds) : (PILImage, tuple)
            The constructed image (as returned by the image manager's 
            "get_image()" method), and bounding box (latmin,latmax,lonmin,lonmax)
            which the tiles covers. The returned bounding box may not be the 
            same as the requested bounding box.

        """

        self.maptype = "" # leave this blank for OSM maps
        return MapManager.create_map(self, (minlat, maxlat, minlon, maxlon), 
            zoom, **kwargs)
            
class GoogleManager(MapManager):
    """A GoogleManager manages the retrieval and storage of GoogleMap images.
    
    """

    def __init__(self, **kwargs):
        """Creates a GoogleManager.
        
        Parameters
        ----------
        cache : str
            Path (relative or absolute) to directory where tiles downloaded
            from Google server should be saved. Default "/tmp".
                     
        language : str
            String providing language of map labels (for themes with 
            them) in the format 'en-EN'. Not all languages are supported;
            for those which aren't the default language is used.
                   
        sensor : bool
            Specifies whether the application requesting the static map is 
            using a sensor to determine the user's location.
                 
        region : str
            Region localization as a region code specified as a two-character 
            ccTLD ('top-level domain') value. For more info, see:
            https://developers.google.com/maps/documentation/javascript/basics#Region
        
        image_manager : ImageManager
            Instance of an ImageManager which will be used to do all
            image manipulation. This is currently ignored if provided.

        """
        
        MapManager.__init__(self, **kwargs)

        language = kwargs.get('language')
        if language:
            if not isinstance(language, str):
                raise Exception, "Invalid language specification, must be str."
            language = "language=%s" % language
        else:
            language = ""
        region = kwargs.get("region")
        if region:
            if not isinstance(region, str):
                raise Exception, "Invalid region specification, must be str."
            region = "region=%s" % region
        else:
            region = ""
        sensor = kwargs.get("sensor")
        if sensor:
            if not isinstance(sensor, bool):
                raise Exception, "Invalid sensor specification, must be True or False."
            sensor = "sensor=%s" % str(sensor).lower()
        else:
            sensor = "sensor=%s" % str(False).lower()
        
        params = (language, region, sensor)
        self.server = "http://maps.googleapis.com/maps/api/staticmap?%s&%s&%s" % params
        
    def get_tile_url(self, bbox, zoom):
        """Get appropriately formatted and parametrized url for GoogleMaps API.

        Given bounding box of the area to return, and the zoom level,
        returns the URL from which to download the image.
        
        This version differs from other subclasses in that it uses the 
        Google V3 API, rather than fetching the map tiles directly.
        
        Parameters
        ----------
        bbox : tuple
            Tuple containing the bounding box of the required map area

        zoom : int
            Zoom level at which to download map.
            
        Returns
        ----------
        api_url : str
            URL string/query to send to the GoogleMaps V3 API.

        """
        center_url = "center=%s,%s" % (sum(bbox[0:2])/2., sum(bbox[2:4])/2.)
        zoom_url = 'zoom=%s' % zoom
        size_url = 'size=%sx%s' % self.size
        scale_url = 'scale=%s' % self.scale
        format_url = 'format=png8' # onle png is supported at the moment
        maptype_url = 'maptype=%s' % self.maptype
        # Optional stuff
        style_url = "style=%s" % self.style if self.style else ""
        if self.markers:
            markers = ["%s,%s" % (round(z[0], 6), round(z[1], 6)) for z in self.markers]
            markers_url = "markers=" + "|".join(markers)
        else:
            markers_url = ""
        if self.paths:
            rnd = lambda x: round(x, 6) # save space and time
            paths = ["|".join(["%s,%s" % (rnd(z[0]), rnd(z[1])) for z in path])
                 for path in paths]
            paths_url = "path=" + "&path=".join(paths)
        else:
            paths_url = ""
        params_url = "&".join((center_url, zoom_url, size_url, scale_url,
            format_url, maptype_url, style_url, markers_url, paths_url))
        full_url = self.server + "&" + params_url
        import re
        full_url = re.sub('[&]+','&', full_url) # Removes 'missing' arguments
        if full_url.endswith("&"): full_url = full_url[:-1]
        return full_url

    def create_map(self, (minlat, maxlat, minlon, maxlon), zoom, **kwargs):
        """Google specific map creation function.
        
        Parameters
        ----------
        bbox : tuple (minlat, maxlat, minlon, maxlon) [required]
            Bounding box lat/lons (in degrees) of the requested map area.

        zoom : int [required]
            Zoom level at which to download map.
            3 (continent) to 21 (building) with default value of 10 (city).
        
        color : str [optional]
            Whether to return a color ('color') or black-and-white ('bw') 
            version of the requested map. This paramter controls the 'mode'
            of the internal image manager.
            
        maptype : str [optional]
            Type of map to return. This can be one of 'terrain' (default),
            'satellite', 'roadmap', or 'hybrid'.
            
        overwrite : bool [optional]
            Whether previously downloaded/created map images should 
            be overwritten.
            
        size : tuple [optional]
            Rectangular dimensions of map in pixels (horizontal, vertical). 
            Max size is (640, 640). This parameter is affected in a 
            multiplicative way by scale.
        
        scale : int [optional]
            Multiplicative factor for the number of pixels returned.
            Possible values are 1, 2, or 4 (e.g. size=(640,640) and
            scale=2 returns an image with 1280x1280 pixels). 4 is 
            reserved for Google business users only. scale also affects
            the size of labels.
        
        style : str [optional]
            Character string to be supplied directly to the api for the
            style argument. This is a powerful complex specification,see:
            https://developers.google.com/maps/documentation/staticmaps/
        
        markers : list [optional]
            List of tuples with (latitude, longitude) coordinates for which 
            google markers should be embedded in the map image.
        
        paths : 
            List of lists of tuples with (latitude, longitude) coordinates for 
            which individual paths should be embedded in the map image.
        
        Returns
        ----------
        (img, bounds) : (PILImage, tuple)
            The constructed image (as returned by the image manager's 
            "get_image()" method), and bounding box (latmin,latmax,lonmin,lonmax)
            which the tiles covers. The returned bounding box may not be the 
            same as the requested bounding box.

        """
        
        self.maptype = kwargs.get('maptype') 
        maptypes = ('terrain', 'satellite', 'roadmap', 'hybrid')
        if self.maptype:
            if not isinstance(self.maptype, str) or not self.maptype in maptypes:
                raise ValueError, "Invalid maptype specified, must be '%s', '%s', %s, or '%s'." % maptypes
        else:
            self.maptype = 'terrain'
        
        self.size = kwargs.get('size')
        if self.size:
            if not isinstance(self.size, tuple) or \
               not all([s>0 and s <= 640 for s in self.size]):
                raise ValueError('Invalid size parameter, must be < 640x640')
        else:
            self.size = (256, 256)
        
        self.scale = kwargs.get('scale')
        if self.scale:
            if not self.scale in (1,2,4):
                raise ValueError('Invalid scale parameter, must be 1, 2, or 4')
        else:
            self.scale = 2
            
        self.style = kwargs.get('style')
        if self.style: # if its None, leave it None
            if not isinstance(self.style, str):
                raise ValueError, "Invalid style specified, must be str."
        
        self.markers = kwargs.get('markers')
        if self.markers: # if its None, leave it None
            if not isinstance(markers, list):
                raise ValueError, "Invalid markers specified, must be list of tuples."
            
        self.paths = kwargs.get('paths')
        if self.paths: # if its None, leave it None
            if not isinstance(paths, list):
                raise ValueError, "Invalid paths specified, must be list of lists of tuples."
            
        if not self.manager:
            raise Exception, "No ImageManager was specified, cannot create image."
            
        color = kwargs.get('color')
        if color:
                if not isinstance(color, str) or not color in ('color', 'bw'):
                        print "Wrong color specification, must be 'color' or 'bw'."
                        print "Defaulting to 'color'"
                        color = 'color'
        if color == 'bw': mode = "L"
        else: mode = "RGBA"
        self.manager.mode = mode
        
        overwrite = kwargs.get('overwrite')
        if overwrite is None:
                overwrite = True
        if not isinstance(overwrite, bool):
            raise Exception, "Invalid overwrite argument, must be True or False."

        pix_width = self.scale*self.size[1]
        pix_height = self.scale*self.size[0]
        
        self.manager.prepare_image(pix_width, pix_height, overwrite)
        #print "Retrieving tiles..."

        fname = self.retrieve_tile_image((minlat, maxlat, minlon, maxlon), zoom)
        self.manager.paste_image_file(fname, (0,0))
        #print "... done."
        # Compute actual bounding box (which is not the same as requested)    
        centX, centY = sum([minlon, maxlon])/2., sum([minlat, maxlat])/2.
        new_minlon, new_maxlat = XYToLL(-self.size[0]/2, -self.size[1]/2, 
            centX, centY, int(zoom))
        new_maxlon, new_minlat = XYToLL(self.size[0]/2, self.size[1]/2, 
            centX, centY, int(zoom))
        return (self.manager.get_image(), 
            (new_minlat, new_maxlat, new_minlon, new_maxlon))

class _useragenthack(urllib.FancyURLopener):
    def __init__(self,*args):
        urllib.FancyURLopener.__init__(self,*args)
        for i,(header,val) in enumerate(self.addheaders):
            if header == "User-Agent":
                del self.addheaders[i]
                break
        self.addheader('User-Agent', 'mappie/1.0 +https://github.com/cfarmer/mappie')

#import httplib
#httplib.HTTPConnection.debuglevel = 1
urllib._urlopener = _useragenthack()

