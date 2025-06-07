import numpy as np
import pandas as pd
import warnings
from typing import Union, Tuple, Optional, Dict, List


def load_data(
    ds: Union[str, pd.DataFrame],
    Spec: dict,
    sample: Optional[float] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, list]:
    """
    Load vintage of data from file and format as structure

    This function reads the dataset, sorts and transforms it
    according to the model specification dictionary, and returns both the transformed
    and raw versions, aligned in time and optionally filtered to a sample period.

    Args:
        datafile: Filename of Microsoft Excel workbook file
        Spec: Model specification containing SeriesID and other info
        sample: Sample period start date in numeric form

    Returns:
        X: T x N numeric array, transformed dataset
        Time: T x 1 numeric array, date number with observation dates
        Z: T x N numeric array, raw (untransformed) dataset
        header: List of series names or identifiers used in the dataset.
    """
    print("Loading data...")

    Z, Time, Mnem = read_data(ds)

    # Sort data based on model specification
    Z = sort_data(Z, Mnem, Spec)

    # Transform data based on model specification
    X, Time, Z, header = transform_data(Z, Time, Spec)

    # Drop data not in estimation sample
    if sample is not None:
        X, Time, Z = drop_data(X, Time, Z, sample)

    return X, Time, Z, header


def read_data(ds: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Read data from Microsoft Excel workbook file

    The input DataFrame is expected to follow a specific format:
    - First row: Variable names (series identifiers), starting from column 1.
    - First column (excluding first row): Time index values.
    - Remaining values: Observations of time series data.

    Args:
        datafile: Filename of the Excel file

    Returns:
        Z: Raw (untransformed) observed data
        Time: Observation periods for the time series data
        Mnem: Series ID for each variable
    """
    # df = pd.read_excel(datafile, sheet_name='data', header=None, engine="openpyxl")
    Mnem = ds.iloc[0, 1:].tolist()
    Time = ds.iloc[1:, 0].to_numpy()
    Z = ds.iloc[:, 1:].to_numpy()
    return Z, Time, Mnem


def sort_data(Z: np.ndarray, Mnem: List[str], Spec: Dict[str, List[str]]) -> np.ndarray:
    """
    Sort series by order of model specification

    This function filters out any series not included in the model spec, then reorders
    the remaining columns in `Z` to align with the order in `Spec["seriesid"]`.

    Args:
        Z (np.ndarray): Raw data
        Mnem (list): Series ID for each variable
        Spec (dict): Model specification

    Returns:
        Z (np.ndarray): Sorted data according to Spec.SeriesID
    """
    in_spec = np.isin(Mnem, Spec["seriesid"])
    Mnem = [mnem for mnem, keep in zip(Mnem, in_spec) if keep]
    Z = Z[:, in_spec]

    # Sort series by ordering of Spec
    N = len(Spec["seriesid"])
    permutation = [Mnem.index(spec_id) for spec_id in Spec["seriesid"]]

    Mnem = [Mnem[i] for i in permutation]
    Z = Z[:, permutation]

    return Z


def transform_data(
    Z: np.ndarray, Time: np.ndarray, Spec: Dict[str, List]
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """
    Transforms each data series based on Spec.Transformation

    Applies various differencing, percent change, and log transformations to make
    series stationary and suitable for dynamic factor modeling.

    Parameters:
        Z: Raw (untransformed) observed data (T+1 × N), including a header row at position 0.
        Time: Observation periods for the time series data (T+1,) aligned with `Z`.
        Spec: Model specification – transformation metadata. Required keys:
            - 'seriesid': List of variable names.
            - 'seriesname': List of human-readable names.
            - 'transformation': List of transformation codes (e.g., 'lin', 'chg', etc.).
            - 'frequency': List with 'm' or 'q' for monthly/quarterly.
    Returns:
        X: Transformed data array (T × N) – typically stationary.
        Time: Adjusted time array, with early entries removed due to lags.
        Z: Adjusted raw data array (T × N), excluding header and initial rows.
        header: List of variable names from the original dataset.
    """
    header = Z[0, :]
    Z = np.float64(Z[1:, :])

    T, N = Z.shape

    X = np.full((T, N), np.nan)

    for i in range(N):
        formula = Spec["transformation"][i]
        freq = Spec["frequency"][i]
        step = 1 if freq == "m" else 3
        t1 = step
        n = step / 12

        assert header[i] == Spec["seriesid"][i]
        series = Spec["seriesname"][i]

        # Apply transformations based on formula
        if formula == "lin":  # Levels (No Transformation)
            X[:, i] = Z[:, i]
        elif formula == "chg":  # Change (Difference)
            X[(t1 - 1 + step) : T, i] = (
                Z[(t1 - 1 + step) : T, i] - Z[(t1 - 1) : (T - t1), i]
            )
        elif formula == "ch1":  # Year over Year Change (Difference)
            if T > 12:
                X[(12 + t1 - 1) : T, i] = (
                    Z[(12 + t1 - 1) : T, i] - Z[(t1 - 1) : (T - 12), i]
                )
        elif formula == "pch":  # Percent Change
            X[(t1 - 1 + step) : T, i] = 100 * (
                Z[(t1 - 1 + step) : T, i] / Z[(t1 - 1) : (T - t1), i] - 1
            )
        elif formula == "pc1":  # Year over Year Percent Change
            if T > 12:
                # Year over Year Percent Change, handle division by zero
                X[(12 + t1 - 1) : T, i] = 100 * (
                    Z[(12 + t1 - 1) : T, i] / Z[(t1 - 1) : (T - 12), i] - 1
                )
        elif formula == "pca":  # Percent Change (Annual Rate)
            X[(t1 - 1 + step) : T, i] = 100 * (
                (Z[(t1 - 1 + step) : T, i] / Z[(t1 - 1) : (T - step), i]) ** (1 / n) - 1
            )
        elif formula == "log":  # Natural Log
            X[:, i] = np.log(Z[:, i])
        else:
            warnings.warn(
                f"Transformation '{formula}' not found for {series}. Using untransformed data."
            )
            X[:, i] = Z[:, i]

    # Drop first quarter of observations since transformations cause missing values
    Time = Time[3:]
    Z = Z[3:, :]
    X = X[3:, :]

    return X, Time, Z, header


def drop_data(
    X: np.ndarray, Time: np.ndarray, Z: np.ndarray, sample: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Removes observations that fall before the start of the estimation sample period.

    Args:
        X: Transformed data array.
        Time: Array of observation dates.
        Z: Raw (untransformed) data array.
        sample: Start date for the estimation sample.

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: Filtered versions of X, Time, and Z
        containing only observations from the sample period onward.
    """
    idx_drop = Time < sample

    Time = Time[~idx_drop]
    X = X[~idx_drop, :]
    Z = Z[~idx_drop, :]

    return X, Time, Z
