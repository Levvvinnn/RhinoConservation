from machine import UART, Pin
import time
import json

SEND_PERIOD_S = 10  # seconds between uploads
LED = Pin("LED", Pin.OUT)
DEBUG = True  # Set to False to disable print statements

# LoRa UART settings
LORA_UART_ID = 0
LORA_BAUD = 57600
LORA_TX_PIN = 0   # GP0 on Pico (change if needed)
LORA_RX_PIN = 1   # GP1 on Pico (change if needed)

gps_uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5), timeout=1000)

lora = UART(LORA_UART_ID, baudrate=LORA_BAUD, tx=Pin(LORA_TX_PIN), rx=Pin(LORA_RX_PIN), timeout=1000)

def dmm_to_deg(dmm, is_lat, hemi):
    """
    Convert degrees-minutes format to decimal degrees.
    
    Args:
        dmm (str): Degrees and minutes as string (e.g., "1234.56")
        is_lat (bool): True for latitude, False for longitude
        hemi (str): Hemisphere ("N", "S", "E", "W")
    
    Returns:
        float or None: Decimal degrees or None if invalid
    """
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
    """
    Parse GPGGA NMEA sentence for GPS data.
    
    Args:
        sentence (str): NMEA sentence starting with $GPGGA
    
    Returns:
        dict or None: Parsed GPS data or None if invalid/no fix
    """
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

def format_payload_for_lora(lat, lon, extra=None):
    """
    Format GPS data as JSON payload for LoRa transmission.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        extra (dict): Additional data (sats, hdop, alt_m)
    
    Returns:
        str: JSON string payload
    """
    if extra is None:
        extra = {}
    payload = {
        "timestamp": time.time(),
        "lat": lat,
        "lon": lon,
        "sats": extra.get("sats", ""),
        "hdop": extra.get("hdop", ""),
        "alt_m": extra.get("alt_m", "")
    }
    return json.dumps(payload) + "\n"

def send_lora(payload_str):
    """
    Send payload via LoRa UART.
    
    Args:
        payload_str (str): Data to send
    """
    try:
        if DEBUG:
            print("LoRa send:", payload_str.strip())
        lora.write(payload_str.encode("utf-8"))
    except Exception as e:
        if DEBUG:
            print("LoRa send error:", e)

def main():
    """
    Main loop: Read GPS data, parse GPGGA, send via LoRa periodically.
    """
    last_send = 0
    if DEBUG:
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

        if DEBUG:
            print(s)

        if s.startswith("$GPGGA"):
            data = parse_gga(s)
            if data:
                lat = data["lat"]
                lon = data["lon"]
                if DEBUG:
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
                    LED.toggle()  # Heartbeat on successful send

        time.sleep(0.5)

if __name__ == "__main__":
    main()