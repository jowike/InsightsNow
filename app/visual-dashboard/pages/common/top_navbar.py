from dash import html, dcc
import dash_bootstrap_components as dbc

from ..icons.hero import ICON

def searchForm():
    return  html.Form([
        html.Div([
            html.Span([
                ICON.SEARCH
            ], className='input-group-text', id='topbar-addon'),
            dcc.Input(type='text', className='form-control', id='topbarInputIconLeft', placeholder='Search')
        ], className='input-group input-group-merge search-bar')
    ], className='navbar-search form-inline', id='navbar-search-main')

def infoControl():
    return html.Div(
        [
            # Info Icon
            html.Span(
                [
                    html.Span(
                        "Let the Journey Begin: Step-by-Step Guide 🧶",
                        style={
                            "fontWeight": "500",
                            "fontSize": "14px",
                            "color": "#472C4C"  # "6A5294"  # "#6F5D00", #8E4E1B, #6A5294
                        }
                    )
                ],
                className="input-group-text bg-light border px-1 shadow-sm px-3",  # 
                id="info-icon",
                style={
                    "height": "42px",
                    "cursor": "pointer",
                    # "backgroundColor": "#E8E9EB"
                    }
            ),


            # Modal for Guidelines
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Landing Page")),
                    dbc.ModalBody(
                        [
                            html.P("Long gone are the days of stability, when simple methods provided reliable insights. Today, navigating the economy requires real-time intelligence and advanced analytics."),
                            html.P(["This Nowcasting Tool ", html.Strong("transforms economic forecasting"), "."]),
                            html.P([
                                "By integrating real-time data vintages with cutting-edge predictive models, it provides a ", 
                                html.Strong("comprehensive outlook on market conditions"), 
                                ", bolstering informed decision making with timely, accurate nowcasts — available in  ",
                                html.Strong("minutes, not weeks"), "."
                            ]),
                        html.H6("🚀 Key assets", className="mt-4 fw-bold"),
                        html.Ul([
                            html.Li([
                                html.B("Data"), 
                                " – FRED-sourced data from around the world provide a truly global perspective."
                            ]),
                            html.Li([
                                html.B("Models"), 
                                " — Instant prediction updates driven by economic news, based on ",
                                html.Strong("cutting-edge econometrics and machine learning"), 
                                "."
                            ]),
                            html.Li([
                                html.B("Explanations"), 
                                " — Aligned with ", 
                                html.Strong("responsible AI principles"), 
                                ", the tool eliminates the ‘black box’ effect — not only tells you ",
                                html.Strong("what’s gonna happen"), 
                                ", but also provides insights into the ", 
                                html.Strong("why"), 
                                " behind the predictions."
                            ])
                        ]),
                        html.H5("Dashboard walkthrough"),
                        html.H6("🔮 Nowcast Browser", className="fw-bold"),
                        html.P([
                            html.Strong("The Nowcast Browser"), 
                            " displays forecasts for the upcoming reporting period alongside backcasting results, comparing actual and predicted values. "
                            "It provides a clear visualization of real-time estimates against historical data, supporting data-driven decision-making."
                        ]),

                        html.H6("🔖 Tiles", className="fw-bold"),
                        html.Ul([
                            html.Li([
                                html.Strong("Prediction Uncertainty"), 
                                " – Represents the confidence interval, estimated using empirical backcasting errors. "
                                "It indicates the range within which actual values are expected to fall."
                            ]),
                            html.Li([
                                html.Strong("ARIMA & VAR Models"), 
                                " – These state-of-the-art time series models serve as benchmark (baseline) methods for evaluating forecast accuracy.",
                                html.Ul([
                                    html.Li([
                                        html.Strong("VAR (Vector Autoregression)"), 
                                        " – A multivariate model capturing interdependencies among multiple time series."
                                    ]),
                                    html.Li([
                                        html.Strong("ARIMA (AutoRegressive Integrated Moving Average)"), 
                                        " – A widely used model for univariate time series forecasting, incorporating past values and trends."
                                    ])
                                ])
                            ])
                        ]),

                        html.H6("📊 Local Explanation", className="fw-bold"),
                        html.P([
                            html.Strong("The Local Explanation"), 
                            " table details the impact of each variable on the model’s predictions. "
                            "Contribution values indicate how much each feature influences the final forecast. "
                            "The table also provides real-time data flow by displaying the ", 
                            html.Strong("release dates"), 
                            " for the latest reporting periods of the variables that drive predictions."
                        ]),

                        html.H6("🌏 Global Explanation", className="fw-bold"),  # 〽️
                        html.P([
                            html.Strong("The Global Explanation"), 
                            " provides a broader view of how predicted indicators co-move with explanatory variables contributing to the forecast. ",
                            "The ", html.Strong("chart visualizes period-over-period percentage changes"), 
                            " in the target variable alongside its key predictors (explanatory variables)."
                        ]),
                        html.P("Users can navigate through the contributing indicators and select specific variables of interest to analyze their influence on the forecast."),

                        html.H6("⏰ Real-Time Monitoring Insights", className="fw-bold"),
                        html.P([
                            "This panel provides users with a clear view of ", 
                            html.Strong("data recency"), 
                            ", displaying the latest updates for both ",
                            html.Strong("source data"), 
                            " and ",
                            html.Strong("estimation results"), 
                            ". It also allows users to monitor the ",
                            html.Strong("status of the nowcasting pipeline"), 
                            " in real time."
                        ]),
                        html.P(["Additionally, the panel includes information on ", html.Strong("Kedro-Viz status"), ":"]),
                        html.Ul([
                            html.Li([
                                "If ", html.Strong("running"), ", the ", html.Strong("Kedro-Viz address"), " is displayed."
                            ]),
                            html.Li([
                                "If ", html.Strong("not running"), " or ", html.Strong("stopped after execution"), ", an appropriate message is shown."
                            ])
                        ]),
                        html.P("This ensures transparency in data processing and enables users to track the progress of ongoing estimations."),

                        html.H6("🧮 Model Assessment", className="fw-bold"),
                        html.P("Gives an overview of key evaluation metrics for predictive analytics, helping assess the accuracy and reliability of nowcasts."),

                        html.H5("How to Use?", className="fw-bold"),
                        html.P("The top navigation pane streamlines the workflow, ensuring smooth data management and seamless execution of nowcasting models."),

                        html.P([
                            "⚙️ ", html.Strong("Settings"), 
                            " dropdown menu provides key functionalities for managing data and pipeline configurations:"
                        ]),

                        html.Ul([
                            html.Li([
                                html.Strong("Upload Files"),
                                html.Ul([
                                    html.Li(["Import ", html.Strong("source economic data"), " for nowcasting."]),
                                    html.Li(["Upload an ", html.Strong("Excel file"), " defining a ", html.Strong("custom model specification"), "."])
                                ])
                            ]),
                            html.Li([
                                html.Strong("Advanced configuration"),
                                html.Ul([
                                    html.Li([
                                        "Edit ", html.Strong("Kedro pipeline run configuration"), " and/or ", html.Strong("data catalog files"), 
                                        " (e.g., ", html.Span("parameters.yaml", style={"color": "green"}), ", ", 
                                        html.Span("catalog.yaml", style={"color": "green"}), ")."
                                    ])
                                ])
                            ])
                        ]),

                        html.P([
                            html.Span(ICON.DIAMOND, className='me-1'), html.Strong("Kedro Run"), " standalone button triggers the nowcasting estimation process by executing the ", 
                            html.Strong("Kedro pipeline"), " (", html.Span("kedro run", style={"color": "green"}), ")."
                        ]),

                        html.P([
                            html.Span("✨", className='me-1'), html.Strong("Kedro Viz"), " button launches ", html.Strong("Kedro Viz"), ", which visualizes the pipeline structure, displaying ",
                            html.Strong("data, nodes, and their connections"), " within the Kedro project."
                        ])


                            # TODO: Impacts of data releases (Data Flow)
                        ]
                    ),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)
                    ),
                ],
                id="guidelines-modal",
                is_open=False,    # True, False
                size="xl",        # "sm", "lg", "xl"
                backdrop=True,    # True, False or Static for modal to not be closed by clicking on backdrop
                scrollable=True,  # False or True if modal has a lot of text
                centered=True,    # True, False
                fade=True         # True, False
            ),
        ],
        className="d-flex align-items-center",  # Align icon and modal trigger
    )

def topNavBar():
    """"Top navbar, search form ..."""
    return html.Nav([
        html.Div([
            html.Div([
                html.Div([
                    # infoControl(),
                ], className='d-flex align-items-center')
            ], className='d-flex justify-content-between w-100', id='navbarSupportedContent')
        ], className='container-fluid px-0')
    ], className='navbar navbar-top navbar-expand navbar-dashboard navbar-dark ps-0 pe-2 pb-0')
