"""
Main entry point for the GYATT Form application.

Orchestrates the complete exercise form analysis pipeline including
camera input, pose detection, form analysis, and real-time feedback.
"""

import cv2
import sys
import argparse
import time
from typing import Optional

from .config.defaults import get_default_processing_config, get_default_validation_config
from .vision.camera import CameraManager
from .vision.detector import PoseDetector
from .vision.frame_processor import FrameProcessor
from .vision.tracker import KeypointTracker
from .analysis.form_analyzer import FormAnalyzer
from .analysis.state_machine import MovementStateMachine
from .analysis.rep_counter import RepCounter
from .utils.geometry import AngleCalculator
from .utils.video_controls import VideoTransformer, detect_video_orientation, suggest_rotation_for_vertical, add_control_overlay
from .utils.rep_analyzer import RepAnalyzer
from .feedback.guidance import GuidanceSystem
from .feedback.visual import VisualFeedback
from .utils.logger import setup_logging, PerformanceLogger
from .utils.ui_helpers import select_input_source, show_welcome_message, get_video_file_info
from .ui.modern_display import render_modern_ui
from .ui.modern_skeleton import draw_modern_landmarks


class GyattFormApp:
    """
    Main application class for GYATT Form analysis system.
    
    Coordinates all system components and manages the main
    application loop for real-time exercise analysis.
    """
    
    def __init__(self, config_mode: str = "default"):
        """Initialize application with specified configuration mode."""
        # For now, use basic logging
        print("Initializing GYATT Form application...")
        
        # Load configurations
        self.processing_config = get_default_processing_config()
        self.validation_config = get_default_validation_config()
        
        # Initialize components
        self.camera_manager = None
        self.pose_detector = None
        self.frame_processor = None
        self.keypoint_tracker = None
        self.form_analyzer = None
        self.state_machine = None
        self.rep_counter = None
        self.guidance_system = None
        self.visual_feedback = None
        
        self.running = False
        self.fps_counter = 0
        self.fps_start_time = time.time()
        
        # Video input support
        self.video_source = None
        
        # Video transformation controls
        self.video_transformer = VideoTransformer()
        self.show_controls = True
        
        # UI configuration
        self.use_modern_ui = True  # Toggle for modern UI vs classic UI
        
        # Rep analysis and logging
        self.rep_analyzer = RepAnalyzer()
    
    def initialize_components(self) -> bool:
        """Initialize all system components. Returns True if successful."""
        try:
            print("Initializing camera manager...")
            self.camera_manager = CameraManager(self.processing_config)
            
            print("Initializing pose detector...")
            self.pose_detector = PoseDetector(self.processing_config)
            
            print("Initializing frame processor...")
            self.frame_processor = FrameProcessor(self.processing_config)
            
            print("Initializing analysis components...")
            self.state_machine = MovementStateMachine(self.validation_config)
            self.rep_counter = RepCounter(self.validation_config)
            
            # For now, skip complex components
            # self.keypoint_tracker = KeypointTracker()
            # self.form_analyzer = FormAnalyzer(self.validation_config)
            # self.guidance_system = GuidanceSystem()
            # self.visual_feedback = VisualFeedback(
            #     self.processing_config.get_frame_size()
            # )
            
            print("All components initialized successfully")
            return True
            
        except Exception as e:
            print(f"Failed to initialize components: {e}")
            return False
    
    def run(self) -> None:
        """Run the main application loop."""
        if not self.initialize_components():
            print("Failed to initialize application")
            return
        
        print("Starting camera capture...")
        if not self.camera_manager.start_capture(self.video_source):
            print("Failed to start camera capture")
            return
        
        self.running = True
        print("Starting GYATT Form analysis...")
        print("Controls: 'q'=quit, 'r'=rotate, 'h'=flip horizontal, 'v'=flip vertical, 'n'=reset, 'c'=toggle controls")
        
        # Check if video appears vertical and suggest rotation
        if self.video_source:
            test_frame = self.camera_manager.get_frame()
            if test_frame is not None:
                orientation = detect_video_orientation(test_frame)
                if orientation == 'portrait':
                    print(f"📱 Detected vertical video! Press 'r' to rotate to horizontal orientation")
        
        try:
            while self.running:
                frame = self.camera_manager.get_frame()
                if frame is None:
                    continue
                
                # Process frame through pipeline
                self.process_frame(frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    rotation = self.video_transformer.cycle_rotation()
                    print(f"🔄 Rotated to: {rotation.name}")
                elif key == ord('h'):
                    flipped = self.video_transformer.toggle_horizontal_flip()
                    print(f"↔️ Horizontal flip: {'ON' if flipped else 'OFF'}")
                elif key == ord('v'):
                    flipped = self.video_transformer.toggle_vertical_flip()
                    print(f"↕️ Vertical flip: {'ON' if flipped else 'OFF'}")
                elif key == ord('n'):
                    self.video_transformer.reset_transforms()
                    print("🔄 Reset to normal orientation")
                elif key == ord('c'):
                    self.show_controls = not self.show_controls
                    print(f"📋 Controls overlay: {'ON' if self.show_controls else 'OFF'}")
                elif key == ord('u'):
                    self.use_modern_ui = not self.use_modern_ui
                    print(f"🎨 UI Mode: {'Modern' if self.use_modern_ui else 'Classic'}")
                    
        except KeyboardInterrupt:
            print("Application interrupted by user")
        except Exception as e:
            print(f"Application error: {e}")
        finally:
            self.cleanup()
    
    def process_frame(self, frame) -> None:
        """Process a single frame through the analysis pipeline."""
        start_time = time.time()
        
        # 1. Apply video transformations first
        transformed_frame = self.video_transformer.transform_frame(frame)
        
        # 2. Preprocess frame
        processed_frame = self.frame_processor.preprocess_frame(transformed_frame)
        if processed_frame is None:
            processed_frame = transformed_frame
        
        # 3. Detect pose
        pose_data = self.pose_detector.detect_pose(processed_frame, start_time)
        
        # 4. Create display frame
        display_frame = processed_frame.copy()
        
        # 4. Analyze movement if pose detected
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
            if rep_completed:
                print(f"🎉 Rep completed! Total: {self.rep_counter.get_rep_count()}")
            
            rep_count = self.rep_counter.get_rep_count()
            
            # Log data for analysis
            keypoint_count = len([kp for kp in pose_data.keypoints.values() if kp.is_visible(0.3)])
            self.rep_analyzer.log_state_transition(
                current_state, elbow_angle, pose_data.confidence, 
                keypoint_count, rep_completed
            )
            
        
        # 5. Calculate FPS for display
        self.fps_counter += 1
        if time.time() - self.fps_start_time >= 1.0:
            fps = self.fps_counter / (time.time() - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = time.time()
            self.current_fps = fps
        
        current_fps = getattr(self, 'current_fps', 0.0)
        
        # 6. Render UI overlay
        if self.use_modern_ui:
            # Use modern UI system
            display_frame = render_modern_ui(
                display_frame, pose_data, elbow_angle, current_state, rep_count, current_fps
            )
        else:
            # Use classic UI system
            if pose_data is not None:
                # Add detection info
                confidence_text = f"Confidence: {pose_data.confidence:.2f}"
                keypoint_count = len([kp for kp in pose_data.keypoints.values() if kp.is_visible(0.5)])
                keypoint_text = f"Keypoints: {keypoint_count}/33"
                
                cv2.putText(display_frame, confidence_text, (10, 30), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, keypoint_text, (10, 60), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(display_frame, "No pose detected", (10, 30), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 255), 2)
            
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
            y_offset += 30
            
            if hasattr(self, 'current_fps'):
                fps_text = f"FPS: {self.current_fps:.1f}"
                cv2.putText(display_frame, fps_text, (10, y_offset), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 0), 2)
        
        # 7. Add control overlay if enabled
        if self.show_controls:
            display_frame = add_control_overlay(display_frame, self.video_transformer)
        else:
            # Just show basic quit instruction
            cv2.putText(display_frame, "Press 'q' to quit, 'c' for controls", (10, display_frame.shape[0] - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # 8. Console output for debugging
        if pose_data is not None:
            visible_kp_count = len([kp for kp in pose_data.keypoints.values() if kp.is_visible(0.3)])
            if current_state and elbow_angle > 0:
                print(f"State: {current_state.value.upper():<12} | Angle: {elbow_angle:6.1f}° | Reps: {rep_count} | Keypoints: {visible_kp_count}")
            elif visible_kp_count > 0:
                print(f"Pose detected with {visible_kp_count} visible keypoints, confidence: {pose_data.confidence:.2f}")
        else:
            # Only print occasionally to avoid spam
            if hasattr(self, '_no_pose_counter'):
                self._no_pose_counter += 1
            else:
                self._no_pose_counter = 1
            
            if self._no_pose_counter % 30 == 0:  # Every 30 frames (~1 second)
                print("No pose detected - check camera/lighting")
        
        # 9. Display frame
        cv2.imshow('GYATT Form - Pushup Analysis', display_frame)
    
    def cleanup(self) -> None:
        """Cleanup resources and save session data."""
        self.running = False
        
        # Save analysis data
        if hasattr(self, 'rep_analyzer'):
            print("\n🔍 Analyzing session data...")
            summary = self.rep_analyzer.save_session_data()
            
            print(f"\n📊 Session Analysis:")
            print(f"  - Rep Success Rate: {summary.success_rate:.1f}%")
            print(f"  - Total Attempts: {summary.rep_attempts}")
            print(f"  - Successful Reps: {summary.successful_reps}")
            
            if summary.common_failure_patterns:
                print(f"  - Common Failures: {', '.join(summary.common_failure_patterns[:3])}")
            
            if summary.recommendations:
                print(f"\n💡 Recommendations:")
                for rec in summary.recommendations[:3]:
                    print(f"  - {rec}")
        
        if self.camera_manager:
            self.camera_manager.stop_capture()
        
        if self.pose_detector:
            self.pose_detector.cleanup()
        
        cv2.destroyAllWindows()
        print("\nApplication cleanup completed")
    
    def set_video_source(self, video_path: str) -> None:
        """Set video file as input source."""
        self.video_source = video_path
    
    def get_session_summary(self) -> dict:
        """Get summary of current session performance."""
        if not self.rep_counter:
            return {}
            
        return {
            'total_reps': self.rep_counter.get_rep_count(),
            'valid_reps': self.rep_counter.get_valid_rep_count(),
            'average_form_score': self.rep_counter.get_average_form_score(),
            'performance_stats': self.rep_counter.get_performance_stats()
        }


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description='GYATT Form - Exercise Form Analysis System'
    )
    
    parser.add_argument(
        '--config-mode',
        choices=['default', 'high-accuracy', 'performance'],
        default='default',
        help='Configuration mode to use'
    )
    
    parser.add_argument(
        '--camera-index',
        type=int,
        default=0,
        help='Camera device index'
    )
    
    parser.add_argument(
        '--video',
        type=str,
        help='Video file path for analysis (instead of camera)'
    )
    
    parser.add_argument(
        '--ui',
        action='store_true',
        help='Use graphical interface to select input source'
    )
    
    parser.add_argument(
        '--no-audio',
        action='store_true',
        help='Disable audio feedback'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    return parser


def main() -> None:
    """Main entry point for the application."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create and configure application
    app = GyattFormApp(config_mode=args.config_mode)
    
    # Handle input source selection
    if args.ui:
        # Use graphical interface to select input
        show_welcome_message()
        source_type, source_path = select_input_source()
        
        if source_type == 'cancel':
            print("👋 Application cancelled by user")
            return
        elif source_type == 'video':
            app.set_video_source(source_path)
            video_info = get_video_file_info(source_path)
            print(f"📹 Using video file: {video_info['name']} ({video_info['size_mb']:.1f} MB)")
        else:  # camera
            print(f"📷 Using camera index: {args.camera_index}")
    elif args.video:
        # Video specified via command line
        app.set_video_source(args.video)
        video_info = get_video_file_info(args.video)
        if video_info:
            print(f"📹 Using video file: {video_info['name']} ({video_info['size_mb']:.1f} MB)")
        else:
            print(f"❌ Video file not found: {args.video}")
            sys.exit(1)
    else:
        # Default to camera
        print(f"📷 Using camera index: {args.camera_index}")
    
    try:
        app.run()
    except Exception as e:
        print(f"Application failed to start: {e}")
        sys.exit(1)
    finally:
        # Print session summary
        summary = app.get_session_summary()
        if summary:
            print("\n=== 📊 Session Summary ===")
            print(f"Total Reps: {summary.get('total_reps', 0)}")
            print(f"Valid Reps: {summary.get('valid_reps', 0)}")
            if summary.get('total_reps', 0) > 0:
                stats = summary.get('performance_stats', {})
                print(f"Average Duration: {stats.get('average_duration', 0):.1f}s per rep")
                print(f"Consistency Score: {stats.get('consistency_score', 0):.1f}/100")


if __name__ == "__main__":
    main()