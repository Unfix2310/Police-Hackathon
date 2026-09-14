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
        "TS", "KL", "WB", "PB", "BR", "CH", "JK", "GA", "UT", "JH",
        "OD", "AS", "TR", "NL", "ML", "MN", "SK", "AR", "MZ", "PY",
        "AN", "DD", "DN", "LD", "CG", "HP"
    }

    def __init__(self, conf_threshold: float = 0.40, tesseract_cmd: Optional[str] = None):
        self.conf_threshold = conf_threshold

        found_cmd = None
        candidates_to_probe = []
        if tesseract_cmd:
            candidates_to_probe.append(tesseract_cmd)
        env_cmd = shutil.which("tesseract")
        if env_cmd:
            candidates_to_probe.append(env_cmd)
        candidates_to_probe.extend([
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/opt/homebrew/bin/tesseract",
        ])

        for c in candidates_to_probe:
            if c and os.path.isfile(c) and os.access(c, os.X_OK):
                found_cmd = c
                break

        self.tesseract_cmd = found_cmd or env_cmd or "/usr/bin/tesseract"
        self.available = found_cmd is not None
        if self.available:
            logger.info(f"ANPREngine initialized with Tesseract: {self.tesseract_cmd}")
        else:
            logger.warning(
                f"Tesseract binary not found (probed: {candidates_to_probe}). "
                "Plate crops will be localized, but OCR text decoding requires tesseract-ocr installed."
            )

    def _locate_plate_candidates(self, vehicle_crop: np.ndarray) -> List[Tuple[np.ndarray, List[int]]]:
        """
        Locate license plate candidate regions inside the vehicle crop.
        Supports both square plates (~1.0 - 1.8, e.g. two-wheelers/rickshaws)
        and rectangular plates (~1.8 - 6.5), with heuristic fallbacks.
        """
        h, w = vehicle_crop.shape[:2]
        if h < 35 or w < 45:
            return []

        candidates = []

        # License plates are predominantly located in the lower 65% of the vehicle
        y_start = int(h * 0.35)
        search_region = vehicle_crop[y_start:, :]
        s_h, s_w = search_region.shape[:2]

        # Grayscale & Blur
        gray = cv2.cvtColor(search_region, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Sobel vertical edge filter (extracts character transitions)
        sobel_x = cv2.Sobel(blurred, cv2.CV_16S, 1, 0, ksize=3)
        abs_sobel_x = cv2.convertScaleAbs(sobel_x)

        # Morphological closing horizontally to bridge character vertical lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        closed = cv2.morphologyEx(abs_sobel_x, cv2.MORPH_CLOSE, kernel)

        # Otsu thresholding
        _, thresh = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        scored_candidates = []
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            if ch < 10 or cw < 20:
                continue

            aspect_ratio = cw / float(ch)
            area = cw * ch

            # Indian plates: square (0.9 to 1.8) or rectangular (1.8 to 6.5)
            if 0.9 <= aspect_ratio <= 6.5 and 150 <= area <= (s_w * s_h * 0.45):
                candidate_mask = abs_sobel_x[y:y+ch, x:x+cw]
                score = np.mean(candidate_mask) if candidate_mask.size > 0 else 0

                pad_x = int(cw * 0.08)
                pad_y = int(ch * 0.12)
                cx1 = max(0, x - pad_x)
                cy1 = max(0, y - pad_y)
                cx2 = min(s_w, x + cw + pad_x)
                cy2 = min(s_h, y + ch + pad_y)

                cand_img = search_region[cy1:cy2, cx1:cx2]
                if cand_img.size > 0:
                    scored_candidates.append((score, cand_img, [cx1, y_start + cy1, cx2, y_start + cy2]))

        scored_candidates.sort(key=lambda item: item[0], reverse=True)
        if scored_candidates:
            # Take top candidate
            candidates.append((scored_candidates[0][1], scored_candidates[0][2]))
            # If second candidate is also strong, take it
            if len(scored_candidates) > 1 and scored_candidates[1][0] > 15:
                candidates.append((scored_candidates[1][1], scored_candidates[1][2]))

        # If no strong contour candidates found, append standard lower-center bumper heuristic
        if not candidates:
            hx1 = int(w * 0.20)
            hx2 = int(w * 0.80)
            hy1 = int(h * 0.55)
            hy2 = int(h * 0.95)
            heur_crop = vehicle_crop[hy1:hy2, hx1:hx2]
            if heur_crop.size > 0:
                candidates.append((heur_crop, [hx1, hy1, hx2, hy2]))

        return candidates

    def _preprocess_variants(self, plate_crop: np.ndarray) -> List[np.ndarray]:
        """
        Produce high-quality OCR image variants:
        1. Contrast-enhanced CLAHE grayscale (superior for Tesseract LSTM).
        2. Adaptive Gaussian binarization (handles non-uniform illumination).
        3. Otsu binarization / inverted binary (handles dark backgrounds / IR night CCTV).
        """
        if plate_crop is None or plate_crop.size == 0:
            return []

        h, w = plate_crop.shape[:2]
        target_h = 64
        target_w = int(w * (target_h / max(1, h)))
        resized = cv2.resize(plate_crop, (max(80, target_w), target_h), interpolation=cv2.INTER_CUBIC)

        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY) if len(resized.shape) == 3 else resized
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)
        denoised = cv2.bilateralFilter(clahe, 5, 35, 35)

        variants = [denoised]

        adapt_bin = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 4)
        variants.append(adapt_bin)

        _, otsu_bin = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        if np.mean(denoised) < 110:
            variants.append(cv2.bitwise_not(otsu_bin))
        else:
            variants.append(otsu_bin)

        return variants

    def _preprocess_for_ocr(self, plate_crop: np.ndarray) -> np.ndarray:
        """Backward-compatible single preprocessed image helper."""
        variants = self._preprocess_variants(plate_crop)
        return variants[0] if variants else None

    def _run_tesseract(self, img: np.ndarray, psm: int = 7) -> str:
        """Executes Tesseract CLI via subprocess with strict timeout."""
        if not self.available or img is None or img.size == 0:
            return ""

        # Fast non-text rejection: flat solid patches (std < 14) contain no characters
        if img.std() < 14.0:
            return ""

        # BMP encoding is raw byte serialization (~0.01ms), 100x faster than PNG
        _, encoded = cv2.imencode(".bmp", img)
        args = [
            self.tesseract_cmd,
            "-",
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
                timeout=0.6,
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

        char_to_digit = {
            "O": "0", "D": "0", "Q": "0",
            "I": "1", "L": "1", "J": "1",
            "Z": "2",
            "E": "3",
            "A": "4",
            "S": "5",
            "G": "6",
            "T": "7",
            "B": "8",
            "P": "9"
        }
        digit_to_char = {
            "0": "O", "1": "I", "2": "Z", "3": "E",
            "4": "A", "5": "S", "6": "G", "7": "T", "8": "B"
        }
        state_corrections = {
            "GI": "GJ", "G1": "GJ", "0J": "GJ", "OJ": "GJ", "6J": "GJ", "QJ": "GJ", "CJ": "GJ",
            "M1": "MH", "NH": "MH", "D1": "DL", "K4": "KA", "R1": "RJ", "T1": "TN",
            "U1": "UP", "VP": "UP", "H1": "HR"
        }

        # ── Format 1: Bharat Series (e.g. 22BH1234AA)
        bh_match = re.match(r"^([0-9]{2})(BH)([0-9]{4})([A-Z]{1,2})$", text)
        if bh_match:
            return text, 0.90, "READABLE"

        # ── Format 2: UK / Commonwealth Format (e.g. MM51 VSU -> 7 chars: 2 letters, 2 digits, 3 letters)
        if len(text) == 7:
            pfx = text[:2]
            dig = text[2:4]
            sfx = text[4:]

            pfx_norm = "".join(digit_to_char.get(c, c) for c in pfx)
            dig_norm = "".join(char_to_digit.get(c, c) for c in dig)
            sfx_norm = "".join(digit_to_char.get(c, c) for c in sfx)

            if pfx_norm.isalpha() and dig_norm.isdigit() and sfx_norm.isalpha():
                formatted = f"{pfx_norm}{dig_norm} {sfx_norm}"
                return formatted, 0.88, "READABLE"

        # ── Format 3: Standard Indian Format with Positional Correction (e.g. GJ01AB1234)
        pfx_raw = text[:2]
        pfx_char = "".join(digit_to_char.get(c, c) for c in pfx_raw)
        state = state_corrections.get(pfx_raw, state_corrections.get(pfx_char, pfx_char))

        if state in self.INDIAN_STATES and len(text) >= 5:
            rem = text[2:]
            d_cand = rem[:2]
            d_norm = "".join(char_to_digit.get(c, c) for c in d_cand)
            if d_norm.isdigit() and len(rem) > 2:
                district = d_norm
                after_dist = rem[2:]
            elif d_cand[0] in "0123456789" or d_cand[0] in char_to_digit:
                district = char_to_digit.get(d_cand[0], d_cand[0])
                after_dist = rem[1:]
            else:
                district = ""
                after_dist = rem

            if district:
                letters_part = ""
                digits_part = ""
                for i, ch in enumerate(after_dist):
                    if i < 3 and (ch.isalpha() or (i < 2 and ch in "01" and len(after_dist) - i > 4)):
                        letters_part += digit_to_char.get(ch, ch)
                    else:
                        num_raw = after_dist[i:]
                        digits_part = "".join(char_to_digit.get(c, c) for c in num_raw)
                        break

                if digits_part.isdigit() and 1 <= len(digits_part) <= 4:
                    full_plate = f"{state}{district}{letters_part}{digits_part}"
                    conf = 0.92 if state == "GJ" else 0.88
                    return full_plate, conf, "READABLE"

        # Standard Indian full pattern regex match
        full_pattern = re.compile(r"^([A-Z]{2})([0-9]{1,2})([A-Z]{0,3})([0-9]{1,4})$")
        match = full_pattern.match(text)
        if match:
            s, d, ser, num = match.groups()
            s_corr = state_corrections.get(s, s)
            formatted = f"{s_corr}{d}{ser}{num}"
            conf = 0.90 if s_corr in self.INDIAN_STATES else 0.80
            return formatted, conf, "READABLE"

        # State prefix valid with partial alphanumeric
        if state in self.INDIAN_STATES:
            if len(text) >= 7:
                return text[:10], 0.78, "READABLE"
            return text, 0.70, "READABLE"

        # ── Format 4: General Alphanumeric Plate Fallback
        if 5 <= len(text) <= 10:
            return text, 0.65, "READABLE"

        return "UNREADABLE", 0.20, "UNREADABLE"

    def detect_plate(self, vehicle_crop: np.ndarray) -> PlateResult:
        """
        Multi-pass plate candidate localization and OCR.
        Tries both PSM 7 (single line) and PSM 6 (uniform block / two-line plates)
        with CLAHE and adaptive preprocessing variants.
        """
        if vehicle_crop is None or vehicle_crop.size == 0:
            return PlateResult(text="NO_PLATE", conf=0.0, status="NO_PLATE")

        h, w = vehicle_crop.shape[:2]
        if h < 35 or w < 45:
            return PlateResult(text="UNREADABLE_LOW_RES", conf=0.0, status="UNREADABLE")

        candidates = self._locate_plate_candidates(vehicle_crop)
        if not candidates:
            return PlateResult(text="NO_PLATE", conf=0.0, status="NO_PLATE")

        # If OCR engine is not installed, attach candidate crop and report status
        if not self.available:
            first_crop, first_bbox = candidates[0]
            return PlateResult(
                text="OCR_UNAVAILABLE",
                conf=0.0,
                plate_bbox=first_bbox,
                status="UNREADABLE",
                raw_text="Tesseract OCR binary not found in container (rebuild required)",
                plate_crop=first_crop,
            )

        best_result = PlateResult(text="UNREADABLE", conf=0.0, status="UNREADABLE")

        for cand_img, bbox in candidates:
            if cand_img is None or cand_img.size == 0 or cand_img.std() < 14.0:
                continue

            # Check if there is an EU/country band to trim
            trimmed_img, was_trimmed = self._trim_country_band(cand_img)
            img_variant = trimmed_img if was_trimmed else cand_img

            ocr_variants = self._preprocess_variants(img_variant)
            for proc_img in ocr_variants:
                # Pass 1: Single line mode (PSM 7)
                raw7 = self._run_tesseract(proc_img, psm=7)
                if raw7 and len(raw7) >= 4:
                    cleaned, conf, status = self._clean_plate_text(raw7)
                    if conf > best_result.plate_confidence:
                        best_result = PlateResult(
                            text=cleaned,
                            conf=conf,
                            plate_bbox=bbox,
                            status=status,
                            raw_text=raw7,
                            plate_crop=img_variant,
                        )
                        # Early exit: if good readable plate found, stop immediately!
                        if conf >= 0.60 or status == "READABLE":
                            return best_result

                # Pass 2: Block / Two-line mode (PSM 6) only if single line found nothing/poor read
                if best_result.plate_confidence < 0.40:
                    raw6 = self._run_tesseract(proc_img, psm=6)
                    if raw6 and len(raw6) >= 4:
                        cleaned, conf, status = self._clean_plate_text(raw6)
                        if conf > best_result.plate_confidence:
                            best_result = PlateResult(
                                text=cleaned,
                                conf=conf,
                                plate_bbox=bbox,
                                status=status,
                                raw_text=raw6,
                                plate_crop=img_variant,
                            )
                            if conf >= 0.60 or status == "READABLE":
                                return best_result

        if best_result.plate_crop is None and candidates:
            best_result.plate_crop = candidates[0][0]
            best_result.plate_bbox = candidates[0][1]

        # Guarantee Plate / UNREADABLE contract
        if best_result.plate_confidence < self.conf_threshold or best_result.status != "READABLE":
            best_result.status = "UNREADABLE"
            best_result.plate_text = "UNREADABLE"

        return best_result


