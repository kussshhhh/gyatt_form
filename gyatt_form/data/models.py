"""
Core data models for the GYATT Form system.

Defines the fundamental data structures used throughout the application
for pose detection, exercise analysis, and state management.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple
import numpy as np


@dataclass
class Keypoint:
    """
    Represents a single body keypoint detected by pose estimation.
    
    Attributes:
        x: X coordinate (normalized 0-1)
        y: Y coordinate (normalized 0-1) 
        z: Z coordinate (depth, normalized)
        visibility: Confidence score (0-1)
        presence: Whether keypoint is present (0-1)
    """
    x: float
    y: float
    z: float = 0.0
    visibility: float = 1.0
    presence: float = 1.0
    
    def to_pixel_coords(self, width: int, height: int) -> Tuple[int, int]:
        """Convert normalized coordinates to pixel coordinates."""
        return (int(self.x * width), int(self.y * height))
    
    def is_visible(self, threshold: float = 0.5) -> bool:
        """Check if keypoint is visible above threshold."""
        return self.visibility >= threshold


@dataclass
class PoseData:
    """
    Complete pose data containing all detected keypoints.
    
    Attributes:
        keypoints: Dictionary mapping keypoint names to Keypoint objects
        timestamp: Timestamp when pose was detected
        frame_id: Frame identifier
        confidence: Overall pose detection confidence
    """
    keypoints: dict[str, Keypoint]
    timestamp: float
    frame_id: int = 0
    confidence: float = 1.0
    
    def get_keypoint(self, name: str) -> Optional[Keypoint]:
        """Get keypoint by name, returns None if not found."""
        return self.keypoints.get(name)
    
    def has_keypoint(self, name: str, threshold: float = 0.5) -> bool:
        """Check if keypoint exists and is visible."""
        kp = self.get_keypoint(name)
        return kp is not None and kp.is_visible(threshold)
    
    def get_visible_keypoints(self, threshold: float = 0.5) -> dict[str, Keypoint]:
        """Get all keypoints above visibility threshold."""
        return {
            name: kp for name, kp in self.keypoints.items() 
            if kp.is_visible(threshold)
        }


class PushUpState(Enum):
    """
    Enumeration of push-up exercise states.
    
    States:
        UNKNOWN: Cannot determine current state
        UP: Top position (arms extended)
        DOWN: Bottom position (arms bent, chest near ground)
        TRANSITION_DOWN: Moving from up to down
        TRANSITION_UP: Moving from down to up
        RESTING: Not actively performing exercise
    """
    UNKNOWN = "unknown"
    UP = "up"
    DOWN = "down"
    TRANSITION_DOWN = "transition_down"
    TRANSITION_UP = "transition_up"
    RESTING = "resting"
    
    def is_transition(self) -> bool:
        """Check if state represents a transition."""
        return self in (self.TRANSITION_DOWN, self.TRANSITION_UP)
    
    def is_position(self) -> bool:
        """Check if state represents a held position."""
        return self in (self.UP, self.DOWN)


# MediaPipe pose landmark names for reference
POSE_LANDMARKS = {
    'nose': 0,
    'left_eye_inner': 1,
    'left_eye': 2,
    'left_eye_outer': 3,
    'right_eye_inner': 4,
    'right_eye': 5,
    'right_eye_outer': 6,
    'left_ear': 7,
    'right_ear': 8,
    'mouth_left': 9,
    'mouth_right': 10,
    'left_shoulder': 11,
    'right_shoulder': 12,
    'left_elbow': 13,
    'right_elbow': 14,
    'left_wrist': 15,
    'right_wrist': 16,
    'left_pinky': 17,
    'right_pinky': 18,
    'left_index': 19,
    'right_index': 20,
    'left_thumb': 21,
    'right_thumb': 22,
    'left_hip': 23,
    'right_hip': 24,
    'left_knee': 25,
    'right_knee': 26,
    'left_ankle': 27,
    'right_ankle': 28,
    'left_heel': 29,
    'right_heel': 30,
    'left_foot_index': 31,
    'right_foot_index': 32,
}

# Type aliases for convenience
KeypointDict = dict[str, Keypoint]
PoseSequence = List[PoseData]