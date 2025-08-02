"""
Push-up state machine for exercise phase detection.

Tracks exercise progression through different phases (up, down, transitions)
and manages state transitions based on pose analysis.
"""

from typing import List, Optional, Tuple
from collections import deque
from enum import Enum
import time

from ..data.models import PoseData, PushUpState
from ..config.validation import FormValidationConfig
from ..utils.geometry import AngleCalculator


class MovementState(Enum):
    """Enhanced movement states for pushup analysis."""
    READY = "ready"           # Starting position, arms extended
    DESCENDING = "descending" # Moving down, arms bending
    BOTTOM = "bottom"         # Bottom position, arms bent
    ASCENDING = "ascending"   # Moving up, arms extending
    TOP = "top"              # Top position, arms extended


class MovementStateMachine:
    """
    State machine for tracking push-up movement phases.
    
    Tracks progression through pushup states with smoothing
    to prevent rapid state changes and false transitions.
    """
    
    def __init__(self, config: FormValidationConfig):
        """Initialize state machine with validation configuration."""
        self.config = config
        self.current_state = MovementState.READY
        self.state_start_time = time.time()
        self.state_frame_count = 0
        
        # State history for smoothing
        self.state_history = deque(maxlen=10)
        self.angle_history = deque(maxlen=5)
        
        # Thresholds for state detection
        self.top_threshold = 150.0      # Angle for top position
        self.bottom_threshold = 100.0   # Angle for bottom position
        self.movement_threshold = 3.0   # Minimum angle change for movement detection (reduced for sensitivity)
        
        # Smoothing parameters  
        self.min_state_frames = 1       # Minimum frames to confirm state (reduced for fast movements)
        self.transition_hysteresis = 5.0   # Prevents oscillation at boundaries (reduced)
        
    def update_state(self, pose_data: PoseData) -> MovementState:
        """Update state based on current pose data."""
        if not pose_data:
            return self.current_state
        
        # Calculate elbow angle
        elbow_angle = AngleCalculator.calculate_average_elbow_angle(pose_data)
        if elbow_angle == 0.0:
            return self.current_state
        
        # Add to history
        self.angle_history.append(elbow_angle)
        
        # Determine new state based on angle
        new_state = self.determine_state_from_angle(elbow_angle)
        
        # Apply smoothing and validation
        if self.should_transition_to_state(new_state):
            if new_state != self.current_state:
                self.transition_to_state(new_state)
        
        self.state_frame_count += 1
        return self.current_state
    
    def determine_state_from_angle(self, elbow_angle: float) -> MovementState:
        """Determine movement state based on elbow angle."""
        # Add hysteresis to prevent oscillation
        if self.current_state in [MovementState.TOP, MovementState.READY]:
            top_thresh = self.top_threshold - self.transition_hysteresis
        else:
            top_thresh = self.top_threshold
            
        if self.current_state == MovementState.BOTTOM:
            bottom_thresh = self.bottom_threshold + self.transition_hysteresis
        else:
            bottom_thresh = self.bottom_threshold
        
        # Determine position-based state
        if elbow_angle >= top_thresh:
            position_state = MovementState.TOP
        elif elbow_angle <= bottom_thresh:
            position_state = MovementState.BOTTOM
        else:
            # In between - determine if moving up or down
            if len(self.angle_history) >= 2:
                angle_trend = self.angle_history[-1] - self.angle_history[-2]
                if angle_trend < -self.movement_threshold:
                    position_state = MovementState.DESCENDING
                elif angle_trend > self.movement_threshold:
                    position_state = MovementState.ASCENDING
                else:
                    # No clear trend, maintain current movement state if applicable
                    if self.current_state in [MovementState.DESCENDING, MovementState.ASCENDING]:
                        position_state = self.current_state
                    else:
                        position_state = MovementState.READY
            else:
                position_state = MovementState.READY
        
        return position_state
    
    def should_transition_to_state(self, new_state: MovementState) -> bool:
        """Check if transition to new state should occur."""
        if new_state == self.current_state:
            return False
        
        # Check if we've been in the current state long enough
        if self.state_frame_count < self.min_state_frames:
            return False
        
        # Validate transition logic
        return self.is_valid_transition(self.current_state, new_state)
    
    def is_valid_transition(self, from_state: MovementState, to_state: MovementState) -> bool:
        """Check if state transition is logically valid."""
        # Define valid transitions
        valid_transitions = {
            MovementState.READY: [MovementState.DESCENDING, MovementState.TOP],
            MovementState.TOP: [MovementState.DESCENDING, MovementState.READY],
            MovementState.DESCENDING: [MovementState.BOTTOM, MovementState.ASCENDING],
            MovementState.BOTTOM: [MovementState.ASCENDING, MovementState.DESCENDING],
            MovementState.ASCENDING: [MovementState.TOP, MovementState.DESCENDING]
        }
        
        return to_state in valid_transitions.get(from_state, [])
    
    def transition_to_state(self, new_state: MovementState) -> None:
        """Transition to new state."""
        self.current_state = new_state
        self.state_start_time = time.time()
        self.state_frame_count = 0
        self.state_history.append((new_state, time.time()))
    
    def get_current_state(self) -> MovementState:
        """Get current movement state."""
        return self.current_state
    
    def get_state_duration(self) -> float:
        """Get duration of current state in seconds."""
        return time.time() - self.state_start_time
    
    def get_state_frame_count(self) -> int:
        """Get number of frames in current state."""
        return self.state_frame_count
    
    def reset_state(self) -> None:
        """Reset state machine to initial state."""
        self.current_state = MovementState.READY
        self.state_start_time = time.time()
        self.state_frame_count = 0
        self.state_history.clear()
        self.angle_history.clear()
    
    def get_state_history(self, count: int = 10) -> List[Tuple[MovementState, float]]:
        """Get recent state history."""
        return list(self.state_history)[-count:]
    
    def get_current_angle_trend(self) -> str:
        """Get current angle trend direction."""
        if len(self.angle_history) < 2:
            return "stable"
        
        recent_change = self.angle_history[-1] - self.angle_history[-2]
        if recent_change > self.movement_threshold:
            return "increasing"
        elif recent_change < -self.movement_threshold:
            return "decreasing"
        else:
            return "stable"
    
    def is_in_movement(self) -> bool:
        """Check if currently in a movement phase."""
        return self.current_state in [MovementState.DESCENDING, MovementState.ASCENDING]
    
    def is_in_position(self) -> bool:
        """Check if currently in a held position."""
        return self.current_state in [MovementState.TOP, MovementState.BOTTOM, MovementState.READY]


# Legacy compatibility
class PushUpStateMachine(MovementStateMachine):
    """Legacy wrapper for MovementStateMachine."""
    pass