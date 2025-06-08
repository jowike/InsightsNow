# 📈 InsightsNow – Nowcasting Dashboard

## 💡 Motivation

Long gone are the days of stability, when simple methods provided reliable insights. Today, navigating the economy requires real-time intelligence and advanced analytics.

This Nowcasting Tool transforms economic forecasting.

By integrating real-time data vintages with cutting-edge predictive models, it provides a comprehensive outlook on market conditions, bolstering informed decision making with timely, accurate nowcasts — available in minutes, not weeks.

---

## 🚀 What’s inside?

* **🌍 Data** – FRED-sourced data from around the world provide a truly global perspective.
* **📈 Models** – Instant prediction updates driven by economic news, based on machine learning + econometrics. 
* **🔍 Explanations** – Aligned with responsible AI principles, the tool eliminates the ‘black box’ effect — not only tells you what’s gonna happen, but also provides insights into the why behind the predictions.

---

## 🕹 How to Use

The top navigation lets you move smoothly through the nowcasting process — from uploading your data to exploring results — with just a few clicks.

### ⚙️ Settings

**📥 Upload your files**:

* Add a CSV file with time series data.
* Optionally upload an Excel file to specify how to set up the model (e.g., which indicators to include, how to transform them).

No config file? No problem.
The tool automatically applies smart defaults based on metadata like units or frequency — including proper transformations (levels, log changes, growth rates) and relevant predictors.

🗂 Example input files can be found at: [app/analytical-backend/data](https://github.com/jowike/InsightsNow/tree/journal-submission/app/analytical-backend/data).

**Advanced setup**:

* `parameters.yaml` — lets you control key settings like forecast horizon, reference date, and target variable.
* `catalog.yaml` — manages where your data and results are stored.

No coding required — you can edit these files directly in the dashboard.

---

### 🪄 Kedro Run

Runs the full nowcasting workflow: data prep → modeling → evaluation → forecasting – all in one step.

### ✨ Kedro Viz

Visual map of the pipeline so you can see how the data flows and the code blueprint behind each step.

---

## 🗺️ Dashboard Walkthrough

### 🔮 Nowcast Browser

The Nowcast Browser displays forecasts for the upcoming reporting period, side-by-side with historical data and backcasts. Helps you immediately assess model accuracy and prediction trends over time.

### 🔖 Tiles Overview

* **Prediction Uncertainty** – Based on empirical backcasting errors; shows the confidence intervals illustrating the likely range within which actual values are expected to fall.
* **ARIMA & VAR** – State-of-the-art time series models; a point of comparison for evaluating the performance of ML-based predictions.

### 📊 Local Explanation

Shows how each variable affects the current forecast — whether it pushes it up or down. Also reveals when each data point was last updated, highlighting the timeliness of contributing "news". 

### 🌏 Global Explanation

Gives a bigger-picture view of how the forecast co-moves together with its key drivers.
You can compare percentage changes over time and explore how each contributing indicator shapes the predicted variable over time.

### ⏰ Real-Time Monitoring

Clearly shows how up to date your data and forecasts are — you always know if you're working with the latest information.

### 🧮 Model Assessment

Includes key stats like R², MAPE, and RMSE so you can judge model quality.

---

## 🎥 Demo

Want to see it in action?

* [▶️ **Demo Video**](https://www.youtube.com/watch?v=RfoxH-lfU7k) – short walkthrough of the dashboard and how to use it.
* [🎞️ **Visual Walkthrough**](https://www.youtube.com/watch?v=MmwHpOVBBT0) — same visuals, no sound (a fallback useful in case of audio restrictions).

---

## 📬 Contact

If any issues arise or bugs are encountered, please file a report with a minimal reproducible example at [https://github.com/jowike/InsightsNow/issues](https://github.com/jowike/InsightsNow/issues).

---