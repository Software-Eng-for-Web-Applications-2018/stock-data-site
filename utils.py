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

    url = 'http://{}:{}/inference'.format(TENSOR_HOST, TENSOR_PORT)

    def get_pred(self, data):
        r = requests.post(self.url, data=json.dumps(data), headers=self.headers)
        if r.status_code != 200:
            return {}

        return r.json()
