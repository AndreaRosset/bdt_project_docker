from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
#import pika
import redis
import threading
import json
import time
import re

chrome_driver = "/usr/local/bin/chromedriver"
#rabbitMQ = "localhost"
redis_ip = "redis"
redis_port = 6379
index_list = "BTC"

url_btc_usd = "https://www.investing.com/indices/investing.com-btc-usd"

#connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitMQ))
#BTC_channel = connection.channel()
#BTC_channel.queue_declare(queue='BTC')

r = redis.Redis(host=redis_ip, port=redis_port)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(executable_path=chrome_driver, options=chrome_options)

driver.get(url_btc_usd)

def get_btc_value():
    threading.Timer(0.5, get_btc_value).start()
    
    content_element = driver.find_element_by_id("last_last")
    content_html = content_element.get_attribute("innerHTML")
    soup = BeautifulSoup(content_html, "html.parser")
    
    new_data_entry = { 
        "timestamp":time.time(), 
        "BTC_value": float(re.sub(r',', '', str(soup)))
    }
    
    new_data_entry = json.dumps(new_data_entry) 
    
    r.rpush(index_list, new_data_entry)
    
#    BTC_channel.basic_publish(exchange='',
#                      routing_key='BTC',
#                      body=new_data_entry)
    
get_btc_value()
