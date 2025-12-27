import argparse
import arcade
import sys
from src.processor.data_manager import DataManager
from src.ui.app import F1Dashboard

def main():
    parser = argparse.ArgumentParser(description="F1 Telemetry Replay Dashboard")
    parser.add_argument("year", type=int, help="Year of the session (e.g., 2024)")
    parser.add_argument("gp", type=str, help="Grand Prix name (e.g., 'Austria', 'Monaco')")
    parser.add_argument("session", type=str, help="Session type (e.g., 'R', 'Q', 'FP1')")
    parser.add_argument("--refresh", action="store_true", help="Force recompute of telemetry data")
    
    args = parser.parse_args()

    try:
        # 1. Ensure data is processed and cached
        # This will either load from pickle or compute via FastF1
        print(f"--- F1 Telemetry Dashboard Orchestrator ---")
        print(f"Target: {args.year} {args.gp} {args.session}")
        
        # We don't actually need the return value here if we just want to pre-cache,
        # but the Dashboard will also call this and benefit from the cache.
        # Calling it here ensures the "heavy lifting" is done before the Window opens.
        DataManager.load_and_process_session(args.year, args.gp, args.session, refresh_data=args.refresh)

        # 2. Launch the Dashboard
        print("Launching dashboard...")
        window = F1Dashboard(args.year, args.gp, args.session)
        arcade.run()
        
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
