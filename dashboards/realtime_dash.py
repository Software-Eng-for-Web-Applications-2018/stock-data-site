from app import db
from collections import deque, OrderedDict
from dash.dependencies import (Input, Output, State, Event)
from flask_security import (Security, SQLAlchemyUserDatastore, UserMixin,
    RoleMixin, current_user, login_required)
from models import StockPriceMinute
from plotly import graph_objs as go
from plotly.graph_objs import *
from plotly_app import app
from sklearn.preprocessing import MinMaxScaler
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
ts_client = PredictionRequest()


dash_data = {
    'x_current': [],
    'y_current': [],
    'closes': [],
    'opens': [],
    'lows': [],
    'highs': [],
    'volumes': [],
    'x_pred': [],
    'y_preds': OrderedDict(neur=[], svm=[], _all=[]),
    'latest_feature': [],
    'close_max': 1,
    'close_min': 1,
    'high_max': 1, 
    'high_min': 1, 
    'low_max': 1, 
    'low_min': 1, 
    'vol_max': 1, 
    'vol_min': 1, 
    'last_sym': None,
    'last_entry': None,
    'last_glyph': hourglass_glyph,
    'nn_scale': 1
}


def norm_scale(val, _min, _max):
    return (val- _min) / (_max - _min)


def norm_descale(scaled_val, _min, _max):
    return (scaled_val * (_max - _min)) + _min


