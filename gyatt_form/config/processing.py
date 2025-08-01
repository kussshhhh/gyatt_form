"""
Processing configuration for computer vision and pose detection.

Contains all parameters related to video processing, pose detection,
and system performance optimization.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class ProcessingConfig:
    """
    Configuration for video processing and pose detection.
    
    Attributes:
        camera_index: Camera device index (0 for default camera)
        frame_width: Target frame width in pixels
        frame_height: Target frame height in pixels
        fps: Target frames per second
        detection_confidence: Minimum confidence for pose detection (0-1)
        tracking_confidence: Minimum confidence for pose tracking (0-1)
        visibility_threshold: Minimum visibility for keypoints (0-1)
        max_num_poses: Maximum number of poses to detect
        enable_segmentation: Whether to enable pose segmentation
        smooth_landmarks: Whether to apply landmark smoothing
        min_detection_confidence: Minimum detection confidence for MediaPipe
        min_tracking_confidence: Minimum tracking confidence for MediaPipe
    """
    
    # Camera settings
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    fps: int = 30
    
    # Pose detection settings
    detection_confidence: float = 0.5
    tracking_confidence: float = 0.5
    visibility_threshold: float = 0.5
    max_num_poses: int = 1
    
    # MediaPipe specific settings
    enable_segmentation: bool = False
    smooth_landmarks: bool = True
    min_detection_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    
    # Performance settings
    enable_gpu: bool = True
    buffer_size: int = 10
    
    def get_frame_size(self) -> Tuple[int, int]:
        """Get frame size as (width, height) tuple."""
        return (self.frame_width, self.frame_height)
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        if not (0.0 <= self.detection_confidence <= 1.0):
            return False
        if not (0.0 <= self.tracking_confidence <= 1.0):
            return False
        if not (0.0 <= self.visibility_threshold <= 1.0):
            return False
        if self.frame_width <= 0 or self.frame_height <= 0:
            return False
        if self.fps <= 0:
            return False
        return True