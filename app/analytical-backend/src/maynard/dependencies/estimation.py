import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from typing import Tuple, Union, Dict, Any

from sklearn.metrics import r2_score
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.base import BaseEstimator

from lineartree import LinearForestRegressor
import pmdarima as pm
from statsmodels.tsa.api import VAR
import shap

from maynard.dependencies.tools import (
    _convert_to_datetime,
    rmse,
    mape,
    cast_spec_to_dict,
)
from maynard.dependencies.retransform_prediction import retransform_
from maynard.dependencies.retransform_data import retransform_data


def ml_fit_predict(
    ds: pd.DataFrame,
    ref_date_col: str,
    model: BaseEstimator,
    series_name: str,
    reference_date: Union[str, pd.Timestamp],
    n_periods: int,
) -> Tuple[
    pd.Series,  # coef_
    pd.Series,  # expected_value
    pd.Series,  # shap_values
    pd.DataFrame,  # yhat
    pd.DatetimeIndex,  # T
    pd.Series,  # X_test
    int,  # number of iterations (n_periods)
]:
    """
    Trains an ML model in a rolling window (cascading) setup and generates SHAP explanations
    for the final prediction.

    Args:
        ds: Input DataFrame with target and features in long format.
        ref_date_col: Name of the column representing reference dates (e.g., 'REF_DATE').
        model: A scikit-learn compatible estimator with `fit` and `predict` methods.
        series_name: Name of the target variable column.
        reference_date: Forecasting reference point (as string or timestamp).
        n_periods: Number of cascading iterations (months to backtest).

    Returns:
        A tuple containing:
            - coef_: Coefficients or feature importances of the final fitted model.
            - expected_value: SHAP expected value for the final test sample.
            - shap_values: SHAP feature attributions for the final test sample.
            - yhat: DataFrame with actual vs. predicted values for all test dates.
            - T: DatetimeIndex of all test dates used for evaluation.
            - X_test: Final test sample used for SHAP explanations.
            - Number of test dates (equals n_periods).
    """

    # Define the prediction function for the model
    def predict_fn(X):
        return model.predict(
            X
        )  # Make sure this returns the correct shape for predictions

    reference_date = pd.to_datetime(reference_date, format="%Y-%m-%d")

    df = _convert_to_datetime(df=ds, colnames=[ref_date_col])
    df = df.set_index(ref_date_col)

    # Create a list of test dates in reverse chronological order
    T = pd.to_datetime(
        [
            (reference_date - relativedelta(months=i))
            for i in range(n_periods - 1, -1, -1)
        ],
        format="%Y-%m-%d",
    )

    # Cascading model training: re-train the model at each time step and forecast one month ahead
    yhat = pd.DataFrame()
    for test_date in T:
        X, y = df.drop(columns=[series_name]), df[series_name]

        train_index, test_index = y.loc[y.index < test_date].index, test_date

        X_train, y_train = X.loc[train_index], y.loc[train_index]
        X_test, y_test = X.loc[[test_index]], y.loc[[test_index]]

        assert X_test.shape[0] == y_test.shape[0] == 1

        model.fit(X_train, y_train)
        pred_ = model.predict(X_test)

        yhat = pd.concat(
            [
                yhat,
                pd.DataFrame(
                    {"y_pred": pred_, "y_actual": y_test},
                    index=[test_date],
                ),
            ]
        )

    # Coefficients values
    try:
        coef_ = pd.Series(model.coef_, index=X_train.columns)
    except AttributeError:
        coef_ = pd.Series(model.feature_importances_, index=X_train.columns)
    except ValueError:
        coef_ = pd.Series(
            model.base_estimator_.fit(X_train, y_train).coef_[0],
            index=X_train.columns,
        )

    # SHAP KernelExplainer
    background_data = shap.kmeans(X_train, k=60)
    explainer = shap.KernelExplainer(predict_fn, background_data)
    shap_values = pd.Series(
        explainer.shap_values(X_test, silent=True)[0], index=X_train.columns
    )
    expected_value = pd.Series(explainer.expected_value, index=X_test.index)
    expected_value.index.name = "reference_date"

    # TODO: elasticity-based impact assessment (contributions)

    return coef_, expected_value, shap_values, yhat, T, X_test.squeeze(axis=0), len(T)


