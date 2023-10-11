import sys
import os
project_path = os.path.abspath('../')
sys.path.append(project_path)

import geopandas as gpd
import math
from pyproj import CRS
from bikeability import settings
from sklearn.cluster import DBSCAN
#from geopy.distance import great_circle
from shapely.geometry import MultiPoint
from shapely.geometry import Point
from geopandas import GeoDataFrame
import pandas as pd
from matplotlib import pyplot as plt
#from geoalchemy2 import Geometry, WKTElement


def create_cycle_tracks(aggregation_units, network):
    cycle_tracks = network[network["highway"] == "cycleway"]
    cycle_tracks = cycle_tracks.overlay(aggregation_units, how="intersection")
    return cycle_tracks


def create_highway_buffers(aggregation_units, network):
    network = project_gdf(network)
    aggregation_units = project_gdf(aggregation_units)
    highway_buffer = network[(network["highway"] == "primary") |
                             (network["highway"] == "secondary") |
                             (network["highway"] == "tertiary")]
    highway_buffer = highway_buffer["geometry"].buffer(15)
    highway_buffer = gpd.GeoDataFrame(highway_buffer, geometry=0, crs=network.crs)
    highway_buffer = highway_buffer.rename_geometry("geometry")

    highway_buffer.reset_index(inplace=True)
    highway_buffer = highway_buffer.rename(columns= {'index':'lid'})
    #highway_buffer = highway_buffer.overlay(aggregation_units, how="union")

    #highway_buffer_union = highway_buffer["geometry"].buffer(15).unary_union
    #highway_buffer_union = gpd.GeoDataFrame(geometry=[highway_buffer_union], crs=network.crs, )
    #highway_buffer_union.to_file(f"{home_directory}/.bikeability/highway_buffers.gpkg", driver="GPKG")

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


def calc_green_share(aggregation_units, urban_green, store_tmp_files=False):
    aggregation_units = project_gdf(aggregation_units)
    aggregation_units["area_total"] = aggregation_units.area
    urban_green = project_gdf(urban_green)
    urban_green = urban_green[(urban_green.geometry.type == "MultiPolygon") |
                      (urban_green.geometry.type == "Polygon")]
    urban_green = urban_green["geometry"].unary_union
    urban_green_union = gpd.GeoDataFrame(geometry=[urban_green], crs=aggregation_units.crs)

    aggregation_units_intersected = urban_green_union.overlay(aggregation_units, how="intersection")
    aggregation_units_intersected["area_green"] = aggregation_units_intersected.area

    #aggregation_units_intersected["area_green"] = aggregation_units.area
    urban_green_share = aggregation_units.merge(aggregation_units_intersected[["xid", "area_green"]], on="xid",
                                                how="left").fillna(0)
    urban_green_share["urban_green_share"] =urban_green_share["area_green"]/urban_green_share["area_total"]

    if store_tmp_files:
        urban_green_share.to_file(f"{settings.tmp_directory}/green_share.gpkg", driver="GPKG")
        aggregation_units_intersected.to_file(f"{settings.tmp_directory}/urban_green_intersected.gpkg", driver="GPKG")
    return urban_green_share

def calc_node_density(nodes, aggregation_units, home_directory, store_tmp_files=False):
    nodes = project_gdf(nodes)
    aggregation_units = project_gdf(aggregation_units)
    aggregation_units["area_total"] = aggregation_units.area/1000000
    crossroads = cluster_intersections_to_crossroad(project_gdf(nodes))

    #calc crossroad density
    aggregation_units_node_count = aggregation_units.merge(aggregation_units.sjoin(crossroads).groupby('xid').size().rename('n_nodes').reset_index(),
                                                           how='left').fillna(0)
    aggregation_units_node_count["node_density"] = aggregation_units_node_count["n_nodes"]/\
                                                   aggregation_units_node_count["area_total"]
    if store_tmp_files:
        crossroads.to_file(f"{home_directory}/.bikeability/crossroads.gpkg", driver="GPKG")
        aggregation_units_node_count.to_file(f"{home_directory}/.bikeability/node_density.gpkg")
    return aggregation_units_node_count

def calc_shop_density(shops, aggregation_units, store_tmp_files=False):
    shops = project_gdf(shops)
    aggregation_units = project_gdf(aggregation_units)
    aggregation_units["area_total"] = aggregation_units.area/1000000

    #calc shop density
    aggregation_units_node_count = \
        aggregation_units.merge(aggregation_units.sjoin(shops).groupby('xid').size().rename('n_shops').reset_index(),
                                how="left").fillna(0)
    aggregation_units_node_count["shop_density"] = aggregation_units_node_count["n_shops"]/\
                                                   aggregation_units_node_count["area_total"]
    if store_tmp_files:
        aggregation_units_node_count.to_file(f"{settings.tmp_directory}/shop_density.gpkg")
    return aggregation_units_node_count

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

