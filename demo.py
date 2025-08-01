#!/usr/bin/env python3
"""
Simple demo script to test the GYATT Form vision module.

This script demonstrates the basic camera capture and pose detection
functionality without requiring the full application framework.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gyatt_form.main import GyattFormApp

def main():
    """Run the pushup analysis demo."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GYATT Form Pushup Analysis Demo')
    parser.add_argument('--video', type=str, help='Video file path for analysis')
    parser.add_argument('--camera-index', type=int, default=0, help='Camera device index')
    parser.add_argument('--ui', action='store_true', help='Use graphical interface to select input')
    args = parser.parse_args()
    
    print("=== 🎯 GYATT Form Pushup Analysis Demo ===")
    
    try:
        # Create and configure the application
        app = GyattFormApp()
        
        if args.ui:
            # Use graphical interface
            from gyatt_form.utils.ui_helpers import select_input_source, show_welcome_message, get_video_file_info
            
            show_welcome_message()
            source_type, source_path = select_input_source()
            
            if source_type == 'cancel':
                print("👋 Demo cancelled by user")
                return
            elif source_type == 'video':
                app.set_video_source(source_path)
                video_info = get_video_file_info(source_path)
                print(f"📹 Analyzing video file: {video_info['name']} ({video_info['size_mb']:.1f} MB)")
                print("🏃‍♂️ Performing pushup movement analysis...")
            else:  # camera
                print("📹 Opening camera for real-time pushup analysis...")
                print("👤 Position yourself 3-6 feet from the camera")
                print("💡 Ensure good lighting for best results")
                print("🏃‍♂️ Perform pushups to see rep counting in action!")
        
        elif args.video:
            app.set_video_source(args.video)
            print(f"📹 Analyzing video file: {args.video}")
            print("🏃‍♂️ Performing pushup movement analysis...")
        else:
            print("📹 Opening camera for real-time pushup analysis...")
            print("👤 Position yourself 3-6 feet from the camera")
            print("💡 Ensure good lighting for best results")
            print("🏃‍♂️ Perform pushups to see rep counting in action!")
        
        print("❌ Press 'q' to quit")
        print("=" * 50)
        
        app.run()
        
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("\n🔧 Troubleshooting:")
        if args.video or (args.ui and 'video' in str(e).lower()):
            print("1. Check that the video file exists and is accessible")
            print("2. Ensure video format is supported (mp4, avi, mov, etc.)")
            print("3. Try a different video file")
        else:
            print("1. Make sure your camera is not being used by another application")
            print("2. Check camera permissions") 
            print("3. Try different camera with: python3 demo.py --camera-index 1")
        print("4. Ensure virtual environment is activated:")
        print("   source .venv/bin/activate")
        print("5. For UI mode, ensure tkinter is installed:")
        print("   sudo apt-get install python3-tk  (on Ubuntu/Debian)")
        sys.exit(1)

if __name__ == "__main__":
    main()