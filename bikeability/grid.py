import h3
import shapely
import os
import geopandas as gpd
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
def create_h3_grid(gdf, res):
    poly = gdf.to_crs(4326).unary_union
    poly_list = [(i[0], i[1]) for i in list(poly.exterior.coords)]
    hexes = h3.polyfill_polygon(
        poly_list, res=res
    )
    geoms = []
    for hex in hexes:
        geoms.append(Polygon(h3.h3_to_geo_boundary(hex)))
        #print(h3.h3_to_geo_boundary(hex))
    #geodf_poly = gpd.GeoDataFrame(crs='epsg:4326', geometry=geoms)
    geodf_poly = gpd.GeoDataFrame(geometry=geoms, crs=4326)
    return geodf_poly

