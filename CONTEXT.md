# GYATT Form - Pushup Rep Counting System Context

## Project Overview

GYATT Form is a real-time computer vision system that analyzes pushup form and counts repetitions using MediaPipe pose detection. The system processes video input (camera or file), detects human poses, tracks movement states, and counts valid pushup repetitions.

## Current System Architecture

### 1. **Pose Detection Pipeline**
- **Input**: Video frames (camera or file)
- **MediaPipe**: Detects 33 body keypoints with confidence scores
- **Key Points**: Shoulders, elbows, wrists, hips, knees, ankles
- **Output**: Normalized coordinates (0-1) + visibility/presence scores

### 2. **Movement Analysis Chain**
```
Raw Video → Pose Detection → Angle Calculation → State Machine → Rep Counter
```

#### **Angle Calculation** (`utils/geometry.py`)
- Calculates elbow angles using 3-point geometry (shoulder-elbow-wrist)
- Averages left and right elbow angles
- **Formula**: `angle = arccos(dot_product(v1, v2) / (|v1| * |v2|))`

#### **State Machine** (`analysis/state_machine.py`)
- **States**: `READY`, `TOP`, `DESCENDING`, `BOTTOM`, `ASCENDING`
- **Input**: Elbow angles from pose detection
- **Logic**: Angle-based state determination with hysteresis
- **Output**: Current movement state

#### **Rep Counter** (`analysis/rep_counter.py`)
- **Expected Sequence**: `DESCENDING → BOTTOM → ASCENDING → TOP`
- **Validation**: Duration (2-10s), form score (≥60%), complete sequence
- **Output**: Valid repetition count

### 3. **Current Issues Identified**
1. **Missing Reps**: System sometimes fails to count valid pushups
2. **Incomplete Sequences**: State transitions don't always follow expected pattern
3. **Timing Sensitivity**: Duration thresholds may be too restrictive
4. **Angle Thresholds**: Fixed values may not suit all users/angles

## Parameters Available for Tuning

### **State Machine Parameters** (`analysis/state_machine.py`)

#### **Critical Angle Thresholds**
```python
self.top_threshold = 150.0      # Angle for TOP/READY position (arms extended)
self.bottom_threshold = 90.0    # Angle for BOTTOM position (arms bent)
self.movement_threshold = 5.0   # Minimum angle change to detect movement
```

#### **Smoothing & Stability**
```python
self.transition_hysteresis = 10.0   # Prevents oscillation at boundaries
self.min_state_frames = 3           # Minimum frames to confirm state change
```

#### **State History**
```python
self.state_history = deque(maxlen=10)  # Recent state transitions
self.angle_history = deque(maxlen=5)   # Recent angles for trend analysis
```

### **Rep Counter Parameters** (`analysis/rep_counter.py`)

#### **Sequence Definition**
```python
self.required_sequence = [MovementState.DESCENDING, MovementState.BOTTOM, 
                         MovementState.ASCENDING, MovementState.TOP]
self.valid_start_states = [MovementState.READY, MovementState.TOP]
```

#### **Validation Criteria**
```python
# Duration validation (RepetitionData.is_valid)
reasonable_duration = 2.0 <= self.duration <= 10.0

# Form score validation  
good_form = self.average_form_score >= 60.0

# Sequence completeness
required_states = {MovementState.TOP, MovementState.DESCENDING, 
                  MovementState.BOTTOM, MovementState.ASCENDING}
```

### **Pose Detection Parameters** (`config/defaults.py`)

#### **Detection Confidence**
```python
min_detection_confidence=0.5    # MediaPipe pose detection threshold
min_tracking_confidence=0.5     # MediaPipe tracking threshold
visibility_threshold=0.3        # Keypoint visibility threshold
```

#### **Processing Quality**
```python
frame_width=640, frame_height=480    # Video resolution
smooth_landmarks=True                # MediaPipe smoothing
enable_segmentation=False            # Body segmentation (slower but more accurate)
```

### **Form Validation Parameters** (`config/validation.py`)

#### **Angle Ranges**
```python
elbow_angle_up_min=150.0, elbow_angle_up_max=180.0      # Valid "up" position
elbow_angle_down_min=45.0, elbow_angle_down_max=90.0    # Valid "down" position
```

#### **Body Alignment**
```python
body_alignment_threshold=15.0           # Shoulder-hip-ankle alignment tolerance
hip_sag_threshold=20.0                  # Hip sagging detection
shoulder_hip_ankle_alignment=10.0       # Overall posture tolerance
```

