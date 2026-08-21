import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .camera_registry import get_all_cameras

class SyntheticDataGenerator:
    def __init__(self, start_time: datetime, duration_hours: int = 24):
        self.start_time = start_time
        self.end_time = start_time + timedelta(hours=duration_hours)
        self.cameras = get_all_cameras()
        self.observations: List[Dict[str, Any]] = []
        
        self.vehicle_colors = ["White", "Black", "Silver", "Red", "Blue", "Grey"]
        self.vehicle_types = ["Sedan", "Hatchback", "SUV", "Motorcycle", "Truck", "Van"]
        
    def _random_time(self) -> datetime:
        delta = self.end_time - self.start_time
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return self.start_time + timedelta(seconds=random_seconds)

    def _generate_plate(self) -> str:
        rto = random.choice(["01", "02", "03", "04", "05", "27"])
        chars = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
        nums = f"{random.randint(0, 9999):04d}"
        
        if random.random() < 0.1: # 10% partial read
            idx = random.randint(0, 3)
            nums = nums[:idx] + "_" + nums[idx+1:]
            
        return f"GJ{rto}{chars}{nums}"

    def generate_noise(self, obs_per_hour_per_cam: int = 100):
        total_hours = int((self.end_time - self.start_time).total_seconds() / 3600)
        
        for cam in self.cameras:
            cam_id = cam["cam_id"]
            num_obs = total_hours * obs_per_hour_per_cam
            
            for _ in range(num_obs):
                is_vehicle = random.random() < 0.7
                
                obs = {
                    "id": str(uuid.uuid4()),
                    "camera_id": cam_id,
                    "timestamp": self._random_time().isoformat(),
                    "entity_type": "vehicle" if is_vehicle else "person",
                    "confidence": round(random.uniform(0.70, 0.99), 2),
                }
                
                if is_vehicle:
                    obs["license_plate"] = self._generate_plate()
                    obs["vehicle_color"] = random.choice(self.vehicle_colors)
                    obs["vehicle_type"] = random.choice(self.vehicle_types)
                else:
                    # Basic person attributes
                    obs["apparel_color"] = random.choice(["Red", "Blue", "Black", "White", "Green"])
                    
                self.observations.append(obs)

    def inject_scenario_1(self):
        # Scenario 1: Vehicle trajectory on SG Highway
        # C101 -> C113 -> C127 -> C144 -> C171
        plate = "GJ01AB1234"
        color = "White"
        v_type = "Sedan"
        
        base_time = self.start_time.replace(hour=19, minute=14, second=2)
        
        stops = [
            ("CAM-GJ-AHM-SG-0101", 0, 0.96),
            ("CAM-GJ-AHM-SG-0113", 435, 0.98), # 19:21:17 (7m 15s)
            ("CAM-GJ-AHM-SG-0127", 942, 0.94), # 19:29:44 (15m 42s)
            ("CAM-GJ-AHM-SG-0144", 1386, 0.97), # 19:37:08 (23m 06s)
            ("CAM-GJ-AHM-SP-0171", 2069, 0.93), # 19:48:31 (34m 29s)
        ]
        
        for cam_id, delay_sec, conf in stops:
            self.observations.append({
                "id": str(uuid.uuid4()),
                "camera_id": cam_id,
                "timestamp": (base_time + timedelta(seconds=delay_sec)).isoformat(),
                "entity_type": "vehicle",
                "confidence": conf,
                "license_plate": plate,
                "vehicle_color": color,
                "vehicle_type": v_type,
                "scenario": "scenario_1"
            })

    def inject_scenario_2(self):
        # Scenario 2: City transit & park GJ05YY5678 (Red Hatchback)
        plate = "GJ05YY5678"
        color = "Red"
        v_type = "Hatchback"
        
        base_time = self.start_time.replace(hour=14, minute=0, second=0)
        
        stops = [
            ("CAM-GJ-AHM-SG-0130", 0),
            ("CAM-GJ-AHM-IM-0501", 300),
            ("CAM-GJ-AHM-CG-0203", 600),
            ("CAM-GJ-AHM-LG-0402", 900),
        ]
        
        for cam_id, delay_sec in stops:
            self.observations.append({
                "id": str(uuid.uuid4()),
                "camera_id": cam_id,
                "timestamp": (base_time + timedelta(seconds=delay_sec)).isoformat(),
                "entity_type": "vehicle",
                "confidence": round(random.uniform(0.85, 0.99), 2),
                "license_plate": plate,
                "vehicle_color": color,
                "vehicle_type": v_type,
                "scenario": "scenario_2"
            })

    def inject_scenario_3(self):
        # Scenario 3: Co-travel
        plate1 = "GJ27CC9999"
        plate2 = "GJ01DD1111"
        
        base_time = self.start_time.replace(hour=22, minute=30, second=0)
        cams = ["CAM-GJ-AHM-132-0901", "CAM-GJ-AHM-132-0902", "CAM-GJ-AHM-132-0903", "CAM-GJ-AHM-132-0904"]
        
        for i, cam_id in enumerate(cams):
            t1 = base_time + timedelta(minutes=i*5)
            t2 = t1 + timedelta(seconds=random.randint(2, 8)) # within 10s
            
            self.observations.append({
                "id": str(uuid.uuid4()),
                "camera_id": cam_id,
                "timestamp": t1.isoformat(),
                "entity_type": "vehicle",
                "confidence": round(random.uniform(0.85, 0.99), 2),
                "license_plate": plate1,
                "vehicle_color": "Black",
                "vehicle_type": "SUV",
                "scenario": "scenario_3"
            })
            
            self.observations.append({
                "id": str(uuid.uuid4()),
                "camera_id": cam_id,
                "timestamp": t2.isoformat(),
                "entity_type": "vehicle",
                "confidence": round(random.uniform(0.85, 0.99), 2),
                "license_plate": plate2,
                "vehicle_color": "Silver",
                "vehicle_type": "Sedan",
                "scenario": "scenario_3"
            })

    def inject_scenario_4(self):
        # Scenario 4: Person ReID
        base_time = self.start_time.replace(hour=10, minute=15, second=0)
        
        # Appearance 1
        self.observations.append({
            "id": str(uuid.uuid4()),
            "camera_id": "CAM-GJ-AHM-RTO-1001",
            "timestamp": base_time.isoformat(),
            "entity_type": "person",
            "confidence": 0.92,
            "apparel_color": "Red",
            "attributes": {"backpack": True, "reid_feature_vector": [0.1, 0.2, 0.3]}, # Mock vector
            "scenario": "scenario_4"
        })
        
        # Appearance 2
        self.observations.append({
            "id": str(uuid.uuid4()),
            "camera_id": "CAM-GJ-AHM-KS-0801",
            "timestamp": self.start_time.replace(hour=11, minute=30, second=0).isoformat(),
            "entity_type": "person",
            "confidence": 0.89,
            "apparel_color": "Red",
            "attributes": {"backpack": True, "reid_feature_vector": [0.1, 0.21, 0.3]}, # Similar mock vector
            "scenario": "scenario_4"
        })

    def inject_scenario_5(self):
        # Scenario 5: Watchlist alert
        plate = "GJ01XX0000"
        
        self.observations.append({
            "id": str(uuid.uuid4()),
            "camera_id": "CAM-GJ-AHM-132-0901",
            "timestamp": self.start_time.replace(hour=16, minute=45, second=0).isoformat(),
            "entity_type": "vehicle",
            "confidence": 0.99,
            "license_plate": plate,
            "vehicle_color": "Black",
            "vehicle_type": "Motorcycle",
            "scenario": "scenario_5"
        })

    def generate_all(self, obs_per_hour_per_cam: int = 20) -> List[Dict]:
        self.generate_noise(obs_per_hour_per_cam)
        self.inject_scenario_1()
        self.inject_scenario_2()
        self.inject_scenario_3()
        self.inject_scenario_4()
        self.inject_scenario_5()
        
        # Sort by timestamp
        self.observations.sort(key=lambda x: x["timestamp"])
        return self.observations
