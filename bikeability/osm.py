#!/usr/bin/env python3
# coding:utf-8
import sys
import os
project_path = os.path.abspath('../')
sys.path.append(project_path)
import osmnx as ox
import bikeability.settings as settings
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)

ox.settings.useful_tags_way = ox.settings.useful_tags_way + settings.additional_useful_tags_way

"""Downloads pois, footprints and graphs from OSM"""

"""
@name : osm.py
@author : Simon Nieland
@date : 26.07.2021
@copyright : Institut fuer Verkehrsforschung, Deutsches Zentrum fuer Luft- und Raumfahrt
"""


def get_network(polygon, network_type="walk", custom_filter=None, simplify=False, verbose=0, date=None):
    """
    Download street network from osm via osmnx.

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

    :return: OSM geometries

    """

    if date is not None:

        ox.settings.overpass_settings = f"[out:json][timeout:200][date:'{date}T00:00:00Z']"
        if verbose:
            print(f"date: {date}")
            print(f"overpass request setting: {ox.settings.overpass_settings}\n")
    return ox.features_from_polygon(polygon=polygon,
                                      tags=tags)

def get_network_from_xml(filepath, verbose=0):
    """
    Load street network from osm from osm-xml files.

    :param filepath: path to xml file
    :type filepath: String

    :return: OSM street network

    """
    if verbose>0:
        print("importing network from osm-xml")
        
    network_gdfs = ox.graph_to_gdfs(ox.graph_from_xml(filepath))

    return network_gdfs