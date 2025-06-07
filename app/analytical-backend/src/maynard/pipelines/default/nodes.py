import pandas as pd
import numpy as np
from itertools import compress
from typing import Tuple, Dict, Any, Optional

from sklearn.metrics import r2_score
import os
from dateutil.relativedelta import relativedelta
from datetime import datetime

import rpy2.robjects as ro
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
from rpy2.robjects import default_converter
from rpy2.robjects import pandas2ri

from maynard.dependencies.tools import (
    _convert_to_datetime,
    cast_spec_to_dict,
    suggest_transformation,
    mape,
    rmse,
    mse,
)
from maynard.dependencies.diagnostics import test_variance as tvar
from maynard.dependencies.diagnostics import test_stationarity as tstat
from maynard.dependencies.data_revisions import prepare_real_time_vintage_data
from maynard.dependencies.ragged_edges import shift_to_fill_trailing_nans
from maynard.dependencies.load_spec import load_spec
from maynard.dependencies.remNaNs_spline import remNaNs_spline
from maynard.dependencies.load_data import load_data
from maynard.dependencies.summarize import summarize
from maynard.dependencies.feature_selection import mtsfs
from maynard.dependencies.estimation import (
    estimate_arima,
    estimate_automl,
    estimate_var,
    cast_to_base_unit,
    calculate_conf_bounds,
)


def prepare_vintage_data(
    ds: pd.DataFrame,
    parameters: Dict[str, str],
    spec_options: Optional[Dict[str, str]] = None,
) -> Tuple[pd.DataFrame, Dict[str, list]]:
    """
    Prepares a retrospective (vintage) dataset based on revision history.

    This function filters and processes a long-format dataset with multiple
    publication dates to reconstruct real-time vintages for a given reference date.

    Args:
        ds: Raw input dataset in long format (with publication and reference dates).
        parameters: Dictionary with required metadata field names and config keys:
            - "ref_date_col": reference date column name
            - "pub_date_col": publication date column name
            - "series_code_col": column identifying variable series
            - "series_val_col": column with observed values
            - "freq_desc_col": frequency descriptor column
            - "scope_freq_desc": list of frequencies to include (if no spec provided)
            - "ref_date": cutoff reference date
            - "y_code": target variable code
            - "vintage_name": type of vintage (currently supports "real-time")
        spec_options: Optional dictionary with path to the Excel spec file:
            - "filepath": path to specification Excel file

    Returns:
        A tuple:
            - DataFrame with real-time aligned values
            - Dictionary containing the model specification
    """
    # Convert ref/pub date columns to datetime
    ds = _convert_to_datetime(
        ds, [parameters["ref_date_col"], parameters["pub_date_col"]]
    )

    if spec_options:
        Spec = load_spec(spec_options["filepath"])
        seriesid, SeriesName, Units, UnitsTransformed, frequency = (
            Spec["seriesid"],
            Spec["seriesname"],
            Spec["units"],
            Spec["unitstransformed"],
            Spec["frequency"],
        )
        df = ds.loc[ds[parameters["series_code_col"]].isin(seriesid)]
    else:
        df = ds.loc[
            ds[parameters["freq_desc_col"]].isin(parameters["scope_freq_desc"])
        ].copy()

    cols = [
        parameters["series_code_col"],
        parameters["ref_date_col"],
        parameters["pub_date_col"],
        parameters["series_val_col"],
    ]

    # TODO: Add more strategies – preliminary, current-vintage (pseudo-real-time)
    if parameters["vintage_name"] == "real-time":
        df_long = prepare_real_time_vintage_data(
            ds=df[cols].drop_duplicates(),
            y_code=parameters["y_code"],
            ref_date=parameters["ref_date"],
            series_code_col=parameters["series_code_col"],
            ref_date_col=parameters["ref_date_col"],
            pub_date_col=parameters["pub_date_col"],
            series_val_col=parameters["series_val_col"],
        )
        spec = suggest_spec(
            ds.loc[ds["VariableCode"].isin(df_long["VariableCode"].unique())],
            parameters,
            spec_options,
        )

        return df_long, spec


def suggest_spec(
    ds: pd.DataFrame, parameters: dict, spec_options: dict = None
) -> pd.DataFrame:
    """
    Build a standardized specification DataFrame from a user-provided file
    or by inferring specifications from raw series unit descriptions.

    This function supports two modes:
    - If a specification file is provided, it is parsed and returned in standardized form.
    - Otherwise, a new specification is constructed based on metadata, where transformation
      codes are heuristically assigned based on the economic meaning of the unit (e.g., levels, growth rates, indexes).

    Args:
        ds: Raw DataFrame containing series metadata (e.g., name, unit, frequency).
        parameters: Dictionary mapping relevant column names and config, including:
            - "freq_desc_col": name of column with frequency descriptions
            - "scope_freq_desc": list of accepted frequency labels (e.g. ["Monthly", "Quarterly"])
            - "series_code_col": column with variable IDs
            - "series_name_col": column with descriptive series names
            - "unit_col": column describing the units of measurement
            - "series_categ_col": column specifying series category/group
            - "region_col": region assignment column
            - "default_transf_code": fallback transformation code
        spec_options: Optional dictionary with:
            - "filepath": path to a pre-defined Excel specification to load

    Returns:
        A standardized DataFrame with the following columns:
            - 'seriesid'
            - 'seriesname'
            - 'frequency'
            - 'transformation'
            - 'units'
            - 'category'
            - 'region'
            - 'model'
    """
    # Define the output columns
    output_columns = [
        "seriesid",
        "seriesname",
        "frequency",
        "transformation",
        "units",
        "category",
        "region",
        "model",
    ]
    if spec_options:
        Spec = load_spec(spec_options["filepath"])
        Spec.pop("blocknames")
        df = pd.DataFrame(Spec)
        df = df.rename(columns={parameters["region_col"]: "region"})
        return df[output_columns]
    else:
        # Filter the source DataFrame based on the specified frequency descriptions
        df = ds.loc[
            ds[parameters["freq_desc_col"]].isin(parameters["scope_freq_desc"])
        ].copy()

        # Select and rename columns
        renamed_df = (
            df[
                [
                    parameters["series_code_col"],
                    parameters["freq_desc_col"],
                    parameters["series_name_col"],
                    parameters["unit_col"],
                    parameters["series_categ_col"],
                    parameters["region_col"],
                ]
            ]
            .drop_duplicates()
            .rename(
                columns={
                    parameters["series_code_col"]: "seriesid",
                    parameters["series_name_col"]: "seriesname",
                    parameters["unit_col"]: "units",
                    parameters["series_categ_col"]: "category",
                    parameters["region_col"]: "region",
                }
            )
        )

        # Map frequency descriptions to standardized frequency codes
        renamed_df["frequency"] = renamed_df[parameters["freq_desc_col"]].apply(
            lambda x: "m" if "Monthly" in x else "q" if "Quarterly" in x else None
        )

        # Add a default transformation column
        renamed_df["transformation"] = [
            suggest_transformation(unit) for unit in renamed_df["units"]
        ]
        renamed_df["model"] = np.nan

        # Return the final DataFrame with standardized columns
        return renamed_df[output_columns]


