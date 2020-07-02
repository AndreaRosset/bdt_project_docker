from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import redis
import threading
import json
import time
import re

chrome_driver = "/usr/local/bin/chromedriver"	#Chrome driver in order for selenium to work
redis_ip = "redis"
redis_port = 6379
index_list = "SP500"							#Name of the Redis list where to push the data

url_SP500 = "https://www.investing.com/indices/us-spx-500"

r = redis.Redis(host=redis_ip, port=redis_port)	#connection to Redis

#Chrome options to run it headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(executable_path=chrome_driver, options=chrome_options)

driver.get(url_SP500)								#use Chrome driver to render the page

def get_sp500_value():
    threading.Timer(0.5, get_sp500_value).start()	#start threads to retrieve data
    
    content_element = driver.find_element_by_id("last_last")	#last_last is the element containing the BTC
    content_html = content_element.get_attribute("innerHTML")
    soup = BeautifulSoup(content_html, "html.parser")			#BeautifulSoup to parse the HTML

    new_data_entry = { 
        "timestamp":time.time(), 
        "SP500_value": float(re.sub(r',', '', str(soup)))		#Stripping BTC value from ','
    }
    
    new_data_entry = json.dumps(new_data_entry)
    
    r.rpush(index_list, new_data_entry)							#Push value in the Redis list as JSON
    
get_sp500_value()
