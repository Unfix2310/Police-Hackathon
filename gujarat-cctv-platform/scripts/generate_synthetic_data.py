import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from backend.simulator.synthetic_data_generator import SyntheticDataGenerator
from backend.simulator.camera_registry import get_all_cameras
from backend.simulator.distance_matrix import export_matrix

def generate_cameras_sql(filepath: str):
    cameras = get_all_cameras()
    with open(filepath, 'w') as f:
        f.write("-- Seed data for cameras\n")
        f.write("INSERT INTO cameras (id, name, latitude, longitude, direction_deg, location_type, police_station, district, capabilities, status) VALUES\n")
        
        values = []
        for cam in cameras:
            caps_json = json.dumps(cam['capabilities']).replace("'", "''")
            display_name = cam['display_name'].replace("'", "''")
            values.append(
                f"('{cam['cam_id']}', '{display_name}', {cam['latitude']}, {cam['longitude']}, {cam['direction_deg']}, '{cam['location_type']}', '{cam['police_station']}', '{cam['district']}', '{caps_json}'::jsonb, 'active')"
            )
        f.write(",\n".join(values) + ";\n")

def generate_seed_data_sql(filepath: str):
    with open(filepath, 'w') as f:
        f.write("-- Seed data for roles, users, watchlists\n")
        
        # Roles
        f.write("INSERT INTO roles (id, name, permissions) VALUES\n")
        f.write("('role_operator', 'Operator', '[\"view_alerts\", \"view_cameras\"]'::jsonb),\n")
        f.write("('role_investigator', 'Investigator', '[\"view_alerts\", \"view_cameras\", \"manage_cases\", \"run_queries\"]'::jsonb),\n")
        f.write("('role_command', 'Command', '[\"view_all\", \"manage_users\"]'::jsonb);\n\n")
        
        # Users
        f.write("INSERT INTO users (id, username, password_hash, role_id, badge_number) VALUES\n")
        f.write("('user_1', 'op1', 'hash1', 'role_operator', 'B101'),\n")
        f.write("('user_2', 'inv1', 'hash2', 'role_investigator', 'B201'),\n")
        f.write("('user_3', 'cmd1', 'hash3', 'role_command', 'B301');\n\n")
        
        # Watchlists
        f.write("INSERT INTO watchlists (id, type, name, description) VALUES\n")
        f.write("('wl_1', 'vehicle', 'Stolen Vehicles', 'List of recently stolen vehicles'),\n")
        f.write("('wl_2', 'person', 'Wanted Persons', 'High profile wanted criminals');\n\n")
        
        # Watchlist Items (Scenario 5)
        f.write("INSERT INTO watchlist_items (id, watchlist_id, entity_id, entity_type, attributes, reason) VALUES\n")
        f.write("('wli_1', 'wl_1', NULL, 'vehicle', '{\"license_plate\": \"GJ01XX0000\"}'::jsonb, 'Stolen motorcycle reported on 2026-08-18');\n")

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data for Gujarat CCTV Platform")
    parser.add_argument("--output-dir", type=str, default="data/seed", help="Directory to save output files")
    parser.add_argument("--obs-per-hour", type=int, default=20, help="Observations per hour per camera")
    parser.add_argument("--start-date", type=str, default="2026-08-19", help="Start date (YYYY-MM-DD)")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    start_time = datetime.strptime(args.start_date, "%Y-%m-%d")
    
    print("Generating cameras.sql...")
    generate_cameras_sql(str(out_dir / "cameras.sql"))
    
    print("Generating seed_data.sql...")
    generate_seed_data_sql(str(out_dir / "seed_data.sql"))
    
    print("Generating distance_matrix.json...")
    export_matrix(str(out_dir / "distance_matrix.json"))
    
    print("Generating synthetic observations...")
    gen = SyntheticDataGenerator(start_time)
    obs = gen.generate_all(obs_per_hour_per_cam=args.obs_per_hour)
    
    obs_file = out_dir / "observations.json"
    with open(obs_file, 'w') as f:
        json.dump(obs, f, indent=2)
        
    print(f"Done! Generated {len(obs)} observations.")
    print(f"Files saved to {out_dir}")

if __name__ == "__main__":
    main()