def harmonize_ragged_edges(
    ds: pd.DataFrame,
    spec: pd.DataFrame,
    parameters: Dict[str, str],
) -> pd.DataFrame:
    """
    Harmonize ragged edges in a dataset by aligning series based on their last available data points.

    This function handles the ragged edge problem common in real-time macroeconomic datasets,
    where some indicators are missing for the most recent periods. It pivots the input data to
    wide format per frequency, shifts series to fill trailing NaNs using lagged observations,
    and reconstructs a consistent panel up to the specified reference date.

    Args:
        ds (pd.DataFrame): Long-format dataset containing series values and reference/publication dates.
        spec (pd.DataFrame): Standardized specification DataFrame including series IDs and frequencies.
        parameters (dict): Configuration dictionary with keys such as:
            - 'ref_date': Target reference date for harmonization.
            - 'ref_date_col': Name of the reference date column in `ds`.
            - 'series_code_col': Name of the column identifying the series.
            - 'series_val_col': Name of the column with values.
            - 'y_code': Target variable to preserve in its original (non-shifted) form.

    Returns:
        pd.DataFrame: A wide-format DataFrame with harmonized values (index = reference dates,
                      columns = series codes), aligned to the reference date.
    """
    to_write = pd.DataFrame()
    ds[parameters["ref_date_col"]] = pd.to_datetime(ds[parameters["ref_date_col"]])
    reference_date = pd.to_datetime(parameters["ref_date"])
    lag_date = reference_date - relativedelta(month=1)

    for freq_desc in spec["frequency"].unique():
        series_codes = list(spec.loc[(spec["frequency"] == freq_desc)]["seriesid"])
        subset = ds.loc[ds[parameters["series_code_col"]].isin(series_codes)]
        if subset.shape[0]:
            df_wide = subset.pivot(
                index=parameters["ref_date_col"],
                columns=parameters["series_code_col"],
                values=parameters["series_val_col"],
            )

            if parameters["y_code"] in series_codes:
                X_df = df_wide.drop(columns=[parameters["y_code"]])
                y_df = df_wide[[parameters["y_code"]]]

                res_i = pd.merge(
                    shift_to_fill_trailing_nans(X_df.loc[:reference_date]),
                    y_df,  # y_df.loc[:lag_date],
                    how="left",
                    left_index=True,
                    right_index=True,
                )
            else:
                res_i = shift_to_fill_trailing_nans(df_wide.loc[:reference_date])

            to_write = pd.concat(
                [to_write, pd.melt(res_i, value_vars=res_i.columns, ignore_index=False)]
            )

    to_write = to_write.reset_index().pivot(
        index=parameters["ref_date_col"],
        columns=parameters["series_code_col"],
        values="value",
    )
    return to_write


