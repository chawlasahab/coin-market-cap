# coin-market-cap

## Generating coin market cap API key
* Go to https://coinmarketcap.com/api/
* Sign up to generate your api key
* Copy and paste the generated api key in `app.py` script at line number 90.

## Instructions to start the application:
* Run `docker compose up -d` to start the application
* Run `docker compose down` to stop the application

## Instructions to setup grafana:
* You can access grafana at http://localhost:3000
* In `add datasource` section, add an `Influxdb` datasource
* Configure it by setting URL as http://influxdb:8086, database name as `mydb` and request type as `GET`
* Once added, you can create a dashboard to visualise the data
* Measurement name should selected as `top5currencies` to visualize price and name of top 5 currencies with highest volatility