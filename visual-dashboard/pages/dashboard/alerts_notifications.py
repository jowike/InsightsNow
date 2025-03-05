from dash import html, dcc
import dash_bootstrap_components as dbc         # pip install dash_bootstrap_components
from ..icons.hero import ICON
import dash_loading_spinners as dls


def alertsNotifications():
    return  html.Div([
        html.Div([
            html.H2("Real-Time Monitoring Insights", className="h5 mb-4"), 
            html.Ul([
                html.Li([
                    html.Div([
                        html.H3("Data Flow", className="h6 mb-1"),
                        html.P("Get the data recency watermarks from the data repository.", className="small pe-4"),
                        html.P("Data as of Date: ", className="small pe-4", id="data-as-of-date"),
                    ]),
                ], className="list-group-item d-flex align-items-center justify-content-between px-0 border-bottom"),
                html.Li([
                    html.Div([
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.H3("Nowcast", className="h6 mb-1"),
                                    width="auto",  # Ensures the title takes up only the necessary space
                                    className="d-flex align-items-center"  # Vertically aligns the title
                                ),
                                # dbc.Col(
                                #     tableAction(), 
                                #     width="auto",  # Ensures the action takes up only the necessary space
                                #     className="d-flex justify-content-end align-items-center ms-auto"  # Pushes to the far right
                                # ),
                            ],
                            className="g-0 w-100"  # Removes gutters and ensures full-width row
                        ),
                        html.P("Monitor the real-time status of the model refinery.", className="small pe-4"),
                        dls.Hash(
                            html.P(
                                html.Div([
                                    html.Span(ICON.DIAMOND), html.Span("Nowcasting pipeline state: "), html.Span(html.Span("Idle", style={"color": "#585858"}))
                                ]), id="pipeline-status", className="pipeline-status small pe-4"),
                            color="#435278",
                            speed_multiplier=2,
                            size=100,
                            fullscreen=True
                        ),
                        html.P("⌛️ Last Run Watermark: ", className="small pe-4", id="nowcast-as-of-date"),
                        html.P(
                            html.Div([
                                html.Span("✨ Kedro-Viz state: "), html.Span(html.Span("Idle", style={"color": "#585858"}))
                            ]), id="pipeline-viz", className="pipeline-status small pe-4"),
                    ]),
                    # html.Div([
                    #     html.Div(id="pipeline-status", className="pipeline-status", style={"margin-top": "20px"})
                    # ])
                ], className="list-group-item d-flex align-items-center justify-content-between px-0 border-bottom"),
            ], className="list-group list-group-flush")
        ], className="card card-body border-0 shadow mb-4 mb-xl-0")
    ], className='col-12 mb-4 mb-xl-0')
