# written by: John Grun and Kevin Pielacki
# tested by: John Grun and Kevin Pielacki


from app import db
from collections import (deque, OrderedDict)
from dash.dependencies import (Input, Output, State, Event)
from flask_security import (Security, SQLAlchemyUserDatastore, UserMixin,
    RoleMixin, current_user, login_required)
from itertools import cycle
from models import StockPriceDay
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


# based upon  https://www.youtube.com/watch?v=37Zj955LFT0 
# https://pythonprogramming.net/live-graphs-data-visualization-application-dash-python-tutorial/
retension = 10
ts_client = PredictionRequest()


buy_img_url = 'https://proxy.duckduckgo.com/iu/?u=http%3A%2F%2Fwww.jeffbullas.com%2Fwp-content%2Fuploads%2F2009%2F03%2FBuy-now-button.jpg&f=1'
sell_img_url = 'https://proxy.duckduckgo.com/iu/?u=https%3A%2F%2Fwww.peakprosperity.com%2Fsites%2Fdefault%2Ffiles%2Fcontent%2Farticle%2Fheader-media-background-image%2Fsell-time-228002737.jpg&f=1'
load_img_url = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRpMoo13mTQR8imvNh-UZyvHsKAlTmng9AWF4w9VLjKS7ahMzSw'
colors = ('green', 'red', 'orange', 'pink', 'purple')
key_order = ('bay', 'neur', 'svm', '_all', 'projected')


dash_data = {
    'x_current': [],
    'y_current': [],
    'closes': [],
    'opens': [],
    'lows': [],
    'highs': [],
    'volumes': [],
    'x_pred': [],
    'y_preds': OrderedDict(neur=[], svm=[], bay=[], _all=[], projected=[]),
    'latest_feature': [],
    'close_max': 1,
    'close_min': 1,
    'close_mean': 0,
    'high_max': 1, 
    'high_min': 1, 
    'high_mean': 0,
    'low_max': 1, 
    'low_min': 1, 
    'low_mean': 0,
    'vol_max': 1, 
    'vol_min': 1, 
    'vol_mean': 0,
    'last_sym': None,
    'last_entry': None,
    'last_glyph': hourglass_glyph,
    'nn_scale': 1
}


def norm_scale(val, _mean, _min, _max):                   
    return (val - _mean) / (_max - _min)                  
                                                          
                                                          
def norm_descale(scaled_val, _mean, _min, _max):          
    return (scaled_val * (_max - _min)) + _mean           


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
    result = StockPriceDay.query.filter_by(sym=sym) \
                                   .order_by(StockPriceDay.dateid).first()
    return result.high, result.low, result.volume


def money_format(val):
    return '${0:.2f}'.format(round(val, 2))


