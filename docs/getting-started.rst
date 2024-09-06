Getting Started
===============

Get Started in 4 Steps
----------------------

1. Install bikeability by following the :doc:`installation` guide.

2. Read the introduction below on this page.

3. Work through the bikebility Examples gallery for step-by-step tutorials and sample code.

4. Consult the :doc:`bikeability` for complete details on using the package.

Finally, if you're not already familiar with `OSMnx`_, `NetworkX`_ and `GeoPandas`_, we would advise to check out their functionality.

.. _Introducing bikeability:

Introducing bikeability
-----------------------


Configuration
^^^^^^^^^^^^^

You can configure bikebility using the :code:`settings` module. Here, you are able to change osm tags to download specific OSM data, the directory to store temporary data and the default projection.

Downloading OpenStreetMap Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bikeability uses `osmnx`_ to download street networks, green spaces and bike shops from OpenStreetMap. `osmnx`_ geocodes place names and addresses with the OpenStreetMap `Nominatim`_ API and enables the download of specific OSM data via Overpass API.


Amenities of bikeability
^^^^^^^^^^^^^^^^^^^^^^^^

Bikeability is a tool to automatically derive bike-related infrastructures from OpenStreetMap and calculate an index reflecting the bike-friendliness of a chosen area, the so-called "Bikeabilit Index". In general, four types of infrastructures are included in the index:

- the share of green-spaces,
- the percentage of bicycle infrastructures on main streets,
- the share of secondary and tertiary roads,
- and the density of bicycle-related shops (rental, buy, repair).


More Info
---------

All of this functionality is demonstrated step-by-step in the `bikeability Examples`_ gallery, and usage is detailed in the :doc:`bikeability`.

Frequently Asked Questions
--------------------------

*Are there any usage limitations?* Yes. Refer to the `Nominatim Usage Policy`_ and `Overpass Commons`_ documentation for usage limitations and restrictions that you must adhere to at all times. If you use an alternative Nominatim/Overpass instance, ensure you understand and obey their usage policies. If you need to exceed these limitations, consider installing your own hosted instance and setting bikebilityto use it.

.. _bikeability Examples: https://github.com/DLR-VF/bikeability-examples
.. _GeoPandas: https://geopandas.org
.. _NetworkX: https://networkx.org
.. _OpenStreetMap: https://www.openstreetmap.org
.. _Nominatim: https://nominatim.org
.. _Overpass: https://wiki.openstreetmap.org/wiki/Overpass_API
.. _features: https://wiki.openstreetmap.org/wiki/Map_features
.. _tags: https://wiki.openstreetmap.org/wiki/Tags
.. _elements: https://wiki.openstreetmap.org/wiki/Elements
.. _MultiDiGraphs: https://networkx.org/documentation/stable/reference/classes/multidigraph.html
.. _MultiGraph: https://networkx.org/documentation/stable/reference/classes/multigraph.html
.. _DiGraph: https://networkx.org/documentation/stable/reference/classes/digraph.html
.. _GeoDataFrames: https://geopandas.org/en/stable/docs/reference/geodataframe.html
.. _Overpass QL: https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL
.. _CRS: https://en.wikipedia.org/wiki/Coordinate_reference_system
.. _Elevation API: https://developers.google.com/maps/documentation/elevation
.. _Folium: https://python-visualization.github.io/folium/
.. _osmnx: https://osmnx.readthedocs.io/en/stable/
.. _Nominatim Usage Policy: https://operations.osmfoundation.org/policies/nominatim/
.. _Overpass Commons: https://dev.overpass-api.de/overpass-doc/en/preface/commons.html
