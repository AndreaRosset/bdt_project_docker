# Importing necessary Packages
import pandas as pd
import numpy as np
import time
import matplotlib.ticker as ticker
from collections import OrderedDict

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import plotly.express as px
import plotly.offline as pyo
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from plotly import tools
import plotly.graph_objects as go

import psycopg2 # python package for Postgres


conn = psycopg2.connect(host="172.20.0.2", dbname="btc_sp500_stocks", user="postgres", password="postgres") #Postgres Connector

sql = """SELECT * FROM btc_sp500_stocks ORDER BY t_time DESC LIMIT 7000""" # Creating Table

cur = conn.cursor()

def dataframe_update(cur, sql):
	cur.execute(sql)
	data = cur.fetchall()
	return pd.DataFrame(data)

reduced_df = dataframe_update(cur, sql) # reduced_df contains BTC and S&P 500 prices

def calc_correl(reduced_df):
	#print(reduced_df)
	reduced_df.columns = ["t_time", "BTC", "SP500"] #rename columns 
	for index, value in enumerate(reduced_df["t_time"]):
		reduced_df["t_time"][index] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value)) # Converting Date & Time in the correct format
     
	reduced_df = reduced_df.iloc[1:] # Dropping first row since price is zero for S&p 500
	#print(reduced_df)


	# Computing Moving Averages using a window of 100 reocords and a window of 200 records. Both window  are a fixed size.
	# The first value will be computed when there are at least 10 records in the moving window, otherwise it will get NA

	# S&P 500 Moving Averages
	# reduced_df["MA_100"] = reduced_df["SP500"].rolling(500,min_periods=10).mean().shift(1) # Size of the moving window = 100 
	# reduced_df["MA_200"] = reduced_df["SP500"].rolling(200,min_periods=10).mean().shift(1) # Size of the moving window = 200 

	# BTC Moving Averages
	reduced_df["MAB_500"] = reduced_df["BTC"].rolling(500,min_periods=500).mean().shift() # Size of the moving window = 100 
	reduced_df["MAB_200"] = reduced_df["BTC"].rolling(200,min_periods=200).mean().shift() # Size of the moving window = 200 

	# We will use the BTC moving average with 100 records since it seems to be closer to the BTC trend (look at optional visualizations here below)

	x = reduced_df.corr() # Matrix correlation
	#print(x)
	correl = round(x["SP500"][0],4) # Extracting the value of correlation between BTC and S&P 500 from the x matrix
	return (correl, reduced_df)


# Create traces moving averages - Optional visualizations
#masp500 = go.Figure()
#masp500.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['SP500'], mode='lines', name='S&P 500'))
#masp500.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['MA_100'], mode='lines', name='MA 100 records'))
#masp500.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['MA_200'], mode='lines', name='MA 200 records'))S
#masp500.update_layout(title='S&P Moving Averages', xaxis_title='Time',)

def print_graph(reduced_df):
	mabtc = go.Figure()
	mabtc.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['BTC'],mode='lines',name='BTC'))
	mabtc.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['MAB_500'], mode='lines', name='MAB 500 records'))
	mabtc.add_trace(go.Scatter(x=reduced_df['t_time'], y=reduced_df['MAB_200'], mode='lines', name='MAB 200 records'))
	mabtc.update_layout(title='BTC Moving Averages', xaxis_title='Time',)

	#masp500.show()
	mabtc.show()

# COMPUTATION: we now impose some conditions on the entity of correlation and on the BTC price to be sure to capture the right trend.
# These conditions try to respect the Short selling strategy. 

def calc_results(reduced_df, correl):

	#print(correl)
	
	results = {}

	if correl == 1: # BTC and S&P 500 both increase/decrease in the same proportion : perfect positive correlation
		if reduced_df["MAB_500"].iloc[1] < reduced_df["BTC"].iloc[1]: # BTC price increases (and also S&P 500)
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl,"act":"Long"}) # Buy to sell later at a higher price
		else: # BTC price decreases (and also S&P 500)
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl,"act":"Short"}) # Sell to buy later at a lower price

	elif 0 < correl < 1: # BTC and S&P 500 both increase/decrease but not in the same proportion : still positive correlation
		if reduced_df["MAB_500"].iloc[1] < reduced_df["BTC"].iloc[1]: # BTC price increases 
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl,"act":"Long"})

		else: # BTC price decreases (and also S&P 500)
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl, "act":"Short"}) # Sell to buy later at a lower price
        
	elif -1 < correl < 0: # Opposite direction: negative correlation
		if reduced_df["MAB_500"].iloc[1] < reduced_df["BTC"].iloc[1]: # BTC price increases (S&P 500 decreases )
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl, "act":"Long"}) # Buy to sell later at a higher price

		else: # BTC price decreases (S&P 500 increases)
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl, "act":"Short"}) # Sell to buy later at a lower price
        
	elif correl == -1: # Opposite direction: perfect negative correlation
		if reduced_df["MAB_500"].iloc[1] < reduced_df["BTC"].iloc[1]: # # BTC price increases (S&P 500 decreases)
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl, "act":"Long"}) # Buy to sell later at a higher price
		else: # BTC price decreases (S&P 500 price increases)
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl, "act":"Long"}) # Sell to buy later at a lower price

	elif correl == 0: # Correlation = 0
		results=({"date":reduced_df["t_time"].iloc[1],"correl":"No correlation", "act":"None"})
	else: # Some Error
		results=({"date":"Error","correl":"Error", "act":"Error"})
    	
	return results
	

