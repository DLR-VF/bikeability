import os
import sys
import geopandas
import math
from pyproj import CRS
from bikeability import settings
import logging as lg
import datetime as dt
import unicodedata as ud
from contextlib import redirect_stdout
from pathlib import Path
from sklearn.cluster import DBSCAN
from shapely.geometry import MultiPoint
from shapely.geometry import Point
from geopandas import GeoDataFrame
import pandas as pd
import warnings

"""Utility functions for bikeability calculation"""

"""
@name : osm.py
@author : Simon Nieland
@date : 26.11.2023
@copyright : Institut fuer Verkehrsforschung, Deutsches Zentrum fuer Luft- und Raumfahrt
"""

project_path = os.path.abspath('../')
sys.path.append(project_path)

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)


# from geoalchemy2 import Geometry, WKTElement

def project_gdf(gdf: geopandas.GeoDataFrame,
                geom_col: str = "geometry",
                to_crs: str = None,
                to_latlong: bool = False) -> geopandas.GeoDataFrame:
    """
    Project a GeoDataFrame to the UTM zone appropriate for its geometries' centroid.

    The simple calculation in this function works well for most latitudes, but
    won't work for some far northern locations like Svalbard and parts of far
    northern Norway.

    :param geom_col: geometry column of the dataset
    :param gdf: the gdf to be projected
    :type gdf: Geopandas.GeoDataFrame
    :param to_crs: CRS code. if not None,project GeodataFrame to CRS
    :type to_crs: int
    :param to_latlong: If True, projects to latlong instead of to UTM
    :type to_latlong: bool
    :return projected_gdf: A projected GeoDataFrame
    :rtype projected_gdf: Geopandas.GeoDataFrame
    """
    assert len(gdf) > 0, "You cannot project an empty GeoDataFrame."

    # if gdf has no gdf_name attribute, create one now
    if not hasattr(gdf, "gdf_name"):
        gdf.gdf_name = "unnamed"

    # if to_crs was passed-in, use this value to project the gdf
    if to_crs is not None:
        projected_gdf = gdf.to_crs(to_crs)

    # if to_crs was not passed-in, calculate the centroid of the geometry to
    # determine UTM zone
    else:
        if to_latlong:
            # if to_latlong is True, project the gdf to latlong
            latlong_crs = settings.default_crs
            projected_gdf = gdf.to_crs(latlong_crs)

        else:
            # else, project the gdf to UTM
            # if GeoDataFrame is already in UTM, just return it
            if (gdf.crs is not None) and (gdf.crs.is_geographic is False):
                return gdf

            # calculate the centroid of the union of all the geometries in the
            # GeoDataFrame
            avg_longitude = gdf[geom_col].unary_union.centroid.x

            # calculate the UTM zone from this avg longitude and define the UTM
            # CRS to project
            utm_zone = int(math.floor((avg_longitude + 180) / 6.0) + 1)
            utm_crs = f"+proj = utm + datum = WGS84 + ellps = WGS84 + zone = {utm_zone} + units = m + type = crs"
            crs = CRS.from_proj4(utm_crs)
            epsg = crs.to_epsg()
            projected_gdf = gdf.to_crs(epsg)

    projected_gdf.gdf_name = gdf.gdf_name
    return projected_gdf


def get_centroids(cluster: object) -> tuple:
    """
    :param cluster: Point cluster
    :return:
    """
    centroid = (MultiPoint(cluster).centroid.x, MultiPoint(cluster).centroid.y)
    return tuple(centroid)


