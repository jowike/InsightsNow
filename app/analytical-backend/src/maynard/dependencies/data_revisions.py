import os
import pandas as pd
import numpy as np
from typing import List, Tuple

from maynard.dependencies.tools import _align_dates, _convert_to_datetime

import warnings

warnings.filterwarnings("ignore")


def prepare_real_time_vintage_data(
    ds: pd.DataFrame,
    y_code: str,
    ref_date: str,
    series_code_col: str,
    ref_date_col: str,
    pub_date_col: str,
    series_val_col: str,
) -> pd.DataFrame:
    """
    Prepares an actual real-time dataset for a given reference date, adjusting for data publication schedules.

    For each explanatory variable, this function identifies the most recent
    publication available *prior to* the first estimate of the target variable
    (`y_code`) at the reference date. This creates a vintage-style dataset
    consistent with real-time forecasting setups.

    Args:
        ds: The dataset containing time series with reference and publication dates.
        y_code: Series code of the target variable (e.g., GDP).
        ref_date: Reference date (string, e.g., '2020-03-01') to extract a vintage snapshot for.
        series_code_col: Column name indicating the series code (e.g., "CODE").
        ref_date_col: Column name indicating the reference date (e.g., "REF_DATE").
        pub_date_col: Column name indicating the publication date (e.g., "PUB_DATE").
        series_val_col: Column name for the series values (e.g., "VALUE").

    Returns:
        A long-format DataFrame containing the real-time vintage dataset
        as observed from the reference date's perspective.
    """

    def _format_individual_series(
        df: pd.DataFrame,
        ref_date: pd.Timestamp,
        pub_date_limit: str,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        This function is structured to process each non-target variable code to create a long format series
        based on available data up to a specified publication date (it extracts the last release dates
        up to a specified publication limit).

        Args:
            df: Subset of the data excluding the target variable (only non-target series).
            ref_date: The reference date for which the vintage is created.
            pub_date_limit: The latest publication date that can be used.

        Returns:
            A tuple with:
                - Long-format DataFrame with series values up to the allowed publication date.
                - List of series codes that contain NaN values.
        """

        df_long = pd.DataFrame(
            columns=[series_code_col, ref_date_col, pub_date_col, series_val_col]
        )
        null_cols = []

        for variable_code in df[series_code_col].unique():
            series_long = df[df[series_code_col] == variable_code]

            series_pivot = series_long.pivot(
                index=pub_date_col, columns=ref_date_col, values=series_val_col
            )
            series_pivot = (
                series_pivot.reindex(
                    sorted(
                        pd.date_range(
                            min(series_pivot.columns),
                            max(series_pivot.columns),
                            freq="MS",
                        )
                    ),
                    axis=1,
                )
                .sort_index()
                .ffill()
            )
            series_min_index = series_pivot.index.min()
            if series_min_index is None:
                continue
            if series_min_index.strftime("%Y-%m-%d") >= pub_date_limit:
                print(
                    f"The observation for {variable_code} was unavailable before {pub_date_limit}."
                )
                series = pd.DataFrame(
                    {series_val_col: np.nan, pub_date_col: np.datetime64("NaT")},
                    index=series_pivot.columns,
                )
            else:
                pivot_limit = series_pivot[series_pivot.index < pub_date_limit]

                last_release_index = (
                    pivot_limit[
                        min(
                            max(pivot_limit.dropna(how="all", axis=1).columns), ref_date
                        )
                    ]
                    .dropna(how="all")
                    .last_valid_index()
                )
                if last_release_index is None:
                    continue
                last_release_dt = last_release_index.strftime("%Y-%m-%d")

                series = pivot_limit.loc[last_release_dt].to_frame()
                series = series.loc[
                    series.first_valid_index() : min(
                        series.last_valid_index(), ref_date
                    )
                ]
                series = series.reindex(
                    sorted(
                        pd.date_range(min(series.index), max(series.index), freq="MS")
                    )
                )
                series.columns = [series_val_col]
                series[pub_date_col] = last_release_dt

            series[series_code_col] = variable_code

            if series[series_val_col].isnull().any():
                null_cols.append(variable_code)

            df_long = pd.concat([df_long, series.reset_index()])

        return df_long, null_cols

    # Start of the main function
    ref_date = pd.to_datetime(ref_date)
    ds = _align_dates(dataframe=ds, date_colname=ref_date_col)

    y_long = ds[ds[series_code_col] == y_code]
    y_pivot = y_long.pivot(
        index=pub_date_col, columns=ref_date_col, values=series_val_col
    )
    y_pivot = (
        y_pivot.reindex(
            sorted(
                pd.date_range(min(y_pivot.columns), max(y_pivot.columns), freq="MS")
            ),
            axis=1,
        )
        .sort_index()
        .ffill()
    )
    first_valid_index = y_pivot[ref_date].first_valid_index()

    if first_valid_index is None:
        return

    y_first_est_release_dt = first_valid_index.strftime("%Y-%m-%d")
    X_df = ds[ds[series_code_col] != y_code]

    # Call the nested helper function for non-target series
    X_df_long, _ = _format_individual_series(
        df=X_df, ref_date=ref_date, pub_date_limit=y_first_est_release_dt
    )

    rt_vintage_dt = y_pivot[y_pivot.index < y_first_est_release_dt].index.max()
    y_series = y_pivot[y_pivot.columns[y_pivot.columns <= ref_date]].loc[rt_vintage_dt]
    y_series.loc[ref_date] = y_pivot.loc[y_first_est_release_dt, ref_date]

    y_long = (
        y_series.to_frame()
        .reset_index()
        .rename(columns={y_series.name: series_val_col})
    )
    y_long[series_code_col] = y_code
    y_long[pub_date_col] = np.where(
        y_long[ref_date_col] < ref_date, rt_vintage_dt, y_first_est_release_dt
    )

    df_long = pd.concat(
        [
            _convert_to_datetime(y_long, [ref_date_col, pub_date_col]),
            _convert_to_datetime(X_df_long, [ref_date_col, pub_date_col]),
        ]
    )

    return df_long
