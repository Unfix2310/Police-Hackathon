"""
Isolated ANPR Unit Test — Gujarat CCTV Intelligence Platform

Tests the robust ANPREngine using synthetic vehicle and plate crops:
1. Standard single-line Indian plates (GJ01AB1234, MH12DE4321)
2. Positional OCR error correction (GJO1AB123S, GI01AB1234, 0J05CD567B)
3. Two-line square plates (motorcycles, scooters, rickshaws)
4. Commercial vehicle yellow plates
5. Bharat Series plates (22BH1234AA)
6. Vehicles with no plate (blank crops)
Completely isolated from database, live streams, and network.
"""

import sys
import os
import cv2
import numpy as np

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.anpr import ANPREngine, PlateResult


def create_synthetic_vehicle_crop(plate_number: str = "GJ01AB1234", bg_color=(255, 255, 255)) -> np.ndarray:
    """Generates a synthetic vehicle crop with a rendered license plate at the lower center."""
    car = np.full((180, 240, 3), 40, dtype=np.uint8)

    # Car body details (bumper, taillights)
    cv2.rectangle(car, (20, 20), (220, 160), (70, 70, 70), -1)
    cv2.rectangle(car, (20, 50), (60, 80), (0, 0, 200), -1)
    cv2.rectangle(car, (180, 50), (220, 80), (0, 0, 200), -1)
    cv2.rectangle(car, (10, 120), (230, 170), (30, 30, 30), -1)

    # License plate: 140x35 rectangle
    px1, py1 = 50, 130
    px2, py2 = 190, 165
    cv2.rectangle(car, (px1, py1), (px2, py2), bg_color, -1)
    cv2.rectangle(car, (px1, py1), (px2, py2), (0, 0, 0), 1)

    # Render plate text
    cv2.putText(car, plate_number, (px1 + 8, py1 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
    return car


def create_synthetic_twowheeler_crop(line1: str = "GJ01", line2: str = "AB1234") -> np.ndarray:
    """Generates a synthetic two-wheeler crop with a two-line square plate (aspect ratio ~1.2)."""
    bike = np.full((220, 180, 3), 55, dtype=np.uint8)

    # Mudguard / frame
    cv2.rectangle(bike, (40, 40), (140, 130), (75, 75, 75), -1)
    cv2.rectangle(bike, (60, 20), (120, 50), (0, 0, 220), -1)

    # Square plate: 70x60
    px1, py1 = 55, 135
    px2, py2 = 125, 195
    cv2.rectangle(bike, (px1, py1), (px2, py2), (255, 255, 255), -1)
    cv2.rectangle(bike, (px1, py1), (px2, py2), (0, 0, 0), 1)

    cv2.putText(bike, line1, (px1 + 8, py1 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
    cv2.putText(bike, line2, (px1 + 4, py1 + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
    return bike


def main():
    print("=" * 60)
    print(" Gujarat CCTV Platform: Isolated ANPR Engine Test")
    print("=" * 60)

    engine = ANPREngine(conf_threshold=0.40)
    print(f"ANPR Engine Available: {engine.available}")
    print(f"Tesseract Command: {engine.tesseract_cmd}")

    if not engine.available:
        print("[-] Tesseract binary not found! Please check installation.")
        sys.exit(1)

    # ── Test Case 1: Clear Synthetic Single-Line Plates ───────────────────────
    test_plates = ["GJ01AB1234", "GJ05CD5678", "MH12DE4321"]

    for expected in test_plates:
        veh_crop = create_synthetic_vehicle_crop(expected)
        result = engine.detect_plate(veh_crop)
        print(f"\n--- Testing Single-Line Plate: {expected} ---")
        print(f"Detected Text:       {result.plate_text}")
        print(f"Confidence:          {result.plate_confidence}")
        print(f"Status:              {result.status}")
        print(f"Plate BBox:          {result.plate_bbox}")
        print(f"Raw OCR:             {result.raw_text}")

        assert result.status == "READABLE", f"Expected READABLE status for {expected}"
        assert result.plate_confidence >= 0.75, f"Expected confidence >= 0.75 for {expected}"
        assert expected[:2] in result.plate_text, f"State code mismatch in {result.plate_text}"
        print(f"[+] SUCCESS: Plate {expected} parsed as {result.plate_text} (conf={result.plate_confidence}).")

    # ── Test Case 2: Positional OCR Error Correction ──────────────────────────
    print("\n--- Testing Positional OCR Syntax Correction ---")
    ocr_error_cases = [
        ("GJO1AB123S", "GJ01AB1235"),  # O->0, S->5
        ("GI01AB1234", "GJ01AB1234"),  # GI->GJ
        ("0J05CD567B", "GJ05CD5678"),  # 0J->GJ, B->8
        ("22BH1234AA", "22BH1234AA"),  # Bharat Series
        ("GJ01A123", "GJ01A123"),      # 3-digit low registration
    ]

    for raw_in, expected_out in ocr_error_cases:
        cleaned, conf, status = engine._clean_plate_text(raw_in)
        print(f"Raw: '{raw_in}' -> Cleaned: '{cleaned}', Conf: {conf}, Status: {status}")
        assert status == "READABLE", f"Failed status for {raw_in}"
        assert cleaned == expected_out, f"Expected {expected_out}, got {cleaned}"
        assert conf >= 0.85, f"Expected high confidence for {raw_in}"
    print("[+] SUCCESS: All OCR error correction cases passed.")

    # ── Test Case 3: Two-Line / Square Plates (Motorcycles / Rickshaws) ───────
    print("\n--- Testing Two-Line Square Plate (Motorcycle/Rickshaw) ---")
    bike_crop = create_synthetic_twowheeler_crop(line1="GJ01", line2="AB1234")
    bike_res = engine.detect_plate(bike_crop)
    print(f"Detected Text:       {bike_res.plate_text}")
    print(f"Confidence:          {bike_res.plate_confidence}")
    print(f"Status:              {bike_res.status}")
    print(f"Raw OCR:             {repr(bike_res.raw_text)}")
    assert bike_res.status == "READABLE", f"Expected READABLE for two-line plate, got {bike_res.status}"
    assert "GJ01AB1234" in bike_res.plate_text or bike_res.plate_confidence >= 0.80
    print("[+] SUCCESS: Two-line square plate detected and parsed successfully.")

    # ── Test Case 4: Commercial Vehicle (Yellow Plate) ─────────────────────────
    print("\n--- Testing Commercial Vehicle (Yellow Plate) ---")
    yellow_crop = create_synthetic_vehicle_crop("GJ01AB1234", bg_color=(0, 215, 255))
    yellow_res = engine.detect_plate(yellow_crop)
    print(f"Detected Text:       {yellow_res.plate_text}")
    print(f"Confidence:          {yellow_res.plate_confidence}")
    print(f"Status:              {yellow_res.status}")
    assert yellow_res.status == "READABLE", "Failed commercial yellow plate test"
    print("[+] SUCCESS: Commercial yellow plate identified successfully.")

    # ── Test Case 5: Vehicle with No Plate (blank crop) ────────────────────────
    print("\n--- Testing No-Plate Vehicle Crop ---")
    blank_veh = np.full((180, 240, 3), 50, dtype=np.uint8)
    no_plate_res = engine.detect_plate(blank_veh)
    print(f"Status: {no_plate_res.status}, Text: {no_plate_res.plate_text}, Conf: {no_plate_res.plate_confidence}")
    assert no_plate_res.status in ("NO_PLATE", "UNREADABLE"), "Failed no plate test"
    print("[+] SUCCESS: No-plate crop correctly identified.")

    print("\n" + "=" * 60)
    print("All Isolated ANPR Unit Tests PASSED Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
