# main.py
# Pico W: LCD dashboard + non-blocking Wi‑Fi + LED status + DST local time (FI) +
# hourly NTP sync + web server with / (HTML) and /data (JSON) + sensor logging
# Firebase sync every minute

from machine import I2C, Pin, RTC, ADC
import time, ujson, network, ntptime, socket
import lcd_driver
from bme680 import *
from firebase_sync import FirebaseSync, load_firebase_config

# --- IAQ calculation ---
def calculate_iaq(humidity, gas_res):
    humidity_baseline = 40
    humidity_weighting = 0.25
    humidity_offset = humidity - humidity_baseline
    if humidity_offset > 0:
        humidity_score = (100 - humidity_baseline - humidity_offset) / \
                         (100 - humidity_baseline) * (humidity_weighting * 100)
    else:
        humidity_score = (humidity_baseline + humidity_offset) / \
                         humidity_baseline * (humidity_weighting * 100)
    gas_score = min((gas_res / 100000.0), 1.0) * (100 - (humidity_weighting * 100))
    iaq = humidity_score + gas_score
    if iaq >= 80: return "Good"
    elif iaq >= 60: return "Avg"
    elif iaq >= 40: return "Poor"
    else: return "Bad"

# --- DST-aware localtime (Finland: EET/EEST) ---
def is_leap(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def days_in_month(year, month):
    if month == 2: return 29 if is_leap(year) else 28
    return [31, None, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1]

def weekday(y, m, d):
    t = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4]
    if m < 3:
        y -= 1
    return (y + y//4 - y//100 + y//400 + t[m-1] + d) % 7

def last_sunday(year, month):
    ld = days_in_month(year, month)
    wd = weekday(year, month, ld)
    return ld if wd == 0 else ld - wd

def localtime_with_dst():
    utc = time.localtime()
    year, month, day = utc[0], utc[1], utc[2]
    dst_start_day = last_sunday(year, 3)
    dst_end_day   = last_sunday(year, 10)
    in_dst = (month > 3 and month < 10) or \
             (month == 3 and day >= dst_start_day) or \
             (month == 10 and day <= dst_end_day)
    offset_hours = 3 if in_dst else 2
    return time.localtime(time.time() + offset_hours * 3600)
time.sleep(4)
# --- Hardware setup ---
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
lcd_driver.lcd_init(i2c)
bme = BME680_I2C(i2c, address=0x77)
rtc = RTC()
led = Pin("LED", Pin.OUT)

# --- Wi‑Fi setup ---
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Load credentials
SSID = None
PASSWORD = None
try:
    with open("key.json", "r") as f:
        wifi_data = ujson.load(f)
        SSID = wifi_data.get("ssid")
        PASSWORD = wifi_data.get("password")
except OSError:
    print("key.json not found!")

def connect_wifi():
    if SSID and PASSWORD and not wlan.isconnected():
        print("Connecting Wi‑Fi…")
        wlan.connect(SSID, PASSWORD)

# --- Restore RTC from last saved UTC time ---
try:
    with open("last_values.json", "r") as f:
        last_data = ujson.load(f)
        date_parts = [int(x) for x in last_data["date"].split("-")]
        time_parts = [int(x) for x in last_data["time_sec"].split(":")]
        rtc.datetime((date_parts[2], date_parts[1], date_parts[0],
                      0, time_parts[0], time_parts[1], time_parts[2], 0))
        print("Restored time:", rtc.datetime())
except Exception:
    print("No saved time, RTC starts at default")
    
connect_wifi()

# --- Firestore setup ---
project_id, api_key = load_firebase_config()
firebase = None
if project_id and api_key:
    firebase = FirebaseSync(project_id, api_key)
    print("Firestore configured:", project_id)
else:
    print("Firestore not configured - skipping sync")

# --- State ---
modes = ["AIRTEMP", "HUMPRESS"]
idx = 0
start_time = time.time()
last_wifi_attempt = 0
last_ntp_sync = 0
last_firebase_sync = 0  # Track last Firebase sync time

# --- Web server setup (non-blocking accept)
PORT = 80
try:
    s
    try:
        s.close()
    except Exception:
        pass
except NameError:
    pass
addr = socket.getaddrinfo('0.0.0.0', PORT)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(2)
s.settimeout(0.5)
print("Web server ready")
print("Server bound to", addr)
print("Open in browser:", "http://{}".format(wlan.ifconfig()[0]))

led_state = 0
while True:
    # LED indicator
    if led_state == 0 and wlan.isconnected():
        led.value(1)
        led_state = 1
        print(wlan.ifconfig())
        print("Web server ready")
        print("Server bound to", addr)
        print("Open in browser:", "http://{}".format(wlan.ifconfig()[0]))
    elif led_state == 1 and not wlan.isconnected():
        led.value(0)
        led_state = 0
    # Measurements
    utc = time.localtime()
    local = localtime_with_dst()
    temp = bme.temperature
    hum  = bme.humidity
    pres = bme.pressure
    gas  = bme.gas
    iaq  = calculate_iaq(hum, gas)
    uptime = int(time.time() - start_time)

    # Internal chip temperature
    sensor_temp = ADC(4)
    conversion_factor = 3.3 / 65535
    reading = sensor_temp.read_u16() * conversion_factor
    internal_temp = 27 - (reading - 0.706)/0.001721

    # Append sensor log (local time)
    try:
        with open("data.json", "r") as f:
            sensor_log = ujson.load(f)
            if not isinstance(sensor_log, list):
                sensor_log = []
    except Exception:
        sensor_log = []
    sensor_log.append({
        "time": "{:02d}:{:02d}:{:02d}".format(local[3], local[4], local[5]),
        "date": "{:02d}-{:02d}-{:04d}".format(local[2], local[1], local[0]),
        "temp": round(temp, 2),
        "hum": round(hum, 2),
        "pres": round(pres, 0),
        "iaq": iaq
    })
    if len(sensor_log) > 500:
        sensor_log = sensor_log[-500:]
    with open("data.json", "w") as f:
        ujson.dump(sensor_log, f)

    # Save latest reading to pending_upload.json for Firebase sync
    pending_data = {
        "timestamp": "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
            local[0], local[1], local[2], local[3], local[4], local[5]
        ),
        "temperature_C": round(temp, 2),
        "humidity_%": round(hum, 2),
        "pressure_hPa": round(pres, 1),
        "gas_ohms": int(gas)
    }
    try:
        with open("pending_upload.json", "w") as f:
            ujson.dump(pending_data, f)
    except Exception as e:
        print(f"Error saving pending upload: {e}")

    # Save system info (UTC) for last_values.json
    sys_data = {
        "time": "{:02d}:{:02d}".format(utc[3], utc[4]),
        "time_sec": "{:02d}:{:02d}:{:02d}".format(utc[3], utc[4], utc[5]),
        "date": "{:02d}-{:02d}-{:04d}".format(utc[2], utc[1], utc[0]),
        "uptime_sec": uptime,
        "wifi": "OK" if wlan.isconnected() else "OFF",
        "chip_temp": round(internal_temp, 2),
        "chip": "RP2040"
    }
    with open("last_values.json", "w") as f:
        ujson.dump(sys_data, f)

    # LCD update (local time)
    line_1 = "{:02d}:{:02d} {:02d}-{:02d}-{:04d}".format(local[3], local[4], local[2], local[1], local[0])
    if modes[idx] == "AIRTEMP":
        line_2 = "{:.2f} C {} Air".format(temp, iaq)
    else:
        line_2 = "{:.2f}% {:.0f} hPa".format(hum, pres)
    lcd_driver.lcd_write_line(i2c, 0, line_1)
    lcd_driver.lcd_write_line(i2c, 1, line_2)

    # Wi‑Fi retry every 60s; hourly NTP sync; Firebase sync every 60s
    if (time.time() - last_wifi_attempt) > 60:
        if not wlan.isconnected():
            connect_wifi()
        else:
            if (time.time() - last_ntp_sync) > 3600:
                try:
                    ntptime.settime()
                    last_ntp_sync = time.time()
                    print("RTC synced (UTC):", time.localtime())
                except Exception:
                    print("NTP sync failed")
        last_wifi_attempt = time.time()
    
    # Firestore sync every 60 seconds (only when WiFi is connected)
    if firebase and wlan.isconnected() and (time.time() - last_firebase_sync) > 60:
        try:
            with open("pending_upload.json", "r") as f:
                upload_data = ujson.load(f)
            
            # Send to Firestore - creates a new document with auto-generated ID
            if firebase.send_data("air_quality_readings", upload_data):
                print(f"Firestore sync OK: {upload_data['timestamp']}")
            else:
                print("Firestore sync failed - will retry in 60s")
                
        except Exception as e:
            print(f"Firestore sync error: {e}")
        
        last_firebase_sync = time.time()

    # Web server (non-blocking accept)
    
    try:
        cl, caddr = s.accept()        # will block up to s.gettimeout()
        print("Client from", caddr)
        cl.settimeout(1.0)            # short timeout for recv
        try:
            req = cl.recv(1024).decode()
        except OSError:
            print("recv timeout or error from", caddr)
            cl.close()
            raise
        
        if req.startswith("GET /reboot"):
            html = "<html><head><meta charset='utf-8'><title>Rebooting</title></head><body><h1>Rebooting...</h1></body></html>"
            headers = ("HTTP/1.1 200 OK\r\n"
                       "Content-Type: text/html; charset=utf-8\r\n"
                       "Connection: close\r\n\r\n")
            try:
                cl.send((headers + html).encode("utf-8"))
            except Exception:
                pass
            try:
                cl.close()      # close client socket
            except Exception:
                pass
            try:
                s.close()       # close listening socket if you can (optional)
            except Exception:
                pass
            import time, machine
            time.sleep(0.3)     # give TCP a moment to flush
            machine.reset()
        else:
            local_time_str = "{:02d}:{:02d}:{:02d} — {:02d}-{:02d}-{:04d}".format(
                local[3], local[4], local[5], local[2], local[1], local[0]
            )

            time_short    = sys_data.get("time", "--:--")
            time_sec      = sys_data.get("time_sec", "--:--:--")
            date_str      = sys_data.get("date", "--")
            uptime_str    = str(sys_data.get("uptime_sec", "--"))
            wifi_str      = sys_data.get("wifi", "OFF")
            chip_temp_str = str(sys_data.get("chip_temp", "--"))
            chip_str      = sys_data.get("chip", "RP2040")

            html_body = (
                '<html><head><title>Pico W Dashboard</title>'
                '<meta http-equiv="refresh" content="10">'
                '<style>'
                'body{font-family:Arial,Helvetica,sans-serif;background:#f5f7fb;padding:20px;color:#111}'
                'table{border-collapse:collapse;width:480px;background:#fff;margin-bottom:16px}'
                'th,td{border:1px solid #e5e7eb;padding:8px 10px;text-align:left}'
                'th{background:#f9fafb}'
                '.sub{color:#6b7280;margin-bottom:12px}'
                'a.button{display:inline-block;padding:8px 12px;background:#2563eb;color:#fff;text-decoration:none;border-radius:6px}'
                '</style></head><body>'
                '<h1>Pico W System Dashboard</h1>'
                '<div class="sub">Local: %s</div>'
                '<table>'
                '<tr><th>Field</th><th>Value</th></tr>'
                '<tr><td>UTC time</td><td>%s %s</td></tr>'
                '<tr><td>Uptime (sec)</td><td>%s</td></tr>'
                '<tr><td>Chip temperature</td><td>%s °C</td></tr>'
                '</table>'
                '<form action="/reboot" method="get" onsubmit="return confirm(\'Reboot Pico W now?\');" style="margin-top:12px">'
                '  <button type="submit" style="padding:8px 12px;background:#ef4444;color:#fff;border:none;border-radius:6px;cursor:pointer;">'
                '    Reboot device'
                '  </button>'
                '</form>'
                '</body></html>'
            ) % (
                local_time_str,
                time_sec, date_str,
                uptime_str,
                chip_temp_str
            )
             
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                "Connection: close\r\n\r\n"
                +html_body
            )
            cl.send(response.encode("utf-8"))
        cl.close()
          
    except OSError:
        pass

    # Rotate LCD mode
    time.sleep(6)
    idx = (idx + 1) % len(modes)

