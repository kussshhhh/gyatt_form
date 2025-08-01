"""
UI helper utilities for file selection and user interaction.

Provides file dialog functionality and user interface helpers
for selecting video files and other input sources.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os
from typing import Optional, List
from pathlib import Path


class FileSelector:
    """
    Handles file selection dialogs and video file validation.
    
    Provides cross-platform file selection with format validation
    and user-friendly error handling.
    """
    
    # Supported video formats
    SUPPORTED_FORMATS = [
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', 
        '.m4v', '.3gp', '.ogv', '.ts', '.mts', '.m2ts'
    ]
    
    def __init__(self):
        """Initialize file selector."""
        self.root = None
        
    def select_video_file(self, title: str = "Select Video File") -> Optional[str]:
        """
        Open file dialog to select a video file.
        
        Args:
            title: Dialog window title
            
        Returns:
            Selected file path or None if cancelled
        """
        # Create root window if it doesn't exist
        if self.root is None:
            self.root = tk.Tk()
            self.root.withdraw()  # Hide the root window
        
        # Define file types for the dialog
        file_types = [
            ("Video files", " ".join(f"*{ext}" for ext in self.SUPPORTED_FORMATS)),
            ("MP4 files", "*.mp4"),
            ("AVI files", "*.avi"),
            ("MOV files", "*.mov"),
            ("All files", "*.*")
        ]
        
        try:
            file_path = filedialog.askopenfilename(
                title=title,
                filetypes=file_types,
                initialdir=os.path.expanduser("~")
            )
            
            if file_path:
                # Validate the selected file
                if self.validate_video_file(file_path):
                    return file_path
                else:
                    messagebox.showerror(
                        "Invalid File",
                        f"The selected file is not a supported video format.\n\n"
                        f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
                    )
                    return None
            else:
                return None  # User cancelled
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select file: {e}")
            return None
    
    def validate_video_file(self, file_path: str) -> bool:
        """
        Validate if the file is a supported video format.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file is valid, False otherwise
        """
        if not file_path or not os.path.exists(file_path):
            return False
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            return False
        
        # Check file size (must be > 0)
        try:
            if os.path.getsize(file_path) == 0:
                return False
        except OSError:
            return False
        
        return True
    
    def show_info_dialog(self, title: str, message: str) -> None:
        """Show information dialog to user."""
        if self.root is None:
            self.root = tk.Tk()
            self.root.withdraw()
        
        messagebox.showinfo(title, message)
    
    def show_error_dialog(self, title: str, message: str) -> None:
        """Show error dialog to user."""
        if self.root is None:
            self.root = tk.Tk()
            self.root.withdraw()
        
        messagebox.showerror(title, message)
    
    def confirm_dialog(self, title: str, message: str) -> bool:
        """
        Show confirmation dialog.
        
        Returns:
            True if user clicked Yes/OK, False otherwise
        """
        if self.root is None:
            self.root = tk.Tk()
            self.root.withdraw()
        
        return messagebox.askyesno(title, message)
    
    def cleanup(self) -> None:
        """Cleanup UI resources."""
        if self.root:
            self.root.destroy()
            self.root = None


def select_input_source() -> tuple[str, Optional[str]]:
    """
    Interactive dialog to select input source (camera or video file).
    
    Returns:
        Tuple of (source_type, source_path) where:
        - source_type: 'camera' or 'video'
        - source_path: None for camera, file path for video
    """
    root = tk.Tk()
    root.withdraw()
    
    # Ask user to choose input source
    choice = messagebox.askyesnocancel(
        "Select Input Source",
        "Choose your input source:\n\n"
        "🎥 YES - Use Camera (live analysis)\n"
        "📹 NO - Select Video File\n"
        "❌ CANCEL - Exit"
    )
    
    if choice is None:  # Cancel
        root.destroy()
        return 'cancel', None
    elif choice:  # Yes - Camera
        root.destroy()
        return 'camera', None
    else:  # No - Video file
        file_selector = FileSelector()
        video_path = file_selector.select_video_file("Select Pushup Video")
        file_selector.cleanup()
        root.destroy()
        
        if video_path:
            return 'video', video_path
        else:
            return 'cancel', None


def show_welcome_message() -> None:
    """Show welcome message with usage instructions."""
    root = tk.Tk()
    root.withdraw()
    
    messagebox.showinfo(
        "Welcome to GYATT Form",
        "🎯 GYATT Form - Pushup Analysis System\n\n"
        "This application will analyze your pushup form and count repetitions.\n\n"
        "📋 Instructions:\n"
        "• Position yourself 3-6 feet from camera\n"
        "• Ensure good lighting\n"
        "• Perform pushups with proper form\n"
        "• Press 'q' to quit analysis\n\n"
        "Ready to start analysis?"
    )
    
    root.destroy()


def get_video_file_info(file_path: str) -> dict:
    """
    Get basic information about a video file.
    
    Args:
        file_path: Path to video file
        
    Returns:
        Dictionary with file information
    """
    if not os.path.exists(file_path):
        return {}
    
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    file_ext = Path(file_path).suffix.lower()
    
    return {
        'name': file_name,
        'path': file_path,
        'size_mb': file_size / (1024 * 1024),
        'extension': file_ext,
        'exists': True
    }