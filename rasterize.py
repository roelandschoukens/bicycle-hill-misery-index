import argparse
from collections import namedtuple
import pandas as pd
import geopandas as gpd
import json
from math import floor
import numpy as np
from scipy.ndimage.filters import gaussian_filter1d
import os
import re
from math import sqrt
import rasterio
from shapely.geometry import LineString, MultiPoint, box
from shapely.ops import split

import matplotlib.pyplot as plt
from our_cm import our_cm

from bbox import *

"""
This creates the raster data with the misery index.

The raster should be reasonably coarse and somewhat blurred. You usually ride up to a few kilometres
away from home so the index should be somewhat dependent on areas up to a kilometre or 2 away.
"""


parser = argparse.ArgumentParser(description="Create our misery index raster.")
parser.add_argument("--resolution", type=float, default=500, help="Size of the pixels in the output")
parser.add_argument("--blur", type=float, default=2, metavar='RADIUS', help="Radius (standard deviation) used to blur the raster")
parser.add_argument("slopes", metavar='ROADS-SLOPE.GEOJSON', help="File with road shapes with slope data")
parser.add_argument("bbox", metavar='ROADS-BBOX.JSON', help="Bounding box")
parser.add_argument("misery_index", metavar='MISERY-INDEX.JSON', help="Misery index table")
parser.add_argument("water", metavar='WATER.GEOJSON', help="Coastline shapes (actually the areas covered in water), if you want to plot them", nargs='?')
parser.add_argument("-o", "--output", metavar='HILL-MISERY-INDEX.TIF', help="Output file (geotiff)")
args = parser.parse_args()


print("loading data", flush=True)

roads = gpd.GeoDataFrame.from_file(args.slopes)
if args.water:
    water = gpd.GeoDataFrame.from_file(args.water)
bbox_total = BBOX(*json.load(open(args.bbox)))
misery_index_json = json.load(open(args.misery_index))

print("making image", flush=True)

# create our image and calculate how the pixel coordinates line up
# the pixels are aligned on an integer multiple of the resolution

img_xy = (floor(bbox_total.x / args.resolution) * args.resolution,
          floor(bbox_total.y / args.resolution) * args.resolution )

def scale_pixel(x, y):
    return int(x - img_xy[0]) // args.resolution, int(y - img_xy[1]) // args.resolution

img_size = scale_pixel(bbox_total.x2(), bbox_total.y2())
img_size = (img_size[0] + 1, img_size[1] + 1)

bbox_img = BBOX(*img_xy, img_size[0] * args.resolution, img_size[1] * args.resolution)

def pixel_for(x, y):
    px = scale_pixel(x, y)
    if px[0] < 0 or px[1] < 0 or px[0] >= img_size[0] or px[1] >= img_size[1]:
        return None
    return px

# image with two channels: misery index and pixel weight
img = np.zeros((img_size[1], img_size[0], 2))


# for every road segment, convert slope to misery index,
# and splat on image

misery_index_sl = np.array([m['slope'] for m in misery_index_json])
misery_index_mi = np.array([m['mi'] for m in misery_index_json])

for slope, centroid, length in zip(roads["slope"], roads.geometry.centroid, roads.geometry.length):
    px = pixel_for(centroid.x, centroid.y)
    # very high slopes are usually artefacts of the DEM following
    # the slope under a bridge
    if px is not None and slope <= 0.25:
        mi, = np.interp([slope], misery_index_sl, misery_index_mi)
        img[img_size[1] - 1 - px[1], px[0], :] += [mi * length, length]

# filter, and discard pixels with too low weight

img = gaussian_filter1d(img, args.blur, 0)
img = gaussian_filter1d(img, args.blur, 1)
img[:, :, 0] =  np.where(img[:, :, 1] > args.resolution * .4, img[:, :, 0], np.nan)
img = img[:, :, 0] / img[:, :, 1]

# write geotiff

from rasterio.transform import Affine

out_meta = rasterio.profiles.DefaultGTiffProfile(
    count=1,
    width=img.shape[1],
    height=img.shape[0],
    crs=roads.crs,
    dtype=rasterio.float32,
    transform=Affine.translation(bbox_img.x, bbox_img.y2()) * Affine.scale(args.resolution, -args.resolution))

with rasterio.open(args.output, "w", **out_meta) as dest:
    dest.write_band(1, img)

print("written " + args.output)

# preview the map data:

fig, ax = plt.subplots()
ax.imshow(img, extent=bbox_img.xxyy(), cmap=our_cm, vmin=0, vmax=1.4)
roads.plot(ax=ax, column='slope', linewidth=2, cmap='turbo', vmax=0.20)
if args.water:
    water.plot(ax=ax, linewidth=0.5, color=(0.7, 0.9, 1), edgecolor=(0.2, 0.5, 0.8))
plt.show()
