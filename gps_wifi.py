from machine import UART, Pin
import network
import urequests
import time

# ------------ CHANGE THESE 3 -------------
SSID = "Riya's iPhone"          # your WiFi / hotspot name
PASSWORD = "yourpassword"  # your WiFi password
WEBHOOK_URL = "https://webhook.site/4201e1c0-4b12-4e73-a440-772aa310e9df"  # your webhook URL
# -----------------------------------------

SEND_PERIOD_S = 10  # seconds between uploads

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
    # NMEA format: DDMM.MMMM or DDDMM.MMMM
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
    # $GPGGA,hhmmss,lat,N,lon,W,fix,sats,hdop,alt,M,...
    parts = sentence.split(',')
    if len(parts) < 10:
        print("Too short")
        return None
    if parts[0] != "$GPGGA":
        return None
    fix = parts[6]
    sats = parts[7]
    hdop = parts[8]
    
    if fix == "0" or fix == "":
        print("no GPS fix yet")
        return None
    lat = dmm_to_deg(parts[2], True, parts[3])
    lon = dmm_to_deg(parts[4], False, parts[5])
    
    print("Parsed lat/lon:", lat, lon)
    
    if lat is None or lon is None:
        print("Lat/lon parse failed")
        return None
    
    return {
        "lat": lat,
        "lon": lon,
        "sats": parts[7] or None,
        "hdop": parts[8] or None,
        "alt_m": parts[9] or None
    }

def send_coordinates(lat, lon, extra=None):
    if extra is None:
        extra = {}
    params = {
        "lat": "{:.6f}".format(lat),
        "lon": "{:.6f}".format(lon)
    }
    params.update(extra)
    query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    url = WEBHOOK_URL + "?" + query
    print("Sending to webhook:", url)
    LED.on()
    try:
        r = urequests.get(url)
        print("Webhook status:", r.status_code)
        r.close()
    except Exception as e:
        print("Error sending:", e)
    LED.off()

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
                print("GPS FIX:", lat, lon)
                now = time.time()
                if now - last_send >= SEND_PERIOD_S:
                    send_coordinates(lat, lon, {
                        "sats": data["sats"],
                        "hdop": data["hdop"],
                        "alt_m": data["alt_m"]
                    })
                    last_send = now

        # little heartbeat so you know it's alive
        LED.toggle()
        time.sleep(0.5)

main()
