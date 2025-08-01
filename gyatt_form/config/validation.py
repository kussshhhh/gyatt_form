"""
Form validation configuration for exercise analysis.

Contains parameters and thresholds used for validating exercise form,
specifically push-up analysis and movement validation.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class FormValidationConfig:
    """
    Configuration for exercise form validation.
    
    Attributes:
        # Angle thresholds for push-up positions
        elbow_angle_up_min: Minimum elbow angle for "up" position (degrees)
        elbow_angle_up_max: Maximum elbow angle for "up" position (degrees)
        elbow_angle_down_min: Minimum elbow angle for "down" position (degrees)
        elbow_angle_down_max: Maximum elbow angle for "down" position (degrees)
        
        # Body alignment thresholds
        body_alignment_threshold: Maximum deviation from straight line (degrees)
        hip_sag_threshold: Maximum hip sag angle (degrees)
        
        # Movement validation
        min_movement_speed: Minimum speed for valid movement (pixels/frame)
        max_movement_speed: Maximum speed for valid movement (pixels/frame)
        transition_smoothness_threshold: Threshold for smooth transitions
        
        # State detection
        position_hold_frames: Frames to hold before confirming position
        transition_min_frames: Minimum frames for transition state
        
        # Quality scoring weights
        form_weight: Weight for form accuracy in scoring
        speed_weight: Weight for movement speed in scoring
        consistency_weight: Weight for movement consistency in scoring
    """
    
    # Push-up angle thresholds (degrees)
    elbow_angle_up_min: float = 150.0
    elbow_angle_up_max: float = 180.0
    elbow_angle_down_min: float = 45.0
    elbow_angle_down_max: float = 90.0
    
    # Body alignment thresholds (degrees)
    body_alignment_threshold: float = 15.0
    hip_sag_threshold: float = 20.0
    shoulder_hip_ankle_alignment: float = 10.0
    
    # Movement validation
    min_movement_speed: float = 1.0
    max_movement_speed: float = 50.0
    transition_smoothness_threshold: float = 0.8
    
    # State detection (frames)
    position_hold_frames: int = 5
    transition_min_frames: int = 3
    max_transition_frames: int = 30
    
    # Quality scoring weights (should sum to 1.0)
    form_weight: float = 0.5
    speed_weight: float = 0.3
    consistency_weight: float = 0.2
    
    # Rep counting
    min_rep_duration_frames: int = 15
    max_rep_duration_frames: int = 180
    
    # Critical keypoints for push-up analysis
    required_keypoints: List[str] = None
    
    def __post_init__(self):
        """Initialize default required keypoints if not provided."""
        if self.required_keypoints is None:
            self.required_keypoints = [
                'left_shoulder', 'right_shoulder',
                'left_elbow', 'right_elbow',
                'left_wrist', 'right_wrist',
                'left_hip', 'right_hip',
                'left_knee', 'right_knee',
                'left_ankle', 'right_ankle'
            ]
    
    def get_angle_thresholds(self) -> Dict[str, tuple]:
        """Get angle thresholds for different positions."""
        return {
            'up': (self.elbow_angle_up_min, self.elbow_angle_up_max),
            'down': (self.elbow_angle_down_min, self.elbow_angle_down_max)
        }
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        # Check angle ranges
        if not (0 <= self.elbow_angle_down_min < self.elbow_angle_down_max <= 180):
            return False
        if not (0 <= self.elbow_angle_up_min < self.elbow_angle_up_max <= 180):
            return False
        
        # Check weights sum to 1.0
        weight_sum = self.form_weight + self.speed_weight + self.consistency_weight
        if not (0.99 <= weight_sum <= 1.01):  # Allow small floating point errors
            return False
        
        # Check frame counts are positive
        if any(frames <= 0 for frames in [
            self.position_hold_frames,
            self.transition_min_frames,
            self.min_rep_duration_frames
        ]):
            return False
        
        return True