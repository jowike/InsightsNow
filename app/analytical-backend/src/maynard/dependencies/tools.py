import re
import numpy as np
import pandas as pd
from typing import List, Dict

import warnings

warnings.filterwarnings("ignore")


def cast_spec_to_dict(df: pd.DataFrame) -> Dict[str, list]:
    """
    Convert a model specification DataFrame into a dictionary format.

    This function processes a DataFrame containing model specifications, ensuring
    column headers are lowercase and extracting required fields (`seriesid`,
    `frequency`, and `transformation`). It raises an error if any of the required
    columns are missing.

    Args:
        df: The input DataFrame containing variables characteristics.

    Returns:
        A dictionary with keys corresponding to column names and values as lists.

    Raises:
        ValueError: If any required column is missing.
    """

    raw_data = df.copy()
    # Convert all headers to lowercase for consistency
    raw_data.columns = raw_data.columns.str.lower()

    # Initialize spec dictionary
    spec = {}

    # Fields to extract from the Excel file
    field_names = [
        "seriesid",
        "seriesname",
        "frequency",
        "transformation",
        "units",
        "category",
        "model",
    ]
    # Extract required fields and ensure they exist
    for field in field_names:
        if field not in raw_data.columns:
            raise ValueError(f"{field} column missing from model specification.")
        spec[field] = raw_data[field].tolist()

    return spec


def suggest_transformation(unit: str) -> str:
    """
    Suggest a suitable transformation code based on the description of the unit.

    This function uses regular expressions to classify unit descriptions and returns
    a suggested transformation code commonly used in macroeconomic modeling.

    Args:
        unit: A string describing the unit of a time series (e.g., 'Billions of Chained 2017 Dollars').

    Returns:
        A string representing the suggested transformation:
            - 'pc1' for year-over-year percent change
            - 'ch1' for year-over-year level change
            - 'lin' for no transformation
    """
    if re.search(
        r"(Billions|Millions|Thousands)\s+of\s+Chained\s+\d{4}\s+Dollars", unit
    ):
        return "pc1"

    if re.search(r"Index", unit):
        return "ch1"  # Wskaźniki, np. CPI, używamy zmiany

    if re.search(r"Percent", unit):
        return "lin"  # Jeśli jednostka to Percent, nie stosujemy transformacji

    if re.search(r"Percent\s+Change\s+at\s+Annual\s+Rate", unit):
        return "lin"  # Jeśli to już procentowa zmiana roczna, nie wymagamy dalszej transformacji

    if re.search(r"Level", unit):
        return "pc1"  # Poziomy (np. liczba osób, PKB) — stosujemy procentową zmianę roczną (pca)

    if re.search(r"Ratio", unit):
        return "lin"  # Wskaźniki proporcji — nie wymagają transformacji

    if re.search(r"Rate", unit):
        return "lin"  # Stopy procentowe (np. procentowa stopa bezrobocia) — pozostawiamy bez zmian

    if re.search(
        r"(Dollars|Euro|Yen|Pounds|Rupees|Franc|Pesos)\s+per\s+[A-Za-z]+", unit
    ):
        return "pc1"  # Ceny jednostkowe (np. "Dollars per Gallon") — zmiana procentowa

    if re.search(r"Thousands\s+of\s+[A-Za-z]+", unit):
        return "pc1"  # Jednostki liczbowe w tysiącach — logarytmizacja

    return "ch1"


def _convert_to_datetime(df: pd.DataFrame, colnames: List[str]) -> pd.DataFrame:
    """
    Convert specified columns in a DataFrame to datetime format.

    Args:
        df (pd.DataFrame): Input DataFrame.
        colnames (List[str]): List of column names to convert.

    Returns:
        pd.DataFrame: DataFrame with updated datetime columns.
    """
    for col in colnames:
        df[col] = pd.to_datetime(df[col])
    return df


def _align_dates(dataframe: pd.DataFrame, date_colname: str) -> pd.DataFrame:
    """
    Align reference dates to the 1st. days of months.

    Args:
        dataframe (pd.DataFrame): Input DataFrame with a date column.
        date_colname (str): Name of the date column to adjust.

    Returns:
        pd.DataFrame: DataFrame with dates aligned to the first of the month.
    """
    df = dataframe.reset_index(drop=True).reset_index()
    df[date_colname] = df[date_colname].apply(lambda x: x.replace(day=1))
    return df.drop(columns=["index"])


def _error(actual: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    """
    Compute simple forecast error.

    Args:
        actual (np.ndarray): Ground truth values.
        predicted (np.ndarray): Forecasted values.

    Returns:
        np.ndarray: Element-wise error (actual - predicted).
    """
    return actual - predicted


def _percentage_error(actual: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    """
    Compute element-wise percentage error.

    Note:
        Result is NOT multiplied by 100 (i.e., result is in decimal form).

    Args:
        actual (np.ndarray): Ground truth values.
        predicted (np.ndarray): Forecasted values.

    Returns:
        np.ndarray: Element-wise percentage error.
    """
    EPSILON = 1e-10
    return _error(actual, predicted) / (actual + EPSILON)


def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Compute Mean Absolute Percentage Error (MAPE).

    Note:
        Result is NOT multiplied by 100 (i.e., result is in decimal form).

    Args:
        actual (np.ndarray): Ground truth values.
        predicted (np.ndarray): Forecasted values.

    Returns:
        float: Mean absolute percentage error.
    """
    return np.mean(np.abs(_percentage_error(actual, predicted)))


def mse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Compute Mean Squared Error (MSE).

    Args:
        actual (np.ndarray): Ground truth values.
        predicted (np.ndarray): Forecasted values.

    Returns:
        float: Mean squared error.
    """
    return np.mean(np.square(_error(actual, predicted)))


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Compute Root Mean Squared Error (RMSE).

    Args:
        actual (np.ndarray): Ground truth values.
        predicted (np.ndarray): Forecasted values.

    Returns:
        float: Root mean squared error.
    """
    return np.sqrt(mse(actual, predicted))
