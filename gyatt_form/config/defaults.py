"""
Default configuration values and factory functions.

Provides convenient access to default configurations and
factory methods for creating common configuration combinations.
"""

from .processing import ProcessingConfig
from .validation import FormValidationConfig


def get_default_processing_config() -> ProcessingConfig:
    """Get default processing configuration optimized for push-up analysis."""
    return ProcessingConfig(
        camera_index=0,
        frame_width=640,
        frame_height=480,
        fps=30,
        detection_confidence=0.5,
        tracking_confidence=0.5,
        visibility_threshold=0.3,
        max_num_poses=1,
        enable_segmentation=False,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        enable_gpu=True,
        buffer_size=10
    )


def get_default_validation_config() -> FormValidationConfig:
    """Get default form validation configuration for push-ups."""
    return FormValidationConfig(
        elbow_angle_up_min=150.0,
        elbow_angle_up_max=180.0,
        elbow_angle_down_min=45.0,
        elbow_angle_down_max=90.0,
        body_alignment_threshold=15.0,
        hip_sag_threshold=20.0,
        shoulder_hip_ankle_alignment=10.0,
        min_movement_speed=1.0,
        max_movement_speed=50.0,
        transition_smoothness_threshold=0.8,
        position_hold_frames=5,
        transition_min_frames=3,
        max_transition_frames=30,
        form_weight=0.5,
        speed_weight=0.3,
        consistency_weight=0.2,
        min_rep_duration_frames=15,
        max_rep_duration_frames=180
    )


def get_high_accuracy_config() -> tuple[ProcessingConfig, FormValidationConfig]:
    """Get configurations optimized for high accuracy analysis."""
    processing = ProcessingConfig(
        camera_index=0,
        frame_width=1280,
        frame_height=720,
        fps=30,
        detection_confidence=0.8,
        tracking_confidence=0.8,
        visibility_threshold=0.7,
        max_num_poses=1,
        enable_segmentation=True,
        smooth_landmarks=True,
        min_detection_confidence=0.8,
        min_tracking_confidence=0.8,
        enable_gpu=True,
        buffer_size=15
    )
    
    validation = FormValidationConfig(
        elbow_angle_up_min=160.0,
        elbow_angle_up_max=180.0,
        elbow_angle_down_min=60.0,
        elbow_angle_down_max=90.0,
        body_alignment_threshold=10.0,
        hip_sag_threshold=15.0,
        shoulder_hip_ankle_alignment=8.0,
        min_movement_speed=0.5,
        max_movement_speed=30.0,
        transition_smoothness_threshold=0.9,
        position_hold_frames=8,
        transition_min_frames=5,
        max_transition_frames=25,
        form_weight=0.6,
        speed_weight=0.2,
        consistency_weight=0.2,
        min_rep_duration_frames=20,
        max_rep_duration_frames=150
    )
    
    return processing, validation


def get_performance_config() -> tuple[ProcessingConfig, FormValidationConfig]:
    """Get configurations optimized for performance over accuracy."""
    processing = ProcessingConfig(
        camera_index=0,
        frame_width=480,
        frame_height=360,
        fps=30,
        detection_confidence=0.5,
        tracking_confidence=0.5,
        visibility_threshold=0.5,
        max_num_poses=1,
        enable_segmentation=False,
        smooth_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        enable_gpu=True,
        buffer_size=5
    )
    
    validation = FormValidationConfig(
        elbow_angle_up_min=140.0,
        elbow_angle_up_max=180.0,
        elbow_angle_down_min=40.0,
        elbow_angle_down_max=100.0,
        body_alignment_threshold=20.0,
        hip_sag_threshold=25.0,
        shoulder_hip_ankle_alignment=15.0,
        min_movement_speed=2.0,
        max_movement_speed=60.0,
        transition_smoothness_threshold=0.7,
        position_hold_frames=3,
        transition_min_frames=2,
        max_transition_frames=35,
        form_weight=0.4,
        speed_weight=0.4,
        consistency_weight=0.2,
        min_rep_duration_frames=10,
        max_rep_duration_frames=200
    )
    
    return processing, validation