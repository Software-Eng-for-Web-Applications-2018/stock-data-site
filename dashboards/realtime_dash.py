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
from collections import deque

from models import StockPriceDay

X=deque(maxlen=20)
Y=deque(maxlen=20)
X.append(1)
Y.append(1)


with app.server.app_context():
    # Label and value pairs for dropdown
    trend_type_options = (
        ('Volume', 'volume'),
        ('Close', 'close'),
        ('High', 'high'), 
        ('Open', '_open'), 
        ('Low', 'low')
    )
    # TODO: Query from available options
    def GetStockSymbols():
        # pull the stock infor from the database --- HIGHLY inefficient way to do this but, very easy to write and I don't have time to go into depth with flask-sql. 
        StockInfoObjectList = StockPriceDay.query.all(); # change Query!!!!  Need distant or return unique values.



        # #GET UNIQUE 
        # loop over all objects returned and use a set to filter for unique values-- Should be filtered in query! COmmunications cost could slow this down quite badly. 
        StockSymOrderedSet = set();
        for StockInfoObject in StockInfoObjectList:
            StockSymOrderedSet.add(StockInfoObject.sym);

        #print(StockSymOrderedSet);
        # just get it in the correct format
        StockSymlist = [];
        for StockSymbol in StockSymOrderedSet:
            StockSet = (StockSymbol,StockSymbol);
            StockSymlist.append(StockSet);

        return tuple(StockSymlist);


    def GetStockDataBySymbol(Datatype,Symbol):
        StockInfoObjectList = StockPriceDay.query.filter_by(sym = Symbol);  # probably could chain filters together
        # print(StockInfoObjectList[0]);
        # print(StockInfoObjectList[0].dateid);
        # print(StockInfoObjectList[0].volume);

        Dates = [];
        Data = [];

        if(Datatype == 'volume'):
            for Record in  StockInfoObjectList:
                Dates.append(Record.dateid);
                Data.append(Record.volume);
        elif(Datatype == 'close'):
            for Record in  StockInfoObjectList:
                Dates.append(Record.dateid);
                Data.append(Record.volume);
        elif(Datatype == 'high'):
            for Record in  StockInfoObjectList:
                Dates.append(Record.dateid);
                Data.append(Record.high);
        elif(Datatype == '_open'):
            for Record in  StockInfoObjectList:
                Dates.append(Record.dateid);
                Data.append(Record._open);
        elif(Datatype == 'low'):
            for Record in  StockInfoObjectList:
                Dates.append(Record.dateid);
                Data.append(Record.low);
        else:
            print('Error!');


        return (Dates,Data);

    trend_sym_options = GetStockSymbols();
    
    layout = html.Div([
        html.Div([
            html.H1('Real-Time Prediction Portal'),
            html.Div([
                dcc.Dropdown(
                    id='rt-trend-type-dropdown',
                    options=[{'label': label, 'value': value}
                             for label, value in trend_type_options],
                    value=trend_type_options[0][1]
                ),
                dcc.Dropdown(
                    id='rt-trend-sym-dropdown',
                    options=[{'label': label, 'value': value}
                             for label, value in trend_sym_options],
                    value=trend_sym_options[0][1]
                ),
                dcc.Graph(
                    id='rt-stock-trend-graph',animate=True,
                    style={
                        'max-height': '300px'
                    }
                ),
                dcc.Interval(id='graph-update', interval=60000)
            ]),
        ], className="container")
    ], style={'padding-bottom': '20px'})

    @app.callback(Output("rt-stock-trend-graph", "figure"),[Input('rt-trend-type-dropdown', 'value'),Input('rt-trend-sym-dropdown', 'value'),Event('graph-update','interval')])


    def update_trend(*args):
        #('type','sym')
        #print(args);
        TrendData = GetStockDataBySymbol(args[0],args[1]);

        try:
            xs = TrendData[0];
            ys = TrendData[1];
        except Exception as e:
            # Debug print and return data not found message
            print(e.message)
            return "Stock Data Not Found"
    
        return {
            'data': [{
                'x': xs,
                'y': ys
            }],
            'layout': go.Layout(xaxis = dict(range=[min(x),min(x)]),yaxis = dict(range=[min(y),min(y)]) )
        }




