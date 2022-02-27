PYTHON = py -3.8

#****************************

# inputs

DATA_DIR=data

#ROADS = $(DATA_DIR)/hackakl/Roads/roads-11000.shp
DEMTILE_DIR = $(DATA_DIR)/LINZ/lds-auckland-lidar-1m-dem-2013-big
COAST = $(DATA_DIR)/LINZ/nz-coastlines-and-islands-polygons-topo-150k/nz-coastlines-and-islands-polygons-topo-150k.shp
PROFILE = bike.ini

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

$(MI) : $(PROFILE)
	$(PYTHON) miseryindex.py $< -o $@

#$(ROAD_ELEVATION) : $(ROADS)
#	$(PYTHON) make-elevation.py $< $(DEMTILE_DIR) -o $@ $(BBOX)

$(WATER) : $(COAST) $(ROAD_ELEVATION)
	$(PYTHON) make-coast.py  $< $(BBOX) -o $@

$(RASTER) : $(ROAD_ELEVATION) $(BBOX) $(MI) $(WATER)
	$(PYTHON) rasterize.py $^ -o $@
