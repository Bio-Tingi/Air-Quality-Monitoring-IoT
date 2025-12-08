# Air-Quality-Monitoring-IoT

##  Overview
This project is an **IoT-based indoor air quality monitoring system** built using a **Raspberry Pi Pico W**, a **BME680 environmental sensor** (DFRobot), and a **Grove 16x2 LCD screen (blue on white)**.  
It measures **temperature, humidity, pressure, and gas resistance**, processes the data, and calculates an **Air Quality Index (AQI)** category:  
- Good  
- Average  
- Poor  
- Bad  

The system displays real-time data on the LCD and hosts a local **HTTP server** for remote monitoring and device management.

### Main Scripts
- **main.py** – The primary application script that runs the indoor air quality monitoring system.
- **bme680.py** – Driver for the BME680 sensor, handling temperature, humidity, pressure, and gas resistance readings.
- **lcd_driver.py** – Driver for the Grove 16x2 LCD screen, managing I²C communication and display output.

### Data Folder (`/data`)
This folder contains files used for storing credentials and sensor data:
- **key.json** – Holds Wi-Fi credentials and other necessary configuration values for Pico W to connect to the internet.
- **data.json** – Stores the last recorded data points from the sensor for reference and logging.
- **last_values.json** – Contains the most recent system state variables (e.g., chip temperature, device type, time, date, uptime, Wi-Fi status).  
  These values are saved so the system can restore or reference them after a reboot.

### Images Folder (`/images`)
This folder includes:
- Screenshots of the local web server interface.  
- Photos of the assembled hardware setup (Pico W, BME680 sensor, Grove LCD).  
- Example management interface images (e.g., reboot button).

---

## Hardware Components
- Raspberry Pi Pico W (Wi-Fi capable, onboard LED indicator)  
- BME680 sensor (DFRobot) – measures temperature, humidity, pressure, and gas resistance  
- Grove 16x2 LCD screen (blue on white) – displays sensor readings and AQI status  
- I²C bus – both LCD and sensor connected via the same I²C bus  
- 5V VCC power supply to sensor and screen 

---

## Features
- Wi-Fi connectivity: Pico W connects to the internet; onboard LED lights up when connected.  
- Sensor data acquisition: Reads temperature, humidity, pressure, and gas resistance from BME680.  
- Air quality calculation: Processes sensor data to determine AQI category.  
- LCD display: Shows date/time, pressure, temperature, humidity, and AQI status.  
- Local HTTP server:  
  - Displays monitoring variables and recent sensor data points.  
  - Provides management options (e.g., rebooting the Pico).  

---

## Circuit Connections
- **BME680 sensor** → I²C bus (SDA, SCL)  
- **Grove LCD 16x2** → Same I²C bus (SDA, SCL)  
- **Power supply** → 5V VCC shared across components  

---

## Web Interface
The Pico W hosts a simple **HTTP server** accessible via the local network.  
Features include:  
- Real-time monitoring of sensor variables  
- Viewing last recorded data points  
- Rebooting the Pico remotely  

