#!/usr/bin/env python3
"""
Modern UI Display System for GYATT Form

Provides modern, clean UI overlays with panels, gradients, and improved styling.
"""

import cv2
import numpy as np
import time
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum

@dataclass
class UIColors:
    """Mellow, nature-inspired color scheme for UI elements."""
    # Background colors (with alpha for transparency) - darker muted tones
    bg_primary = (45, 35, 40)        # Dark maroon-brown
    bg_secondary = (55, 45, 50)      # Lighter maroon-brown  
    bg_accent = (65, 55, 60)         # Accent maroon-brown
    
    # Text colors - soft and readable
    text_primary = (235, 230, 225)   # Warm off-white
    text_secondary = (200, 195, 190) # Warm light gray
    text_accent = (171, 222, 171)    # Soft sage green
    
    # Status colors - mellow nature palette
    success = (138, 187, 108)        # Mellow green (#8ABB6C)
    warning = (221, 222, 171)        # Soft sage (#DDDEAB)
    error = (217, 44, 84)            # Mellow red (#D92C54)
    info = (171, 222, 171)           # Sage green (#ABDEAB)
    
    # Skeleton colors - nature-inspired mellow tones
    skeleton_face = (221, 222, 171)  # Soft sage for face
    skeleton_arms = (138, 187, 108)  # Mellow green for arms
    skeleton_torso = (147, 47, 103)  # Maroon for torso core
    skeleton_legs = (217, 44, 84)    # Mellow red for legs
    skeleton_outline = (30, 25, 28)  # Dark muted outline

class PanelPosition(Enum):
    """Panel positioning options."""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"

@dataclass
class Panel:
    """UI panel configuration."""
    position: PanelPosition
    width: int
    height: int
    padding: int = 15
    margin: int = 10
    alpha: float = 0.8
    border_radius: int = 8

