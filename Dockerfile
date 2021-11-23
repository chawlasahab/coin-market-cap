FROM python:3.8.0-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt
COPY app.py /app/app.py
CMD ["python", "-u", "app.py", "influxdb", "8086"]