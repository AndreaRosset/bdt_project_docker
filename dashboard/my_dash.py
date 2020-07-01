import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import time
import matplotlib.ticker as ticker
import csv
from collections import OrderedDict
#%matplotlib inline
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table

from dash.exceptions import PreventUpdate
import multiprocessing
import plotly.express as px
import plotly.offline as pyo
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly import tools
import psycopg2

conn = psycopg2.connect(host="postgresql", dbname="btc_sp500_stocks", user="postgres", password="postgres")
sql = """SELECT * FROM btc_sp500_stocks"""
cur = conn.cursor()
cur.execute(sql)
data = cur.fetchall()
reduced_df = pd.DataFrame(data)
#print(reduced_df)
reduced_df.columns = ["t_time", "BTC", "SP500"]

for index, value in enumerate(reduced_df["t_time"]):
    reduced_df["t_time"][index] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
    
reduced_df = reduced_df.iloc[1:]
print(reduced_df)

reduced_df["MA_100"] = reduced_df["SP500"].rolling(100,min_periods=10).mean().shift(1) #9 giorni
reduced_df["MA_200"] = reduced_df["SP500"].rolling(200,min_periods=10).mean().shift(1) #21 giorni

reduced_df["MAB_100"] = reduced_df["BTC"].rolling(100,min_periods=10).mean().shift()
reduced_df["MAB_200"] = reduced_df["BTC"].rolling(200,min_periods=10).mean().shift()

x = reduced_df.corr()
print(x)
correl = round(x["SP500"][0],4)
correl

import plotly.express as px

# Create traces moving averages
#masp500 = go.Figure()
#masp500.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['SP500'], mode='lines', name='S&P 500'))
#masp500.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['MA_100'], mode='lines', name='MA 100 records'))
#masp500.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['MA_200'], mode='lines', name='MA 200 records'))
#masp500.update_layout(title='S&P Moving Averages', xaxis_title='Time',)

#mabtc = go.Figure()
#mabtc.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['BTC'],mode='lines',name='BTC'))
#mabtc.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['MAB_100'], mode='lines', name='MAB 100 records'))
#mabtc.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['MAB_200'], mode='lines', name='MAB 200 records'))
#mabtc.update_layout(title='BTC Moving Averages', xaxis_title='Time',)




#masp500.show()
#mabtc.show()

results = {}

if correl == 1: #entrambi salgono/scendono : perfetta corr positiva
    if reduced_df["MAB_100"].iloc[-1] < reduced_df["BTC"].iloc[-1]: #se btc sale
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl,"act":"strong long", "type":"aggressive"}) #prezzi a rialzo
    else: # se btc scende mi devo difendere
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl,"act":"short", "type":"defensive"}) #prezzi a ribasso

elif 0 < correl < 1: #entrambi salgono o scendono  ma la corr è più bassa
    if reduced_df["MAB_100"].iloc[-1] < reduced_df["BTC"].iloc[-1]: # prezzi btc lenti a rialzo
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl,"act":"Long","type": "neutral"})
    else: #prezzi btc lenti a ribasso
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl, "act":"short","type": "neutral"}) #prezzi lenti a ribasso
        
elif correl -1 < correl < 0: #uno sale e uno scende con corr bassa 
    if reduced_df["MAB_100"].iloc[-1] < reduced_df["BTC"].iloc[-1]: # BTC sale (sp scende)
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl, "act":"long","type": "neutral"})
    else: # BTC scende (sp sale)
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl, "act":"short", "type":"neutral"})
        
elif correl == -1: # uno sale e uno scende : perfetta corr negativa
    if reduced_df["MAB_100"].iloc[-1] < reduced_df["BTC"].iloc[-1]: #se btc sale (sp500 scende)
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl, "act":"strong long","type": "aggressive"})
    else: # se btc scende (sp500 sale)
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl, "act":"long", "type":"defensive"})

elif correl == 0: #x=0
    results=({"date":reduced_df["t_time"].iloc[-1],"correl":"no correlation", "act":"non", "type":"non"})
else:
    results=({"date":"error","correl":"error", "act":"error", "type":"error"})

import plotly.graph_objects as go

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=reduced_df["t_time"],
    y=reduced_df['SP500'],
    name="S&P 500",
    line=dict(color='orange')
))


fig.add_trace(go.Scatter(
    x=reduced_df["t_time"],
    y=reduced_df['BTC'],
    name="BTC",
    line=dict(color='#00FE35'),
    yaxis="y2"
))

# Create axis objects
fig.update_layout(
    xaxis=dict(
    title='Time',
    titlefont=dict(
    color='yellow',size=12),
    showgrid = False, showspikes= True,spikedash= 'dot',spikemode= 'across',spikesnap= 'cursor',
    ),
    
    yaxis=dict(
        title="S&P 500 Price",
        titlefont=dict(
            color="orange" ##1f77b4
        ),showgrid = False,showspikes= True,spikedash= 'dot',spikemode= 'across',spikesnap= 'cursor',
        tickfont=dict(
            color="orange"
        )
    ),
    yaxis2=dict(
        title="BTC Price",
        titlefont=dict(
            color="#00FE35" ##ff7f0e
        ),
        tickfont=dict(
            color="#00FE35"
        ),showgrid = False,showspikes= True,spikedash= 'dot',spikemode= 'across',spikesnap= 'cursor',
        anchor="x",
        overlaying="y",
        side="right",
        #position=0.15
    ),

)

