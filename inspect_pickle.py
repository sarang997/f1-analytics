import pickle
import pandas as pd
import numpy as np

FILE = "data/processed/2024_Austria_Sprint_processed.pkl"

try:
    with open(FILE, 'rb') as f:
        data = pickle.load(f)
        
    frames = data.frames
    print(f"Total Frames: {len(frames)}")
    
    if not frames:
        print("No frames found.")
        exit()
        
    first_frame = frames[0]
    
    # Inspect ALL drivers
    drivers = list(first_frame.drivers.keys())
    print(f"Drivers found: {drivers}")
    
    for drv in drivers:
        xs = []
        spd = []
        
        for f in frames:
            if drv in f.drivers:
                d = f.drivers[drv]
                xs.append(d.x)
                spd.append(d.speed)
                
        # Analyze
        x_arr = np.array(xs)
        s_arr = np.array(spd)
        
        dx = np.diff(x_arr)
        ds = np.diff(s_arr)
        
        # Count frames where Speed changes but Pos is static
        zombie = np.sum((dx == 0) & (ds != 0))
        
        print(f"Driver {drv}: Total {len(xs)}, Static Pos {np.sum(dx==0)}, Zombie Frames {zombie}")
        
        if zombie > 100:
             print(f"!!! Driver {drv} is a ZOMBIE (Moving but stuck on map) !!!")
             
        # Check Bounds
        print(f"  Range X: {np.min(x_arr):.2f} to {np.max(x_arr):.2f}")
        print(f"  Range Y: {np.min(y_arr):.2f} to {np.max(y_arr):.2f}")
        
except Exception as e:
    print(f"Error: {e}")
