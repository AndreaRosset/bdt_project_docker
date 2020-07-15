import redis
import json
import psycopg2
# import test                           Not used to improve performance

redis_ip = "redis"
redis_port = 6379

SP500_list = "SP500"					#Name of the Redis lists where to push the data
BTC_list= "BTC"							#

host = "postgresql"
database= "btc_sp500_stocks"			#Name of the Postgres database where to push the data
user= "postgres"						#postgres user
password= "postgres"					#postgres password

#create table if not exists
create = """CREATE TABLE IF NOT EXISTS btc_sp500_stocks(	
   t_time float primary key not null,
   BTC_value float not null,
   SP500 float not null
);"""

#sql insertion query
sql = """INSERT INTO btc_sp500_stocks
             VALUES(%f, %f, %f);"""

r = redis.Redis(host=redis_ip, port=redis_port)		#connection to Redis
conn = psycopg2.connect(host=host, database=database, user=user, password=password)		#connection to Postgres
cur = conn.cursor()
cur.execute(create)		#create table if not exists

SP500_BTC_db_entry = {}

def db_insertion(json_to_insert):			#function for json insertion into postgres database
    
    cur.execute(sql % (json_to_insert["timestamp"], json_to_insert["BTC_value"], json_to_insert["SP500_value"]))
    conn.commit()    

SP500 = [json.loads(r.blpop(SP500_list)[1].decode('utf8'))]		#pop first SP500 value
BTC = [json.loads(r.blpop(BTC_list)[1].decode('utf8'))]			#pop first BTC value

#pop from SP500 list
last_SP500 = r.blpop(SP500_list)
last_SP500 = last_SP500[1].decode('utf8')
last_SP500 = json.loads(last_SP500)
#pop from BTC list
last_BTC = r.blpop(BTC_list)
last_BTC = last_BTC[1].decode('utf8')
last_BTC = json.loads(last_BTC)
 
def sync(BTC, SP500, last_BTC, last_SP500):  			#function to syncronize the 2 lists

#if one of the lists have multiple values lower than the other we pop them in order to sync
 
    while (BTC[-1]["timestamp"] < SP500[-1]["timestamp"] and last_BTC["timestamp"] < SP500[-1]["timestamp"]) or (SP500[-1]["timestamp"] < BTC[-1]["timestamp"] and last_SP500["timestamp"] < BTC[-1]["timestamp"]):
    
        if BTC[-1]["timestamp"] < SP500[-1]["timestamp"] and last_BTC["timestamp"] < SP500[-1]["timestamp"]:
        
            BTC = [last_BTC]
            last_BTC = r.blpop(BTC_list)
            last_BTC = last_BTC[1].decode('utf8')
            last_BTC = json.loads(last_BTC)
    
        else:
        
            SP500 = [last_SP500]
            last_SP500 = r.blpop(SP500_list)
            last_SP500 = last_SP500[1].decode('utf8')
            last_SP500 = json.loads(last_SP500)
        
    return ([last_BTC], [last_SP500])
    
while True:

#pop new values
    
    last_SP500 = r.blpop(SP500_list)
    last_SP500 = last_SP500[1].decode('utf8')
    last_SP500 = json.loads(last_SP500)
    last_BTC = r.blpop(BTC_list)
    last_BTC = last_BTC[1].decode('utf8')
    last_BTC = json.loads(last_BTC)
  
#if lists are not syncronized we sync them
    
    if (BTC[-1]["timestamp"] < SP500[-1]["timestamp"] and last_BTC["timestamp"] < SP500[-1]["timestamp"]) or (SP500[-1]["timestamp"] < BTC[-1]["timestamp"] and last_SP500["timestamp"] < BTC[-1]["timestamp"]):
        
        x = sync(BTC, SP500, last_BTC, last_SP500)
        BTC = x[0]
        SP500 = x[1]

#if BTC value changes we fix this change in the database
  
    if last_BTC["BTC_value"] != BTC[-1]["BTC_value"]:
        
        SP500.append(last_SP500)
        min = 0
        
        for pos, obj in enumerate(SP500):
            if abs(obj["timestamp"] - last_BTC["timestamp"]) < abs(SP500[min]["timestamp"] - last_BTC["timestamp"]):
                min = pos
         
		#pick the SP500 value nearest in time
                
        while abs(last_BTC["timestamp"] - last_SP500["timestamp"]) <= abs(SP500[min]["timestamp"] - last_BTC["timestamp"]):
            
            last_SP500 = r.blpop(SP500_list)
            last_SP500 = last_SP500[1].decode('utf8')
            last_SP500 = json.loads(last_SP500)
            
            if abs(last_BTC["timestamp"] - last_SP500["timestamp"]) <= abs(SP500[-1]["timestamp"] - last_BTC["timestamp"]):
                
                min = len(SP500)
                SP500.append(last_SP500)
            
        r.lpush("SP500", json.dumps(last_SP500))
        
        if abs(SP500[min]["timestamp"] - last_BTC["timestamp"] < 1):		#check that time difference is acceptable
            
            SP500_BTC_db_entry = {
                "timestamp": last_BTC["timestamp"],
                "BTC_value": last_BTC["BTC_value"],
                "SP500_value": SP500[min]["SP500_value"]
            }
        
            db_insertion(SP500_BTC_db_entry)								#insert into postgres

		#updete lists
	
        SP500 = [SP500[-1]]
        BTC = [last_BTC]
        
        # reduced_df = test.dataframe_update()                            
        # x = test.calc_correl(reduced_df)
        # correl = x[0]
        # reduced_df = x[1]
        # test.calc_results(reduced_df, correl) """
 
 #if SP500 value changes we fix this change in the database
        
    elif last_SP500["SP500_value"] != SP500[-1]["SP500_value"]:
        
        BTC.append(last_BTC)
        min = 0
        
        for pos, obj in enumerate(BTC):
            if obj["timestamp"] - last_SP500["timestamp"] < BTC[min]["timestamp"] - last_SP500["timestamp"]:
                min = pos
       
       #pick the BTC value nearest in time
           
        while abs(last_BTC["timestamp"] - last_SP500["timestamp"]) <= abs(BTC[min]["timestamp"] - last_SP500["timestamp"]):
            
            last_BTC = r.blpop(BTC_list)
            last_BTC = last_BTC[1].decode('utf8')
            last_BTC = json.loads(last_BTC)
            
            if abs(last_BTC["timestamp"] - last_SP500["timestamp"]) <= abs(BTC[-1]["timestamp"] - last_SP500["timestamp"]):
                
                min = len(BTC)
                BTC.append(last_BTC)
            
        r.lpush("BTC", json.dumps(last_BTC))
        
        if abs(BTC[min]["timestamp"] - last_SP500["timestamp"] < 1):		#check that time difference is acceptable
        
            SP500_BTC_db_entry = {
                "timestamp": last_SP500["timestamp"],
                "BTC_value": BTC[min]["BTC_value"],
                "SP500_value": last_SP500["SP500_value"]
            }
        
            db_insertion(SP500_BTC_db_entry)								#insert into postgres
        
		#updete lists
        
        SP500 = [last_SP500]
        BTC = [BTC[-1]]
        
        # reduced_df = test.dataframe_update()
        # x = test.calc_correl(reduced_df)
        # correl = x[0]
        # reduced_df = x[1]
        # test.calc_results(reduced_df, correl) """
        
    else:
        
        #if no value changed we save the values we have and continue
        
        SP500.append(last_SP500)
        BTC.append(last_BTC)
