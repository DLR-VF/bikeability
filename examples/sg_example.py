import os

import matplotlib.pyplot as plt

from bikeability import bikeability
import geopandas as gpd
from bikeability import grid
from pathlib import Path
import matplotlib.pyplot as plt




project_path = os.path.abspath('../')
aggregation_boundaries = gpd.read_file(project_path+f"/data/sg_test.gpkg").to_crs(epsg='4326')

id_column = "h3_id"
h3_res = 9
download = True
verbose = 1
#agg_table = aggregation_boundaries[[id_column, "geometry"]]

agg_table = grid.create_h3_grid(aggregation_boundaries, res=h3_res)
agg_table.reset_index(names=id_column, inplace=True)

bikeability_gdf = bikeability.calc_bikeability(id_column, agg_table, download=download, verbose=verbose)
bikeability_gdf.to_file(project_path+f"/data/h3_{h3_res}_sg_test.gpkg")