from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class DriverFrame:
    x: float
    y: float
    speed: int
    gear: int
    throttle: int
    brake: bool
    drs: int
    dist: float
    lap: int

@dataclass
class Frame:
    t: float
    status: int
    lap: int
    drivers: Dict[str, DriverFrame] = field(default_factory=dict)

@dataclass
class DriverMetadata:
    color: str
    name: str
    abb: str

@dataclass
class SessionData:
    frames: List[Frame]
    driver_metadata: Dict[str, DriverMetadata]
    total_laps: int
    track_status_raw: List[dict]
