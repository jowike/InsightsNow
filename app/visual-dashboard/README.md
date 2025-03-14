# InsightsNow

Long gone are the days of stability, when simple methods provided reliable insights. Today, navigating the economy requires real-time intelligence and advanced analytics.
This Nowcasting Tool transforms economic forecasting.
By integrating real-time data vintages with cutting-edge predictive models, it provides a comprehensive outlook on market conditions, bolstering informed decision making with timely, accurate nowcasts — available in minutes, not weeks.

**🚀 Key assets**

* **Data** – FRED-sourced data from around the world provide a truly global perspective.
* **Models** — Instant prediction updates driven by economic news, based on cutting-edge econometrics and machine learning.
* **Explanations** — Aligned with responsible AI principles, the tool eliminates the ‘black box’ effect — not only tells you what’s gonna happen, but also provides insights into the why behind the predictions.

#### 🗺️ Dashboard walkthrough 

**🔮 Nowcast Browser**

The Nowcast Browser displays forecasts for the upcoming reporting period alongside backcasting results, comparing actual and predicted values. It provides a clear visualization of real-time estimates against historical data, supporting data-driven decision-making.

**🔖 Tiles**

* **Prediction Uncertainty** – Represents the confidence interval, estimated using empirical backcasting errors. It indicates the range within which actual values are expected to fall.
* **ARIMA & VAR Models** – These state-of-the-art time series models serve as benchmark (baseline) methods for evaluating forecast accuracy.
    * VAR (Vector Autoregression) – A multivariate model capturing interdependencies among multiple time series.
    * ARIMA (AutoRegressive Integrated Moving Average) – A widely used model for univariate time series forecasting, incorporating past values and trends.

**📊 Local Explanation**

The Local Explanation table details the impact of each variable on the model’s predictions. Contribution values indicate how much each feature influences the final forecast. The table also provides real-time data flow by displaying the release dates for the latest reporting periods of the variables that drive predictions.

**🌏 Global Explanation**

The Global Explanation provides a broader view of how predicted indicators co-move with explanatory variables contributing to the forecast. The chart visualizes period-over-period percentage changes in the target variable alongside its key predictors (explanatory variables).
Users can navigate through the contributing indicators and select specific variables of interest to analyze their influence on the forecast.

**⏰ Real-Time Monitoring Insights**

This panel provides users with a clear view of data recency, displaying the latest updates for both source data and estimation results. It also allows users to monitor the status of the nowcasting pipeline in real time.
Additionally, the panel includes information on Kedro-Viz status:
* If running, the Kedro-Viz address is displayed.
* If not running or stopped after execution, an appropriate message is shown.
This ensures transparency in data processing and enables users to track the progress of ongoing estimations.

**🧮 Model Assessment**

Gives an overview of key evaluation metrics for predictive analytics, helping assess the accuracy and reliability of nowcasts.

#### 🕹 How to Use? ️ 
The top navigation pane streamlines the workflow, ensuring smooth data management and seamless execution of nowcasting models.

**⚙️ Settings** dropdown menu provides key functionalities for managing data and pipeline configurations:

* **📥 Upload Files**
    * Import source economic data for nowcasting.
    * Upload an Excel file defining a custom model specification.
* **🛠️ Advanced configuration**
    * Edit Kedro pipeline run configuration and/or data catalog files (e.g., parameters.yaml, catalog.yaml).

**️🪄 Kedro Run** standalone button triggers the nowcasting estimation process by executing the Kedro pipeline (kedro run).

**✨ Kedro Viz ** button launches Kedro Viz, which visualizes the pipeline structure, displaying data, nodes, and their connections within the Kedro project.
