import json
from src.utils.models import Frame, DriverFrame, DriverMetadata

def build_race_context(frame: Frame, driver_metadata: dict, sorted_drivers: list) -> str:
    """
    Constructs a JSON string representing the current race state.
    """
    
    # 1. General Status
    context = {
        "time": round(frame.t, 1),
        "lap": frame.lap,
        "track_status": frame.status,
        "leaderboard": []
    }
    
    # 2. Leaderboard State
    # sorted_drivers is list of (driver_id, telemetry)
    leader_dist = sorted_drivers[0][1].dist if sorted_drivers else 0
    
    for i, (drv_id, telemetry) in enumerate(sorted_drivers):
        meta = driver_metadata.get(drv_id)
        name = meta.name if meta else drv_id
        
        # Gap calc
        gap = 0.0
        if i > 0:
            dist_delta = leader_dist - telemetry.dist
            speed_ms = max(1, telemetry.speed) / 3.6
            gap = round(dist_delta / speed_ms, 1)
            
        entry = {
            "pos": i + 1,
            "driver": name,
            "compound": telemetry.compound,
            "gap_leader": gap,
            "lap": telemetry.lap,
            "last_lap_time": "N/A" # We assume instantaneous state for now
        }
        context["leaderboard"].append(entry)
        
    return json.dumps(context)
