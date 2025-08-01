"""
Pose detection using MediaPipe.

Implements pose detection and keypoint extraction using Google's MediaPipe
framework for real-time human pose estimation.
"""

import mediapipe as mp
import numpy as np
import cv2
import time
from typing import Optional, List

from ..data.models import PoseData, Keypoint, POSE_LANDMARKS
from ..config.processing import ProcessingConfig


class PoseDetector:
    """
    MediaPipe-based pose detection system.
    
    Detects human poses in images and extracts keypoint coordinates
    with confidence scores for downstream analysis.
    """
    
    def __init__(self, config: ProcessingConfig):
        """Initialize pose detector with MediaPipe configuration."""
        self.config = config
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=config.smooth_landmarks,
            enable_segmentation=config.enable_segmentation,
            smooth_segmentation=True,
            min_detection_confidence=config.min_detection_confidence,
            min_tracking_confidence=config.min_tracking_confidence
        )
        
        self.initialized = True
        self.frame_id = 0
        
        # Landmark name mapping
        self.landmark_names = list(POSE_LANDMARKS.keys())
    
    def detect_pose(self, image: np.ndarray, timestamp: float = 0.0) -> Optional[PoseData]:
        """Detect pose in image and return structured pose data."""
        if not self.initialized:
            return None
        
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Make detection
            results = self.pose.process(rgb_image)
            
            if results.pose_landmarks is None:
                return None
            
            # Convert to our data structure
            pose_data = self.process_landmarks(results.pose_landmarks, timestamp)
            pose_data.frame_id = self.frame_id
            self.frame_id += 1
            
            return pose_data
            
        except Exception as e:
            print(f"Error in pose detection: {e}")
            return None
    
    def process_landmarks(self, landmarks, timestamp: float) -> PoseData:
        """Convert MediaPipe landmarks to PoseData structure."""
        keypoints = {}
        
        for i, landmark in enumerate(landmarks.landmark):
            if i < len(self.landmark_names):
                name = self.landmark_names[i]
                keypoint = Keypoint(
                    x=landmark.x,
                    y=landmark.y,
                    z=landmark.z,
                    visibility=landmark.visibility,
                    presence=getattr(landmark, 'presence', 1.0)  # Some MediaPipe versions don't have presence
                )
                keypoints[name] = keypoint
        
        # Calculate overall confidence as average visibility of key landmarks
        key_landmarks = ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']
        confidences = []
        for name in key_landmarks:
            if name in keypoints:
                confidences.append(keypoints[name].visibility)
        
        overall_confidence = np.mean(confidences) if confidences else 0.0
        
        return PoseData(
            keypoints=keypoints,
            timestamp=timestamp if timestamp > 0 else time.time(),
            confidence=overall_confidence
        )
    
    def is_initialized(self) -> bool:
        """Check if detector is properly initialized."""
        return self.initialized and self.pose is not None
    
    def cleanup(self) -> None:
        """Cleanup MediaPipe resources."""
        if self.pose is not None:
            self.pose.close()
        self.initialized = False
    
    def draw_landmarks(self, image: np.ndarray, pose_data: PoseData) -> np.ndarray:
        """Draw pose landmarks on image for visualization."""
        if not pose_data or not pose_data.keypoints:
            return image
        
        # Convert keypoints back to MediaPipe format for drawing
        height, width = image.shape[:2]
        
        # Count visible keypoints for debugging
        visible_keypoints = [kp for kp in pose_data.keypoints.values() if kp.is_visible(0.3)]
        
        # Lower visibility threshold for more visible skeleton
        visibility_threshold = 0.3
        
        # Draw connections between keypoints with thicker, more visible lines
        connections = self.mp_pose.POSE_CONNECTIONS
        lines_drawn = 0
        
        for connection in connections:
            start_idx, end_idx = connection
            if start_idx < len(self.landmark_names) and end_idx < len(self.landmark_names):
                start_name = self.landmark_names[start_idx]
                end_name = self.landmark_names[end_idx]
                
                if start_name in pose_data.keypoints and end_name in pose_data.keypoints:
                    start_kp = pose_data.keypoints[start_name]
                    end_kp = pose_data.keypoints[end_name]
                    
                    if start_kp.is_visible(visibility_threshold) and end_kp.is_visible(visibility_threshold):
                        start_pos = start_kp.to_pixel_coords(width, height)
                        end_pos = end_kp.to_pixel_coords(width, height)
                        
                        # Make lines more visible with different colors for different body parts
                        if any(x in start_name or x in end_name for x in ['nose', 'eye', 'ear', 'mouth']):
                            line_color = (255, 255, 0)  # Yellow for face
                        elif any(x in start_name or x in end_name for x in ['shoulder', 'elbow', 'wrist', 'thumb', 'index', 'pinky']):
                            line_color = (0, 255, 255)  # Cyan for arms/hands  
                        elif any(x in start_name or x in end_name for x in ['hip', 'knee', 'ankle', 'heel', 'foot']):
                            line_color = (255, 0, 255)  # Magenta for legs/feet
                        else:
                            line_color = (0, 255, 0)    # Green for torso
                        
                        # Draw thicker lines with black outline for better visibility
                        cv2.line(image, start_pos, end_pos, (0, 0, 0), 5)     # Black outline
                        cv2.line(image, start_pos, end_pos, line_color, 3)    # Colored line
                        lines_drawn += 1
        
        # Draw keypoints with larger, more visible circles
        keypoints_drawn = 0
        for name, keypoint in pose_data.keypoints.items():
            if keypoint.is_visible(visibility_threshold):
                pos = keypoint.to_pixel_coords(width, height)
                
                # Color-code keypoints by body part
                if 'face' in name or 'nose' in name or 'eye' in name or 'ear' in name or 'mouth' in name:
                    color = (255, 255, 0)  # Yellow for face
                elif 'shoulder' in name or 'elbow' in name or 'wrist' in name or any(x in name for x in ['thumb', 'index', 'pinky']):
                    color = (0, 255, 255)  # Cyan for arms/hands
                elif 'hip' in name or 'knee' in name or 'ankle' in name or 'heel' in name or 'foot' in name:
                    color = (255, 0, 255)  # Magenta for legs/feet
                else:
                    color = (0, 0, 255)    # Red for other
                
                # Draw larger circles with white border for visibility
                cv2.circle(image, pos, 6, (255, 255, 255), 2)  # White border
                cv2.circle(image, pos, 4, color, -1)           # Colored center
                keypoints_drawn += 1
        
        # Add debug info to image
        debug_text = f"Keypoints: {keypoints_drawn}, Lines: {lines_drawn}"
        cv2.putText(image, debug_text, (10, height - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return image