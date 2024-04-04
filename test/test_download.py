import pandas as pd
from dotenv import load_dotenv
load_dotenv()
import tempfile
from os import environ
from pathlib import Path

from src.copernicus_api import Sentinel1API


class TestDownload:

    username = environ.get("OPENEO_USER")
    password = environ.get("OPENEO_PASS")

    def api_instance(self):
        # Initialize the API instance
        assert self.username
        assert self.password
        return Sentinel1API(username=self.username, password=self.password)

    def products(self):
        # Perform a query with some parameters
        start_time = "2023-01-01"
        end_time = "2023-01-15"
        api = self.api_instance()
        products = api.query(start_time=start_time,
                             end_time=end_time,
                             prod_type='GRDM' # To avoid very large files
                            )
        return products

    def test_query(self):
        products = self.products()
        # Ensure that the result is a DataFrame
        assert isinstance(products, pd.DataFrame)

    def test_download_all(self):
        # download test files in temporary output directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Query the products
            products = self.products()
            # Perform download for just 2 samples
            self.api_instance().download_all(products[:2], Path(tmp_dir))

            # Add assertions to check if the files are downloaded properly
            assert (Path(tmp_dir) / f"{products.iloc[0]['Name']}.zip").exists()
            assert (Path(tmp_dir) / f"{products.iloc[1]['Name']}.zip").exists()
