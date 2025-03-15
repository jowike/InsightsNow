from dash import html, dcc
from dash_chartist import DashChartist

import os
import pandas as pd
from config import load_predictions

from ..icons.hero import ICON


options = {
    # 'low': 0,
    "showArea": False,
    "fullWidth": False,
    "axisX": {
        # On the x-axis start means top and end means bottom
        "position": "end",
    },
    "axisY": {
        # On the y-axis start means left and end means right
        "showGrid": False,
        "scaleMinSpace": 30,  # Minimum space between ticks (in pixels)
    },
}

chartType = "Line"


def _chartHeader():
    return html.Div(
        [
            html.Div(
                [
                    html.Div("Nowcast Browser", className="fs-5 fw-normal mb-0"),
                    html.Small("", className="text-gray-500", id="nowcast-series-name"),
                    html.Small(
                        [],
                        className="d-flex align-items-center text-gray-500 mb-2",
                        id="nowcast-annotation",
                    ),
                    html.H2(
                        "Not Available",
                        className="fs-3 fw-extrabold",
                        id="nowcast-pred-value",
                    ),
                    html.Div([], className="small mt-2", id="nowcast-pred-change"),
                ],
                className="d-block mb-3 mb-sm-0",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(className="circle-black"),
                            html.Span(
                                "Actual",
                                className="fw-normal small",
                                id="global-explanation-legend-gray",
                            ),
                        ],
                        className="d-flex align-items-center text-end mb-2",
                    ),
                    html.Div(
                        [
                            html.Span(className="circle-purple"),
                            html.Span(
                                "Estimate",
                                className="fw-normal small",
                                id="global-explanation-selected-option",
                            ),
                        ],
                        className="d-flex align-items-center text-end",
                    ),
                ],
                className="d-block ms-auto",
            ),
        ],
        className="card-header d-sm-flex flex-row align-items-center flex-0",
    )


def nowcastChart():
    return html.Div(
        [
            html.Div(
                [
                    _chartHeader(),
                    html.Div(
                        [
                            DashChartist(
                                className="ct-chart-sales-value ct-double-octave",
                                type=chartType,
                                options=options,
                                tooltips=True,
                                data={},  # This will be populated dynamically via callback
                                id="nowcast-chart",
                            )
                        ],
                        className="card-body p-2",
                    ),
                ],
                className="card border-0",
            )
        ],
        className="col-12 mb-4",
    )
