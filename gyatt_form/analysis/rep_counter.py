"""
Repetition counting and performance metrics.

Counts completed push-up repetitions and tracks performance metrics
including timing, consistency, and quality scores.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import time
from collections import deque

from ..data.models import PoseData, PushUpState
from ..config.validation import FormValidationConfig
from .state_machine import MovementState


@dataclass
class RepetitionData:
    """Data structure for a single repetition."""
    rep_number: int
    start_time: float
    end_time: float
    form_scores: List[float]
    state_sequence: List[MovementState]
    average_form_score: float
    duration: float
    elbow_angles: List[float]
    
    @property
    def is_valid(self) -> bool:
        """Check if repetition meets minimum quality standards."""
        # Check if we have a complete movement cycle
        required_states = {MovementState.TOP, MovementState.DESCENDING, 
                          MovementState.BOTTOM, MovementState.ASCENDING}
        has_complete_cycle = required_states.issubset(set(self.state_sequence))
        
        # Check duration is reasonable (2-10 seconds per rep)
        reasonable_duration = 2.0 <= self.duration <= 10.0
        
        # Check form score if available
        good_form = len(self.form_scores) == 0 or self.average_form_score >= 60.0
        
        return has_complete_cycle and reasonable_duration and good_form


class RepCounter:
    """
    Counts and tracks push-up repetitions based on movement states.
    
    Tracks complete movement cycles and validates repetitions
    based on state sequence and timing.
    """
    
    def __init__(self, config: FormValidationConfig):
        """Initialize repetition counter with validation configuration."""
        self.config = config
        
        # State sequence tracking
        self.required_sequence = [
            MovementState.TOP,
            MovementState.DESCENDING, 
            MovementState.BOTTOM,
            MovementState.ASCENDING,
            MovementState.TOP
        ]
        
        # Initialize tracking variables first
        self.sequence_index = 0  # Where we are in the required sequence
        self.current_rep_start = None
        self.current_rep_states = []
        self.current_rep_angles = []
        self.current_rep_scores = []
        
        # Now initialize the counter
        self.reset_counter()
        
    def update(self, current_state: MovementState, elbow_angle: float = 0.0, 
              form_score: float = 100.0, timestamp: float = None) -> bool:
        """Update counter with current state. Returns True if new rep completed."""
        if timestamp is None:
            timestamp = time.time()
        
        # Track current repetition data
        self.current_rep_states.append(current_state)
        self.current_rep_angles.append(elbow_angle)
        self.current_rep_scores.append(form_score)
        
        # Check if we're progressing through the sequence
        expected_state = self.required_sequence[self.sequence_index]
        
        if current_state == expected_state:
            # We're on track - advance to next state
            self.sequence_index += 1
            
            # If this is the start of a rep (first TOP position)
            if self.sequence_index == 1 and self.current_rep_start is None:
                self.current_rep_start = timestamp
            
            # If we completed the full sequence
            if self.sequence_index >= len(self.required_sequence):
                return self._complete_repetition(timestamp)
                
        elif self.sequence_index > 0:
            # We were in a sequence but deviated - check if we should reset or continue
            if current_state == self.required_sequence[0]:
                # Started a new rep from the beginning
                self._reset_current_rep()
                self.sequence_index = 1
                self.current_rep_start = timestamp
            # Otherwise, stay in current position and wait for correct state
        
        return False
    
    def _complete_repetition(self, timestamp: float) -> bool:
        """Complete the current repetition and add to history."""
        if self.current_rep_start is None:
            self._reset_current_rep()
            return False
        
        duration = timestamp - self.current_rep_start
        average_score = sum(self.current_rep_scores) / len(self.current_rep_scores) if self.current_rep_scores else 100.0
        
        rep_data = RepetitionData(
            rep_number=len(self.repetitions) + 1,
            start_time=self.current_rep_start,
            end_time=timestamp,
            form_scores=self.current_rep_scores.copy(),
            state_sequence=self.current_rep_states.copy(),
            average_form_score=average_score,
            duration=duration,
            elbow_angles=self.current_rep_angles.copy()
        )
        
        # Only count if it's a valid repetition
        if rep_data.is_valid:
            self.repetitions.append(rep_data)
            self.total_reps += 1
            if rep_data.is_valid:
                self.valid_reps += 1
        
        # Reset for next rep
        self._reset_current_rep()
        
        return rep_data.is_valid
    
    def _reset_current_rep(self):
        """Reset current repetition tracking."""
        self.sequence_index = 0
        self.current_rep_start = None
        self.current_rep_states.clear()
        self.current_rep_angles.clear()
        self.current_rep_scores.clear()
    
    def get_rep_count(self) -> int:
        """Get total number of completed repetitions."""
        return self.total_reps
    
    def get_valid_rep_count(self) -> int:
        """Get number of valid repetitions (meeting quality standards)."""
        return self.valid_reps
    
    def get_average_form_score(self) -> float:
        """Get average form score across all repetitions."""
        if not self.repetitions:
            return 0.0
        return sum(rep.average_form_score for rep in self.repetitions) / len(self.repetitions)
    
    def get_rep_history(self) -> List[RepetitionData]:
        """Get complete repetition history."""
        return self.repetitions.copy()
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get comprehensive performance statistics."""
        if not self.repetitions:
            return {
                'total_reps': 0,
                'valid_reps': 0,
                'average_duration': 0.0,
                'average_form_score': 0.0,
                'consistency_score': 0.0
            }
        
        durations = [rep.duration for rep in self.repetitions]
        form_scores = [rep.average_form_score for rep in self.repetitions]
        
        # Calculate consistency (lower standard deviation = more consistent)
        if len(durations) > 1:
            import statistics
            duration_std = statistics.stdev(durations)
            form_std = statistics.stdev(form_scores)
            # Normalize consistency score (100 = perfectly consistent)
            consistency_score = max(0, 100 - (duration_std * 10 + form_std / 10))
        else:
            consistency_score = 100.0
        
        return {
            'total_reps': self.total_reps,
            'valid_reps': self.valid_reps,
            'average_duration': sum(durations) / len(durations),
            'average_form_score': sum(form_scores) / len(form_scores),
            'consistency_score': consistency_score,
            'fastest_rep': min(durations),
            'slowest_rep': max(durations)
        }
    
    def reset_counter(self) -> None:
        """Reset counter and clear all data."""
        self.repetitions: List[RepetitionData] = []
        self.total_reps = 0
        self.valid_reps = 0
        self._reset_current_rep()
    
    def get_current_progress(self) -> Dict[str, any]:
        """Get current repetition progress information."""
        if self.sequence_index == 0:
            progress_stage = "Waiting to start"
            progress_percent = 0
        else:
            progress_stage = f"Stage {self.sequence_index}/{len(self.required_sequence)-1}"
            progress_percent = (self.sequence_index / (len(self.required_sequence)-1)) * 100
        
        return {
            'stage': progress_stage,
            'progress_percent': progress_percent,
            'current_state': self.required_sequence[self.sequence_index] if self.sequence_index < len(self.required_sequence) else None,
            'next_state': self.required_sequence[self.sequence_index] if self.sequence_index < len(self.required_sequence) else None,
            'rep_in_progress': self.current_rep_start is not None
        }


# Legacy compatibility
class RepetitionCounter(RepCounter):
    """Legacy wrapper for RepCounter."""
    pass