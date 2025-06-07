# 🌕 A modern, real-time forecasting tool for the XXI century economy

Want to know what will happen to the economy next week / month / quarter?

**InsightsNow.app** helps you forecast what’s coming — fast and with confidence.

Based on years of experience in machine learning and econometrics, we’ve build **InsightsNow.app** — a modern, high-frequency forecasting tool for the XXI century economy

It includes a powerful backend (`maynard`) and a clear, interactive dashboard — so you can go from raw data to insights in just a few steps.

---

## 📦 What’s inside?

The app consists of two main parts:

#### ✨ maynard: Analytical Engine

A Python-based backend built with **Kedro**, responsible for processing macroeconomic time series, selecting features, training ML and benchmark models, and generating explainable nowcasts.

It supports:

* revision-aware forecasting (real-time vintages),
* mixed-frequency data handling,
* feature selection and explainability,
* structural break detection and fallback logic.

> Named after John Maynard Keynes, an economist who revolutionized macroeconomics in XX century — `maynard` aims to do the same for economic forecasting in the modern era.

📄 [See backend README →](https://github.com/jowike/InsightsNow/blob/journal-submission/app/analytical-backend/README.md)

---

#### 🎨 Visual Dashboard

A simple interface for running models, viewing results, and understanding how everything works — all in one place.

Built for clarity and ease of use, the dashboard lets you:

* run models in real time,
* see what’s driving each forecast,
* understand prediction uncertainty and performance.

It’s designed to make advanced economic forecasting accessible — whether you’re an economist, market analyst, or subject-matter expert.

📄 [See dashboard README →](https://github.com/jowike/InsightsNow/blob/journal-submission/app/visual-dashboard/README.md)

---

## 🚀 Why use InsightsNow?

* **Fast** – From raw data to a forecast in minutes
* **Transparent** – Explainable AI along the way offers full visibility into the pipeline
* **Realistic** – Forecasts based on what was *actually* known at the time
* **Modular** – Use just the backend, or just the dashboard — or both together
* **Battle-tested** – Used on real data, including during the COVID-19 economic shock

---

## 🧱 Architecture Overview

```text
          +---------------------+
          |  InsightsNow        |
          |  Dashboard (UI)     |
          +---------------------+
                    |
                    v
          +---------------------+
          |  maynard            |
          |  (Kedro pipeline)   |
          +---------------------+
                    |
                    v
         +------------------------+
         | Raw macro data (CSV,   |
         | Excel, FRED API, etc.)|
         +------------------------+
```

---

## 🏁 Getting Started

To run the full app locally:

1. **Install backend dependencies**
   
   From the `analytical-backend` folder:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the dashboard**
   
   From the `visual-dashboard` folder:

   ```bash
   pip install -r requirements.txt
   python setup.py install
   ```

5. **Run the dashboard**
   
   From the same folder:

   ```bash
   python app.py
   ```

7. Open your browser and start exploring forecasts!

---

## 🎥 Demo

Want to see it in action?

* [▶️ **Demo Video**](https://www.youtube.com/watch?v=RfoxH-lfU7k) – short walkthrough of the dashboard and how to use it.
* [🎞️ **Visual Walkthrough**](https://www.youtube.com/watch?v=MmwHpOVBBT0) — same visuals, no sound (a fallback useful in case of audio restrictions).

---

## 🔜 Coming soon

* PyPI release for the `maynard` package
* Live demo instance → [https://insightsnow.mini.pw.edu.pl/pages/dashboard](https://insightsnow.mini.pw.edu.pl/pages/dashboard)

---

## 🙌 Credits & References

* 🎨 **Dashboard layout**

  The look and feel of the dashboard was inspired by the awesome [Volt Bootstrap 5 Dashboard](https://demo.themesberg.com/volt/) — an open-source UI built with Bootstrap 5.
  We also borrowed some ideas (and a bit of code) from [dash-flightdeck](https://github.com/stevej2608/dash-flightdeck), a Plotly/Dash version created by Steve Jones.

* 🧠 **Feature selection logic**
  
  Some of the feature selection magic comes from the [mifs](https://github.com/danielhomola/mifs) package by Daniel Homola — a great tool for selecting the most informative variables using mutual information.
  
---

## 🙋 Need help?

* Backend issues → [Open an issue](https://github.com/jowike/InsightsNow/issues)
* Dashboard bugs → [Report here](https://github.com/jowike/InsightsNow/issues)

---

