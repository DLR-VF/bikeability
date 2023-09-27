
default_crs = "epsg:4326"

bikeability_urban_green_tags = {'landuse': ['grass', 'scrub', 'wood', 'meadow', 'forest', 'village_green', \
                                              'farmland', 'conservation', 'orchard', 'recreation_ground', 'vinyard'],
                            'natural': ['scrub', 'wood', 'grassland', 'protected_area'],
                            'leisure': ['park']}
bikeability_shops_tags = {'shop': ['bicycle'], 'amenity': ['bike_rental']}
#bikeability_amenity_tags = {'amenity': 'bike_rental'}

additional_useful_tags_way = ['surface', 'cycleway:both', 'lid', 'cycleway', 'cycleway:left', 'cycleway:right']

colums_of_street_network = ["lid", "maxspeed", "surface", "highway",
                 "cycleway",
                 "cycleway:right",
                 "cycleway:left",
                 "cycleway:both",
                 "oneway", "length", "geometry"]

columns_of_urban_green = ["landuse", "natural", "leisure", "geometry"]

columns_of_shops = ["name", "geometry", "shop"]
