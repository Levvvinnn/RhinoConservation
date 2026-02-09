# main.py — refactored for send abstraction (WiFi or LoRa)
from machine import UART, Pin
import time

COMM_MODE = "wifi"    # "wifi" or "lora"
DEVICE_ID = "RHINO01"
SEND_PERIOD_S = 30    # adjust for LoRa power constraints

# GPS UART (existing)
uart_gps = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5), timeout=1000)

# LoRa UART stub (adjust pins/baud to your module when available)
uart_lora = UART(0, baudrate=57600, tx=Pin(0), rx=Pin(1), timeout=2000)

LED = Pin("LED", Pin.OUT)

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
    if len(parts) < 10:
        return None
    if parts[0] != "$GPGGA":
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
        "alt_m": parts[9] or None
    }

def format_payload(lat, lon, extra=None):
    if extra is None:
        extra = {}
    # Minimal compact CSV payload for LoRa: DEVICE,lat,lon,alive_flag,batt
    alive = extra.get("alive", 1)   
    batt = extra.get("battery_v", "")
    return "{},{:.5f},{:.5f},{},{}".format(DEVICE_ID, lat, lon, alive, batt)

def send_wifi(payload, wlan=None):
    print("WIFI SEND (simulated):", payload)
    return True

def send_lora(payload):
    """
    Send an ASCII packet to the LoRa module via UART.
    Currently a stub: writes to uart_lora. When hardware is present, validate module API.
    """
    try:
        if not payload.endswith("\n"):
            payload = payload + "\n"
        uart_lora.write(payload.encode("ascii"))
        LED.on()
        time.sleep(0.05)
        LED.off()
        print("LoRa send:", payload.strip())
        return True
    except Exception as e:
        print("LoRa send error:", e)
        return False

def main():
    last_send = 0
    print("Starting main loop (COMM_MODE={})".format(COMM_MODE))
    while True:
        line = uart_gps.readline()
        if not line:
            time.sleep(0.1)
            continue
        try:
            s = line.decode("ascii").strip()
        except:
            continue

        if s.startswith("$GPGGA"):
            data = parse_gga(s)
            if data:
                lat = data["lat"]
                lon = data["lon"]
                now = time.time()
                if now - last_send >= SEND_PERIOD_S:
                    payload = format_payload(lat, lon, {
                        "sats": data.get("sats"),
                        "hdop": data.get("hdop"),
                        "alt_m": data.get("alt_m"),
                        # alive flag/battery will be added when sensors/ADC present
                    })
                    if COMM_MODE == "wifi":
                        send_wifi(payload)
                    else:
                        send_lora(payload)
                    last_send = now

        LED.toggle()
        time.sleep(0.5)

if __name__ == "__main__":
    main()