def calc_small_street_share(network, aggregation_units, store_tmp_files=False):

    aggregation_units = project_gdf(aggregation_units)
    network = network[['highway', 'geometry']]
    network = project_gdf(network)

    network_intersected = gpd.sjoin(network, aggregation_units, how='inner', predicate='intersects')
    #network_length = network_intersected.dissolve("xid").reset_index(names='xid')
    network_intersected["length_all_streets"] = network_intersected.length
    network_length = network_intersected.groupby(["xid"])['length_all_streets'].agg('sum').reset_index()


    network_length_small_streets_intersected = \
        gpd.sjoin(network[(network["highway"] == "residential") | (network["highway"] == "living_street")],
                  aggregation_units, how='inner', predicate='intersects')

    #network_length_small_streets = network_length_small_streets_intersected.dissolve("xid").reset_index(names='xid')

    network_length_small_streets_intersected["length_small_streets"] = network_length_small_streets_intersected.length
    network_length_small_streets = network_length_small_streets_intersected.groupby(["xid"])["length_small_streets"].agg('sum').reset_index()

    #network_length_small_streets["length_small_streets"] = network_length_small_streets.length
    small_streets_share = network_length.merge(network_length_small_streets[["xid", "length_small_streets"]], on="xid",
                                               how="left").fillna(0)
    small_streets_share["small_streets_share"] = small_streets_share["length_small_streets"]/ small_streets_share["length_all_streets"]

    small_streets_share = aggregation_units.merge(
        small_streets_share[['xid',
                             "length_all_streets",
                             "length_small_streets",
                             "small_streets_share",
                             ]],
        on='xid',
        how='left').fillna(0)

    if store_tmp_files:
        small_streets_share.to_file(f"{settings.tmp_directory}/small_streets_share.gpkg",
                                                      driver="GPKG")
    return small_streets_share[["xid", "length_all_streets", "length_small_streets","small_streets_share", "geometry"]]

