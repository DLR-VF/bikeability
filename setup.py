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

INSTALL_REQUIRES = ['pandas==2.1.4',
                    'numpy==1.26.2',
                    'geopandas== 0.14.1',
                    'osmnx== 1.8.0',
                    'requests== 2.31.0',
                    'scikit-learn== 1.3.2',
                    'h3==3.7.6']

setuptools.setup(
    name='bikeability',
    version='1.0.0',
    author='German Aerospace Center - DLR (Simon Nieland)',
    author_email='simon.nieland@dlr.de',
    description='A Package to derive bike-friendliness from OpenStreetMap data ',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/DLR-VF/bikeability',
    project_urls={
        "Documentation": 'https://bikeability.readthedocs.io/',
        "Source": 'https://github.com/DLR-VF/bikeability',
        "Bug Tracker": "https://github.com/DLR-VF/bikeability/issues "
    },
    license='MIT License',
    packages=['bikeability'],
    python_requires='>=3.10',
    install_requires=INSTALL_REQUIRES)
