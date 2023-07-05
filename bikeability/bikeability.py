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

def calc_bikeability(id_column, agg_table, download=True, verbose=0):
    project_path = os.path.abspath('../')
    agg_table = agg_table[[id_column, "geometry"]]
    agg_table = agg_table.rename(columns={id_column:"xid"})

    boundary_gdf = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[agg_table.unary_union])
    boundary = boundary_gdf.loc[0, 'geometry']
    logging.basicConfig(filename=r'%s/logs/bikeability.log' % project_path, filemode='a',
                        format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    print(f'Generating bikeability indicator\n')
    logging.info('generating bikeability indicator based on aggregation units...')


    if not os.path.exists(f"{home_directory}/.bikeability"):
        os.makedirs(f"{home_directory}/.bikeability")

    if download:
        if verbose > 0:
            print("downloading street network and additional data from osm\n")
        logging.info('downloading street network and nodes ')
        network_gdfs = osm.get_network(boundary_gdf, network_type="bike", custom_filter=None, simplify=False, verbose=0)
        network = network_gdfs[1]
        network.reset_index(inplace=True)
        network.reset_index(names="lid", inplace=True)
        nodes = network_gdfs[0][network_gdfs[0]["street_count"] > 2]
        network[["lid", "maxspeed", "surface", "highway",
                 "cycleway",
                 "cycleway:right",
                 "cycleway:left",
                 "cycleway:both",
                 "oneway", "length", "geometry"]].to_file(f"{home_directory}/.bikeability/network.gpkg", driver="GPKG")
        nodes[["x", "y", "street_count", "geometry"]].to_file(f"{home_directory}/.bikeability/nodes.gpkg", driver="GPKG")

        logging.info('downloading urban green')
        if verbose > 0:
            print("downloading green spaces from osm\n")
        urban_green = osm.get_geometries(boundary, settings.bikeability_urban_green_tags, verbose)
        urban_green[["landuse", "natural", "leisure", "geometry"]].to_file(f"{home_directory}/.bikeability/urban_green.gpkg", driver="GPKG")

        if verbose>0:
            print("downloading bike shops from osm\n")
        logging.info('downloading bike shops')
        shops = osm.get_geometries(boundary, settings.bikeability_shops_tags, verbose)
        shops[["name", "geometry", "shop"]].to_file(f"{home_directory}/.bikeability/shops.gpkg", driver="GPKG")

    else:

        try:
            print("loading street network and additional data from disk\n")
            logging.info('loading street network and additional data from disk')

            shops = gpd.read_file(f"{home_directory}/.bikeability/shops.gpkg")
            urban_green = gpd.read_file(f"{home_directory}/.bikeability/urban_green.gpkg")
            network = gpd.read_file(f"{home_directory}/.bikeability/network.gpkg")
            nodes = gpd.read_file(f"{home_directory}/.bikeability/nodes.gpkg")

        except Exception as e:
            print(e)
            print('Error: Can\'t find file or read data. Please download first\n')
            logging.info('Error: can\'t find file or read data. Please download first')
            sys.exit()

    logging.info('all necessary data has been downloaded')

    share_cycling_infrastructure = util.calc_share_cycling_infrastructure(network, agg_table, home_directory)
    if verbose > 0:
        print('share of cycling infrastructure calculated\n')
    logging.info('share of cycling infrastructure calculated')
    small_street_share = util.calc_small_street_share(network, agg_table, home_directory)
    if verbose > 0:
        print('share of small streets calculated\n')
    logging.info('share of small streets calculated')
    green_share = util.calc_green_share(agg_table, urban_green, home_directory)
    if verbose > 0:
        print('green share calculated\n')
    logging.info('green share calculated')
    node_density = util.calc_node_density(nodes, agg_table, home_directory)
    if verbose > 0:
        print('node density calculated\n')
    logging.info('node density calculated')
    shop_density = util.calc_shop_density(shops, agg_table, home_directory)
    if verbose > 0:
        print('shop density calculated\n')
    logging.info('shop density calculated')

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


    print(f'bikeability values have been calculated for {agg_table.shape[0]} geometries\n')
    logging.info('process finished\n')
    return bikeability_gdf
