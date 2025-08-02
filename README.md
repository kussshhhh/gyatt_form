# GYATT Form - Exercise Form Analysis System

A computer vision-based system for analyzing and providing real-time feedback on exercise form, specifically designed for push-up analysis using pose estimation.

## Overview

GYATT Form uses MediaPipe pose estimation to track body keypoints and analyze exercise form in real-time. The system provides instant feedback to help users maintain proper form during workouts and counts reps.



## Quick Start

### 1. Setup with UV (Recommended)
```bash
# Create virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt

# Run the pushup analysis demo
./run_demo.sh

# Or use graphical interface to select input
python3 demo.py --ui

# Or analyze a video file directly
python3 demo.py --video path/to/your/pushup_video.mp4
```
### 2. Activate Environment Manually
```bash
# If using the virtual environment manually
source .venv/bin/activate
python3 demo.py
```

### 3. Controls
- **Press 'q'** to quit the application
- **Position yourself** in front of the camera for best results
- **Good lighting** improves detection accuracy

## System Requirements

- **Python 3.8+**
- **Webcam** (built-in or USB camera)
- **Dependencies:**
  - OpenCV 4.5.0+ (`opencv-python`)
  - MediaPipe 0.8.0+ (`mediapipe`) 
  - NumPy 1.21.0+ (`numpy`)
  - SciPy 1.7.0+ (`scipy`)

## Architecture

The system is built with a modular architecture:

```
gyatt_form/
├── vision/          # Computer vision processing
│   ├── camera.py           # Camera capture and management
│   ├── detector.py         # MediaPipe pose detection  
│   ├── frame_processor.py  # Image preprocessing
│   └── tracker.py          # Keypoint tracking (planned)
├── analysis/        # Form analysis (planned)
├── feedback/        # User feedback (planned)  
├── data/           # Data models and storage
├── utils/          # Utility functions
├── config/         # Configuration management
└── main.py         # Application entry point
```

## What You'll See

When you run the demo, you'll see:
- **Live camera feed** with your pose overlay
- **Skeleton visualization** - green lines connecting keypoints
- **Keypoint dots** - red (high confidence) or yellow (lower confidence)
- **Real-time analysis:**
  - Detection confidence score
  - Number of visible keypoints (out of 33)
  - **Current movement state** (READY, DESCENDING, BOTTOM, ASCENDING, TOP)
  - **Elbow angle** in degrees
  - **Rep counter** - automatically incremented for complete pushups
  - FPS counter

### Console Output:
```
State: DESCENDING | Angle: 145.3° | Reps: 0
State: BOTTOM     | Angle:  78.2° | Reps: 0  
State: ASCENDING  | Angle: 112.5° | Reps: 0
🎉 Rep completed! Total: 1
State: TOP        | Angle: 165.4° | Reps: 1
```

## Configuration

The system uses configuration classes for easy customization:

```python
from gyatt_form.config.defaults import get_default_processing_config

config = get_default_processing_config()
config.frame_width = 1280  # Higher resolution
config.frame_height = 720
config.fps = 60           # Higher frame rate
```

## Usage Examples

### Graphical Interface (Recommended):
```bash
# Use friendly UI to select camera or video file
python3 demo.py --ui

# Main application with UI
python3 -m gyatt_form.main --ui
```

### Camera Analysis:
```bash
# Basic pushup analysis with camera
python3 demo.py

# Use different camera
python3 demo.py --camera-index 1
```

### Video Analysis:
```bash
# Analyze a pushup video directly
python3 demo.py --video workout.mp4

# Using the main application
python3 -m gyatt_form.main --video pushups.avi
```

## 📝 Troubleshooting

**Camera not working?**
- Ensure no other apps are using your camera
- Try different camera index: `--camera-index 1`
- Check camera permissions

**Poor detection?**
- Ensure good lighting
- Stand 3-6 feet from camera
- Wear contrasting colors
- Clear background helps

**Performance issues?**
- Lower resolution in config
- Reduce FPS
- Close other applications