#### **Movement Timing**
```python
min_rep_duration_frames=15              # Minimum frames per rep (~0.5s at 30fps)
max_rep_duration_frames=180             # Maximum frames per rep (~6s at 30fps)
transition_min_frames=3                 # Minimum transition duration
max_transition_frames=30                # Maximum transition duration
```

## Data Collection & Analysis System

### **RepAnalyzer** (`utils/rep_analyzer.py`)
The system now logs comprehensive data for analysis and optimization:

#### **State Transition Logging**
```python
@dataclass
class StateTransition:
    timestamp: float
    from_state: str          # Previous state
    to_state: str           # New state  
    elbow_angle: float      # Angle at transition
    confidence: float       # Pose detection confidence
    keypoint_count: int     # Number of visible keypoints
    duration_in_state: float # Time spent in previous state
```

#### **Rep Attempt Tracking**
```python
@dataclass  
class RepAttempt:
    attempt_id: int
    start_time: float
    end_time: Optional[float]
    duration: Optional[float]
    state_sequence: List[str]     # Complete state progression
    angle_sequence: List[float]   # Angle values throughout attempt
    was_counted: bool            # Whether rep was successfully counted
    failure_reason: Optional[str] # Why rep failed (if applicable)
    quality_score: float         # Calculated quality metric (0-100)
```

#### **Session Analysis**
```python
@dataclass
class SessionSummary:
    session_id: str
    start_time: float
    end_time: float
    total_transitions: int
    rep_attempts: int
    successful_reps: int
    success_rate: float
    common_failure_patterns: List[str]    # Most frequent failure reasons
    angle_statistics: Dict[str, float]    # Min/max/mean angles
    recommendations: List[str]            # Suggested parameter changes
```

## Iteration & Fine-Tuning Strategy

### **Data-Driven Parameter Optimization**

#### **1. Angle Threshold Optimization**
- **Data Source**: StateTransition logs with elbow angles per state
- **Method**: Statistical analysis of angle distributions
- **Optimization**: 
  - TOP threshold = 25th percentile of TOP/READY angles
  - BOTTOM threshold = 75th percentile of BOTTOM angles
  - Movement threshold = based on angle variance during transitions

#### **2. Timing Parameter Optimization**
- **Data Source**: RepAttempt duration analysis
- **Method**: Analyze successful vs failed rep durations
- **Optimization**:
  - Min duration = 80% of fastest successful rep
  - Max duration = 120% of slowest successful rep
  - State frame requirements based on transition stability

#### **3. Sequence Pattern Analysis**
- **Data Source**: state_sequence from RepAttempt logs
- **Method**: Pattern matching and failure classification
- **Common Failure Patterns**:
  - `"never_reached_bottom"` → Lower bottom_threshold
  - `"stuck_at_bottom"` → Reduce movement_threshold  
  - `"pattern_mismatch"` → Relax sequence requirements
  - `"too_slow"` → Increase max_rep_duration

#### **4. Quality Score Calibration**
- **Data Source**: Successful vs failed attempts with quality_score
- **Method**: ROC analysis to find optimal quality threshold
- **Optimization**: Adjust scoring weights based on predictive value

### **Automated Optimization Loop**

#### **Phase 1: Data Collection**
1. Run application on test videos/live sessions
2. RepAnalyzer logs all state transitions and rep attempts
3. Generate session summaries with failure analysis

#### **Phase 2: Analysis & Recommendations**
1. `optimize_parameters.py` analyzes logged data
2. Statistical analysis of angle distributions per state
3. Timing analysis of successful vs failed attempts
4. Pattern analysis of state sequences
5. Generate optimized parameter recommendations

#### **Phase 3: Parameter Updates**
1. Apply recommended parameters to config files
2. A/B testing: compare old vs new parameters
3. Measure success rate improvement
4. Iterate based on results

#### **Phase 4: Validation**
1. Test on diverse video samples
2. Measure precision/recall for rep counting
3. User acceptance testing
4. Edge case analysis

### **Advanced Optimization Techniques**

#### **1. Machine Learning Approaches**
- **Feature Engineering**: Extract features from state sequences, angle progressions
- **Classification**: Train model to predict "valid rep" vs "invalid rep"
- **Regression**: Predict optimal thresholds based on user characteristics
- **Clustering**: Group users by movement patterns, customize parameters per cluster

#### **2. Adaptive Parameters**
- **User Calibration**: Learn individual user's angle ranges during warm-up
- **Real-time Adaptation**: Adjust thresholds based on recent performance
- **Context Awareness**: Different parameters for different exercise variations

#### **3. Multi-Objective Optimization**
- **Objectives**: Maximize true positives, minimize false positives, minimize false negatives
- **Constraints**: Real-time performance, user experience
- **Methods**: Genetic algorithms, Bayesian optimization, grid search with cross-validation

