import pandas as pd
from typing import List

from statsmodels.tsa.stattools import adfuller
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import MaxAbsScaler

import warnings

warnings.filterwarnings("ignore")


def test_stationarity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect series with non-stationarity effects

    This function applies the Augmented Dickey-Fuller (ADF) test to each column (assumed to be a time series) in the input DataFrame.
    Series with p-values above the significance threshold are considered non-stationary.

    Args:
        df (pd.DataFrame): A DataFrame where each column represents a time series to be tested.

    Returns:
        pd.DataFrame: List of column names corresponding to non-stationary series.
    """

    def __adfuller_test(
        series: pd.Series, signif: float = 0.05, name: str = "", verbose: bool = False
    ):
        """Perform ADFuller to test for Stationarity of given series and print report"""
        r = adfuller(series, autolag="AIC")
        output = {
            "test_statistic": round(r[0], 4),
            "pvalue": round(r[1], 4),
            "n_lags": round(r[2], 4),
            "n_obs": r[3],
        }
        p_value = output["pvalue"]

        def adjust(val, length=6):
            return str(val).ljust(length)

        # Print Summary
        if verbose:
            print(f' Augmented Dickey-Fuller Test on "{name}"', "\n   ", "-" * 47)
            print(" Null Hypothesis: Data has unit root. Non-Stationary.")
            print(f" Significance Level = {signif}")
            print(f' Test Statistic = {output["test_statistic"]}')
            print(' No. Lags Chosen = {output["n_lags"]}')

            for key, val in r[4].items():
                print(f" Critical value {adjust(key)} = {round(val, 3)}")

            if p_value <= signif:
                print(f" => P-Value = {p_value}. Rejecting Null Hypothesis.")
                print(" => Series is Stationary.")
            else:
                print(
                    f" => P-Value = {p_value}. Weak evidence to reject the Null Hypothesis."
                )
                print(" => Series is Non-Stationary.")
        return p_value

    stat = []

    for _id in df.columns:
        series_df = df[[_id]]
        series = series_df.dropna().sort_index()

        test_pval = __adfuller_test(series=series, name=_id)
        if test_pval < 0.05:
            stat.append(_id)

    return list(set(df.columns) - set(stat))


def test_variance(data: pd.DataFrame) -> List[str]:
    """
    Identify low-variance features in a DataFrame.

    This function scales the data using MaxAbsScaler, computes the variance of each feature,
    and removes features whose variance falls below the 5th percentile threshold.

    Args:
        data (pd.DataFrame): Input DataFrame with numerical features.

    Returns:
        List[str]: Names of columns identified as low-variance features.
    """
    transformer = MaxAbsScaler().fit(data)
    df_scaled = pd.DataFrame(transformer.transform(data), columns=data.columns)
    tsh = df_scaled.var().quantile(0.05)
    selector = VarianceThreshold()

    selector = VarianceThreshold(threshold=tsh)
    selector.fit(df_scaled)

    features = df_scaled.columns[selector.get_support(indices=True)]

    return list(set(data.columns) - set(features))