def transform_time_series(
    ds: pd.DataFrame,
    spec: pd.DataFrame,
    parameters: Dict[str, str],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transform, clean, and impute time series data.

    This function prepares macroeconomic time series for downstream use by applying
    transformations, handling missing values, and reshaping the data.

    Logic:
        - If the specification includes a non-NaN 'model' flag, it is treated as a
          user-provided specification. Only the indicated series are included and
          transformed according to user-specified transformation codes.
        - Otherwise, all available series are used and transformed according to heuristics
          inferred from unit descriptions (e.g., levels, percentages, indexes).

    Steps:
        - Load and align time series data.
        - Filter based on 'model' flag or retain all series.
        - Drop variables with excessive missing values (≥80%).
        - Apply transformation and impute missing values using cubic spline smoothing.
        - Return both the transformed dataset (X_df) and original raw series (Z_df).

    Args:
        ds: Long-format DataFrame with columns including reference date, series code, and values.
        spec: Model specification DataFrame, either user-defined or auto-generated.
        parameters: Dictionary of required parameters and column mappings, e.g.:
            - 'ref_date_col': column name for reference dates
            - 'sample_start': first date to include
            - 'y_code': target variable ID

    Returns:
        X_df: Transformed, imputed, and aligned time series DataFrame.
        Z_df: Original raw time series (wide format) for reference.
    """

    if parameters["sample_start"]:
        sample_start = pd.to_datetime(parameters["sample_start"], format="%Y-%m-%d")
    Spec = cast_spec_to_dict(spec)

    if not np.isnan(Spec["model"]).all():
        X, Time, Z, header = load_data(ds, Spec, sample_start)

        # summarize data
        summarize(X.astype(float), Time, Spec)

        # Prepare data -----------------------------------------------------------
        optNaN = {"method": 2, "k": 3}
        x_est, _, nanLE = remNaNs_spline(X, optNaN)  # Impute series
        X[np.isnan(X)] = x_est[np.isnan(X)]

        summarize(X, Time[~nanLE], Spec)

        X_df = (
            pd.DataFrame(x_est, columns=header, index=Time[~nanLE])
            .reset_index()
            .rename(columns={"index": parameters["ref_date_col"]})
        )  # Transformed, standarized, imputed data
        Z_df = (
            pd.DataFrame(data=Z, columns=header, index=Time)
            .reset_index()
            .rename(columns={"index": parameters["ref_date_col"]})
        )  # Source data (just in cases)
    else:
        X, Time, Z, header = load_data(ds, Spec, sample_start)

        # summarize data
        summarize(X.astype(float), Time, Spec)

        # Prepare data -----------------------------------------------------------
        T, N = X.shape  # Gives dimensions for data input
        indNaN = np.isnan(X)  # Returns location of NaNs
        rem = (
            np.sum(indNaN, axis=0) > T * 0.8
        )  # Returns columns sum for NaN values. Marks true for rows with more than 80% NaN
        X = X[:, ~rem]
        x_header = list(compress(header, ~rem))

        optNaN = {"method": 2, "k": 3}
        x_est, indNaN, nanLE = remNaNs_spline(X, optNaN)  # Impute series

        X[np.isnan(X)] = x_est[np.isnan(X)]

        indFin = np.isfinite(x_est)
        X = X[:, indFin.all(axis=0)]  # Drop all-NaN columns
        x_header = list(compress(x_header, indFin.all(axis=0)))

        Spec = cast_spec_to_dict(spec.loc[spec["seriesid"].isin(x_header)])

        summarize(X, Time[~nanLE], Spec)

        X_df = (
            pd.DataFrame(X, columns=x_header, index=Time[~nanLE])
            .reset_index()
            .rename(columns={"index": parameters["ref_date_col"]})
        )  # Transformed, standarized, imputed data

        Z_df = (
            pd.DataFrame(data=Z, columns=header, index=Time)
            .reset_index()
            .rename(columns={"index": parameters["ref_date_col"]})
        )  # Source data

    return X_df, Z_df


def test_variance(
    ds: pd.DataFrame,
    spec: pd.DataFrame,
    parameters: Dict[str, str],
) -> pd.DataFrame:
    """
    Remove low-variance predictors unless the specification explicitly selects variables.

    This function filters out low-variance predictors to reduce noise in modeling.
    If a user-defined specification is provided (i.e., the 'model' flag is not entirely NaN),
    all series explicitly indicated in the specification are retained.
    Otherwise, the function drops features with variance below a
    data-driven threshold (5th percentile) and returns the cleaned dataset.

    Args:
        ds: Input dataset in long format with reference date column and series values.
        spec: Variable specification DataFrame.
        parameters: Dictionary containing key column names and config, including:
            - 'ref_date_col': column name for reference dates
            - 'y_code': name of the target variable

    Returns:
        pd.DataFrame: A DataFrame with low-variance features removed (if auto-selected)
                      or the original dataset preserved (if model spec is provided).
    """
    Spec = cast_spec_to_dict(spec)

    if not np.isnan(Spec["model"]).all():
        # if spec_options:
        to_write = ds.copy()
    else:
        ds = _convert_to_datetime(ds, [parameters["ref_date_col"]])

        ds = ds.set_index(parameters["ref_date_col"]).sort_index()
        X, y = ds.drop(columns=[parameters["y_code"]]), ds[[parameters["y_code"]]]

        x_est = X.drop(columns=tvar(data=X))

        to_write = pd.merge(x_est, y, left_index=True, right_index=True, how="right")
        to_write = to_write.reset_index()

    return to_write


def test_stationarity(
    ds: pd.DataFrame,
    spec: pd.DataFrame,
    parameters: Dict[str, str],
) -> pd.DataFrame:
    """
    Filter out non-stationary predictors to improve model stability.

    This function removes predictors that exhibit signs of non-stationarity based on
    the Augmented Dickey-Fuller (ADF) test. If a user-defined specification is provided
    (i.e., the 'model' flag is not entirely NaN), all indicated series are retained as-is.

    Otherwise, the function runs the ADF test on each feature (excluding the target variable)
    and removes those that fail the test (p-value > 0.05). The resulting DataFrame includes
    only stationary predictors and the original target variable.

    Args:
        ds: Input dataset containing predictor and target variables.
        spec: Variable specification DataFrame with a 'model' column.
        parameters: Dictionary of configuration parameters including:
            - 'ref_date_col': name of the date column
            - 'y_code': name of the target variable

    Returns:
        pd.DataFrame: Cleaned dataset with only stationary predictors retained,
                      or the full dataset if user-specified variables are defined.
    """
    Spec = cast_spec_to_dict(spec)

    if not np.isnan(Spec["model"]).all():
        # if spec_options:
        to_write = ds.copy()
    else:
        ds = _convert_to_datetime(ds, [parameters["ref_date_col"]])

        ds = ds.set_index(parameters["ref_date_col"]).sort_index()
        X, y = ds.drop(columns=[parameters["y_code"]]), ds[[parameters["y_code"]]]

        x_stat = X.drop(columns=tstat(X))

        to_write = pd.merge(x_stat, y, left_index=True, right_index=True, how="right")
        to_write = to_write.reset_index()

    return to_write


def apply_series_selection(
    ds: pd.DataFrame,
    spec: pd.DataFrame,
    parameters: Dict[str, str],
) -> pd.DataFrame:
    """
    Apply feature selection to retain the most relevant predictors for modeling.

    This function selects a subset of relevant time series based on either:
    - user-defined specification (if 'model' field is provided), or
    - mutual information feature selection (MIFS), if no predefined selection exists.

    Args:
        ds (pd.DataFrame): The input dataset with a datetime column and multiple series.
        spec (pd.DataFrame): Specification DataFrame including the 'model' flag.
        parameters (Dict[str, str]): Dictionary with required parameters, including:
            - 'ref_date_col': name of the datetime column
            - 'y_code': name of the target variable
            - 'mifs_method': method used for mutual information-based selection (e.g., 'JMIM')

    Returns:
        pd.DataFrame: Filtered dataset with only selected series and the datetime column.
    """
    ds = _convert_to_datetime(ds, [parameters["ref_date_col"]])
    ds = ds.set_index(parameters["ref_date_col"]).sort_index()

    Spec = cast_spec_to_dict(spec)

    if not np.isnan(Spec["model"]).all():
        # if spec_options:
        to_write = ds.copy()
    else:
        to_write = mtsfs(
            ds=ds, series_name=parameters["y_code"], method=parameters["mifs_method"]
        )
    to_write = to_write.dropna(axis=1, how="all")
    return to_write.reset_index()


def estimate_ml_node(
    ds: pd.DataFrame,
    ds_base: pd.DataFrame,
    spec: pd.DataFrame,
    parameters: Dict[str, Any],
) -> str:
    """
    Estimate and adjust machine learning-based nowcast for a macroeconomic variable.

    This function runs multiple regression models on rolling backtests,
    selects the best model using R², generates forecasts, evaluates model performance,
    and applies a structural break adjustment based on Bai–Perron test.
    It also retransforms predictions to original units and saves
    all relevant outputs to a multi-sheet Excel file.

    Args:
        ds: Transformed and imputed input data for model training (wide format).
        ds_base: Base dataset used for retransforming the forecast back to original units.
        spec: Specification DataFrame containing metadata (e.g., transformation type).
        parameters: Dictionary containing required parameter values such as:
            - 'ref_date_col': name of reference date column.
            - 'y_code': series code to forecast.
            - 'ref_date': forecast reference date (str, 'YYYY-MM-DD').
            - 'backcasting_period': number of months used for evaluation.
            - 'model_output_directory': path to save Excel output.
            - 'ml_report_filename': filename for Excel report.

    Returns:
        A string message with the path to the saved Excel report.
    """
    # Example usage
    model_result = estimate_automl(
        ds=ds,
        ref_date_col=parameters["ref_date_col"],
        series_name=parameters["y_code"],
        reference_date=parameters["ref_date"],
        n_periods=parameters["backcasting_period"],
    )

    reference_date = pd.to_datetime(parameters["ref_date"]).date()
    lag_date = reference_date - relativedelta(months=1)
    pred = model_result["pred_"]["forecast"]
    coef_ = model_result["coef_"]
    values = model_result["values"]

    print("============ Model Details ============")
    print(f"Model                     : {model_result['best_model']}")
    print(f"Reference Date            : {reference_date}")
    print(f"Forecast                  : {pred:.4f}")
    print(f"R-Squared (R²)            : {model_result['r_squared']:.4f}")
    print(f"Mean Absolute Percentage Error (MAPE): {model_result['mape']:.2f}%")
    print(f"Root Mean Square Error (RMSE) : {model_result['rmse']:.4f}")
    print("\n")

    dt = model_result["pred_"]["backcast"].index

    pred = model_result["pred_"]["backcast"]
    actual = model_result["actual"].loc[dt]
    bounds = calculate_conf_bounds(pred, actual)

    bounds_level = {}
    for key, value in bounds.items():
        data, dt_, _ = cast_to_base_unit(
            ds_base, spec, parameters["y_code"], value, dtype="pred"
        )
        tmp = pd.Series(data.reshape(1, -1)[0], index=dt_)
        bounds_level[key] = tmp.loc[dt]

    transf_pred = pd.concat(
        [
            model_result["pred_"]["backcast"],
            pd.Series(
                model_result["pred_"]["forecast"],
                index=[pd.to_datetime(model_result["pred_"]["reference_date"])],
            ),
        ]
    )
    transf_actual = model_result["actual"]

    # Retransform forecast
    Rhat, Time, _ = cast_to_base_unit(
        ds_base, spec, parameters["y_code"], transf_pred, dtype="pred"
    )
    R, _, _ = cast_to_base_unit(
        ds_base, spec, parameters["y_code"], transf_actual, dtype="actual"
    )

    # TBC
    header = [parameters["y_code"]]
    Rhat_df = pd.DataFrame(Rhat, columns=header, index=Time)
    R_df = pd.DataFrame(R, columns=header, index=Time)

    retr_forecast = Rhat_df.loc[reference_date].item()
    retr_actual = R_df.loc[reference_date].item()

    # Backcast (test) values should be returned without any adjustments
    retr_backcast = Rhat_df.loc[:lag_date]
    retr_actuals = R_df.loc[:lag_date]

    # Shap-based impact assessment
    # [SHAP] Rozwiązanie 2. (plan A): Powiedzmy, że to "expected value" to byłaby nasza uśredniona prognoza, a jeśli to prognoza to możemy ją sobie normalnie retransformować używając indexu zbioru treningowego. Więc jeśli modelujemy np. zmianę procentową, to możemy zrobić procentową retransformację zarówno prognozy jak i expected value. Wtedy jak wrzucimy obydwie wartości w tę samą retransformację opartą o tę samą (ostatnią) obserwację ze zbioru treningowego, to nie ma bata, ale zależność miedzy expected i predicted values przed i po retransformacji muszą być takie same.
    # Retransform expected value
    Ehat, Time, _ = cast_to_base_unit(
        ds_base,
        spec,
        parameters["y_code"],
        model_result["expected_value"],
        dtype="pred",
    )

    header = [parameters["y_code"]]
    Ehat_df = pd.DataFrame(Ehat, columns=header, index=Time)

    expected_retransformed = Ehat_df.loc[reference_date].item()

    shap_values = model_result["shap_values"]

    shap_diff = retr_forecast - expected_retransformed
    shap_contributions = pd.DataFrame(
        {
            "variable_id": list(coef_.index),
            "coef_": coef_,
            "value": values,
            "shap_value": shap_values,
            "impact": shap_values
            * (shap_diff / shap_values.sum()),  # Shap retransformed
        }
    )

    # Post-inference nowcast adjustment
    start_date, end_date = (
        model_result["pred_"]["backcast"].index.min().date(),
        reference_date,
    )
    pred_act = pd.concat(
        [
            Rhat_df.loc[start_date:reference_date].rename(
                columns={parameters["y_code"]: "Predicted"}
            ),
            R_df.loc[start_date:reference_date].rename(
                columns={parameters["y_code"]: "VariableValue"}
            ),
            Rhat_df.shift()
            .loc[start_date:reference_date]
            .rename(columns={parameters["y_code"]: "Lag"}),
        ],
        axis=1,
    )
    eval_df1 = pred_act.loc[:lag_date]

    print("\n======== Retransformed Nowcast ========")
    print(f"Reference Date            : {reference_date}")
    print(f"Retransformed Forecast    : {retr_forecast:,.2f}")
    print(f"R-Squared (R²)            : {r2_score(y_true=eval_df1["VariableValue"], y_pred=eval_df1["Predicted"]):.4f}")
    print(f"Mean Absolute Percentage Error (MAPE): {mape(actual=eval_df1["VariableValue"], predicted=eval_df1["Predicted"]):.2f}%")
    print(f"Root Mean Square Error (RMSE) : {mse(actual=eval_df1["VariableValue"], predicted=eval_df1["Predicted"]):.4f}")

    pred_act["Lag(Actual Change (MoM))"] = (
        pred_act["VariableValue"] - pred_act["Lag"]
    ).shift()
    pred_act["Predicted - Lag"] = pred_act["Predicted"] - pred_act["Lag"]
    df = (
        pred_act.reset_index()
        .rename(columns={"index": "ReferenceDate"})
        .dropna(subset=["Lag"])
    )

    with localconverter(default_converter + pandas2ri.converter):
        # Import the R package
        strucchange = importr("strucchange")
        # Identify breakpoints
        ro.globalenv["y"] = ro.FloatVector(df["Lag"])
        ro.globalenv["reference_date"] = ro.StrVector(df["ReferenceDate"].astype(str))
        ro.r(
            """
            data <- data.frame(y = y, reference_date = reference_date)
            bp_model <- breakpoints(y ~ 1, data = data)
            bp_dates <- data$reference_date[bp_model$breakpoints]
        """
        )

        # Extract breakpoints
        breakpoints = ro.r("bp_model$breakpoints")
        print("\n")
        print("Detected Breakpoints at:", list(breakpoints))

        bp_dates = ro.r("as.character(bp_dates)")
        bp_dates = list(bp_dates)

        print("Structural breaks detected at:", bp_dates)

    pred_act.index = pd.to_datetime(pred_act.index)
    bp_dates = pd.to_datetime(bp_dates)

    baseline = (
        (pred_act["Lag(Actual Change (MoM))"] / pred_act["Lag"])
        .abs()
        .rolling(6)
        .quantile(0.9)
    )  # adaptively high
    ratio = (pred_act["Predicted - Lag"] / pred_act["Lag"]).abs() > np.maximum(
        baseline, 0.015
    )

    dynamic_windows = []
    start, end = np.nan, np.nan

    for i in range(len(bp_dates)):
        start = bp_dates[i]
        try:
            end = bp_dates[i + 1]
        except IndexError:
            end = ratio.index.max()

        window = (ratio > baseline).loc[start:end]

        if window.any():
            end_date = window.loc[window].index.max()
            dynamic_windows.append((start, end_date))

    # Nowcasts adjustment
    pred_act = pred_act.reset_index().rename(columns={"index": "ReferenceDate"})
    pred_act["in_dynamic_window"] = False

    # Check for each window
    for start, end in dynamic_windows:
        pred_act["in_dynamic_window"] |= pred_act["ReferenceDate"].between(start, end)

    # Flag preview
    adjusted_nowcast = pred_act["Lag"]

    pred_act["Nowcast"] = np.where(
        pred_act["in_dynamic_window"], adjusted_nowcast, pred_act["Predicted"]
    )
    eval_df2 = pred_act.loc[pred_act["ReferenceDate"] <= pd.to_datetime(lag_date)]

    # Adjustments should be applied only to forecast values, only if indicated by the Bai-Perron test
    adjusted_forecast = pred_act.loc[
        pred_act["ReferenceDate"] == pd.to_datetime(reference_date)
    ]["Nowcast"].item()

    # Log.INFO
    formatted_windows = [
        (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        for start, end in dynamic_windows
    ]

    print(
        "Nowcasts adjusted for periods flagged by the Bai-Perron structural break test:",
        formatted_windows,
    )
    print("\n")

    print("=============== Summary ===============")
    print(f"Adjusted Forecast    : {adjusted_forecast:,.2f}")
    print(f"R-Squared (R²)            : {r2_score(y_true=eval_df2["VariableValue"], y_pred=eval_df2["Nowcast"]):.4f}")
    print(f"Mean Absolute Percentage Error (MAPE): {mape(actual=eval_df2["VariableValue"], predicted=eval_df2["Nowcast"]):.2f}%")
    print(f"Root Mean Square Error (RMSE) : {mse(actual=eval_df2["VariableValue"], predicted=eval_df2["Nowcast"]):.4f}")

    # Save everything to an Excel file with multiple sheets
    excel_file = os.path.join(
        parameters["model_output_directory"], parameters["ml_report_filename"]
    )

    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        # Save model details as a dataframe
        sheet1 = (
            pd.DataFrame.from_dict(
                {
                    "Model Name": model_result["best_model"],
                    "Series Code": parameters["y_code"],
                    "Reference Date": reference_date,
                    "R-Squared": r2_score(
                        y_true=retr_actuals, y_pred=retr_backcast
                    ),  # model_result['r_squared'],
                    "MAPE": mape(
                        actual=retr_actuals, predicted=retr_backcast
                    ),  # f"{model_result['mape']:.2%}",
                    "RMSE": rmse(
                        actual=retr_actuals, predicted=retr_backcast
                    ),  # f"{model_result['rmse']:.4f}",
                    "Model Estimations Count": model_result["n_est"],
                },
                orient="index",
                columns=["Value"],
            )
            .reset_index()
            .rename(columns={"index": "Banner"})
        )
        sheet1.to_excel(writer, sheet_name="Model Details", index=False)

        # Save contributions
        shap_contributions.to_excel(writer, sheet_name="Contributions")

        # Save forecast and actual values
        R_df = R_df.rename(columns={parameters["y_code"]: "Actual"})
        Rhat_adjusted = pd.concat(
            [
                Rhat_df.loc[:lag_date].rename(
                    columns={parameters["y_code"]: "Predicted"}
                ),
                pd.DataFrame(
                    adjusted_forecast, index=[reference_date], columns=["Predicted"]
                ),
            ]
        )

        # Save confidence bounds
        # Backcast (test) values should be returned without any adjustments
        bounds_level["Predicted"] = Rhat_df.loc[dt][
            parameters["y_code"]
        ]  # retransformed backcast
        pd.DataFrame(bounds_level).to_excel(writer, sheet_name="Confidence Bounds")

        sheet3 = (
            # Adjustments should be applied only to forecast values, only if indicated by the Bai-Perron test
            pd.merge(
                Rhat_adjusted, R_df, how="outer", left_index=True, right_index=True
            )
            .reset_index()
            .rename(columns={"index": "Reference Date"})
        )
        sheet3.to_excel(writer, sheet_name="Forecast vs Actual", index=False)

    return f"Results saved to {excel_file}"


def estimate_arima_node(
    ds: pd.DataFrame,
    ds_base: pd.DataFrame,
    spec: pd.DataFrame,
    parameters: Dict[str, Any],
) -> str:
    """
    Fits an ARIMA model to the time series data and evaluates its performance.

    The function estimates an ARIMA model using the transformed dataset, then re-transforms both predictions and actuals back to their original scale.
    It evaluates model accuracy based on recent historical values and computes standard metrics such as R², MAPE, and RMSE.
    Forecast results, confidence bounds, and model details are saved to an Excel file to serve as a baseline for future benchmarking.

    Args:
        ds: Transformed dataset used for estimation.
        ds_base: Original (raw) dataset used for retransforming predictions.
        spec: Series specification including transformation rules and metadata.
        parameters: Dictionary of configuration parameters such as target variable, reference date, and output paths.

    Returns:
        A string with the path to the saved Excel report.
    """
    model_result = estimate_arima(
        ds=ds,
        ref_date_col=parameters["ref_date_col"],
        series_name=parameters["y_code"],
        reference_date=parameters["ref_date"],
        n_periods=parameters["backcasting_period"],
    )

    reference_date = pd.to_datetime(parameters["ref_date"]).date()

    dt = model_result["pred_"]["backcast"].index
    pred = model_result["pred_"]["backcast"]
    actual = model_result["actual"].loc[dt]

    bounds = calculate_conf_bounds(pred, actual)

    transf_pred = pd.concat(
        [
            model_result["pred_"]["backcast"],
            pd.Series(
                model_result["pred_"]["forecast"],
                index=[pd.to_datetime(model_result["pred_"]["reference_date"])],
            ),
        ]
    )
    transf_actual = model_result["actual"]

    # Retransform forecast
    Rhat, Time, _ = cast_to_base_unit(
        ds_base, spec, parameters["y_code"], transf_pred, dtype="pred"
    )
    R, _, _ = cast_to_base_unit(
        ds_base, spec, parameters["y_code"], transf_actual, dtype="actual"
    )

    header = [parameters["y_code"]]
    Rhat_df = pd.DataFrame(Rhat, columns=header, index=Time)
    R_df = pd.DataFrame(R, columns=header, index=Time)

    reference_date = pd.to_datetime(parameters["ref_date"]).date()
    lag_date = reference_date - relativedelta(months=1)

    retr_backcast = Rhat_df.loc[:lag_date]
    retr_actuals = R_df.loc[:lag_date]

    # calculate confidence bounds
    bounds_level = {}
    for key, value in bounds.items():
        data, dt_, _ = cast_to_base_unit(
            ds_base, spec, parameters["y_code"], value, dtype="pred"
        )
        tmp = pd.Series(data.reshape(1, -1)[0], index=dt_)
        bounds_level[key] = tmp.loc[dt]

    bounds_level["Predicted"] = Rhat_df.loc[dt][
        parameters["y_code"]
    ]  # retransformed backcast

    # Save everything to an Excel file with multiple sheets
    excel_file = os.path.join(
        parameters["model_output_directory"], parameters["ar_report_filename"]
    )

    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        # Save model details as a dataframe
        sheet1 = (
            pd.DataFrame.from_dict(
                {
                    "Model Name": model_result["model"],
                    "Series Code": parameters["y_code"],
                    "Reference Date": reference_date,
                    "R-Squared": r2_score(y_true=retr_actuals, y_pred=retr_backcast),
                    "MAPE": mape(actual=retr_actuals, predicted=retr_backcast),
                    "RMSE": rmse(actual=retr_actuals, predicted=retr_backcast),
                },
                orient="index",
                columns=["Value"],
            )
            .reset_index()
            .rename(columns={"index": "Banner"})
        )
        sheet1.to_excel(writer, sheet_name="Model Details", index=False)

        # Save forecast and actual values
        R_df = R_df.rename(columns={parameters["y_code"]: "Actual"})
        Rhat_df = Rhat_df.rename(columns={parameters["y_code"]: "Predicted"})
        sheet2 = (
            pd.merge(Rhat_df, R_df, how="outer", left_index=True, right_index=True)
            .reset_index()
            .rename(columns={"index": "Reference Date"})
        )
        sheet2.to_excel(writer, sheet_name="Forecast vs Actual", index=False)

        # Save confidence bounds
        pd.DataFrame(bounds_level).to_excel(writer, sheet_name="Confidence Bounds")

    return f"Results saved to {excel_file}"


def estimate_var_node(
    ds: pd.DataFrame,
    ds_base: pd.DataFrame,
    spec: pd.DataFrame,
    parameters: dict,
) -> str:
    """
    Fits a VAR model to the time series data and evaluates its performance.

    This function estimates a Vector Autoregression (VAR) model on the provided dataset.
    After generating predictions, it retransforms both forecasted and actual values to
    their original units for interpretability. Model performance is assessed using
    standard accuracy metrics such as R², MAPE, and RMSE, calculated on the backcast
    (test) period. The results—including predicted values, actual values, confidence
    bounds, and model metadata—are exported to an Excel file. This output serves as a
    benchmark for comparing alternative forecasting methods.

    Args:
        ds: The input dataset containing time series variables, including the target.
        ds_base: The original dataset used to perform inverse transformations.
        spec: A DataFrame containing variable metadata and transformation specifications.
        parameters: A dictionary with configuration keys such as:
            - 'ref_date_col': Name of the reference date column.
            - 'y_code': Target variable identifier.
            - 'ref_date': Cutoff date for forecast.
            - 'backcasting_period': Number of months for backtesting.
            - 'model_output_directory': Output directory for results.
            - 'var_report_filename': Output Excel filename.

    Returns:
        A message indicating the path to the saved Excel file with results.
    """
    model_result = estimate_var(
        ds=ds,
        ref_date_col=parameters["ref_date_col"],
        series_name=parameters["y_code"],
        reference_date=parameters["ref_date"],
        n_periods=parameters["backcasting_period"],
    )

    reference_date = pd.to_datetime(parameters["ref_date"]).date()
    lag_date = reference_date - relativedelta(months=1)

    dt = model_result["pred_"]["backcast"].index
    pred = model_result["pred_"]["backcast"]
    actual = model_result["actual"].loc[dt]

    bounds = calculate_conf_bounds(pred, actual)

    transf_pred = pd.concat(
        [
            model_result["pred_"]["backcast"],
            pd.Series(
                model_result["pred_"]["forecast"],
                index=[pd.to_datetime(model_result["pred_"]["reference_date"])],
            ),
        ]
    )
    transf_actual = model_result["actual"]

    # Retransform forecast
    Rhat, Time, cutoff_date = cast_to_base_unit(
        ds_base, spec, parameters["y_code"], transf_pred, dtype="pred"
    )
    R, _, _ = cast_to_base_unit(
        ds_base, spec, parameters["y_code"], transf_actual, dtype="actual"
    )

    header = [parameters["y_code"]]
    Rhat_df = pd.DataFrame(Rhat, columns=header, index=Time)
    R_df = pd.DataFrame(R, columns=header, index=Time)

    retr_backcast = Rhat_df.loc[:lag_date]
    retr_actuals = R_df.loc[:lag_date]

    # calculate confidence bounds
    bounds_level = {}
    for key, value in bounds.items():
        data, dt_, _ = cast_to_base_unit(
            ds_base, spec, parameters["y_code"], value, dtype="pred"
        )
        tmp = pd.Series(data.reshape(1, -1)[0], index=dt_)
        bounds_level[key] = tmp.loc[dt]
    bounds_level["Predicted"] = Rhat_df.loc[dt][
        parameters["y_code"]
    ]  # retransformed backcast

    # Save everything to an Excel file with multiple sheets
    excel_file = os.path.join(
        parameters["model_output_directory"], parameters["var_report_filename"]
    )

    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        # Save model details as a dataframe
        sheet1 = (
            pd.DataFrame.from_dict(
                {
                    "Model Name": model_result["model"],
                    "Series Code": parameters["y_code"],
                    "Reference Date": reference_date,
                    "R-Squared": r2_score(y_true=retr_actuals, y_pred=retr_backcast),
                    "MAPE": mape(actual=retr_actuals, predicted=retr_backcast),
                    "RMSE": rmse(actual=retr_actuals, predicted=retr_backcast),
                },
                orient="index",
                columns=["Value"],
            )
            .reset_index()
            .rename(columns={"index": "Banner"})
        )
        sheet1.to_excel(writer, sheet_name="Model Details", index=False)

        # Save forecast and actual values
        R_df = R_df.rename(columns={parameters["y_code"]: "Actual"})
        Rhat_df = Rhat_df.rename(columns={parameters["y_code"]: "Predicted"})
        sheet2 = (
            pd.merge(Rhat_df, R_df, how="outer", left_index=True, right_index=True)
            .reset_index()
            .rename(columns={"index": "Reference Date"})
        )
        sheet2.to_excel(writer, sheet_name="Forecast vs Actual", index=False)

        # Save confidence bounds
        pd.DataFrame(bounds_level).to_excel(writer, sheet_name="Confidence Bounds")

    return f"Results saved to {excel_file}"


def collect_results(
    variable: pd.DataFrame,
    vintagedata: pd.DataFrame,
    ts: pd.DataFrame,
    parameters: Dict[str, Any],
    s1: Any,
    s2: Any,
    s3: Any,
) -> str:
    """
    Compiles forecast results, explanatory insights, and metadata into a structured Excel report.

    This function loads the outputs of ARIMA, VAR, and ML models (stored as Excel reports),
    extracts relevant metrics and predictions, and merges them with metadata and actual values.
    It prepares summary cards, detailed breakdowns, and forecast explanations (local and global impact assessments).

    All results are saved to a multi-sheet Excel file, offering a comprehensive snapshot
    of model performance and nowcasting outcomes.

    The resulting Excel file is structured specifically to serve as a backend data model for the visual dashboard.

    Args:
        variable: Specification DataFrame containing metadata (e.g., names, codes, regions).
        vintagedata: Raw time series data with update timestamps and descriptions.
        ts: Full transformed time series data used in modeling.
        parameters: Dictionary containing paths and configuration variables for file I/O and labels.
        s1, s2, s3: Reserved placeholders for future use (currently not used).

    Returns:
        A message indicating the path to the saved Excel report.
    """

    vintagedata[parameters["ref_date_col"]] = pd.to_datetime(
        vintagedata[parameters["ref_date_col"]]
    )

    ar_xl = pd.ExcelFile(
        os.path.join(
            parameters["model_output_directory"], parameters["ar_report_filename"]
        )
    )
    ar_sheets = {}
    for sheet_name in ar_xl.sheet_names:
        ar_sheets[sheet_name] = ar_xl.parse(sheet_name)

    var_xl = pd.ExcelFile(
        os.path.join(
            parameters["model_output_directory"], parameters["var_report_filename"]
        )
    )
    var_sheets = {}
    for sheet_name in var_xl.sheet_names:
        var_sheets[sheet_name] = var_xl.parse(sheet_name)

    ml_xl = pd.ExcelFile(
        os.path.join(
            parameters["model_output_directory"], parameters["ml_report_filename"]
        )
    )
    ml_sheets = {}
    for sheet_name in ml_xl.sheet_names:
        ml_sheets[sheet_name] = ml_xl.parse(sheet_name)

    to_write = {}

    # Cards
    contents = []

    # ARIMA
    reference_date = (
        ar_sheets["Model Details"]
        .loc[ar_sheets["Model Details"]["Banner"] == "Reference Date"]["Value"]
        .item()
    )
    forecast = (
        ar_sheets["Forecast vs Actual"]
        .loc[ar_sheets["Forecast vs Actual"]["Reference Date"] == reference_date][
            "Predicted"
        ]
        .item()
    )
    lag = (
        ar_sheets["Forecast vs Actual"]
        .loc[
            ar_sheets["Forecast vs Actual"]["Reference Date"]
            == reference_date - relativedelta(months=1)
        ]["Actual"]
        .item()
    )

    width = (
        (
            ar_sheets["Confidence Bounds"]["Predicted"]
            - ar_sheets["Confidence Bounds"]["L1"]
        )
        .tail(12)
        .mean()
    )

    contents.append(
        {
            "Card": ar_sheets["Model Details"]
            .loc[ar_sheets["Model Details"]["Banner"] == "Model Name"]["Value"]
            .item(),
            "Value": forecast,
            "Since Last Month": (forecast - lag) / lag,
            "Prediction Range": width,
        }
    )

    # VAR
    reference_date = (
        var_sheets["Model Details"]
        .loc[var_sheets["Model Details"]["Banner"] == "Reference Date"]["Value"]
        .item()
    )
    forecast = (
        var_sheets["Forecast vs Actual"]
        .loc[var_sheets["Forecast vs Actual"]["Reference Date"] == reference_date][
            "Predicted"
        ]
        .item()
    )
    lag = (
        var_sheets["Forecast vs Actual"]
        .loc[
            var_sheets["Forecast vs Actual"]["Reference Date"]
            == reference_date - relativedelta(months=1)
        ]["Actual"]
        .item()
    )

    width = (
        (
            var_sheets["Confidence Bounds"]["Predicted"]
            - var_sheets["Confidence Bounds"]["L1"]
        )
        .tail(12)
        .mean()
    )

    contents.append(
        {
            "Card": var_sheets["Model Details"]
            .loc[var_sheets["Model Details"]["Banner"] == "Model Name"]["Value"]
            .item(),
            "Value": forecast,
            "Since Last Month": (forecast - lag) / lag,
            "Prediction Range": width,
        }
    )

    # ML
    reference_date = (
        ml_sheets["Model Details"]
        .loc[ml_sheets["Model Details"]["Banner"] == "Reference Date"]["Value"]
        .item()
    )
    forecast = (
        ml_sheets["Forecast vs Actual"]
        .loc[ml_sheets["Forecast vs Actual"]["Reference Date"] == reference_date][
            "Predicted"
        ]
        .item()
    )
    lag = (
        ml_sheets["Forecast vs Actual"]
        .loc[
            ml_sheets["Forecast vs Actual"]["Reference Date"]
            == reference_date - relativedelta(months=1)
        ]["Actual"]
        .item()
    )

    width = (
        (
            ml_sheets["Confidence Bounds"]["Predicted"]
            - ml_sheets["Confidence Bounds"]["L1"]
        )
        .tail(12)
        .mean()
    )

    contents.append(
        {
            "Card": "Confidence Interval",
            "Value": width,
            "Since Last Month": (forecast - lag) / lag,
            "Prediction Range": "",
        }
    )

    to_write["Cards"] = pd.DataFrame(contents)

    # Nowcast Browser – Header
    reference_date = (
        ml_sheets["Model Details"]
        .loc[ml_sheets["Model Details"]["Banner"] == "Reference Date"]["Value"]
        .item()
    )
    forecast = (
        ml_sheets["Forecast vs Actual"]
        .loc[ml_sheets["Forecast vs Actual"]["Reference Date"] == reference_date][
            "Predicted"
        ]
        .item()
    )
    lag = (
        ml_sheets["Forecast vs Actual"]
        .loc[
            ml_sheets["Forecast vs Actual"]["Reference Date"]
            == reference_date - relativedelta(months=1)
        ]["Actual"]
        .item()
    )
    series_code = (
        ml_sheets["Model Details"]
        .loc[ml_sheets["Model Details"]["Banner"] == "Series Code"]["Value"]
        .item()
    )
    LastUpdatedOnSource = pd.to_datetime(vintagedata["LastUpdatedOnSource"]).max()

    contents = {
        "Value": forecast,
        "Since Last Month": (forecast - lag) / lag,
        "Series Name": variable.loc[variable["seriesid"] == series_code][
            "seriesname"
        ].item(),
        "Series Code": series_code,
        "Reference Period": f"{reference_date.strftime('%b')} 1 - {reference_date.strftime('%b')} {pd.Period(reference_date.strftime('%Y-%m')).days_in_month}",
        "Region": variable.loc[variable["seriesid"] == series_code]["region"].item(),
        "Unit": variable.loc[variable["seriesid"] == series_code]["units"].item(),
        "Last Run Watermark": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "Data as of": LastUpdatedOnSource.strftime("%d/%m/%Y %H:%M"),
    }

    to_write["Nowcast Browser – Header"] = (
        pd.DataFrame.from_dict(contents, orient="index")
        .reset_index()
        .rename(columns={"index": "Banner", 0: "Value"})
    )

    # Nowcast Browser – Base
    reference_date = (
        ml_sheets["Model Details"]
        .loc[ml_sheets["Model Details"]["Banner"] == "Reference Date"]["Value"]
        .item()
    )

    traces = ml_sheets["Forecast vs Actual"].loc[
        (
            ml_sheets["Forecast vs Actual"]["Reference Date"]
            >= (reference_date - relativedelta(months=18))
        )
        & (ml_sheets["Forecast vs Actual"]["Reference Date"] <= reference_date)
    ]
    traces.loc[(traces["Reference Date"] == reference_date), "Actual"] = None
    to_write["Nowcast Browser – Base"] = traces

    # Local Explanation
    reference_date = (
        ml_sheets["Model Details"]
        .loc[ml_sheets["Model Details"]["Banner"] == "Reference Date"]["Value"]
        .item()
    )
    forecast = (
        ml_sheets["Forecast vs Actual"]
        .loc[ml_sheets["Forecast vs Actual"]["Reference Date"] == reference_date][
            "Predicted"
        ]
        .item()
    )
    lag = (
        ml_sheets["Forecast vs Actual"]
        .loc[
            ml_sheets["Forecast vs Actual"]["Reference Date"]
            == reference_date - relativedelta(months=1)
        ]["Actual"]
        .item()
    )

    impact_assessment = ml_sheets["Contributions"][["Unnamed: 0", "impact"]].rename(
        columns={"Unnamed: 0": "Series ID", "impact": "Impact"}
    )

    tmp = vintagedata.loc[
        (
            vintagedata[parameters["series_code_col"]].isin(
                list(impact_assessment["Series ID"])
            )
        )
        & (vintagedata[parameters["ref_date_col"]] <= reference_date)
    ]

    actuals = (
        tmp.merge(
            tmp.groupby([parameters["series_code_col"]])
            .agg({parameters["ref_date_col"]: "max"})
            .reset_index(),
            on=[parameters["series_code_col"], parameters["ref_date_col"]],
        )[
            [
                parameters["series_code_col"],
                "Description",
                parameters["ref_date_col"],
                "LastUpdatedOnSource",
            ]
        ]
        .groupby(
            [parameters["series_code_col"], "Description", parameters["ref_date_col"]]
        )
        .min()
        .reset_index()
        .rename(
            columns={
                parameters["series_code_col"]: "Series ID",
                "Description": "Data Series",
                "LastUpdatedOnSource": "Release Date",
            }
        )
    )

    impact_assessment = impact_assessment.merge(actuals, on="Series ID", how="left")
    to_write["Local Explanation"] = impact_assessment[
        ["Release Date", "Series ID", "Data Series", "Impact"]
    ]

    #  Global Explanation
    series_code = (
        ml_sheets["Model Details"]
        .loc[ml_sheets["Model Details"]["Banner"] == "Series Code"]["Value"]
        .item()
    )
    reference_date = (
        ml_sheets["Model Details"]
        .loc[ml_sheets["Model Details"]["Banner"] == "Reference Date"]["Value"]
        .item()
    )
    df = ts.set_index(parameters["ref_date_col"])[
        list(impact_assessment["Series ID"]) + [series_code]
    ]
    df.loc[reference_date, series_code] = None

    # Melt wide DataFrame to long format
    df_long = (
        df.sort_index()
        .loc[reference_date - relativedelta(months=12) : reference_date]
        .reset_index()
        .melt(
            id_vars=[parameters["ref_date_col"]],
            var_name="Variable Code",
            value_name="Variable Value",
        )
    )

    to_write["Global Explanation"] = df_long

    # Model Assessment
    df = (
        ml_sheets["Model Details"]
        .loc[
            ml_sheets["Model Details"]["Banner"].isin(
                ["R-Squared", "MAPE", "Model Estimations Count"]
            )
        ]
        .rename(columns={"Banner": "Measure"})
    )
    df["Measure"] = df["Measure"].replace(
        {"R-Squared": "Adjusted R-Squared", "MAPE": "Average Error Rate"}
    )
    df = pd.concat(
        [
            df,
            pd.DataFrame(
                {
                    "Measure": "Processed Variables Count",
                    "Value": vintagedata["VariableCode"].nunique(),
                },
                index=[0],
            ),
        ]
    )

    to_write["Model Assessment"] = df

    excel_file = os.path.join(
        parameters["reporting_directory"], parameters["out_report_filename"]
    )

    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        for sheet_name, contents in to_write.items():
            contents.to_excel(writer, sheet_name=sheet_name, index=False)
    return f"Results saved to {excel_file}"
