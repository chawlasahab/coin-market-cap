from functools import update_wrapper
import pprint
import requests
from influxdb import InfluxDBClient
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import datetime
import time
import sys


client = None
dbname = 'mydb'
measurment = 'crypto_price'


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


def get_entries():
    '''returns all entries in the database.'''
    results = client.query('select * from {}'.format(measurment))
    return results


def remove():
    '''delete any data which is older than 5 minutes from currennt time.'''
    client.query(
      'delete from {} where time < now() - 5m'.format(measurment)
    )


def capture():
    '''insert data into database at an interval of 60 secs'''
    #TIME_5_MINS_AGO = int(datetime.datetime.now().timestamp()) - 360
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {
      'start': '1',
      'limit': '200',
      'convert': 'USD',
    }
    headers = {
      'Accepts': 'application/json',
      'X-CMC_PRO_API_KEY': 'Your API KEY',
    }
    session = Session()
    session.headers.update(headers)
    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        remove()
        for currency in data["data"]:
            currency_data = [{
              "measurement": "crypto_price",
              "fields": {
                "id": currency["id"],
                "name": currency["name"],
                "price": currency["quote"]["USD"]["price"],
              }
            }]
            client.write_points(currency_data)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
    client.query('drop measurement metrics')
    push()
    time.sleep(60)


def push():
    '''push data in measurement: metrics to visualize on grafana'''
    output = []
    results_5m = client.query(
      'select *::field from {} where time >= now() - 5m and time < now() - 4m '.format(
        measurment
      )
    )
    results_now = client.query(
      'select *::field from {} where time <= now() and time > now() - 60s'.format(
        measurment
      )
    )
    r1 = list(results_5m.get_points())
    r2 = list(results_now.get_points())
    for e1 in r1:
        for e2 in r2:
            if e2['id'] == e1['id']:
                output.append(
                  [abs(e1['price']-e2['price']), e1['name'], e2['price']]
                )
    output.sort(key=lambda x: x[0], reverse=True)
    for element in output[:5]:
        metrics_data = [{
            "measurement": "metrics",
            "fields": {
                "name": element[1],
                "price": element[2]
            }
        }]
        client.write_points(metrics_data)


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
        capture()
