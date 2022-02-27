PYTHON = py -3.8

#****************************

# inputs

#ROADS = data/hackakl/Roads/roads-11000.shp
DEMTILE_DIR = data/LINZ/lds-auckland-lidar-1m-dem-2013-big
COAST = data/LINZ/nz-coastlines-and-islands-polygons-topo-150k/nz-coastlines-and-islands-polygons-topo-150k.shp

# outputs

MI = misery-index.json
ROAD_ELEVATION = roads-elevation.geojson
BBOX = roads-bbox.json
WATER = water.geojson
RASTER = hill-misery-index.tif

#****************************

.PHONY: water elevation miseryindex raster all
raster: $(RASTER)
all: raster water
miseryindex: $(MI)
water: $(WATER)
elevation: $(ROAD_ELEVATION)

$(MI) :
	$(PYTHON) miseryindex.py -o $@

#$(ROAD_ELEVATION) : $(ROADS)
#	$(PYTHON) make-elevation.py $< $(DEMTILE_DIR) -o $@ $(BBOX)

$(WATER) : $(COAST) $(ROAD_ELEVATION)
	$(PYTHON) make-coast.py  $< $(BBOX) -o $@

$(RASTER) : $(ROAD_ELEVATION) $(BBOX) $(MI) $(WATER)
	$(PYTHON) rasterize.py $^ -o $@