def calc_share_cycling_infrastructure(network, aggregation_units, store_tmp_files=False):

    # create buffer of main streets
    main_street_buffer = create_highway_buffers(aggregation_units, network)

    #project to UTM
    aggregation_units = project_gdf(aggregation_units)
    network = project_gdf(network)

   #Select bicycle infrastructure
    cycling_network = network[(network["highway"] == "cycleway") |
                      (network["cycleway"] == "lane") |
                      (network["cycleway"] == "track") |
                      (network["cycleway:right"] == "lane") |
                      (network["cycleway:right"] == "track") |
                      (network["cycleway:right"] == "separate") |
                      (network["cycleway:left"] == "lane") |
                      (network["cycleway:left"] == "track") |
                      (network["cycleway:left"] == "separate") |
                      (network["cycleway:both"] == "lane") |
                      (network["cycleway:both"] == "track") |
                      (network["cycleway:both"] == "separate")]


    # spatial join of cycling network and main street buffers
    # result are edges of the network with cycling infrastructure

    cycling_network_buffer_intersected = gpd.sjoin(cycling_network[["highway",
                                                                    "cycleway",
                                                                    "cycleway:right",
                                                                    "cycleway:left",
                                                                    "cycleway:both",
                                                                    "geometry"
                                                                                ]],

                                                   main_street_buffer,
                                                   how='right',
                                                   predicate='crosses')

    cycling_network_buffer_intersected  = cycling_network_buffer_intersected [
                      (cycling_network_buffer_intersected["highway"] == "cycleway") |
                      (cycling_network_buffer_intersected["cycleway"] == "lane") |
                      (cycling_network_buffer_intersected["cycleway"] == "track") |
                      (cycling_network_buffer_intersected["cycleway:right"] == "lane") |
                      (cycling_network_buffer_intersected["cycleway:right"] == "track") |
                      (cycling_network_buffer_intersected["cycleway:right"] == "separate") |
                      (cycling_network_buffer_intersected["cycleway:left"] == "lane") |
                      (cycling_network_buffer_intersected["cycleway:left"] == "track") |
                      (cycling_network_buffer_intersected["cycleway:left"] == "separate") |
                      (cycling_network_buffer_intersected["cycleway:both"] == "lane") |
                      (cycling_network_buffer_intersected["cycleway:both"] == "track") |
                      (cycling_network_buffer_intersected["cycleway:both"] == "separate")]

    cycling_network_buffer_intersected = cycling_network_buffer_intersected[[
                                                                    "geometry",
                                                                    "lid",
                                                                 ]].drop_duplicates()

    # select main streets
    main_street_network = network[(network["highway"] == "primary") |
                            (network["highway"] == "secondary") |
                            (network["highway"] == "tertiary")]

    # now, we do not need the buffers anymore. so we merge our buffers with cycling infrastructure to the main street
    # network by id
    # select only main streets with bicycle infrastructure and write to file
    network_with_cycling_infrastructure = main_street_network.merge(cycling_network_buffer_intersected[["lid"]],
                                                                    on="lid",
                                                                    how="inner")


    main_street_network_intersected = gpd.overlay(main_street_network, aggregation_units,
                                                  how='union',
                                                  keep_geom_type=True)
    main_street_network_intersected["length_main_street"] = main_street_network_intersected.length
    main_street_network_intersected = main_street_network_intersected.groupby(["xid"])['length_main_street'].agg('sum').reset_index()

    if network_with_cycling_infrastructure.empty:
        network_with_cycling_infrastructure_share = main_street_network_intersected
        network_with_cycling_infrastructure_share["length_bike_infra"] = 0
        network_with_cycling_infrastructure_share["cycling_infra_share"] = 0
        network_with_cycling_infrastructure_share = aggregation_units.merge(
            network_with_cycling_infrastructure_share[['xid',
                                                       'cycling_infra_share',
                                                       'length_main_street',
                                                       'length_bike_infra']],
            on='xid',
            how='left').fillna(0)

    else:
        network_with_cycling_infrastructure = gpd.overlay(network_with_cycling_infrastructure, aggregation_units,
                                                      how="union",
                                                      keep_geom_type=True)

        network_with_cycling_infrastructure['length_bike_infra'] = network_with_cycling_infrastructure.length
        network_with_cycling_infrastructure_share = network_with_cycling_infrastructure.groupby(["xid"])['length_bike_infra'].agg('sum').reset_index()



    # merge and calculate shares
        network_with_cycling_infrastructure_share = network_with_cycling_infrastructure_share.merge(
            main_street_network_intersected[["xid", "length_main_street"]], on="xid", how="left").fillna(0)

        network_with_cycling_infrastructure_share["cycling_infra_share"] = \
            network_with_cycling_infrastructure_share["length_bike_infra"] / \
            network_with_cycling_infrastructure_share["length_main_street"]

        network_with_cycling_infrastructure_share = network_with_cycling_infrastructure_share.fillna(0)

        network_with_cycling_infrastructure_share = aggregation_units.merge(network_with_cycling_infrastructure_share[['xid',
                                                                            'cycling_infra_share',
                                                                            'length_main_street',
                                                                            'length_bike_infra']]   ,
                                                                        on='xid',
                                                                        how='left').fillna(0)
    if store_tmp_files:
        cycling_network.to_file(
            f"{settings.tmp_directory}/cycling_network.gpkg",
            driver="GPKG")

        main_street_buffer.to_file(
            f"{settings.tmp_directory}/highway_buffer.gpkg",
            driver="GPKG")

        cycling_network_buffer_intersected.to_file(
            f"{settings.tmp_directory}/highway_buffer_intersected.gpkg",
            driver="GPKG")

        network_with_cycling_infrastructure.to_file(
            f"{settings.tmp_directory}/main_street_network_network_with_cycling_infrastructure.gpkg",
            driver="GPKG")

        main_street_network.to_file(f"{settings.tmp_directory}/main_street_network.gpkg",
                                    driver="GPKG")
        main_street_network_intersected.to_file(f"{settings.tmp_directory}/main_street_network.gpkg",
                                                driver="GPKG")
        network_with_cycling_infrastructure_share.to_file(f"{settings.tmp_directory}/cycling_infra_share.gpkg",
                                                      driver="GPKG")

    return network_with_cycling_infrastructure_share[["xid",
                                  "length_main_street",
                                  "length_bike_infra",
                                  "cycling_infra_share",
                                  "geometry"]]

def cluster_intersections_to_crossroad(nodes, verbose=0):

    nodes["y"] = nodes["geometry"].y
    nodes["x"] = nodes["geometry"].x
    coords = nodes[['y', 'x']].values

    ##clustering
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

