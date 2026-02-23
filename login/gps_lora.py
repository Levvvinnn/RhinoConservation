# main_lora.py  (Micropython for Pico)
from machine import UART, Pin
import time

# ------------ CONFIG -------------
SEND_PERIOD_S = 10  # seconds between uploads
LED = Pin("LED", Pin.OUT)

# LoRa UART settings - CHANGE THESE to your module's pins/baud
# Example uses UART(0) with TX=GP0, RX=GP1 at 57600 as in research notes.
LORA_UART_ID = 0
LORA_BAUD = 57600
LORA_TX_PIN = 0   # GP0 on Pico (change if needed)
LORA_RX_PIN = 1   # GP1 on Pico (change if needed)
# ---------------------------------

# GPS UART (same as your working code)
gps_uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5), timeout=1000)

# LoRa UART (used to send payloads to radio)
lora = UART(LORA_UART_ID, baudrate=LORA_BAUD, tx=Pin(LORA_TX_PIN), rx=Pin(LORA_RX_PIN), timeout=1000)

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
        # Too short
        return None
    if parts[0] != "$GPGGA":
        return None
    fix = parts[6]
    if fix == "0" or fix == "":
        # no GPS fix yet
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

def format_payload_for_lora(lat, lon, extra=None):
    # Compact CSV: lat,lon,sats,hdop,alt
    # Keep it short to reduce airtime. Empty fields become ""
    if extra is None:
        extra = {}
    sats = extra.get("sats", "")
    hdop = extra.get("hdop", "")
    alt = extra.get("alt_m", "")
    return "{:.6f},{:.6f},{},{},{}\n".format(lat, lon, sats or "", hdop or "", alt or "")

def send_lora(payload_str):
    # Write to LoRa UART. The exact command depends on your LoRa module.
    # Many UART-attached LoRa radios accept raw bytes; others require AT commands.
    # If your module requires an AT command wrapper, change this function accordingly.
    try:
        print("LoRa send:", payload_str.strip())
        lora.write(payload_str.encode("utf-8"))
    except Exception as e:
        print("LoRa send error:", e)

def main():
    last_send = 0
    print("Starting GPS loop (COMM_MODE = LoRa)")
    while True:
        line = gps_uart.readline()
        if not line:
            time.sleep(0.1)
            continue
        try:
            s = line.decode("ascii", errors="ignore").strip()
        except:
            continue

        print(s)  # keeps the same terminal output you had

        if s.startswith("$GPGGA"):
            data = parse_gga(s)
            if data:
                lat = data["lat"]
                lon = data["lon"]
                print("GPS FIX:", lat, lon)
                now = time.time()
                if now - last_send >= SEND_PERIOD_S:
                    payload = format_payload_for_lora(lat, lon, {
                        "sats": data.get("sats"),
                        "hdop": data.get("hdop"),
                        "alt_m": data.get("alt_m")
                    })
                    send_lora(payload)
                    last_send = now

        # little heartbeat so you know it's alive
        LED.toggle()
        time.sleep(0.5)

if __name__ == "__main__":
    main()