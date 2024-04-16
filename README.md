# OData_API

![Tests](https://github.com/CoLAB-ATLANTIC/odata_api/actions/workflows/ci_utilities.yml/badge.svg)

OData Python API makes searching and downloading of Copernicus Sentinel mission images from
[Copernicus Data Space Ecosystem (CDSE)](https://dataspace.copernicus.eu/) easy.

Current supported missions:
  - SENTINEL-1
  - SENTINEL-2
  - SENTINEL-3
  - SENTINEL-5P
  - SENTINEL-6

## About OData
[OData](https://documentation.dataspace.copernicus.eu/APIs/OData.html) enables
access to Copernicus dataspace catalog via HTTPS messages. It is an
SO/IEC approved, OASIS standard , which is based on https RESTful Application
Programming Interfaces. It enables resources, which are identified by URLs and
defined in a data model, to be created and edited using simple HTTPS messages.


## Installation Guide
1. Clone the repository

    ```
    git clone git@github.com:armkhudinyan/copernicus_api.git
    cd copernicus_api
    ```

2. Install the side packages in the currently active python env, using pip:
    ```
    pip install -r requirements.txt
    ```
    using conda
    ```
    conda env update -f environment.yml
    ```

3. Run a test
    ```
    pytest test/test_download.py
    ```

## Usage

It offers an easy-to-use Python API.

Example for Sentinel-1 query and download:

```python
from src.copernicus_api import Sentinel1API
from src.utils import to_openeo_wkt

api = Sentinel1API('user', 'password')

footprint = to_openeo_wkt('path/to/search_polygon.geojson')
specific_attrs = {
  'relativeOrbitNumber': [52, 118, 145],
  'sliceNumber': [7, 18],
  'orbitDirection': ['ASCENDING']
  }

products = api.query(
  start_time = '2024-01-01',
  end_time='2024-01-15',
  prod_type='GRD',
  exclude='COG',
  wkt=footprint,
  orderby='desc',
  limit=20,
  **specific_attrs
  )
  api.download_all(products, out_dir='path/to/out_dir')
  ```

Example for Sentinel-2 query and download:

```python
from src.copernicus_api import Sentinel2API
from src.utils import to_openeo_wkt

api = Sentinel2API('user', 'password')

footprint = to_openeo_wkt('path/to/search_polygon.shp')
specific_attrs = {
    'cloudCover' : [0, 30],
    'tileId' : ['29SNB', '29TLE', '29TLE']
}

products = api.query(
  start_time = '2024-01-01',
  end_time='2024-01-15',
  prod_type='L1C',
  wkt=footprint,
  limit=20,
  **specific_attrs
  )
  api.download_all(products, out_dir='path/to/out_dir')
  ```

## Contributions
To contribute to the repository, please follow the guidelines in
[here](CONTRIBUTING.md)