def combine_predictions(predictions, actual):
    '''Weigh each algorithm by percent error.
    
    args:
        predictions (dict): Machine learning algorithm with value pair.
            ml_type: values
        actual (float): Latest actual value to weigh against.
    returns:
        float: Weight prediction value
    '''
    p_errors = []
    p_vals = []
    for key in predictions.keys():
        if key not in ('bay', 'neur', 'sv'): continue
        val = predictions[key]
        if len(val) <= 0: continue
        else: val = val[-1]
        p_errors.append(np.absolute((actual - val) / actual))
        p_vals.append(val)
    p_errors = np.array(p_errors)
    p_errors_inv = np.array(np.absolute(1 - p_errors))
    w_sum = np.sum(p_errors_inv)
    weights = (p_errors_inv / w_sum)
    return np.sum(weights * p_vals).tolist()


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
        StockInfoObjectList = StockPriceDay.query.all(); # change Query!!!!  Need distant or return unique values.

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
            StockInfoObjectList = StockPriceDay.query.filter_by(sym=Symbol).first()
        elif dash_data['last_sym'] == Symbol:
            # query for only new data
            if len(dash_data['x_current']) > 0:
                max_date = dash_data['x_current'][-1]
            else:
                max_date = datetime.date(2015, 1, 1)
            StockInfoObjectList = StockPriceDay.query \
                                                .filter(StockPriceDay.dateid > max_date) \
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
            StockInfoObjectList = StockPriceDay.query.filter_by(sym=Symbol)
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
            dash_data['close_mean'] = np.mean(dash_data['closes']) 
            dash_data['high_min'] = np.min(dash_data['highs'])     
            dash_data['high_max'] = np.max(dash_data['highs'])     
            dash_data['high_mean'] = np.mean(dash_data['highs'])   
            dash_data['low_min'] = np.min(dash_data['lows'])       
            dash_data['low_max'] = np.max(dash_data['lows'])       
            dash_data['low_mean'] = np.mean(dash_data['lows'])     
            dash_data['vol_min'] = np.min(dash_data['volumes'])    
            dash_data['vol_max'] = np.max(dash_data['volumes'])    
            dash_data['vol_mean'] = np.mean(dash_data['volumes'])  
        else:
            dash_data['close_max'] = 1  
            dash_data['close_min'] = 1  
            dash_data['close_mean'] = 0 
            dash_data['high_min'] = 1   
            dash_data['high_max'] = 1   
            dash_data['high_mean'] = 0  
            dash_data['low_min'] = 1    
            dash_data['low_max'] = 1    
            dash_data['low_mean'] = 0   
            dash_data['vol_min'] = 1    
            dash_data['vol_max'] = 1    
            dash_data['vol_mean'] = 0   

        if(Datatype == 'volume'): dash_data['y_current'] = dash_data['volumes']
        elif(Datatype == 'close'): dash_data['y_current'] = dash_data['closes']
        elif(Datatype == 'high'): dash_data['y_current'] = dash_data['highs']
        elif(Datatype == '_open'): dash_data['y_current'] = dash_data['opens']
        elif(Datatype == 'low'): dash_data['y_current'] = dash_data['lows']
        else: dash_data['y_current'] = lows

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
        ('Past Week', 8),
        ('Past Month', 32),
        ('Past Year', 391),
        ('All Time', 'all')
    )
    trend_projection_options = (
        ('10', 10),
        ('25', 25),
        ('50', 50)
    )
    layout = html.Div([
        html.Div([
            dcc.Interval(id='graph-update', interval=10000),
            html.H1('Historical Prediction Portal'),
            html.Div([
                dcc.Dropdown(                                         
                    id='hist-trend-count-dropdown',                      
                    options=[{'label': label, 'value': value}         
                             for label, value in trend_count_options], 
                    value=trend_count_options[1][1]                    
                ),                                                    
                dcc.Dropdown(
                    id='hist-trend-type-dropdown',
                    options=[{'label': label, 'value': value}
                             for label, value in trend_type_options],
                    value=trend_type_options[0][1]
                ),
                dcc.Dropdown(
                    id='hist-trend-sym-dropdown',
                    options=[{'label': label, 'value': value}
                             for label, value in trend_sym_options],
                    value=trend_sym_options[0][1]
                ),
                dcc.Dropdown(                                        
                    id='hist-trend-projection-dropdown',                      
                    options=[{'label': label, 'value': value}        
                             for label, value in trend_projection_options], 
                    value=trend_projection_options[0][1]                    
                ),                                                   
                dcc.Graph(
                    id='hist-stock-trend-graph',animate=True,
                    style={
                        'max-height': '500px'
                    }
                ),
            ]),
            html.Div([
                html.H1('Guessing Game'),
                html.Div(
                    dcc.Slider(
                        id='hist-guess-slider',
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
                html.Div(id='hist-guessing-score')
            ]),
            html.Div(id='hist-quick-info'),
            html.Div(id='intermediate-value', style={'display': 'none'}),
            html.P(id='placeholder'),   # THIS IS A HACK! TO ALLOW US TO UPDATE VALUES ON A CALLBACK
            html.Div(id='intermediate-value', style={'display': 'none'}),
        ], className="container")
    ], style={'padding-bottom': '20px'})

    #This is really what they suggest 
    #https://dash.plot.ly/sharing-data-between-callbacks
    @app.callback(Output("hist-stock-trend-graph", "figure"),
                  [Input('hist-trend-type-dropdown', 'value'),
                   Input('hist-trend-sym-dropdown', 'value'),
                   Input('hist-trend-count-dropdown', 'value'),
                   Input('hist-trend-projection-dropdown', 'value')],
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
        if args[2] != 'all':
            try:
                n = int(args[2])
            except ValueError:
                n = 8
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
        close_min = dash_data['close_min']    
        close_max = dash_data['close_max']    
        close_mean = dash_data['close_mean']  
        if run_pred:
            # Set plot data                                       
            dash_data['x_pred'].append(X[-1] + datetime.timedelta(days=1)) 
            while len(dash_data['x_pred']) > retension: dash_data['x_pred'].pop(0)

            for ml_type in dash_data['y_preds'].keys():
                if ml_type == '_all': continue
                # Requests latest prediction
                if ml_type == 'svm':
                    close_val = dash_data['closes'][-1]
                    post_feature = (norm_scale(close_val, close_mean, close_min, close_max),)
                    scaled_pred = ts_client.get_pred(post_feature, 'hist', ml_type, args[1].lower()).get('ScaledPrediction', 0)
                    pred = norm_descale(scaled_pred, close_mean, close_min, close_max)
                    if pred <= 0: continue
                    dash_data['y_preds'][ml_type].append(pred)
                else:
                    high_val, low_val, vol_val = dash_data['latest_feature']
                    high_min = dash_data['high_min']   
                    high_max = dash_data['high_max']   
                    high_mean = dash_data['high_mean'] 
                    low_min = dash_data['low_min']     
                    low_max = dash_data['low_max']     
                    low_mean = dash_data['low_mean']   
                    vol_min = dash_data['vol_min']     
                    vol_max = dash_data['vol_max']     
                    vol_mean = dash_data['vol_mean']   
                    high_scale = norm_scale(high_val, high_mean, high_min, high_max) 
                    low_scale = norm_scale(low_val, low_mean, low_min, low_max)      
                    vol_scale = norm_scale(vol_val, vol_mean, vol_min, vol_max)      
                    post_feature = (high_scale, low_scale, vol_scale)
                    scaled_pred = ts_client.get_pred(post_feature, 'hist', ml_type, args[1].lower()).get('ScaledPrediction', 0)
                    pred = norm_descale(scaled_pred, close_mean, close_min, close_max)
                    if pred <= 0: continue
                    dash_data['y_preds'][ml_type].append(pred)

                while len(dash_data['y_preds'][ml_type]) > retension: dash_data['y_preds'][ml_type].pop(0)

        pred_comb_val = combine_predictions(dash_data['y_preds'], dash_data['closes'][-1])
        dash_data['y_preds']['_all'] = [pred_comb_val]
        str_o = json.dumps({                                                
            'dateid': [dash_data['x_pred'][-1].strftime('%Y-%m-%d')], 
            'close': [pred_comb_val]                                        
        })                                                                  
        fname = './predictions/hist_{}.json'.format(args[1].lower())          
        with open(fname, 'w') as f:                                         
            f.write(str_o)                                                  

        project_x = []
        dash_data['projected'] = []
        for x in range(args[3]):
            if x == 0:
                close_val = pred_comb_val
            else:
                close_val = dash_data['y_preds']['projected'][-1]
            post_feature = (norm_scale(close_val, close_mean, close_min, close_max),)                                             
            scaled_pred = ts_client.get_pred(post_feature, 'hist', 'svm', args[1].lower()).get('ScaledPrediction', 0) 
            pred = norm_descale(scaled_pred, close_mean, close_min, close_max)                                                    
            project_x.append(dash_data['x_pred'][-1] + datetime.timedelta(days=(x+1)))
            dash_data['y_preds']['projected'].append(pred)

        # Drop junk values
        x_vals = []
        y_vals = []
        for x_val, y_val in zip(project_x, dash_data['y_preds']['projected']):
                if y_val <= 0: continue
                x_vals.append(x_val)
                y_vals.append(y_val)
        dash_data['y_preds']['projected'] = y_vals

        color_cycle = cycle(colors)
        if args[0] == 'close':
            for key, color in zip(key_order, color_cycle):
                if key == 'neur':
                    x_plot = dash_data['x_pred']
                    name = 'Neural Prediction'
                    mode = 'markers'
                elif key == 'svm':
                    x_plot = dash_data['x_pred']
                    name = 'SVM Prediction'
                    mode = 'markers'
                elif key == 'bay':
                    x_plot = dash_data['x_pred']
                    name = 'Bayesian Prediction'
                    mode = 'markers'
                elif key == '_all':
                    x_plot = dash_data['x_pred']
                    name = 'Combined Prediction'
                    mode = 'markers'
                elif key == 'projected':
                    x_plot = x_vals
                    name = 'Projected Prediction'
                    mode = 'line'
                else:
                    x_plot = dash_data['x_pred']
                    name = 'Unknown Prediction'
                    mode = 'markers'

                data_list.append({
                    'x': x_plot,
                    'y': dash_data['y_preds'][key],
                    'name': name,
                    'mode': mode,
                    'marker': {
                        'size': 10,
                        'line': {'width': 2},
                        'color': color
                    }
                })

        return {
            'data': data_list,
            'layout': go.Layout(
                autosize=True,
                margin=go.Margin(l=50, r=50, b=50, t=50, pad=10)
            )
        }

    @app.callback(Output('hist-guessing-score', 'children'),                                          
                  [Input('hist-guess-slider', 'value')],
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
                update_score(1, 50)                                                                      
                glyph = plus_glyph                                                                      
                dash_data['last_glyph'] = glyph
            elif (guess == 2 and diff < 0) or (guess == 0 and diff > 0):    
                update_score(1, -50)                                                                      
                glyph = minus_glyph                                                                     
                dash_data['last_glyph'] = glyph
            else:
                glyph = hourglass_glyph                                                                         
                dash_data['last_glyph'] = glyph
        current_score = 'Current Score: {} '.format(get_score(1, 1))                                     
        return html.Div([current_score, glyph])                                              

    @app.callback(Output('hist-quick-info', 'children'),
                  [Input('hist-trend-sym-dropdown', 'value')],
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
        SELECT stock_price_minute.sym AS "Company", close AS "{}"
        FROM stock_price_minute

        JOIN (
          SELECT sym, MAX(dateid) as mdate
          FROM stock_price_minute
          GROUP BY sym
        ) as sub
          ON stock_price_minute.dateid = sub.mdate AND stock_price_minute.sym = sub.sym
        ORDER BY dateid DESC, stock_price_minute.sym ASC
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
            display_val = '  ${0:.2f}'.format(dash_data['y_preds']['_all'][-1])
            display_val = '  ${0:.2f}'.format(dash_data['y_preds']['_all'][-1])

        # Buy sell summary
        pred_list = [html.H3("Predicted Value")]
        if len(dash_data['y_preds']['_all']) <= 0:
            pred_list.append(html.Img(   
                src=load_img_url,         
                style={'height': '50px'} 
            ))                           
        elif dash_data['y_preds']['_all'][-1] > dash_data['closes'][-1]:
            pred_list.append(html.Img(
                src=buy_img_url,
                style={'height': '50px'}
            ))
        else:
            pred_list.append(html.Img(
                src=sell_img_url,
                style={'height': '50px'}
            ))
        pred_list.append(display_val)
        pred_data = html.Div(pred_list)

        return [pred_data, qh1, sym_table, qh2, max_table, qh3, avg_table, qh4,
                low_table, qh5, avglow_table]
