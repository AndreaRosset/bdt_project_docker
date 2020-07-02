# Big Data Project

This repo contains a project for a Big Data Technology University course.
It aims to provide usefull insight about short selling on Bitcoin
based on the correlation with S&P 500 index


# Documentation

## Building

In order to build the files contained in this repository, you'll generally use the `docker-compose up` command.
This will download the various images needed fot the project to run, build and start them.

## Requirements

* Ensure to have docker running
* Ensure to have docker-compose

## Possible errors

There is a known error that may ocoure in some cases where the table is not created before trying to access it.
In this case it is sufficient to stop the service an run it again.

## Structure

### BTC_scraper

This folder contains the service that retrieves the Bitcoin value every .5 seconds from Investing.com
and put them into the Redis queue.
`BTC_scraper.py` Uses selenium in order to retrieve data from investing.com and then dunp them into a Redis queue.

### SP500_scraper

This folder contains the service that retrieves the S&P 500 value every .5 secons from investing.com
and put them into the Redis queue.
`SP500_scraper.py` Uses selenium in order to retrieve data from investing.com and then dump them into a Redis queue.

### dashboard

This folder contains the service we use as dashboard that retrieve data from PostgreSQL. 
`my_dash.py`uses the Plotly's Python graphing library that makes interactive, publication-quality graphs.

### sink

This folder contains the service that sincronize data from the 2 indexes and dump them into the PostgreSQL database.
`redis_sink_to_postgresql.py` The service takes the data from the Redis queues, syncronize them and push
the values into the persistent PostgreSQL database.

### docker-compose.yml

This is the docker-compose configuration file.
