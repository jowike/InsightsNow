from dash import html, dcc
from dash_chartist import DashChartist

import os
import pandas as pd
from config import load_predictions

from ..icons.hero import ICON

# data = {
#     "labels": ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
#     "series": [ 
#         [0, 10, 30, 40, 80, 60, 100],
#         [1, 11, 29, 41, 79, 65, ]
#           ]
# }

# data = load_predictions(type="base")

options = {
    # 'low': 0,
    'showArea': False,
    'fullWidth': False,
    'axisX': {
        # On the x-axis start means top and end means bottom
        'position': 'end',
        # 'showGrid': True,
        },
    'axisY': {
        # On the y-axis start means left and end means right
        'showGrid': False,
        # 'showLabel': False,
        'scaleMinSpace': 30           # Minimum space between ticks (in pixels)
        }
    }

chartType = 'Line'

def _chartHeader():
    return  html.Div([
                html.Div([
                html.Div("Nowcast Browser", className='fs-5 fw-normal mb-0'),
                    html.Small("", className='text-gray-500', id="nowcast-series-name"),
                    html.Small([
                        # "Aug 1 - Aug 31,",
                        # ICON.GLOBE.ME1,
                        # "USA"
                    ], className='d-flex align-items-center text-gray-500 mb-2', id='nowcast-annotation'),
                html.H2("Not Available", className='fs-3 fw-extrabold', id='nowcast-pred-value'),
                html.Div([
                #     html.Span("Since last month", className='fw-normal me-2'),
                #     html.Span(className='fas fa-angle-up text-success me-1'),
                #     html.Span("2.57%", className='text-success fw-bold')
                ], className='small mt-2', id='nowcast-pred-change')
            ], className='d-block mb-3 mb-sm-0'),

            html.Div(
                [
                    html.Div(
                        [
                            html.Span(className="circle-black"),
                            html.Span("Actual", className="fw-normal small", id="global-explanation-legend-gray"),
                        ],
                        className="d-flex align-items-center text-end mb-2",
                    ),
                    html.Div(
                        [
                            html.Span(className="circle-purple"),
                            html.Span("Estimate", className="fw-normal small", id="global-explanation-selected-option"),
                        ],
                        className="d-flex align-items-center text-end",
                    ),
                ],
                className="d-block ms-auto",
            ),

            
            # html.Div([
            #     dcc.Link("Base", href='#', className='btn btn-secondary text-dark btn-sm me-2'),
            #     dcc.Link("Adjusted", href='#', className='btn btn-sm me-3')
            # ], className='d-flex ms-auto')
        ], className='card-header d-sm-flex flex-row align-items-center flex-0')


def salesChart():
    return  html.Div([
        html.Div([
            _chartHeader(),
            html.Div([
                DashChartist(
                    className='ct-chart-sales-value ct-double-octave',
                    type=chartType,
                    options=options,
                    tooltips=True,
                    data={},  # This will be populated dynamically via callback
                    id='nowcast-chart',
                    )
            ], className='card-body p-2')
        ], className='card border-0')
    ], className='col-12 mb-4')
