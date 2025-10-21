import os
import sys

sys.path.insert(0, os.path.abspath(".."))
sys.setrecursionlimit(1500)


# -- Project information -----------------------------------------------------

project = "bikeability"
copyright = "2024 German Aerospace Center (DLR)"
author = "Simon Nieland, Michael Hardinghaus"

# The full version, including alpha/beta/rc tags
release = "1.0.3"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
# mock import all required + optional dependency packages because readthedocs
# does not have them installed
autodoc_mock_imports = [
    "geopandas",
    "matplotlib",
    "networkx",
    "numpy",
    "osgeo",
    "pandas",
    "rasterio",
    "requests",
    "scipy",
    "shapely",
    "sklearn",
]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.viewcode"]
language = "en"
needs_sphinx = "7"  # same value as pinned in /docs/requirements.txt
root_doc = "index"
source_suffix = ".rst"
templates_path = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_static_path = []
html_theme = "furo"
