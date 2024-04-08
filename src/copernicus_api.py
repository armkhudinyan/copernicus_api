"""This is an Python API accomodating search and download of Copernicus Sentinel
mission data products."""


from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from abc import ABC, abstractmethod
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import requests

from .exceptions import (AttributeNotFoundError,
                         TokenGenerationError,
                         QueryError)


CATALOG_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection"
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
DOWNLOAD_URL = "https://zipper.dataspace.copernicus.eu/odata/v1/Products"


class CopernicusDataspaceAPI(ABC):
    """Class to connect to Datascpace Copernicus, search and download imagery.

    Parameters
    ----------
    user : string
        username for Copernicus dataspace
    password : string
        password for Copernicus dataspace
    mission : string, optional
        Current supported missions:
        SENTINEL-1
        SENTINEL-2
        SENTINEL-3
        SENTINEL-5P
        SENTINEL-6
    """

    def __init__(
            self,
            username: str,
            password: str,
        ) -> None:
        self.username = username
        self.password = password

    @property
    @abstractmethod
    def mission(self) -> str:
        """Mission name"""
        return NotImplementedError

    @property
    @abstractmethod
    def prod_types(self) -> list[str]:
        """List of keywords to match specific product types from product name"""
        raise NotImplementedError

    def _get_access_token(self) -> str:
        data = {
            "client_id": "cdse-public",
            "username": self.username,
            "password": self.password,
            "grant_type": "password",
        }
        try:
            r = requests.post(TOKEN_URL, data=data, timeout=100)
            r.raise_for_status()
        except Exception as e:
            raise TokenGenerationError(
                    f"Access token creation failed. Error: {e} \n"
                    f"\tMake sure your login credentials are correct for"
                    " https://dataspace.copernicus.eu/")
        return r.json()["access_token"]

    @staticmethod
    def __add_attrs_to_df(product: pd.Series) -> pd.Series:
        "Extracts Sentinel product attributes and add to the DataFrame"
        attributes = product.get('Attributes', [])
        for attr in attributes:
            product[attr['Name']] = attr['Value']
        return product

    def query(
            self,
            *,
            start_time: str,
            end_time: str,
            prod_type: str | None = None,
            exclude: str | None = None,
            footprint: str | None = None,
            orderby: str | None = None,
            limit: int | None = None,
            **kwargs: list[int] | list[float] | list[str]
        ) -> pd.DataFrame:
        """
        Query Copernicus DataSpace API for products matching specified criteria.

        Parameters:
        start_time : str
            Start time of the query period in '%Y-%m-%d' format.
        end_time : str
            End time of the query period in '%Y-%m-%d' format.
        prod_type : str, optional
            Keyword for product type match in the prod name. Must be one of the
            supported product types. To check the available options call
            `prod_types` attribute of instantiated CopernicusDataspaceAPI class.
        footprint : str, optional
            Well-Known Text representation of the spatial geometry
            NOTE:
            1. MULTIPOLYGON is currently not supported.
            2. Polygon must start and end with the same point.
            3. Coordinates must be given in EPSG 4326
        orderby : str, optional
            Sort order by acquizition time. Can be 'asc' or 'desc'.
        limit : int, optional
            Maximum number of products to return.
        **kwargs : Mapping[str, Union[List[int], List[float], List[str]]]
            Additional filters based on product sepcific attributes.
            Each key should be an attribute name, and the corresponding value
            should be a list of acceptable values for that attribute.

        Returns : pd.DataFrame
            DataFrame containing the resulting products of the query.
        """

        # Building query string
        query_str = self._build_query(
            start_time=start_time,
            end_time=end_time,
            prod_type=prod_type,
            exclude=exclude,
            footprint=footprint,
            orderby=orderby,
            limit=limit)

        # Send query
        try:
            json = requests.get(query_str, timeout=100).json()
        except Exception as e:
            raise QueryError(f"{e.__class__.__name__}: Query failed: {e}")

        # convert dict into pd.Dataframe
        products = pd.DataFrame.from_dict(json['value'])
        # Extract more Attributes and add as new fields in DataFram
        products = products.apply(self.__add_attrs_to_df, axis=1)
        # Apply product specific attribute filter
        if kwargs:
            products = filter_by_attributes(products, **kwargs
                                            ).reset_index(drop=True)
        return products

    def _build_query(
            self,
            start_time: str,
            end_time: str,
            prod_type: str | None = None,
            exclude: str | None = None,
            footprint: str | None = None,
            orderby: str | None = None,
            limit: int | None = None
        ) -> str:
        """Builds the API product request string based on given properties and
        constraints.

        Returns: str
            API product request string
        """

        query_str = f"{CATALOG_URL}/Name eq '{self.mission}'" + \
            f" and ContentDate/Start gt {start_time}T00:00:00.000Z" + \
            f" and ContentDate/Start lt {end_time}T00:00:00.000Z"
        if prod_type:
            if prod_type in self.prod_types:
                query_str += f" and contains(Name, '{prod_type}')"
            else:
                raise ValueError("Product type not found. Must be one from " +
                                 f"the list: {self.prod_types}")
        if exclude:
            query_str += f" and not contains(Name,'{exclude}')"
        if footprint:
            query_str += f" and OData.CSC.Intersects(area=geography'SRID=4326;{footprint}')"
        if orderby:
            query_str += f"&$orderby=ContentDate/Start {orderby}"
        if limit:
            query_str += f"&$top={limit}"
        query_str += "&$expand=Attributes"
        return query_str

    def download_by_id(self, uid: str, out_path: Path) -> None:
        """Download single products by UIDs.

        Parameters:
        uid : str
            UID of the product to be downloaded
        out_path : Path
            Output file path for downloaded product
        """

        access_token = self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        url = f"{DOWNLOAD_URL}({uid})/$value"

        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, headers=headers, stream=True)

        with open(str(out_path) + ".zip", "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

    def download_all(
            self,
            products: pd.DataFrame,
            out_dir: Path,
            threads: int=4,
            show_progress: bool=True
        ) -> None:
        """Download all products in parallel using multithreading.

        Parameters:
        products : DataFrame
            Pandas Dataframe containing UIDs of the products to be downloaded
        out_dir : Path
            Output directory path for downloaded products
        threads : int
            Number of simultaneous downloads
        show_progress : bool
            Show download progress bar
        """

        if show_progress:
            pbar = tqdm(total=len(products), unit="files")

        # Generate tupe of UIds and Names for each product
        prod_ids = [(prod.Id, prod.Name) for _, prod in products.iterrows()]

        def download_worker(prod_id: str, prod_name: str) -> None:
            out_file = out_dir / f"{prod_name}"
            try:
                self.download_by_id(prod_id, out_path=out_file)
            except Exception as e:
                raise Exception(f"'{e.__class__.__name__}': Failed to download "
                                f"{prod_name}: {e}")
            finally:
                if show_progress:
                    pbar.update(1)

        threads_ = threads if threads else min(cpu_count() - 2, len(products))
        with ThreadPoolExecutor(threads_) as executor:
            for prod_id, prod_name in prod_ids:
                executor.submit(download_worker, prod_id, prod_name)

        if show_progress:
            pbar.close()


class Sentinel1API(CopernicusDataspaceAPI):
    """Class to download Sentinel-1 products"""

    @property
    def mission(self):
        return "SENTINEL-1"

    @property
    def prod_types(self) -> list[str]:
        return ['RAW', 'SLC', 'GRD', 'GRDH', 'GRDM', 'OCN', 'IW', 'EW']


class Sentinel2API(CopernicusDataspaceAPI):
    """Class to download Sentinel-2 products"""

    @property
    def mission(self):
        return "SENTINEL-2"

    @property
    def prod_types(self) -> list[str]:
        return ['L1C', 'L2A']


class Sentinel3API(CopernicusDataspaceAPI):
    """Class to download Sentinel-3 products"""

    @property
    def mission(self):
        return "SENTINEL-3"

    @property
    def prod_types(self) -> list[str]:
        return ['OL_1', 'OL_2', 'SL_1', 'SL_2', 'SR_1', 'SR_2', 'SR', 'SY_2']


class Sentinel5API(CopernicusDataspaceAPI):
    """Class to download Sentinel-5P products"""

    @property
    def mission(self):
        return "SENTINEL-5P"

    @property
    def prod_types(self) -> list[str]:
        return ['L1B_RA_BD1', 'L1B_RA_BD2', 'L1B_RA_BD3', 'L1B_RA_BD4',
                'L1B_RA_BD5', 'L1B_RA_BD6', 'L1B_RA_BD7', 'L1B_RA_BD8',
                'L2__AER_AI', 'L2__AER_LH', 'L2__CH4', 'L2__CLOUD', 'L2__CO',
                'L2__HCHO', 'L2__NO2', 'L2__NP_BD3', 'L2__NP_BD6', 'L2__NP_BD7',
                'L2__O3_TCL', 'L2__O3__PR', 'L2__O3', 'L2__SO2']


class Sentinel6API(CopernicusDataspaceAPI):
    """Class to download Sentinel-6 products"""

    @property
    def mission(self):
        return "SENTINEL-3"

    @property
    def prod_types(self) -> list[str]:
        return ['MW_2__AMR', 'P4_1B_LR', 'P4_2__LR']


def filter_by_cloud_cover(
        prod_df: pd.DataFrame,
        min_cover: float=0,
        max_cover: float=100
        ) -> pd.DataFrame:
    """Filter products by cloud cover range.

    Parameters:
    prod_df : pd.DataFrame
        DataFrame containing the products to filter.
    min_cover : float
        Minimum cloud cover percentage.
    max_cover : float
        Maximum cloud cover percentage.

    Returns:
    pd.DataFrame
        Filtered DataFrame containing the resulting products.
    """
    try:
        return prod_df[
                (prod_df['cloudCover'] >= min_cover) &
                (prod_df['cloudCover'] <= max_cover)
            ]
    except KeyError as e:
        raise AttributeNotFoundError(e)


def _filter_by_attrs(
        prod_df: pd.DataFrame,
        attribute: str,
        values: list[float | str]
        ) -> pd.DataFrame:
    """Filter products by a specific attribute and its values.

    Parameters:
    prod_df : pd.DataFrame
        DataFrame containing the products to filter.
    attribute : str
        Attribute name for filtering.
    values : list
        List of acceptable values for the attribute.

    Returns:
    pd.DataFrame
        Filtered DataFrame containing the resulting products.
    """
    try:
        return prod_df[prod_df[attribute].isin(values)]
    except KeyError as e:
        raise AttributeNotFoundError(e)


def filter_by_attributes(prod_df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Filter products based on various attributes.

    Parameters:
    prod_df : pd.DataFrame
        DataFrame containing the products to filter.
    **kwargs : Mapping[str, Union[List[int], List[float], List[str]]]
        Additional filters based on product specific attributes.

    Returns:
    pd.DataFrame
        Filtered DataFrame containing the resulting products.
    """
    for key, val in kwargs.items():
        if key == 'cloudCover':
            try:
                assert len(val) == 2
                prod_df = filter_by_cloud_cover(prod_df, val[0], val[1])
            except AssertionError:
                raise ValueError(f"Values for 'cloudCover' must be a list of "
                                 f"2 elements [min, max], {val} was given")
        else:
            prod_df = _filter_by_attrs(prod_df, key, val)
    return prod_df