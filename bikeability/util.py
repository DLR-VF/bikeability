import geopandas as gpd
import math
from pyproj import CRS
from bikeability import settings
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
from shapely.geometry import MultiPoint
from shapely.geometry import Point
from geopandas import GeoDataFrame
import pandas as pd
from geoalchemy2 import Geometry, WKTElement


def create_cycle_tracks(aggregation_units, network):
    cycle_tracks = network[network["highway"] == "cycleway"]
    cycle_tracks = cycle_tracks.overlay(aggregation_units, how="intersection")
    return cycle_tracks


def create_highway_buffers(aggregation_units, network):
    network = project_gdf(network)
    aggregation_units = project_gdf(aggregation_units)
    highway_buffer = network[(network["highway"] == "primary") |
                             (network["highway"] == "secondary") |
                             (network["highway"] == "tertiary")].unary_union.buffer(15)
    highway_buffer = gpd.GeoDataFrame(geometry=[highway_buffer], crs=network.crs)
    highway_buffer = highway_buffer.overlay(aggregation_units, how="intersection")
    return highway_buffer


def create_steets(aggregation_units, network):

    streets = network[(network["highway"] == "primary") |
                             (network["highway"] == "secondary") |
                             (network["highway"] == "tertiary") |
                             (network["highway"] == "residential") |
                             (network["highway"] == "living_street") |
                             (network["highway"] == "motorway") |
                             (network["highway"] == "trunk") ]
    streets = streets[["highway", "oneway", "surface", "geometry"]]
    streets = streets.overlay(aggregation_units, how="intersection")
    return streets


def create_parks(aggregation_units, urban_green):
    aggregation_units = project_gdf(aggregation_units)
    urban_green = project_gdf(urban_green)
    urban_green = urban_green.overlay(aggregation_units, how="intersection")
    urban_green = urban_green.dissolve("sg_id")
    print("hi")
    return urban_green


def project_gdf(gdf, geom_col="geometry", to_crs=None, to_latlong=False):
    """
    Project a GeoDataFrame to the UTM zone appropriate for its geometries' centroid.

    The simple calculation in this function works well for most latitudes, but
    won't work for some far northern locations like Svalbard and parts of far
    northern Norway.

    :param gdf: the gdf to be projected
    :type gdf: Geopandas.GeoDataFrame
    :param to_crs: CRS code. if not None,project GeodataFrame to CRS
    :type to_crs: int
    :param to_latlong: If True, projects to latlong instead of to UTM
    :type to_latlong: bool
    :return projected_gdf: A projected GeoDataFrame
    :rtype projected_gdf: Geopandas.GeoDataFrame
    """
    assert len(gdf) > 0, "You cannot project an empty GeoDataFrame."

    # if gdf has no gdf_name attribute, create one now
    if not hasattr(gdf, "gdf_name"):
        gdf.gdf_name = "unnamed"

    # if to_crs was passed-in, use this value to project the gdf
    if to_crs is not None:
        projected_gdf = gdf.to_crs(to_crs)

    # if to_crs was not passed-in, calculate the centroid of the geometry to
    # determine UTM zone
    else:
        if to_latlong:
            # if to_latlong is True, project the gdf to latlong
            latlong_crs = settings.default_crs
            projected_gdf = gdf.to_crs(latlong_crs)

        else:
            # else, project the gdf to UTM
            # if GeoDataFrame is already in UTM, just return it
            if (gdf.crs is not None) and (gdf.crs.is_geographic is False):
                return gdf

            # calculate the centroid of the union of all the geometries in the
            # GeoDataFrame
            avg_longitude = gdf[geom_col].unary_union.centroid.x

            # calculate the UTM zone from this avg longitude and define the UTM
            # CRS to project
            utm_zone = int(math.floor((avg_longitude + 180) / 6.0) + 1)
            utm_crs = f"+proj = utm + datum = WGS84 + ellps = WGS84 + zone = {utm_zone} + units = m + type = crs"
            crs = CRS.from_proj4(utm_crs)
            epsg = crs.to_epsg()
            projected_gdf = gdf.to_crs(epsg)

    projected_gdf.gdf_name = gdf.gdf_name
    return projected_gdf

def get_centroids(cluster):
    centroid = (MultiPoint(cluster).centroid.x, MultiPoint(cluster).centroid.y)
    return tuple(centroid)


def cluster_intersections_to_crossroad(nodes, verbose=0):
    ### Uses DBScan clustering algorithm to produce one crossing from several street intersections.
    ###Input:
    ###connection: sqlAlchemy db connection
    ###intersection_schema: schema of street intersection table
    ###intersection_schema: street intersection table
    ###srid: srid code of region

    #srid = int(srid)

    ##data import
    # sql_stmt = "select num, St_X(st_transform(geom,%s)) " \
    #            "AS lon, st_y(st_transform(geom,%s)) " \
    #            "as lat from %s.%s" % (srid, srid, intersection_schema, intersection_table)
    # if verbose > 0:
    #     print(sql_stmt)
    # df = pd.read_sql(sql_stmt, connection)
    nodes["y"] = nodes["geometry"].y
    nodes["x"] = nodes["geometry"].x
    coords = nodes[['y', 'x']].values

    ##clustering
    print('    performing clustering of intersections..')
    db = DBSCAN(eps=40, min_samples=1, n_jobs=-1).fit(coords)
    cluster_labels = db.labels_
    num_clusters = len(set(cluster_labels))
    print('    Number of crossroads: {}\n'.format(num_clusters))
    clusters = pd.Series([coords[cluster_labels == n] for n in range(num_clusters)])

    # get cluster centroids
    centermost_points = clusters.map(get_centroids)
    lats, lons = zip(*centermost_points)
    rep_points = pd.DataFrame({'lon': lons, 'lat': lats})
    rs = rep_points
    geometry = [Point(xy) for xy in zip(rs.lon, rs.lat)]

    geo_df = GeoDataFrame(rs, crs=nodes.crs, geometry=geometry)
    #geo_df['geometry'] = geo_df['geometry'].apply(lambda x: WKTElement(x.wkt, srid=gpd.tools.epsg_from_crs(nodes.crs)))
    #geo_df.drop('geometry', 1, inplace=True)
    return geo_df
    # rs.to_sql(intersection_table+"_clustered", connection, schema='osm', if_exists='replace', index=True,
    #                     dtype={'geom': Geometry('POINT', srid= srid)})
    ##write centriods to db
