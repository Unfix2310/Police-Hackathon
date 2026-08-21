import cv2
import os
import time
from typing import Generator, Tuple, Dict
from .camera_registry import get_all_cameras

class CameraSimulator:
    def __init__(self, video_dir: str, target_fps: int = 15):
        self.video_dir = video_dir
        self.target_fps = target_fps
        self.cameras = get_all_cameras()
        self.video_caps: Dict[str, cv2.VideoCapture] = {}
        self.frame_delay = 1.0 / target_fps if target_fps > 0 else 0
        
        self._initialize_caps()
        
    def _initialize_caps(self):
        if not os.path.exists(self.video_dir):
            print(f"Warning: Video directory {self.video_dir} not found.")
            return
            
        for cam in self.cameras:
            cam_id = cam["cam_id"]
            video_path = os.path.join(self.video_dir, f"{cam_id}.mp4")
            
            if os.path.exists(video_path):
                cap = cv2.VideoCapture(video_path)
                if cap.isOpened():
                    self.video_caps[cam_id] = cap
                else:
                    print(f"Warning: Could not open video {video_path}")
            
    def get_frames(self) -> Generator[Tuple[any, float, str], None, None]:
        """Yields (frame, timestamp, camera_id) for all initialized cameras."""
        while True:
            start_time = time.time()
            frames_yielded = 0
            
            for cam_id, cap in list(self.video_caps.items()):
                ret, frame = cap.read()
                
                # Loop video if it ends
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    
                if ret:
                    yield (frame, time.time(), cam_id)
                    frames_yielded += 1
                    
            if frames_yielded == 0:
                break
                
            elapsed = time.time() - start_time
            if elapsed < self.frame_delay:
                time.sleep(self.frame_delay - elapsed)

    def release(self):
        for cap in self.video_caps.values():
            cap.release()
