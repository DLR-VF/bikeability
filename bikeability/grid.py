import geopandas
import h3
import geopandas as gpd
from shapely.geometry import Polygon
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)


def create_h3_grid(gdf: geopandas.GeoDataFrame, res: int):
    """
    :param gdf: Geometries to use. Should be a GeoDataFrame with polygon geometries.
    :param res: resolution of h3 grid (0-15. see https://h3geo.org/docs/core-library/restable)
    :type res: integer
    :returns: 3h grid for respective region in given resolution
    """
    poly = gdf.to_crs(4326).unary_union
    poly_list = [(i[0], i[1]) for i in list(poly.exterior.coords)]
    hexes = h3.polyfill_polygon(
        poly_list, res=res
    )
    geoms = []
    for hexa in hexes:
        geoms.append(Polygon(h3.h3_to_geo_boundary(hexa)))
    geodf_poly = gpd.GeoDataFrame(geometry=geoms, crs=4326)
    return geodf_poly
