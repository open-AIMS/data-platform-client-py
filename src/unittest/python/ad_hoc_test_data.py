from aims_data_platform import AIMSDataClient, DataSet, SummaryType, FilterType


def test_data():
    client = AIMSDataClient()
    df, citation = (
        client.data_request(DataSet.WEATHER)
        .summary(SummaryType.DAILY)
        .add_filter(FilterType.SERIES_ID, 104905)
        .add_filter(FilterType.FROM_DATE, "2020-01-01")
        .add_filter(FilterType.THRU_DATE, "2023-01-01")
        .data_frame()
    )
    assert citation.startswith(
        "Australian Institute of Marine Science (AIMS). 2009, Australian Institute of Marine Science Automatic Weather Stations, Time period:2020-01-01 to 2023-01-01. https://doi.org/10.25845/5b4eb0f9bb848, accessed"
    )
    assert len(df.index) == 951
