[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/DLR-VF/bikeability/blob/master/LICENSE.md)
[![PyPI version](https://badge.fury.io/py/bikeability.svg)](https://pypi.python.org/pypi/bikeability)
![test](https://github.com/DLR-VF/bikeability/actions/workflows/test-bikeability.yml/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/bikeability/badge/?version=latest)](https://bikeability.readthedocs.io/en/latest/?badge=latest)
[![DOI](https://img.shields.io/badge/doi-10.5281%2Fzenodo.13318512-blue)](https://doi.org/10.5281/zenodo.13318512)


# Bikeability

"Bikeability" is a Python package to automatically compute bike-friendliness of specific areas.
With this library, users can download [OpenStreetMap](https://www.openstreetmap.org) (OSM)
 data and generate spatial indicators for bikeability (bike facilities on main streets, green share, share of secondary 
and tertiary roads, node density and bike shop density). Based on these indicators, it is possible to calculate a bikeability index 
([Hardinghaus et al. 2021](https://elib.dlr.de/144713/)) using a weighting approach derived from an expert survey.


# Installation and Usage

Please see the [user guide](https://github.com/DLR-VF/bikeability/blob/master/docs/index.rst) 
for information about installation and usage.

# Examples

To get started with bikeability, read the user reference and see the sample code and input data in the [examples repository](https://github.com/DLR-VF/bikeability-examples).

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
* María López Díaz

# Citation

If you use bikeability in your work, please cite the journal article:

Hardinghaus, Michael, et al. "[More than bike lanes—a multifactorial index of urban bikeability.](https://elib.dlr.de/144713/)" Sustainability 13.21 (2021): 11584.

# Support

If you have a usage question, please contact us via email ([simon.nieland@dlr.de](mailto:simon.nieland@dlr.de)).

# License Information  

Bikeability is licensed under the [MIT License](https://github.com/DLR-VF/bikeability/blob/master/LICENSE). See the [LICENSE](https://github.com/DLR-VF/bikeability/blob/master/LICENSE) file for more information.

# Disclaimer

* We have chosen some links to external pages as we think they contain useful information. 
  However, we are not responsible for the contents of the pages we link to.

* The software is provided "AS IS".

* We tested the software, and it worked as expected. Nonetheless, we cannot guarantee it will work as you expect.

# References

