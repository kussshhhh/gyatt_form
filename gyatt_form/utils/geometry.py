"""
Geometric calculations and utilities for pose analysis.

Provides functions for calculating angles, distances, and geometric
relationships between keypoints for form analysis.
"""

import numpy as np
import math
from typing import Tuple, List, Optional

from ..data.models import Keypoint, PoseData


class AngleCalculator:
    """
    Specialized class for calculating angles and geometric relationships
    for pushup form analysis.
    """
    
    @staticmethod
    def calculate_angle(p1: Keypoint, p2: Keypoint, p3: Keypoint) -> float:
        """Calculate angle at p2 formed by points p1-p2-p3 in degrees."""
        if not all([p1.is_visible(), p2.is_visible(), p3.is_visible()]):
            return 0.0
        
        # Create vectors from p2 to p1 and p2 to p3
        v1 = np.array([p1.x - p2.x, p1.y - p2.y])
        v2 = np.array([p3.x - p2.x, p3.y - p2.y])
        
        # Calculate dot product and magnitudes
        dot_product = np.dot(v1, v2)
        magnitude1 = np.linalg.norm(v1)
        magnitude2 = np.linalg.norm(v2)
        
        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Calculate angle in radians, then convert to degrees
        cos_angle = dot_product / (magnitude1 * magnitude2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)  # Handle numerical errors
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
    
    @staticmethod
    def calculate_elbow_angle(pose_data: PoseData, side: str = 'left') -> float:
        """Calculate elbow angle for specified side."""
        if side == 'left':
            shoulder = pose_data.get_keypoint('left_shoulder')
            elbow = pose_data.get_keypoint('left_elbow')
            wrist = pose_data.get_keypoint('left_wrist')
        else:
            shoulder = pose_data.get_keypoint('right_shoulder')
            elbow = pose_data.get_keypoint('right_elbow')
            wrist = pose_data.get_keypoint('right_wrist')
        
        if not all([shoulder, elbow, wrist]):
            return 0.0
        
        return AngleCalculator.calculate_angle(shoulder, elbow, wrist)
    
    @staticmethod
    def calculate_average_elbow_angle(pose_data: PoseData) -> float:
        """Calculate average of both elbow angles."""
        left_angle = AngleCalculator.calculate_elbow_angle(pose_data, 'left')
        right_angle = AngleCalculator.calculate_elbow_angle(pose_data, 'right')
        
        # If only one side is visible, use that
        if left_angle == 0.0 and right_angle > 0.0:
            return right_angle
        elif right_angle == 0.0 and left_angle > 0.0:
            return left_angle
        elif left_angle > 0.0 and right_angle > 0.0:
            return (left_angle + right_angle) / 2.0
        else:
            return 0.0
    
    @staticmethod
    def calculate_body_alignment(pose_data: PoseData) -> float:
        """Calculate body alignment deviation from straight line (degrees)."""
        # Use center points for better stability
        left_shoulder = pose_data.get_keypoint('left_shoulder')
        right_shoulder = pose_data.get_keypoint('right_shoulder')
        left_hip = pose_data.get_keypoint('left_hip')
        right_hip = pose_data.get_keypoint('right_hip')
        left_ankle = pose_data.get_keypoint('left_ankle')
        right_ankle = pose_data.get_keypoint('right_ankle')
        
        # Calculate center points
        if not all([left_shoulder, right_shoulder, left_hip, right_hip, left_ankle, right_ankle]):
            return 0.0
        
        shoulder_center = Keypoint(
            x=(left_shoulder.x + right_shoulder.x) / 2,
            y=(left_shoulder.y + right_shoulder.y) / 2,
            visibility=min(left_shoulder.visibility, right_shoulder.visibility)
        )
        
        hip_center = Keypoint(
            x=(left_hip.x + right_hip.x) / 2,
            y=(left_hip.y + right_hip.y) / 2,
            visibility=min(left_hip.visibility, right_hip.visibility)
        )
        
        ankle_center = Keypoint(
            x=(left_ankle.x + right_ankle.x) / 2,
            y=(left_ankle.y + right_ankle.y) / 2,
            visibility=min(left_ankle.visibility, right_ankle.visibility)
        )
        
        # Calculate the angle between shoulder-hip and hip-ankle lines
        return AngleCalculator.calculate_angle(shoulder_center, hip_center, ankle_center)


