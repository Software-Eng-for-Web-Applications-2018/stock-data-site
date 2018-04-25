# written by: Kevin Pielacki
# debugged by: Kevin Pielacki


from config import TENSOR_HOST
import dash_html_components as html
import json
import requests


def generate_table(dataframe, max_rows=10):
    '''Example code from Plotly Dash documentation for DataFrame to html table.

    args:
        dataframe (DataFrame): Pandas DataFrame to convert to HTML table

    returns:
        DCC Table: HTML table of DataFrame
    '''
    return html.Table(
        [html.Tr([html.Th(col, style={'width': '100px'}) for col in dataframe.columns])] +
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))],
        className='table table-striped'
    )


class PredictionRequest(object):

    headers = {
        'postman-token': '1b4663d0-fc47-007a-673d-721ebad9985e',
        'cache-control': 'no-cache',
        'content-type': 'application/json'
    }

    root_url = 'http://{}:'.format(TENSOR_HOST)

    resource = '/inference'

    sym_port_map = {
        'rt': {
            'neur': {
                'aaba': '9000',
                'aapl': '9001',
                'amd': '9002',
                'amzn': '9003',
                'c': '9004',
                'goog': '9005',
                'googl': '9006',
                'intc': '9007',
                'msft': '9008',
                'vz': '9009'
            }, 'svm': {            
                'aaba': '9020',  
                'aapl': '9021',  
                'amd': '9022',   
                'amzn': '9023',  
                'c': '9024',     
                'goog': '9025',  
                'googl': '9026', 
                'intc': '9027',  
                'msft': '9028',  
                'vz': '9029'     
            }                    
        }, 'hist': {
            'neur': {
                'aaba': '9010',
                'aapl': '9011',
                'amd': '9012',
                'amzn': '9013',
                'c': '9014',
                'goog': '9015',
                'googl': '9016',
                'intc': '9017',
                'msft': '9018',
                'vz': '9019'
            }, 'svm': {             
                'aaba': '9030',     
                'aapl': '9031',     
                'amd': '9032',      
                'amzn': '9033',     
                'c': '9034',        
                'goog': '9035',     
                'googl': '9036',    
                'intc': '9037',     
                'msft': '9038',     
                'vz': '9039'        
            }                       
        }
    }

    def get_pred(self, data, freq, ml_type, sym):
        try:
            port = self.sym_port_map[freq][ml_type][sym]
        except:
            return {}
        print(port)
        url = self.root_url + port + self.resource
        print(url)
        r = requests.post(url, data=json.dumps(data), headers=self.headers)
        if r.status_code != 200:
            return {}

        return r.json()


plus_glyph = html.Span(
    className='glyphicon glyphicon-ok',
    style={'color': 'green'}
)
hourglass_glyph = html.Span(                    
    className='glyphicon glyphicon-hourglass',  
    style={'color': 'orange'}                  
)                                           
minus_glyph = html.Span(                 
    className='glyphicon glyphicon-minus', 
    style={'color': 'red'}            
)                                       
