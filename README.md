# Air-Quality-Monitoring-IoT

##  Overview
This project is an **IoT-based indoor air quality monitoring system** built using a **Raspberry Pi Pico W**, a **BME680 environmental sensor** (DFRobot), and a **Grove 16x2 LCD screen (blue on white)**.  
It measures **temperature, humidity, pressure, and gas resistance**, processes the data, and calculates an **Air Quality Index (AQI)** category:  
- Good  
- Average  
- Poor  
- Bad  

The system displays real-time data on the LCD and hosts a local **HTTP server** for remote monitoring and device management.

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