def cluster_intersections_to_crossroad(nodes: geopandas.GeoDataFrame,
                                       verbose: int = 0) -> geopandas.GeoDataFrame:
    """
    Clusters nodes of the street network into real crossroads
    :param nodes: nodes of the street network
    :param verbose: degree of verbosity
    :return: Geodataframe including real crossroads as Points
    """
    nodes["y"] = nodes["geometry"].y
    nodes["x"] = nodes["geometry"].x
    coords = nodes[['y', 'x']].values

    # clustering
    if verbose > 1:
        print('    performing clustering of intersections..')
    db = DBSCAN(eps=40, min_samples=1, n_jobs=-1).fit(coords)
    cluster_labels = db.labels_
    num_clusters = len(set(cluster_labels))
    if verbose > 1:
        print('    Number of crossroads: {}\n'.format(num_clusters))
    clusters = pd.Series([coords[cluster_labels == n] for n in range(num_clusters)])

    # get cluster centroids
    centermost_points = clusters.map(get_centroids)
    lats, lons = zip(*centermost_points)
    rep_points = pd.DataFrame({'lon': lons, 'lat': lats})
    rs = rep_points
    geometry = [Point(xy) for xy in zip(rs.lon, rs.lat)]

    geo_df = GeoDataFrame(rs, crs=nodes.crs, geometry=geometry)

    return geo_df

def ts(style="datetime", template=None):
    """
    Return current local timestamp as a string.

    Parameters
    ----------
    style : string {"datetime", "date", "time"}
        format the timestamp with this built-in style
    template : string
        if not None, format the timestamp with this format string instead of
        one of the built-in styles

    Returns
    -------
    ts : string
        local timestamp string
    """
    if template is None:
        if style == "datetime":
            template = "{:%Y-%m-%d %H:%M:%S}"
        elif style == "date":
            template = "{:%Y-%m-%d}"
        elif style == "time":
            template = "{:%H:%M:%S}"
        else:  # pragma: no cover
            msg = f"unrecognized timestamp style {style!r}"
            raise ValueError(msg)

    return template.format(dt.datetime.now().astimezone())


def log(message, level=None, name=None, filename=None):
    """
    Write a message to the logger.

    This logs to file and/or prints to the console (terminal), depending on
    the current configuration of settings.log_file and settings.log_console.

    Parameters
    ----------
    message : string
        the message to log
    level : int
        one of Python's logger.level constants
    name : string
        name of the logger
    filename : string
        name of the log file, without file extension

    Returns
    -------
    None
    """
    if level is None:
        level = settings.log_level
    if name is None:
        name = settings.log_name
    if filename is None:
        filename = settings.log_filename

    # if logging to file is turned on
    if settings.log_file:
        # get the current logger (or create a new one, if none), then log
        # message at requested level
        logger = _get_logger(level=level, name=name, filename=filename)
        if level == lg.DEBUG:
            logger.debug(message)
        elif level == lg.INFO:
            logger.info(message)
        elif level == lg.WARNING:
            logger.warning(message)
        elif level == lg.ERROR:
            logger.error(message)

    # if logging to console (terminal window) is turned on
    if settings.log_console:
        # prepend timestamp then convert to ASCII for Windows command prompts
        message = f"{ts()} {message}"
        message = ud.normalize("NFKD", message).encode("ascii", errors="replace").decode()

        try:
            # print explicitly to terminal in case Jupyter has captured stdout
            if getattr(sys.stdout, "_original_stdstream_copy", None) is not None:
                # redirect the Jupyter-captured pipe back to original
                os.dup2(sys.stdout._original_stdstream_copy, sys.__stdout__.fileno())
                sys.stdout._original_stdstream_copy = None
            with redirect_stdout(sys.__stdout__):
                print(message, file=sys.__stdout__, flush=True)
        except OSError:
            # handle pytest on Windows raising OSError from sys.__stdout__
            print(message, flush=True)  # noqa: T201


def _get_logger(level, name, filename):
    """
    Create a logger or return the current one if already instantiated.

    Parameters
    ----------
    level : int
        one of Python's logger.level constants
    name : string
        name of the logger
    filename : string
        name of the log file, without file extension

    Returns
    -------
    logger : logging.logger
    """
    logger = lg.getLogger(name)

    # if a logger with this name is not already set up
    if not getattr(logger, "handler_set", None):
        # get today's date and construct a log filename
        log_filename = Path(settings.logs_folder) / f'{filename}_{ts(style="date")}.log'

        # if the logs folder does not already exist, create it
        log_filename.parent.mkdir(parents=True, exist_ok=True)

        # create file handler and log formatter and set them up
        handler = lg.FileHandler(log_filename, encoding="utf-8")
        formatter = lg.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.handler_set = True

    return logger