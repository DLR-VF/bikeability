import bikeability.grid as grid
import bikeability.bikeability as bikeability
import geopandas as gpd
import os
from matplotlib import pyplot as plt

download = True
verbose = 1
id_column = 'h3_id'
store_temp_files = False

project_path = os.path.abspath('../')
aggregation_boundaries = gpd.read_file(project_path+f"/data/AWK_AH21_25833.shp").to_crs(epsg='4326')
h3_test = grid.create_h3_grid(aggregation_boundaries, res=8)
h3_test.plot()
h3_test = h3_test.reset_index(names=id_column)
plt.show()

h3_bikeability = bikeability.calc_bikeability(id_column, h3_test, download=download,
                                                           verbose=verbose,
                                                           store_tmp_files=store_temp_files)
h3_bikeability.plot(column="bikeability")

plt.show()
print("hi")