from dash import html
from dash_chartist import DashChartist
import dash_bootstrap_components as dbc

from ..icons.hero import ICON


options = {
    "showArea": True,
    "fullWidth": True,
    "axisX": {
        # On the x-axis start means top and end means bottom
        "position": "end"
    },
    "axisY": {
        # On the y-axis start means left and end means right
        "showGrid": True,
        "showLabel": True,
    },
}

chartType = "Bar"
dropdown_options = []
target_variable = ""
selected_option = ""
value = ""
children = []
data = {}


def globalExplanationBarChart():
    dropdown = html.Div(
        [
            dbc.DropdownMenu(
                label=html.I(className="fas fa-cog"),  # Remove default label
                toggleClassName="btn btn-white dropdown-toggle d-flex align-items-center",
                toggle_style={"border": "1px solid #ced4da", "borderRadius": "4px"},
                children=[
                    dbc.DropdownMenuItem(
                        "Loading...",
                        id={"type": "series-option", "index": "placeholder"},
                        disabled=True,
                    )
                ],
                id="dropdown-menu",
                className="dropdown-menu-end dropdown-menu-xs",  # Menu styling
                menu_variant="light",  # Light menu style
            ),
        ],
        className="dropdown",
    )
    header = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                "Global Explanation",
                                className="h6 fw-normal text-gray me-auto",
                            ),  # Title
                        ],
                        className="d-flex align-items-center justify-content-between mb-2",
                    ),
                    html.H2(
                        [value],
                        className="h3 fw-extrabold",
                        id="global-explanation-value",
                    ),
                    html.Div(
                        children, id="global-explanation-change", className="small mt-2"
                    ),
                ],
                className="d-block",
            ),
            html.Div(
                [
                html.Div(
                    [
                        html.Span([
                            html.I(className="fas fa-info-circle me-1", style={"color": "black"}),
                            "Uncover the ",
                            html.Strong("why"),
                            " →"
                        ], className="fw-normal small me-2"),
                        dropdown,
                    ],
                    className="d-flex align-items-center justify-content-end mb-4",
                ),
                    html.Div(
                        [
                            html.Span(className="dot rounded-circle bg-gray-800 me-2"),
                            html.Span(
                                target_variable,
                                className="fw-normal small",
                                id="global-explanation-legend-gray",
                            ),
                        ],
                        className="d-flex align-items-center text-end mb-2",
                    ),
                    html.Div(
                        [
                            html.Span(className="dot rounded-circle bg-secondary me-2"),
                            html.Span(
                                selected_option,
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
        className="card-header d-flex flex-row align-items-center flex-0 border-bottom",
    )

    return html.Div(
        [
            html.Div(
                [
                    header,
                    html.Div(
                        [
                            DashChartist(
                                className="ct-chart-ranking ct-golden-section ct-series-a",
                                type=chartType,
                                options=options,
                                data=data,
                                id="global-explanation-chart",
                            )
                        ],
                        className="card-body p-2",
                        id="global-explanation-table",
                    ),
                ],
                className="card border-0 shadow",
            )
        ],
        className="col-12 px-0 mb-4",
    )
