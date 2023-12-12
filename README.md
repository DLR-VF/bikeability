<!-- PtAC documentation master file, created by
sphinx-quickstart on Fri Jul  9 10:40:37 2021.
You can adapt this file completely to your liking, but it should at least
contain the root `toctree` directive. -->

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/DLR-VF/bikeability/blob/master/LICENSE)
[![PyPI version](https://badge.fury.io/py/ultimodel.svg)](https://pypi.python.org/pypi/bikeability)
[![Documentation Status](https://readthedocs.org/projects/ultimodel/badge/?version=latest)](https://bikeability.readthedocs.io/en/latest/?badge=latest)
[![Cite-us](XXX)


# Bikeability

PtAC is a Python package to automatically compute walking
accessibilities from residential areas to public transport stops for the Sustainable Development Goal 11.2
defined by the United Nations. The goal aims to measure and monitor the proportion
of the population in a city that has convenient access to public transport
(see https://sdgs.un.org/goals/goal11). With this library users can download and process [OpenStreetMap](https://www.openstreetmap.org) (OSM)
street networks and population information worldwide. Based on this it is possible to calculate accessibilities
from population points to public transit stops based on minimum street network distance.

In order to calculate SDG 11.2.1 indicator the necessary input sources are
population information, public transit stops and city networks.
Worldwide population information can be downloaded via WMS 
from [World Settlement Footprint](https://www.nature.com/articles/s41597-020-00580-5)
(WSF) and converted
to points. Public transit stops can be obtained from
[OpenStreetMap (OSM)](https://wiki.openstreetmap.org/wiki/Public_transport) or
[General Transit Feed Specification (GTFS)](https://gtfs.org/) feeds (have a look at the examples if you want to know how this
works exactly). The street network can be downloaded and prepared for routing automatically within the library.

# Installation and Usage

Please see the [user guide](https://github.com/DLR-VF/PtAC/blob/master/docs/source/index.rst) 
for information about installation and usage.

# Examples

To get started with PtAC, read the user reference and see sample code and input data in
[examples repository](https://github.com/DLR-VF/PtAC-examples).

# Features

Bikeability is built on top of osmnx, geopandas, networkx.


* Download and prepare road networks and additional data from OpenStreetMap 


* Calculate indicators to derive bike-friendliness of certain regions


* Weight the indicators and generate a bikeability index


  
# Authors

* [Simon Nieland](https://github.com/SimonNieland)

# Contributors

* Michael Hardinghaus
* Marius Lehne

# Support

If you have a usage question, please contact us via email ([simon.nieland@dlr.de](mailto:simon.nieland@dlr.de),
[serra.yosmaoglu@dlr.de](mailto:serra.yosmaoglu@dlr.de)).

# License Information  

Bikeability is licensed under the MIT License . See the [LICENSE.md](https://github.com/DLR-VF/bikeability/blob/master/LICENSE.md) file for more information.

# Disclaimer

* This is a test version only and must not be given to any third party.

* We have chosen some links to external pages as we think they contain useful information. 
  However, we are not responsible for the contents of the pages we link to.

* The software is provided "AS IS".

* We tested the software, and it worked as expected. Nonetheless, we cannot guarantee it will work as you expect.

# References


## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
