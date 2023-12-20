import logging
from pathlib import Path
home_directory = Path.home()

default_crs = "epsg:4326"

bikeability_green_spaces_tags = {'landuse': ['grass', 'scrub', 'wood', 'meadow', 'forest', 'village_green', \
                                              'farmland', 'conservation', 'orchard', 'recreation_ground', 'vinyard'],
                            'natural': ['scrub', 'wood', 'grassland', 'protected_area'],
                            'leisure': ['park']}

bikeability_shops_tags = {'shop': ['bicycle'], 'amenity': ['bike_rental']}

additional_useful_tags_way = ['surface', 'cycleway:both', 'lid', 'cycleway', 'cycleway:left', 'cycleway:right']

colums_of_street_network = ["lid",
                            "maxspeed",
                            "surface",
                            "highway",
                            "cycleway",
                            "cycleway:right",
                            "cycleway:left",
                            "cycleway:both",
                            "oneway",
                            "length",
                            "geometry"]

columns_of_green_spaces = ["landuse", "natural", "leisure", "geometry"]
columns_of_shops = ["name", "geometry", "shop"]
tmp_directory = f"{home_directory}/.bikeability"
log_level = logging.INFO
log_name = ("bikeability")
log_filename = (f"{tmp_directory}/{log_name}")
log_console = True
log_file = False

