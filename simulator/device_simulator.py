"""Lightweight device telemetry generator.

Produces JSON packets representing rhino tracker telemetry and sends
them to a gateway HTTP endpoint.

This module is intentionally standalone and configurable for demo/testing.
"""
from __future__ import annotations
import time
import hashlib
import json
import random
from datetime import datetime, timezone
from typing import Dict, Iterator, Optional


def compute_checksum(packet: Dict) -> str:
    """Compute a short checksum for the packet (8 hex chars).

    This is a convenience validation token, not a security feature.
    """
    s = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]


class DeviceSimulator:
    def __init__(self, rhino_id: str, start_lat: float, start_lon: float, interval: float = 2.0):
        self.rhino_id = rhino_id
        self.lat = start_lat
        self.lon = start_lon
        self.interval = interval

    def _tick(self):
        # small random movement
        self.lat += random.uniform(-0.0003, 0.0003)
        self.lon += random.uniform(-0.0003, 0.0003)

    def generate_packet(self) -> Dict:
        """Generate a single telemetry packet dict (without checksum).
        Caller may add checksum with `compute_checksum`.
        """
        self._tick()
        battery = max(0, min(100, int(100 - random.random() * 0.5)))
        motion = random.random() < 0.7
        heart_rate = random.randint(30, 80) if motion else random.randint(24, 50)
        status = "active" if battery > 10 else "low_battery"

        packet = {
            "rhino_id": self.rhino_id,
            "device_id": f"dev-{self.rhino_id}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": round(self.lat, 6),
            "longitude": round(self.lon, 6),
            "battery": battery,
            "motion": bool(motion),
            "heart_rate": heart_rate,
            "status": status,
        }
        return packet


def packet_stream(rhino_id: str, start_lat: float, start_lon: float, interval: float = 2.0) -> Iterator[Dict]:
    sim = DeviceSimulator(rhino_id, start_lat, start_lon, interval)
    while True:
        pkt = sim.generate_packet()
        pkt["checksum"] = compute_checksum(pkt)
        yield pkt
        time.sleep(interval)


if __name__ == "__main__":
    # quick demo: print 5 packets
    stream = packet_stream("RHINO-TEST", -1.2921, 36.8219, interval=1.0)
    for _ in range(5):
        print(next(stream))
