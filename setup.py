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


#import required packages from requirements file
with open("requirements.txt") as f:
    INSTALL_REQUIRES = [line.strip() for line in f.readlines()]

setuptools.setup(
    name='bikeability',
    version='0.0.2c',
    author='German Aerospace Center - DLR (Simon Nieland)',
    author_email='simon.nieland@dlr.de',
    description='A Package to derive bike-friendliness from OpenStreetMap Data ',
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
