import sys
import os
import logging

from bikeability import osm
import geopandas
from bikeability import settings
from pathlib import Path
from bikeability import util
import numpy as np
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)

sys.path.append(os.getcwd())
home_directory = Path.home()


def main_streets(network: geopandas.GeoDataFrame):
    """
    Extracts main street network from osm street network

    :type network: street network from osmnx
    :return: main street network
    """
    main_street_network = network[(network["highway"] == "primary") |
                                  (network["highway"] == "secondary") |
                                  (network["highway"] == "tertiary")]
    return main_street_network


def cycling_network(network: geopandas.GeoDataFrame):
    """
    Extracts cycling network from osm street network

    :type network: street network from osmnx
    :return: cycling network
    """
    cycling_network_gdf = network[(network["highway"] == "cycleway") |
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
    return cycling_network_gdf


def cycle_tracks_per_agg_unit(aggregation_units: geopandas.GeoDataFrame,
                              network: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
    """
    Intersects cycle tracks with aggregation units


    :param aggregation_units: Given aggregation units
    :param network: network data set
    :return: cycle tracks per aggreation unit
    """
    cycle_tracks = network[network["highway"] == "cycleway"]
    cycle_tracks = cycle_tracks.overlay(aggregation_units, how="intersection")
    return cycle_tracks


def steets_per_agg_unit(aggregation_units, network):
    """
    Intersects street network with aggregation units


    :param aggregation_units: Given aggregation units
    :param network: network data set
    :return: cycle tracks per aggreation unit
    """
    streets = network[(network["highway"] == "primary") |
                      (network["highway"] == "secondary") |
                      (network["highway"] == "tertiary") |
                      (network["highway"] == "residential") |
                      (network["highway"] == "living_street") |
                      (network["highway"] == "motorway") |
                      (network["highway"] == "trunk")]
    streets = streets[["highway", "oneway", "surface", "geometry"]]
    streets = streets.overlay(aggregation_units, how="intersection")
    return streets


def main_street_buffer(network):
    """
    Generates 15m buffer of main streets

    :type network: street network from osmnx
    :return: buffer of main streets (15 m)
    """
    network = util.project_gdf(network)
    main_streets_buffer = main_streets(network)
    main_streets_buffer = main_streets_buffer["geometry"].buffer(15)
    main_streets_buffer = geopandas.GeoDataFrame(main_streets_buffer, geometry=0, crs=network.crs)
    main_streets_buffer = main_streets_buffer.rename_geometry("geometry")
    main_streets_buffer.reset_index(inplace=True)
    main_streets_buffer = main_streets_buffer.rename(columns={'index': 'lid'})
    return main_streets_buffer


def share_green_spaces(aggregation_units: geopandas.GeoDataFrame,
                       green_spaces: geopandas.GeoDataFrame,
                       store_tmp_files: bool = False) -> geopandas.GeoDataFrame:
    aggregation_units = util.project_gdf(aggregation_units)
    aggregation_units["area_total"] = aggregation_units.area
    if not green_spaces.empty:
        green_spaces = util.project_gdf(green_spaces)
    green_spaces = green_spaces[(green_spaces.geometry.type == "MultiPolygon") |
                                (green_spaces.geometry.type == "Polygon")]
    green_spaces = green_spaces["geometry"].unary_union
    green_spaces_union = geopandas.GeoDataFrame(geometry=[green_spaces], crs=aggregation_units.crs)

    aggregation_units_intersected = green_spaces_union.overlay(aggregation_units, how="intersection")
    aggregation_units_intersected["area_green"] = aggregation_units_intersected.area

    green_spaces_share = aggregation_units.merge(aggregation_units_intersected[["xid", "area_green"]], on="xid",
                                                 how="left").fillna(0)
    green_spaces_share["green_spaces_share"] = green_spaces_share["area_green"] / green_spaces_share["area_total"]

    if store_tmp_files:
        green_spaces_share.to_file(f"{settings.tmp_directory}/green_share.gpkg", driver="GPKG")
        aggregation_units_intersected.to_file(f"{settings.tmp_directory}/green_spaces_intersected.gpkg", driver="GPKG")
    return green_spaces_share


def node_density(nodes, aggregation_units, store_tmp_files=False):
    nodes = util.project_gdf(nodes)
    aggregation_units = util.project_gdf(aggregation_units)
    aggregation_units["area_total"] = aggregation_units.area / 1000000
    crossroads = util.cluster_intersections_to_crossroad(util.project_gdf(nodes))
    # calc crossroad density
    aggregation_units_node_count = aggregation_units.merge(
        aggregation_units.sjoin(crossroads).groupby('xid').size().rename('n_nodes').reset_index(),
        how='left').fillna(0)
    aggregation_units_node_count["node_density"] = aggregation_units_node_count["n_nodes"] / \
                                                   aggregation_units_node_count["area_total"]
    if store_tmp_files:
        crossroads.to_file(f"{settings.tmp_directory}/crossroads.gpkg", driver="GPKG")
        aggregation_units_node_count.to_file(f"{settings.tmp_directory}/node_density.gpkg")
    return aggregation_units_node_count


def shop_density(shops, aggregation_units, store_tmp_files=False):
    shops = util.project_gdf(shops)
    aggregation_units = util.project_gdf(aggregation_units)
    aggregation_units["area_total"] = aggregation_units.area / 1000000

    # calc shop density
    aggregation_units_node_count = \
        aggregation_units.merge(aggregation_units.sjoin(shops).groupby('xid').size().rename('n_shops').reset_index(),
                                how="left").fillna(0)
    aggregation_units_node_count["shop_density"] = aggregation_units_node_count["n_shops"] / \
                                                   aggregation_units_node_count["area_total"]
    if store_tmp_files:
        aggregation_units_node_count.to_file(f"{settings.tmp_directory}/shop_density.gpkg")
    return aggregation_units_node_count


def share_small_streets(network: geopandas.GeoDataFrame,
                        aggregation_units: geopandas.GeoDataFrame,
                        store_tmp_files: bool = False) -> geopandas.GeoDataFrame:
    """

    :param network: street network
    :param aggregation_units: geometries to aggregate
    :param store_tmp_files: if True: store all kinds of data into settings.tmp_directory
    :return: Geodataframe including share of small streets in the area
    """
    aggregation_units = util.project_gdf(aggregation_units)
    network = network[['highway', 'geometry']]
    network = util.project_gdf(network)

    network_intersected = geopandas.sjoin(network, aggregation_units, how='inner', predicate='intersects')
    # network_length = network_intersected.dissolve("xid").reset_index(names='xid')
    network_intersected["length_all_streets"] = network_intersected.length
    network_length = network_intersected.groupby(["xid"])['length_all_streets'].agg('sum').reset_index()

    network_length_small_streets_intersected = \
        geopandas.sjoin(network[(network["highway"] == "residential") | (network["highway"] == "living_street")],
                        aggregation_units, how='inner', predicate='intersects')

    # network_length_small_streets = network_length_small_streets_intersected.dissolve("xid").reset_index(names='xid')

    network_length_small_streets_intersected["length_small_streets"] = network_length_small_streets_intersected.length
    network_length_small_streets = network_length_small_streets_intersected.groupby(["xid"])[
        "length_small_streets"].agg('sum').reset_index()

    # network_length_small_streets["length_small_streets"] = network_length_small_streets.length
    small_streets_share = network_length.merge(network_length_small_streets[["xid", "length_small_streets"]], on="xid",
                                               how="left").fillna(0)
    small_streets_share["small_streets_share"] = small_streets_share["length_small_streets"] / small_streets_share[
        "length_all_streets"]

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
    return small_streets_share[["xid", "length_all_streets", "length_small_streets", "small_streets_share", "geometry"]]


def share_cycling_infrastructure(network: geopandas.GeoDataFrame,
                                 aggregation_units: geopandas.GeoDataFrame,
                                 store_tmp_files: bool = False) -> geopandas.GeoDataFrame:
    """

    :param network: Street network of the specified region
    :param aggregation_units: Geometries to aggregate the Index
    :param store_tmp_files: if True: store all kinds of pre-products to settings.tmp_directory
    :return: Geodataframe with share of cycling infrastructure on main streets
    """
    # create buffer of main streets
    main_street_buffer_gdf = main_street_buffer(network)

    # project to UTM
    aggregation_units = util.project_gdf(aggregation_units)
    network = util.project_gdf(network)

    # Select bicycle infrastructure
    cycling_network_gdf = cycling_network(network)

    # spatial join of cycling network and main street buffers
    # result are edges of the network with cycling infrastructure

    cycling_network_buffer_intersected = geopandas.sjoin(cycling_network_gdf[["highway",
                                                                              "cycleway",
                                                                              "cycleway:right",
                                                                              "cycleway:left",
                                                                              "cycleway:both",
                                                                              "geometry"
                                                                              ]],

                                                         main_street_buffer_gdf,
                                                         how='right',
                                                         predicate='crosses')

    cycling_network_buffer_intersected = cycling_network(cycling_network_buffer_intersected)
    cycling_network_buffer_intersected = cycling_network_buffer_intersected[[
        "geometry",
        "lid", ]].drop_duplicates()

    # select main streets
    main_street_network = main_streets(network)

    # now, we do not need the buffers anymore. so we merge our buffers with cycling infrastructure to the main street
    # network by id
    # select only main streets with bicycle infrastructure and write to file
    network_with_cycling_infrastructure = main_street_network.merge(cycling_network_buffer_intersected[["lid"]],
                                                                    on="lid",
                                                                    how="inner")

    main_street_network_intersected = geopandas.overlay(main_street_network, aggregation_units,
                                                        how='union',
                                                        keep_geom_type=True)
    main_street_network_intersected["length_main_street"] = main_street_network_intersected.length
    main_street_network_intersected = main_street_network_intersected.groupby(["xid"])['length_main_street'].agg(
        'sum').reset_index()

    if network_with_cycling_infrastructure.empty:
        network_with_cycling_infrastructure_share = aggregation_units[["xid"]]
        network_with_cycling_infrastructure_share['length_main_street'] = 0
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
        network_with_cycling_infrastructure = geopandas.overlay(network_with_cycling_infrastructure, aggregation_units,
                                                                how="union",
                                                                keep_geom_type=True)

        network_with_cycling_infrastructure['length_bike_infra'] = network_with_cycling_infrastructure.length
        network_with_cycling_infrastructure_share = network_with_cycling_infrastructure.groupby(["xid"])[
            'length_bike_infra'].agg('sum').reset_index()

        # merge and calculate shares
        network_with_cycling_infrastructure_share = network_with_cycling_infrastructure_share.merge(
            main_street_network_intersected[["xid", "length_main_street"]], on="xid", how="left").fillna(0)

        network_with_cycling_infrastructure_share["cycling_infra_share"] = \
            network_with_cycling_infrastructure_share["length_bike_infra"] / \
            network_with_cycling_infrastructure_share["length_main_street"]

        network_with_cycling_infrastructure_share = network_with_cycling_infrastructure_share.fillna(0)

        network_with_cycling_infrastructure_share = aggregation_units.merge(
            network_with_cycling_infrastructure_share[['xid',
                                                       'cycling_infra_share',
                                                       'length_main_street',
                                                       'length_bike_infra']],
            on='xid',
            how='left').fillna(0)
    if store_tmp_files:
        cycling_network_gdf.to_file(
            f"{settings.tmp_directory}/cycling_network.gpkg",
            driver="GPKG")

        main_street_buffer_gdf.to_file(
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
        # main_street_network_intersected.to_file(f"{settings.tmp_directory}/main_street_network.gpkg",
        #                                        driver="GPKG")
        network_with_cycling_infrastructure_share.to_file(f"{settings.tmp_directory}/cycling_infra_share.gpkg",
                                                          driver="GPKG")

    return network_with_cycling_infrastructure_share[["xid",
                                                      "length_main_street",
                                                      "length_bike_infra",
                                                      "cycling_infra_share",
                                                      "geometry"]]


def calc_bikeability(id_column: str,
                     agg_table: geopandas.GeoDataFrame,
                     download: bool = True,
                     verbose: int = 0,
                     network_gdf: geopandas.GeoDataFrame = None,
                     store_tmp_files: bool = False,
                     date: str = None) -> geopandas.GeoDataFrame:
    """

    :param id_column: unique id column
    :type id_column: str
    :param agg_table: Aggregation geometries to use. Should be a GeoDataFrame with polygon geometries.
    :type agg_table: geopandas.GeoDataFrame
    :param download:  if True, download all data from OSM. If False, use stored data in settings.temp_folder
    :type download: bool
    :param verbose: verbose
    :type verbose: integer
    :param network_gdf: use given network for calculation
    :type network_gdf: geopandas.GeoDataFrame
    :param store_tmp_files: store pre- products for debugging. data sets will be written in settings.temp_folder
    :type store_tmp_files: bool
    :return: calculated bikeability values for the given aggregation units

    """

    if not os.path.exists(settings.tmp_directory):
        os.makedirs(settings.tmp_directory)

    if not os.path.exists(settings.tmp_directory + "/logs"):
        os.makedirs(settings.tmp_directory + "/logs")

    logging.basicConfig(filename=r'%s/logs/bikeability.log' % settings.tmp_directory, filemode='a',
                        format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.INFO)

    if agg_table["geometry"].isna().sum() > 0:
        print(f'{agg_table["geometry"].isna().sum()} objects without geometry will be dropped')
        agg_table = agg_table.dropna()

    agg_table = agg_table[[id_column, "geometry"]]
    agg_table = agg_table.rename(columns={id_column: "xid"})

    boundary_gdf = geopandas.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[agg_table.unary_union])
    boundary = boundary_gdf.loc[0, 'geometry']

    print(f'Generating bikeability indicator\n')
    logging.info('generating bikeability indicator based on aggregation units...')

    if download:

        logging.info('downloading street network and nodes ')
        if verbose > 0:
            print("downloading street network and additional data from osm\n")

        network_gdfs = osm.get_network(boundary_gdf, network_type="bike", simplify=False, verbose=verbose, date=date)
        network = network_gdfs[1]

        # create lid column
        if 'lid' in network.columns:
            del network['lid']
        network.reset_index(inplace=True)
        network.reset_index(names="lid", inplace=True)
        # select only nodes which are connected to more than 2 edges
        nodes = network_gdfs[0][network_gdfs[0]["street_count"] > 2]
        # be sure, that all necessary columns exist in the dataset, if not, create them with nan values
        network = network.reindex(settings.colums_of_street_network, fill_value=np.nan, axis=1)

        # store network and nodes to disk
        network[settings.colums_of_street_network].to_file(f"{settings.tmp_directory}/network.gpkg", driver="GPKG")
        nodes[["x", "y", "street_count", "geometry"]].to_file(f"{settings.tmp_directory}/nodes.gpkg", driver="GPKG")

        logging.info('downloading green spaces')
        if verbose > 0:
            print("downloading green spaces from osm\n")
        try:
            green_spaces = osm.get_geometries(boundary, settings.bikeability_green_spaces_tags, verbose, date=date)
            green_spaces = green_spaces.reindex(settings.columns_of_green_spaces, fill_value=np.nan, axis=1)
            green_spaces[settings.columns_of_green_spaces].to_file(f"{settings.tmp_directory}/green_spaces.gpkg",
                                                                   driver="GPKG")
        except Exception as e:
            print(e)
            green_spaces = geopandas.GeoDataFrame(columns=settings.columns_of_green_spaces)
            green_spaces[settings.columns_of_green_spaces].to_file(f"{settings.tmp_directory}/green_spaces.gpkg",
                                                                   driver="GPKG")

        logging.info('downloading bike shops')
        if verbose > 0:
            print("downloading bike shops from osm\n")
        try:
            shops = osm.get_geometries(boundary, settings.bikeability_shops_tags, verbose, date=date)
            shops = shops.reindex(settings.columns_of_shops, fill_value=np.nan, axis=1)
            shops[settings.columns_of_shops].to_file(f"{settings.tmp_directory}/shops.gpkg", driver="GPKG")
        except Exception as e:
            print(e)
            shops = geopandas.GeoDataFrame(columns=settings.columns_of_shops)
            shops[settings.columns_of_shops].to_file(f"{settings.tmp_directory}/shops.gpkg", driver="GPKG")

        logging.info('all necessary data has been downloaded')
        print('all necessary data has been downloaded\n')

    else:

        try:
            print("loading street network and additional data from disk\n")
            logging.info('loading street network and additional data from disk')

            shops = geopandas.read_file(f"{settings.tmp_directory}/shops.gpkg")
            green_spaces = geopandas.read_file(f"{settings.tmp_directory}/green_spaces.gpkg")
            network = geopandas.read_file(f"{settings.tmp_directory}/network.gpkg")
            nodes = geopandas.read_file(f"{settings.tmp_directory}/nodes.gpkg")
            print('all necessary data has been loaded\n')

        except Exception as e:
            print(e)
            print('Error: Can\'t find file or read data. Please download first\n')
            logging.info('Error: can\'t find file or read data. Please download first')
            sys.exit()

        logging.info('all necessary data has been loaded from disk')

    logging.info('calculating share of cycling infrastructure')
    if verbose > 0:
        print('calculating share of cycling infrastructure\n')
    cycling_infrastructure_share = share_cycling_infrastructure(network, agg_table, store_tmp_files)

    logging.info('calculating share of small streets')
    if verbose > 0:
        print('calculating share of small streets\n')
    small_street_share = share_small_streets(network, agg_table, store_tmp_files)

    logging.info('calculating green share')
    if verbose > 0:
        print('calculating green share\n')
    green_share = share_green_spaces(agg_table, green_spaces, store_tmp_files)

    logging.info('calculating node density')
    if verbose > 0:
        print('calculating node density\n')
    node_dens = node_density(nodes, agg_table, store_tmp_files)

    logging.info('calculating shop density')
    if verbose > 0:
        print('calculating shop density calculated\n')

    if shops.empty:
        shop_dens = agg_table[['xid']]
        shop_dens['shop_density'] = 0
    else:
        shop_dens = shop_density(shops, agg_table, store_tmp_files)

    bikeability_gdf = green_share[["xid", "green_spaces_share", "geometry"]].merge(
        small_street_share[["xid", "small_streets_share"]], on="xid").merge(
        cycling_infrastructure_share[["xid", "cycling_infra_share"]], on="xid").merge(
        node_dens[["xid", "node_density"]], on="xid").merge(
        shop_dens[["xid", "shop_density"]], on="xid")

    # scaling
    bikeability_gdf["node_dens_scaled"] = bikeability_gdf["node_density"].div(78.27)
    bikeability_gdf["shop_dens_scaled"] = bikeability_gdf["shop_density"].div(5.153)

    bikeability_gdf.loc[bikeability_gdf["node_dens_scaled"] > 1, "node_dens_scaled"] = 1
    bikeability_gdf.loc[bikeability_gdf["shop_dens_scaled"] > 1, "shop_dens_scaled"] = 1

    bikeability_gdf["bikeability"] = bikeability_gdf["small_streets_share"].mul(0.1651828) \
                                     + bikeability_gdf["node_dens_scaled"].mul(0.2315489) \
                                     + bikeability_gdf["shop_dens_scaled"].mul(0.0817205) \
                                     + bikeability_gdf["cycling_infra_share"].mul(0.2828365) \
                                     + bikeability_gdf["green_spaces_share"].mul(0.1559295) \
        # + bikeability_gdf["shop_density"].mul(0.0817205)

    bikeability_gdf.to_file(f"{settings.tmp_directory}/bikeability.gpkg", driver="GPKG")
    print(f'bikeability values have been calculated for {agg_table.shape[0]} geometries\n')
    logging.info(f'bikeability values have been calculated for {agg_table.shape[0]} geometries')
    logging.info('process finished\n')
    return bikeability_gdf
