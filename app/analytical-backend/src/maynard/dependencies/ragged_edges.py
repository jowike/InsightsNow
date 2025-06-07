import pandas as pd


def shift_to_fill_trailing_nans(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Handle the ragged edge problem by shifting time series to fill trailing NaNs.

    For each column with trailing missing values, this function determines how far 
    the last non-NaN value is from the end of the series and shifts the entire 
    column forward by that amount.

    Args:
        dataframe (pd.DataFrame): DataFrame with time series data (columns = variables).

    Returns:
        pd.DataFrame: A new DataFrame with adjusted columns where possible.
    """
    # Iterate over each column in the DataFrame
    for column in dataframe.columns:
        series = dataframe[column]
        
        # Check if the column has missing values at the end
        if series.iloc[-1:].isna().all():
            # Find the index of the last non-NaN value
            last_valid_index = series.last_valid_index()
            
            # If a valid non-NaN index exists, create a lagged version of the series
            if last_valid_index is not None:
                lag_amount = len(series) - series.index.get_loc(last_valid_index) - 1
                dataframe[column] = series.shift(lag_amount)
    
    return dataframe
