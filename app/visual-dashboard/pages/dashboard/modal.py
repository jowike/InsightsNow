# Video:    [Bootstrap Alerts & Modals - Dash Plotly](https://youtu.be/X3OuhqS8ueM)
# Docs:     [Dash Bootstrap Components:](https://dash-bootstrap-components.opensource.faculty.ai/docs/components/alert/)
#           [Dash Bootstrap Themes:](https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/)
#           [Dash HTML/CORE Components:](https://dash.plotly.com/dash-html-components)
import dash
from dash import Dash, dcc, html, Input, Output, State           # pip install dash
from dash_spa.components.dropdown_aio import DropdownAIO
import dash_bootstrap_components as dbc         # pip install dash_bootstrap_components
import plotly.express as px
import pandas as pd
# from app import app


def modalAction():

    button = DropdownAIO.Button([
        html.Span(html.Span(className='fas fa-ellipsis-h icon-dark'), className='icon icon-sm'),
        html.Span("Toggle Dropdown", className='visually-hidden')
    ], className='btn btn-link text-dark dropdown-toggle-split m-0 p-0')

    # Action column dropdown bottom-left. Ripped from the Volt transactions table using Firefox debug tools

    style={
        "position": "absolute",
        "inset": "0px 0px auto auto",
        "margin": "0px",
        "transform": "translate3d(0px, 25.3333px, 0px)"
        }

    container = html.Div([
        html.A([html.Span(className='fas fa-edit me-2'), "Edit"], className='dropdown-item', id="enable-edit", n_clicks=0),
        html.A([html.Span(className='fas fa-trash-alt me-2'), "Discard" ], className='dropdown-item text-danger rounded-bottom', id="discard-changes", n_clicks=0)
    ], className='dropdown-menu py-0', style=style)

    return html.Div(DropdownAIO(button, container, id='edit-parameter-button'), className='btn-group')



def modal(
        parameters='Textarea content initialized\nwith multiple lines of text',
        data_catalog='Another textarea content initialized\nwith multiple lines of text'
        # parameters=app.parameters, data_catalog=app.data_catalog
        ):
    return html.Div(
    [
        # dbc.Button("Add comment", id="open"),

        dbc.Modal([
            dbc.ModalHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.ModalTitle("Configuration Sources"), 
                            width="auto"  # Ensures the title takes up only the necessary space
                        ),
                        dbc.Col(
                            modalAction(), 
                            width="auto",  # Ensures the action takes up only the necessary space
                            className="text-end pe-4"  # Aligns content to the right
                        ),
                    ],
                    justify="between",  # Spreads the columns to opposite sides
                    align="center",     # Vertically aligns content in the row
                    className="w-100"
                )
            ),
            dbc.ModalBody(
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                # dbc.Label("Name property", className="mt-1"),
                                # dbc.Input(type="text", placeholder="Specify the name of the parameter"),
                                dbc.Label("Parameters", className="mt-1"),
                                    dcc.Textarea(
                                        id='textarea-parameters',
                                        value=parameters,
                                        className="mt-1",
                                        style={
                                            "height": "35px",
                                            "width": "calc(100% - 24px)",  # Adjust width for 12px margins
                                            "marginLeft": "12px",         # Symmetric margin-left
                                            "marginRight": "12px",        # Symmetric margin-right
                                            "boxSizing": "border-box"     # Ensures padding doesn't affect width
                                        },
                                        disabled=True,
                                    ),
                            ],
                            className="mb-2",
                        ),
                        # dbc.Row(
                        #     [
                        #         dbc.Label("Lorem ipsum", className="mt-1"),
                        #         dbc.Input(type="email", placeholder="Enter ..."),
                        #     ],
                        #     className="mb-2",
                        # ),
                        dbc.Row(
                            [
                                # dbc.Label("Value", className="mt-1"),
                                # dbc.Input(type="text", placeholder="Enter parameter value"),
                                dbc.Label("Data Catalog", className="mt-1"),
                                dcc.Textarea(
                                    id='textarea-catalog',
                                    value=data_catalog,
                                    style={
                                        "height": "35px",
                                        "width": "calc(100% - 24px)",  # Adjust width for 12px margins
                                        "marginLeft": "12px",         # Symmetric margin-left
                                        "marginRight": "12px",        # Symmetric margin-right
                                        "boxSizing": "border-box"     # Ensures padding doesn't affect width
                                    },
                                    disabled=True,
                                ),
                            ],
                            className="mb-2",
                        ),
                        html.Div(id='output-edit-advanced-config'),
                        dbc.Button("Save", id="save-button", color="primary", n_clicks=0),
                    ],
                )
            ),
            dbc.ModalFooter(
                dbc.Button("Close", id="advanced-config-modal-close", className="ml-auto")
            ),

        ],
            id="advanced-config-modal",
            is_open=False,    # True, False
            size="xl",        # "sm", "lg", "xl"
            backdrop=True,    # True, False or Static for modal to not be closed by clicking on backdrop
            scrollable=True,  # False or True if modal has a lot of text
            centered=True,    # True, False
            fade=True         # True, False
        ),
    ]
)






