from dash import html, dcc

from ..icons.hero import ICON

def cardFrame(content):
    return html.Div([
        html.Div([
            html.Div([
                html.Div(content, className='row d-block d-xl-flex align-items-center')
            ], className='card-body')
        ], className='card border-0 shadow')
    ], className='col-12 col-sm-6 col-xl-4 mb-4')



def customers():
    return cardFrame([
        dcc.Store(id='shared-data'),
        html.Div([
            html.Div([
                ICON.CHART_SIMPLE,
            ], className='icon-shape icon-shape-primary rounded me-4 me-sm-0', style={'background-color': '#ECEEEB', 'color': '#464A4D'}),  # #91989E
            # html.Div([
            #     html.H2("Confidence Interval", className='h5'),
            #     html.H3("345,678", className='fw-extrabold mb-1')
            # ], className='d-sm-none')
        ], className='col-12 col-xl-5 text-xl-center mb-0 mb-xl-0 d-flex align-items-center justify-content-xl-center'),
        html.Div([
            html.Div([
                dcc.Store(id='shared-data'),
                html.H2("Prediction Uncertainty", className='h6 text-gray-400 mb-0'),
                html.H3("Not Available", className='fw-extrabold mb-2', id='conf-int-value')
            ], className='d-none d-sm-block'),
            html.Small("Residual Standard Deviation", className='text-gray-500', id='conf-int-unit'),
            html.Div([
                html.Div([
                    "Since last month",
                    ICON.CHEVRON_UP_DOWN,
                    html.Span("", className='text fw-bolder', id='conf-int-change')
                ])
            ], className='small d-flex mt-1'),
        ], className='col-12 col-xl-7 px-xl-0')
    ])


def revenue():
    return cardFrame([
        dcc.Store(id='shared-data'),
        html.Div([
            html.Div([
                ICON.CHART
            ], className='icon-shape icon-shape-secondary rounded me-4 me-sm-0'),
            # html.Div([
            #     html.H2("VAR", className='fw-extrabold h5'),
            #     html.H3("$15,488", className='mb-1')  # TODO: to be populated based on file
            # ], className='d-sm-none')
        ], className='col-12 col-xl-5 text-xl-center mb-3 mb-xl-0 d-flex align-items-center justify-content-xl-center'),
        html.Div([
            html.Div([
                html.H2("VAR", className='h6 text-gray-400 mb-0'),
                html.H3("Not Available", className='fw-extrabold mb-2', id='var-pred-value'),
            ], className='d-none d-sm-block'),
            html.Small([
                # "Feb 1 - Apr 1,"
                # ICON.GLOBE.ME1,
                # "USA"
            ], className='d-flex align-items-center text-gray-500', id='var-annotation'),
            html.Div([
                html.Div([
                    "Since last month",
                    ICON.CHEVRON_UP_DOWN,
                    html.Span("", className='text-danger fw-bolder')
                ], id='var-pred-change')
            ], className='small d-flex mt-1'),
        ], className='col-12 col-xl-7 px-xl-0')
    ])


def bounceRate():
    return cardFrame([
        dcc.Store(id='shared-data'),
        html.Div([
            html.Div([
                ICON.CHART
            ], className='icon-shape icon-shape-tertiary rounded me-4 me-sm-0'),
            # html.Div([
            #     html.H2("ARIMA", className='fw-extrabold h5'),
            #     html.H3("$15,757", className='mb-1')
            # ], className='d-sm-none')
        ], className='col-12 col-xl-5 text-xl-center mb-3 mb-xl-0 d-flex align-items-center justify-content-xl-center'),
        html.Div([
            html.Div([
                html.H2("ARIMA", className='h6 text-gray-400 mb-0'),
                html.H3("Not Available", className='fw-extrabold mb-2', id='arima-pred-value'),
            ], className='d-none d-sm-block'),
            html.Small([
                # "Aug 1 - Aug 31,",
                # ICON.GLOBE.ME1,
                # "USA"
            ], className='d-flex align-items-center text-gray-500', id='arima-annotation'),
            html.Div([
                html.Div([
                    "Since last month",
                    ICON.CHEVRON_UP_DOWN,
                    html.Span("", className='text-success fw-bolder')
                ], id='arima-pred-change')
            ], className='small d-flex mt-1')
        ], className='col-12 col-xl-7 px-xl-0')
    ])
