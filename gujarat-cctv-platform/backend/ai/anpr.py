"""
ANPR Engine — Baseline OCR Engine for Isolated Testing

Uses morphological edge/contour plate candidate localization and Tesseract OCR
as an initial baseline for testing on real-world CCTV footage.
"""

import logging
import os
import re
import shutil
import subprocess
from typing import Dict, Any, List, Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class PlateResult:
    """Encapsulates the detected license plate result."""
    def __init__(
        self,
        text: str,
        conf: float,
        plate_bbox: Optional[List[int]] = None,
        status: str = "UNREADABLE",
        raw_text: str = "",
        plate_crop: Optional[np.ndarray] = None,
    ):
        self.plate_text = text
        self.plate_confidence = round(conf, 2)
        self.plate_bbox = plate_bbox or [0, 0, 0, 0]
        self.status = status  # "READABLE", "UNREADABLE", "NO_PLATE"
        self.raw_text = raw_text
        self.plate_crop = plate_crop

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plate_text": self.plate_text,
            "plate_confidence": self.plate_confidence,
            "plate_bbox": self.plate_bbox,
            "status": self.status,
            "raw_text": self.raw_text,
        }


class ANPREngine:
    """
    Two-stage baseline ANPR Engine:
    1. Plate Candidate Localizer: Identifies high-gradient rectangular contours
       in the vehicle crop (aspect ratios ~2.0 - 5.5).
    2. OCR Engine: Preprocesses candidate crops and executes Tesseract OCR
       with character whitelisting and Indian plate format normalization.
    """

    INDIAN_STATES = {
        "GJ", "MH", "DL", "KA", "TN", "UP", "HR", "RJ", "MP", "AP",
        "TS", "KL", "WB", "PB", "BR", "CH", "JK", "GA", "UT", "JH"
    }

    def __init__(self, conf_threshold: float = 0.5, tesseract_cmd: Optional[str] = None):
        self.conf_threshold = conf_threshold
        self.tesseract_cmd = (
            tesseract_cmd
            or shutil.which("tesseract")
            or "/opt/homebrew/bin/tesseract"
            or "/usr/local/bin/tesseract"
            or "/usr/bin/tesseract"
        )
        self.available = os.path.isfile(self.tesseract_cmd) and os.access(self.tesseract_cmd, os.X_OK)
        if self.available:
            logger.info(f"ANPREngine initialized with Tesseract: {self.tesseract_cmd}")
        else:
            logger.warning(f"Tesseract binary not found at {self.tesseract_cmd}. ANPR fallback mode active.")

    def _locate_plate_candidates(self, vehicle_crop: np.ndarray) -> List[Tuple[np.ndarray, List[int]]]:
        """
        Locate license plate candidate regions inside the vehicle crop.
        Returns top 2 candidates scored by edge density and rectangular aspect ratio.
        """
        h, w = vehicle_crop.shape[:2]
        # Skip vehicles that are too small to ever have a readable plate
        if h < 45 or w < 60:
            return []

        candidates = []

        # License plates are predominantly located in the lower 55% of the vehicle
        y_start = int(h * 0.40)
        search_region = vehicle_crop[y_start:, :]
        s_h, s_w = search_region.shape[:2]

        # Grayscale & Blur
        gray = cv2.cvtColor(search_region, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Sobel vertical edge filter (extracts character transitions)
        sobel_x = cv2.Sobel(blurred, cv2.CV_16S, 1, 0, ksize=3)
        abs_sobel_x = cv2.convertScaleAbs(sobel_x)

        # Morphological closing horizontally to bridge character vertical lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
        closed = cv2.morphologyEx(abs_sobel_x, cv2.MORPH_CLOSE, kernel)

        # Otsu thresholding
        _, thresh = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        scored_candidates = []
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            if ch < 10 or cw < 25:
                continue

            aspect_ratio = cw / float(ch)
            area = cw * ch

            # Standard Indian plates: rectangular (2.0 to 5.5) or square (1.2 to 2.0)
            if 1.5 <= aspect_ratio <= 6.0 and 300 <= area <= (s_w * s_h * 0.35):
                # Edge density score within the candidate box
                candidate_mask = abs_sobel_x[y:y+ch, x:x+cw]
                score = np.mean(candidate_mask) if candidate_mask.size > 0 else 0

                pad_x = int(cw * 0.06)
                pad_y = int(ch * 0.10)
                cx1 = max(0, x - pad_x)
                cy1 = max(0, y - pad_y)
                cx2 = min(s_w, x + cw + pad_x)
                cy2 = min(s_h, y + ch + pad_y)

                cand_img = search_region[cy1:cy2, cx1:cx2]
                if cand_img.size > 0:
                    scored_candidates.append((score, cand_img, [cx1, y_start + cy1, cx2, y_start + cy2]))

        # Sort candidates by edge density (highest score first) and pick top 2
        scored_candidates.sort(key=lambda item: item[0], reverse=True)
        for _, img, bbox in scored_candidates[:2]:
            candidates.append((img, bbox))

        # Heuristic fallback: lower-center 25% of vehicle if no candidate found
        if not candidates:
            hx1 = int(w * 0.25)
            hx2 = int(w * 0.75)
            hy1 = int(h * 0.60)
            hy2 = int(h * 0.92)
            heur_crop = vehicle_crop[hy1:hy2, hx1:hx2]
            if heur_crop.size > 0:
                candidates.append((heur_crop, [hx1, hy1, hx2, hy2]))

        return candidates

    def _preprocess_for_ocr(self, plate_crop: np.ndarray) -> np.ndarray:
        """Produce a single high-quality contrast-enhanced binarized image for fast OCR."""
        if plate_crop is None or plate_crop.size == 0:
            return None

        h, w = plate_crop.shape[:2]
        target_h = 60
        target_w = int(w * (target_h / max(1, h)))
        resized = cv2.resize(plate_crop, (max(70, target_w), target_h), interpolation=cv2.INTER_CUBIC)

        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        denoised = cv2.bilateralFilter(enhanced, 5, 40, 40)
        _, otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        return otsu

    def _run_tesseract(self, img: np.ndarray, psm: int = 7) -> str:
        """Executes Tesseract CLI via subprocess with strict 1.0s timeout."""
        if not self.available or img is None or img.size == 0:
            return ""

        _, encoded = cv2.imencode(".png", img)
        args = [
            self.tesseract_cmd,
            "stdin",
            "stdout",
            "--oem", "1",
            "--psm", str(psm),
            "-c", "tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        ]

        try:
            proc = subprocess.run(
                args,
                input=encoded.tobytes(),
                capture_output=True,
                timeout=1.0,
                check=False,
            )
            return proc.stdout.decode("utf-8", errors="ignore").strip()
        except Exception:
            return ""

    def _trim_country_band(self, plate_crop: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Detects and trims out the left EU/UK/country identifier band (blue/dark stripe)."""
        if plate_crop is None or plate_crop.size == 0:
            return plate_crop, False

        h, w = plate_crop.shape[:2]
        if w < 50:
            return plate_crop, False

        left_width = int(w * 0.18)
        left_strip = plate_crop[:, :left_width]

        # 1. Check for blue color (Euro / UK GB band)
        hsv = cv2.cvtColor(left_strip, cv2.COLOR_BGR2HSV)
        blue_mask = cv2.inRange(hsv, np.array([90, 35, 30]), np.array([135, 255, 255]))
        blue_ratio = np.count_nonzero(blue_mask) / float(left_strip.shape[0] * left_strip.shape[1])

        # 2. Check for dark vertical edge band
        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        mean_left = np.mean(gray[:, :int(w * 0.14)])
        mean_center = np.mean(gray[:, int(w * 0.25):int(w * 0.75)])

        if blue_ratio > 0.08 or (mean_center > 90 and mean_left < mean_center * 0.62):
            trim_x = int(w * 0.13)
            trimmed = plate_crop[:, trim_x:]
            if trimmed.shape[1] > 30:
                return trimmed, True

        return plate_crop, False

    def _clean_plate_text(self, raw_text: str) -> Tuple[str, float, str]:
        """
        Cleans and evaluates license plate text across Indian, UK, and European standards.
        Applies positional character syntax correction (digits vs letters).
        Returns: (cleaned_text, confidence, status)
        """
        text = re.sub(r"[^A-Z0-9]", "", raw_text.upper())
        if text.startswith("IND"):
            text = text[3:]

        if len(text) < 4:
            return "UNREADABLE", 0.0, "UNREADABLE"

        # ── Format 1: UK / Commonwealth Format (e.g. MM51 VSU -> 7 chars: 2 letters, 2 digits, 3 letters)
        if len(text) == 7:
            pfx = text[:2]
            dig = text[2:4]
            sfx = text[4:]

            l2d = {"0": "O", "1": "I", "5": "S", "8": "B"}
            d2l = {"S": "5", "I": "1", "L": "1", "O": "0", "Z": "2", "B": "8", "A": "4", "G": "6", "Y": "1", "T": "7"}

            pfx_norm = "".join(l2d.get(c, c) for c in pfx)
            dig_norm = "".join(d2l.get(c, c) for c in dig)
            sfx_norm = "".join(l2d.get(c, c) for c in sfx)

            if pfx_norm.isalpha() and dig_norm.isdigit() and sfx_norm.isalpha():
                formatted = f"{pfx_norm}{dig_norm} {sfx_norm}"
                return formatted, 0.88, "READABLE"

        # ── Format 2: Standard Indian Format (e.g. GJ01AB1234)
        if len(text) >= 6:
            if text.startswith(("GIJ", "G1J", "0IJ", "O1J", "OIJ")):
                text = "GJ" + text[3:]
            elif text[:2] in ("GI", "G1", "0J", "OJ"):
                text = "GJ" + text[2:]

        full_pattern = re.compile(r"^([A-Z]{2})([0-9]{1,2})([A-Z]{0,3})([0-9]{4})$")
        match = full_pattern.match(text)
        if match:
            state, district, series, num = match.groups()
            formatted = f"{state}{district}{series}{num}"
            conf = 0.90 if state in self.INDIAN_STATES else 0.75
            return formatted, conf, "READABLE"

        state_cand = text[:2]
        if state_cand in self.INDIAN_STATES:
            if len(text) >= 8:
                return text[:10], 0.75, "READABLE"
            return text, 0.60, "READABLE"

        # ── Format 3: General Alphanumeric Plate
        if 6 <= len(text) <= 10:
            return text, 0.50, "READABLE"

        return "UNREADABLE", 0.20, "UNREADABLE"

    def detect_plate(self, vehicle_crop: np.ndarray) -> PlateResult:
        """
        Fast single-pass plate detection and OCR.
        Applies country-band trimming and multi-format validation.
        """
        if vehicle_crop is None or vehicle_crop.size == 0 or not self.available:
            return PlateResult(text="NO_PLATE", conf=0.0, status="NO_PLATE")

        h, w = vehicle_crop.shape[:2]
        if h < 45 or w < 60:
            return PlateResult(text="UNREADABLE_LOW_RES", conf=0.0, status="UNREADABLE")

        candidates = self._locate_plate_candidates(vehicle_crop)
        if not candidates:
            return PlateResult(text="NO_PLATE", conf=0.0, status="NO_PLATE")

        best_result = PlateResult(text="UNREADABLE", conf=0.0, status="UNREADABLE")

        for cand_img, bbox in candidates:
            # Try trimmed version (without blue/country stripe) first
            trimmed_img, was_trimmed = self._trim_country_band(cand_img)
            variants_to_try = [trimmed_img]
            if was_trimmed:
                variants_to_try.append(cand_img)

            for img_variant in variants_to_try:
                binary_img = self._preprocess_for_ocr(img_variant)
                if binary_img is None:
                    continue

                raw = self._run_tesseract(binary_img, psm=7)
                if raw and len(raw) >= 4:
                    cleaned, conf, status = self._clean_plate_text(raw)
                    if conf > best_result.plate_confidence:
                        best_result = PlateResult(
                            text=cleaned,
                            conf=conf,
                            plate_bbox=bbox,
                            status=status,
                            raw_text=raw,
                            plate_crop=img_variant,
                        )
                        if conf >= 0.80:
                            return best_result

        if best_result.plate_crop is None and candidates:
            best_result.plate_crop = candidates[0][0]
            best_result.plate_bbox = candidates[0][1]

        # Guarantee Plate / UNREADABLE contract
        if best_result.plate_confidence < self.conf_threshold or best_result.status != "READABLE":
            best_result.status = "UNREADABLE"
            best_result.plate_text = "UNREADABLE"

        return best_result