def calculate_distance(p1: Keypoint, p2: Keypoint) -> float:
    """Calculate Euclidean distance between two keypoints."""
    if not (p1.is_visible() and p2.is_visible()):
        return 0.0
    
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    return math.sqrt(dx * dx + dy * dy)


def calculate_line_angle(p1: Keypoint, p2: Keypoint) -> float:
    """Calculate angle of line from p1 to p2 relative to horizontal (degrees)."""
    if not (p1.is_visible() and p2.is_visible()):
        return 0.0
    
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    angle_rad = math.atan2(dy, dx)
    return math.degrees(angle_rad)


def point_to_line_distance(point: Keypoint, line_start: Keypoint, line_end: Keypoint) -> float:
    """Calculate perpendicular distance from point to line."""
    if not all([point.is_visible(), line_start.is_visible(), line_end.is_visible()]):
        return 0.0
    
    # Line vector
    line_vec = np.array([line_end.x - line_start.x, line_end.y - line_start.y])
    # Point vector from line start
    point_vec = np.array([point.x - line_start.x, point.y - line_start.y])
    
    # Calculate distance
    line_length = np.linalg.norm(line_vec)
    if line_length == 0:
        return calculate_distance(point, line_start)
    
    # Project point onto line and calculate perpendicular distance
    projection = np.dot(point_vec, line_vec) / line_length
    closest_point = line_start.x + projection * line_vec[0] / line_length, \
                   line_start.y + projection * line_vec[1] / line_length
    
    dx = point.x - closest_point[0]
    dy = point.y - closest_point[1]
    return math.sqrt(dx * dx + dy * dy)


def get_bounding_box(keypoints: List[Keypoint]) -> Tuple[float, float, float, float]:
    """Get bounding box (min_x, min_y, max_x, max_y) for keypoints."""
    visible_points = [kp for kp in keypoints if kp.is_visible()]
    if not visible_points:
        return (0.0, 0.0, 0.0, 0.0)
    
    min_x = min(kp.x for kp in visible_points)
    min_y = min(kp.y for kp in visible_points)
    max_x = max(kp.x for kp in visible_points)
    max_y = max(kp.y for kp in visible_points)
    
    return (min_x, min_y, max_x, max_y)


def normalize_coordinates(keypoint: Keypoint, width: int, height: int) -> Keypoint:
    """Normalize pixel coordinates to 0-1 range."""
    return Keypoint(
        x=keypoint.x / width,
        y=keypoint.y / height,
        z=keypoint.z,
        visibility=keypoint.visibility,
        presence=keypoint.presence
    )


def denormalize_coordinates(keypoint: Keypoint, width: int, height: int) -> Keypoint:
    """Convert normalized coordinates to pixel coordinates."""
    return Keypoint(
        x=keypoint.x * width,
        y=keypoint.y * height,
        z=keypoint.z,
        visibility=keypoint.visibility,
        presence=keypoint.presence
    )


def calculate_center_of_mass(keypoints: List[Keypoint]) -> Keypoint:
    """Calculate center of mass for a list of keypoints."""
    visible_points = [kp for kp in keypoints if kp.is_visible()]
    if not visible_points:
        return Keypoint(0.0, 0.0, 0.0, 0.0, 0.0)
    
    total_weight = sum(kp.visibility for kp in visible_points)
    if total_weight == 0:
        return Keypoint(0.0, 0.0, 0.0, 0.0, 0.0)
    
    weighted_x = sum(kp.x * kp.visibility for kp in visible_points) / total_weight
    weighted_y = sum(kp.y * kp.visibility for kp in visible_points) / total_weight
    weighted_z = sum(kp.z * kp.visibility for kp in visible_points) / total_weight
    
    return Keypoint(weighted_x, weighted_y, weighted_z, 1.0, 1.0)


def smooth_angle_sequence(angles: List[float], window_size: int = 5) -> List[float]:
    """Apply moving average smoothing to angle sequence."""
    if len(angles) < window_size:
        return angles
    
    smoothed = []
    for i in range(len(angles)):
        start_idx = max(0, i - window_size // 2)
        end_idx = min(len(angles), i + window_size // 2 + 1)
        
        window_angles = angles[start_idx:end_idx]
        smoothed_angle = sum(window_angles) / len(window_angles)
        smoothed.append(smoothed_angle)
    
    return smoothed