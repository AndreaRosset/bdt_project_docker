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
import plotly.express as px
from plotly import tools
import psycopg2 # python package for Postgres

conn = psycopg2.connect(host="postgresql", dbname="btc_sp500_stocks", user="postgres", password="postgres") #postgres connector
sql = """SELECT * FROM btc_sp500_stocks"""
cur = conn.cursor()
cur.execute(sql)
data = cur.fetchall()
reduced_df = pd.DataFrame(data)
#print(reduced_df)
reduced_df.columns = ["t_time", "BTC", "SP500"] #Databse

for index, value in enumerate(reduced_df["t_time"]):
    reduced_df["t_time"][index] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
    
reduced_df = reduced_df.iloc[1:]
print(reduced_df)

# Computing Moving Averages (the only one needed next is the BTC Moving Average)
reduced_df["MA_100"] = reduced_df["SP500"].rolling(100,min_periods=10).mean().shift(1) #9 giorni
reduced_df["MA_200"] = reduced_df["SP500"].rolling(200,min_periods=10).mean().shift(1) #21 giorni

reduced_df["MAB_100"] = reduced_df["BTC"].rolling(100,min_periods=10).mean().shift()
reduced_df["MAB_200"] = reduced_df["BTC"].rolling(200,min_periods=10).mean().shift()

x = reduced_df.corr() # Matrix Correlation
print(x)
correl = round(x["SP500"][0],4) # Correlation between BTC and S&P 500
correl



# Create traces moving averages - Optional visualizations
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


# COMPUTATION: Imposing conditions on Correlation and Trend by comparing the BTC Moving Average and BTC Real Trend
results = {}

if correl == 1: # both increase/decrease in the same proportion  : perfect positive correlation
    if reduced_df["MAB_100"].iloc[-1] < reduced_df["BTC"].iloc[-1]: # rising btc price
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl,"act":"Long"}) # Buy for sell later at a higher price
    else: # decreasing btc price
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl,"act":"Short"}) # Sell for buy later at a lower price

elif 0 < correl < 1: # both increase/decrease but not in the same proportion : positive correlation
    if reduced_df["MAB_100"].iloc[-1] < reduced_df["BTC"].iloc[-1]: # rising btc price
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl,"act":"Long"})
    else: # decreasing btc price
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl, "act":"Short"}) # 
        
elif correl -1 < correl < 0: # Opposite trend between BTC and S&P 500 but not in the same proportion : negative correlation
    if reduced_df["MAB_100"].iloc[-1] < reduced_df["BTC"].iloc[-1]: # BTC increases (sp500 decreases)
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl, "act":"Long"})
    else: # BTC decreases (sp500 increases)
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl, "act":"Short"})
        
elif correl == -1: # Opposite trend between BTC and S&P 500 : perfect negative correlation
    if reduced_df["MAB_100"].iloc[-1] < reduced_df["BTC"].iloc[-1]: # BTC increases (sp500 decreases)
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl, "act":"Long"})
    else: # BTC decreases (sp500 increases)
        results=({"date":reduced_df["t_time"].iloc[-1],"correl":correl, "act":"Short"})

elif correl == 0: # No correlation
    results=({"date":reduced_df["t_time"].iloc[-1],"correl":"no correlation", "act":"None"})
else:
    results=({"date":"Error","correl":"Error", "act":"Error"})

import plotly.graph_objects as go


# Creating figures for the Dash

# fig: S&P 500 and BTC are displayed together in a unique graph, so it is needed a second y-axis 
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
            color="orange" 
        ),showgrid = False,showspikes= True,spikedash= 'dot',spikemode= 'across',spikesnap= 'cursor',
        tickfont=dict(
            color="orange"
        )
    ),
    yaxis2=dict(
        title="BTC Price",
        titlefont=dict(
            color="#00FE35" 
        ),
        tickfont=dict(
            color="#00FE35"
        ),showgrid = False,showspikes= True,spikedash= 'dot',spikemode= 'across',spikesnap= 'cursor',
        anchor="x",
        overlaying="y",
        side="right",
    ),

)

# Update layout properties of fig
fig.update_layout(title_text="S&P 500 and BTC Prices", plot_bgcolor='rgb(10,10,10)',paper_bgcolor='black',
                 font=dict(
                    color = 'yellow',
                     size=18
                 )
                 )


# fig1: displaying BTC
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['BTC'],mode='lines',name='BTC',
                          line=dict(color='#00FE35'),))
                          
              
# Updating fig1 (btc) layout
fig1.update_layout(plot_bgcolor='rgb(10,10,10)',paper_bgcolor='black', clickmode= 'event+select',
                   xaxis=dict(title='Time', titlefont=dict(color='yellow',size=12),
                              showspikes= True, color='yellow',showgrid = False,
                              spikedash= 'dot',spikemode= 'across',spikesnap= 'cursor'),
                              
                  yaxis=dict(title='Price',titlefont=dict(color='yellow',size=12),
                            showspikes= True,color='yellow', showgrid = False,
                            spikedash= 'dot',spikemode= 'across',spikesnap= 'cursor'),
                  title='BTC Price', titlefont=dict(color='#00FE35',size=18))



# fig2: displaying S&P 500
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['SP500'],mode='lines',name='BTC',
                          line=dict(color='orange'),))
                          
              
# Updating fig2 (sp500) layout
fig2.update_layout(plot_bgcolor='rgb(10,10,10)',paper_bgcolor='black', clickmode= 'event+select',
                   xaxis=dict(title='Time', titlefont=dict(color='yellow',size=12),
                              showspikes= True,color='yellow',showgrid = False,
                              spikedash= 'dot',spikemode= 'across',spikesnap= 'cursor'),
                              
                  yaxis=dict(title='Price',titlefont=dict(color='yellow',size=12),
                            showspikes= True,color='yellow',showgrid = False,
                            spikedash= 'dot',spikemode= 'across',spikesnap= 'cursor'),
                  title='S&P 500 Price', titlefont=dict(color='orange',size=18))


# RESULTS
# Creating the Plotly Dash for visualize results of conditions imposed on correlation and graphs

import flask

app = dash.Dash()
app.layout = html.Div()


all_options = {
    'DateTime': [results["date"]],
    'Correlation': [results['correl']],
    'Act': [results['act']]
}


app.layout = html.Div(children=[
    html.Div(className='row',  # Define the row element
                            style={
                                      'textAlign': 'center',
                                      "background": "DimGray", 
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
                        
                        html.Div([ # Define RadioItems 
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
                                   
    # Define Dropdown
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
    
    # Define (space for) graph
    html.Div(className='graph',children=[
                dcc.Graph(id='timeseries')
    ])
])
])      

# Making Dashboard Interactive using callbacks

# Callback for visualize graphs one at time       
@app.callback(
    dash.dependencies.Output('timeseries', 'figure'),
    [dash.dependencies.Input('drop-indicator-px', 'value')])   
def up_image(selector): 
   
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
    
    
# Two callback for RadioItems results and options
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
    
# use_reloader = False since we used Jupyter
