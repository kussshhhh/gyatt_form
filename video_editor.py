#!/usr/bin/env python3
"""
GYATT Form Video Editor

Interactive video editor for analyzing pushup form with export capabilities.
Provides timeline scrubbing, multiple view modes, and video export.
"""

import cv2
import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gyatt_form.main import GyattFormApp
from gyatt_form.vision.detector import PoseDetector
from gyatt_form.analysis.state_machine import MovementStateMachine
from gyatt_form.analysis.rep_counter import RepCounter
from gyatt_form.utils.geometry import AngleCalculator
from gyatt_form.utils.video_controls import VideoTransformer
from gyatt_form.config.defaults import get_default_processing_config, get_default_validation_config


class VideoEditor:
    """Interactive video editor for pushup analysis."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GYATT Form Video Editor")
        self.root.geometry("1200x800")
        
        # Video processing components
        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.fps = 30
        self.current_frame = 0
        
        # Analysis components
        self.processing_config = get_default_processing_config()
        self.validation_config = get_default_validation_config()
        self.pose_detector = None
        self.state_machine = None
        self.rep_counter = None
        self.video_transformer = VideoTransformer()
        
        # Processed data cache
        self.frame_cache = {}
        self.analysis_cache = {}
        
        # UI state
        self.is_playing = False
        self.view_mode = tk.StringVar(value="combined")
        self.export_format = tk.StringVar(value="mp4")
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface."""
        # Main menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Video", command=self.open_video)
        file_menu.add_command(label="Export Video", command=self.export_video)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video display area
        self.video_frame = ttk.Frame(main_frame)
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        
        self.video_label = ttk.Label(self.video_frame, text="Open a video to start analysis")
        self.video_label.pack(expand=True)
        
        # Controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Playback controls
        playback_frame = ttk.Frame(controls_frame)
        playback_frame.pack(fill=tk.X)
        
        ttk.Button(playback_frame, text="⏮", command=self.prev_frame).pack(side=tk.LEFT)
        self.play_button = ttk.Button(playback_frame, text="▶", command=self.toggle_play)
        self.play_button.pack(side=tk.LEFT)
        ttk.Button(playback_frame, text="⏭", command=self.next_frame).pack(side=tk.LEFT)
        
        # Timeline slider
        self.timeline = ttk.Scale(playback_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                 command=self.on_timeline_change)
        self.timeline.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Frame info
        self.frame_info = ttk.Label(playback_frame, text="Frame: 0/0")
        self.frame_info.pack(side=tk.RIGHT)
        
        # View options
        options_frame = ttk.LabelFrame(controls_frame, text="View Options")
        options_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Radiobutton(options_frame, text="Original", variable=self.view_mode, 
                       value="original", command=self.update_display).pack(side=tk.LEFT)
        ttk.Radiobutton(options_frame, text="Skeleton Only", variable=self.view_mode,
                       value="skeleton", command=self.update_display).pack(side=tk.LEFT)
        ttk.Radiobutton(options_frame, text="Combined", variable=self.view_mode,
                       value="combined", command=self.update_display).pack(side=tk.LEFT)
        
        # Analysis info
        analysis_frame = ttk.LabelFrame(controls_frame, text="Analysis")
        analysis_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.analysis_info = ttk.Label(analysis_frame, text="No analysis data")
        self.analysis_info.pack(side=tk.LEFT)
        
        ttk.Button(analysis_frame, text="Process All Frames", 
                  command=self.process_all_frames).pack(side=tk.RIGHT)
        
        # Export options
        export_frame = ttk.LabelFrame(controls_frame, text="Export")
        export_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(export_frame, text="Format:").pack(side=tk.LEFT)
        ttk.Combobox(export_frame, textvariable=self.export_format, 
                    values=["mp4", "avi", "mov"], width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(export_frame, text="Export Video", 
                  command=self.export_video).pack(side=tk.RIGHT)
        
    def open_video(self):
        """Open video file for analysis."""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.load_video(file_path)
    
    def load_video(self, video_path):
        """Load video and initialize analysis components."""
        self.video_path = video_path
        
        # Open video capture
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open video file")
            return
        
        # Get video properties
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        # Update timeline
        self.timeline.config(to=self.total_frames - 1)
        self.current_frame = 0
        
        # Initialize analysis components
        self.pose_detector = PoseDetector(self.processing_config)
        self.state_machine = MovementStateMachine(self.validation_config)
        self.rep_counter = RepCounter(self.validation_config)
        
        # Clear caches
        self.frame_cache.clear()
        self.analysis_cache.clear()
        
        # Load first frame
        self.seek_to_frame(0)
        
        print(f"Loaded video: {Path(video_path).name}")
        print(f"Frames: {self.total_frames}, FPS: {self.fps:.1f}")
    
    def seek_to_frame(self, frame_num):
        """Seek to specific frame number."""
        if not self.cap:
            return
        
        frame_num = max(0, min(frame_num, self.total_frames - 1))
        self.current_frame = frame_num
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = self.cap.read()
        
        if ret:
            # Cache original frame
            self.frame_cache[frame_num] = frame.copy()
            
            # Process frame if not already cached
            if frame_num not in self.analysis_cache:
                self.process_frame(frame_num, frame)
            
            self.update_display()
            self.update_ui()
    
    def process_frame(self, frame_num, frame):
        """Process single frame for analysis."""
        # Transform frame if needed
        transformed_frame = self.video_transformer.transform_frame(frame)
        
        # Detect pose
        pose_data = self.pose_detector.detect_pose(transformed_frame)
        
        analysis_data = {
            'pose_data': pose_data,
            'elbow_angle': 0.0,
            'state': None,
            'rep_count': 0
        }
        
        if pose_data:
            # Calculate elbow angle
            analysis_data['elbow_angle'] = AngleCalculator.calculate_average_elbow_angle(pose_data)
            
            # Update state machine (for this frame only)
            current_state = self.state_machine.determine_state_from_angle(analysis_data['elbow_angle'])
            analysis_data['state'] = current_state
            
            # Draw skeleton
            skeleton_frame = np.zeros_like(transformed_frame)
            skeleton_frame = self.pose_detector.draw_landmarks(skeleton_frame, pose_data)
            analysis_data['skeleton_frame'] = skeleton_frame
            
            # Draw combined
            combined_frame = transformed_frame.copy()
            combined_frame = self.pose_detector.draw_landmarks(combined_frame, pose_data)
            analysis_data['combined_frame'] = combined_frame
        
        self.analysis_cache[frame_num] = analysis_data
    
    def process_all_frames(self):
        """Process all frames in background thread."""
        def process_worker():
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Processing Video")
            progress_window.geometry("400x100")
            
            ttk.Label(progress_window, text="Processing all frames...").pack(pady=10)
            progress_bar = ttk.Progressbar(progress_window, maximum=self.total_frames)
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            
            # Reset analysis components for full processing
            self.state_machine = MovementStateMachine(self.validation_config)
            self.rep_counter = RepCounter(self.validation_config)
            
            for frame_num in range(self.total_frames):
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = self.cap.read()
                
                if ret:
                    self.process_frame(frame_num, frame)
                    
                    # Update state machine for continuous analysis
                    if frame_num in self.analysis_cache:
                        analysis = self.analysis_cache[frame_num]
                        if analysis['pose_data']:
                            state = self.state_machine.update_state(analysis['pose_data'])
                            analysis['state'] = state
                            
                            # Update rep counter
                            rep_completed = self.rep_counter.update(state, analysis['elbow_angle'])
                            analysis['rep_count'] = self.rep_counter.get_rep_count()
                
                progress_bar['value'] = frame_num + 1
                progress_window.update()
            
            progress_window.destroy()
            self.seek_to_frame(self.current_frame)  # Refresh display
            messagebox.showinfo("Complete", "Video processing complete!")
        
        if self.cap:
            threading.Thread(target=process_worker, daemon=True).start()
    
    def update_display(self):
        """Update the video display based on current view mode."""
        if not self.cap or self.current_frame not in self.frame_cache:
            return
        
        mode = self.view_mode.get()
        original_frame = self.frame_cache[self.current_frame]
        
        if mode == "original":
            display_frame = original_frame
        elif mode == "skeleton" and self.current_frame in self.analysis_cache:
            analysis = self.analysis_cache[self.current_frame]
            if 'skeleton_frame' in analysis:
                display_frame = analysis['skeleton_frame']
            else:
                display_frame = np.zeros_like(original_frame)
        elif mode == "combined" and self.current_frame in self.analysis_cache:
            analysis = self.analysis_cache[self.current_frame]
            if 'combined_frame' in analysis:
                display_frame = analysis['combined_frame']
            else:
                display_frame = original_frame
        else:
            display_frame = original_frame
        
        # Convert to tkinter format
        display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        
        # Resize for display
        height, width = display_frame_rgb.shape[:2]
        max_width, max_height = 800, 600
        
        if width > max_width or height > max_height:
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            display_frame_rgb = cv2.resize(display_frame_rgb, (new_width, new_height))
        
        # Convert to PhotoImage
        from PIL import Image, ImageTk
        image = Image.fromarray(display_frame_rgb)
        photo = ImageTk.PhotoImage(image)
        
        self.video_label.config(image=photo, text="")
        self.video_label.image = photo  # Keep reference
    
    def update_ui(self):
        """Update UI elements."""
        # Update timeline
        self.timeline.set(self.current_frame)
        
        # Update frame info
        self.frame_info.config(text=f"Frame: {self.current_frame}/{self.total_frames}")
        
        # Update analysis info
        if self.current_frame in self.analysis_cache:
            analysis = self.analysis_cache[self.current_frame]
            info_text = f"Angle: {analysis['elbow_angle']:.1f}°"
            if analysis['state']:
                info_text += f" | State: {analysis['state'].value.upper()}"
            if 'rep_count' in analysis:
                info_text += f" | Reps: {analysis['rep_count']}"
            self.analysis_info.config(text=info_text)
        else:
            self.analysis_info.config(text="No analysis data")
    
    def on_timeline_change(self, value):
        """Handle timeline slider change."""
        frame_num = int(float(value))
        if frame_num != self.current_frame:
            self.seek_to_frame(frame_num)
    
    def toggle_play(self):
        """Toggle play/pause."""
        self.is_playing = not self.is_playing
        self.play_button.config(text="⏸" if self.is_playing else "▶")
        
        if self.is_playing:
            self.play_video()
    
    def play_video(self):
        """Play video at normal speed."""
        if not self.is_playing or not self.cap:
            return
        
        if self.current_frame < self.total_frames - 1:
            self.seek_to_frame(self.current_frame + 1)
            
            # Schedule next frame
            delay = int(1000 / self.fps) if self.fps > 0 else 33
            self.root.after(delay, self.play_video)
        else:
            # End of video
            self.is_playing = False
            self.play_button.config(text="▶")
    
    def prev_frame(self):
        """Go to previous frame."""
        self.seek_to_frame(self.current_frame - 1)
    
    def next_frame(self):
        """Go to next frame."""
        self.seek_to_frame(self.current_frame + 1)
    
    def export_video(self):
        """Export processed video."""
        if not self.cap:
            messagebox.showerror("Error", "No video loaded")
            return
        
        if not self.analysis_cache:
            messagebox.showerror("Error", "No processed frames. Run 'Process All Frames' first.")
            return
        
        # Get export path
        file_path = filedialog.asksaveasfilename(
            title="Export Video",
            defaultextension=f".{self.export_format.get()}",
            filetypes=[
                (f"{self.export_format.get().upper()} files", f"*.{self.export_format.get()}"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        self.export_worker(file_path)
    
    def export_worker(self, output_path):
        """Export video in background thread."""
        def export_thread():
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Exporting Video")
            progress_window.geometry("400x100")
            
            ttk.Label(progress_window, text="Exporting video...").pack(pady=10)
            progress_bar = ttk.Progressbar(progress_window, maximum=self.total_frames)
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            
            # Get frame dimensions
            sample_frame = list(self.frame_cache.values())[0]
            height, width = sample_frame.shape[:2]
            
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, self.fps, (width, height))
            
            mode = self.view_mode.get()
            
            for frame_num in range(self.total_frames):
                if frame_num in self.frame_cache:
                    original_frame = self.frame_cache[frame_num]
                    
                    if mode == "original":
                        export_frame = original_frame
                    elif mode == "skeleton" and frame_num in self.analysis_cache:
                        analysis = self.analysis_cache[frame_num]
                        export_frame = analysis.get('skeleton_frame', np.zeros_like(original_frame))
                    elif mode == "combined" and frame_num in self.analysis_cache:
                        analysis = self.analysis_cache[frame_num]
                        export_frame = analysis.get('combined_frame', original_frame)
                    else:
                        export_frame = original_frame
                    
                    out.write(export_frame)
                
                progress_bar['value'] = frame_num + 1
                progress_window.update()
            
            out.release()
            progress_window.destroy()
            messagebox.showinfo("Complete", f"Video exported to: {output_path}")
        
        threading.Thread(target=export_thread, daemon=True).start()
    
    def run(self):
        """Start the video editor."""
        self.root.mainloop()


def main():
    """Main entry point."""
    editor = VideoEditor()
    
    # Auto-load video if provided as argument
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        if os.path.exists(video_path):
            editor.load_video(video_path)
    
    editor.run()


if __name__ == "__main__":
    main()