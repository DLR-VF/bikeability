import sys
import os
import logging
from bikeability import osm
import geopandas as gpd
from bikeability import settings
sys.path.append(os.getcwd())
from pathlib import Path
from bikeability import util
home_directory = Path.home()
import numpy as np

def calc_bikeability(id_column: str, agg_table: gpd.GeoDataFrame, download: bool = True, verbose: int = 0,
                     network_gdf: gpd.GeoDataFrame = None, store_tmp_files: bool = False) -> gpd.GeoDataFrame:
    """
    :param id_column: Network dataset to use (optional, if None is provided dataset will be downloaded from
        osm automatically)
    :type download:
    :param agg_table (geopandas.GeoDataFrame): Aggregation geometries to use. Should be a GeoDataFrame with polygon geometries.
    :param download (bool):  if True, download all data from OSM. If False, use stored data in settings.temp_folder
    :param verbose (integer): verbose
    :network_gdf (geopandas.GeoDataFrame): use given network for calculation
    :store_tmp_files (bool): store pre- products for debugging. data sets will be written in settings.temp_folder
    """

    if agg_table["geometry"].isna().sum() > 0:
        print(f'{agg_table["geometry"].isna().sum()} objects without geometry will be dropped')
        agg_table = agg_table.dropna()


    agg_table = agg_table[[id_column, "geometry"]]
    agg_table = agg_table.rename(columns={id_column:"xid"})

    boundary_gdf = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[agg_table.unary_union])
    boundary = boundary_gdf.loc[0, 'geometry']

    print(f'Generating bikeability indicator\n')
    logging.info('generating bikeability indicator based on aggregation units...')


    if not os.path.exists(settings.tmp_directory):
        os.makedirs(settings.tmp_directory)

    if not os.path.exists(settings.tmp_directory+"/logs"):
        os.makedirs(settings.tmp_directory+"/logs")

    logging.basicConfig(filename=r'%s/logs/bikeability.log' % settings.tmp_directory, filemode='a',
                        format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.DEBUG)

    if download:

        logging.info('downloading street network and nodes ')
        if verbose > 0:
            print("downloading street network and additional data from osm\n")
        if network_gdf is None:
            network_gdfs = osm.get_network(boundary_gdf, network_type="bike", custom_filter=None, simplify=False, verbose=0)
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

        logging.info('downloading urban green')
        if verbose > 0:
            print("downloading green spaces from osm\n")
        try:
            urban_green = osm.get_geometries(boundary, settings.bikeability_urban_green_tags, verbose)
            urban_green = urban_green.reindex(settings.columns_of_urban_green, fill_value=np.nan, axis=1)
            urban_green[settings.columns_of_urban_green].to_file(f"{settings.tmp_directory}/urban_green.gpkg", driver="GPKG")
        except Exception as e:
            print(e)
            urban_green = gpd.GeoDataFrame(columns=settings.columns_of_urban_green)
            urban_green[settings.columns_of_urban_green].to_file(f"{settings.tmp_directory}/urban_green.gpkg",
                                                                 driver="GPKG")

        logging.info('downloading bike shops')
        if verbose>0:
            print("downloading bike shops from osm\n")
        try:
            shops = osm.get_geometries(boundary, settings.bikeability_shops_tags, verbose)
            shops = shops.reindex(settings.columns_of_shops, fill_value=np.nan, axis=1)
            shops[settings.columns_of_shops].to_file(f"{settings.tmp_directory}/shops.gpkg", driver="GPKG")
        except Exception as e:
            print(e)
            shops = gpd.GeoDataFrame(columns=settings.columns_of_shops)
            shops[settings.columns_of_shops].to_file(f"{settings.tmp_directory}/shops.gpkg", driver="GPKG")

        logging.info('all necessary data has been downloaded')
        print('all necessary data has been downloaded\n')

    else:

        try:
            print("loading street network and additional data from disk\n")
            logging.info('loading street network and additional data from disk')

            shops = gpd.read_file(f"{settings.tmp_directory}/shops.gpkg")
            urban_green = gpd.read_file(f"{settings.tmp_directory}/urban_green.gpkg")
            network = gpd.read_file(f"{settings.tmp_directory}/network.gpkg")
            nodes = gpd.read_file(f"{settings.tmp_directory}/nodes.gpkg")
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
    share_cycling_infrastructure = util.calc_share_cycling_infrastructure(network, agg_table, store_tmp_files)


    logging.info('calculating share of small streets')
    if verbose > 0:
        print('calculating share of small streets\n')
    small_street_share = util.calc_small_street_share(network, agg_table, store_tmp_files)

    logging.info('calculating green share')
    if verbose > 0:
        print('calculating green share\n')
    green_share = util.calc_green_share(agg_table, urban_green, store_tmp_files)

    logging.info('calculating node density')
    if verbose > 0:
        print('calculating node density\n')
    node_density = util.calc_node_density(nodes, agg_table, store_tmp_files)

    logging.info('calculating shop density')
    if verbose > 0:
        print('calculating shop density calculated\n')

    if shops.empty:
        shop_density = agg_table[['xid']]
        shop_density['shop_density'] = 0
    else:
        shop_density = util.calc_shop_density(shops, agg_table, store_tmp_files)


    bikeability_gdf = green_share[["xid", "urban_green_share", "geometry"]].merge(
        small_street_share[["xid", "small_streets_share"]], on="xid").merge(
        share_cycling_infrastructure[["xid", "cycling_infra_share"]], on="xid").merge(
        node_density[["xid", "node_density"]], on="xid").merge(
        shop_density[["xid", "shop_density"]], on="xid")

    #scaling
    bikeability_gdf["node_dens_scaled"] = bikeability_gdf["node_density"].div(78.27)
    bikeability_gdf["shop_dens_scaled"] = bikeability_gdf["shop_density"].div(5.153)

    bikeability_gdf.loc[bikeability_gdf["node_dens_scaled"] > 1, "node_dens_scaled"] = 1
    bikeability_gdf.loc[bikeability_gdf["shop_dens_scaled"] > 1, "shop_dens_scaled"] = 1

    bikeability_gdf["bikeability"] = bikeability_gdf["small_streets_share"].mul(0.1651828)\
                                     + bikeability_gdf["node_dens_scaled"].mul(0.2315489)\
                                     + bikeability_gdf["shop_dens_scaled"].mul(0.0817205)\
                                     + bikeability_gdf["cycling_infra_share"].mul(0.2828365)\
                                     + bikeability_gdf["urban_green_share"].mul(0.1559295)\
                                     #+ bikeability_gdf["shop_density"].mul(0.0817205)

    bikeability_gdf.to_file(f"{settings.tmp_directory}/bikeability.gpkg", driver="GPKG")
    print(f'bikeability values have been calculated for {agg_table.shape[0]} geometries\n')
    logging.info(f'bikeability values have been calculated for {agg_table.shape[0]} geometries')
    logging.info('process finished\n')
    return bikeability_gdf
