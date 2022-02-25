The Cycling Hill Misery Index
=============================

This is the code used to generate the map on my [Cycling Hill Misery Index](http://wrongsideofmycar.blogspot.com/2022/01/cycling-hill-misery-index.html)
post.

![Map](https://raw.githubusercontent.com/roelandschoukens/bicycle-hill-misery-index/main/Cycling%20Hill%20Misery%20Index.jpg)

Dependencies
============

You need Python 3.x (probably something reasonably recent), and these packages:

 - `matplotlib` (not strictly needed to generate things, but nice for debugging)
 - `geopandas` and its dependencies
 - `rasterio`
 - `scipy`

On Windows follow the instructions [from Geoff Boeing](https://geoffboeing.com/2014/09/using-geopandas-windows/) to install geopandas.

Additionally GNU Make is nice to have, and QGIS was used to create the final map.

Input data
==========

You definitely need this data (the linked data is for Auckland, New Zealand):

 - A digital elevation model: I used the [Auckland 1m DEM](https://data.linz.govt.nz/layer/53405-auckland-lidar-1m-dem-2013/).
 - A roads data set, and some way to read it. I got a data set published by Auckland Council for the HackAKL
   hackaton in 2014. This was very detailed but it is no longer available.
   Maybe I’ll use openStreetMap data in the future. `make-elevation.py` will have to be updated to read this data.

To make a nice map you’ll probably want some topographic data. [LINZ](https://data.linz.govt.nz/) publishes topographic
maps, and all the underlying data to generate these maps. You’d probably get:

 - Coast lines: this is Auckland.
 - Lakes: you’ll definitely be able to tell there’s something off about your map if Lake Pupuke isn’t there.
 - Rivers: nice to have

To the best of my knowledge all this data is available under a Creative Commons license. This map, and the underlying
raster data is thus also available under the Creative Commons Attribution 4.0 license.

Making the map
==============

Ideally you could edit the variables in the makefile and run `make all`. If you have QGIS you can open `misery-index.qgz`
and open the **Map** layout.

---------------------------------------------------

This page is dedicated to my parents, who had to tolerate me as a child on bicycle rides.