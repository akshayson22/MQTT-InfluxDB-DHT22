#**DHT22 Sensor Data Logger with MQTT and InfluxDB**

A Python script that reads temperature and humidity data from a DHT22 sensor on Raspberry Pi, publishes it to MQTT, and stores it in InfluxDB.

#**Features**
Real-time Monitoring: Continuously reads temperature and humidity data from DHT22 sensor

MQTT Integration: Publishes sensor data to MQTT broker for distributed systems

InfluxDB Storage: Stores time-series data in InfluxDB for historical analysis

Error Handling: Robust error handling for sensor read failures and connection issues

Configurable: Easy configuration through JSON file for InfluxDB connection

#**Prerequisites**

Raspberry Pi with GPIO pins

DHT22 temperature and humidity sensor

Internet connection for package installation

#**Hardware Setup**

Connect the DHT22 sensor to your Raspberry Pi:

VCC pin to 3.3V

GND pin to Ground

DATA pin to GPIO4 (physical pin 7)

#**Software Installation**

#**Step 1: Update System Packages**
bash
sudo apt update
sudo apt upgrade -y

#**Step 2: Install Required System Packages**
bash
sudo apt install -y python3 python3-pip python3-venv mosquitto mosquitto-clients

**Step 3: Install **

#**InfluxDB**
bash

# Add InfluxDB repository
wget -q https://repos.influxdata.com/influxdata-archive.key
echo '23a1c8836f0afc5ed24e0486339d7cc8f6790b83886c4c96995b88a061c5bb5d influxdata-archive.key' | sha256sum -c && cat influxdata-archive.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive.gpg > /dev/null
echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list

# Install InfluxDB
sudo apt update
sudo apt install -y influxdb2

# Start and enable InfluxDB service
sudo systemctl start influxdb
sudo systemctl enable influxdb

**Step 4: Create Python Virtual Environment**
bash
python3 -m venv sensor_env
source sensor_env/bin/activate
Step 5: Install Python Dependencies
bash
pip install paho-mqtt influxdb-client adafruit-circuitpython-dht
Configuration


**Step 1: Set Up InfluxDB**
bash
# Setup InfluxDB (run this once)
influx setup
Follow the prompts to create:

Organization name

Bucket name (e.g., sensor_data)

Admin username

Admin password

Retention period

**Step 2: Create API Token**
bash
# Generate API token
influx auth create --org your-org-name --all-access
Save the generated token securely.

**Step 3: Create Configuration File**
Create APIInfluxDB.json in your project directory:

json
{
    "INFLUX_URL": "http://localhost:8086",
    "INFLUX_TOKEN": "your-generated-token-here",
    "INFLUX_ORG": "your-organization-name",
    "INFLUX_BUCKET": "your-bucket-name"
}

**Step 4: Configure MQTT (Optional)**
The script uses the local Mosquitto broker. If you need to configure authentication:

bash
# Edit Mosquitto configuration
sudo nano /etc/mosquitto/mosquitto.conf

# Add these lines if needed:
# allow_anonymous false
# password_file /etc/mosquitto/passwd

# Create password file (if using authentication)
sudo mosquitto_passwd -c /etc/mosquitto/passwd username

# Restart Mosquitto
sudo systemctl restart mosquitto
Usage
**Step 1: Clone the Repository**
bash
git clone https://github.com/yourusername/dht22-sensor-logger.git
cd dht22-sensor-logger

**Step 2: Activate Virtual Environment**
bash
source sensor_env/bin/activate

**Step 3: Run the Script**
bash
python3 sensor_logger.py
The script will:

Start reading from DHT22 sensor every 30 seconds

Publish data to MQTT topic Temp_and_Humidity

Store data in InfluxDB

**Step 4: Verify Data Flow**
Check MQTT messages:

bash
mosquitto_sub -h localhost -t Temp_and_Humidity
Check InfluxDB data:

bash
# Query recent data
influx query '
from(bucket: "your-bucket-name")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "temperature_humidity")
'
Running as a Service (Optional)
Create a systemd service for automatic startup:

**Step 1: Create Service File**
bash
sudo nano /etc/systemd/system/sensor-logger.service

**Step 2: Add Service Configuration**
ini
[Unit]
Description=DHT22 Sensor Logger
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/dht22-sensor-logger
Environment=PATH=/home/pi/dht22-sensor-logger/sensor_env/bin
ExecStart=/home/pi/dht22-sensor-logger/sensor_env/bin/python /home/pi/dht22-sensor-logger/sensor_logger.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

**Step 3: Enable and Start Service**
bash
sudo systemctl daemon-reload
sudo systemctl enable sensor-logger.service
sudo systemctl start sensor-logger.service
Monitoring and Troubleshooting
Check Service Status
bash
sudo systemctl status sensor-logger.service
View Logs
bash
sudo journalctl -u sensor-logger.service -f
Test Sensor Manually
bash
python3 -c "
import board
import adafruit_dht
dht = adafruit_dht.DHT22(board.D4)
try:
    temp = dht.temperature
    hum = dht.humidity
    print(f'Temperature: {temp}°C, Humidity: {hum}%')
except Exception as e:
    print(f'Error: {e}')
"
**Data Visualization**
You can visualize the data using:

Grafana: Connect to InfluxDB datasource

InfluxDB UI: Built-in dashboard tools

Chronograf: InfluxData's visualization tool

Example Grafana Query:
text
FROM temperature_humidity
SELECT mean("temperature") AS "Temperature", mean("humidity") AS "Humidity"
WHERE $timeFilter
GROUP BY time($__interval)

**File Structure**
text
dht22-sensor-logger/
├── sensor_logger.py          # Main script
├── APIInfluxDB.json          # Configuration file (create this)
├── requirements.txt          # Python dependencies
└── README.md                # This file




