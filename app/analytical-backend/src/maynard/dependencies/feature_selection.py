import mifs
import pandas as pd
from typing import Literal

def mtsfs(
    ds: pd.DataFrame,
    series_name: str,
    method: Literal["JMI", "JMIM", "MRMR"]
) -> pd.DataFrame:
    """
    Selects relevant predictors for a given univariate time series from a multivariate dataset.

    This function applies the Mutual Information Feature Selector (MIFS) to extract a subset
    of relevant features from a multivariate dataset for a given target series. The method is
    based on information-theoretic criteria and is suitable for model-agnostic feature filtering
    prior to forecasting or regression.

    Args:
        ds: Time-indexed DataFrame containing the target series and candidate predictors.
        series_name: Name of the target series to be predicted. Must be a column in `ds`.
        method: Mutual information feature selection method. One of:
            - 'JMI': Joint Mutual Information
            - 'JMIM': Joint Mutual Information Maximization
            - 'MRMR': Minimum Redundancy Maximum Relevance

    Returns:
        A DataFrame containing only the selected features and the original target series,
        indexed by time and aligned with the input data.

    Notes:
        - Uses `mifs.MutualInformationFeatureSelector` from https://github.com/danielhomola/mifs.
        - Handles known issues (e.g. all-zero columns) by catching and logging exceptions.
    """

    df = ds.sort_index()
    df.index = pd.to_datetime(df.index)

    X = df.drop(columns=[series_name])
    y = df[[series_name]]

    feat_selector = mifs.MutualInformationFeatureSelector(
        method=method,
        n_features="auto",
        categorical=False
    )

    # Find all relevant features
    try:
        feat_selector.fit(X.values, y.values.ravel())
    except ValueError as e:
        print(f"ERROR: Exception raised for {series_name}: {e}")  # https://github.com/danielhomola/mifs/issues/15

    # Call transform() on X to filter it down to selected features
    X_support = pd.DataFrame(
        feat_selector.transform(X.values),
        columns=X.columns[feat_selector._support_mask],
        index=X.index,
    )
    to_write = pd.merge(X_support, y, left_index=True, right_index=True, how="right")

    return to_write