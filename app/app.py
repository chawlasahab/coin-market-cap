import os
import time
import json
import logging
import pandas as pd
import requests
from influxdb import InfluxDBClient
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import argparse


# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DB_NAME = os.getenv("INFLUXDB_DB")
MEASUREMENT = "top5currencies"
CMC_API_KEY = os.getenv("CMC_API_KEY")

client = None
DATA_5M = []

def db_exists():
    '''returns True if the database exists'''
    return any(db["name"] == DB_NAME for db in client.get_list_database())


def wait_for_server(host, port, retries=5):
    '''wait for the server to come online for waiting_time, retries times.'''
    url = f"http://{host}:{port}"
    waiting_time = 1
    for _ in range(retries):
        try:
            requests.get(url)
            return
        except requests.exceptions.ConnectionError:
            logger.info(f"Waiting for {url}...")
            time.sleep(waiting_time)
            waiting_time *= 2
    logger.error(f"Cannot connect to {url}")
    sys.exit(1)


def connect_db(host, port):
    '''connect to the database, and create it if it does not exist'''
    global client
    logger.info(f"Connecting to InfluxDB at {host}:{port}")
    client = InfluxDBClient(host, port, retries=5, timeout=1)
    wait_for_server(host, port)
    if not db_exists():
        logger.info(f"Creating database '{DB_NAME}'...")
        client.create_database(DB_NAME)
    else:
        logger.info(f"Database '{DB_NAME}' already exists.")
    client.switch_database(DB_NAME)


def push(data):
    '''push data in measurement: metrics to visualize on grafana'''
    try:
        client.drop_measurement(MEASUREMENT)
        for e in data:
            metrics_data = [{
                "measurement": MEASUREMENT,
                "fields": {
                    "name": e[0],
                    "price": e[1]
                }
            }]
            client.write_points(metrics_data)
        logger.info("Data pushed to InfluxDB.")
    except Exception as e:
        logger.error(f"Failed to push data: {e}")


def calculate(data):
    result = []
    for r1, c1 in data[0].iterrows():
        for r2, c2 in data[4].iterrows():
            if c1[0] == c2[0]:
                price_diff = abs(c1[2] - c2[2])
                result.append([c1[1], c2[2], price_diff])
    result.sort(key=lambda x: x[2], reverse=True)
    return result[:5]


def capture():
    currency_data = []
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': CMC_API_KEY,
    }
    parameters = {
        'start': '1',
        'limit': '200',
        'convert': 'USD',
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        response.raise_for_status()
        data = response.json()
        for currency in data.get("data", []):
            currency_data.append([
                currency["id"],
                currency["name"],
                currency["quote"]["USD"]["price"]
            ])
    except Exception as e:
        logger.error(f"Error fetching data from CoinMarketCap: {e}")
    df = pd.DataFrame(currency_data)
    return df.sort_values(by=[0])

def main():
    parser = argparse.ArgumentParser(description="Crypto to InfluxDB pipeline")
    parser.add_argument("host", help="InfluxDB host")
    parser.add_argument("port", help="InfluxDB port", type=int)
    args = parser.parse_args()

    connect_db(args.host, args.port)

    while True:
        temp = capture()
        DATA_5M.append(temp)
        if len(DATA_5M) == 5:
            metrics_data = calculate(DATA_5M)
            push(metrics_data)
            DATA_5M.pop(0)
        time.sleep(60)

if __name__ == "__main__":
    if not CMC_API_KEY:
        logger.error("CMC_API_KEY is not set. Check your .env file.")
        sys.exit(1)
    main()