def arima_fit_predict(
    ds: pd.DataFrame,
    ref_date_col: str,
    series_name: str,
    reference_date: Union[str, pd.Timestamp],
    n_periods: int,
) -> pd.DataFrame:
    """
    Trains an ARIMA model in a cascading fashion to produce recursive one-step-ahead forecasts.

    At each time step, the model is trained on all data up to that point and used to forecast
    the next value of the target series.

    Args:
        ds: Input DataFrame with a datetime reference column and a univariate series to forecast.
        ref_date_col: Name of the datetime column to be parsed and set as index.
        series_name: Name of the column containing the target time series.
        reference_date: The end point of the backtest window, in YYYY-MM-DD format or Timestamp.
        n_periods: Number of months to backcast recursively.

    Returns:
        A DataFrame with forecasted values (`y_pred`) and actual observations (`actual`)
        for each evaluated date.
    """

    def __arima_feed(series: pd.Series, h: int = 6) -> pd.Series:
        """
        Trains an ARIMA model and forecasts `h` periods ahead.

        Args:
            series: Time series to fit.
            h: Forecast horizon (default is 6).

        Returns:
            Forecasted values as a pandas Series with datetime index.
        """
        series = series.dropna()
        arima_model = pm.auto_arima(series, stepwise=True)
        forecast = arima_model.predict(n_periods=h)
        forecast_index = pd.date_range(
            series.index[-1] + relativedelta(months=1), periods=h, freq="MS"
        )
        forecast_series = pd.Series(forecast, index=forecast_index)
        return forecast_series

    reference_date = pd.to_datetime(reference_date, format="%Y-%m-%d")

    df = _convert_to_datetime(df=ds, colnames=[ref_date_col])
    df = df.set_index(ref_date_col)

    test_dates = pd.to_datetime(
        [
            (reference_date - relativedelta(months=i))
            for i in range(n_periods - 1, -1, -1)
        ],
        format="%Y-%m-%d",
    )

    # Cascading model training: re-train the model at each time step and forecast one month ahead
    to_write = pd.DataFrame()
    for test_date in test_dates:
        # Split between train and test subsets
        y_train, y_test = (
            df[[series_name]].loc[df.index < test_date],
            df[[series_name]].loc[df.index == test_date],
        )
        # AR forecast inference
        y_pred = y_train.apply(__arima_feed, h=y_test.shape[0], axis=0)

        to_write = pd.concat(
            [
                to_write,
                pd.merge(
                    y_pred.rename(columns={series_name: "y_pred"}),
                    y_test.rename(columns={series_name: "actual"}),
                    left_index=True,
                    right_index=True,
                ),
            ]
        )
    return to_write


