"""
Rep analysis and data logging for fine-tuning the counting system.

Logs state transitions, rep attempts, and performance metrics
for analysis and parameter optimization.
"""

import json
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import deque

from ..analysis.state_machine import MovementState


@dataclass
class StateTransition:
    """Single state transition record."""
    timestamp: float
    from_state: str
    to_state: str
    elbow_angle: float
    confidence: float
    keypoint_count: int
    duration_in_state: float


@dataclass
class RepAttempt:
    """Complete rep attempt analysis."""
    attempt_id: int
    start_time: float
    end_time: Optional[float]
    duration: Optional[float]
    state_sequence: List[str]
    angle_sequence: List[float]
    was_counted: bool
    failure_reason: Optional[str]
    quality_score: float
    
    
@dataclass
class SessionSummary:
    """Complete session analysis."""
    session_id: str
    start_time: float
    end_time: float
    total_transitions: int
    rep_attempts: int
    successful_reps: int
    success_rate: float
    common_failure_patterns: List[str]
    angle_statistics: Dict[str, float]
    recommendations: List[str]


class RepAnalyzer:
    """
    Analyzes rep counting performance and logs data for fine-tuning.
    
    This class tracks state transitions, identifies potential reps,
    and provides insights for parameter optimization.
    """
    
    def __init__(self, log_dir: str = "rep_analysis_logs"):
        """Initialize rep analyzer."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Session tracking
        self.session_id = f"session_{int(time.time())}"
        self.session_start = time.time()
        
        # State tracking
        self.current_state = None
        self.last_state_change = time.time()
        self.state_transitions: List[StateTransition] = []
        
        # Rep attempt tracking
        self.current_attempt: Optional[RepAttempt] = None
        self.rep_attempts: List[RepAttempt] = []
        self.attempt_counter = 0
        
        # Analysis buffers
        self.state_buffer = deque(maxlen=20)  # Recent states for pattern detection
        self.angle_buffer = deque(maxlen=50)  # Recent angles for statistics
        
        # Expected rep pattern
        self.expected_sequence = ["DESCENDING", "BOTTOM", "ASCENDING", "TOP"]
        self.valid_start_states = ["READY", "TOP"]
        
    def log_state_transition(self, new_state: MovementState, elbow_angle: float, 
                           confidence: float, keypoint_count: int, was_rep_counted: bool = False):
        """Log a state transition with context."""
        now = time.time()
        state_str = new_state.value.upper()
        
        # Only log actual state changes to reduce noise
        if self.current_state != state_str:
            if self.current_state is not None:
                # Log the transition
                transition = StateTransition(
                    timestamp=now,
                    from_state=self.current_state,
                    to_state=state_str,
                    elbow_angle=elbow_angle,
                    confidence=confidence,
                    keypoint_count=keypoint_count,
                    duration_in_state=now - self.last_state_change
                )
                self.state_transitions.append(transition)
                
                # Update rep attempt tracking
                self._update_rep_attempt(state_str, elbow_angle, was_rep_counted)
            
            self.current_state = state_str
            self.last_state_change = now
        
        # Always update buffers for analysis
        self.state_buffer.append(state_str)
        self.angle_buffer.append(elbow_angle)
    
    def _update_rep_attempt(self, new_state: str, elbow_angle: float, was_rep_counted: bool):
        """Update current rep attempt tracking."""
        # Start new attempt if we see a starting state
        if new_state in self.valid_start_states and self.current_attempt is None:
            self._start_new_attempt()
        
        # If we have an active attempt, update it
        if self.current_attempt is not None:
            self.current_attempt.state_sequence.append(new_state)
            self.current_attempt.angle_sequence.append(elbow_angle)
            
            # Check if rep was counted
            if was_rep_counted:
                self._complete_attempt(success=True)
            
            # Check if attempt should be failed (too long or bad pattern)
            elif self._should_fail_attempt():
                self._complete_attempt(success=False)
    
    def _start_new_attempt(self):
        """Start tracking a new rep attempt."""
        self.attempt_counter += 1
        self.current_attempt = RepAttempt(
            attempt_id=self.attempt_counter,
            start_time=time.time(),
            end_time=None,
            duration=None,
            state_sequence=[],
            angle_sequence=[],
            was_counted=False,
            failure_reason=None,
            quality_score=0.0
        )
    
    def _complete_attempt(self, success: bool):
        """Complete the current rep attempt."""
        if self.current_attempt is None:
            return
        
        now = time.time()
        self.current_attempt.end_time = now
        self.current_attempt.duration = now - self.current_attempt.start_time
        self.current_attempt.was_counted = success
        
        if not success:
            self.current_attempt.failure_reason = self._analyze_failure()
        
        self.current_attempt.quality_score = self._calculate_quality_score()
        
        self.rep_attempts.append(self.current_attempt)
        self.current_attempt = None
    
    def _should_fail_attempt(self) -> bool:
        """Check if current attempt should be failed."""
        if self.current_attempt is None:
            return False
        
        # Fail if attempt is too long
        duration = time.time() - self.current_attempt.start_time
        if duration > 15.0:  # 15 seconds max
            return True
        
        # Fail if we've been stuck in same state too long
        if len(self.current_attempt.state_sequence) > 50:  # Too many frames
            return True
        
        return False
    
    def _analyze_failure(self) -> str:
        """Analyze why a rep attempt failed."""
        if self.current_attempt is None:
            return "unknown"
        
        sequence = self.current_attempt.state_sequence
        
        # Common failure patterns
        if len(sequence) < 4:
            return "incomplete_sequence"
        elif "BOTTOM" not in sequence:
            return "never_reached_bottom"
        elif sequence.count("BOTTOM") > 3:
            return "stuck_at_bottom"
        elif "ASCENDING" not in sequence:
            return "never_ascended"
        elif self.current_attempt.duration and self.current_attempt.duration > 12:
            return "too_slow"
        elif len(set(sequence)) < 3:
            return "insufficient_state_variety"
        else:
            return "pattern_mismatch"
    
    def _calculate_quality_score(self) -> float:
        """Calculate quality score for the attempt."""
        if self.current_attempt is None:
            return 0.0
        
        score = 100.0
        sequence = self.current_attempt.state_sequence
        angles = self.current_attempt.angle_sequence
        
        # Penalize incomplete sequences
        if len(sequence) < 4:
            score -= 50
        
        # Reward proper state progression
        expected_present = sum(1 for state in self.expected_sequence if state in sequence)
        score += (expected_present / len(self.expected_sequence)) * 30
        
        # Penalize excessive state changes (jittery)
        if len(sequence) > 20:
            score -= min(30, (len(sequence) - 20) * 2)
        
        # Reward good angle range
        if angles:
            angle_range = max(angles) - min(angles)
            if angle_range > 60:  # Good range of motion
                score += 20
            elif angle_range < 30:  # Poor range
                score -= 20
        
        return max(0.0, min(100.0, score))
    
    def get_session_analysis(self) -> SessionSummary:
        """Generate comprehensive session analysis."""
        now = time.time()
        
        # Calculate statistics
        successful_reps = sum(1 for attempt in self.rep_attempts if attempt.was_counted)
        total_attempts = len(self.rep_attempts)
        success_rate = (successful_reps / total_attempts * 100) if total_attempts > 0 else 0
        
        # Analyze failure patterns
        failure_reasons = [attempt.failure_reason for attempt in self.rep_attempts 
                          if not attempt.was_counted and attempt.failure_reason]
        failure_counts = {}
        for reason in failure_reasons:
            failure_counts[reason] = failure_counts.get(reason, 0) + 1
        
        common_failures = sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Angle statistics
        all_angles = list(self.angle_buffer)
        angle_stats = {}
        if all_angles:
            angle_stats = {
                "min": min(all_angles),
                "max": max(all_angles),
                "mean": sum(all_angles) / len(all_angles),
                "range": max(all_angles) - min(all_angles)
            }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(common_failures, angle_stats, success_rate)
        
        return SessionSummary(
            session_id=self.session_id,
            start_time=self.session_start,
            end_time=now,
            total_transitions=len(self.state_transitions),
            rep_attempts=total_attempts,
            successful_reps=successful_reps,
            success_rate=success_rate,
            common_failure_patterns=[f"{reason}: {count}" for reason, count in common_failures[:5]],
            angle_statistics=angle_stats,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, common_failures: List[Tuple[str, int]], 
                                angle_stats: Dict[str, float], success_rate: float) -> List[str]:
        """Generate parameter tuning recommendations."""
        recommendations = []
        
        if success_rate < 50:
            recommendations.append("SUCCESS_RATE_LOW: Consider relaxing thresholds")
        
        if common_failures:
            top_failure = common_failures[0][0]
            
            if top_failure == "never_reached_bottom":
                recommendations.append("BOTTOM_THRESHOLD: Increase bottom_threshold (currently 90°)")
            elif top_failure == "stuck_at_bottom":
                recommendations.append("MOVEMENT_SENSITIVITY: Decrease movement_threshold for better transition detection")
            elif top_failure == "never_ascended":
                recommendations.append("STATE_SMOOTHING: Increase min_state_frames for more stable detection")
            elif top_failure == "too_slow":
                recommendations.append("TIMING: Increase max rep duration or improve movement detection")
        
        if angle_stats.get("range", 0) < 60:
            recommendations.append("ANGLE_RANGE: Low range of motion detected - check pose detection quality")
        
        if len(self.state_transitions) > 100 and success_rate > 80:
            recommendations.append("PERFORMANCE_GOOD: Current settings working well")
        
        return recommendations
    
    def save_session_data(self):
        """Save all session data to files."""
        timestamp = int(time.time())
        
        # Save transitions (cleaned data)
        transitions_file = self.log_dir / f"transitions_{self.session_id}_{timestamp}.json"
        transitions_data = [asdict(t) for t in self.state_transitions]
        
        with open(transitions_file, 'w') as f:
            json.dump(transitions_data, f, indent=2)
        
        # Save rep attempts
        attempts_file = self.log_dir / f"attempts_{self.session_id}_{timestamp}.json"
        attempts_data = [asdict(a) for a in self.rep_attempts]
        
        with open(attempts_file, 'w') as f:
            json.dump(attempts_data, f, indent=2)
        
        # Save session summary
        summary = self.get_session_analysis()
        summary_file = self.log_dir / f"summary_{self.session_id}_{timestamp}.json"
        
        with open(summary_file, 'w') as f:
            json.dump(asdict(summary), f, indent=2)
        
        print(f"\n📊 Session data saved:")
        print(f"  - Transitions: {transitions_file}")
        print(f"  - Rep attempts: {attempts_file}")
        print(f"  - Summary: {summary_file}")
        
        return summary
    
    def print_live_stats(self):
        """Print live statistics during analysis."""
        if len(self.rep_attempts) > 0:
            successful = sum(1 for a in self.rep_attempts if a.was_counted)
            total = len(self.rep_attempts)
            print(f"📈 Live Stats: {successful}/{total} reps counted ({successful/total*100:.1f}% success rate)")