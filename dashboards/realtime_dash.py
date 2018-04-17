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

from models import StockPriceMinute
# from MenuTypeSymbolStore import MenuTypeSymbolStore


#based upon  https://www.youtube.com/watch?v=37Zj955LFT0 
#https://pythonprogramming.net/live-graphs-data-visualization-application-dash-python-tutorial/
# global CurrentType;
# global CurrentSymbol;
# global LastCurrentType;
# global LastCurrentSymbol;


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
        StockInfoObjectList = StockPriceMinute.query.all(); # change Query!!!!  Need distant or return unique values.

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


    # if update is false all the records will be pulled. if update is true then only the last few elements will be pulled. 
    def GetStockDataBySymbol(Datatype,Symbol,update):

        if(update == True):
            StockInfoObjectList = StockPriceMinute.query.filter_by(sym = Symbol).first();  # probably could chain filters together
        else:
            StockInfoObjectList = StockPriceMinute.query.filter_by(sym = Symbol);  # probably could chain filters together
        # print(StockInfoObjectList[0]);
        # print(StockInfoObjectList[0].dateid);
        # print(StockInfoObjectList[0].volume);

        Dates = [];
        Data = [];

        if(Datatype == 'volume'):
            if(update == True):
                Dates.append(StockInfoObjectList.dateid);
                Data.append(StockInfoObjectList.volume);
            else:
                for Record in StockInfoObjectList:
                    Dates.append(Record.dateid);
                    Data.append(Record.volume);
        elif(Datatype == 'close'):
            for Record in  StockInfoObjectList:
                Dates.append(Record.dateid);
                Data.append(Record.close);
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

    # THIS CANNOT BE THE RIGHT OR CLEAN WAY TO DO THIS   FIXME!
    CurrentType ='volume';
    LastCurrentType = CurrentType;

    CurrentSymbol = trend_sym_options[0][1];
    LastCurrentSymbol =  CurrentSymbol; 
    InitValues = GetStockDataBySymbol(CurrentType,CurrentSymbol,False);

    #Need an inital populate function 
    X=deque(maxlen=len(InitValues[0]))
    Y=deque(maxlen=len(InitValues[1]))

    #populate the init values 
    X.extend(InitValues[0])
    Y.extend(InitValues[1])
    
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
                dcc.Interval(id='graph-update', interval=10000)
            ]),
            html.P(id='placeholder'),   # THIS IS A HACK! TO ALLOW US TO UPDATE VALUES ON A CALLBACK
            html.Div(id='intermediate-value', style={'display': 'none'}),
        ], className="container")
    ], style={'padding-bottom': '20px'})


    # @app.callback(Output('intermediate-value', 'children'),[Input('rt-trend-type-dropdown', 'value'),Input('rt-trend-sym-dropdown', 'value')])  #,Event('graph-update','interval')])

    # def update_Menu(*args):
    #     #('type','sym')
    #     # MenuTypeSymbolStore.SetType(self,args[0]);
    #     # MenuTypeSymbolStore.SetSymbol(self,args[1]);
    #     print("Update_Menu Called");
    #     #CurrentType=args[0];
    #     #CurrentSymbol= args[1];

    #     #print("Current Type is :" + CurrentType);
    #     #print("Current Symbol is :" + CurrentSymbol);

    #     return args.to_json();

    #This is really what they suggest 
    #https://dash.plot.ly/sharing-data-between-callbacks
    @app.callback(Output("rt-stock-trend-graph", "figure"),[Input('rt-trend-type-dropdown', 'value'),Input('rt-trend-sym-dropdown', 'value')],events=[Event('graph-update', 'interval')]) #,Event('graph-update','interval')])


    def update_trend(*args):
        #('type','sym')
        print(args);

        try:

            # if((CurrentType == LastCurrentType) and (CurrentSymbol == LastCurrentSymbol)): # same data, just extend 
            #     TrendData = GetStockDataBySymbol(CurrentType,CurrentSymbol,True);
            #     if(X[-1] != TrendData[0]): # check that we are not adding the same date to the end of the graph 
            #         X.extend(TrendData[0]);
            #         Y.extend(TrendData[1]);
            # else:
            X.clear();
            Y.clear();
            TrendData = GetStockDataBySymbol(args[0],args[1],False); # New data 
            X.extend(TrendData[0])
            Y.extend(TrendData[1])
            #LastCurrentType = CurrentType;
            #LastCurrentSymbol =  CurrentSymbol; 

        except Exception as e:
            # Debug print and return data not found message
            print(e.message)
            return "Stock Data Not Found"
    
        return {
            'data': [{
                'x': list(X),
                'y': list(Y)
            }],
            'layout': go.Layout(xaxis = dict(range=[min(X),max(X)]),yaxis = dict(range=[min(Y),max(Y)]) )
        }




