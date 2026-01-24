"""Proactive race engineer that monitors race state and generates alerts"""

import logging
from typing import List, Dict, Optional
from src.utils.models import Frame, DriverFrame

logger = logging.getLogger(__name__)


class ProactiveEngineer:
    """
    Monitors race conditions and generates proactive alerts/suggestions
    Examples: tire degradation warnings, undercut opportunities, VSC pit windows
    """
    
    def __init__(self, data_manager=None):
        self.data_manager = data_manager
        
        # Alert cooldowns (prevent spam)
        self.alert_cooldowns: Dict[str, int] = {}  # {alert_type: last_lap_sent}
        self.cooldown_laps = 5  # Wait 5 laps before repeating same alert type
        
        # State tracking
        self.last_analyzed_lap = 0
        self.tire_warning_sent = False
        self.undercut_warning_sent = False
        
    def analyze_frame(self, frame: Frame, selected_driver: str, sorted_drivers: list, frames_history: List[Frame] = None) -> List[str]:
        """
        Analyzes current frame and returns list of alert messages
        
        Returns:
            List of alert strings to display to user
        """
        alerts = []
        current_lap = frame.lap
        
        # Only analyze once per lap (avoid spam)
        if current_lap == self.last_analyzed_lap:
            return alerts
        
        self.last_analyzed_lap = current_lap
        
        # Skip early laps (need data for trends)
        if current_lap < 3:
            return alerts
        
        # Check tire degradation
        if self._should_send_alert("tire_deg", current_lap):
            tire_alert = self._check_tire_degradation(frame, selected_driver, frames_history)
            if tire_alert:
                alerts.append(tire_alert)
                self.alert_cooldowns["tire_deg"] = current_lap
        
        # Check undercut risk
        if self._should_send_alert("undercut", current_lap):
            undercut_alert = self._check_undercut_risk(frame, selected_driver, sorted_drivers, frames_history)
            if undercut_alert:
                alerts.append(undercut_alert)
                self.alert_cooldowns["undercut"] = current_lap
        
        # Check track status changes (VSC, Safety Car)
        status_alert = self._check_track_status_change(frame)
        if status_alert:
            alerts.append(status_alert)
        
        # Check DRS opportunities
        if self._should_send_alert("drs", current_lap):
            drs_alert = self._check_drs_opportunity(frame, selected_driver, sorted_drivers)
            if drs_alert:
                alerts.append(drs_alert)
                self.alert_cooldowns["drs"] = current_lap
        
        return alerts
    
    def _should_send_alert(self, alert_type: str, current_lap: int) -> bool:
        """Check if enough laps have passed since last alert of this type"""
        last_sent = self.alert_cooldowns.get(alert_type, 0)
        return current_lap - last_sent >= self.cooldown_laps
    
    def _check_tire_degradation(self, frame: Frame, driver_id: str, frames_history: List[Frame]) -> Optional[str]:
        """Check if tires are degrading rapidly"""
        if not frames_history or driver_id not in frame.drivers:
            return None
        
        current_lap = frame.lap
        
        # Analyze last 3 laps
        lap_data = {}
        for f in frames_history:
            if driver_id in f.drivers:
                lap = f.drivers[driver_id].lap
                if current_lap - 3 <= lap <= current_lap:
                    if lap not in lap_data:
                        lap_data[lap] = {'times': [], 'compound': f.drivers[driver_id].compound}
                    lap_data[lap]['times'].append(f.t)
        
        # Calculate lap times
        lap_times = []
        for lap_num in sorted(lap_data.keys()):
            if len(lap_data[lap_num]['times']) > 10:
                lap_time = max(lap_data[lap_num]['times']) - min(lap_data[lap_num]['times'])
                lap_times.append({'lap': lap_num, 'time': lap_time})
        
        if len(lap_times) < 3:
            return None
        
        # Check if last 3 laps show increasing times (degradation)
        times = [lt['time'] for lt in lap_times[-3:]]
        
        # Simple degradation detection: each lap slower than previous
        if all(times[i] < times[i+1] for i in range(len(times)-1)):
            # Calculate degradation rate
            deg_rate = round((times[-1] - times[0]) / 2, 2)  # Average per lap
            
            if deg_rate > 0.3:  # More than 0.3s per lap = significant
                compound = frame.drivers[driver_id].compound
                return f"⚠️ TIRE DEG: Losing {deg_rate}s/lap on {compound}. Consider box soon."
        
        return None
    
    def _check_undercut_risk(self, frame: Frame, driver_id: str, sorted_drivers: list, frames_history: List[Frame]) -> Optional[str]:
        """Check if car behind is on fresher tires and closing"""
        if not sorted_drivers or driver_id not in frame.drivers:
            return None
        
        # Find driver position
        driver_idx = None
        for i, (drv_id, tel) in enumerate(sorted_drivers):
            if drv_id == driver_id:
                driver_idx = i
                break
        
        if driver_idx is None or driver_idx == len(sorted_drivers) - 1:
            return None  # No car behind
        
        # Check car behind
        behind_drv_id, behind_tel = sorted_drivers[driver_idx + 1]
        our_tel = frame.drivers[driver_id]
        
        # Calculate gap
        dist_delta = our_tel.dist - behind_tel.dist
        speed_ms = max(1, behind_tel.speed) / 3.6
        gap = dist_delta / speed_ms
        
        # Alert if gap < 5s and different tire compound (likely fresher)
        if gap < 5.0 and our_tel.compound != behind_tel.compound:
            return f"⚠️ UNDERCUT RISK: Car behind on {behind_tel.compound}, gap {round(gap, 1)}s"
        
        return None
    
    def _check_track_status_change(self, frame: Frame) -> Optional[str]:
        """Alert on VSC, Safety Car, or other important track status changes"""
        status_map = {
            4: "🟡 SAFETY CAR deployed! Pit window open!",
            5: "🔴 RED FLAG! Session stopped.",
            6: "🟡 VSC deployed! Consider cheap pit stop!",
            7: "🟢 VSC ending soon."
        }
        
        # Only alert on important statuses (not green/yellow)
        if frame.status in status_map:
            return status_map[frame.status]
        
        return None
    
    def _check_drs_opportunity(self, frame: Frame, driver_id: str, sorted_drivers: list) -> Optional[str]:
        """Check if DRS is available and there's a car to attack"""
        if not sorted_drivers or driver_id not in frame.drivers:
            return None
        
        our_tel = frame.drivers[driver_id]
        
        # Only alert if DRS is available (not already active)
        if our_tel.drs != 0:
            return None
        
        # Find car ahead
        driver_idx = None
        for i, (drv_id, tel) in enumerate(sorted_drivers):
            if drv_id == driver_id:
                driver_idx = i
                break
        
        if driver_idx is None or driver_idx == 0:
            return None  # We're leading or not found
        
        ahead_drv_id, ahead_tel = sorted_drivers[driver_idx - 1]
        
        # Calculate gap
        dist_delta = ahead_tel.dist - our_tel.dist
        speed_ms = max(1, our_tel.speed) / 3.6
        gap = dist_delta / speed_ms
        
        # Alert if within DRS range (< 1.0s typically)
        if gap < 1.2:
            return f"💨 DRS available! {round(gap, 1)}s to car ahead, push!"
        
        return None