# Update layout properties
fig.update_layout(title_text="S&P 500 and BTC Prices", plot_bgcolor='rgb(10,10,10)',paper_bgcolor='black',
                 font=dict(
                    color = 'yellow',
                     size=18
                 )
                 ),


fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['BTC'],mode='lines',name='BTC',
                          line=dict(color='#00FE35'),))
                          
              

fig1.update_layout(plot_bgcolor='rgb(10,10,10)',paper_bgcolor='black', clickmode= 'event+select',
                   xaxis=dict(title='Time', titlefont=dict(color='yellow',size=12),
                              showspikes= True, color='yellow',showgrid = False,
                              spikedash= 'dot',spikemode= 'across',spikesnap= 'cursor'),
                              
                  yaxis=dict(title='Price',titlefont=dict(color='yellow',size=12),
                            showspikes= True,color='yellow', showgrid = False,
                            spikedash= 'dot',spikemode= 'across',spikesnap= 'cursor'),
                  title='BTC Price', titlefont=dict(color='#00FE35',size=18))



fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['SP500'],mode='lines',name='BTC',
                          line=dict(color='orange'),))
                          
              

fig2.update_layout(plot_bgcolor='rgb(10,10,10)',paper_bgcolor='black', clickmode= 'event+select',
                   xaxis=dict(title='Time', titlefont=dict(color='yellow',size=12),
                              showspikes= True,color='yellow',showgrid = False,
                              spikedash= 'dot',spikemode= 'across',spikesnap= 'cursor'),
                              
                  yaxis=dict(title='Price',titlefont=dict(color='yellow',size=12),
                            showspikes= True,color='yellow',showgrid = False,
                            spikedash= 'dot',spikemode= 'across',spikesnap= 'cursor'),
                  title='S&P 500 Price', titlefont=dict(color='orange',size=18))


import flask

#from jupyterlab_dash import AppViewer
#viewer = AppViewer()

#server = flask.Flask(__name__) # define flask app.server
#app = dash.Dash(__name__, server=server) # call flask server
#gunicorn my_dash:app.server -b :8000
app = dash.Dash()
app.layout = html.Div()




all_options = {
    'DateTime': [results["date"]],
    'Correlation': [results['correl']],
    'Act': [results['act']],
    'Type': [results['type']]
}


app.layout = html.Div(children=[
    html.Div(className='row',  # Define the row element
                            style={
                                      'textAlign': 'center',
                                      "background": "DimGray", #DimGray
                                      'fontWeight': 'bold',
                                       'color': 'black'},
                               
                               children=[
                                      html.Div(className='Suggestion',
                                           
                               children= [  
                                      html.H1('Position on Bitcoin'),
                                      html.H2('Our suggestion is to stay:'),
                                      html.H3(results["act"]),
                                   ]),
                        html.Hr(),
                        
                        html.Div([
                                dcc.RadioItems(
                                id='results-dropdown',
                                    style={'marginTop': 0, 'marginBottom': 0},
                                    options =[{'label':k, 'value':k} for k in all_options.keys()],
                                value = 'DateTime'
                            ),
                        html.Hr(),
                            dcc.RadioItems(id='opt-dropdown'),
                        html.Hr(),
                            html.Div(id='display-selected-values')
                        ]),
                                   

    html.Div(className='drop-dwn',children=[
        dcc.Dropdown(id='drop-indicator-px',
                multi = False,
                options = [
                    {'label':'BTC', 'value':'btc'},
                    {'label':'S&P 500','value': 'sp500'},
                    {'label':'BOTH', 'value': 'both'}
                ],#value=['btc','sp500','both'],
                placeholder='Select graph'),
    ]),
    
    html.Div(className='graph',children=[
                dcc.Graph(id='timeseries')
    ])
])
])      

                
@app.callback(
    dash.dependencies.Output('timeseries', 'figure'),
    [dash.dependencies.Input('drop-indicator-px', 'value')])   
def up_image(selector):
    #data=[]
    #figure=go.Figure()
   
    try:

        if 'sp500'in selector:
            figure=fig2
        
        
        elif 'btc'in selector :
            figure=fig1
  
        else:
            #'both' in selector:
            figure=fig
            
    except TypeError: 
        return fig
   
        
    return figure
    
    
    
@app.callback(
    dash.dependencies.Output('opt-dropdown', 'options'),
    [dash.dependencies.Input('results-dropdown', 'value')])
def set_results_options(selected_results):
    return [{'label': i, 'value': i} for i in all_options[selected_results]]


@app.callback(
    dash.dependencies.Output('opt-dropdown', 'value'),
    [dash.dependencies.Input('opt-dropdown', 'options')])
def set_results_value(available_options):
    return available_options[0]['value']

    
    
    
if __name__ == "__main__" :
    app.run_server(debug=True, use_reloader=False, host="0.0.0.0")         
    
#viewer.show(app)
