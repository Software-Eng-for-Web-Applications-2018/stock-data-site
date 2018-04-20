# written by: Kevin Pielacki
# debugged by: Kevin Pielacki


import dash_html_components as html


def generate_table(dataframe, max_rows=10):
    '''Example code from Plotly Dash documentation for DataFrame to html table.

    args:
        dataframe (DataFrame): Pandas DataFrame to convert to HTML table

    returns:
        DCC Table: HTML table of DataFrame
    '''
    return html.Table(
        [html.Tr([html.Th(col) for col in dataframe.columns])] +
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))],
        className='table table-striped'
    )
