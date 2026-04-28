# MicroPython script for Pico W: read GPS NMEA and POST JSON to backend
# Configure SSID/PASSWORD, BACKEND_IP and RHINO_ID below before saving as main.py

import network
import urequests
import ujson
import time
from machine import UART, Pin

# --- CONFIG ---
SSID = "iPhone"
PASSWORD = "levvviinn"
BACKEND_IP = "172.20.10.2"  # replace with your PC IP running backend
BACKEND_PORT = 5000
RHINO_ID = "rhino-1"
SEND_PERIOD_S = 10

LED = Pin("LED", Pin.OUT)
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5), timeout=1000)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        print("WiFi already connected:", wlan.ifconfig())
        return wlan
    print("Connecting to WiFi...")
    wlan.connect(SSID, PASSWORD)
    start = time.time()
    while not wlan.isconnected():
        if time.time() - start > 30:
            raise RuntimeError("WiFi connect timeout")
        LED.toggle()
        time.sleep(0.5)
    LED.off()
    print("WiFi connected:", wlan.ifconfig())
    return wlan


def dmm_to_deg(dmm, is_lat, hemi):
    if not dmm or not hemi:
        return None
    try:
        deg_len = 2 if is_lat else 3
        degrees = int(dmm[:deg_len])
        minutes = float(dmm[deg_len:])
        value = degrees + minutes / 60.0
        if hemi in ("S", "W"):
            value = -value
        return value
    except:
        return None


def parse_gga(sentence):
    parts = sentence.split(',')
    if len(parts) < 10 or parts[0] != "$GPGGA":
        return None
    fix = parts[6]
    if fix == "0" or fix == "":
        return None
    lat = dmm_to_deg(parts[2], True, parts[3])
    lon = dmm_to_deg(parts[4], False, parts[5])
    if lat is None or lon is None:
        return None
    return {
        "lat": lat,
        "lon": lon,
        "sats": parts[7] or None,
        "hdop": parts[8] or None,
        "alt_m": parts[9] or None,
    }


def post_telemetry(rhino_id, lat, lon, battery=100, flags=0, altitude=None, accuracy=None, sats=None):
    url = f"http://{BACKEND_IP}:{BACKEND_PORT}/telemetry"
    payload = {
        "rhino_id": rhino_id,
        "latitude": lat,
        "longitude": lon,
        "battery": battery,
        "flags": flags,
    }
    if altitude is not None:
        payload["altitude"] = altitude
    if accuracy is not None:
        payload["accuracy"] = accuracy
    if sats is not None:
        payload["sats"] = sats

    try:
        data = ujson.dumps(payload)
        resp = urequests.request("POST", url, data=data, headers={"Content-Type": "application/json"})
        print("POST", url, "->", resp.status_code)
        resp.close()
    except Exception as e:
        print("POST error:", e)


def main():
    try:
        connect_wifi()
    except Exception as e:
        print("WiFi error:", e)

    last_send = 0
    print("Starting GPS loop...")
    while True:
        line = uart.readline()
        if not line:
            time.sleep(0.1)
            continue
        try:
            s = line.decode("ascii").strip()
        except:
            continue
        print(s)
        if s.startswith("$GPGGA"):
            data = parse_gga(s)
            if data:
                lat = data["lat"]
                lon = data["lon"]
                now = time.time()
                if now - last_send >= SEND_PERIOD_S:
                    post_telemetry(RHINO_ID, lat, lon, battery=100, flags=0, altitude=data.get("alt_m"), sats=data.get("sats"))
                    last_send = now
        LED.toggle()
        time.sleep(0.5)


if __name__ == '__main__':
    main()