## Current System Status

### **What's Working Well**
1. ✅ Pose detection with MediaPipe is robust and fast
2. ✅ State machine correctly identifies movement phases
3. ✅ Skeleton visualization is clear and responsive  
4. ✅ Video rotation controls work perfectly
5. ✅ Rep counting works for "perfect" pushups

### **What Needs Improvement**
1. ❌ Misses some valid reps (false negatives)
2. ❌ Fixed thresholds don't adapt to different users/angles
3. ❌ Sequence requirements too strict for natural movement
4. ❌ No learning from user feedback
5. ❌ Limited form analysis beyond basic angle checks

### **Next Steps for Optimization**
1. **Immediate**: Run data collection sessions, analyze failure patterns
2. **Short-term**: Implement parameter optimization based on collected data
3. **Medium-term**: Add user calibration and adaptive thresholds
4. **Long-term**: Implement ML-based rep validation and form scoring

## Files & Data Flow

### **Key Files**
- `gyatt_form/main.py` - Main application with integrated RepAnalyzer
- `gyatt_form/analysis/state_machine.py` - Movement state detection
- `gyatt_form/analysis/rep_counter.py` - Rep counting logic
- `gyatt_form/utils/rep_analyzer.py` - Data logging and analysis
- `gyatt_form/config/defaults.py` - Configuration parameters
- `optimize_parameters.py` - Parameter optimization script

### **Data Output**
- `rep_analysis_logs/transitions_*.json` - State transition data
- `rep_analysis_logs/attempts_*.json` - Rep attempt data  
- `rep_analysis_logs/summary_*.json` - Session analysis
- `rep_analysis_logs/optimized_config.json` - Recommended parameters

### **Usage Workflow**
1. Run app: `./run_demo.sh --video "video.mp4"`
2. Perform pushups, system logs all data
3. Exit app, system saves analysis data
4. Run optimization: `python3 optimize_parameters.py`
5. Apply recommended parameters
6. Repeat for continuous improvement

This system provides a complete framework for data-driven optimization of the rep counting algorithm, enabling systematic improvement through real-world usage data.

## Current Project Status & Progress

### **Latest Updates**

#### **Rep Counting Improvements**
- ✅ **Fixed skeleton visibility**: Lowered visibility threshold from 0.5 to 0.3, enhanced drawing with thicker lines and better colors
- ✅ **Fixed presence detection bug**: MediaPipe was setting presence=0.0, updated is_visible() to only check visibility scores
- ✅ **Optimized angle thresholds**: Adjusted bottom_threshold from 90° to 100° for better rep detection
- ✅ **Enhanced state machine responsiveness**: Reduced min_state_frames from 3 to 1, movement_threshold from 5° to 3°
- ✅ **Fixed rep counter reset bug**: Added safeguards to prevent rep counts from going backwards during session
- ✅ **Improved timing sensitivity**: System now catches faster pushups that were previously missed

#### **User Interface & Controls**
- ✅ **Video rotation controls**: Added real-time rotation (r=rotate, h=flip horizontal, v=flip vertical, n=reset)
- ✅ **Graphical file selection**: Created UI helpers for easy video/camera selection instead of command line only
- ✅ **Enhanced visual feedback**: Real-time display of state, elbow angles, rep count, and keypoint confidence
- ✅ **Control overlay**: Toggle-able on-screen controls display (c=toggle controls)

#### **Data Analysis & Optimization**
- ✅ **Comprehensive logging system**: RepAnalyzer logs clean state transitions and rep attempts for analysis
- ✅ **Session analytics**: Automatic failure pattern analysis with recommendations for parameter tuning
- ✅ **Parameter optimization framework**: Automated analysis of angle thresholds, timing, and state transitions

### **Performance Metrics**
- **Current Success Rate**: ~75% (varies by video quality and user movement patterns)
- **Processing Speed**: ~30 FPS real-time analysis with full skeleton overlay
- **Detection Accuracy**: Skeleton overlay working reliably with 26-33 visible keypoints
- **State Machine**: Correctly transitions through READY → TOP → DESCENDING → BOTTOM → ASCENDING → TOP

### **Known Issues & Solutions**
1. **Issue**: Fast pushups sometimes skip BOTTOM state
   - **Status**: ✅ FIXED - Reduced min_state_frames and adjusted thresholds
2. **Issue**: Rep counts going backwards during session
   - **Status**: ✅ FIXED - Added monotonic counting safeguards
3. **Issue**: Skeleton not visible over body
   - **Status**: ✅ FIXED - Enhanced drawing with better colors and thicker lines

