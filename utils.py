# written by: Kevin Pielacki
# debugged by: Kevin Pielacki


from config import (TENSOR_HOST, TENSOR_PORT)
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

    root_url = 'http://{}:{}'.format(TENSOR_HOST, TENSOR_PORT)

    resource = 'inference'

    timeout = 0.4

    def get_pred(self, data, freq, ml_type, sym):
        url = '/'.join((self.root_url, self.resource, freq, ml_type, sym))
        try:
            r = requests.post(
                url,
                data=json.dumps(data),
                headers=self.headers,
                timeout=self.timeout
            )
        except:
            return {}
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
