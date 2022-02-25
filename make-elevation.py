import argparse
from glob import iglob
import json
import os
import re

import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString
import numpy as np
import rasterio

from bbox import *
from lineops import *

parser = argparse.ArgumentParser(description="Load road shapefile and create a new shape file with elevation data")
parser.add_argument("road", metavar='ROADS.SHP', help="Shapefile with roads")
parser.add_argument("dem", metavar='DEM_DIR', help="Directory with LIDAR data tiles")
parser.add_argument("--test", action='store_true', help="Load only a small set of tiles, and show a plot. This is useful to test alignment")
parser.add_argument("--dist-limit", type=float, default=100, metavar='LENGTH', help="Subdivide street shapes in parts of approximately this length")
parser.add_argument("--output", "-o", nargs=2, metavar=('ROADS-SLOPE.GEOJSON', 'BBOX.JSON'), help="Output files")
args = parser.parse_args()


# roads
# -----

# We’re expected to create a data frame with the following columns:
#
#  - geometry: LineString, preferably reasonably short ones
#  - length: the length of the segment
#  - slope: the slope of the segment (where 0.01 represents a 1% slope)
#  - el1: elevation at the start
#  - el2: elevation at the end
#
# The general idea is to include the streets where ‘most’ cycling will happen.
# So probably not the tiniest residential streets. But also no limited access
# arterials, busways, etc. Bicyclie paths would by nice if we can identify them
# (and if your city actually has them!)
#
# A possible refinement is to add weights, so a tiny street has a lower weight than
# a major bike path.

# At the moment the calculated bounding box is simply the extent of the DEM
# tile grid. This is by far the largest chunk of input data.


# load the roads, and extract columns and rows of interest
import pandas as pd
pd.options.mode.chained_assignment = 'raise'

print("Loading shapefile (patience...)", flush=True)
roads = gpd.GeoDataFrame.from_file(args.road)

# which roads to consider: only the major roads for now
# these often have a favourable elevation profile and are often
# where you cycle for long distances anyway
# bicycle paths are so rare we can ignore them (sadly, and they don’t show
# up as a distinct category in our data)
roadClassTable = {
 'Arterial urban'   : 'L',
 'Arterial rural'   : 'L',
 'Medium urban'     : 'M',
 'Medium rural'     : 'M',
}

# generate a class column. Initially use table
road_type = roads['CLASSIFICA'].map(roadClassTable)
road_type = road_type.mask(road_type.isna(),           False)

# insert kludges here:
road_type = road_type.mask(roads['USE_TYPE'] == "Vehicle only",           False)
road_type = road_type.mask(roads['ID'].isin((2165640, 1955770, 1955710)), 'L') # pretty sure that ramp is not limited access anymore
road_type = road_type.mask(roads['PRIMARY_RO'].isin(("DAIRY FLAT HIGHWAY", "ALBANY EXPRESSWAY")), 'L') # former SH17
road_type = road_type.mask(roads['PRIMARY_RO'].str.contains("BUSWAY", na=False), False)
road_type = road_type.mask(roads['CLASSIFICA'] == "Motorway", False)

roads2 = pd.DataFrame({'road_type': road_type})
roads = gpd.GeoDataFrame(roads2, geometry=roads.geometry, crs=roads.crs)
roads = roads.loc[road_type.astype(bool)].reindex()


def round_line(l):
    return LineString([(int(c[0]), int(c[1])) for c in l.coords])

def split_line_df(dataframe, dist_limit):
    """ splits line segments in this dataframe in place

    also round everything to integer"""

    iloc_index = []
    new_geometry = []
    
    for index, line in enumerate(dataframe.geometry):
        splitted_line = split_line(line, dist_limit)
        splitted_line = [round_line(l) for l in splitted_line]
        new_geometry += splitted_line
        iloc_index += [index] * len(splitted_line)

    dataframe = dataframe.iloc[iloc_index]
    # using in-place produces the "A value is trying to be set on a copy of a slice from a DataFrame." warning
    return dataframe.set_geometry(new_geometry)


# Elevation tiles
# ---------------

tlist = []

def read_sidecar(f):
    """ guess the file name of the sidecar file and read it """
    
    assert f[-4] == '.'
    # sidecar file name:
    f = f[:-4] + '.' + f[-3] + f[-1] + 'w'
    with open(f) as tfwf:
        tfw = tuple(tfwf)
        scale = float(tfw[0].strip())
        x, y = ( float(tfw[4].strip()), float(tfw[5].strip()))
        return x, y, scale


