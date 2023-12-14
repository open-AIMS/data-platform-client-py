import datetime
import logging
import os
import time
from configparser import ConfigParser
from urllib.parse import quote

import pandas as pd
import requests
from pandas import DataFrame
from strenum import StrEnum

logger = logging.getLogger(__name__)

_DOI_PREFIX_ = "10.25845"
_DATA_V2_ = "/data-v2.0"
_DATA_V3_ = "/data-v3.0"
_DATA_V2_APIS_ = ["5b4eb0f9bb848", "5c09bf93f315d"]
_DEFAULT_HOST_ = "api.aims.gov.au"
_DEFAULT_SCHEME_ = "https"


class NoDataFoundError(Exception):
    pass


class NoConfigurationFound(Exception):
    pass


class DataRequestFailedError(Exception):
    pass


class SummaryType(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    SERIES = "summary-by-series"
    DEPLOYMENT = "summary-by-deployment"


class DataSet(StrEnum):
    TEMP_LOGGERS = "5b4eb0f9bb848"
    WEATHER = "5c09bf93f315d"
    # UNDERWAY = ""

    def base_url(self, scheme=None, host=None, base_path=None):
        if base_path is None:
            final_base_path = _DATA_V2_ if self.value in _DATA_V2_APIS_ else _DATA_V3_
        else:
            final_base_path = base_path
        final_host = host or _DEFAULT_HOST_
        final_scheme = scheme or _DEFAULT_SCHEME_
        return f"{final_scheme}://{final_host}{final_base_path}/{_DOI_PREFIX_}/{self.value}"

    def target_url(
        self, target, scheme=None, host=None, base_path=None, query_params=None
    ):
        if query_params is not None:
            query_params_list = [f"{p}={quote(v)}" for p, v in query_params.items()]
            query_params_string = "?" + "&".join(query_params_list)
        else:
            query_params_string = ""
        return (
            self.base_url(scheme=scheme, host=host, base_path=base_path)
            + f"/{target}{query_params_string}"
        )

    def data_url(self, scheme=None, host=None, base_path=None):
        return self.target_url("data", scheme=scheme, host=host, base_path=base_path)

    def summary_url(
        self,
        summary_type: SummaryType,
        scheme=None,
        host=None,
        base_path=None,
    ):
        return self.target_url(
            f"data/{summary_type.value}", scheme=scheme, host=host, base_path=base_path
        )

    def filters_url(
        self,
        scheme=None,
        host=None,
        base_path=None,
    ):
        return self.target_url("filter", scheme=scheme, host=host, base_path=base_path)

    def sites_url(
        self,
        include_details=False,
        scheme=None,
        host=None,
        base_path=None,
    ):
        return self.target_url(
            "site",
            scheme=scheme,
            host=host,
            base_path=base_path,
            query_params={"include_details": str(include_details).lower()},
        )

    def subsites_url(
        self,
        scheme=None,
        host=None,
        base_path=None,
    ):
        return self.target_url("subsite", scheme=scheme, host=host, base_path=base_path)

    def series_url(
        self,
        include_details=False,
        scheme=None,
        host=None,
        base_path=None,
    ):
        return self.target_url(
            "series",
            scheme=scheme,
            host=host,
            base_path=base_path,
            query_params={"include_details": str(include_details).lower()},
        )

    def parameters_url(
        self,
        scheme=None,
        host=None,
        base_path=None,
    ):
        return self.target_url(
            "parameter", scheme=scheme, host=host, base_path=base_path
        )

    def summaries_url(
        self,
        scheme=None,
        host=None,
        base_path=None,
    ):
        return self.target_url("summary", scheme=scheme, host=host, base_path=base_path)


class FilterType(StrEnum):
    SERIES = "series"
    SERIES_ID = "series_id"
    FROM_DATE = "from_date"
    THRU_DATE = "thru_date"
    SITE = "site"
    SUBSITE = "subsite"
    MIN_LAT = "min_lat"
    MAX_LAT = "max_lat"
    MIN_LON = "min_lon"
    MAX_LON = "max_lon"
    SIZE = "size"


class DataRequestBuilder:
    def __init__(
        self,
        data_set: DataSet,
        aims_data_client: "AIMSDataClient" = None,
        retry_attempts=4,
        return_partial=False,
        sleep_time=5,
        **url_args,
    ):
        self.filter_dict = {}
        self.summary_type = None
        self.data_set_type = data_set
        self.url_args_dict = url_args
        self.aims_data_client = aims_data_client
        self.retry_attempts = retry_attempts
        self.return_partial = return_partial
        self.sleep_time = sleep_time

    def add_filter(self, filter_type: FilterType, value):
        self.filter_dict[filter_type.value] = value
        return self

    def from_date(self, value):
        return self.add_filter(FilterType.FROM_DATE, value)

    def thru_date(self, value):
        return self.add_filter(FilterType.THRU_DATE, value)

    def summary(self, summary_type: SummaryType):
        self.summary_type = summary_type
        return self

    def daily(self):
        return self.summary(SummaryType.DAILY)

    def add_url_args(self, **url_args):
        self.url_args_dict.update(url_args)
        return self

    def return_partial_data_frame(self, return_partial=True):
        self.return_partial = return_partial
        return self

    def number_retry_attempts(self, retry_attempts=4, sleep_time=5):
        self.retry_attempts = retry_attempts
        self.sleep_time = sleep_time
        return self

    def retry_sleep_time(self, sleep_time=5):
        self.sleep_time = sleep_time
        return self

    def request_size(self, size=1000):
        self.add_filter(FilterType.SIZE, size)
        return self

    def faster(self):
        return self.number_retry_attempts(0, sleep_time=0).return_partial_data_frame()

    def build_url(self):
        if self.summary_type is not None:
            return self.data_set_type.summary_url(
                self.summary_type, **self.url_args_dict
            ) + self.build_filters(with_starting_query=True)
        return self.data_set_type.data_url(**self.url_args_dict) + self.build_filters(
            with_starting_query=True
        )

    def build_filters(self, with_starting_query=False):
        date_filters = [FilterType.FROM_DATE, FilterType.THRU_DATE]
        filters_list = [
            f"{f}={quote(str(v))}"
            for f, v in self.filter_dict.items()
            if f not in date_filters
        ]
        for filter_type in date_filters:
            if filter_type in self.filter_dict:
                date_value = self.build_date_filter(filter_type)
                filters_list.append(f"{filter_type.value}={quote(date_value)}")
        if len(filters_list) > 0:
            filters_string = "&".join(filters_list)
            if with_starting_query:
                return "?" + filters_string
            else:
                return filters_string
        return ""

    def build_date_filter(self, filter_type: FilterType):
        if filter_type in self.filter_dict:
            if isinstance(self.filter_dict[filter_type], str):
                return self.filter_dict[filter_type]
            elif isinstance(self.filter_dict[filter_type], datetime.date):
                return self.filter_dict[filter_type].isoformat()
            elif isinstance(self.filter_dict[filter_type], datetime.datetime):
                return self.filter_dict[filter_type].isoformat(timespec="minutes")
            else:
                return str(self.filter_dict[filter_type])

    def data_frame(self):
        return self.aims_data_client.aims_data(
            self.build_url(),
            retry_attempts=self.retry_attempts,
            return_partial=self.return_partial,
            sleep_time=self.sleep_time,
        )

    def csv(self, csv_file_path, citation_file_path=None):
        df: DataFrame
        df, citation = self.data_frame()
        df.to_csv(csv_file_path)
        if citation_file_path is not None:
            with open(citation_file_path, mode='wt') as citation_file:
                citation_file.write(citation)


class AIMSDataClient:
    def __init__(self, api_key=None, **url_args):
        self.api_key = api_key
        self.url_args_dict = url_args

    def filters(self, data_set: DataSet):
        response = requests.get(data_set.filters_url(**self.url_args_dict))
        return response.json()

    def sites(self, data_set: DataSet, include_details=False):
        response = requests.get(
            data_set.sites_url(**self.url_args_dict, include_details=include_details)
        )
        return response.json()

    def subsites(self, data_set: DataSet):
        response = requests.get(data_set.subsites_url(**self.url_args_dict))
        return response.json()

    def series(self, data_set: DataSet, include_details=False):
        response = requests.get(
            data_set.series_url(**self.url_args_dict, include_details=include_details)
        )
        return response.json()

    def parameters(self, data_set: DataSet):
        response = requests.get(data_set.parameters_url(**self.url_args_dict))
        return response.json()

    def data_request(self, data_set: DataSet):
        return DataRequestBuilder(data_set, self, **self.url_args_dict)

    def aims_data(self, url, retry_attempts=4, return_partial=False, sleep_time=5):
        df: pd.DataFrame = None
        more_data = True
        citation = None
        if self.api_key is not None:
            headers = {"X-Api-Key": self.api_key}
        else:
            headers = None
        total_rows = 0
        while more_data:
            try:
                result = self.get_page(
                    url,
                    headers=headers,
                    retry_attempts=retry_attempts,
                    sleep_time=sleep_time,
                )
                total_rows += len(result["results"])
                logger.debug("Result has %s rows", total_rows)
                if citation is None:
                    citation = result["citation"]
                    logger.debug(citation)
                if df is None:
                    df = pd.DataFrame(result["results"])
                else:
                    df = pd.concat(
                        [df, pd.DataFrame(result["results"])], ignore_index=True
                    )
                if "links" in result and result["links"] is not None:
                    # there's more pages so get the next page URL
                    url = result["links"]["next"]
                else:
                    # no more pages, end the loop
                    more_data = False
            except DataRequestFailedError:
                if return_partial:
                    logger.warning("Request failed but returning")
                    more_data = False
                else:
                    logger.warning("Request failed, ending")
                    raise
        logger.info("Final data size is %s", len(df.index))
        return df, citation

    def get_page(self, url, headers=None, retry_attempts=4, sleep_time=5):
        no_attempts = 0
        total_attempts = retry_attempts + 1
        while no_attempts < total_attempts:
            no_attempts += 1
            try:
                logger.debug("Attempt %s fetching data from %s", no_attempts, url)
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(
                        "Failed attempt %s, response %s", no_attempts, response
                    )
                    if (
                        retry_attempts > 0
                        and no_attempts < total_attempts
                        and sleep_time > 0
                    ):
                        time.sleep(sleep_time)
            except Exception as ex:
                logger.exception("Unknown error")
                raise DataRequestFailedError("Unknown error") from ex
        raise DataRequestFailedError(f"Failed after {no_attempts} attempts to {url}")

    @classmethod
    def dev_client(cls):
        return cls(host="dev.api.aims.gov.au")

    @classmethod
    def local_dev_client(cls):
        return cls(scheme="http", host="localhost:8000", base_path="")

    @classmethod
    def from_env(cls, key, fail_not_found=True):
        if key in os.environ:
            return cls(api_key=os.getenv(key))
        elif fail_not_found:
            raise NoConfigurationFound("No environment variable found: " + key)
        else:
            return cls()

    @classmethod
    def from_conf(
        cls,
        conf_file,
        section="default",
        key="AIMS_DATA_PLATFORM_API_KEY",
        fail_not_found=True,
    ):
        if conf_file is not None and os.path.exists(conf_file):
            config = ConfigParser()
            config.read(conf_file)
            logger.info("Loaded config from %s", conf_file)
            return cls(api_key=config[section][key])
        elif fail_not_found:
            raise NoConfigurationFound("No config file found: " + conf_file)
        else:
            return cls()

    @classmethod
    def from_defaults(cls):
        try:
            return cls.from_env("AIMS_DATA_PLATFORM_API_KEY")
        except NoConfigurationFound:
            try:
                CONF_FILE = os.path.join(".aims", "dataplatform.ini")
                if "HOME" in os.environ:
                    CONF_PATH = os.path.join(os.getenv("HOME"), CONF_FILE)
                elif "USERPROFILE" in os.environ:
                    CONF_PATH = os.path.join(os.getenv("USERPROFILE"), CONF_FILE)
                else:
                    CONF_PATH = "dataplatform.ini"
                logger.info("Loading configuration from %s", CONF_PATH)
                return cls.from_conf(CONF_PATH)
            except NoConfigurationFound:
                logger.warning("No api key found, returning basic client")
                return cls()
