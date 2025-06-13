import dash
from dash import Dash, dcc, html, Input, Output, State
from dash_spa.components.dropdown_aio import DropdownAIO
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd


def uploadModal():
    return html.Div(
    [
        dbc.Modal([
            dbc.ModalHeader(
            ),
            dbc.ModalBody(
                html.Div([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            html.I(className='fa fa-upload', style={'margin-right': '10px'}),  # Icon
                            html.A('Click here', style={'color': '#5046E4', 'font-weight': 'bold'}),
                            ' to upload your file or drag and drop',
                        ]),
                        style={
                            "width": "calc(100% - 24px)",  # Adjust width for 12px margins
                            'height': '120px',
                            'lineHeight': '60px',
                            'borderWidth': '2px',
                            'borderStyle': 'dotted',
                            'borderRadius': '10px',
                            'textAlign': 'center',
                            'backgroundColor': '#f8f9fa',
                            "marginLeft": "12px",         # Symmetric margin-left
                            "marginRight": "12px",        # Symmetric margin-right
                            "boxSizing": "border-box",    # Ensures padding doesn't affect width
                            'padding': '30px',
                            'cursor': 'pointer',
                            'fontSize': '16px',
                        },
                        className='upload-container',
                        # Allow multiple files to be uploaded
                        multiple=True
                    ),
                    html.Div(id='output-data-upload'),
                ])
            ),
            dbc.ModalFooter(
                dbc.Button("Close", id="upload-files-modal-close", className="ml-auto")
            ),
        ],
            id="upload-files-modal",
            is_open=False,    # True, False
            size="xl",        # "sm", "lg", "xl"
            backdrop=True,    # True, False or Static for modal to not be closed by clicking on backdrop
            scrollable=True,  # False or True if modal has a lot of text
            centered=True,    # True, False
            fade=True         # True, False
        ),
    ]
)
