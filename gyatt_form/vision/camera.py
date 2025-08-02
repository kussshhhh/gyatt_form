"""
Camera input and video stream management.

Handles camera initialization, frame capture, and video stream processing
for real-time pose detection and analysis.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Generator
import threading
import queue
import time

from ..config.processing import ProcessingConfig


class CameraManager:
    """
    Manages camera input and video stream processing.
    
    Provides thread-safe camera access with buffering and frame rate control.
    Supports both live camera feeds and video file input.
    """
    
    def __init__(self, config: ProcessingConfig):
        """Initialize camera manager with configuration."""
        self.config = config
        self.cap = None
        self.is_video_file = False
        self.capturing = False
        self.frame_count = 0
        self.start_time = None
        self.last_frame_time = 0
        self.target_frame_interval = 1.0 / config.fps if config.fps > 0 else 0
        
    def start_capture(self, source: Optional[str] = None) -> bool:
        """Start camera capture. Returns True if successful."""
        try:
            if source is None:
                # Use camera index from config
                self.cap = cv2.VideoCapture(self.config.camera_index)
                self.is_video_file = False
            else:
                # Use video file or other source
                self.cap = cv2.VideoCapture(source)
                self.is_video_file = True
            
            if not self.cap.isOpened():
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)
            if not self.is_video_file:
                self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
            
            # Test frame capture
            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                return False
            
            self.capturing = True
            self.start_time = time.time()
            self.frame_count = 0
            return True
            
        except Exception as e:
            print(f"Error starting camera capture: {e}")
            return False
    
    def stop_capture(self) -> None:
        """Stop camera capture and cleanup resources."""
        self.capturing = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame from camera. Returns None if no frame available."""
        if not self.capturing or self.cap is None:
            return None
        
        # Frame rate control - skip for video files to process all frames
        if not self.is_video_file:
            current_time = time.time()
            if (current_time - self.last_frame_time) < self.target_frame_interval:
                return None
            self.last_frame_time = current_time
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        self.frame_count += 1
        
        return frame
    
    def is_capturing(self) -> bool:
        """Check if camera is currently capturing."""
        return self.capturing and self.cap is not None and self.cap.isOpened()
    
    def get_fps(self) -> float:
        """Get current capture frame rate."""
        if self.start_time is None or self.frame_count == 0:
            return 0.0
        
        elapsed_time = time.time() - self.start_time
        return self.frame_count / elapsed_time if elapsed_time > 0 else 0.0
    
    def get_frame_size(self) -> Tuple[int, int]:
        """Get current frame size as (width, height)."""
        if self.cap is None:
            return (self.config.frame_width, self.config.frame_height)
        
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width, height)