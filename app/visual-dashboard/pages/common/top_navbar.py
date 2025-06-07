from dash import html


def topNavBar():
    """"Top navbar, search form ..."""
    return html.Nav([
        html.Div([
            html.Div([
                html.Div([
                ], className='d-flex align-items-center')
            ], className='d-flex justify-content-between w-100', id='navbarSupportedContent')
        ], className='container-fluid px-0')
    ], className='navbar navbar-top navbar-expand navbar-dashboard navbar-dark ps-0 pe-2 pb-0')
