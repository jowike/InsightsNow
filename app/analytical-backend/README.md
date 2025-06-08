# ✨ maynard

[![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)](https://kedro.org)

## 🔮 What is this?

This is the engine behind the **InsightsNow** dashboard.
It takes raw macroeconomic data and turns it into clear, actionable nowcasts.

The pipeline is built with **Kedro** and will soon be available as a Python package on PyPI under the name `maynard`.

---

## 🧭 How it works — step by step

This pipeline is built for information efficiency. It is designed to be realistic, transparent, and focused . Here’s what it does:

### 1. 📅 Revision Tracking

It rebuilds the data as it looked *at the time* — no future info sneaks in.
This avoids look-ahead bias, sidestepping the inherent risk of information leak.

### 2. ⏳ Handling Missing & Mixed-Frequency Data

Deals with different data frequencies and missing points — common problems in economic time series.
It fills gaps smartly and keeps the timeline consistent.

### 3. 🔄 Data Transformation

Applies the right math — log changes, growth rates, differences — to highlight trends and smooth out noise.
Sparse series are removed, and missing values are filled using splines.

### 4. 📉 Checking for Stationarity

Uses the Augmented Dickey-Fuller (ADF) test to check for unstable patterns in the data.
Automatically flags or transforms series that could mislead the model.

### 5. 🧮 Filtering Low-Variance Features

Removes features with almost no variation, so the model focuses on the signals, not the noise.

### 6. 🧠 Feature Selection

Keeps only the most useful variables using a method based on mutual information (MRMR).
This makes the model simpler, faster, and easier to understand.

### 7. 🤖 Model Estimation

Combines battle-tested time-series models (VAR, ARIMA) and modern machine learning algorithms (random forests, gradient boosting, regularized regressions)

The pipeline picks the best-performing model based on out-of-sample R² — its forecast becomes the Master Prediction.

### 8. 🧾 Explainable AI along the way (global and local)

Every forecast comes with explanations.
Users know which features are important and what are the underlying reasons for each forecast — no black boxes.

### 9. 🛡️ Post-inference validation

Detects sudden shifts (using the Bai-Perron test) and applies fallback logic when needed.
Keeps the forecasts reliable – even during unexpected changes (regime shifts, policy interventions or crises).

### 10. 📊 Benchmark Models

Also runs ARIMA and VAR models as baselines, so you can compare them directly with ML-based forecasts.

### 11. 📁 Output: Dashboard-Ready Report

Puts all results into a clear Excel file — ready to be used in the dashboard.
Includes forecasts, confidence bands, model metrics, and variable impacts.

---

## 🛠 Configuration

You can control how the pipeline runs using these two files:

* `parameters.yaml`: sets options like forecast target, backtest window, and date.
* `catalog.yaml`: tells Kedro where to find data and save results.

Both files can be edited right from the dashboard — no coding needed.

---

## 📂 Inputs and Outputs

🗂 **Example input files** can be found at: [app/analytical-backend/data](https://github.com/jowike/InsightsNow/tree/journal-submission/app/analytical-backend/data).
Use these as a reference to prepare your own data.

---

## 🧙🏻‍♂️ Tested during COVID-19 pandemic

By using machine learning algorithms and high-frequency data, `maynard` reacts fast to economic shocks. Our models started showing signs of weakening US growth in April 2020.

---

## 🧪 Requirements

Main dependencies:

* `kedro`, `kedro-datasets`
* `pmdarima`, `linear-tree`
* `shap`, `rpy2`, `bottleneck`
* `openpyxl`, `xlsxwriter`

See `requirements.txt` for the full list.

---

## 🐛 Need help?

If something doesn’t work or you find a bug, please raise an issue with a short example.
Or reach out at: [https://github.com/jowike/InsightsNow/issues](https://github.com/jowike/InsightsNow/issues).

---