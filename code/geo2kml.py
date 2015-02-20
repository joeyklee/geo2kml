'''
geo2kml+.py 
By: @joeyklee
About: geo2kml+ is a python script that coverts a csv (with lat/lon coordinates), a point shapefile, 
or polygon shapefile to a kml file, extruding each polygon feature by a specified attribute to highlight
a variable of interest. The lat/lon coordinates of the CSV and the shapefiles should be in 
WGS 84 (EPSG:4236).  This was inspired by work being done in the urban climate community visualizing 
greenhouse gas (GHG) traces in google earth.

Refs:
simplekml:
# http://simplekml.readthedocs.org/en/latest/index.html
RGB Colors:
# http://stackoverflow.com/questions/214359/converting-hex-color-to-rgb-and-vice-versa
# http://stackoverflow.com/questions/27206300/assign-color-to-value
# http://stackoverflow.com/questions/20792445/calculate-rgb-value-for-a-range-of-values-to-create-heat-map
Hex opacity:
http://stackoverflow.com/questions/15852122/hex-transparency-in-colors
'''

import simplekml
import pandas as pd
from geopandas import GeoDataFrame, GeoSeries
from shapely.geometry import Point, Polygon
import numpy as np
import colorsys
import matplotlib.cm as cm
import matplotlib.colors as colors
import sys

# RGB/HEX Color function
def f2hex(f2rgb, f):
    rgb = f2rgb.to_rgba(f)[:3]
    return '#%02x%02x%02x' % tuple([255*fc for fc in rgb])


# Data Filtering/Prep 
def makedata(ifile, zfield, *args):
	# if csv:
	if ifile[-4:] == '.csv':
		data = pd.read_csv(ifile, header=0)
		# Filter data
		data = data[(data[zfield] != -9999.0) & (data[lat] != -9999.0) & (pd.isnull(data[lat]) == False)]
		# Get points and Buffer to create polygon type
		coords = GeoSeries([Point(x, y) for x, y in zip(data[lon], data[lat])])
		data['geometry'] = coords.buffer(0.0001)
		# Filter out null types
		data = data[pd.isnull(data.geometry) == False]
		#Recreate index
		data.index = [i for i in range(len(data))]
		return GeoDataFrame(data)#

	elif ifile[-4:] == '.shp':
		data = GeoDataFrame.from_file(ifile)
		# Polygon types
		if isinstance(data.geometry[1], Polygon) == True:
			data = data[pd.isnull(data.geometry) == False]
			return data
		# Point types
		elif isinstance(data.geometry[1], Point) == True:
			coords = data.geometry.buffer(0.0001)
			data['geometry'] = coords
			# Filter out null types
			data = data[pd.isnull(data.geometry) == False]
			# Recreate index
			data.index = [i for i in range(len(data))]
			return GeoDataFrame(data)
		else:
			return "Filetype not supported - Only points or polygons!"

# Build the KML from the input data
def geo2kml(ifile, zfield, ofile, inflate=1):
	# Create empty KML object
	kml = simplekml.Kml()
	# Select the zfield from which to extrude
	altitude = [[i*inflate] for i in ifile[zfield]] 
	# norm = colors.Normalize(vmin=380, vmax=600)
	norm = colors.Normalize(vmin=ifile[zfield].min(), vmax=ifile[zfield].max())
	f2rgb = cm.ScalarMappable(norm=norm, cmap=cm.get_cmap('YlOrRd')) #RdYlGn'
	a_color = [f2hex(f2rgb, i[0]) for i in altitude]
	a_color_alpha = [simplekml.Color.hex(i[1:]) for i in a_color]

	# Create list of coordinates for each polygon
	polycoords = []
	for i in np.arange(0,len(ifile),1):
		polycoords.append([i for i in ifile.geometry[i].exterior.coords])
	# add the z value to the coordinate list
	newcoords =[]
	for j in np.arange(0, len(ifile),1):
		newcoords.append([i + (tuple(altitude[j])) for i in polycoords[j]])
	# Create a new polygon for each feature, iteritively adding to the kml object
	for i in np.arange(0,len(ifile),1):
		pol = kml.newpolygon(name="data",
	                     outerboundaryis= newcoords[i])

		pol.altitudemode = simplekml.AltitudeMode.relativetoground
		pol.style.polystyle.fill = 1
		pol.style.polystyle.outline = 0
		# pol.style.polystyle.color = simplekml.Color.hex(a_color[i][1:])
		pol.style.polystyle.color = simplekml.Color.changealpha('80', a_color_alpha[i])
		pol.extrude = 1

	# add a legend
	legendimg = 'http://ibis.geog.ubc.ca/~achristn/images/mobile_co2_legend_small.gif'
	screen = kml.newscreenoverlay(name='ScreenOverlay')
	screen.icon.href = legendimg
	screen.overlayxy = simplekml.OverlayXY(x=0,y=0,xunits=simplekml.Units.fraction,
	                                       yunits=simplekml.Units.fraction)
	screen.screenxy = simplekml.ScreenXY(x=25,y=95,xunits=simplekml.Units.pixel,
	                                     yunits=simplekml.Units.pixel)
	screen.size.x = 56
	screen.size.y = 355
	screen.size.xunits = simplekml.Units.pixel
	screen.size.yunits = simplekml.Units.pixel

	
	kml.save(ofile)
	print "process complete!"

def main():
	# --- uncomment For shapefiles --- #
	# data = makedata(ifile, zfield)
	# --- uncomment For CSV  --- #
	data = makedata(ifile, zfield, lat, lon)
	# --- Build kml from input data --- #
	geo2kml(data, zfield, ofile)


if __name__ == '__main__':
	# --- Csv test --- #
	ifile = '/Users/Jozo/Dropbox/projects/webpage/pyGeo/geo2kml+/example/csv/140911141741_filtered.csv'
	zfield = 'CO2ppm'
	lon = 'GPSLondeg'
	lat = 'GPSLatdeg'
	# ofile = '/Users/Jozo/Dropbox/projects/webpage/pyGeo/geo2kml+/example/csv/test.kml'
	ofile = ifile[:-4]+".kml"

	# # --- shp test --- #
	# ifile = '/Users/Jozo/Dropbox/projects/webpage/pyGeo/geo2kml+/example/pointshp/example.shp'
	# zfield = 'altitude'
	# ofile = '/Users/Jozo/Dropbox/projects/webpage/pyGeo/geo2kml+/example/pointshp/example.kml'

	# --- shp test2 --- #
	# ifile = '/Users/Jozo/Dropbox/projects/webpage/pyGeo/geo2kml+/example/polygonshp/test.shp'
	# zfield = 'MAXCo2_ppm'
	# ofile = '/Users/Jozo/Dropbox/projects/webpage/pyGeo/geo2kml+/example/polygonshp/test.kml'


	# Run main()
	main()

