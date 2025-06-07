from dash_spa.components.dropdown_button_aoi import DropdownButtonAIO, dropdownLink
from dash_spa.components.dropdown_aio import DropdownAIO

from dash import html
from ..icons.hero import ICON


def settingsButton():
    return DropdownButtonAIO(
        [
            html.Div(
                [dropdownLink("Upload Files", ICON.UPLOAD)],
                id="upload-files-modal-open",
                n_clicks=0,
                className="dropdown-button",
                style={"height": "fit-content"},
            ),
            html.Div(
                [dropdownLink("Advanced configuration", ICON.CUBE_TRANSPARENT)],
                id="advanced-config-modal-open",
                n_clicks=0,
                className="dropdown-button",
                style={"height": "fit-content"},
            ),
        ],
        "Settings",
        buttonColor="gray-800",
        buttonIcon=ICON.SETTINGS,
    )


def runButton():
    return html.Button(
        [
            html.Span(ICON.DIAMOND, className="me-2"),  # Icon with spacing
            html.Span("Kedro Run", className="me-2"),
        ],
        type="button",
        id="run-pipeline-button",
        n_clicks=0,
        className="btn btn-gray-800 d-inline-flex align-items-center me-2",
    )


def vizButton():
    button = DropdownAIO.Button(
        [
            html.Span("✨", className="me-2"),  # Icon with spacing
            # ICON.SPARKLES,
            html.Span("Kedro Viz"),
        ],
        className="btn btn-gray-800 d-inline-flex align-items-center me-2",
    )

    # Action column dropdown bottom-left. Ripped from the Volt transactions table using Firefox debug tools
    style = {
        "position": "absolute",
        "inset": "0px 0px auto auto",
    }

    container = html.Div(
        [
            html.A(
                [html.Span(className="fas fa-project-diagram me-2"), "Run"],
                id="start-viz-button",
                n_clicks=0,
                className="dropdown-item rounded-top",
            ),
            html.A(
                [html.Span(className="fas fa-stop me-2"), "Stop"],
                id="stop-viz-button",
                n_clicks=0,
                className="dropdown-item rounded-bottom",
            ),
        ],
        className="dropdown-menu py-0",
        style=style,
    )

    return html.Div(
        DropdownAIO(button, container, id="manage-kedro-viz-button"),
        className="btn-group",
    )
