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
        ])

def category_legend():
    categories = [
        ("Housing and construction", "#b8584b"),
        ("Manufacturing", "#d19a4b"),
        ("Surveys", "#4a508e"),
        ("Retail and consumption", "#6a8759"),
        ("Income", "#58a5d2"),
        ("Labor", "#c9998e"),
        ("International trade", "#a4ae91"),
        ("Prices", "#c396db"),
        ("Others", "#d3d3d3"),
    ]

    def create_legend_item(label, color):
        return html.Span([
            html.Span(style={
                'display': 'inline-block',
                'width': '12px',
                'height': '12px',
                'backgroundColor': color,
                'marginRight': '6px',
                'verticalAlign': 'middle'
            }),
            html.Span(label, style={'fontSize': '0.875rem'})
        ], style={'marginRight': '20px', 'whiteSpace': 'nowrap'})

    row1 = categories[:4]
    row2 = categories[4:]

    return html.Div([
        html.Div(
            [create_legend_item(label, color) for label, color in row1],
            style={
                'display': 'flex',
                'justifyContent': 'center',
                'gap': '20px',
                'marginBottom': '8px',
                'flexWrap': 'wrap',

            }
        ),
        html.Div(
            [create_legend_item(label, color) for label, color in row2],
            style={
                'display': 'flex',
                'justifyContent': 'center',
                'gap': '20px',
                'flexWrap': 'wrap'
            }
        )
    ], style={'paddingTop': '0rem', 'marginBottom': '0rem', 'paddingLeft': '1rem', 'paddingRight': '1rem'})

# def category_legend():
#     categories = {
#         "Housing and construction": "#b8584b",
#         "Manufacturing": "#d19a4b",
#         "Surveys": "#4a508e",
#         "Retail and consumption": "#6a8759",
#         "Income": "#58a5d2",
#         "Labor": "#c9998e",
#         "International trade": "#a4ae91",
#         "Prices": "#c396db",
#         "Others": "#d3d3d3",
#     }

#     legend_items = []
#     for label, color in categories.items():
#         legend_items.append(html.Span([
#             html.Span(style={
#                 'display': 'inline-block',
#                 'width': '12px',
#                 'height': '12px',
#                 'backgroundColor': color,
#                 'marginRight': '6px',
#                 'verticalAlign': 'middle'
#             }),
#             html.Span(label)
#         ], style={'marginRight': '20px', 'whiteSpace': 'nowrap', 'fontSize': '0.875rem'}))

#     return html.Div(
#         html.Div(legend_items, style={
#             'display': 'inline-flex',
#             'gap': '20px',
#             'whiteSpace': 'nowrap',
#             'padding': '0 1rem'
#         }),
#         style={
#             'overflowX': 'auto',
#             'overflowY': 'hidden',
#             'width': 'max-content',
#             'maxWidth': '700px',  # Adjust to show about 4 items
#             'margin': '0 auto 1rem',
#             'WebkitOverflowScrolling': 'touch',
#             'scrollbarWidth': 'none',         # Firefox
#             '-msOverflowStyle': 'none',       # IE 10+
#         }
#     )



@TableContext.Provider(id='page_visits_table')
def pageVisitsTable():
    table = PageVisitsTable(
        data=data,  # This will be populated dynamically via callback
        columns=[{'id': c, 'name': c} for c in ['Release Date', 'Data Series', 'Impact']],
        )

    return html.Div([
        html.Div([
            # Header
            html.Div([
                html.Div([
                    html.H3("Local Explanation", className='fs-5 fw-normal mb-1'),
                ], className='col'),
                html.P("Impact of Data Releases", className='ms-0.5 mb-3'),
                # category_legend(),
            ], className='row align-items-center card-header mb-0', style={'borderBottom': 'none'}),

            # Table
            html.Div(table, className='table-responsive mt-0', id='local-explanation-table',
                     style={'maxHeight': '540px', 'overflowY': 'auto'}),

            # Footer
            html.Div([
                # html.P("Data as of Date: ", className="small pe-4 ms-4 text-mute", id="data-as-of-date"),
                # html.P(
                #     html.Div([
                #         html.Span(ICON.DIAMOND), html.Span("Last Run Watermark: ", className="small pe-4 text-mute", id="nowcast-as-of-date")
                #     ]), className="mb-1 mt-0 ms-4"
                #     ),
            ], className='col-12 py-4 mb-xl-0 mt-4 mb-1'),
        ], className='card border-0 shadow')
    ], className='col-12 mb-3')