import struct

def crc8(data):
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def decode_packet(packet_bytes):
    if len(packet_bytes) != 12:
        raise ValueError("Packet must be 12 bytes")

    version = packet_bytes[0]
    flags = packet_bytes[1]

    lat_int = struct.unpack(">i", packet_bytes[2:6])[0]
    lon_int = struct.unpack(">i", packet_bytes[6:10])[0]

    battery = packet_bytes[10]
    crc_received = packet_bytes[11]

    crc_calculated = crc8(packet_bytes[:11])

    if crc_received != crc_calculated:
        raise ValueError("CRC mismatch")

    latitude = lat_int / 1e7
    longitude = lon_int / 1e7

    return {
        "version": version,
        "flags": flags,
        "latitude": latitude,
        "longitude": longitude,
        "battery": battery
    }


if __name__ == "__main__":
    # Example packet
    example_hex = "0105FEA40FE0012F727E579A"

    packet = bytes.fromhex(example_hex)

    decoded = decode_packet(packet)

    print("Decoded telemetry:")
    print(decoded)