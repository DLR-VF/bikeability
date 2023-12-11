# =========================================================
# setup.py
# @author Simon Nieland
# @date 11.12.2023
# @copyright Institut fuer Verkehrsforschung,
#            Deutsches Zentrum fuer Luft- und Raumfahrt
# @brief setup module for bikeability
# =========================================================

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

'''
import required packages from requirements file
with open("requirements.txt") as f:
    INSTALL_REQUIRES = [line.strip() for line in f.readlines()]'''

setuptools.setup(
    name='bikeability',
    version='0.0.1',
    author='German Aerospace Center - DLR (Simon Nieland)',
    author_email='simon.nieland@dlr.de',
    description='A Package to derive bike-friendliness of spatial areas',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/DLR-VF/bikeability',
    project_urls = {
        "Documentation": 'https://bikeability.readthedocs.io/',
        "Source": 'https://github.com/DLR-VF/bikeability',
        "Bug Tracker": "https://github.com/DLR-VF/bikeability/issues "
    },
    license='MIT',
    packages=['bikeability'],
    install_requires=['pandas==2.1',
                      'numpy==1.26',
                      'geopandas== 0.14',
                      'shapely== 2.0',
                      'osmnx== 1.8',
                      'networkx== 3.2',
                      'requests== 2.31',
                      'scikit-learn== 1.3',
                      'scipy== 1.11',
                      'h3'])