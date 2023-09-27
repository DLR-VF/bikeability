import bikeability.grid as grid
import geopandas as gpd
import os

project_path = os.path.abspath('../')
aggregation_boundaries = gpd.read_file(project_path+f"/data/sg_test.gpkg").to_crs(epsg='4326')
test = grid.create_h3_grid(aggregation_boundaries, res=9)

print("hi")