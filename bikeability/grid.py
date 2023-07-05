import h3
import shapely
import geopandas as gpd
def create_h3_grid(gdf, res):
    poly = gdf.to_crs(4326).unary_union
    poly_list = [(i[1], i[0]) for i in list(poly.exterior.coords)]
    hexes = h3.polyfill_polygon(
        poly_list, res=res
    )
    multipolygons = h3.h3_set_to_multi_polygon(hexes, geo_json=True)
    from shapely.geometry import Polygon
    geom = [i for i in multipolygons]
    test = gpd.GeoDataFrame({'geometry': geom})

    #sh_test = shapely.geometry.MultiPolygon(multipolygons)
    print("hi")
    return test