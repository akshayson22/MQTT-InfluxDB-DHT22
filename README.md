# DHT22 Sensor Data Logger with MQTT and InfluxDB

This project provides a comprehensive solution for logging temperature and humidity data from a DHT22 sensor connected to a Raspberry Pi. It leverages MQTT for real-time data streaming and InfluxDB for efficient time-series data storage and historical analysis.

## Features

- Real-time Monitoring: Continuously reads temperature and humidity data from a DHT22 sensor.
- MQTT Integration: Publishes sensor data to a specified MQTT broker, making it accessible to other distributed systems.
- InfluxDB Storage: Stores all time-series data in InfluxDB, a purpose-built database for sensor data.
- Robust Error Handling: Includes robust error handling for sensor read failures and network connection issues.
- Configurable: Easily configure InfluxDB and other settings via a simple JSON file.

## Prerequisites

To get started, you'll need the following:

- A Raspberry Pi with available GPIO pins.
- A DHT22 temperature and humidity sensor.
- A stable internet connection for package installation.

## Hardware Setup

Connect the DHT22 sensor to your Raspberry Pi as follows:

- VCC pin: Connect to the 3.3V pin.
- GND pin: Connect to a Ground pin.
- DATA pin: Connect to GPIO4 (physical pin 7).

---

## Software Installation

### Step 1: Update System Packages
Start by ensuring your system packages are up to date.

sudo apt update
sudo apt upgrade -y


### Step 2: Install Required System Packages
Install the necessary system dependencies, including Python 3, pip, venv, and the Mosquitto MQTT broker.

sudo apt install -y python3 python3-pip python3-venv mosquitto mosquitto-clients


### Step 3: Install InfluxDB
Follow these commands to add the InfluxDB repository and install InfluxDB 2.

Add InfluxDB repository
wget -q https://repos.influxdata.com/influxdata-archive.key
echo '23a1c8836f0afc5ed24e0486339d7cc8f6790b83886c4c96995b88a061c5bb5d influxdata-archive.key' | sha256sum -c && cat influxdata-archive.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive.gpg > /dev/null
echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list

Install InfluxDB
sudo apt update
sudo apt install -y influxdb2

Start and enable InfluxDB service
sudo systemctl start influxdb
sudo systemctl enable influxdb


### Step 4: Create Python Virtual Environment
It's best practice to use a virtual environment to manage project dependencies.

python3 -m venv sensor_env
source sensor_env/bin/activate


### Step 5: Install Python Dependencies
Install the required Python libraries using pip.

pip install paho-mqtt influxdb-client adafruit-circuitpython-dht


---

## Configuration

### Step 1: Set Up InfluxDB
After installation, you'll need to run the setup command to configure your InfluxDB instance.

Setup InfluxDB (run this once)
influx setup


Follow the prompts to create your organization, bucket, and an admin user.

### Step 2: Create an API Token
Generate an all-access API token that the Python script will use to write data to InfluxDB.

influx auth create --org your-org-name --all-access


Note: Save the generated token securely.

### Step 3: Create Configuration File
Create a file named APIInfluxDB.json in your project directory and add your InfluxDB connection details.

{
"INFLUX_URL": "http://localhost:8086",
"INFLUX_TOKEN": "your-generated-token-here",
"INFLUX_ORG": "your-organization-name",
"INFLUX_BUCKET": "your-bucket-name"
}


### Step 4: Configure MQTT (Optional)
The script uses the local Mosquitto broker by default. If you need to enable authentication, edit the configuration file and add user credentials.

Edit Mosquitto configuration
sudo nano /etc/mosquitto/mosquitto.conf

Add these lines if needed:
allow_anonymous false
password_file /etc/mosquitto/passwd
Create password file (if using authentication)
sudo mosquitto_passwd -c /etc/mosquitto/passwd username

Restart Mosquitto
sudo systemctl restart mosquitto


---

## Usage

### Step 1: Clone the Repository
Clone the project repository and navigate into the directory.

git clone https://github.com/yourusername/dht22-sensor-logger.git
cd dht22-sensor-logger


### Step 2: Activate Virtual Environment
Make sure you activate the virtual environment you created earlier.

source sensor_env/bin/activate


### Step 3: Run the Script
Execute the main Python script. It will begin reading data from the sensor, publishing it to MQTT, and storing it in InfluxDB.

python3 sensor_logger.py

The script is configured to read from the DHT22 sensor every 30 seconds.

### Step 4: Verify Data Flow
You can verify that data is being transmitted correctly using the following commands.

Check MQTT messages:
mosquitto_sub -h localhost -t Temp_and_Humidity

Check InfluxDB data:
influx query '
from(bucket: "your-bucket-name")
|> range(start: -1h)
|> filter(fn: (r) => r._measurement == "temperature_humidity")
'


---

## Running as a Service (Optional)

To ensure the script runs automatically on startup, you can create a systemd service.

### Step 1: Create Service File
Create a new service file using sudo.

sudo nano /etc/systemd/system/sensor-logger.service


### Step 2: Add Service Configuration
Add the following configuration to the service file. Be sure to update the User and WorkingDirectory paths if your setup is different.

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


### Step 3: Enable and Start Service
Reload the systemd daemon and enable the service to start automatically at boot.

sudo systemctl daemon-reload
sudo systemctl enable sensor-logger.service
sudo systemctl start sensor-logger.service


---

## Monitoring and Troubleshooting

### Check Service Status
sudo systemctl status sensor-logger.service


### View Logs
sudo journalctl -u sensor-logger.service -f


### Test Sensor Manually
If you suspect an issue with the sensor, you can test it with a simple Python one-liner.

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


---

## Data Visualization

Once your data is flowing into InfluxDB, you can visualize it using various tools.

- Grafana: Connect to your InfluxDB instance as a data source to create custom dashboards.
- InfluxDB UI: Use the built-in dashboard tools available at http://<your-influxdb-ip>:8086.
- Chronograf: Another visualization tool from InfluxData.

### Example Grafana Query:
This query can be used in Grafana to plot temperature and humidity over time.

FROM temperature_humidity
SELECT mean("temperature") AS "Temperature", mean("humidity") AS "Humidity"
WHERE timeFilterGROUPBYtime(__interval)


---

## File Structure

The project has a straightforward file structure:

dht22-sensor-logger/
├── sensor_logger.py          # Main script
├── APIInfluxDB.json          # Configuration file (create this)
└── README.md                 # This file

