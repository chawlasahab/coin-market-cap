from influxdb import InfluxDBClient
import requests
import pandas as pd
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import time
import sys

client = None
dbname = 'mydb'
measurment = 'top5currencies'
DATA_5M = []

def db_exists():
    '''returns True if the database exists'''
    databases = client.get_list_database()
    for database in databases:
        if database['name'] == dbname:
            return True
    return False


def wait_for_server(host, port, nretries=5):
    '''wait for the server to come online for waiting_time, nretries times.'''
    url = 'http://{}:{}'.format(host, port)
    waiting_time = 1
    for i in range(nretries):
        try:
            requests.get(url)
            return
        except requests.exceptions.ConnectionError:
            print('waiting for', url)
            time.sleep(waiting_time)
            waiting_time *= 2
            pass
    print('cannot connect to', url)
    sys.exit(1)


def connect_db(host, port, reset):
    '''connect to the database, and create it if it does not exist'''
    global client
    print('connecting to database: {}:{}'.format(host, port))
    client = InfluxDBClient(host, port, retries=5, timeout=1)
    wait_for_server(host, port)
    if not db_exists():
        print('creating database...')
        client.create_database(dbname)
    else:
        print('database already exists')
    client.switch_database(dbname)


def push(data):
    '''push data in measurement: metrics to visualize on grafana'''
    client.drop_measurement(measurment)
    for e in data:
        metrics_data = [{
            "measurement": measurment,
            "fields": {
                "name": e[0],
                "price": e[1]
            }
        }]
        client.write_points(metrics_data)


def calculate(data):
    result = []
    for r1, c1 in data[0].iterrows():
        for r2, c2 in data[4].iterrows():
            if c1[0] == c2[0]:
                price_diff = abs(c1[2] - c2[2])
                result.append([c1[1], c2[2], price_diff])
    result.sort(key=lambda x: x[2], reverse=True)
    return result[0:5]


def capture():
    currency_data = []
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {
        'start': '1',
        'limit': '200',
        'convert': 'USD',
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': '4b75ed5d-bce2-4578-bb5e-ae9e089df2f8',
    }
    session = Session()
    session.headers.update(headers)
    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        for currency in data["data"]:
            currency_data.append([currency["id"], currency["name"], currency["quote"]["USD"]["price"]])
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
    df = pd.DataFrame(currency_data)
    return df.sort_values(by=[0])


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser('%prog [OPTIONS] <host> <port>')
    parser.add_option(
        '-r', '--reset', dest='reset',
        help='reset database',
        default=False,
        action='store_true'
        )
    parser.add_option(
        '-n', '--nmeasurements', dest='nmeasurements',
        type='int',
        help='reset database',
        default=0
        )

    options, args = parser.parse_args()
    if len(args) != 2:
        parser.print_usage()
        print('please specify two arguments')
        sys.exit(1)
    host, port = args
    connect_db(host, port, options.reset)

    while True:
        temp = capture()
        DATA_5M.append(temp)
        if len(DATA_5M) == 5:
            metrics_data = calculate(DATA_5M)
            push(metrics_data)
            DATA_5M = DATA_5M[1:]
        time.sleep(60)
