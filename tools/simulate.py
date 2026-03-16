import random
import time

lat = -25.123456
lon = 31.987654

while True:
    lat += random.uniform(-0.0001, 0.0001)
    lon += random.uniform(-0.0001, 0.0001)

    data = {
        "rhino_id": "RHINO001",
        "latitude": lat,
        "longitude": lon,
        "battery": random.randint(60, 100),
        "status": "active"
    }

    print(data)

    time.sleep(3)