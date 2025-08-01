"""
Frame preprocessing and validation for pose detection.

Provides frame preprocessing, quality validation, and optimization
functions to improve pose detection accuracy and performance.
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any

from ..config.processing import ProcessingConfig


class FrameProcessor:
    """
    Handles frame preprocessing and quality validation.
    
    Provides frame enhancement, resizing, format conversion,
    and quality checks for optimal pose detection performance.
    """
    
    def __init__(self, config: ProcessingConfig):
        """Initialize frame processor with configuration."""
        self.config = config
        self.target_size = (config.frame_width, config.frame_height)
        
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Apply complete preprocessing pipeline to frame."""
        if frame is None:
            return None
        
        # Resize frame
        processed_frame = self.resize_frame(frame)
        
        # Basic enhancement
        processed_frame = self.enhance_frame(processed_frame)
        
        # Validate frame quality
        if not self.validate_frame_quality(processed_frame):
            return None
        
        return processed_frame
    
    def resize_frame(self, frame: np.ndarray, maintain_aspect: bool = True) -> np.ndarray:
        """Resize frame to target dimensions."""
        if frame is None:
            return None
        
        current_height, current_width = frame.shape[:2]
        target_width, target_height = self.target_size
        
        if not maintain_aspect:
            return cv2.resize(frame, (target_width, target_height))
        
        # Calculate scaling to maintain aspect ratio
        width_ratio = target_width / current_width
        height_ratio = target_height / current_height
        scale = min(width_ratio, height_ratio)
        
        # Calculate new dimensions
        new_width = int(current_width * scale)
        new_height = int(current_height * scale)
        
        # Resize frame
        resized = cv2.resize(frame, (new_width, new_height))
        
        # Add padding if needed
        if new_width != target_width or new_height != target_height:
            # Create black canvas
            canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            
            # Calculate position to center the image
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            
            # Place resized image on canvas
            canvas[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized
            return canvas
        
        return resized
    
    def enhance_frame(self, frame: np.ndarray) -> np.ndarray:
        """Apply basic frame enhancement for better detection."""
        if frame is None:
            return None
        
        # Convert to LAB color space for better processing
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels back
        enhanced_lab = cv2.merge([l, a, b])
        enhanced_frame = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        return enhanced_frame
    
    def validate_frame_quality(self, frame: np.ndarray) -> bool:
        """Validate frame quality for pose detection."""
        if frame is None:
            return False
        
        # Check frame dimensions
        height, width = frame.shape[:2]
        if width < 320 or height < 240:
            return False
        
        # Check if frame is not completely black or white
        mean_intensity = np.mean(frame)
        if mean_intensity < 10 or mean_intensity > 245:
            return False
        
        # Check for sufficient contrast
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        contrast = np.std(gray)
        if contrast < 15:  # Too low contrast
            return False
        
        return True
    
    def calculate_frame_metrics(self, frame: np.ndarray) -> Dict[str, Any]:
        """Calculate frame quality metrics."""
        if frame is None:
            return {}
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate various metrics
        metrics = {
            'brightness': np.mean(gray),
            'contrast': np.std(gray),
            'sharpness': cv2.Laplacian(gray, cv2.CV_64F).var(),
            'width': frame.shape[1],
            'height': frame.shape[0],
            'channels': frame.shape[2] if len(frame.shape) > 2 else 1
        }
        
        return metrics
    
    def detect_motion(self, current_frame: np.ndarray, previous_frame: np.ndarray, 
                     threshold: float = 30.0) -> Tuple[bool, float]:
        """Detect motion between consecutive frames."""
        if current_frame is None or previous_frame is None:
            return False, 0.0
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
        
        # Resize to same dimensions if needed
        if gray1.shape != gray2.shape:
            gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))
        
        # Calculate absolute difference
        diff = cv2.absdiff(gray1, gray2)
        
        # Calculate motion score
        motion_score = np.mean(diff)
        
        return motion_score > threshold, motion_score
    
    def apply_noise_reduction(self, frame: np.ndarray) -> np.ndarray:
        """Apply noise reduction to frame."""
        if frame is None:
            return None
        
        # Apply bilateral filter to reduce noise while preserving edges
        denoised = cv2.bilateralFilter(frame, 9, 75, 75)
        return denoised
    
    def normalize_lighting(self, frame: np.ndarray) -> np.ndarray:
        """Normalize lighting conditions across the frame."""
        if frame is None:
            return None
        
        # Convert to YUV color space
        yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
        
        # Apply histogram equalization to Y channel
        yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
        
        # Convert back to BGR
        normalized = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        return normalized