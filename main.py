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
from sqlalchemy import create_engine

if __name__ == '__main__':

    region_of_interest = "test_0_v10"
    id_column = "sg_id"

    current_path = os.path.dirname(os.path.realpath(__file__))
    agg_table = gpd.read_file(current_path+f"\\data\sg_test.gpkg").to_crs(epsg='4326')


    download = True
    verbose = 0
    #timestamp = int(round(time.time()))
    agg_table = agg_table[[id_column, "geometry"]]
    agg_table = agg_table.rename(columns={id_column:"xid"})

    boundary_gdf = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[agg_table.unary_union])
    boundary = boundary_gdf.loc[0, 'geometry']
    logging.basicConfig(filename=r'%s/logs/bikeability.log' % current_path, filemode='a',
                        format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    print(f'generating bikeability indicator\n')
    logging.info('generating bikeability indicator based on aggregation units...\n')


    if not os.path.exists(f"{home_directory}/.bikeability"):
        os.makedirs(f"{home_directory}/.bikeability")

    if download:
        print("downloading street network and additional data from osm\n")
        logging.info('downloading street network and nodes ')
        network_gdfs = osm.get_network(boundary_gdf, network_type="bike", custom_filter=None, simplify=False, verbose=0)
        network = network_gdfs[1]
        nodes = network_gdfs[0][network_gdfs[0]["street_count"]>2]
        network[["maxspeed", "surface", "highway", "cycleway", "oneway", "length", "geometry"]].to_file(f"{home_directory}/.bikeability/network.gpkg", driver="GPKG")
        nodes[["x", "y", "street_count", "geometry"]].to_file(f"{home_directory}/.bikeability/nodes.gpkg", driver="GPKG")

        logging.info('downloading urban green')
        urban_green = osm.get_geometries(boundary, settings.bikeability_urban_green_tags, verbose)
        urban_green[["landuse", "natural", "leisure", "geometry"]].to_file(f"{home_directory}/.bikeability/urban_green.gpkg", driver="GPKG")

        logging.info('downloading bike shops')
        shops = osm.get_geometries(boundary, settings.bikeability_shops_tags, verbose)
        shops[["name", "geometry"]].to_file(f"{home_directory}/.bikeability/shops.gpkg", driver="GPKG")

        logging.info('downloading amenities \n')
        amenities = osm.get_geometries(boundary, settings.bikeability_amenity_tags, verbose)
        amenities[["geometry"]].to_file(f"{home_directory}/.bikeability/amenities.gpkg", driver="GPKG")

    else:

        try:
            print("loading street network and additional data from disk\n")
            logging.info('loading street network and additional data from disk')

            if os.path.exists(f"{home_directory}/.bikeability/amenities.gpkg"):
                amenities = gpd.read_file(f"{home_directory}/.bikeability/amenities.gpkg")
            shops = gpd.read_file(f"{home_directory}/.bikeability/shops.gpkg")
            leisure = gpd.read_file(f"{home_directory}/.bikeability/leisure.gpkg")
            urban_green = gpd.read_file(f"{home_directory}/.bikeability/landuse.gpkg")
            network = gpd.read_file(f"{home_directory}/.bikeability/network.gpkg")
            nodes = gpd.read_file(f"{home_directory}/.bikeability/nodes.gpkg")

        except Exception as e:
            print(e)
            print('Error: Can\'t find file or read data. Please download first\n')
            logging.info('Error: can\'t find file or read data. Please download first')
            sys.exit()

    cycle_tracks = util.create_cycle_tracks(agg_table, network)
    cycle_tracks.to_file(f"{home_directory}/.bikeability/cycle_tracks.gpkg", driver="GPKG")
    highway_buffers = util.create_highway_buffers(agg_table, network)
    highway_buffers.to_file(f"{home_directory}/.bikeability/highway_buffers.gpkg", driver="GPKG")
    parks = util.create_parks(agg_table, urban_green)
    parks["geometry"].to_file(f"{home_directory}/.bikeability/parks.gpkg", driver="GPKG")
    streets = util.create_steets(agg_table, network)
    streets.to_file(f"{home_directory}/.bikeability/streets.gpkg", driver="GPKG")

    nodes_utm = util.project_gdf(nodes)
    crossroads = util.cluster_intersections_to_crossroad(util.project_gdf(nodes), verbose=verbose)
    crossroads.to_file(f"{home_directory}/.bikeability/crossroads.gpkg", driver="GPKG")

    login = {"username": sys.argv[1],
             "password": sys.argv[2],
             "host": "vf-athene",
             "dbname": "user_simon_nieland",
             "schema": "bikeability_tests"
             }

    try:
        engine = create_engine('postgresql://%s:%s@%s:5432/%s' % (login["username"], login["password"],
                                                                  login["host"],
                                                                  login["dbname"]))
        conn = engine.connect()
    except Exception as e:
        logging.error(e)
        print(e)
        sys.exit()

    network = util.project_gdf(network)
    network.to_postgis(f"{region_of_interest}_network",
                          con=conn,
                          if_exists="replace",
                          schema=login["schema"])

    agg_table = util.project_gdf(agg_table)
    agg_table["area"] = agg_table.area
    agg_table.to_postgis(f"{region_of_interest}_boundaries",
                          con=conn,
                          if_exists="replace",
                          schema=login["schema"])

    cycle_tracks = util.project_gdf(cycle_tracks)
    cycle_tracks.to_postgis(f"{region_of_interest}_cycle_tracks",
                          con=conn,
                          if_exists="replace",
                          schema=login["schema"])

    urban_green.to_postgis(f"{region_of_interest}_green",
                     con=conn,
                     if_exists="replace",
                     schema=login["schema"])

    highway_buffers = util.project_gdf(highway_buffers)
    highway_buffers.to_postgis(f"{region_of_interest}_highway_buffers",
                     con=conn,
                     if_exists="replace",
                     schema=login["schema"])

    crossroads.to_postgis(f"{region_of_interest}_intersection_clustered",
                          con=conn,
                          if_exists="replace",
                          schema=login["schema"])
    parks.to_postgis(f"{region_of_interest}_parks",
                          con=conn,
                          if_exists="replace",
                          schema=login["schema"])
    urban_green.to_postgis(f"{region_of_interest}_green",
                     con=conn,
                     if_exists="replace",
                     schema=login["schema"])
    streets = util.project_gdf(streets)
    streets.to_postgis(f"{region_of_interest}_streets",
                     con=conn,
                     if_exists="replace",
                     schema=login["schema"])



    # command = 'Rscript'
    # path2script = r"%s/util/bikeability.R" % current_path
    # cmd_args = [args.host, args.dbname, args.user, args.password, args.location, args.agg_schema, args.srid]
    # cmd = [command, path2script] + cmd_args
    #
    # subprocess.check_output(cmd, universal_newlines=True)
    # logging.info('bikeability calculation successful\n')


    ##
    ## Straßentypen
    ##


    print("hi")









