import json
from src.utils.models import Frame, DriverFrame, DriverMetadata
from typing import List, Dict

def build_race_context(
    frame: Frame, 
    driver_metadata: dict, 
    sorted_drivers: list,
    selected_driver: str = None,
    frames_history: List[Frame] = None,
    total_laps: int = None
) -> str:
    """
    Constructs a comprehensive JSON string representing the current race state.
    Includes telemetry, lap history, tire status, and strategic insights.
    """
    
    # 1. General Race Status
    context = {
        "current_state": {
            "time": round(frame.t, 1),
            "lap": frame.lap,
            "total_laps": total_laps or "Unknown",
            "track_status": _get_track_status_name(frame.status),
            "selected_driver": selected_driver
        },
        "leaderboard": [],
        "selected_driver_telemetry": None,
        "recent_history": None,
        "battle_analysis": []
    }
    
    # 2. Build Leaderboard with Enhanced Data
    leader_dist = sorted_drivers[0][1].dist if sorted_drivers else 0
    
    for i, (drv_id, telemetry) in enumerate(sorted_drivers):
        meta = driver_metadata.get(drv_id)
        name = meta.name if meta else drv_id
        abb = meta.abb if meta else drv_id[:3]
        
        # Gap calculation
        gap = 0.0
        if i > 0:
            dist_delta = leader_dist - telemetry.dist
            speed_ms = max(1, telemetry.speed) / 3.6
            gap = round(dist_delta / speed_ms, 1)
        
        # Interval to car ahead
        interval = 0.0
        if i > 0:
            ahead_dist = sorted_drivers[i-1][1].dist
            dist_delta = ahead_dist - telemetry.dist
            speed_ms = max(1, telemetry.speed) / 3.6
            interval = round(dist_delta / speed_ms, 1)
            
        entry = {
            "pos": i + 1,
            "driver": name,
            "abb": abb,
            "compound": telemetry.compound,
            "gap_leader": gap,
            "interval": interval,
            "lap": telemetry.lap,
            "speed": telemetry.speed,
            "drs_status": "ACTIVE" if telemetry.drs > 0 else "AVAILABLE" if telemetry.drs == 0 else "CLOSED"
        }
        context["leaderboard"].append(entry)
    
    # 3. Selected Driver Detailed Telemetry
    if selected_driver and selected_driver in frame.drivers:
        tel = frame.drivers[selected_driver]
        meta = driver_metadata.get(selected_driver, DriverMetadata(color="white", name=selected_driver, abb=selected_driver[:3]))
        
        context["selected_driver_telemetry"] = {
            "driver": meta.name,
            "speed": tel.speed,
            "throttle": tel.throttle,
            "brake": "ON" if tel.brake else "OFF",
            "gear": tel.gear,
            "drs": tel.drs,
            "compound": tel.compound,
            "current_lap": tel.lap,
            "position": _get_position(selected_driver, sorted_drivers)
        }
    
    # 4. Recent History Analysis (last 5 laps if available)
    if frames_history and selected_driver:
        history = _analyze_recent_laps(frames_history, selected_driver, current_lap=frame.lap)
        if history:
            context["recent_history"] = history
    
    # 5. Battle Analysis (cars within 3 seconds)
    if selected_driver:
        battles = _find_nearby_battles(sorted_drivers, selected_driver, driver_metadata)
        if battles:
            context["battle_analysis"] = battles
    
    return json.dumps(context, indent=2)


def _get_track_status_name(status_code: int) -> str:
    """Convert status code to readable name"""
    status_map = {
        1: "GREEN",
        2: "YELLOW",
        4: "SAFETY_CAR",
        5: "RED_FLAG",
        6: "VSC",
        7: "VSC_ENDING"
    }
    return status_map.get(status_code, f"CODE_{status_code}")


def _get_position(driver_id: str, sorted_drivers: list) -> int:
    """Get driver's current position"""
    for i, (drv_id, _) in enumerate(sorted_drivers):
        if drv_id == driver_id:
            return i + 1
    return 0


