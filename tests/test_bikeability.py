"""
Unit tests for bikebability library
"""

import pathlib
import unittest
import time
import geopandas as gpd
import bikeability.grid as grid
import bikeability.bikeability as bikeability



class BikeabilityTest(unittest.TestCase):
    def set_up(self):
        self.data_path = str(pathlib.Path(__file__).parent.absolute())
        self.id_column = "sg_id"
        self.boundaries = gpd.read_file(self.data_path + "/data/bikeability_test.gpkg")
        self.boundaries = self.boundaries.rename(columns={self.id_column: "xid"})
        self.green_spaces = gpd.read_file(self.data_path + "/data/green_spaces.gpkg")
        self.network = gpd.read_file(self.data_path + "/data/network.gpkg")
        self.shops = gpd.read_file(self.data_path + "/data/shops.gpkg")
        self.nodes = gpd.read_file(self.data_path + "/data/nodes.gpkg")

        self.timestamp = int(round(time.time()))

    def test_create_h3_grid(self):
        self.set_up()
        df_h3_grid = grid.create_h3_grid(
            gdf=self.boundaries, res=10
        )
        value = df_h3_grid.count()
        self.assertEqual(value.values[0], 166)

    def test_share_green_spaces(self):
        self.set_up()
        green_share = bikeability.share_green_spaces(aggregation_units=self.boundaries,
                       green_spaces=self.green_spaces,
                       store_tmp_files=False)
        green_share = round(green_share["green_spaces_share"].values[0], 2)
        self.assertEqual(green_share, 0.17)

    def test_share_cycling_infrastructure(self):
        self.set_up()
        cycling_infa_share = bikeability.share_cycling_infrastructure(network=self.network,
                                                               aggregation_units=self.boundaries,
                                                               store_tmp_files=False)
        cycling_infa_share = round(cycling_infa_share["cycling_infra_share"].values[0], 2)
        self.assertEqual(cycling_infa_share, 0.95)

    def test_share_small_streets(self):
        self.set_up()
        small_street_share = bikeability.share_small_streets(network=self.network,
                                                             aggregation_units=self.boundaries,
                                                             store_tmp_files=False)
        small_street_share = round(small_street_share["small_streets_share"].values[0], 2)
        self.assertEqual(small_street_share, 0.38)

    def test_shop_density(self):
        self.set_up()
        shop_density = bikeability.shop_density(self.shops,
                                                aggregation_units=self.boundaries,
                                                store_tmp_files=False)
        shop_density = round(shop_density["shop_density"].values[0], 2)
        self.assertEqual(shop_density, 4.21)

    def test_node_density(self):
        self.set_up()
        node_density = bikeability.node_density(nodes=self.nodes,
                                               aggregation_units=self.boundaries)
        node_density = round(node_density["node_density"].values[0],2)
        self.assertEqual(node_density, 73.2)

    def test_cycling_network(self):
        self.set_up()
        cycling_network = bikeability.cycling_network(network=self.network)
        cycling_network = cycling_network.count()
        self.assertEqual(cycling_network.iloc[0], 1074)

    def test_main_street_buffer(self):
        self.set_up()
        main_street_buffer = bikeability.main_street_buffer(network=self.network)
        main_street_buffer = main_street_buffer.count()
        self.assertEqual(main_street_buffer.iloc[0], 882)

    def test_main_street_buffer_geom(self):
        self.set_up()
        main_street_buffer = bikeability.main_street_buffer(network=self.network)
        geom_type = main_street_buffer['geometry'].geom_type.unique()[0]
        self.assertEqual(geom_type, "Polygon")


if __name__ == "__main__":
    unittest.main()
