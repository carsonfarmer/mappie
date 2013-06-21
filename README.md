mappie
======

mappie: A Python package for playing with webmap images

mappie makes it easy to download map tiles from various webmap sources and use 
them in visualizations with any type of geospatial data. It is designed with 
'matplotlib' and 'cartopy' in mind, but should work nicely with most geospatial 
plotting libraries in Python (e.g., Basemap).

License
----------
mappie is licensed under an 
[MIT license](https://github.com/cfarmer/mappie/blob/master/LICENSE), 
and so are the [bits](https://github.com/geopy/geopy) and 
[bobs](https://github.com/cbick/osmviz) it is based on.

Dependencies
----------
On it's own, mappie doesn't require anything beyond basic Python packages and 
['PIL'](http://www.pythonware.com/products/pil/) or ['pillow'](http://python-imaging.github.io/Pillow/):
    Pillow is the "friendly" PIL fork by Alex Clark and Contributors.
    PIL is the Python Imaging Library by Fredrik Lundh and Contributors.

To do anything useful with mappie though, you'll want a few additional packages:
For plotting and visualization of the downloaded map tiles, you'll want 
to use ['matplotlib'](http://matplotlib.org/) - the de-facto 2-D plotting library for Python 
    
For functions and tools specific to drawing maps and visualizing geospatial
data check out ['cartopy'](http://scitools.org.uk/cartopy/) or ['Basemap'](http://matplotlib.org/basemap/).
The following plotting example is based on 'cartopy', but you can do 
similar things with 'Basemap' based on the [examples here](http://matplotlib.org/basemap/users/examples.html).

Example
----------

```python
import mappie.sources as sources
from mappie.geocoder import Geocoder
google = sources.GoogleManager()
geocoder = Geocoder()
bbox = geocoder.geocode('Hunter College, New York, NY, USA', output='bbox')
webmap, newbox = google.create_map(bbox, zoom=7)
newbox
(39.694555483164955, 41.824595150921695, -75.37065401673316, -72.55815401673317)
webmap.show()
```

Plotting
----------
```python
from cartopy import config
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
fig = plt.figure(figsize=(8, 12))
ax = plt.axes(projection=ccrs.PlateCarree())
ext = newbox[2:4]+newbox[0:2] # re-arrange bounding box for 'imshow'
ax.imshow(webmap, origin='upper', extent=ext, transform=ccrs.PlateCarree())
ax.coastlines(resolution='50m', color='black', linewidth=2)
plt.show() # or plt.savefig('google-map.png')
```
![image](https://raw.github.com/cfarmer/mappie/master/google-map.png "GoogleMap Tile")
