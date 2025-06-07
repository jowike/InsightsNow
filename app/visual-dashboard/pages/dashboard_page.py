from dash import html, dcc 
from dash_spa import register_page, prefix

from .common import topNavBar, footer, buttonBar
from .dashboard import (
    nowcastChart,
    uncertainty,
    var,
    arima,
    localExplanationTable,
    globalExplanationBarChart,
    watermarksDiv,
    settingsButton,
    runButton,
    vizButton,
    assessmentDiv,
    settingsModal,
    uploadModal,
    infoControl
)
from .icons.hero import ICON

import os
import sys
import pandas as pd
import dash_loading_spinners as dls
from config import parameters, data_catalog


register_page(__name__, path="/pages/dashboard", title="Dash/InsightsNow - Dashboard")


layout = html.Main(
    [
        dcc.Interval(
            id='interval-component',
            interval=1000,  # Check for file updates every second
            n_intervals=0
        ),
        # Store for shared data
        dcc.Store(id='shared-data'),  # Store the shared data here
        topNavBar(),
        buttonBar(infoControl(), [settingsButton(), runButton(), vizButton()]),
        html.P("", id="pipeline-viz", className="pipeline-status small pe-4"),
        dls.Hash(
            html.P("", id="pipeline-status", className="pipeline-status small pe-4"),
            color="#435278",
            speed_multiplier=2,
            size=100,
            fullscreen=True
        ),
        settingsModal(parameters=parameters, data_catalog=data_catalog),
        uploadModal(),
        html.Div([nowcastChart(), uncertainty(), var(), arima()], className="row"),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                localExplanationTable(),
                                watermarksDiv(),
                            ],
                            className="row",
                        )
                    ],
                    className="col-12 col-xl-8",
                ),
                html.Div(
                    [
                        globalExplanationBarChart(),
                        assessmentDiv(),
                        ],
                    className="col-12 col-xl-4",
                ),
            ],
            className="row",
        ),
        footer()
    ],
    className="content container-fluid",  # Ensure it’s fluid, no padding/margin
    style={
        "margin-left": "90px",  # Remove left margin
        # "margin-right": "100px",  # Remove left padding
        "width": "90%",  # Full width layout
    }
)
