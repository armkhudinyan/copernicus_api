import pytest
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
from os import environ
from pathlib import Path

from src.copernicus_api import Sentinel1API


@pytest.fixture
def password():
    """Returns password if it exists as env variable otherwise raise error"""
    passw = environ.get("OPENEO_PASS")
    if passw:
        return passw
    raise ValueError("Set environment variable 'OPENEO_PASS'")


@pytest.fixture
def username():
    """Returns username if it exists as env variable otherwise raise error"""
    user = environ.get("OPENEO_USER")
    if user:
        return user
    raise ValueError("Set environment variable 'OPENEO_USER'")


@pytest.fixture
def api_instance(username, password):
    # Initialize your API instance with retrieved credentials
    return Sentinel1API(username=username, password=password)


@pytest.fixture
def products(api_instance):
    # Perform a query with some parameters
    start_time = "2023-01-01"
    end_time = "2023-01-15"
    products = api_instance.query(start_time=start_time,
                                  end_time=end_time,
                                  prod_type='GRDM' # To avoid very large files
                                )
    return products


class TestDownload:

    def test_query(self, products):
        # Ensure that the result is a DataFrame
        assert isinstance(products, pd.DataFrame)

    def test_download_all(self, api_instance, products):
        # Mock output directory
        out_dir = Path(__file__).parent.parent / 'data/test_outfiles'

        # Perform download for just 2 samples
        api_instance.download_all(products[:2], out_dir)

        # Add assertions to check if the files are downloaded properly
        assert (out_dir / f"{products.iloc[0]['Name']}.zip").exists()
        assert (out_dir / f"{products.iloc[1]['Name']}.zip").exists()