c = calc_correl(reduced_df)
correl = c[0]
reduced_df = c[1]

results = calc_results(reduced_df, correl)
print_graph(reduced_df)



# Create figures for the Dash


def create_figure_btc_sp500(reduced_df): # Displaying BTC and S&P500 in the same plot with double y-axis for a fast comparison

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
		),

	)

	# Update layout properties for fig
	fig.update_layout(title_text="S&P 500 and BTC Prices", plot_bgcolor='rgb(10,10,10)',paper_bgcolor='black',font=dict( color = 'yellow', size=18))
	return fig
	
fig = create_figure_btc_sp500(reduced_df)



def create_figure_btc(reduced_df): # Displaying BTC prices (fig1)

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
	return fig1
	
fig1 = create_figure_btc(reduced_df)

def create_figure_sp500(reduced_df): # Displaying S&P 500 prices (fig2)

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
	return fig2
	
fig2 = create_figure_sp500(reduced_df)



# Creating Plotly Dash for visualize results and position to take on Bitcoin 

app = dash.Dash()
app.layout = html.Div()

def calc_options(results):
	return {
    	'DateTime': [results["date"]],
    	'Correlation': [results['correl']],
		'Position': [results['act']],
	}
	
all_options = calc_options(results)

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
                                      html.H1('Results and Position on Bitcoin'),
                                   ]),
                        html.Hr(),
                        
                        html.Div([ # Define RadioItems for results (DateTime, Correlation and Position)
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
                                   
    # Define Dropdown for graphs
    html.Div(className='drop-dwn',children=[
        dcc.Dropdown(id='drop-indicator-px',
                multi = False,
                options = [
                    {'label':'BTC', 'value':'btc'},
                    {'label':'S&P 500','value': 'sp500'},
                    {'label':'BOTH', 'value': 'both'}
                ],#value=['btc','sp500','both'],
                value='both',
				clearable=False,),
    ]),
    
    # Define (space for) graph
    html.Div(className='graph',children=[
                dcc.Graph(id='timeseries')
    ])
])
])      

# Making Dashboard Interactive using callbacks and updating Results

# Callback for visualize graphs one at time. It is possible to choose which chart to see. 
@app.callback(
    dash.dependencies.Output('timeseries', 'figure'),
    [dash.dependencies.Input('drop-indicator-px', 'value')])   
def up_image(selector): 
   
	try:

		if 'sp500'in selector:
			reduced_df = dataframe_update(cur, sql)
			c = calc_correl(reduced_df)
			correl = c[0]
			reduced_df = c[1]
			results = calc_results(reduced_df, correl)
			all_options = calc_options(results)
			figure = create_figure_sp500(reduced_df)
			
        
		elif 'btc'in selector :
			reduced_df = dataframe_update(cur, sql)
			c = calc_correl(reduced_df)
			correl = c[0]
			reduced_df = c[1]
			results = calc_results(reduced_df, correl)
			all_options = calc_options(results)
			figure = create_figure_btc(reduced_df)
  
		else:
            #'both' in selector:
			reduced_df = dataframe_update(cur, sql)
			c = calc_correl(reduced_df)
			correl = c[0]
			reduced_df = c[1]
			results = calc_results(reduced_df, correl)
			all_options = calc_options(results)
			figure = create_figure_btc_sp500(reduced_df)
            
	except TypeError: 
		return fig
   
        
	return figure
    
    
# Two callback for RadioItems results and options
@app.callback(
	dash.dependencies.Output('opt-dropdown', 'options'),
	[dash.dependencies.Input('results-dropdown', 'value')])
def set_results_options(selected_results):
	reduced_df = dataframe_update(cur, sql)
	c = calc_correl(reduced_df)
	correl = c[0]
	reduced_df = c[1]
	results = calc_results(reduced_df, correl)	
	all_options = calc_options(results)
	return [{'label': i, 'value': i} for i in all_options[selected_results]]


@app.callback(
	dash.dependencies.Output('opt-dropdown', 'value'),
	[dash.dependencies.Input('opt-dropdown', 'options')])
def set_results_value(available_options):
	return available_options[0]['value']

    
    
    
if __name__ == "__main__" :
	app.run_server(debug=False, use_reloader=False, host="0.0.0.0")         

# use_reloader = False since we used Jupyter
