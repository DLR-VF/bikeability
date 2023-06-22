import os
from bikeability import bikeability
import geopandas as gpd
from pathlib import Path
home_directory = Path.home()

if __name__ == '__main__':

    id_column = "track_id"
    download = False
    verbose = 1
    current_path = os.path.dirname(os.path.realpath(__file__))
    agg_table = gpd.read_file(current_path+f"\\data\cargo_test_berlin_2.gpkg").to_crs(epsg='4326')
    agg_table = agg_table[[id_column, "person_id", "geometry"]]
    bikeability_gdf = bikeability.calc_bikeability(id_column, agg_table, download=download, verbose=verbose)

