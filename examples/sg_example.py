import os
from bikeability import bikeability
import geopandas as gpd
from bikeability import grid
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

project_path = os.path.abspath('../')
aggregation_boundaries = gpd.read_file(project_path+f"/data/bikeability_test.gpkg").to_crs(epsg='4326')

id_column = "h3_id"
date = '2021-10-28'
h3_res = 8
download = True
verbose = 1
store_temp_files = False

agg_table = grid.create_h3_grid(aggregation_boundaries, res=h3_res)
agg_table.reset_index(names=id_column, inplace=True)

bikeability_gdf = bikeability.calc_bikeability(id_column, agg_table, download=download, verbose=verbose)
bikeability_gdf.to_file(project_path+f"/data/h3_{h3_res}_sg_test.gpkg")
bikeability_gdf.plot(column="bikeability", cmap="Reds")
plt.show()

bikeability_gdf_2019 = bikeability.calc_bikeability(id_column, agg_table, download=download, store_tmp_files=True,
                                                    verbose=verbose,
                                                    date=date)
bikeability_gdf_2019.to_file(project_path+f"/data/h3_{h3_res}_muenchen_2019.gpkg")

bikeability_gdf_2019.plot(column="bikeability", cmap="Reds")
plt.show()
bikeability_difference_2019_now = bikeability_gdf.merge(bikeability_gdf_2019[['xid', 'bikeability']],
                                                        on="xid",
                                                        suffixes=('_2023', '_2019'))
bikeability_difference_2019_now["difference"] = bikeability_difference_2019_now["bikeability_2023"] - \
                                                bikeability_difference_2019_now["bikeability_2019"]

ax = bikeability_difference_2019_now.plot(figsize=(17, 15), column='difference', cmap='YlOrRd', legend=True)
plt.show()
