import sys
import os

import pandas as pd

project_path = os.path.abspath('../')
sys.path.append(project_path)
from bikeability import bikeability
import geopandas as gpd
from pathlib import Path
import matplotlib.pyplot as plt


slice_from = 0
slice_to = 62
project_path = os.path.abspath('../')
boundaries = gpd.read_file(project_path + f"/data_iroutecargobike/boundaries3.shp",
                           crs=25832,
                           rows=slice(slice_from, slice_to)).to_crs(
                           epsg='4326')

#boundaries = gpd.read_file(project_path + f"/data3/boundaries2.shp").to_crs(
#            epsg='4326')

shapes = [#['gps_tracks_metadata_anonym_export_filtallBuff20.shp', 'FID'],
          #['AltRouteGHspdata_all2Buff20.shp', 'fid'],
          #['AltRouteGHtrack_all_allBuff20_new.shp', 'FID'],
          #['AltRouteORSspdata_allBuff20.shp', 'FID'],
          #['AltRouteORStrack_all_allBuff20.shp', 'FID'],
          #['snapped_roads_format_together_sp_AllBuff20.shp', 'FID'],
          ['Directions_reproj_buffered.shp', 'FID']
          ]


download = True
verbose = 1
counter = 0
store_temp_files = False
for shape in shapes:
    #aggregation_boundaries = gpd.read_file(project_path + f"/data3/{shape[0]}").to_crs(
    #        epsg='4326')
    gdf_list = []
    for index, row in boundaries.iterrows():
        hi = row.to_frame().T
        boundary = gpd.GeoDataFrame(geometry=row.to_frame().T['geometry'], crs=4326)
        aggregation_boundaries = gpd.read_file(project_path + f"/data_iroutecargobike/{shape[0]}", mask=boundary).to_crs(4326)
        if aggregation_boundaries.empty:
            continue
        aggregation_boundaries = aggregation_boundaries[[shape[1], 'geometry']]
        id_column = shape[1]
        print(f'number of elements: {aggregation_boundaries.shape[0]}')


        agg_table = aggregation_boundaries[[id_column, "geometry"]]
        print(f'processing file: {shape[0]}')
        print(f'{agg_table["geometry"].isna().sum()} objects without geometry')
        agg_table = agg_table.dropna()
        print('..dropped')
        #if counter == 0:
        bikeability_gdf = bikeability.calc_bikeability(id_column, agg_table, download=download,
                                                           verbose=verbose,
                                                           store_tmp_files=store_temp_files)
        #else:
        #    bikeability_gdf = bikeability.calc_bikeability(id_column, agg_table, download=False,
        #                                                   store_tmp_files=store_temp_files)
        gdf_list.append(bikeability_gdf.to_crs(25832))
        #counter = counter + 1
    bikeability_gdf_all = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))




    bikeability_gdf_all.to_file(project_path + f"/data_iroutecargobike/"
                                               f"{shape[0].split('.')[0]}{slice_from}_{slice_to}_bikeability.gpkg",
                                driver="GPKG")