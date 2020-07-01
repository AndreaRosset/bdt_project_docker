FROM python:3.8

# upgrade pip
RUN pip install --upgrade pip

# install psycopg2
RUN pip install psycopg2

#install redis
RUN pip install redis

#install dash
RUN pip install dash

#install plotly
RUN pip install plotly

#install pandar
RUN pip install pandas

#install matplotlib
RUN pip install matplotlib

ADD my_dash.py /
ADD wait-for-it.sh /

RUN chmod +x ./wait-for-it.sh 

CMD [ "./wait-for-it.sh", "-t", "0" , "postgresql:5432" ,"--", "python", "my_dash.py" ]
