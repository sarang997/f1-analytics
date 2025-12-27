import os
import fastf1
import pandas as pd
import numpy as np
import pickle
from scipy.interpolate import interp1d
import logging
from src.utils.config import CACHE_DIR, PROCESSED_DIR
from src.utils.models import SessionData, Frame, DriverFrame, DriverMetadata

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup Caching
fastf1.Cache.enable_cache(CACHE_DIR)

class DataManager:
    @staticmethod
    def get_cache_filename(year, gp, session_type):
        """Generates a consistent filename for the computed pickle file."""
        return f"{year}_{gp}_{session_type}_processed.pkl"

    @classmethod
    def load_and_process_session(cls, year, gp, session_type, refresh_data=False):
        """
        Loads an F1 session, processes telemetry into a uniform timeline,
        and returns a structures SessionData object.
        """
        cache_file = os.path.join(PROCESSED_DIR, cls.get_cache_filename(year, gp, session_type))

        if os.path.exists(cache_file) and not refresh_data:
            logger.info(f"Loading pre-computed data from {cache_file}...")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)

        logger.info(f"Computing telemetry for {year} {gp} {session_type}...")
        session = fastf1.get_session(year, gp, session_type)
        session.load()

        # Get track status
        track_status_raw = session.track_status

        # Get all drivers
        drivers = session.drivers
        
        all_telemetry = {}
        min_time = float('inf')
        max_time = float('-inf')

        for drv in drivers:
            drv_info = session.get_driver(drv)
            team_color = drv_info['TeamColor'] or "FFFFFF"
            
            # Get all telemetry for this driver
            driver_laps = session.laps.pick_drivers(drv)
            if len(driver_laps) == 0: continue
                
            telemetry = driver_laps.get_telemetry()
            if len(telemetry) == 0: continue
                
            # Accurately map LapNumber
            lap_mapping = driver_laps[['Time', 'LapNumber']].rename(columns={'Time': 'SessionTime'})
            telemetry = telemetry.sort_values('SessionTime')
            lap_mapping = lap_mapping.sort_values('SessionTime')
            
            # Use forward direction as fixed previously
            telemetry = pd.merge_asof(telemetry, lap_mapping, on='SessionTime', direction='forward')
            telemetry['LapNumber'] = telemetry['LapNumber'].ffill().bfill().fillna(1)
                
            telemetry['TimeSecs'] = telemetry['SessionTime'].dt.total_seconds()
            min_time = min(min_time, telemetry['TimeSecs'].min())
            max_time = max(max_time, telemetry['TimeSecs'].max())
            
            all_telemetry[drv] = {
                'telemetry': telemetry,
                'color': f"#{team_color}",
                'name': drv_info['FullName'],
                'abb': drv_info['Abbreviation']
            }

        # Create uniform timeline (10Hz)
        dt = 0.1
        common_times = np.arange(min_time, max_time + dt, dt)
        
        # Track status mapping
        ts_mapping = track_status_raw[['Time', 'Status']].rename(columns={'Time': 'SessionTime'})
        ts_mapping['TimeSecs'] = ts_mapping['SessionTime'].dt.total_seconds()
        ts_mapping = ts_mapping.sort_values('TimeSecs')
        
        f_status = interp1d(ts_mapping['TimeSecs'], ts_mapping['Status'], kind='nearest', 
                             bounds_error=False, fill_value=(ts_mapping['Status'].iloc[0], ts_mapping['Status'].iloc[-1]))
        common_statuses = f_status(common_times).astype(int)

        # Pre-calculate interpolation curves
        driver_curves = {}
        for drv, data in all_telemetry.items():
            tel = data['telemetry']
            t_min, t_max = tel['TimeSecs'].min(), tel['TimeSecs'].max()
            
            funcs = {
                'x': interp1d(tel['TimeSecs'], tel['X'], kind='linear', fill_value="extrapolate"),
                'y': interp1d(tel['TimeSecs'], tel['Y'], kind='linear', fill_value="extrapolate"),
                'speed': interp1d(tel['TimeSecs'], tel['Speed'], kind='linear', fill_value="extrapolate"),
                'gear': interp1d(tel['TimeSecs'], tel['nGear'], kind='nearest', fill_value="extrapolate"),
                'throttle': interp1d(tel['TimeSecs'], tel['Throttle'], kind='linear', fill_value="extrapolate"),
                'brake': interp1d(tel['TimeSecs'], tel['Brake'], kind='linear', fill_value="extrapolate"),
                'dist': interp1d(tel['TimeSecs'], tel['Distance'], kind='linear', fill_value="extrapolate"),
                'lap': interp1d(tel['TimeSecs'], tel['LapNumber'], kind='nearest', fill_value="extrapolate"),
                'drs': interp1d(tel['TimeSecs'], tel['DRS'], kind='nearest', fill_value="extrapolate")
            }
            
            driver_curves[drv] = {
                'x': funcs['x'](common_times),
                'y': funcs['y'](common_times),
                'speed': funcs['speed'](common_times).astype(int),
                'gear': funcs['gear'](common_times).astype(int),
                'throttle': funcs['throttle'](common_times).astype(int),
                'brake': (funcs['brake'](common_times) > 5).astype(bool), 
                'dist': funcs['dist'](common_times),
                'lap': funcs['lap'](common_times).astype(int),
                'drs': funcs['drs'](common_times).astype(int),
                't_min': t_min,
                't_max': t_max
            }

        frames = []
        for i, t in enumerate(common_times):
            frame_obj = Frame(t=float(t), status=int(common_statuses[i]), lap=0)
            max_lap = 0
            for drv, curves in driver_curves.items():
                if t < curves['t_min'] or t > curves['t_max']:
                    continue
                    
                frame_obj.drivers[drv] = DriverFrame(
                    x=float(curves['x'][i]),
                    y=float(curves['y'][i]),
                    speed=int(curves['speed'][i]),
                    gear=int(curves['gear'][i]),
                    throttle=int(curves['throttle'][i]),
                    brake=bool(curves['brake'][i]),
                    drs=int(curves['drs'][i]),
                    dist=float(curves['dist'][i]),
                    lap=int(curves['lap'][i])
                )
                max_lap = max(max_lap, frame_obj.drivers[drv].lap)
            
            frame_obj.lap = max_lap
            frames.append(frame_obj)

        processed_data = SessionData(
            frames=frames,
            driver_metadata={drv: DriverMetadata(color=data['color'], name=data['name'], abb=data['abb']) 
                               for drv, data in all_telemetry.items()},
            total_laps=int(session.laps['LapNumber'].max()) if not session.laps.empty else 0,
            track_status_raw=track_status_raw.to_dict('records') if not track_status_raw.empty else []
        )

        logger.info(f"Saving processed data to {cache_file}...")
        with open(cache_file, 'wb') as f:
            pickle.dump(processed_data, f)

        return processed_data
