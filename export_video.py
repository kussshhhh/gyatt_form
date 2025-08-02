#!/usr/bin/env python3
"""
Video Export Script for GYATT Form

Exports processed videos with skeleton overlay and analysis data.
Saves output to ~/Downloads for easy access.
"""

import cv2
import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gyatt_form.config.defaults import get_default_processing_config, get_default_validation_config
from gyatt_form.vision.camera import CameraManager
from gyatt_form.vision.detector import PoseDetector
from gyatt_form.vision.frame_processor import FrameProcessor
from gyatt_form.analysis.state_machine import MovementStateMachine
from gyatt_form.analysis.rep_counter import RepCounter
from gyatt_form.utils.geometry import AngleCalculator
from gyatt_form.utils.video_controls import VideoTransformer
from gyatt_form.ui.modern_display import render_modern_ui
from gyatt_form.ui.modern_skeleton import draw_modern_landmarks


class VideoExporter:
    """Export videos with pose analysis overlay."""
    
    def __init__(self):
        """Initialize video exporter."""
        # Load configurations
        self.processing_config = get_default_processing_config()
        self.validation_config = get_default_validation_config()
        
        # Initialize components
        self.camera_manager = None
        self.pose_detector = None
        self.frame_processor = None
        self.state_machine = None
        self.rep_counter = None
        self.video_transformer = VideoTransformer()
        
        # Export settings
        self.video_writer = None
        self.total_frames = 0
        self.processed_frames = 0
        
        # UI configuration - use modern UI for exports
        self.use_modern_ui = True
        
    def initialize_components(self):
        """Initialize all processing components."""
        try:
            print("📦 Initializing components...")
            self.camera_manager = CameraManager(self.processing_config)
            self.pose_detector = PoseDetector(self.processing_config)
            self.frame_processor = FrameProcessor(self.processing_config)
            self.state_machine = MovementStateMachine(self.validation_config)
            self.rep_counter = RepCounter(self.validation_config)
            return True
        except Exception as e:
            print(f"❌ Failed to initialize components: {e}")
            return False
    
    def export_video(self, input_path: str, output_filename: str = None):
        """Export video with pose analysis overlay."""
        if not os.path.exists(input_path):
            print(f"❌ Input video not found: {input_path}")
            return False
        
        # Generate output filename if not provided - default to MP4
        if output_filename is None:
            input_name = Path(input_path).stem
            output_filename = f"{input_name}_analyzed.mp4"
        
        # Output to Downloads folder
        downloads_path = Path.home() / "Downloads"
        output_path = downloads_path / output_filename
        
        print(f"🎬 Exporting: {Path(input_path).name}")
        print(f"📁 Output: {output_path}")
        
        # Initialize components
        if not self.initialize_components():
            return False
        
        # Start video capture
        if not self.camera_manager.start_capture(input_path):
            print(f"❌ Failed to open video: {input_path}")
            return False
        
        # Get video properties
        cap = self.camera_manager.cap
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Get original video dimensions
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"📐 Original video dimensions: {width}x{height}")
        
        if width <= 0 or height <= 0:
            print("❌ Could not get video dimensions")
            return False
        
        # Try multiple codecs - prioritize MP4 for better compression and compatibility
        codecs_to_try = [
            ('mp4v', '.mp4'),   # MPEG-4 - best compatibility for MP4
            ('XVID', '.mp4'),   # XVID in MP4 - excellent compression
            ('MJPG', '.mp4'),   # MJPEG in MP4 - good compatibility
            ('XVID', '.avi'),   # XVID in AVI - fallback with good compression
            ('MJPG', '.avi'),   # MJPEG in AVI - maximum compatibility fallback
        ]
        
        self.video_writer = None
        for codec, ext in codecs_to_try:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            test_output = output_path.with_suffix(ext)
            writer = cv2.VideoWriter(str(test_output), fourcc, fps, (width, height))
            
            if writer.isOpened():
                print(f"✅ Using {codec} codec with {ext} format")
                self.video_writer = writer
                output_path = test_output
                break
            else:
                writer.release()
                print(f"❌ {codec} codec failed")
        
        if self.video_writer is None:
            print("❌ No compatible video codec found")
            return False
        
        if not self.video_writer.isOpened():
            print(f"❌ Failed to open video writer")
            return False
        
        print(f"📹 Video writer setup: {width}x{height} @ {fps:.1f} FPS")
        
        # Ensure video starts from beginning
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        print(f"📍 Video position reset to frame 0")
        
        print(f"🚀 Processing {self.total_frames} frames...")
        
        # Process all frames
        rep_count = 0
        start_time = time.time()
        
        while True:
            frame = self.camera_manager.get_frame()
            if frame is None:
                print(f"📊 End of video reached at frame {self.processed_frames}")
                break
            
            # Process frame normally
            processed_frame = self.process_frame(frame)
            
            # Validate and resize frame if needed
            if processed_frame is None:
                continue
            
            if len(processed_frame.shape) != 3:
                continue
            
            # Resize frame to match video writer dimensions if needed
            frame_height, frame_width = processed_frame.shape[:2]
            if (frame_height, frame_width) != (height, width):
                processed_frame = cv2.resize(processed_frame, (width, height))
            
            # Write frame
            self.video_writer.write(processed_frame)
            
            self.processed_frames += 1
            
            # Show progress
            if self.processed_frames % 30 == 0:  # Every 30 frames
                progress = (self.processed_frames / self.total_frames) * 100
                print(f"⏳ Progress: {progress:.1f}% ({self.processed_frames}/{self.total_frames})")
        
        # Cleanup
        elapsed_time = time.time() - start_time
        final_rep_count = self.rep_counter.get_rep_count()
        
        self.video_writer.release()
        self.camera_manager.stop_capture()
        self.pose_detector.cleanup()
        
        print(f"\n✅ Export completed!")
        print(f"📹 Output: {output_path}")
        print(f"⏱️  Processing time: {elapsed_time:.1f} seconds")
        print(f"🏃 Detected reps: {final_rep_count}")
        
        # Safe FPS calculation
        if elapsed_time > 0:
            fps = self.processed_frames / elapsed_time
            print(f"📊 Processing speed: {fps:.1f} FPS")
        else:
            print(f"📊 Processing speed: {self.processed_frames} frames processed")
        print(f"📊 Total frames processed: {self.processed_frames}/{self.total_frames}")
        
        return True
    
    def process_frame(self, frame):
        """Process single frame with pose analysis."""
        start_time = time.time()
        
        # Apply video transformations
        transformed_frame = self.video_transformer.transform_frame(frame)
        
        # Preprocess frame
        processed_frame = self.frame_processor.preprocess_frame(transformed_frame)
        if processed_frame is None:
            processed_frame = transformed_frame
        
        # Detect pose
        pose_data = self.pose_detector.detect_pose(processed_frame, start_time)
        
        # Create display frame
        display_frame = processed_frame.copy()
        
        # Analyze movement if pose detected
        current_state = None
        elbow_angle = 0.0
        rep_count = 0
        
        if pose_data is not None:
            # Draw pose landmarks with modern styling
            if self.use_modern_ui:
                display_frame = draw_modern_landmarks(display_frame, pose_data)
            else:
                display_frame = self.pose_detector.draw_landmarks(display_frame, pose_data)
            
            # Calculate elbow angle
            elbow_angle = AngleCalculator.calculate_average_elbow_angle(pose_data)
            
            # Update state machine
            current_state = self.state_machine.update_state(pose_data)
            
            # Update rep counter
            rep_completed = self.rep_counter.update(current_state, elbow_angle, 100.0, start_time)
            rep_count = self.rep_counter.get_rep_count()
            
        
        # Render UI overlay
        if self.use_modern_ui:
            # Calculate a mock FPS for display (not meaningful for export)
            mock_fps = 30.0 if self.total_frames > 0 else 0.0
            
            # Use modern UI system
            display_frame = render_modern_ui(
                display_frame, pose_data, elbow_angle, current_state, rep_count, mock_fps
            )
        else:
            # Use classic UI system
            if pose_data is not None:
                # Add analysis info to frame
                confidence_text = f"Confidence: {pose_data.confidence:.2f}"
                keypoint_count = len([kp for kp in pose_data.keypoints.values() if kp.is_visible(0.5)])
                keypoint_text = f"Keypoints: {keypoint_count}/33"
                
                cv2.putText(display_frame, confidence_text, (10, 30), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, keypoint_text, (10, 60), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0), 2)
            
            # Classic analysis info
            y_offset = 90
            if current_state:
                state_text = f"State: {current_state.value.upper()}"
                cv2.putText(display_frame, state_text, (10, y_offset), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 0, 255), 2)
                y_offset += 30
            
            if elbow_angle > 0:
                angle_text = f"Elbow Angle: {elbow_angle:.1f}°"
                cv2.putText(display_frame, angle_text, (10, y_offset), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 255), 2)
                y_offset += 30
            
            rep_text = f"Reps: {rep_count}"
            cv2.putText(display_frame, rep_text, (10, y_offset), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2)
        
        # Add export progress indicator (always show regardless of UI mode)
        progress = (self.processed_frames / self.total_frames) * 100 if self.total_frames > 0 else 0
        progress_text = f"Export Progress: {progress:.1f}%"
        cv2.putText(display_frame, progress_text, (10, display_frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 0), 1)
        
        return display_frame


def main():
    """Main export function."""
    if len(sys.argv) < 2:
        print("🎬 GYATT Form Video Exporter")
        print("Usage: python3 export_video.py <input_video> [output_filename]")
        print("Example: python3 export_video.py /path/to/video.mp4")
        print("Example: python3 export_video.py /path/to/video.mp4 my_analysis.avi")
        return 1
    
    input_path = sys.argv[1]
    output_filename = sys.argv[2] if len(sys.argv) > 2 else None
    
    exporter = VideoExporter()
    
    try:
        success = exporter.export_video(input_path, output_filename)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏸️  Export cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())