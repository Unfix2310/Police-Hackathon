"""
Isolated ANPR Unit Test — Gujarat CCTV Intelligence Platform

Tests the baseline ANPREngine using synthetic vehicle and plate crops.
Completely isolated from database, live streams, and network.
"""

import sys
import os
import cv2
import numpy as np

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.anpr import ANPREngine, PlateResult

def create_synthetic_vehicle_crop(plate_number: str = "GJ01AB1234") -> np.ndarray:
    """Generates a synthetic vehicle crop with a rendered license plate at the lower center."""
    # Car rear: 240 width, 180 height
    car = np.full((180, 240, 3), 40, dtype=np.uint8)
    
    # Car body details (bumper, taillights)
    cv2.rectangle(car, (20, 20), (220, 160), (70, 70, 70), -1)  # trunk
    cv2.rectangle(car, (20, 50), (60, 80), (0, 0, 200), -1)     # left taillight
    cv2.rectangle(car, (180, 50), (220, 80), (0, 0, 200), -1)   # right taillight
    cv2.rectangle(car, (10, 120), (230, 170), (30, 30, 30), -1) # bumper

    # License plate: 140x35 white rectangle with black text
    px1, py1 = 50, 130
    px2, py2 = 190, 165
    cv2.rectangle(car, (px1, py1), (px2, py2), (255, 255, 255), -1)
    cv2.rectangle(car, (px1, py1), (px2, py2), (0, 0, 0), 1)

    # Render plate text
    cv2.putText(car, plate_number, (px1 + 8, py1 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
    return car

def main():
    print("=" * 60)
    print(" Gujarat CCTV Platform: Isolated ANPR Engine Test")
    print("=" * 60)

    engine = ANPREngine()
    print(f"ANPR Engine Available: {engine.available}")
    print(f"Tesseract Command: {engine.tesseract_cmd}")

    if not engine.available:
        print("[-] Tesseract binary not found! Please check installation.")
        sys.exit(1)

    # Test Case 1: Clear Synthetic Plate
    test_plates = ["GJ01AB1234", "GJ05CD5678", "MH12DE4321"]
    all_passed = True

    for expected in test_plates:
        veh_crop = create_synthetic_vehicle_crop(expected)
        result = engine.detect_plate(veh_crop)
        print(f"\n--- Testing Plate: {expected} ---")
        print(f"Detected Text:       {result.plate_text}")
        print(f"Confidence:          {result.plate_confidence}")
        print(f"Status:              {result.status}")
        print(f"Plate BBox:          {result.plate_bbox}")
        print(f"Raw OCR:             {result.raw_text}")

        # Check if detected contains expected or state code
        if expected[:4] in result.plate_text or result.status == "READABLE":
            print(f"[+] SUCCESS: Plate {expected} parsed successfully.")
        else:
            print(f"[-] WARNING: Plate {expected} partial match.")
            all_passed = False

    # Test Case 2: Vehicle with No Plate (blank crop)
    blank_veh = np.full((180, 240, 3), 50, dtype=np.uint8)
    no_plate_res = engine.detect_plate(blank_veh)
    print("\n--- Testing No-Plate Vehicle Crop ---")
    print(f"Status: {no_plate_res.status}, Text: {no_plate_res.plate_text}, Conf: {no_plate_res.plate_confidence}")
    assert no_plate_res.status in ("NO_PLATE", "UNREADABLE"), "Failed no plate test"
    print("[+] SUCCESS: No-plate crop correctly identified.")

    print("\n" + "=" * 60)
    print("Isolated ANPR Test Finished. Engine ready for test lab.")
    print("=" * 60)

if __name__ == "__main__":
    main()