def var_fit_predict(
    ds: pd.DataFrame,
    ref_date_col: str,
    series_name: str,
    reference_date: Union[str, pd.Timestamp],
    n_periods: int,
) -> pd.DataFrame:
    """
    Trains a VAR model in a cascading fashion and generates one-step-ahead forecasts.

    At each iteration, the model is trained on all available data up to a given test date.
    It then forecasts the target series for that point in time.

    Args:
        ds: Input DataFrame containing time series features and a target series.
        ref_date_col: Name of the column containing reference dates.
        series_name: Name of the column representing the target variable.
        reference_date: Last date to include in the evaluation window (YYYY-MM-DD or Timestamp).
        n_periods: Number of monthly iterations for cascading backtesting.

    Returns:
        A DataFrame with predicted and actual values for each evaluation date.
    """
    reference_date = pd.to_datetime(reference_date, format="%Y-%m-%d")

    df = _convert_to_datetime(df=ds, colnames=[ref_date_col])
    df = df.set_index(ref_date_col)

    test_dates = pd.to_datetime(
        [
            (reference_date - relativedelta(months=i))
            for i in range(n_periods - 1, -1, -1)
        ],
        format="%Y-%m-%d",
    )

    # Cascading model training
    to_write = pd.DataFrame()
    for test_date in test_dates:
        X, y = df.drop(columns=[series_name]), df[series_name]

        train_index, test_index = y.loc[y.index < test_date].index, test_date

        X_train, y_train = X.loc[train_index], y.loc[train_index]
        X_test, y_test = X.loc[[test_index]], y.loc[[test_index]]

        assert X_test.shape[0] == y_test.shape[0] == 1
        train_data = pd.merge(X_train, y_train, left_index=True, right_index=True)
        y_test.index = pd.to_datetime(y_test.index)
        test_data = pd.merge(X_test, y_test, left_index=True, right_index=True)

        var_model = VAR(train_data)
        var_fit = var_model.fit(
            maxlags=1
        )  # You can adjust the maxlags based on the model's AIC/BIC criteria

        # train_preds = var_fit.fittedvalues

        lag_order = var_fit.k_ar
        forecast_input = train_data.values[-lag_order:]
        forecast_output = pd.DataFrame(
            var_fit.forecast(y=forecast_input, steps=len(test_data)),
            columns=test_data.columns,
        )

        to_write = pd.concat(
            [
                to_write,
                pd.DataFrame(
                    {
                        "y_pred": forecast_output[series_name].item(),
                        "actual": y_test.item(),
                    },
                    index=[test_date],
                ),
            ]
        )

    return to_write


def estimate_automl(
    ds: pd.DataFrame,
    ref_date_col: str,
    series_name: str,
    reference_date: Union[str, pd.Timestamp],
    n_periods: int,
) -> Dict[str, Any]:
    """
    Automatically trains multiple models, evaluates them using R², and selects the best one.

    This function fits several regressors on rolling backtests, compares their in-sample
    predictive accuracy, and selects the best-performing model based on R-squared.
    It also computes SHAP explanations and prediction errors.

    Args:
        ds: Input DataFrame containing features and target series.
        ref_date_col: Name of the column with time information (e.g., 'REF_DATE').
        series_name: Name of the target column to forecast.
        reference_date: Cutoff date (as str or Timestamp) for the forecast horizon.
        n_periods: Number of monthly backtesting steps to run per model.

    Returns:
        A dictionary with:
            - 'best_model': Name of the best model.
            - 'r_squared': R² score of the best model.
            - 'coef_': Feature coefficients or importances.
            - 'expected_value': SHAP expected value.
            - 'shap_values': SHAP attributions.
            - 'values': SHAP input values.
            - 'pred_': Full prediction dictionary.
            - 'actual': Actual values for backcast + forecast.
            - 'rmse': Root Mean Squared Error.
            - 'mape': Mean Absolute Percentage Error.
            - 'n_est': Total number of model estimations performed.
    """
    models = {
        "LinearRegression": LinearRegression(),
        "Ridge": Ridge(),
        "LinearForest": LinearForestRegressor(
            base_estimator=Ridge(), random_state=42, max_features="log2"
        ),
        "RandomForestRegressor": RandomForestRegressor(),
    }

    models_results = {}
    n_est = 0
    for model_name, model in models.items():
        coef_, expected_value, shap_values, pred, T, values, n_iter = ml_fit_predict(
            ds=ds,
            ref_date_col=ref_date_col,
            model=model,
            series_name=series_name,
            reference_date=reference_date,
            n_periods=n_periods,
        )

        models_results[model_name] = {
            "backcast": pred["y_pred"].drop(reference_date),
            "forecast": pred["y_pred"].loc[reference_date],
            "reference_date": reference_date,
            "coef_": coef_,
            "expected_value": expected_value,
            "shap_values": shap_values,
            "values": values,
        }
        n_est = n_est + n_iter

    # Ensure all predictions align with the actuals index
    y_actual = ds.set_index(ref_date_col).loc[T].sort_index()[series_name]

    # Select the best model based on R-squared
    best_model_res = select_model_by_r2(models_results, y_actual.drop(reference_date))
    best_model_res["actual"] = y_actual
    best_model_res["rmse"] = rmse(
        actual=y_actual.drop(reference_date),
        predicted=models_results[model_name]["backcast"],
    )
    best_model_res["mape"] = mape(
        actual=y_actual.drop(reference_date),
        predicted=models_results[model_name]["backcast"],
    )
    best_model_res["n_est"] = n_est

    return best_model_res


