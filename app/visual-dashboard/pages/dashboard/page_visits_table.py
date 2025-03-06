from collections import OrderedDict
from dash import html, dcc
import pandas as pd

from dash_spa.components.table import TableAIO, TableContext
from ..icons import ICON

data=[{'Release Date': '', 'Data Series': 'Not Available', 'Impact': ''}]

class PageVisitsTable(TableAIO):

    TABLE_CLASS_NAME = 'table align-items-center table-flush'

    def tableRow(self, index, args):
        try:
            name, views, rate, change = args.values()
        except ValueError:
            name, views, rate = args.values()
            change = None

        if change == "Up":
            icon = ICON.ARROW_NARROW_UP
        elif change == "Down":
            icon = ICON.ARROW_NARROW_DOWN
        else:
            icon = None

        return  html.Tr([
            html.Th(name, className='text-gray-900', scope='row'),
            html.Td(views, className='text-gray-900'),
            html.Td(icon, className='text-gray-900', style={'textAlign': 'center', 'verticalAlign': 'middle'}),
            # html.Td(value, className='fw-bolder text-gray-500'),
            # html.Td([
            #     html.Div([
            #         icon,
            #         rate
            #     ], className='d-flex')
            # ], className='text-gray-900')
        ])


@TableContext.Provider(id='page_visits_table')
def pageVisitsTable():
    table = PageVisitsTable(
        data=data,  # This will be populated dynamically via callback
        columns=[{'id': c, 'name': c} for c in ['Release Date', 'Data Series', 'Impact']],
        )

    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.H2("Local Explanation", className='fs-5 fw-bold mb-0')
                    ], className='col'),
                    # html.Div([
                    #     dcc.Link("See all", href='#', className='btn btn-sm btn-primary')
                    # ], className='col text-end')
                ], className='row align-items-center')
            ], className='card-header'),
            html.Div(table, className='table-responsive', id='local-explanation-table', style={'maxHeight': '480px', 'overflowY': 'auto'})
        ], className='card border-0 shadow')
    ], className='col-12 mb-4')
