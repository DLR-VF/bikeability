import sys
import os
import geopandas
import geopandas as gpd
import math
from pyproj import CRS
from bikeability import settings
from sklearn.cluster import DBSCAN
from shapely.geometry import MultiPoint
from shapely.geometry import Point
from geopandas import GeoDataFrame
import pandas as pd
import warnings

"""Utility functions for bikeability calculation"""

"""
@name : osm.py
@author : Simon Nieland
@date : 26.11.2023
@copyright : Institut fuer Verkehrsforschung, Deutsches Zentrum fuer Luft- und Raumfahrt
"""

project_path = os.path.abspath('../')
sys.path.append(project_path)

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)


# from geoalchemy2 import Geometry, WKTElement




def project_gdf(gdf: geopandas.GeoDataFrame,
                geom_col: str = "geometry",
                to_crs: str = None,
                to_latlong: bool = False) -> geopandas.GeoDataFrame:
    """
    Project a GeoDataFrame to the UTM zone appropriate for its geometries' centroid.

    The simple calculation in this function works well for most latitudes, but
    won't work for some far northern locations like Svalbard and parts of far
    northern Norway.

    :param geom_col: geometry column of the dataset
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


def get_centroids(cluster: object) -> tuple:
    """
    :param cluster: Point cluster
    :return:
    """
    centroid = (MultiPoint(cluster).centroid.x, MultiPoint(cluster).centroid.y)
    return tuple(centroid)


def cluster_intersections_to_crossroad(nodes: geopandas.GeoDataFrame,
                                       verbose: int = 0) -> geopandas.GeoDataFrame:
    """
    Clusters nodes of the street network into real crossroads
    :param nodes: nodes of the street network
    :param verbose: degree of verbosity
    :return: Geodataframe including real crossroads as Points
    """
    nodes["y"] = nodes["geometry"].y
    nodes["x"] = nodes["geometry"].x
    coords = nodes[['y', 'x']].values

    # clustering
    if verbose > 1:
        print('    performing clustering of intersections..')
    db = DBSCAN(eps=40, min_samples=1, n_jobs=-1).fit(coords)
    cluster_labels = db.labels_
    num_clusters = len(set(cluster_labels))
    if verbose > 1:
        print('    Number of crossroads: {}\n'.format(num_clusters))
    clusters = pd.Series([coords[cluster_labels == n] for n in range(num_clusters)])

    # get cluster centroids
    centermost_points = clusters.map(get_centroids)
    lats, lons = zip(*centermost_points)
    rep_points = pd.DataFrame({'lon': lons, 'lat': lats})
    rs = rep_points
    geometry = [Point(xy) for xy in zip(rs.lon, rs.lat)]

    geo_df = GeoDataFrame(rs, crs=nodes.crs, geometry=geometry)

    return geo_df
