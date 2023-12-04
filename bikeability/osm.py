import sys
import os

import geopandas
import osmnx as ox
import bikeability.settings as settings
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)

"""Downloads pois, geometries and graphs from OSM"""

"""
@name : osm.py
@author : Simon Nieland
@date : 26.11.2023
@copyright : Institut fuer Verkehrsforschung, Deutsches Zentrum fuer Luft- und Raumfahrt
"""

project_path = os.path.abspath('../')
sys.path.append(project_path)
ox.settings.useful_tags_way = ox.settings.useful_tags_way + settings.additional_useful_tags_way


def get_network(polygon: geopandas.GeoDataFrame,
                network_type: str = "walk",
                custom_filter: str = None,
                simplify: bool = True,
                verbose: int = 0,
                date: str = None) -> geopandas.GeoDataFrame:
    """
    Download street network from osm via osmnx.

    :param date: date, on which to download the data
    :param simplify: simplify network
    :param polygon: boundary of the area from which to download the network (in WGS84)
    :type polygon: Geopandas.GeoDataFrame::POLYGON
    :param network_type: can be "all_private", "all", "bike", "drive", "drive_service",
        "walk" (see osmnx for description)
    :type network_type: str
    :param custom_filter: filter network (see osmnx for description)
    :type custom_filter: str
    :param verbose: Degree of verbosity (the higher, the more)
    :type verbose: int

    :return: OSM street network

    """

    if date is not None:
        ox.settings.overpass_settings = f"[out:json][timeout:200][date:'{date}T00:00:00Z']"
        if verbose > 0:
            print(f"date: {date}")
            print(f"overpass request setting: {ox.settings.overpass_settings}\n")
    bounds = polygon.unary_union.bounds
    network_gdfs = ox.graph_to_gdfs(
        ox.graph_from_bbox(
            north=bounds[3],
            south=bounds[1],
            east=bounds[2],
            west=bounds[0],
            custom_filter=custom_filter,
            network_type=network_type,
            simplify=simplify,
            retain_all=True
        )
    )
    return network_gdfs


def get_geometries(polygon, tags, verbose=1, date=None):
    """
    Download geometries from osm via osmnx.

    :param polygon: boundary of the area from which to download the data stets (in WGS84)
    :type polygon: Geopandas.GeoDataFrame::POLYGON
    :param tags: osm tags to download (example: {'landuse': ['grass', 'scrub', 'wood',],
                            'natural': ['scrub', 'wood', 'grassland', 'protected_area'],
                            'leisure': ['park']}
    :param verbose: degree of verbosity. the higher, the more.
    :param date: date: date, on which to download the data

    :return: OSM geometries

    """

    if date is not None:

        ox.settings.overpass_settings = f"[out:json][timeout:200][date:'{date}T00:00:00Z']"
        if verbose:
            print(f"date: {date}")
            print(f"overpass request setting: {ox.settings.overpass_settings}\n")
    return ox.features_from_polygon(polygon=polygon, tags=tags)


def get_network_from_xml(filepath: str, verbose: int = 0) -> geopandas.GeoDataFrame:
    """
    Load street network from osm from osm-xml files.

    :param filepath: path to xml file
    :type filepath: String
    :param verbose: degree of verbosity. The higher, the more

    :return: OSM street network

    """
    if verbose > 0:
        print("importing network from osm-xml")

    network_gdfs = ox.graph_to_gdfs(ox.graph_from_xml(filepath))

    return network_gdfs
