from typing import List
from dash import html, dcc
from dash_spa import prefix, url_for, NOUPDATE
from dash_chartist import DashChartist
from dash_spa.components import SPA_LOCATION, TableContext
from dash_spa import trigger_index
from dash_spa.components.dropdown_button_aoi import DropdownButtonAIO, dropdownLink
from dash_spa.components.dropdown_aio import DropdownAIO
from dash_spa.components.button_container_aoi import ButtonContainerAIO
import dash_bootstrap_components as dbc

from ..icons.hero import ICON
from config import load_contributions, load_predictions, load_series, format_diff
# from callbacks.dashboard_callbacks import format_diff

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
children=[]
data = {}
# _, dropdown_options = load_contributions()
# _, header = load_predictions()

# try:
#     selected_option = dropdown_options[0]
#     target_variable = header["Series Code"]

#     data = load_series(series_id=selected_option, diff=False)

#     value = float(data["series"][1][-1])
#     lag = float(data["series"][1][-2])
#     pct_diff = (value - lag) / lag

#     diff_class, diff_icon = format_diff(pct_diff)

#     # Format children for VAR and ARIMA change
#     children = [
#         "Since Last Month",
#         diff_icon,
#         html.Span('{:.1%}'.format(pct_diff).replace(".0%", "%"), className=diff_class)
#     ]
#     value = '{:,.1f}'.format(value).rstrip('.0')

#     data = load_series(selected_option)
# except Exception:
#     data = {}

def totalOrdersBarChart():
    dropdown = html.Div(
                [
                    dbc.DropdownMenu(
                        label=html.I(className="fas fa-cog"),  # Remove default label
                        toggleClassName="btn btn-white dropdown-toggle d-flex align-items-center",
                        toggle_style={"border": "1px solid #ced4da", "borderRadius": "4px"},
                        children=[
                            # dbc.DropdownMenuItem(option, id=f"option-{option}")
                            # for option in dropdown_options
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
                    html.H2([value], className="h3 fw-extrabold", id="global-explanation-value"),
                    html.Div(children, id="global-explanation-change", className="small mt-2"),
                ],
                className="d-block",
            ),
            html.Div(
                [
                    html.Div(
                        dropdown,
                        className='d-flex justify-content-end align-items-center mb-4'
                    ),
                    html.Div(
                        [
                            html.Span(className="dot rounded-circle bg-gray-800 me-2"),
                            html.Span(target_variable, className="fw-normal small", id="global-explanation-legend-gray"),
                        ],
                        className="d-flex align-items-center text-end mb-2",
                    ),
                    html.Div(
                        [
                            html.Span(className="dot rounded-circle bg-secondary me-2"),
                            html.Span(selected_option, className="fw-normal small", id="global-explanation-selected-option"),
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
                        className="card-body p-2", id='global-explanation-table'
                    ),
                ],
                className="card border-0 shadow",
            )
        ],
        className="col-12 px-0 mb-4",
    )