def update_score(userid, val):
    query = '''
    INSERT INTO `user_score`
    (`userid`, score)
    VALUES({}, {})
    ON DUPLICATE KEY UPDATE
    `score` = `score` + {};
    '''.format(userid, val, val)
    db.engine.execute(query)


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
    def GetStockSymbols():
        # pull the stock infor from the database --- HIGHLY inefficient way to do this but, very easy to write and I don't have time to go into depth with flask-sql. 
        StockInfoObjectList = StockPriceMinute.query.all(); # change Query!!!!  Need distant or return unique values.

        # #GET UNIQUE 
        # loop over all objects returned and use a set to filter for unique values-- Should be filtered in query! COmmunications cost could slow this down quite badly. 
        StockSymOrderedSet = set();
        for StockInfoObject in StockInfoObjectList:
            StockSymOrderedSet.add(StockInfoObject.sym);

        # just get it in the correct format
        StockSymlist = [];
        for StockSymbol in StockSymOrderedSet:
            StockSet = (StockSymbol,StockSymbol);
            StockSymlist.append(StockSet);

        StockSymlist.sort(key=lambda x: x[0])
        return tuple(StockSymlist)

    def GetStockDataBySymbol(Datatype, Symbol, update):
        '''Fill dash_data variable with proper data.'''
        global dash_data

        if update:
            StockInfoObjectList = StockPriceMinute.query.filter_by(sym=Symbol).first()
        elif dash_data['last_sym'] == Symbol:
            # query for only new data
            if len(dash_data['x_current']) > 0:
                max_date = dash_data['x_current'][-1]
            else:
                max_date = datetime.date(2015, 1, 1)
            StockInfoObjectList = StockPriceMinute.query \
                                                  .filter(StockPriceMinute.dateid > max_date) \
                                                  .filter_by(sym=Symbol)
        else:
            # Reset values if for new symbol
            dash_data['x_current'] = []      
            dash_data['y_current'] = []      
            dash_data['closes'] = []
            dash_data['opens'] = []
            dash_data['lows'] = []
            dash_data['highs'] = []
            dash_data['volumes'] = []
            StockInfoObjectList = StockPriceMinute.query.filter_by(sym=Symbol)
        dash_data['latest_feature'] = [] 

        for record in StockInfoObjectList:
            dash_data['x_current'].append(record.dateid) 
            dash_data['closes'].append(record.close)     
            dash_data['opens'].append(record._open)      
            dash_data['lows'].append(record.low)         
            dash_data['highs'].append(record.high)       
            dash_data['volumes'].append(record.volume)   

        dash_data['latest_feature'] = (
            dash_data['highs'][-1],
            dash_data['lows'][-1],
            dash_data['volumes'][-1]
        )
        if len(dash_data['closes']) > 0:
            dash_data['close_min'] = np.min(dash_data['closes'])
            dash_data['close_max'] = np.max(dash_data['closes'])
            dash_data['high_min'] = np.min(dash_data['highs']) 
            dash_data['high_max'] = np.max(dash_data['highs']) 
            dash_data['low_min'] = np.min(dash_data['lows']) 
            dash_data['low_max'] = np.max(dash_data['lows']) 
            dash_data['vol_min'] = np.min(dash_data['volumes']) 
            dash_data['vol_max'] = np.max(dash_data['volumes']) 
        else:
            dash_data['close_max'] = 1
            dash_data['high_min'] = 1
            dash_data['high_max'] = 1
            dash_data['low_min'] = 1
            dash_data['low_max'] = 1
            dash_data['vol_min'] = 1
            dash_data['vol_max'] = 1

        if(Datatype == 'volume'): dash_data['y_current'] = dash_data['volumes']
        elif(Datatype == 'close'): dash_data['y_current'] = dash_data['closes']
        elif(Datatype == 'high'): dash_data['y_current'] = dash_data['highs']
        elif(Datatype == '_open'): dash_data['y_current'] = dash_data['opens']
        elif(Datatype == 'low'): dash_data['y_current'] = dash_data['lows']
        else: dash_data['y_current'] = lows

        #features = np.array([dash_data['highs'], dash_data['lows'], dash_data['volumes']])
        #scaler = MinMaxScaler(feature_range=(-1, 1))
        #f_scaler = scaler.fit(features)
        #x_scaler = f_scaler.transform(features)
        #print(x_scaler)

    trend_sym_options = GetStockSymbols();

    # THIS CANNOT BE THE RIGHT OR CLEAN WAY TO DO THIS   FIXME!
    CurrentType ='volume';
    LastCurrentType = CurrentType;

    CurrentSymbol = trend_sym_options[0][1];
    LastCurrentSymbol =  CurrentSymbol; 
    GetStockDataBySymbol(CurrentType, CurrentSymbol, False);

    #Need an inital populate function 
    X=deque(maxlen=len(dash_data['x_current']))
    Y=deque(maxlen=len(dash_data['y_current']))

    #populate the init values 
    X.extend(dash_data['x_current'])
    Y.extend(dash_data['y_current'])

    trend_count_options = (
        ('Last Hour', '60'),
        ('Today', 'today'),
        ('Last Day', '391'),
        ('Last Week', '2730'),
        ('Last Month', '142715'),
        ('All Time', 'all'),
    )
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
                html.Div(
                    dcc.Slider(
                        id='rt-guess-slider',
                        min=0,
                        max=2,
                        value=1,
                        step=None,
                        marks={
                            0: "It's Going Down!",
                            1: "I'm Not Guessing",
                            2: "It's Going Up!",
                        },
                    ), style={
                        'padding-top': '20px',
                        'padding-bottom': '50px',
                        'padding-left': '200px',
                        'padding-right': '200px'
                    }
                ),
                html.Div(id='rt-guessing-score')
            ]),
            html.Div(id='rt-quick-info'),
            html.Div(id='intermediate-value', style={'display': 'none'}),
            html.P(id='placeholder'),   # THIS IS A HACK! TO ALLOW US TO UPDATE VALUES ON A CALLBACK
            html.Div(id='intermediate-value', style={'display': 'none'}),
        ], className="container")
    ], style={'padding-bottom': '20px'})

    #This is really what they suggest 
    #https://dash.plot.ly/sharing-data-between-callbacks
    @app.callback(Output("rt-stock-trend-graph", "figure"),
                  [Input('rt-trend-type-dropdown', 'value'),
                   Input('rt-trend-sym-dropdown', 'value'),
                   Input('rt-trend-count-dropdown', 'value')],
                  events=[Event('graph-update', 'interval')])
    def update_trend(*args):
        try:
            X.clear()
            Y.clear()
            GetStockDataBySymbol(args[0], args[1], False)
            X.extend(dash_data['x_current'])
            Y.extend(dash_data['y_current'])
        except Exception as e:
            # Debug print and return data not found message
            print(e.message)
            return "Stock Data Not Found"

        data_list = []
        if args[2] == 'today':                                          
            # UTC to est
            dt_today = (datetime.datetime.today() - datetime.timedelta(seconds=14400)).replace(hour=0)
            n = len([date for date in list(X) if date > dt_today])
            idx = max((len(X) - n, 0))
            data_list.append({                                            
                'x': list(X)[idx:],                                       
                'y': list(Y)[idx:],                                       
                'name': 'Actual'                                          
            })                                                            
        elif args[2] != 'all':
            try:
                n = int(args[2])
            except ValueError:
                n = 1440
            idx = max((len(X) - n, 0))
            data_list.append({
                'x': list(X)[idx:],
                'y': list(Y)[idx:],
                'name': 'Actual'
            })
        else:
            data_list.append({'x': list(X), 'y': list(Y), 'name': 'Actual'})

        # Add predictions if close is plotted

        run_pred = False
        # Reset plot for new syms
        if dash_data['last_sym'] != args[1]:
            dash_data['last_sym'] = args[1]
            dash_data['x_pred'] = []
            for key in dash_data['y_preds'].keys(): dash_data['y_preds'][key] = []

        if len(dash_data['x_pred']) == 0: run_pred = True
        elif X[-1] > dash_data['x_pred'][-1]: run_pred = True
        if run_pred:
            # Set plot data                                       
            dash_data['x_pred'].append(X[-1] + datetime.timedelta(seconds=60)) 
            while len(dash_data['x_pred']) > retension: dash_data['x_pred'].pop(0)

            close_min = dash_data['close_min'] 
            close_max = dash_data['close_max'] 
            for ml_type in dash_data['y_preds'].keys():
                if ml_type == '_all': continue
                # Requests latest prediction
                if ml_type == 'svm':
                    close_val = dash_data['closes'][-1]
                    post_feature = (norm_scale(close_val, close_min, close_max),)
                    scaled_pred = ts_client.get_pred(post_feature, 'rt', ml_type, args[1].lower()).get('ScaledPrediction', 0)
                    pred = norm_descale(scaled_pred, close_min, close_max)
                    dash_data['y_preds'][ml_type].append(pred)
                else:
                    high_val, low_val, vol_val = dash_data['latest_feature']
                    high_min = dash_data['high_min']
                    high_max = dash_data['high_max']
                    low_min = dash_data['low_min'] 
                    low_max = dash_data['low_max'] 
                    vol_min = dash_data['vol_min'] 
                    vol_max = dash_data['vol_max'] 
                    high_scale = norm_scale(high_val, high_min, high_max)
                    low_scale = norm_scale(low_val, low_min, low_max)
                    vol_scale = norm_scale(vol_val, vol_min, vol_max)
                    post_feature = (high_scale, low_scale, vol_scale)
                    scaled_pred = ts_client.get_pred(post_feature, 'rt', ml_type, args[1].lower()).get('ScaledPrediction', 0)
                    pred = norm_descale(scaled_pred, close_min, close_max)
                    dash_data['y_preds'][ml_type].append(pred)


                while len(dash_data['y_preds'][ml_type]) > retension: dash_data['y_preds'][ml_type].pop(0)

        if args[0] == 'close':
            for key in dash_data['y_preds'].keys():
                if key == 'neur': name = 'Neural Prediction'
                elif key == 'svm': name = 'SVM Prediction'
                elif key == 'bay': name = 'Bayesian Prediction'
                elif key == '_all': name = 'Combined Prediction'
                else: name = 'Unknown Prediction'

                data_list.append({
                    'x': dash_data['x_pred'],
                    'y': dash_data['y_preds'][key],
                    'name': name,
                    'mode': 'markers',
                    'marker': {
                        'size': 10,
                        'line': {'width': 2}
                    }
                })

        #x_min = min(data_list[0]['x'])
        #x_max = max(data_list[-1]['x']) + datetime.timedelta(seconds=900)
        #ys = [item for data in data_list for item in data['y']]
        #y_min = min(ys) - 1
        #y_max = max(ys) + 1
        return {
            'data': data_list,
            'layout': go.Layout(
                #xaxis=dict(range=[x_min, x_max]),
                #yaxis=dict(range=[y_min, y_max]),
                margin=go.Margin(l=50, r=50, b=50, t=50, pad=10)
            )
        }

    @app.callback(Output('rt-guessing-score', 'children'),                                          
                  [Input('rt-guess-slider', 'value')],
                  events=[Event('graph-update', 'interval')])
    def score_update(guess):                                                                 
        global dash_data
        glyph = dash_data['last_glyph']
        if dash_data['last_entry'] is None:                                                                          
            dash_data['last_entry'] = dash_data['y_current'][-1]                                                                  
        elif dash_data['last_entry'] != dash_data['y_current'][-1]:                                                               
            diff = dash_data['y_current'][-1] - dash_data['last_entry']
            dash_data['last_entry'] = dash_data['y_current'][-1]                                                                  
            if (guess == 2 and diff > 0) or (guess == 0 and diff < 0):
                update_score(1, 1)                                                                      
                glyph = plus_glyph                                                                      
                dash_data['last_glyph'] = glyph
            elif (guess == 2 and diff < 0) or (guess == 0 and diff > 0):    
                update_score(1, -1)                                                                      
                glyph = minus_glyph                                                                     
                dash_data['last_glyph'] = glyph
            else:
                glyph = hourglass_glyph                                                                         
                dash_data['last_glyph'] = glyph
        current_score = 'Current Score: {} '.format(get_score(1, 1))                                     
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

        if len(dash_data['y_preds']['_all']) <= 0:
            display_val = 'Loading...'
        else:
            display_val = '${0:.2f}'.format(dash_data['y_preds']['_all'][-1])

        pred_data = html.Div([html.H3("Predicted Value"), display_val])

        return [pred_data, qh1, sym_table, qh2, max_table, qh3, avg_table, qh4,
                low_table, qh5, avglow_table]
