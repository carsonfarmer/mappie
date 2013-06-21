#!/usr/bin/python

"""adjust.py

Python port of adjust.js (original by Bratliff: <http://www.polyarc.us/adjust.js>)
Ported by Gatubit <gatubit@gmail.com>

This version comes from:
https://gist.github.com/astrocosa/724526

"""

import math

"""
	Parameters:
	 - x:	X pixel offset of new map center from old map center
	 - y:	Y pixel offset of new map center from old map center
	 - lon:	Longitude of map center
	 - lat:	Latitude of map center
	 - z:	Zoom level

	Return Values:
	 - resultX:	Longitude of adjusted map center
	 - resultY:	Latitude of adjusted map center
"""
def XYToLL(x, y, lon, lat, z):
	resultX = XToLon(
		LonToX(lon) + (
			x << (21 - z)
		)
	)
	resultY = YToLat(
		LatToY(lat) + (
			y << (21 - z)
		)
	)
	return resultX, resultY

# ======================= #

OFFSET	= 268435456
RADIUS	= OFFSET / math.pi

def LonToX(lon):
	return round(
		OFFSET + RADIUS * math.radians(lon)
	)

def LatToY(lat):
	return round(
		OFFSET - RADIUS * (math.log(
			(1 + math.sin(math.radians(lat)))
			/
			(1 - math.sin(math.radians(lat)))
		)) / 2
	)

def XToLon(x):
	return math.degrees(
		(round(x) - OFFSET) / RADIUS
	)

def YToLat(y):
	return math.degrees(
		math.pi / 2 - 2 * math.atan(
			math.exp((round(y) - OFFSET) / RADIUS)
		)
	)