def estimate_arima(
    ds: pd.DataFrame,
    ref_date_col: str,
    series_name: str,
    reference_date: Union[str, pd.Timestamp],
    n_periods: int,
) -> Dict[str, Any]:
    """
    Estimates an ARIMA model and evaluates its performance using a cascading forecast approach.

    The model is trained on expanding windows and used to backcast and forecast a univariate series.
    Backcast results are used to calculate accuracy metrics and identify forecast quality.

    Args:
        ds: Input DataFrame containing the time series to forecast.
        series_name: Name of the target variable.
        reference_date: Date at which to split training and forecast evaluation (str or Timestamp).
        n_periods: Number of monthly backtest periods to run.

    Returns:
        A dictionary containing:
            - 'model': Name of the model.
            - 'r_squared': R² score for the backcast period.
            - 'pred_': Dictionary with backcast and forecast predictions.
            - 'actual': Actual observed values.
            - 'rmse': Root Mean Squared Error.
            - 'mape': Mean Absolute Percentage Error.
    """
    ar_pred = arima_fit_predict(
        ds=ds,
        ref_date_col=ref_date_col,
        series_name=series_name,
        reference_date=reference_date,
        n_periods=n_periods,
    )
    y_actual = ar_pred["actual"]
    backcast = ar_pred["y_pred"].drop(reference_date)

    model_info = {
        "model": "ARIMA",
        "r_squared": r2_score(y_true=y_actual.drop(reference_date), y_pred=backcast),
        "pred_": {
            "backcast": backcast,
            "forecast": ar_pred["y_pred"].loc[reference_date],
            "reference_date": reference_date,
        },
        "actual": y_actual,
        "rmse": rmse(actual=y_actual.drop(reference_date), predicted=backcast),
        "mape": mape(actual=y_actual.drop(reference_date), predicted=backcast),
    }

    return model_info


def estimate_var(
    ds: pd.DataFrame,
    ref_date_col: str,
    series_name: str,
    reference_date: Union[str, pd.Timestamp],
    n_periods: int,
) -> Dict[str, Any]:
    """
    Estimates a Vector Autoregression (VAR) model and evaluates its performance.

    This function uses a cascading forecast strategy to repeatedly train a VAR model
    on expanding time windows. It evaluates model performance on backcasted values and
    produces one-step-ahead forecast for the reference date.

    Args:
        ds: Input DataFrame with all time series, including the target.
        series_name: Name of the target series to forecast.
        reference_date: Forecast cutoff date (str or Timestamp).
        n_periods: Number of months for rolling backtest.

    Returns:
        A dictionary containing:
            - 'model': Model name.
            - 'r_squared': R² score on backcast.
            - 'pred_': Dictionary with backcast and forecast values.
            - 'actual': Actual observed values for comparison.
            - 'rmse': Root Mean Squared Error.
            - 'mape': Mean Absolute Percentage Error.
    """
    var_pred = var_fit_predict(
        ds=ds,
        ref_date_col=ref_date_col,
        series_name=series_name,
        reference_date=reference_date,
        n_periods=n_periods,
    )
    y_actual = var_pred["actual"]
    backcast = var_pred["y_pred"].drop(reference_date)

    model_info = {
        "model": "VAR",
        "r_squared": r2_score(y_true=y_actual.drop(reference_date), y_pred=backcast),
        "pred_": {
            "backcast": backcast,
            "forecast": var_pred["y_pred"].loc[reference_date],
            "reference_date": reference_date,
        },
        "actual": y_actual,
        "rmse": rmse(actual=y_actual.drop(reference_date), predicted=backcast),
        "mape": mape(actual=y_actual.drop(reference_date), predicted=backcast),
    }

    return model_info


