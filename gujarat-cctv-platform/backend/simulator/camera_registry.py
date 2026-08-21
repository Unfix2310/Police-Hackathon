import json
from typing import Dict, List, Optional

CAMERAS = [
    {"cam_id": "CAM-GJ-AHM-SG-0101", "display_name": "SG Highway / ISRO", "latitude": 23.0258, "longitude": 72.5074, "direction_deg": 350, "location_type": "highway", "police_station": "Satellite", "district": "Ahmedabad", "capabilities": ["ANPR", "PTZ", "Night Vision"]},
    {"cam_id": "CAM-GJ-AHM-SG-0102", "display_name": "SG Highway / ISRO South", "latitude": 23.0245, "longitude": 72.5072, "direction_deg": 170, "location_type": "highway", "police_station": "Satellite", "district": "Ahmedabad", "capabilities": ["ANPR", "Night Vision"]},
    {"cam_id": "CAM-GJ-AHM-SG-0113", "display_name": "SG Highway / Drive-In Jn", "latitude": 23.0495, "longitude": 72.5175, "direction_deg": 345, "location_type": "intersection", "police_station": "Vastrapur", "district": "Ahmedabad", "capabilities": ["ANPR", "PTZ"]},
    {"cam_id": "CAM-GJ-AHM-SG-0114", "display_name": "SG Highway / Drive-In South", "latitude": 23.0482, "longitude": 72.5170, "direction_deg": 165, "location_type": "intersection", "police_station": "Vastrapur", "district": "Ahmedabad", "capabilities": ["Detection Only"]},
    {"cam_id": "CAM-GJ-AHM-SG-0127", "display_name": "SG Highway / Thaltej", "latitude": 23.0531, "longitude": 72.5186, "direction_deg": 350, "location_type": "intersection", "police_station": "Sola", "district": "Ahmedabad", "capabilities": ["ANPR", "Night Vision"]},
    {"cam_id": "CAM-GJ-AHM-SG-0128", "display_name": "SG Highway / Thaltej Cross", "latitude": 23.0531, "longitude": 72.5186, "direction_deg": 90, "location_type": "intersection", "police_station": "Sola", "district": "Ahmedabad", "capabilities": ["Detection Only"]},
    {"cam_id": "CAM-GJ-AHM-SG-0130", "display_name": "SG Highway / Pakwan", "latitude": 23.0381, "longitude": 72.5123, "direction_deg": 355, "location_type": "highway", "police_station": "Vastrapur", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-SG-0131", "display_name": "SG Highway / Pakwan Flyover", "latitude": 23.0380, "longitude": 72.5123, "direction_deg": 175, "location_type": "highway", "police_station": "Vastrapur", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-SG-0144", "display_name": "SG Highway / Sola Bhagwat", "latitude": 23.0805, "longitude": 72.5284, "direction_deg": 340, "location_type": "highway", "police_station": "Sola", "district": "Ahmedabad", "capabilities": ["ANPR", "Night Vision"]},
    {"cam_id": "CAM-GJ-AHM-SG-0145", "display_name": "SG Highway / Sola Bridge", "latitude": 23.0800, "longitude": 72.5282, "direction_deg": 160, "location_type": "highway", "police_station": "Sola", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-SP-0171", "display_name": "SP Ring Road / Motera", "latitude": 23.1118, "longitude": 72.5975, "direction_deg": 90, "location_type": "highway", "police_station": "Chandkheda", "district": "Ahmedabad", "capabilities": ["ANPR", "Night Vision"]},
    {"cam_id": "CAM-GJ-AHM-SP-0172", "display_name": "SP Ring Road / Tapovan", "latitude": 23.1189, "longitude": 72.5802, "direction_deg": 270, "location_type": "highway", "police_station": "Chandkheda", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-SP-0173", "display_name": "SP Ring Road / Bopal", "latitude": 23.0234, "longitude": 72.4645, "direction_deg": 180, "location_type": "highway", "police_station": "Bopal", "district": "Ahmedabad", "capabilities": ["ANPR", "PTZ"]},
    {"cam_id": "CAM-GJ-AHM-SP-0174", "display_name": "SP Ring Road / Sanand Cir", "latitude": 22.9912, "longitude": 72.4721, "direction_deg": 180, "location_type": "intersection", "police_station": "Sarkhej", "district": "Ahmedabad", "capabilities": ["ANPR", "Night Vision"]},
    {"cam_id": "CAM-GJ-AHM-SP-0175", "display_name": "SP Ring Road / Kamod", "latitude": 22.9543, "longitude": 72.5312, "direction_deg": 90, "location_type": "highway", "police_station": "Aslali", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-CG-0201", "display_name": "CG Road / Swastik", "latitude": 23.0345, "longitude": 72.5567, "direction_deg": 10, "location_type": "market", "police_station": "Navrangpura", "district": "Ahmedabad", "capabilities": ["PTZ", "Detection"]},
    {"cam_id": "CAM-GJ-AHM-CG-0202", "display_name": "CG Road / Girish Cold", "latitude": 23.0312, "longitude": 72.5552, "direction_deg": 190, "location_type": "market", "police_station": "Navrangpura", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-CG-0203", "display_name": "CG Road / Panchvati", "latitude": 23.0254, "longitude": 72.5523, "direction_deg": 20, "location_type": "intersection", "police_station": "Ellis Bridge", "district": "Ahmedabad", "capabilities": ["ANPR", "PTZ"]},
    {"cam_id": "CAM-GJ-AHM-CG-0204", "display_name": "CG Road / Parimal", "latitude": 23.0211, "longitude": 72.5501, "direction_deg": 200, "location_type": "intersection", "police_station": "Ellis Bridge", "district": "Ahmedabad", "capabilities": ["Detection Only"]},
    {"cam_id": "CAM-GJ-AHM-AR-0301", "display_name": "Ashram Road / Income Tax", "latitude": 23.0456, "longitude": 72.5689, "direction_deg": 180, "location_type": "intersection", "police_station": "Navrangpura", "district": "Ahmedabad", "capabilities": ["ANPR", "Night Vision"]},
    {"cam_id": "CAM-GJ-AHM-AR-0302", "display_name": "Ashram Road / Bata", "latitude": 23.0412, "longitude": 72.5678, "direction_deg": 0, "location_type": "highway", "police_station": "Navrangpura", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-AR-0303", "display_name": "Ashram Road / Vallabh Sadan", "latitude": 23.0345, "longitude": 72.5667, "direction_deg": 180, "location_type": "intersection", "police_station": "Ellis Bridge", "district": "Ahmedabad", "capabilities": ["PTZ", "Detection"]},
    {"cam_id": "CAM-GJ-AHM-AR-0304", "display_name": "Ashram Road / VS Hospital", "latitude": 23.0214, "longitude": 72.5712, "direction_deg": 0, "location_type": "building_entry", "police_station": "Ellis Bridge", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-LG-0401", "display_name": "Law Garden / NCC", "latitude": 23.0278, "longitude": 72.5589, "direction_deg": 90, "location_type": "market", "police_station": "Ellis Bridge", "district": "Ahmedabad", "capabilities": ["Detection Only"]},
    {"cam_id": "CAM-GJ-AHM-LG-0402", "display_name": "Law Garden / Happy Street", "latitude": 23.0289, "longitude": 72.5595, "direction_deg": 270, "location_type": "market", "police_station": "Ellis Bridge", "district": "Ahmedabad", "capabilities": ["PTZ"]},
    {"cam_id": "CAM-GJ-AHM-IM-0501", "display_name": "IIM Road / Panjrapole", "latitude": 23.0305, "longitude": 72.5412, "direction_deg": 270, "location_type": "intersection", "police_station": "Vastrapur", "district": "Ahmedabad", "capabilities": ["ANPR", "Night Vision"]},
    {"cam_id": "CAM-GJ-AHM-IM-0502", "display_name": "IIM Road / IIM Gate", "latitude": 23.0321, "longitude": 72.5356, "direction_deg": 90, "location_type": "building_entry", "police_station": "Vastrapur", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-IM-0503", "display_name": "IIM Road / AMA", "latitude": 23.0315, "longitude": 72.5388, "direction_deg": 270, "location_type": "building_entry", "police_station": "Vastrapur", "district": "Ahmedabad", "capabilities": ["Detection Only"]},
    {"cam_id": "CAM-GJ-AHM-RR-0601", "display_name": "Relief Road / Laldarwaja", "latitude": 23.0256, "longitude": 72.5812, "direction_deg": 90, "location_type": "intersection", "police_station": "Karanj", "district": "Ahmedabad", "capabilities": ["ANPR", "PTZ"]},
    {"cam_id": "CAM-GJ-AHM-RR-0602", "display_name": "Relief Road / Electricity House", "latitude": 23.0267, "longitude": 72.5834, "direction_deg": 270, "location_type": "building_entry", "police_station": "Karanj", "district": "Ahmedabad", "capabilities": ["Detection Only"]},
    {"cam_id": "CAM-GJ-AHM-RR-0603", "display_name": "Relief Road / Zaveriwad", "latitude": 23.0278, "longitude": 72.5865, "direction_deg": 90, "location_type": "market", "police_station": "Kalupur", "district": "Ahmedabad", "capabilities": ["PTZ"]},
    {"cam_id": "CAM-GJ-AHM-MC-0701", "display_name": "Manek Chowk / Entry", "latitude": 23.0234, "longitude": 72.5891, "direction_deg": 180, "location_type": "market", "police_station": "Khadia", "district": "Ahmedabad", "capabilities": ["Detection Only"]},
    {"cam_id": "CAM-GJ-AHM-MC-0702", "display_name": "Manek Chowk / Food Market", "latitude": 23.0230, "longitude": 72.5895, "direction_deg": 0, "location_type": "market", "police_station": "Khadia", "district": "Ahmedabad", "capabilities": ["PTZ"]},
    {"cam_id": "CAM-GJ-AHM-MC-0703", "display_name": "Manek Chowk / Bullion", "latitude": 23.0225, "longitude": 72.5890, "direction_deg": 90, "location_type": "market", "police_station": "Khadia", "district": "Ahmedabad", "capabilities": ["Detection Only"]},
    {"cam_id": "CAM-GJ-AHM-KS-0801", "display_name": "Kalupur / Station Entry", "latitude": 23.0298, "longitude": 72.5987, "direction_deg": 270, "location_type": "building_entry", "police_station": "Kalupur", "district": "Ahmedabad", "capabilities": ["ANPR", "PTZ"]},
    {"cam_id": "CAM-GJ-AHM-KS-0802", "display_name": "Kalupur / Station Exit", "latitude": 23.0301, "longitude": 72.5985, "direction_deg": 90, "location_type": "building_entry", "police_station": "Kalupur", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-KS-0803", "display_name": "Kalupur / Sindhi Market", "latitude": 23.0285, "longitude": 72.5956, "direction_deg": 180, "location_type": "market", "police_station": "Kalupur", "district": "Ahmedabad", "capabilities": ["PTZ"]},
    {"cam_id": "CAM-GJ-AHM-SG-0150", "display_name": "SG Highway / Makarba", "latitude": 23.0045, "longitude": 72.4987, "direction_deg": 350, "location_type": "highway", "police_station": "Sarkhej", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-SG-0151", "display_name": "SG Highway / Prahladnagar", "latitude": 23.0112, "longitude": 72.5023, "direction_deg": 170, "location_type": "intersection", "police_station": "Anandnagar", "district": "Ahmedabad", "capabilities": ["ANPR", "Night Vision"]},
    {"cam_id": "CAM-GJ-AHM-SG-0152", "display_name": "SG Highway / YMCA", "latitude": 23.0089, "longitude": 72.5011, "direction_deg": 350, "location_type": "highway", "police_station": "Anandnagar", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-132-0901", "display_name": "132ft Ring / Shivranjani", "latitude": 23.0245, "longitude": 72.5256, "direction_deg": 0, "location_type": "intersection", "police_station": "Satellite", "district": "Ahmedabad", "capabilities": ["ANPR", "PTZ"]},
    {"cam_id": "CAM-GJ-AHM-132-0902", "display_name": "132ft Ring / Nehrunagar", "latitude": 23.0189, "longitude": 72.5345, "direction_deg": 0, "location_type": "intersection", "police_station": "Ellis Bridge", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-132-0903", "display_name": "132ft Ring / AEC", "latitude": 23.0567, "longitude": 72.5456, "direction_deg": 180, "location_type": "intersection", "police_station": "Naranpura", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-132-0904", "display_name": "132ft Ring / Helmet Cir", "latitude": 23.0456, "longitude": 72.5389, "direction_deg": 90, "location_type": "intersection", "police_station": "Vastrapur", "district": "Ahmedabad", "capabilities": ["ANPR", "Night Vision"]},
    {"cam_id": "CAM-GJ-AHM-132-0905", "display_name": "132ft Ring / Akhbar Nagar", "latitude": 23.0678, "longitude": 72.5567, "direction_deg": 180, "location_type": "intersection", "police_station": "Vadaj", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-132-0906", "display_name": "132ft Ring / Vadaj Cir", "latitude": 23.0612, "longitude": 72.5678, "direction_deg": 90, "location_type": "intersection", "police_station": "Vadaj", "district": "Ahmedabad", "capabilities": ["ANPR", "PTZ"]},
    {"cam_id": "CAM-GJ-AHM-RTO-1001", "display_name": "RTO Circle / North", "latitude": 23.0745, "longitude": 72.5789, "direction_deg": 180, "location_type": "intersection", "police_station": "Sabarmati", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-RTO-1002", "display_name": "RTO Circle / South", "latitude": 23.0740, "longitude": 72.5789, "direction_deg": 0, "location_type": "intersection", "police_station": "Sabarmati", "district": "Ahmedabad", "capabilities": ["ANPR"]},
    {"cam_id": "CAM-GJ-AHM-RTO-1003", "display_name": "RTO / Subhash Bridge", "latitude": 23.0712, "longitude": 72.5834, "direction_deg": 90, "location_type": "highway", "police_station": "Sabarmati", "district": "Ahmedabad", "capabilities": ["ANPR", "Night Vision"]},
    {"cam_id": "CAM-GJ-AHM-RTO-1004", "display_name": "RTO / Collector Office", "latitude": 23.0756, "longitude": 72.5812, "direction_deg": 270, "location_type": "building_entry", "police_station": "Sabarmati", "district": "Ahmedabad", "capabilities": ["Detection Only"]}
]

# Generate missing cameras to reach 50 if needed
def _ensure_50_cameras():
    global CAMERAS
    if len(CAMERAS) >= 50:
        return
    base_lat = 23.0500
    base_lng = 72.5000
    for i in range(50 - len(CAMERAS)):
        CAMERAS.append({
            "cam_id": f"CAM-GJ-AHM-EXT-{i+1000}",
            "display_name": f"Ext Camera {i}",
            "latitude": base_lat + (i * 0.001),
            "longitude": base_lng + (i * 0.001),
            "direction_deg": 0,
            "location_type": "highway",
            "police_station": "Unknown",
            "district": "Ahmedabad",
            "capabilities": ["ANPR"]
        })

_ensure_50_cameras()

def get_all_cameras() -> List[Dict]:
    """Returns the list of all 50 simulated cameras."""
    return CAMERAS

def get_camera(cam_id: str) -> Optional[Dict]:
    """Returns a specific camera by ID."""
    for cam in CAMERAS:
        if cam["cam_id"] == cam_id:
            return cam
    return None
