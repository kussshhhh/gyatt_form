"""
Video control utilities for rotation, flipping, and other transformations.

Provides real-time video transformation controls during analysis,
including rotation for vertical videos and mirroring options.
"""

import cv2
import numpy as np
from enum import Enum
from typing import Tuple


class RotationMode(Enum):
    """Video rotation modes."""
    NORMAL = 0          # No rotation
    ROTATE_90_CW = 1    # 90 degrees clockwise
    ROTATE_180 = 2      # 180 degrees
    ROTATE_90_CCW = 3   # 90 degrees counter-clockwise


class VideoTransformer:
    """
    Handles video transformations like rotation and flipping.
    
    Provides real-time controls for adjusting video orientation
    during analysis, particularly useful for vertical videos.
    """
    
    def __init__(self):
        """Initialize video transformer."""
        self.rotation_mode = RotationMode.NORMAL
        self.flip_horizontal = False
        self.flip_vertical = False
        
    def rotate_frame(self, frame: np.ndarray, rotation: RotationMode) -> np.ndarray:
        """Rotate frame according to specified mode."""
        if rotation == RotationMode.NORMAL:
            return frame
        elif rotation == RotationMode.ROTATE_90_CW:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif rotation == RotationMode.ROTATE_180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif rotation == RotationMode.ROTATE_90_CCW:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            return frame
    
    def flip_frame(self, frame: np.ndarray, flip_h: bool = False, flip_v: bool = False) -> np.ndarray:
        """Flip frame horizontally and/or vertically."""
        if flip_h and flip_v:
            return cv2.flip(frame, -1)  # Both axes
        elif flip_h:
            return cv2.flip(frame, 1)   # Horizontal
        elif flip_v:
            return cv2.flip(frame, 0)   # Vertical
        else:
            return frame
    
    def transform_frame(self, frame: np.ndarray) -> np.ndarray:
        """Apply all current transformations to frame."""
        # Apply rotation first
        transformed = self.rotate_frame(frame, self.rotation_mode)
        
        # Apply flipping
        transformed = self.flip_frame(transformed, self.flip_horizontal, self.flip_vertical)
        
        return transformed
    
    def cycle_rotation(self) -> RotationMode:
        """Cycle to next rotation mode."""
        current_value = self.rotation_mode.value
        next_value = (current_value + 1) % 4
        self.rotation_mode = RotationMode(next_value)
        return self.rotation_mode
    
    def toggle_horizontal_flip(self) -> bool:
        """Toggle horizontal flip."""
        self.flip_horizontal = not self.flip_horizontal
        return self.flip_horizontal
    
    def toggle_vertical_flip(self) -> bool:
        """Toggle vertical flip."""
        self.flip_vertical = not self.flip_vertical
        return self.flip_vertical
    
    def reset_transforms(self) -> None:
        """Reset all transformations to normal."""
        self.rotation_mode = RotationMode.NORMAL
        self.flip_horizontal = False
        self.flip_vertical = False
    
    def get_status_text(self) -> str:
        """Get current transformation status as text."""
        status_parts = []
        
        if self.rotation_mode != RotationMode.NORMAL:
            if self.rotation_mode == RotationMode.ROTATE_90_CW:
                status_parts.append("↻90°")
            elif self.rotation_mode == RotationMode.ROTATE_180:
                status_parts.append("↻180°")
            elif self.rotation_mode == RotationMode.ROTATE_90_CCW:
                status_parts.append("↺90°")
        
        if self.flip_horizontal:
            status_parts.append("↔️")
        
        if self.flip_vertical:
            status_parts.append("↕️")
        
        return " ".join(status_parts) if status_parts else "Normal"
    
    def get_control_help(self) -> list:
        """Get list of control instructions."""
        return [
            "Controls:",
            "'r' - Rotate 90° clockwise",
            "'h' - Flip horizontal",
            "'v' - Flip vertical", 
            "'n' - Reset to normal",
            "'c' - Toggle controls",
            "'u' - Toggle UI style",
            "'q' - Quit"
        ]


def detect_video_orientation(frame: np.ndarray) -> str:
    """
    Detect if video appears to be vertical (portrait) or horizontal (landscape).
    
    Args:
        frame: Video frame to analyze
        
    Returns:
        'portrait' or 'landscape'
    """
    height, width = frame.shape[:2]
    aspect_ratio = width / height
    
    if aspect_ratio < 0.8:  # More tall than wide
        return 'portrait'
    elif aspect_ratio > 1.2:  # More wide than tall
        return 'landscape'
    else:
        return 'square'


def suggest_rotation_for_vertical(frame: np.ndarray) -> RotationMode:
    """
    Suggest rotation mode for vertical videos to make them horizontal.
    
    Args:
        frame: Video frame to analyze
        
    Returns:
        Suggested rotation mode
    """
    orientation = detect_video_orientation(frame)
    
    if orientation == 'portrait':
        # For portrait videos, rotating 90° clockwise usually works best
        return RotationMode.ROTATE_90_CW
    else:
        return RotationMode.NORMAL


def add_control_overlay(frame: np.ndarray, transformer: VideoTransformer) -> np.ndarray:
    """Add control instructions overlay to frame."""
    height, width = frame.shape[:2]
    
    # Add semi-transparent background for text
    overlay = frame.copy()
    
    # Control instructions
    controls = transformer.get_control_help()
    y_start = height - (len(controls) + 1) * 25
    
    # Background rectangle
    cv2.rectangle(overlay, (width - 220, y_start - 10), (width - 10, height - 10), (0, 0, 0), -1)
    
    # Blend with original
    frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
    
    # Add text
    for i, control in enumerate(controls):
        y_pos = y_start + i * 20
        color = (0, 255, 255) if i == 0 else (255, 255, 255)  # Yellow for title, white for controls
        cv2.putText(frame, control, (width - 210, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    # Add current status
    status = f"Current: {transformer.get_status_text()}"
    cv2.putText(frame, status, (width - 210, height - 5), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    
    return frame