# This is a sample Python script.

# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import sys
import os
import logging
from bikeability import osm
import geopandas as gpd
from bikeability import settings
sys.path.append(os.getcwd())
from pathlib import Path
import time
from bikeability import util
home_directory = Path.home()  #

if __name__ == '__main__':


    current_path = os.path.dirname(os.path.realpath(__file__))
    agg_table = gpd.read_file(current_path+f"\\data\sg_test_0.gpkg").to_crs(epsg='4326')
    agg_table = agg_table[["sg_id", "geometry"]]
    download = True
    verbose = 0
    timestamp = int(round(time.time()))


    boundary_gdf = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[agg_table.unary_union])
    boundary = boundary_gdf.loc[0, 'geometry']
    logging.basicConfig(filename=r'%s/logs/__osm_preprocessing.log' % current_path, filemode='a',
                        format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    print(f'generating bikeability indicator\n')
    logging.info('generating bikeability indicator based on aggregation units...\n')


    if not os.path.exists(f"{home_directory}/.bikeability"):
        os.makedirs(f"{home_directory}/.bikeability")

    if download:
        print("downloading necessary polygon data (landuse, leisure, etc..)\n")
        logging.info('downloading necessary polygon and road network data (landuse, leisure, etc..) of ways')
        network_gdfs = osm.get_network(boundary_gdf, network_type="all", custom_filter=None, simplify=False, verbose=0)
        network = network_gdfs[1]
        nodes = network_gdfs[0][network_gdfs[0]["street_count"]>2]
        network[["osmid", "maxspeed", "surface", "highway", "oneway", "length", "geometry"]].to_file(f"{home_directory}/.bikeability/network.gpkg", driver="GPKG")
        nodes[["x", "y", "street_count", "geometry"]].to_file(f"{home_directory}/.bikeability/nodes.gpkg", driver="GPKG")

        urban_green = osm.get_geometries(boundary, settings.bikeability_urban_green_tags, verbose)
        urban_green[["osmid", "landuse", "natural", "leisure", "geometry"]].to_file(f"{home_directory}/.bikeability/urban_green.gpkg", driver="GPKG")
        shops = osm.get_geometries(boundary, settings.bikeability_shops_tags, verbose)
        shops[["osmid", "name", "geometry"]].to_file(f"{home_directory}/.bikeability/shops.gpkg", driver="GPKG")
        amenities = osm.get_geometries(boundary, settings.bikeability_amenity_tags, verbose)
        if "osmid" in amenities.columns:
            amenities[["osmid", "geometry"]].to_file(f"{home_directory}/.bikeability/amenities.gpkg", driver="GPKG")

    else:
        if os.path.exists(f"{home_directory}/.bikeability/amenities.gpkg"):
            amenities = gpd.read_file(f"{home_directory}/.bikeability/amenities.gpkg")
        shops = gpd.read_file(f"{home_directory}/.bikeability/shops.gpkg")
        leisure = gpd.read_file(f"{home_directory}/.bikeability/leisure.gpkg")
        urban_green = gpd.read_file(f"{home_directory}/.bikeability/landuse.gpkg")
        network = gpd.read_file(f"{home_directory}/.bikeability/network.gpkg")
        nodes = gpd.read_file(f"{home_directory}/.bikeability/nodes.gpkg")

    cycle_tracks = util.create_cycle_tracks(agg_table, network)
    cycle_tracks.to_file(f"{home_directory}/.bikeability/cycle_tracks.gpkg", driver="GPKG")
    highway_buffers = util.create_highway_buffers(agg_table, network)
    highway_buffers.to_file(f"{home_directory}/.bikeability/highway_buffers.gpkg", driver="GPKG")
    parks = util.create_parks(agg_table, urban_green)
    parks["geometry"].to_file(f"{home_directory}/.bikeability/parks.gpkg", driver="GPKG")
    streets = util.create_steets(agg_table, network)
    streets.to_file(f"{home_directory}/.bikeability/streets.gpkg", driver="GPKG")
    crossroads = util.cluster_intersections_to_crossroad(util.project_gdf(nodes), verbose=verbose)
    crossroads.to_file(f"{home_directory}/.bikeability/crossroads.gpkg", driver="GPKG")
    ##
    ## Straßentypen
    ##


    print("hi")