class ModernUIRenderer:
    """Modern UI rendering system."""
    
    def __init__(self):
        self.colors = UIColors()
        self.animation_time = 0.0
        self.rep_flash_time = 0.0
        self.last_rep_count = 0
        
        # Panel configurations
        self.info_panel = Panel(PanelPosition.TOP_LEFT, 300, 180)
        self.rep_panel = Panel(PanelPosition.TOP_RIGHT, 200, 100)
        self.state_panel = Panel(PanelPosition.BOTTOM_LEFT, 250, 80)
        self.fps_panel = Panel(PanelPosition.BOTTOM_RIGHT, 150, 60)
    
    def draw_rounded_rectangle(self, img: np.ndarray, top_left: Tuple[int, int], 
                             bottom_right: Tuple[int, int], color: Tuple[int, int, int], 
                             alpha: float = 0.8, border_radius: int = 8) -> np.ndarray:
        """Draw a rounded rectangle with transparency."""
        overlay = img.copy()
        
        # Create rounded rectangle mask
        x1, y1 = top_left
        x2, y2 = bottom_right
        
        # Draw main rectangle
        cv2.rectangle(overlay, (x1 + border_radius, y1), 
                     (x2 - border_radius, y2), color, -1)
        cv2.rectangle(overlay, (x1, y1 + border_radius), 
                     (x2, y2 - border_radius), color, -1)
        
        # Draw rounded corners
        cv2.circle(overlay, (x1 + border_radius, y1 + border_radius), 
                  border_radius, color, -1)
        cv2.circle(overlay, (x2 - border_radius, y1 + border_radius), 
                  border_radius, color, -1)
        cv2.circle(overlay, (x1 + border_radius, y2 - border_radius), 
                  border_radius, color, -1)
        cv2.circle(overlay, (x2 - border_radius, y2 - border_radius), 
                  border_radius, color, -1)
        
        # Apply transparency
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        return img
    
    def get_panel_coordinates(self, panel: Panel, frame_width: int, frame_height: int) -> Tuple[int, int, int, int]:
        """Calculate panel coordinates based on position and frame size."""
        margin = panel.margin
        
        if panel.position == PanelPosition.TOP_LEFT:
            x1, y1 = margin, margin
        elif panel.position == PanelPosition.TOP_RIGHT:
            x1, y1 = frame_width - panel.width - margin, margin
        elif panel.position == PanelPosition.BOTTOM_LEFT:
            x1, y1 = margin, frame_height - panel.height - margin
        elif panel.position == PanelPosition.BOTTOM_RIGHT:
            x1, y1 = frame_width - panel.width - margin, frame_height - panel.height - margin
        else:  # CENTER
            x1, y1 = (frame_width - panel.width) // 2, (frame_height - panel.height) // 2
        
        x2, y2 = x1 + panel.width, y1 + panel.height
        return x1, y1, x2, y2
    
    def draw_text_with_shadow(self, img: np.ndarray, text: str, position: Tuple[int, int],
                            font_scale: float = 0.7, color: Tuple[int, int, int] = None,
                            thickness: int = 2, shadow_offset: int = 2) -> None:
        """Draw text with shadow for better readability."""
        if color is None:
            color = self.colors.text_primary
        
        x, y = position
        # Use FONT_HERSHEY_DUPLEX as closest to Inconsolata (monospace-like)
        # Note: OpenCV doesn't support custom fonts directly, but DUPLEX is clean and modern
        font = cv2.FONT_HERSHEY_DUPLEX
        
        # Draw shadow with muted color
        shadow_color = tuple(max(0, c - 40) for c in self.colors.bg_primary)
        cv2.putText(img, text, (x + shadow_offset, y + shadow_offset), 
                   font, font_scale, shadow_color, thickness + 1)
        
        # Draw main text
        cv2.putText(img, text, (x, y), font, font_scale, color, thickness)
    
    def draw_info_panel(self, img: np.ndarray, pose_data: Optional[Any], 
                       elbow_angle: float, current_state: Optional[Any]) -> np.ndarray:
        """Draw the main information panel."""
        frame_height, frame_width = img.shape[:2]
        x1, y1, x2, y2 = self.get_panel_coordinates(self.info_panel, frame_width, frame_height)
        
        # Draw panel background with gradient effect
        self.draw_rounded_rectangle(img, (x1, y1), (x2, y2), 
                                  self.colors.bg_primary, self.info_panel.alpha)
        
        # Add subtle border
        cv2.rectangle(img, (x1, y1), (x2, y2), self.colors.bg_accent, 2)
        
        # Content positioning
        content_x = x1 + self.info_panel.padding
        content_y = y1 + self.info_panel.padding + 25
        line_height = 30
        
        # Title
        self.draw_text_with_shadow(img, "POSE ANALYSIS", (content_x, content_y - 5), 
                                 0.6, self.colors.text_accent, 2)
        
        if pose_data:
            # Confidence with color coding
            confidence = pose_data.confidence
            conf_color = self.colors.success if confidence > 0.8 else \
                        self.colors.warning if confidence > 0.5 else self.colors.error
            
            self.draw_text_with_shadow(img, f"Confidence: {confidence:.2f}", 
                                     (content_x, content_y + line_height), 0.6, conf_color)
            
            # Keypoint count
            keypoint_count = len([kp for kp in pose_data.keypoints.values() if kp.is_visible(0.3)])
            kp_color = self.colors.success if keypoint_count > 25 else \
                      self.colors.warning if keypoint_count > 15 else self.colors.error
            
            self.draw_text_with_shadow(img, f"Keypoints: {keypoint_count}/33", 
                                     (content_x, content_y + 2 * line_height), 0.6, kp_color)
            
            # Current state with enhanced styling
            if current_state:
                state_text = current_state.value.upper()
                state_colors = {
                    'READY': self.colors.info,
                    'TOP': self.colors.success,
                    'DESCENDING': self.colors.warning,
                    'BOTTOM': self.colors.error,
                    'ASCENDING': self.colors.info
                }
                state_color = state_colors.get(state_text, self.colors.text_primary)
                
                self.draw_text_with_shadow(img, f"State: {state_text}", 
                                         (content_x, content_y + 3 * line_height), 0.6, state_color)
            
            # Elbow angle with visual indicator
            if elbow_angle > 0:
                angle_color = self.colors.success if 140 <= elbow_angle <= 170 else \
                             self.colors.warning if 90 <= elbow_angle <= 140 else self.colors.error
                
                self.draw_text_with_shadow(img, f"Elbow: {elbow_angle:.1f}°", 
                                         (content_x, content_y + 4 * line_height), 0.6, angle_color)
                
                # Draw angle indicator bar
                bar_x = content_x + 130
                bar_y = content_y + 4 * line_height - 10
                bar_width = 100
                bar_height = 8
                
                # Background bar
                cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                            self.colors.bg_secondary, -1)
                
                # Angle indicator (0-180 degrees)
                angle_progress = min(elbow_angle / 180.0, 1.0)
                fill_width = int(bar_width * angle_progress)
                cv2.rectangle(img, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), 
                            angle_color, -1)
        else:
            self.draw_text_with_shadow(img, "No pose detected", 
                                     (content_x, content_y + line_height), 0.6, self.colors.error)
        
        return img
    
    def draw_rep_counter(self, img: np.ndarray, rep_count: int) -> np.ndarray:
        """Draw an animated rep counter panel."""
        frame_height, frame_width = img.shape[:2]
        x1, y1, x2, y2 = self.get_panel_coordinates(self.rep_panel, frame_width, frame_height)
        
        # Check for rep increase for animation
        current_time = time.time()
        if rep_count > self.last_rep_count:
            self.rep_flash_time = current_time
            self.last_rep_count = rep_count
        
        # Animation effect for new reps
        flash_duration = 1.0  # seconds
        flash_active = (current_time - self.rep_flash_time) < flash_duration
        
        if flash_active:
            # Pulsing effect
            pulse_factor = abs(np.sin((current_time - self.rep_flash_time) * 10)) * 0.3 + 0.7
            bg_color = tuple(int(c * pulse_factor + (255 - c) * (1 - pulse_factor)) 
                           for c in self.colors.success)
        else:
            bg_color = self.colors.bg_primary
        
        # Draw panel
        self.draw_rounded_rectangle(img, (x1, y1), (x2, y2), bg_color, self.rep_panel.alpha)
        cv2.rectangle(img, (x1, y1), (x2, y2), self.colors.success, 2)
        
        # Rep count text
        content_x = x1 + self.rep_panel.padding
        content_y = y1 + self.rep_panel.padding + 20
        
        self.draw_text_with_shadow(img, "REPS", (content_x, content_y), 0.5, self.colors.text_accent)
        
        # Large rep number
        rep_text = str(rep_count)
        font_scale = 1.5 if flash_active else 1.2
        self.draw_text_with_shadow(img, rep_text, (content_x + 20, content_y + 40), 
                                 font_scale, self.colors.success, 3)
        
        return img
    
    def draw_fps_panel(self, img: np.ndarray, fps: float) -> np.ndarray:
        """Draw FPS performance panel."""
        frame_height, frame_width = img.shape[:2]
        x1, y1, x2, y2 = self.get_panel_coordinates(self.fps_panel, frame_width, frame_height)
        
        # Color code FPS
        fps_color = self.colors.success if fps >= 25 else \
                   self.colors.warning if fps >= 15 else self.colors.error
        
        # Draw panel
        self.draw_rounded_rectangle(img, (x1, y1), (x2, y2), 
                                  self.colors.bg_primary, self.fps_panel.alpha)
        
        # Content
        content_x = x1 + self.fps_panel.padding
        content_y = y1 + self.fps_panel.padding + 20
        
        self.draw_text_with_shadow(img, f"FPS: {fps:.1f}", (content_x, content_y), 
                                 0.6, fps_color)
        
        return img
    
    def render_modern_ui(self, img: np.ndarray, pose_data: Optional[Any], 
                        elbow_angle: float, current_state: Optional[Any], 
                        rep_count: int, fps: float) -> np.ndarray:
        """Render the complete modern UI overlay."""
        self.animation_time = time.time()
        
        # Draw all panels
        img = self.draw_info_panel(img, pose_data, elbow_angle, current_state)
        img = self.draw_rep_counter(img, rep_count)
        img = self.draw_fps_panel(img, fps)
        
        return img

# Global renderer instance
ui_renderer = ModernUIRenderer()

def render_modern_ui(img: np.ndarray, pose_data: Optional[Any], 
                    elbow_angle: float, current_state: Optional[Any], 
                    rep_count: int, fps: float) -> np.ndarray:
    """Convenience function for rendering modern UI."""
    return ui_renderer.render_modern_ui(img, pose_data, elbow_angle, current_state, rep_count, fps)