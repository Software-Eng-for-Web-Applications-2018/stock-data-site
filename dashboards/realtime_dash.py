from app import db
from dash.dependencies import (Input, Output, State, Event)
from flask_security import (Security, SQLAlchemyUserDatastore, UserMixin,
    RoleMixin, current_user, login_required)
from models import StockPriceMinute
from plotly import graph_objs as go
from plotly.graph_objs import *
from plotly_app import app
import dash
import dash_core_components as dcc
import dash_html_components as html
import datetime
import numpy as np
import plotly.plotly as py


with app.server.app_context():
    # Label and value pairs for dropdown
    trend_type_options = (
        ('Volume', 'volume'),
        ('Close', 'close')
    )
    # TODO: Query from available options
    trend_sym_options = (
        ('AMD', 'AMD'),
        ('GOOGL', 'GOOGL')
    )
    
    layout = html.Div([
        html.Div([
            html.H1('Real-Time Prediction Portal'),
            html.Div([
                dcc.Dropdown(
                    id='trend-type-dropdown',
                    options=[{'label': label, 'value': value}
                             for label, value in trend_type_options],
                    value=trend_type_options[0][1]
                ),
                dcc.Dropdown(
                    id='trend-sym-dropdown',
                    options=[{'label': label, 'value': value}
                             for label, value in trend_sym_options],
                    value=trend_sym_options[0][1]
                ),
                dcc.Graph(
                    id='stock-trend-graph',
                    style={
                        'max-height': '300px'
                    }
                ),
            ]),
        ], className="container")
    ], style={'padding-bottom': '20px'})

    @app.callback(Output("stock-trend-graph", "figure"),
                  [Input('trend-type-dropdown', 'value'),
                   Input('trend-sym-dropdown', 'value')])
    def update_trend(*args):
        try:
            xs, ys = [0, 1, 2], [0, 1, 2]
        except Exception as e:
            # Debug print and return data not found message
            print(e.message)
            return "Stock Data Not Found"
    
        return {
            'data': [{
                'x': xs,
                'y': ys
            }],
            'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}
        }