# the DEM from LINZ comes in two formats: kea and tiff
def image_files(d):
    yield from iglob(os.path.join(d, "*.tif"))
    yield from iglob(os.path.join(d, "*.kea"))

image_f_list = list(image_files(args.dem))
if args.test:
    image_f_list = image_f_list[700:900]

for f in image_f_list:
    with rasterio.open(f) as raster:
        arr = raster.read(1)
    
        # The *.kea files don’t have any georeference data in them.
        x, y, scale = read_sidecar(f)
        
        # It is actually feasible to load all those images at once.
        # This may break down if you cover a very large area
        size = (arr.shape[1], arr.shape[0])
        w, h = size[0] * scale, size[1] * scale
        bbox = BBOX(x - 0.5 * scale, y - h + 0.5 * scale, w, h)
        tlist.append(SrcTile(bbox, f, arr, scale))
        
        print(end=f'{len(tlist)}/{len(image_f_list)} DEM tiles at {x:.1f}, {y:.1f}\r', flush=True)

print()

# These images come from a regular grid.
# Reconstruct this grid, and create a lookup table from cell coordinate to
# image

# assume the largest of those images fills exactly one cell
grid_w = max(t.bbox.w for t in tlist)
grid_h = max(t.bbox.h for t in tlist)
grid_x0 = None
grid_y0 = None

bbox_total = BBOX.with_xyxy(
    min(t.bbox.x for t in tlist),
    min(t.bbox.y for t in tlist),
    max(t.bbox.x2() for t in tlist),
    max(t.bbox.y2() for t in tlist))

# the origin is a corner of a full size tile
for t in tlist:
    if t.bbox.w == grid_w and t.bbox.h == grid_h:
        grid_x0 = t.bbox.x
        grid_y0 = t.bbox.y
        break

assert grid_x0, "We are missing the grid"

def tile_index(point):
    return (int(point[0] - grid_x0) // grid_w, int(point[1] - grid_y0) // grid_h)

# now, the lookup table
tmap = {}
for t in tlist:
    tmap[tile_index((t.bbox.x, t.bbox.y))] = t

# and the function to lookup the elevation of a point
def elevation(p):
    tile = tmap.get(tile_index(p), None)
    if tile is None:
        return None
    px = min(tile.bbox.w - 1, max(0, p[0] - tile.bbox.x)) / tile.scale
    py = min(tile.bbox.h - 1, max(0, p[1] - tile.bbox.y)) / tile.scale
    h = tile.img[int(tile.bbox.h - 1 - py)][int(px)]
    if h < -100:
        return None
    if h < 0:
        return 0
    return h

# slopes
# ------

print("Slopes")

# first ensure the segments are short enough
roads = split_line_df(roads, args.dist_limit)

# then create new data columns: start and end point
length = roads.geometry.length.to_numpy()
p1 = roads.geometry.map(lambda x : x.coords[0])
p2 = roads.geometry.map(lambda x : x.coords[-1])

# ...elevation and slope
el1 = p1.map(elevation).to_numpy()
el2 = p2.map(elevation).to_numpy()
slope = np.abs(el2 - el1) / length

# and make dataframe
roads = roads.assign(
    length=np.round(length, 1),
    slope=np.round(slope, 3),
    el1=np.round(el1, 1),
    el2=np.round(el2, 1))
roads = roads.loc[np.isfinite(slope)]


# test
def debug_inspect_height(ax):
    """ Plot elevation as a raster image """
    X = list(range(int(bbox_total.x), int(bbox_total.x2()), 10))
    Y = list(range(int(bbox_total.y), int(bbox_total.y2()), 10))
    Y.reverse()
    Z = np.zeros((len(Y), len(X)))

    for ix, x in enumerate(X):
        for iy, y in enumerate(Y):
            Z[iy][ix] = elevation((x, y))
    dxdZ, dydZ = np.gradient(Z)
    shade = (dxdZ + dydZ) * .2 + .5
    ax.imshow(shade, extent=bbox_total.xxyy())
    

def debug_show_roads(ax):
    """ plot road data """
    roads.plot(ax=ax, column='slope', linewidth=2, vmax=0.25, cmap='hot')

if args.test:
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()

    debug_inspect_height(ax)
    debug_show_roads(ax)
    plt.show()
else:
    roads.to_file(args.output[0], driver='GeoJSON')
    print('written to ' + args.output[0])
    open(args.output[1], "wt").write(json.dumps(bbox_total))
    print("written " + args.output[1])
