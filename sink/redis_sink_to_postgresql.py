import redis
import json
import psycopg2

redis_ip = "redis"
redis_port = 6379

SP500_list = "SP500"
BTC_list= "BTC"

host = "postgresql"
database= "btc_sp500_stocks"
user= "postgres"
password= "postgres"

create = """CREATE TABLE IF NOT EXISTS btc_sp500_stocks(
   t_time float primary key not null,
   BTC_value float not null,
   SP500 float not null
);"""

sql = """INSERT INTO btc_sp500_stocks
             VALUES(%f, %f, %f);"""

r = redis.Redis(host=redis_ip, port=redis_port)
conn = psycopg2.connect(host=host, database=database, user=user, password=password)
cur = conn.cursor()
cur.execute(create)

SP500_BTC_db_entry = {}

def db_insertion(json_to_insert):
    
    cur.execute(sql % (json_to_insert["timestamp"], json_to_insert["BTC_value"], json_to_insert["SP500_value"]))
    conn.commit()    

SP500 = [json.loads(r.blpop(SP500_list)[1].decode('utf8'))]
BTC = [json.loads(r.blpop(BTC_list)[1].decode('utf8'))]

last_SP500 = r.blpop(SP500_list)
last_SP500 = last_SP500[1].decode('utf8')
last_SP500 = json.loads(last_SP500)
last_BTC = r.blpop(BTC_list)
last_BTC = last_BTC[1].decode('utf8')
last_BTC = json.loads(last_BTC)
 
def sinc(BTC, SP500, last_BTC, last_SP500):    
    
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
    
    last_SP500 = r.blpop(SP500_list)
    last_SP500 = last_SP500[1].decode('utf8')
    last_SP500 = json.loads(last_SP500)
    last_BTC = r.blpop(BTC_list)
    last_BTC = last_BTC[1].decode('utf8')
    last_BTC = json.loads(last_BTC)
    
    if (BTC[-1]["timestamp"] < SP500[-1]["timestamp"] and last_BTC["timestamp"] < SP500[-1]["timestamp"]) or (SP500[-1]["timestamp"] < BTC[-1]["timestamp"] and last_SP500["timestamp"] < BTC[-1]["timestamp"]):
        
        x = sinc(BTC, SP500, last_BTC, last_SP500)
        BTC = x[0]
        SP500 = x[1]
    
    if last_BTC["BTC_value"] != BTC[-1]["BTC_value"]:
        
        SP500.append(last_SP500)
        min = 0
        
        for pos, obj in enumerate(SP500):
            if abs(obj["timestamp"] - last_BTC["timestamp"]) < abs(SP500[min]["timestamp"] - last_BTC["timestamp"]):
                min = pos
                
        while abs(last_BTC["timestamp"] - last_SP500["timestamp"]) <= abs(SP500[min]["timestamp"] - last_BTC["timestamp"]):
            
            last_SP500 = r.blpop(SP500_list)
            last_SP500 = last_SP500[1].decode('utf8')
            last_SP500 = json.loads(last_SP500)
            
            if abs(last_BTC["timestamp"] - last_SP500["timestamp"]) <= abs(SP500[-1]["timestamp"] - last_BTC["timestamp"]):
                
                min = len(SP500)
                SP500.append(last_SP500)
            
        r.lpush("SP500", json.dumps(last_SP500))
        
        if abs(SP500[min]["timestamp"] - last_BTC["timestamp"] < 1):
            
            SP500_BTC_db_entry = {
                "timestamp": last_BTC["timestamp"],
                "BTC_value": last_BTC["BTC_value"],
                "SP500_value": SP500[min]["SP500_value"]
            }
        
            db_insertion(SP500_BTC_db_entry)

        SP500 = [SP500[-1]]
        BTC = [last_BTC]
        
    elif last_SP500["SP500_value"] != SP500[-1]["SP500_value"]:
        
        BTC.append(last_BTC)
        min = 0
        
        for pos, obj in enumerate(BTC):
            if obj["timestamp"] - last_SP500["timestamp"] < BTC[min]["timestamp"] - last_SP500["timestamp"]:
                min = pos
           
        while abs(last_BTC["timestamp"] - last_SP500["timestamp"]) <= abs(BTC[min]["timestamp"] - last_SP500["timestamp"]):
            
            last_BTC = r.blpop(BTC_list)
            last_BTC = last_BTC[1].decode('utf8')
            last_BTC = json.loads(last_BTC)
            
            if abs(last_BTC["timestamp"] - last_SP500["timestamp"]) <= abs(BTC[-1]["timestamp"] - last_SP500["timestamp"]):
                
                min = len(BTC)
                BTC.append(last_BTC)
            
        r.lpush("BTC", json.dumps(last_BTC))
        
        if abs(BTC[min]["timestamp"] - last_SP500["timestamp"] < 1):
        
            SP500_BTC_db_entry = {
                "timestamp": last_SP500["timestamp"],
                "BTC_value": BTC[min]["BTC_value"],
                "SP500_value": last_SP500["SP500_value"]
            }
        
            db_insertion(SP500_BTC_db_entry)
        
        SP500 = [last_SP500]
        BTC = [BTC[-1]]
        
    else:
        
        SP500.append(last_SP500)
        BTC.append(last_BTC)
