from aims_data_platform import DataRequestBuilder, DataSet, SummaryType, FilterType


def test_summary_series():
    url = (
        DataRequestBuilder(DataSet.TEMP_LOGGERS).summary(SummaryType.SERIES).build_url()
    )
    assert (
        url
        == "https://api.aims.gov.au/data-v2.0/10.25845/5b4eb0f9bb848/data/summary-by-series"
    )


def test_daily_summary():
    url = (
        DataRequestBuilder(DataSet.TEMP_LOGGERS)
        .summary(SummaryType.DAILY)
        .add_filter(FilterType.SERIES_ID, 2648)
        .build_url()
    )
    assert (
        url
        == "https://api.aims.gov.au/data-v2.0/10.25845/5b4eb0f9bb848/data/daily?series_id=2648"
    )


def test_weekly_summary():
    url = (
        DataRequestBuilder(DataSet.TEMP_LOGGERS)
        .summary(SummaryType.WEEKLY)
        .add_filter(FilterType.SERIES_ID, 2648)
        .add_filter(FilterType.FROM_DATE, "2006-01-01")
        .build_url()
    )
    assert (
        url
        == "https://api.aims.gov.au/data-v2.0/10.25845/5b4eb0f9bb848/data/weekly?series_id=2648&from_date=2006-01-01"
    )


def test_dev_data():
    url = (
        DataRequestBuilder(DataSet.TEMP_LOGGERS)
        .add_url_args(host="localhost:8000", scheme="http", base_path="")
        .add_filter(FilterType.SERIES_ID, 2648)
        .add_filter(FilterType.FROM_DATE, "2006-01-01")
        .build_url()
    )
    assert (
        url
        == "http://localhost:8000/10.25845/5b4eb0f9bb848/data?series_id=2648&from_date=2006-01-01"
    )
