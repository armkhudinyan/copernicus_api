# copernicus_api
Copernicus API makes searching and downloading of Copernicus Sentinel mission images from
[Copernicus Data Space Ecosystem (CDSE)](https://dataspace.copernicus.eu/) easy.

Current supported missions:
  - SENTINEL-1
  - SENTINEL-2
  - SENTINEL-3
  - SENTINEL-5P
  - SENTINEL-6

## Installation Guide
1. Clone the repository

    ```
    git clone git@github.com:armkhudinyan/copernicus_api.git
    cd copernicus_api
    ```

2. Install the side packages in the currently active python env, using conda:

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

footprint = to_openeo_wkt('path/to/search_polygon.geojson')
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