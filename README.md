# 🪙 coin-market-cap Monitoring Stack

This project fetches real-time cryptocurrency data using the CoinMarketCap API, stores it in InfluxDB, and visualizes it with Grafana.

---

## 🔑 Generate Your CoinMarketCap API Key

1. Go to [https://coinmarketcap.com/api/](https://coinmarketcap.com/api/)
2. Sign up for a free plan
3. Copy your API key
4. Paste it in the `.env` file at the root of this project:

```env
CMC_API_KEY=your_api_key_here
INFLUXDB_DB=mydb
```

---

## 🚀 Run the Application

```bash
# Build and start all services
docker compose up -d

# Stop the application
docker compose down
```

> Make sure Docker is running, and you are in the root of the project (where `docker-compose.yml` is located).

---

## 📦 Project Structure

```
.
├── .env                    # Contains API key and InfluxDB config
├── docker-compose.yml      # Defines InfluxDB, Grafana, and app services
├── Makefile                # (Optional) CLI helper commands
├── app/
│   ├── app.py              # Python script to fetch and store crypto data
│   ├── Dockerfile          # Dockerfile for the app
│   └── requirements.txt    # Python dependencies
└── grafana/
    └── provisioning/       # Optional: auto-setup Grafana dashboards/datasource
```

---

## 📊 Accessing Grafana

Once the services are up:

- Visit: [http://localhost:3000](http://localhost:3000)
- Default login:
  - **Username**: `admin`
  - **Password**: `admin` (you may be prompted to change this)

> If provisioning is enabled, Grafana will automatically detect the InfluxDB data source.

---

### 📈 Creating the Dashboard (Manually)

If no dashboards are provisioned:

1. Click **"New Dashboard"** → **"Add new panel"**
2. Select **InfluxDB** as the data source
3. Enter this query:

```sql
SELECT "price" FROM "top5currencies"
```

4. Under **"Legend"**, choose **`name`** to show different currencies
5. Choose **Time Series**, **Bar Gauge**, or **Table** visualization

---

## ⚙️ Customization

- Update the fetch interval or volatility logic in `app/app.py`
- Modify `.env` to change database name or API keys
- Add Grafana dashboard JSONs under `grafana/provisioning/dashboards/`

---

## 📌 Tips

- To inspect raw data:
  ```bash
  docker exec -it influxdb influx
  > USE mydb;
  > SELECT * FROM "top5currencies";
  ```

- To watch logs:
  ```bash
  docker compose logs -f app
  ```

---

## 📃 Coming Soon
- Auto-provisioned Grafana dashboards
- Alerts on extreme volatility
- Export to CSV/API endpoints

---

## 📄 License

MIT