## Script Documentation

### **Main Application Scripts**

#### **1. `./run_demo.sh` - Primary Real-Time Analysis**
**Purpose**: Main application for real-time pushup analysis and rep counting
**Usage**: 
```bash
./run_demo.sh                                    # UI mode - select camera/video
./run_demo.sh --video "/path/to/video.mp4"      # Analyze specific video
./run_demo.sh --camera-index 1                  # Use different camera
```
**Features**:
- Real-time pose detection with skeleton overlay
- Live rep counting and state machine display
- Video rotation/transformation controls
- Session data logging for later analysis
- Optimized for smooth performance (~30 FPS)

#### **2. `./run_export.sh` - Video Export**
**Purpose**: Export analyzed videos with skeleton overlay to ~/Downloads
**Usage**:
```bash
./run_export.sh "/path/to/video.mp4"                    # Auto-generated MP4 filename
./run_export.sh "/path/to/video.mp4" "my_analysis.mp4"  # Custom filename
```
**Features**:
- Processes entire video with pose analysis
- Saves with skeleton overlay and analysis data
- Progress tracking during export
- Output automatically saved to ~/Downloads folder
- Uses MP4 format with optimized compression (65% smaller than AVI)
- Automatic codec fallback for maximum compatibility

#### **3. `./run_editor.sh` - Video Editor (Optional)**
**Purpose**: Frame-by-frame video analysis with timeline controls
**Usage**:
```bash
./run_editor.sh "/path/to/video.mp4"    # Open video in editor
```
**Features**:
- Timeline scrubbing and playback controls
- Multiple view modes (original, skeleton-only, combined)
- Frame-by-frame analysis
- Export capabilities
- **Note**: Slower than real-time analysis, use for detailed inspection only

### **Analysis & Optimization Scripts**

#### **4. `python3 optimize_parameters.py` - Parameter Optimization**
**Purpose**: Analyze logged session data and recommend parameter improvements
**Usage**:
```bash
source .venv/bin/activate && python3 optimize_parameters.py
```
**Features**:
- Analyzes state transitions and rep attempts from logged data
- Recommends optimal angle thresholds based on actual movement data
- Identifies common failure patterns and suggests fixes
- Generates optimized configuration files

#### **5. `python3 ui_demo.py` - UI Testing**
**Purpose**: Test the graphical file selection interface
**Usage**:
```bash
source .venv/bin/activate && python3 ui_demo.py
```
**Features**:
- Demonstrates file selection dialogs
- Tests UI components without running full analysis

### **Development & Configuration Files**

#### **Configuration Files**
- `gyatt_form/config/defaults.py` - Main parameter settings
- `gyatt_form/config/processing.py` - Video processing parameters
- `gyatt_form/config/validation.py` - Rep validation criteria

#### **Key Components**
- `gyatt_form/main.py` - Main application logic
- `gyatt_form/analysis/state_machine.py` - Movement state detection
- `gyatt_form/analysis/rep_counter.py` - Rep counting logic
- `gyatt_form/vision/detector.py` - Pose detection and skeleton drawing
- `gyatt_form/utils/rep_analyzer.py` - Data logging and analysis

### **Data Output Locations**
- **Analysis Logs**: `rep_analysis_logs/` (session data, transitions, attempts)
- **Exported Videos**: `~/Downloads/` (processed videos with overlays)
- **Optimization Results**: `rep_analysis_logs/optimized_config.json`

### **Workflow Examples**

#### **Standard Analysis Workflow**
1. `./run_demo.sh --video "my_pushups.mp4"` - Analyze video
2. Review real-time rep counting and states
3. Check session summary for success rate
4. `python3 optimize_parameters.py` - Get improvement recommendations

#### **Video Export Workflow** 
1. `./run_export.sh "my_pushups.mp4"` - Export with analysis overlay
2. Check `~/Downloads/` for processed video
3. Share/review the analyzed video with skeleton overlay

#### **Parameter Tuning Workflow**
1. Collect data from multiple sessions
2. Run optimization analysis
3. Apply recommended parameter changes
4. Test with new videos to measure improvement
5. Iterate based on results

### **Current Parameter Settings**
- **Angle Thresholds**: TOP=150°, BOTTOM=100° (optimized from 90°)
- **State Machine**: min_state_frames=1, movement_threshold=3°, hysteresis=5°
- **Rep Validation**: 2-10 second duration, 60% minimum form score
- **Detection**: min_confidence=0.5, visibility_threshold=0.3

This comprehensive system provides both real-time analysis and detailed optimization capabilities for continuous improvement of the pushup detection algorithm.