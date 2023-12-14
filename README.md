AIMS Data Platform Python Client
--------------------------------

AIMS Data Platform Python Client is an _HTTP_ client for AIMS Research Data Platform.  It
makes use of [AIMS Data Platform API](https://open-aims.github.io/data-platform/) to fulfill
data requests.  It allows for simple configuration of API Keys and easy access to a Pandas data frame
of AIMS data.


## Installation ##

It is possible to install the python package using pip and git directly since the
package is not yet published on PyPI:

```shell
pip install data_platform_client_py@git+https://github.com/open-AIMS/data-platform-client-py.git
```
Alternatively if you have been supplied with the Python wheel file it can be installed using pip:

```shell
pip install data_platform_client_py-1.0-py3-none-any.whl
```

The package should now be installed along with any dependencies.  For requests of daily,
weekly or other summary data there is no requirement to supply an API Key, however requests
for raw data will require an API Key to be supplied.  The API Key can be obtained
[here](https://open-aims.github.io/data-platform/).

The default place to store the API Key is: `<USER_HOME>/.aims/dataplatform.ini` in a file
structured per this example:

```ini
[default]
AIMS_DATA_PLATFORM_API_KEY=xxxxxxxxxxxxxxxxxxxxxxx
```

## Usage ##

AIMS Data Platform Python Client can be used as per the following example:

```python

import datetime
import logging

from aims_data_platform import AIMSDataClient, DataSet, FilterType

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.INFO)

if __name__ == "__main__":
    aims_data_client = AIMSDataClient.from_conf("my-api-key.ini")
    df, citation = (
        aims_data_client.data_request(DataSet.WEATHER)
        .add_filter(FilterType.SERIES_ID, 65)
        .add_filter(FilterType.FROM_DATE, datetime.date(2023, 10, 18))
        .add_filter(FilterType.THRU_DATE, datetime.date(2023, 11, 15))
        .data_frame()
    )

    print(df.head())

```

Output:

```text
INFO:aims_data_platform:Loaded config from C:\Users\username\Development\my-api-key.ini
DEBUG:aims_data_platform:Attempt 1 fetching data from https://api.aims.gov.au/data-v2.0/10.25845/5c09bf93f315d/data?series_id=65&from_date=2023-10-18&thru_date=2023-11-15
DEBUG:aims_data_platform:Result has 1000 rows
DEBUG:aims_data_platform:Australian Institute of Marine Science (AIMS). 2009, Australian Institute of Marine Science Automatic Weather Stations, Time period:2023-10-18 to 2023-11-15. https://doi.org/10.25845/5b4eb0f9bb848, accessed 17 Nov 2023.
DEBUG:aims_data_platform:Attempt 1 fetching data from https://api.aims.gov.au/data-v2.0/10.25845/5c09bf93f315d/data?series_id=65&size=1000&from_date=2023-10-18T00%3A00%3A00%2B00%3A00&thru_date=2023-11-15T00%3A00%3A00%2B00%3A00&cursor=496703%212023-10-24T22%3A30%3A00%2B00%3A00
DEBUG:aims_data_platform:Result has 2000 rows
DEBUG:aims_data_platform:Attempt 1 fetching data from https://api.aims.gov.au/data-v2.0/10.25845/5c09bf93f315d/data?series_id=65&size=1000&from_date=2023-10-18T00%3A00%3A00%2B00%3A00&thru_date=2023-11-15T00%3A00%3A00%2B00%3A00&cursor=496703%212023-10-31T21%3A10%3A00%2B00%3A00
DEBUG:aims_data_platform:Result has 3000 rows
DEBUG:aims_data_platform:Attempt 1 fetching data from https://api.aims.gov.au/data-v2.0/10.25845/5c09bf93f315d/data?series_id=65&size=1000&from_date=2023-10-18T00%3A00%3A00%2B00%3A00&thru_date=2023-11-15T00%3A00%3A00%2B00%3A00&cursor=496703%212023-11-07T19%3A50%3A00%2B00%3A00
DEBUG:aims_data_platform:Result has 4000 rows
DEBUG:aims_data_platform:Attempt 1 fetching data from https://api.aims.gov.au/data-v2.0/10.25845/5c09bf93f315d/data?series_id=65&size=1000&from_date=2023-10-18T00%3A00%3A00%2B00%3A00&thru_date=2023-11-15T00%3A00%3A00%2B00%3A00&cursor=496703%212023-11-14T18%3A40%3A00%2B00%3A00
DEBUG:aims_data_platform:Result has 4032 rows
INFO:aims_data_platform:Final data size is 4032
Series 65 data frame:
   deployment_id         site  ...     data_id                       time
0         496703  Davies Reef  ...  1280489241  2023-10-18T00:00:00+00:00
1         496703  Davies Reef  ...  1280490146  2023-10-18T00:10:00+00:00
2         496703  Davies Reef  ...  1280491853  2023-10-18T00:20:00+00:00
3         496703  Davies Reef  ...  1280492329  2023-10-18T00:30:00+00:00
4         496703  Davies Reef  ...  1280492788  2023-10-18T00:40:00+00:00

[5 rows x 14 columns]

```
Another example to get daily summary data:

```python
from aims_data_platform import AIMSDataClient, DataSet, SummaryType, FilterType

client = AIMSDataClient() # No api key required for summary data
df, citation = (
    client.data_request(DataSet.WEATHER)
    .summary(SummaryType.DAILY)
    .add_filter(FilterType.SERIES_ID, 104905)
    .add_filter(FilterType.FROM_DATE, "2020-01-01")
    .add_filter(FilterType.THRU_DATE, "2023-01-01")
    .data_frame()
)

```

```python
from aims_data_platform import AIMSDataClient, DataSet, SummaryType, FilterType

client = AIMSDataClient().from_defaults()
df, citation = (
    client.data_request(DataSet.WEATHER)
    .summary(SummaryType.DAILY)
    .add_filter(FilterType.SERIES_ID, 104905)
    .add_filter(FilterType.FROM_DATE, "2020-01-01")
    .add_filter(FilterType.THRU_DATE, "2023-01-01")
    .retry_sleep_time(0)
    .data_frame()
)

```
To get the list of series including details:

```python
from aims_data_platform import AIMSDataClient, DataSet

client = AIMSDataClient()
client.sites(DataSet.WEATHER, include_details=True)

```
