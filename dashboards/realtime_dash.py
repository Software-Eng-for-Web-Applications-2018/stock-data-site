from app import db
from collections import deque, OrderedDict
from dash.dependencies import (Input, Output, State, Event)
from flask_security import (Security, SQLAlchemyUserDatastore, UserMixin,
    RoleMixin, current_user, login_required)
from models import StockPriceMinute
from plotly import graph_objs as go
from plotly.graph_objs import *
from plotly_app import app
from utils import (generate_table, PredictionRequest, plus_glyph, hourglass_glyph, minus_glyph)
import dash
import dash_core_components as dcc
import dash_html_components as html
import datetime
import numpy as np
import pandas as pd
import plotly.plotly as py
import plotly.graph_objs as go
import json
# from MenuTypeSymbolStore import MenuTypeSymbolStore


#based upon  https://www.youtube.com/watch?v=37Zj955LFT0 
#https://pythonprogramming.net/live-graphs-data-visualization-application-dash-python-tutorial/
# global CurrentType;
# global CurrentSymbol;
# global LastCurrentType;
# global LastCurrentSymbol;
retension = 100
x_current = []
y_current = []
latest_feature = []
x_pred = []
y_preds = OrderedDict(neur=[], svm=[], _all=[])
close_max = 1
last_sym = None
last_entry = None
current_selection = 'neutral'


ts_client = PredictionRequest()


def update_score(userid, val):
    query = '''
    INSERT INTO `user_score`
    (`userid`, score)
    VALUES({}, {})
    ON DUPLICATE KEY UPDATE
    `score` = `score` + {};
    '''.format(userid, val, val)
    pd.read_sql(query, db.engine)


def get_score(userid, val):    
    query = '''                   
    SELECT score
    FROM user_score
    WHERE userid = {}
    LIMIT 1
    '''.format(userid)  
    df = pd.read_sql(query, db.engine) 
    vals = df['score'].tolist()
    if len(vals) <= 0:
        return 0
    return vals[0]



def get_latest_data(sym):
    result = StockPriceMinute.query.filter_by(sym=sym) \
                                   .order_by(StockPriceMinute.dateid).first()
    return result.high, result.low, result.volume


def money_format(val):
    return '${0:.2f}'.format(round(val, 2))


def dt_format(val):
    return datetime.datetime.strptime(val, '%Y-%m-%d %H:%M')


