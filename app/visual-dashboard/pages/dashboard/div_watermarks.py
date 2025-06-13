from dash import html, dcc
import dash_bootstrap_components as dbc
from ..icons.hero import ICON
import dash_loading_spinners as dls


def watermarksDiv():
    return  html.Div([
                html.Div([
                    html.P("Data as of Date: ", className="small pe-4 mt-3", id="data-as-of-date"),
                    html.P(
                        html.Div([
                            html.Span(ICON.DIAMOND), html.Span("Last Run Watermark: ", className="small pe-4", id="nowcast-as-of-date")
                        ]), className="mb-3 mt-1"
                        ),
                ], className="card card-body border-0 shadow mb-0 mb-xl-0")
            ], className='col-12 mt-0 mb-xl-0')
