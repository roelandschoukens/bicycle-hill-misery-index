#! python3

"""
Clip the coast line polygons, and inverts the area so it covers the ocean.

It is important to do all overlay operations here, since these tend to cause
heap corruption in some versions of geopandas
"""

import argparse
import sys
import json
import re

import geopandas as gpd
from shapely.geometry import box


parser = argparse.ArgumentParser(description="Load coastline shapefile and create the water shapefile")
parser.add_argument("coastlines", metavar='COASTLINES.SHP', help="Shapefile with coastlines")
parser.add_argument("bbox", metavar='ROADS.BBOX', help="JSON file with bounding box")
parser.add_argument("--output", "-o", metavar='OCEANS.GEOJSON', help="Output file, geojson with oceans")
parser.add_argument("--tolerance", default=40, help="Tolerance to simplify the coastline shapes")
args = parser.parse_args()


coast = gpd.GeoDataFrame.from_file(args.coastlines)

# bounding box in various representations
from bbox import *
bbox_total = BBOX(*json.load(open(args.bbox)))
bbox_sh = box(*bbox_total.xyxy())
box_df = gpd.GeoDataFrame(gpd.GeoSeries(bbox_sh), columns=['geometry'], crs=coast.crs)

# discard any polygon which doesn't intersect the area at all:
print("clipping coastlines", flush=True)
small = coast.iloc[list(coast.sindex.query(bbox_sh))]

# clip to slightly larger area
box_df_extend = gpd.GeoDataFrame(box_df.buffer(args.tolerance, cap_style = 3), columns=['geometry'], crs=coast.crs)
small = gpd.overlay(box_df_extend, small, how='intersection')
# simplify and clip exactly
small.geometry = small.simplify(args.tolerance)
small = gpd.overlay(box_df, small, how='difference')

# beware: to_json() doesn’t produce usable JSON files
args.output
small.to_file(args.output, driver='GeoJSON')
with open(args.output, encoding='utf-8') as f:
    json = f.read()

# since we only have coordinates here, we can round them by cutting anything that looks like
# digits after the decimal point
json = re.sub(r"(\d+)\.\d+", r"\1", json)
open(args.output, 'w', encoding='utf-8').write(json)

print('written to '+args.output)