def _analyze_recent_laps(frames: List[Frame], driver_id: str, current_lap: int, lookback: int = 5) -> Dict:
    """Analyze recent lap performance and tire degradation"""
    if not frames or current_lap < 2:
        return None
    
    # Find lap times for the last N laps
    lap_data = {}
    for frame in frames:
        if driver_id in frame.drivers:
            lap = frame.drivers[driver_id].lap
            if current_lap - lookback <= lap <= current_lap:
                if lap not in lap_data:
                    lap_data[lap] = {
                        'times': [],
                        'compound': frame.drivers[driver_id].compound,
                        'speeds': []
                    }
                lap_data[lap]['times'].append(frame.t)
                lap_data[lap]['speeds'].append(frame.drivers[driver_id].speed)
    
    # Calculate approximate lap times
    lap_times = []
    for lap_num in sorted(lap_data.keys()):
        if len(lap_data[lap_num]['times']) > 10:  # Ensure we have enough data
            lap_time = max(lap_data[lap_num]['times']) - min(lap_data[lap_num]['times'])
            avg_speed = sum(lap_data[lap_num]['speeds']) / len(lap_data[lap_num]['speeds'])
            lap_times.append({
                'lap': lap_num,
                'time': round(lap_time, 2),
                'avg_speed': round(avg_speed, 1),
                'compound': lap_data[lap_num]['compound']
            })
    
    if not lap_times:
        return None
    
    # Calculate degradation trend
    degradation = "STABLE"
    if len(lap_times) >= 3:
        recent_times = [lt['time'] for lt in lap_times[-3:]]
        if all(recent_times[i] < recent_times[i+1] for i in range(len(recent_times)-1)):
            degradation = "DEGRADING"
        elif all(recent_times[i] > recent_times[i+1] for i in range(len(recent_times)-1)):
            degradation = "IMPROVING"
    
    return {
        "last_5_laps": lap_times[-5:],
        "tire_trend": degradation,
        "current_compound": lap_times[-1]['compound'] if lap_times else "UNKNOWN"
    }


def _find_nearby_battles(sorted_drivers: list, selected_driver: str, driver_metadata: dict, gap_threshold: float = 3.0) -> List[Dict]:
    """Find cars within gap_threshold seconds"""
    battles = []
    selected_idx = None
    selected_dist = None
    
    # Find selected driver
    for i, (drv_id, tel) in enumerate(sorted_drivers):
        if drv_id == selected_driver:
            selected_idx = i
            selected_dist = tel.dist
            break
    
    if selected_idx is None:
        return battles
    
    # Check car ahead
    if selected_idx > 0:
        ahead_drv_id, ahead_tel = sorted_drivers[selected_idx - 1]
        dist_delta = ahead_tel.dist - selected_dist
        speed_ms = max(1, ahead_tel.speed) / 3.6
        gap = dist_delta / speed_ms
        
        if gap <= gap_threshold:
            meta = driver_metadata.get(ahead_drv_id)
            battles.append({
                "position": "ahead",
                "driver": meta.name if meta else ahead_drv_id,
                "abb": meta.abb if meta else ahead_drv_id[:3],
                "gap": round(gap, 2),
                "compound": ahead_tel.compound
            })
    
    # Check car behind
    if selected_idx < len(sorted_drivers) - 1:
        behind_drv_id, behind_tel = sorted_drivers[selected_idx + 1]
        dist_delta = selected_dist - behind_tel.dist
        speed_ms = max(1, behind_tel.speed) / 3.6
        gap = dist_delta / speed_ms
        
        if gap <= gap_threshold:
            meta = driver_metadata.get(behind_drv_id)
            battles.append({
                "position": "behind",
                "driver": meta.name if meta else behind_drv_id,
                "abb": meta.abb if meta else behind_drv_id[:3],
                "gap": round(gap, 2),
                "compound": behind_tel.compound
            })
    
    return battles
