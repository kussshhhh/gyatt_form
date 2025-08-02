#!/usr/bin/env python3
"""
Modern Skeleton Renderer for GYATT Form

Provides smooth, modern skeleton visualization with enhanced styling.
"""

import cv2
import numpy as np
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass

@dataclass
class SkeletonStyle:
    """Modern skeleton styling configuration with mellow nature colors."""
    # Line styles
    line_thickness = 4
    outline_thickness = 6
    
    # Joint styles  
    joint_radius = 6
    joint_outline_radius = 8
    
    # Colors (BGR format for OpenCV) - nature-inspired mellow tones
    face_color = (171, 222, 221)    # Soft sage for face
    arm_color = (108, 187, 138)     # Mellow green for arms
    torso_color = (103, 47, 147)    # Maroon for torso core
    leg_color = (84, 44, 217)       # Mellow red for legs
    outline_color = (28, 25, 30)    # Dark muted outline
    joint_outline_color = (225, 230, 235)  # Warm off-white outline
    
    # Transparency and effects
    line_alpha = 0.8
    glow_effect = True
    anti_aliasing = True

class ModernSkeletonRenderer:
    """Modern skeleton rendering system with smooth lines and effects."""
    
    def __init__(self):
        self.style = SkeletonStyle()
        
        # Define body part mappings for improved organization
        self.body_parts = {
            'face': ['nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear', 
                    'mouth_left', 'mouth_right'],
            'arms': ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
                    'left_wrist', 'right_wrist', 'left_thumb', 'right_thumb',
                    'left_index', 'right_index', 'left_pinky', 'right_pinky'],
            'torso': ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip'],
            'legs': ['left_hip', 'right_hip', 'left_knee', 'right_knee',
                    'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
                    'left_foot_index', 'right_foot_index']
        }
    
    def get_part_color(self, keypoint_name: str) -> Tuple[int, int, int]:
        """Get color for a body part based on keypoint name."""
        for part_name, keypoints in self.body_parts.items():
            if any(kp in keypoint_name.lower() for kp in keypoints):
                if part_name == 'face':
                    return self.style.face_color
                elif part_name == 'arms':
                    return self.style.arm_color
                elif part_name == 'torso':
                    return self.style.torso_color
                elif part_name == 'legs':
                    return self.style.leg_color
        return self.style.torso_color  # Default color
    
    def draw_smooth_line(self, img: np.ndarray, pt1: Tuple[int, int], pt2: Tuple[int, int],
                        color: Tuple[int, int, int], thickness: int = 4) -> None:
        """Draw a smooth line with anti-aliasing and optional glow effect."""
        if self.style.anti_aliasing:
            # Use LINE_AA for anti-aliasing
            line_type = cv2.LINE_AA
        else:
            line_type = cv2.LINE_8
        
        # Draw outline first
        cv2.line(img, pt1, pt2, self.style.outline_color, 
                self.style.outline_thickness, line_type)
        
        # Draw main line
        cv2.line(img, pt1, pt2, color, thickness, line_type)
        
        # Optional glow effect
        if self.style.glow_effect:
            # Create lighter version of color for glow
            glow_color = tuple(min(255, int(c * 1.3)) for c in color)
            cv2.line(img, pt1, pt2, glow_color, max(1, thickness - 2), line_type)
    
    def draw_smooth_circle(self, img: np.ndarray, center: Tuple[int, int],
                          color: Tuple[int, int, int], radius: int = 6) -> None:
        """Draw a smooth circle with outline and optional glow."""
        # Draw outline
        cv2.circle(img, center, self.style.joint_outline_radius, 
                  self.style.joint_outline_color, -1, cv2.LINE_AA)
        
        # Draw main circle
        cv2.circle(img, center, radius, color, -1, cv2.LINE_AA)
        
        # Optional inner highlight for 3D effect
        if self.style.glow_effect:
            highlight_color = tuple(min(255, int(c * 1.5)) for c in color)
            highlight_radius = max(1, radius - 2)
            offset_center = (center[0] - 1, center[1] - 1)
            cv2.circle(img, offset_center, highlight_radius, highlight_color, -1, cv2.LINE_AA)
    
    def draw_connection_group(self, img: np.ndarray, connections: List[Tuple[str, str]],
                             keypoints: Dict, visibility_threshold: float = 0.3) -> None:
        """Draw a group of connections with consistent styling."""
        for start_name, end_name in connections:
            if start_name in keypoints and end_name in keypoints:
                start_kp = keypoints[start_name]
                end_kp = keypoints[end_name]
                
                if start_kp.is_visible(visibility_threshold) and end_kp.is_visible(visibility_threshold):
                    # Get frame dimensions from first keypoint
                    height, width = img.shape[:2]
                    
                    start_pos = start_kp.to_pixel_coords(width, height)
                    end_pos = end_kp.to_pixel_coords(width, height)
                    
                    # Determine color based on body part
                    color = self.get_part_color(start_name)
                    
                    # Draw smooth line
                    self.draw_smooth_line(img, start_pos, end_pos, color, self.style.line_thickness)
    
    def draw_landmarks(self, img: np.ndarray, pose_data) -> np.ndarray:
        """Draw modern pose landmarks with enhanced styling."""
        if not pose_data or not pose_data.keypoints:
            return img
        
        height, width = img.shape[:2]
        visibility_threshold = 0.3
        
        # Define modern connection groups for better organization
        face_connections = [
            ('nose', 'left_eye'), ('nose', 'right_eye'),
            ('left_eye', 'left_ear'), ('right_eye', 'right_ear'),
            ('mouth_left', 'mouth_right')
        ]
        
        torso_connections = [
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_hip'), ('right_shoulder', 'right_hip'),
            ('left_hip', 'right_hip')
        ]
        
        arm_connections = [
            ('left_shoulder', 'left_elbow'), ('left_elbow', 'left_wrist'),
            ('right_shoulder', 'right_elbow'), ('right_elbow', 'right_wrist'),
            ('left_wrist', 'left_thumb'), ('left_wrist', 'left_index'), ('left_wrist', 'left_pinky'),
            ('right_wrist', 'right_thumb'), ('right_wrist', 'right_index'), ('right_wrist', 'right_pinky')
        ]
        
        leg_connections = [
            ('left_hip', 'left_knee'), ('left_knee', 'left_ankle'),
            ('right_hip', 'right_knee'), ('right_knee', 'right_ankle'),
            ('left_ankle', 'left_heel'), ('left_ankle', 'left_foot_index'),
            ('right_ankle', 'right_heel'), ('right_ankle', 'right_foot_index')
        ]
        
        # Draw connections by body part for consistent coloring
        self.draw_connection_group(img, torso_connections, pose_data.keypoints, visibility_threshold)
        self.draw_connection_group(img, arm_connections, pose_data.keypoints, visibility_threshold)
        self.draw_connection_group(img, leg_connections, pose_data.keypoints, visibility_threshold)
        self.draw_connection_group(img, face_connections, pose_data.keypoints, visibility_threshold)
        
        # Draw keypoints with enhanced styling
        keypoints_drawn = 0
        for name, keypoint in pose_data.keypoints.items():
            if keypoint.is_visible(visibility_threshold):
                pos = keypoint.to_pixel_coords(width, height)
                color = self.get_part_color(name)
                
                # Draw enhanced joint
                self.draw_smooth_circle(img, pos, color, self.style.joint_radius)
                keypoints_drawn += 1
        
        # Add modern debug info with better styling
        if keypoints_drawn > 0:
            debug_bg_height = 30
            debug_bg_width = 200
            
            # Semi-transparent background for debug info
            overlay = img.copy()
            cv2.rectangle(overlay, (10, height - debug_bg_height - 10), 
                         (debug_bg_width, height - 10), (20, 25, 35), -1)
            cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
            
            # Debug text with modern styling
            debug_text = f"Skeleton: {keypoints_drawn} joints"
            cv2.putText(img, debug_text, (15, height - 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        return img
    
    def draw_minimalist_skeleton(self, img: np.ndarray, pose_data, 
                               focus_joints: List[str] = None) -> np.ndarray:
        """Draw a minimalist skeleton focusing on key joints for analysis."""
        if not pose_data or not pose_data.keypoints:
            return img
        
        if focus_joints is None:
            # Focus on pushup-relevant joints
            focus_joints = [
                'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
                'left_wrist', 'right_wrist', 'left_hip', 'right_hip'
            ]
        
        height, width = img.shape[:2]
        visibility_threshold = 0.3
        
        # Key connections for pushup analysis
        key_connections = [
            ('left_shoulder', 'left_elbow'), ('left_elbow', 'left_wrist'),
            ('right_shoulder', 'right_elbow'), ('right_elbow', 'right_wrist'),
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_hip'), ('right_shoulder', 'right_hip')
        ]
        
        # Draw key connections with emphasis
        for start_name, end_name in key_connections:
            if (start_name in pose_data.keypoints and end_name in pose_data.keypoints and
                start_name in focus_joints and end_name in focus_joints):
                
                start_kp = pose_data.keypoints[start_name]
                end_kp = pose_data.keypoints[end_name]
                
                if start_kp.is_visible(visibility_threshold) and end_kp.is_visible(visibility_threshold):
                    start_pos = start_kp.to_pixel_coords(width, height)
                    end_pos = end_kp.to_pixel_coords(width, height)
                    
                    # Use brighter colors for key joints
                    color = self.get_part_color(start_name)
                    enhanced_color = tuple(min(255, int(c * 1.2)) for c in color)
                    
                    self.draw_smooth_line(img, start_pos, end_pos, enhanced_color, 
                                        self.style.line_thickness + 1)
        
        # Draw focus joints with larger circles
        for joint_name in focus_joints:
            if joint_name in pose_data.keypoints:
                keypoint = pose_data.keypoints[joint_name]
                if keypoint.is_visible(visibility_threshold):
                    pos = keypoint.to_pixel_coords(width, height)
                    color = self.get_part_color(joint_name)
                    enhanced_color = tuple(min(255, int(c * 1.2)) for c in color)
                    
                    self.draw_smooth_circle(img, pos, enhanced_color, 
                                          self.style.joint_radius + 2)
        
        return img

# Global renderer instance
skeleton_renderer = ModernSkeletonRenderer()

def draw_modern_landmarks(img: np.ndarray, pose_data) -> np.ndarray:
    """Convenience function for modern landmark drawing."""
    return skeleton_renderer.draw_landmarks(img, pose_data)

def draw_minimalist_skeleton(img: np.ndarray, pose_data, 
                           focus_joints: List[str] = None) -> np.ndarray:
    """Convenience function for minimalist skeleton drawing."""
    return skeleton_renderer.draw_minimalist_skeleton(img, pose_data, focus_joints)