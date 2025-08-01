#!/usr/bin/env python3
"""
UI Demo script to showcase the graphical file selection interface.

This script demonstrates just the file selection dialog without
running the full analysis pipeline.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gyatt_form.utils.ui_helpers import select_input_source, show_welcome_message, get_video_file_info, FileSelector

def main():
    """Demonstrate the UI file selection interface."""
    print("=== 🖥️ GYATT Form UI Demo ===")
    print("This demo shows the graphical interface for selecting input sources.")
    print("=" * 50)
    
    try:
        # Show welcome message
        show_welcome_message()
        
        # Select input source
        source_type, source_path = select_input_source()
        
        print(f"\n📋 Selection Result:")
        print(f"Source Type: {source_type}")
        
        if source_type == 'cancel':
            print("❌ User cancelled selection")
        elif source_type == 'camera':
            print("📷 Selected: Camera input")
            print("Ready to start camera analysis!")
        elif source_type == 'video':
            print(f"📹 Selected: Video file")
            video_info = get_video_file_info(source_path)
            print(f"File: {video_info['name']}")
            print(f"Size: {video_info['size_mb']:.1f} MB")
            print(f"Path: {video_info['path']}")
            print("Ready to start video analysis!")
        
        print("\n✅ UI Demo completed successfully!")
        print("Run './run_demo.sh' to start the full analysis with this interface.")
        
    except Exception as e:
        print(f"❌ UI Demo failed: {e}")
        print("\nNote: This demo requires tkinter (GUI support)")
        print("Install with: sudo apt-get install python3-tk")

if __name__ == "__main__":
    main()