def select_model_by_r2(
    models_results: Dict[str, Dict[str, Any]], y_actual: pd.Series
) -> Dict[str, Any]:
    """
    Selects the best-performing model based on R-squared score from backcast results.

    Args:
        models_results: A dictionary where keys are model names, and values are dictionaries
            containing:
                - 'backcast': pd.Series or array-like with in-sample predictions
                - 'forecast': future predictions
                - 'coef_': model coefficients (optional)
                - 'expected_value': SHAP expected value (optional)
                - 'shap_values': SHAP feature attributions (optional)
                - 'values': test sample used for SHAP (optional)
        y_actual: Actual target values used for evaluating in-sample (backcast) accuracy.

    Returns:
        A dictionary with:
            - 'best_model': Name of the best model.
            - 'r_squared': R² score of the best model.
            - 'coef_': Extracted model coefficients.
            - 'expected_value': SHAP expected value.
            - 'shap_values': SHAP feature attributions.
            - 'values': Feature vector used for explanation.
            - 'pred_': Full prediction dictionary for the selected model.
    """

    r2_scores = {
        model_name: r2_score(y_true=y_actual, y_pred=results["backcast"])
        for model_name, results in models_results.items()
    }

    # Find the best model
    best_model = max(r2_scores, key=r2_scores.get)

    return {
        "best_model": best_model,
        "r_squared": r2_scores[best_model],
        "coef_": models_results[best_model].pop("coef_"),
        "values": models_results[best_model].pop("values"),
        "expected_value": models_results[best_model].pop("expected_value"),
        "shap_values": models_results[best_model].pop("shap_values"),
        "pred_": models_results[best_model],
    }


def cast_to_base_unit(
    ds: pd.DataFrame,
    spec: pd.DataFrame,
    series_name: str,
    series_values: pd.Series,
    dtype: str,
) -> Tuple[np.ndarray, np.ndarray, pd.Timestamp]:
    """
    Applies a reverse transformation (retransformation) to align predicted or actual values
    to the base measurement unit defined in the transformation specification.

    Args:
        ds: Original dataset with time series data, including the base version of the series.
        spec: DataFrame containing transformation specifications (e.g., scaling, diffing, etc.).
        series_name: Name of the time series to be retransformed.
        series_values: Forecasted or actual values (typically transformed) to be retransformed.
        dtype: Type of values to retransform. Must be one of:
            - 'actual': Use retransform_data()
            - 'pred': Use retransform_()

    Returns:
        A tuple with:
            - R: Retransformed values as a NumPy array.
            - Time: Ordered array of dates (np.ndarray).
            - cutoff_date: First date in the provided `series_values` index.
    """
    Spec = cast_spec_to_dict(spec.loc[spec["seriesid"] == series_name])
    ds = _convert_to_datetime(ds, ["ReferenceDate"])
    dsrc = ds.set_index("ReferenceDate")

    base_series = dsrc[series_name]
    header = [series_name]
    Time = np.sort(
        np.unique(np.concatenate((base_series.index.date, series_values.index.date)))
    )
    cutoff_date = series_values.index.min().date()

    Z = base_series.reindex(Time).to_numpy().reshape(-1, 1)
    Y = series_values.reindex(Time).to_numpy().reshape(-1, 1)

    ## Retransform
    if dtype == "actual":
        R = retransform_data(
            X=Y, Z=Z, Time=Time, Spec=Spec, header=header, cutoff_date=cutoff_date
        )
    elif dtype == "pred":
        R = retransform_(
            X=Y, Z=Z, Time=Time, Spec=Spec, header=header, cutoff_date=cutoff_date
        )
    else:
        raise Exception(f"ValueError: {dtype} not supported")

    return R, Time, cutoff_date


