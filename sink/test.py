import pandas as pd
import numpy as np
import psycopg2
import time

pockets = 1000		   # in USD
invested = 0			# in BTC
debt = 0				# in BTC
investing_long = False
investing_short = False
last_trans = 0

conn = psycopg2.connect(host="postgresql", dbname="btc_sp500_stocks", user="postgres", password="postgres") #Postgres Connector

sql = """SELECT * FROM btc_sp500_stocks ORDER BY t_time DESC LIMIT 502"""

cur = conn.cursor()

def dataframe_update():
	global cur
	global sql
	cur.execute(sql)
	data = cur.fetchall()
	return pd.DataFrame(data)

def buy_long(correl, reduced_df):					# open a long position
	global pockets
	global invested
	global investing_long
	global investing_short

	if not investing_long and not investing_short:
		pockets -= 750 * abs(correl)
		invested = 750 * abs(correl) / reduced_df["BTC"].iloc[1]
		investing_long = True
		print("buy_long")

def sell_long(correl, reduced_df):					# close a long position
	global pockets
	global invested
	global investing_long
	global last_trans

	if investing_long:
		pockets += invested * reduced_df["BTC"].iloc[1]
		last_trans = pockets
		invested = 0
		investing_long = False
		print("sell_long")
		print("$$$$$$$$$$$$$$$$$$$$$")
		print("$ " + str(last_trans) + " $")
		print("$$$$$$$$$$$$$$$$$$$$$")

# in short we want to buy later at a lower price

def sell_short(correl, reduced_df):					# open a short position
	global pockets
	global investing_long
	global investing_short
	global debt

	if not investing_long and not investing_short:
		pockets += 750 * abs(correl)
		debt = 750 * abs(correl) / reduced_df["BTC"].iloc[1]
		investing_short = True
		print("sell_short")

def buy_short(correl, reduced_df):					# close a short position
	global pockets
	global investing_short
	global debt
	global last_trans

	if investing_short:
		pockets -= debt * reduced_df["BTC"].iloc[1]
		last_trans = pockets
		debt = 0
		investing_short = False
		print("buy_short")
		print("$$$$$$$$$$$$$$$$$$$$$")
		print("$ " + str(last_trans) + " $")
		print("$$$$$$$$$$$$$$$$$$$$$")



def calc_results(reduced_df, correl):
	
	results = {}

	if correl == 1: # BTC and S&P 500 both increase/decrease in the same proportion : perfect positive correlation
		if reduced_df["MAB_500"].iloc[1] < reduced_df["BTC"].iloc[1]: # BTC price increases (and also S&P 500)
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl,"act":"Long"}) # Buy to sell later at a higher price
		else: # BTC price decreases (and also S&P 500)
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl,"act":"Short"}) # Sell to buy later at a lower price

	elif 0 < correl < 1: # BTC and S&P 500 both increase/decrease but not in the same proportion : still positive correlation
		if reduced_df["MAB_500"].iloc[1] < reduced_df["BTC"].iloc[1]: # BTC price increases 
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl,"act":"Long"})

			if(investing_short):
				buy_short(correl, reduced_df)
			if(correl >= 0.35):
				buy_long(correl, reduced_df)

		else: # BTC price decreases (and also S&P 500)
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl, "act":"Short"}) # Sell to buy later at a lower price

			if(investing_long):
				sell_long(correl, reduced_df)
			if(correl >= 0.35):
				sell_short(correl, reduced_df)

	elif -1 < correl < 0: # Opposite direction: negative correlation
		if reduced_df["MAB_500"].iloc[1] < reduced_df["BTC"].iloc[1]: # BTC price increases (S&P 500 decreases )
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl, "act":"Long"}) # Buy to sell later at a higher price

			if(investing_short):
				buy_short(correl, reduced_df)
			if(correl <= -0.35):
				buy_long(correl, reduced_df)

		else: # BTC price decreases (S&P 500 increases)
			results=({"date":reduced_df["t_time"].iloc[1],"correl":correl, "act":"Short"}) # Sell to buy later at a lower price

			if(investing_long):
				sell_long(correl, reduced_df)
			if(correl <= -0.35):
				sell_short(correl, reduced_df)

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


def calc_correl(reduced_df):
	reduced_df.columns = ["t_time", "BTC", "SP500"] #rename columns 
	for index, value in enumerate(reduced_df["t_time"]):
		reduced_df["t_time"][index] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value)) # Converting Date & Time in the correct format

	reduced_df = reduced_df.iloc[1:] # Dropping first row since price is zero for S&p 500
	#print(reduced_df)


	# Computing Moving Averages using a window of 100 reocords and a window of 200 records. Both window  are a fixed size.
	# The first value will be computed when there are at least 10 records in the moving window, otherwise it will get NA

	# S&P 500 Moving Averages
	# reduced_df["MA_500"] = reduced_df["SP500"].rolling(500,min_periods=500).mean().shift(1) # Size of the moving window = 100 
	# reduced_df["MA_200"] = reduced_df["SP500"].rolling(200,min_periods=10).mean().shift(1) # Size of the moving window = 200 

	# BTC Moving Averages
	reduced_df["MAB_500"] = reduced_df["BTC"].rolling(500,min_periods=500).mean().shift(1) # Size of the moving window = 100 
	# reduced_df["MAB_200"] = reduced_df["BTC"].rolling(200,min_periods=10).mean().shift() # Size of the moving window = 200 

	# We will use the BTC moving average with 100 records since it seems to be closer to the BTC trend (look at optional visualizations here below)

	x = reduced_df.corr() # Matrix correlation
	#print(x)
	correl = round(x["SP500"][0],4) # Extracting the value of correlation between BTC and S&P 500 from the x matrix
	return (correl, reduced_df)
