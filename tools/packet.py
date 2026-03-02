
import struct

def crc8(data: bytes, poly=0x07, init=0x00):
    crc = init
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) & 0xFF) ^ poly
            else:
                crc = (crc << 1) & 0xFF
    return crc & 0xFF

# Pack short telemetry into 12 bytes
def pack_short(lat, lon, batt_pct, flags=0, version=1):
    lat_i = int(round(lat * 1e7))
    lon_i = int(round(lon * 1e7))
    # > = big-endian, B=uint8, i=int32
    header = struct.pack(">BBiiB", version, flags, lat_i, lon_i, batt_pct)
    c = crc8(header)
    return header + bytes([c])

# Unpack and validate
def unpack_short(buf):
    if len(buf) != 12:
        raise ValueError("Invalid length")
    header = buf[:11]
    crc = buf[11]
    if crc8(header) != crc:
        raise ValueError("CRC mismatch")
    version, flags, lat_i, lon_i, batt = struct.unpack(">BBiiB", header)
    return {
        "version": version,
        "flags": flags,
        "lat": lat_i / 1e7,
        "lon": lon_i / 1e7,
        "batt": batt
    }

# Quick test
if __name__ == "__main__":
    p = pack_short(-25.123456, 31.987654, 87, flags=1)
    print("hex:", p.hex())
    print("decoded:", unpack_short(p))