def calculate_contributions(
    coef_: pd.Series, forecast: float, lag: float, values: Union[pd.Series, np.ndarray]
) -> pd.DataFrame:
    """
    Calculates variable-level contributions to a forecast based on model coefficients,
    input values, and a reference (lagged) value.

    Contributions are derived from normalized model impact weights and scaled to match
    the total forecast value. The procedure ensures directional consistency and full
    attribution of the forecasted change.

    Args:
        coef_: Series of model coefficients (indexed by feature name).
        forecast: The predicted value from the model.
        lag: The previous value of the target series (used for delta-based impact).
        values: The feature vector used for prediction (should match `coef_` index).

    Returns:
        DataFrame with variable names as index and the following columns:
            - 'var': Original input values.
            - 'coef_': Model coefficients.
            - 'model_imp_': Raw contribution (value × coefficient).
            - 'weight': Normalized contribution weights.
            - 'contrib': Scaled contribution values (sum equals forecast).
            - 'impact': Change-based impact = (forecast − lag) × weight.
    """
    # Merge feature values and coefficients
    var_imp = pd.merge(
        pd.DataFrame([values], index=["var"]).T,
        pd.DataFrame(coef_).rename(columns={0: "coef_"}),
        left_index=True,
        right_index=True,
    )
    var_imp["model_imp_"] = var_imp["var"] * var_imp["coef_"]

    # https://math.stackexchange.com/questions/452566/how-to-calculate-weight-of-positive-and-negative-values
    s = var_imp["model_imp_"]
    t = s - s.min() + 1
    weights = t / t.sum()

    s_weighted = weights * s
    s_weighted = s_weighted / np.abs(s_weighted.sum())

    assert np.abs(np.round(s_weighted.sum())) == 1

    var_imp["weight"] = s_weighted
    assert (np.sign(var_imp["weight"]) == np.sign(var_imp["model_imp_"])).all()
    assert np.isclose(var_imp["weight"].sum(), 1)

    var_imp["contrib"] = var_imp["weight"] * np.abs(forecast)
    assert (np.sign(var_imp["contrib"]) == np.sign(var_imp["model_imp_"])).all()
    assert np.isclose(np.abs(var_imp["contrib"].sum()), forecast)

    # (Forecast	− Lag) × Weight = Impact
    var_imp["impact"] = (forecast - lag) * var_imp["weight"]
    assert np.isclose(var_imp["impact"].sum(), (forecast - lag))

    return var_imp


def calculate_conf_bounds(pred: pd.Series, actual: pd.Series) -> Dict[str, pd.Series]:
    """
    Calculates rolling confidence bounds around the prediction using expanding window standard deviation.

    Two sets of bounds are computed:
    - 1 standard deviation (approx. 68% confidence interval)
    - 3 standard deviations (approx. 99.7% confidence interval)

    The standard deviation is estimated from the shifted residuals (actual - predicted),
    allowing it to adapt over time.

    Args:
        pred: Series of model predictions.
        actual: Series of actual observed values.

    Returns:
        A dictionary with the following keys:
            - 'L1': Lower bound at 1×std
            - 'U1': Upper bound at 1×std
            - 'L2': Lower bound at 3×std
            - 'U2': Upper bound at 3×std
    """
    std = (actual - pred).shift(1).expanding(2).std().fillna(0)
    low1, upp1 = pred - std, pred + std
    low2, upp2 = pred - 3 * std, pred + 3 * std
    return {"L1": low1, "U1": upp1, "L2": low2, "U2": upp2}