with app.server.app_context():
    # Label and value pairs for dropdown
    trend_type_options = (
        ('Close', 'close'),
        ('Open', '_open'), 
        ('High', 'high'), 
        ('Low', 'low'),
        ('Volume', 'volume')
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

        StockSymlist.sort(key=lambda x: x[0])
        return tuple(StockSymlist)


    # if update is false all the records will be pulled. if update is true then only the last few elements will be pulled. 
    def GetStockDataBySymbol(Datatype,Symbol,update):

        if update:
            StockInfoObjectList = StockPriceMinute.query.filter_by(sym=Symbol).first();  # probably could chain filters together
        else:
            StockInfoObjectList = StockPriceMinute.query.filter_by(sym=Symbol);  # probably could chain filters together
        # print(StockInfoObjectList[0]);
        # print(StockInfoObjectList[0].dateid);
        # print(StockInfoObjectList[0].volume);
        closes = []
        opens = []
        lows = []
        highs = []
        volumes = []

        Dates = [];
        Data = [];
        global x_current
        global y_current
        global latest_feature
        global close_max
        x_current = []
        y_current = []
        latest_feature = []

        # Get records
        if update:
            Dates.append(StockInfoObjectList.dateid)
            closes.append(StockINfoObjectList.close)   
            opens.append(StockINfoObjectList._open)     
            lows.append(StockINfoObjectList.low)       
            highs.append(StockINfoObjectList.high)     
            volumes.append(StockINfoObjectList.volume) 
        else:
            for Record in StockInfoObjectList:
                Dates.append(Record.dateid)
                closes.append(Record.close)
                opens.append(Record._open)
                lows.append(Record.low)
                highs.append(Record.high)
                volumes.append(Record.volume)

        x_current.append(Dates[-1])
        y_current.append(closes[-1])
        latest_feature = (highs[-1] / np.max(highs), lows[-1] / np.max(lows), volumes[-1] / np.max(volumes))
        close_max = np.max(closes)
        if(Datatype == 'volume'):
            Data = volumes
        elif(Datatype == 'close'):
            Data = closes
        elif(Datatype == 'high'):
            Data = highs
        elif(Datatype == '_open'):
            Data = opens
        elif(Datatype == 'low'):
            Data = lows
        else:
            print("Bad selection")
            Data = []

        return (Dates, Data);

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

    trend_count_options = (
        ('Last Hour', '60'),
        ('Last Day', '391'),
        ('Last Week', '2730'),
        ('Last Month', '142715'),
        ('All Time', 'all'),
    )
    global current_selection
    layout = html.Div([
        html.Div([
            dcc.Interval(id='graph-update', interval=10000),
            html.H1('Real-Time Prediction Portal'),
            html.Div([
                dcc.Dropdown(                                         
                    id='rt-trend-count-dropdown',                      
                    options=[{'label': label, 'value': value}         
                             for label, value in trend_count_options], 
                    value=trend_count_options[1][1]                    
                ),                                                    
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
                        'max-height': '500px'
                    }
                ),
            ]),
            html.Div([
                html.H1('Guessing Game'),
                    html.Div(id='rt-guessing-score'),
                    dcc.RadioItems(
                        id='rt-game-radio',
                        options=[
                            {'label': "It's Going UP!", 'value': 'up'},
                            {'label': "Not Going to Guess", 'value': 'neutral'},
                            {'label': "It's Going Down!", 'value': 'down'}
                        ],
                        value=current_selection,
                        className='radio',
                        style={'padding-left': '10px'}
                    )
            ]),
            html.Div(id='rt-quick-info'),
            html.Div(id='intermediate-value', style={'display': 'none'}),
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
    @app.callback(Output("rt-stock-trend-graph", "figure"),
                  [Input('rt-trend-type-dropdown', 'value'),
                   Input('rt-trend-sym-dropdown', 'value'),
                   Input('rt-trend-count-dropdown', 'value')],
                  events=[Event('graph-update', 'interval')]) #,Event('graph-update','interval')])
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

        data_list = []
        if args[2] != 'all':
            try:
                n = int(args[2])
            except ValueError:
                n = 1440
            idx = len(X) - n
            if idx > 0:
                data_list.append({'x': list(X)[idx:], 'y': list(Y)[idx:], 'name': 'Actual'})
            else:
                data_list.append({'x': list(X)[idx:], 'y': list(Y)[idx:], 'name': 'Actual'})
        else:
            data_list.append({'x': list(X), 'y': list(Y), 'name': 'Actual'})

        # Add predictions if close is plotted
        global latest_feature 
        global last_sym
        global x_pred
        global y_preds

        run_pred = False
        # Reset plot for new syms
        if last_sym != args[1]:
            last_sym = args[1]
            x_pred = []
            for key in y_preds.keys(): y_preds[key] = []

        if len(x_pred) == 0: run_pred = True
        elif X[-1] > x_pred[-1]: run_pred = True
        if run_pred:
            # Set plot data                                       
            x_pred.append(X[-1] + datetime.timedelta(seconds=60)) 
            while len(x_pred) > retension: x_pred.pop(0)
            for ml_type in y_preds.keys():
                if key == '_all': continue
                # Requests latest prediction
                pred = ts_client.get_pred(latest_feature, 'rt', ml_type, args[1].lower())
                y_preds[ml_type].append(pred.get('ScaledPrediction', 0) * close_max)
                while len(y_preds[ml_type]) > retension: y_preds[ml_type].pop(0)

        if args[0] == 'close':
            for key in y_preds.keys():
                if key == 'neur': name = 'Neural Prediction'
                elif key == 'svm': name = 'SVM Prediction'
                elif key == 'bay': name = 'Bayesian Prediction'
                elif key == '_all': name = 'Combined Prediction'
                else: name = 'Unknown Prediction'

                data_list.append({
                    'x': x_pred,
                    'y': y_preds[key],
                    'name': name,
                    'mode': 'markers',
                    'marker': {
                        'size': 10,
                        'line': {'width': 2}
                    }
                })

        x_min = min(data_list[0]['x'])
        x_max = max(data_list[-1]['x']) + datetime.timedelta(seconds=900)

        y_min = min(data_list[0]['y'] + data_list[-1]['y']) - 1
        y_max = max(data_list[0]['y'] + data_list[-1]['y']) + 1
        return {
            'data': data_list,
            'layout': go.Layout(
                xaxis=dict(range=[x_min, x_max]),
                yaxis=dict(range=[y_min, y_max]),
                margin=go.Margin(l=50, r=50, b=50, t=50, pad=10)
            )
        }

    @app.callback(Output('rt-guessing-score', 'children'),                                          
                  [Input('rt-trend-sym-dropdown', 'value')],                                    
                  events=[Event('graph-update', 'interval')])                                   
    def score_update(guess):                                                                 
        global last_entry                                                    
        global current_selection
        current_selection = guess
        glyph = hourglass_glyph                                              
        if last_entry is None:                                               
            last_entry = y_current[-1]                                       
        elif last_entry != y_current[-1]:                                    
            diff = y_current[-1] - last_entry                                
            last_entry = y_current[-1]                                       
            if guess == 'up' and diff > -1 or guess == 'down' and diff < 0:   
                update_score(1, 1)                                           
                glyph = plus_glyph                                           
            elif guess == 'up' and diff < 0 or guess == 'down' and diff > 0: 
                update_score(1, 1)                                           
                glyph = minus_glyph                                          
        current_score = 'Current Score: {}'.format(get_score(1, 1))
        return html.Div([current_score, glyph])

    @app.callback(Output('rt-quick-info', 'children'),
                  [Input('rt-trend-sym-dropdown', 'value')],
                  events=[Event('graph-update', 'interval')])
    def quick_info_update(sym):
        '''Updates tables on dashboards.

        Section 4 requirement queries.

        args:
            sym: Stock symbol for "any" argument in requirements.

        returns:
            list: HTML headers and DCC tables
        '''
        # Really lazy hack to prevent SQL injection
        valid_syms = [val for val, _ in GetStockSymbols()]
        if sym not in valid_syms:
            return "ERROR: Invalid symbol selection"

        # Query 4.1 in requirements
        qh1 = html.H3("Company Prices")
        header = 'Price'
        df = pd.read_sql('''
        SELECT sym AS "Company", close AS "{}"
        FROM stock_price_minute
        WHERE dateid IN (
          SELECT MAX(dateid)
          FROM stock_price_minute
        )
        ORDER BY dateid DESC, sym ASC
        '''.format(header), db.engine)
        df[header] = df[header].apply(money_format)
        sym_table = generate_table(df, 10)

        # Query 4.2 in requirements
        qh2 = html.H3("Highest Price in 10 Days")
        header = 'Highest Price'
        df = pd.read_sql('''
        SELECT sym AS "Company", MAX(close) AS "{}"
        FROM stock_price_minute
        WHERE dateid >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
          AND sym = '{}';
        '''.format(header, sym), db.engine)
        df[header] = df[header].apply(money_format)
        max_table = generate_table(df, 10)

        # Query 4.3 in requirements
        qh3 = html.H3("Year Average Price")
        header = 'Average Price'
        df = pd.read_sql('''
        SELECT sym AS "Company", AVG(close) AS "{}"
        FROM stock_price_minute
        WHERE dateid >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
          AND sym = '{}';
        '''.format(header, sym), db.engine)
        df[header] = df[header].apply(money_format)
        avg_table = generate_table(df, 1)

        # Query 4.4 in requirements
        qh4 = html.H3("Year Lowest Price")
        header = 'Lowest Price'
        df = pd.read_sql('''
        SELECT sym AS "Company", MIN(close) AS "{}"
        FROM stock_price_minute
        WHERE dateid >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
          AND sym = '{}';
        '''.format(header, sym), db.engine)
        df[header] = df[header].apply(money_format)
        low_table = generate_table(df, 1)

        # Query 4.5 in requirements
        qh5 = html.H3("Average Less Than Lowest of {}".format(sym.upper()))
        header = 'Average Price'
        df = pd.read_sql('''
        SELECT sym AS "Company", sub1.close AS "{}"

        FROM (
            SELECT sym, AVG(close) AS "close"
            FROM stock_price_minute
            WHERE dateid >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
            GROUP BY sym
        ) as sub1

        LEFT JOIN (
          SELECT MIN(close) AS criteria
          FROM stock_price_minute
          WHERE dateid >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
            AND sym = '{}'
        ) AS sub2
          ON 1 = 1

        GROUP BY sym, criteria
        HAVING sub1.close < criteria
        ORDER BY sym ASC;'''.format(header, sym), db.engine)
        df[header] = df[header].apply(money_format)
        avglow_table = generate_table(df, 100)

        pred_data = html.Div([
            html.H3("Predicted Value"),
            '${0:.2f}'.format(y_preds['_all'][-1])
        ])

        return [pred_data, qh1, sym_table, qh2, max_table, qh3, avg_table, qh4,
                low_table, qh5, avglow_table]
