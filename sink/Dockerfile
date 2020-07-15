FROM python:3.8

# upgrade pip
RUN pip install --upgrade pip

# install psycopg2
RUN pip install psycopg2

#install redis
RUN pip install redis

#install pandas
RUN pip install pandas

ADD redis_sink_to_postgresql.py /
# ADD test.py /                     not used in production to improve performance
ADD wait-for-it.sh /

RUN chmod +x ./wait-for-it.sh 

CMD [ "./wait-for-it.sh", "-t", "0" , "postgresql:5432" ,"--", "python", "redis_sink_to_postgresql.py" ]
