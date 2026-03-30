from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class RhinoStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    INJURED = "injured"
    MISSING = "missing"


class RhinoSpecies(Enum):
    WHITE = "white"
    BLACK = "black"
    INDIAN = "indian"
    SUMATRAN = "sumatran"
    JAVAN = "javan"


@dataclass
class Location:
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    satellites: Optional[int] = None
    timestamp: Optional[datetime] = None

    def to_dict(self):
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "accuracy": self.accuracy,
            "satellites": self.satellites,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class Rhino:
    id: str
    name: str
    species: str
    collar_id: str
    status: RhinoStatus = RhinoStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    last_seen: Optional[datetime] = None
    health_notes: Optional[str] = None
    current_location: Optional[Location] = None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "species": self.species,
            "collar_id": self.collar_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "health_notes": self.health_notes,
            "current_location": self.current_location.to_dict() if self.current_location else None,
        }
