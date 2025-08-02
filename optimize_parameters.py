#!/usr/bin/env python3
"""
Parameter optimization script for the rep counting system.

Analyzes logged data and suggests optimal parameter values for
better rep detection accuracy.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import statistics

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gyatt_form.analysis.state_machine import MovementState
from gyatt_form.config.defaults import get_default_processing_config, get_default_validation_config


class ParameterOptimizer:
    """Analyzes session data and optimizes parameters for better rep detection."""
    
    def __init__(self, log_dir: str = "rep_analysis_logs"):
        self.log_dir = Path(log_dir)
        self.current_config = get_default_processing_config()
        self.current_validation = get_default_validation_config()
        
    def load_latest_session_data(self) -> Tuple[List[Dict], List[Dict], Dict]:
        """Load the most recent session data."""
        if not self.log_dir.exists():
            print(f"❌ Log directory {self.log_dir} not found. Run the app first to generate data.")
            return [], [], {}
        
        # Find latest files
        transition_files = list(self.log_dir.glob("transitions_*.json"))
        attempt_files = list(self.log_dir.glob("attempts_*.json"))
        summary_files = list(self.log_dir.glob("summary_*.json"))
        
        if not transition_files:
            print("❌ No session data found. Run the app to generate analysis data.")
            return [], [], {}
        
        # Load latest files
        latest_transitions = sorted(transition_files)[-1]
        latest_attempts = sorted(attempt_files)[-1]
        latest_summary = sorted(summary_files)[-1]
        
        print(f"📂 Loading data from: {latest_transitions.name}")
        
        with open(latest_transitions) as f:
            transitions = json.load(f)
        
        with open(latest_attempts) as f:
            attempts = json.load(f)
            
        with open(latest_summary) as f:
            summary = json.load(f)
        
        return transitions, attempts, summary
    
    def analyze_angle_thresholds(self, transitions: List[Dict], attempts: List[Dict]) -> Dict[str, float]:
        """Analyze optimal angle thresholds based on actual data."""
        print("\n🔍 Analyzing angle thresholds...")
        
        # Collect angles for each state
        state_angles = {
            "TOP": [],
            "BOTTOM": [],
            "READY": [],
            "DESCENDING": [],
            "ASCENDING": []
        }
        
        for transition in transitions:
            state = transition["to_state"]
            angle = transition["elbow_angle"]
            if state in state_angles and 0 < angle < 180:  # Valid angle range
                state_angles[state].append(angle)
        
        # Calculate statistics
        recommendations = {}
        
        # TOP/READY threshold analysis
        top_angles = state_angles["TOP"] + state_angles["READY"]
        if top_angles:
            top_median = statistics.median(top_angles)
            top_25th = statistics.quantiles(top_angles, n=4)[0]  # 25th percentile
            current_top = 150.0
            
            # Recommend threshold that captures 75% of top positions
            recommended_top = max(140.0, min(165.0, top_25th))
            recommendations["top_threshold"] = {
                "current": current_top,
                "recommended": recommended_top,
                "reason": f"Captures 75% of TOP states (median: {top_median:.1f}°)"
            }
            
            print(f"  📐 TOP angles - Median: {top_median:.1f}°, 25th percentile: {top_25th:.1f}°")
            print(f"     Current threshold: {current_top}°, Recommended: {recommended_top:.1f}°")
        
        # BOTTOM threshold analysis
        bottom_angles = state_angles["BOTTOM"]
        if bottom_angles:
            bottom_median = statistics.median(bottom_angles)
            bottom_75th = statistics.quantiles(bottom_angles, n=4)[2]  # 75th percentile
            current_bottom = 90.0
            
            # Recommend threshold that captures 75% of bottom positions
            recommended_bottom = min(100.0, max(75.0, bottom_75th))
            recommendations["bottom_threshold"] = {
                "current": current_bottom,
                "recommended": recommended_bottom,
                "reason": f"Captures 75% of BOTTOM states (median: {bottom_median:.1f}°)"
            }
            
            print(f"  📐 BOTTOM angles - Median: {bottom_median:.1f}°, 75th percentile: {bottom_75th:.1f}°")
            print(f"     Current threshold: {current_bottom}°, Recommended: {recommended_bottom:.1f}°")
        
        return recommendations
    
    def analyze_timing_parameters(self, attempts: List[Dict]) -> Dict[str, Any]:
        """Analyze timing-related parameters."""
        print("\n⏱️  Analyzing timing parameters...")
        
        recommendations = {}
        
        # Analyze successful rep durations
        successful_durations = [
            attempt["duration"] for attempt in attempts 
            if attempt["was_counted"] and attempt["duration"]
        ]
        
        if successful_durations:
            min_duration = min(successful_durations)
            max_duration = max(successful_durations)
            median_duration = statistics.median(successful_durations)
            
            # Current range: 2-10 seconds
            current_min, current_max = 2.0, 10.0
            
            # Recommend based on actual data with some margin
            recommended_min = max(1.0, min_duration * 0.8)
            recommended_max = min(15.0, max_duration * 1.2)
            
            recommendations["rep_duration"] = {
                "current_range": [current_min, current_max],
                "recommended_range": [recommended_min, recommended_max],
                "actual_range": [min_duration, max_duration],
                "median": median_duration,
                "reason": f"Based on {len(successful_durations)} successful reps"
            }
            
            print(f"  ⏱️  Successful rep durations: {min_duration:.1f}s - {max_duration:.1f}s (median: {median_duration:.1f}s)")
            print(f"     Current range: {current_min}-{current_max}s")
            print(f"     Recommended: {recommended_min:.1f}-{recommended_max:.1f}s")
        
        return recommendations
    
    def analyze_state_transitions(self, transitions: List[Dict]) -> Dict[str, Any]:
        """Analyze state transition patterns."""
        print("\n🔄 Analyzing state transition patterns...")
        
        # Count transition frequencies
        transition_counts = {}
        total_transitions = len(transitions)
        
        for transition in transitions:
            key = f"{transition['from_state']} → {transition['to_state']}"
            transition_counts[key] = transition_counts.get(key, 0) + 1
        
        # Find most common transitions
        common_transitions = sorted(transition_counts.items(), key=lambda x: x[1], reverse=True)
        
        print(f"  🔄 Most common transitions:")
        for transition, count in common_transitions[:8]:
            percentage = (count / total_transitions) * 100
            print(f"     {transition}: {count} ({percentage:.1f}%)")
        
        # Analyze rapid state changes (potential jitter)
        rapid_changes = 0
        for i in range(1, len(transitions)):
            if transitions[i]["duration_in_state"] < 0.1:  # Less than 100ms
                rapid_changes += 1
        
        jitter_percentage = (rapid_changes / total_transitions) * 100 if total_transitions > 0 else 0
        
        recommendations = {
            "state_smoothing": {
                "rapid_changes": rapid_changes,
                "jitter_percentage": jitter_percentage,
                "recommendation": "increase_min_state_frames" if jitter_percentage > 20 else "current_ok"
            }
        }
        
        print(f"  ⚡ Rapid state changes: {rapid_changes} ({jitter_percentage:.1f}%)")
        if jitter_percentage > 20:
            print(f"     🔧 Recommendation: Increase min_state_frames to reduce jitter")
        
        return recommendations
    
    def generate_optimized_config(self, all_recommendations: Dict) -> Dict[str, Any]:
        """Generate optimized configuration based on analysis."""
        config = {
            "state_machine": {
                "top_threshold": 150.0,
                "bottom_threshold": 90.0,
                "movement_threshold": 5.0,
                "transition_hysteresis": 10.0,
                "min_state_frames": 3
            },
            "rep_validation": {
                "min_rep_duration": 2.0,
                "max_rep_duration": 10.0,
                "min_form_score": 60.0
            },
            "pose_detection": {
                "min_detection_confidence": 0.5,
                "min_tracking_confidence": 0.5,
                "visibility_threshold": 0.3
            }
        }
        
        # Apply angle threshold recommendations
        if "top_threshold" in all_recommendations:
            config["state_machine"]["top_threshold"] = all_recommendations["top_threshold"]["recommended"]
        
        if "bottom_threshold" in all_recommendations:
            config["state_machine"]["bottom_threshold"] = all_recommendations["bottom_threshold"]["recommended"]
        
        # Apply timing recommendations
        if "rep_duration" in all_recommendations:
            duration_rec = all_recommendations["rep_duration"]["recommended_range"]
            config["rep_validation"]["min_rep_duration"] = duration_rec[0]
            config["rep_validation"]["max_rep_duration"] = duration_rec[1]
        
        # Apply smoothing recommendations
        if "state_smoothing" in all_recommendations:
            smoothing = all_recommendations["state_smoothing"]
            if smoothing["recommendation"] == "increase_min_state_frames":
                config["state_machine"]["min_state_frames"] = 5
        
        return config
    
    def run_optimization(self):
        """Run complete parameter optimization analysis."""
        print("🚀 Starting parameter optimization analysis...")
        
        # Load data
        transitions, attempts, summary = self.load_latest_session_data()
        if not transitions:
            return
        
        print(f"\n📊 Session Summary:")
        print(f"  - Total transitions: {len(transitions)}")
        print(f"  - Rep attempts: {len(attempts)}")
        print(f"  - Success rate: {summary.get('success_rate', 0):.1f}%")
        
        # Run analyses
        all_recommendations = {}
        
        # Analyze different aspects
        angle_recs = self.analyze_angle_thresholds(transitions, attempts)
        all_recommendations.update(angle_recs)
        
        timing_recs = self.analyze_timing_parameters(attempts)
        all_recommendations.update(timing_recs)
        
        transition_recs = self.analyze_state_transitions(transitions)
        all_recommendations.update(transition_recs)
        
        # Generate optimized config
        optimized_config = self.generate_optimized_config(all_recommendations)
        
        # Save optimized config
        config_file = self.log_dir / "optimized_config.json"
        with open(config_file, 'w') as f:
            json.dump(optimized_config, f, indent=2)
        
        print(f"\n✅ Optimization complete!")
        print(f"📁 Optimized config saved to: {config_file}")
        
        # Print key recommendations
        print(f"\n🔧 Key Recommendations:")
        for param, rec in all_recommendations.items():
            if isinstance(rec, dict) and "reason" in rec:
                print(f"  - {param}: {rec['reason']}")
        
        print(f"\n📝 To apply these settings, update your configuration files or")
        print(f"   use the optimized_config.json file as reference.")
        
        return optimized_config


def main():
    """Main optimization function."""
    optimizer = ParameterOptimizer()
    
    try:
        config = optimizer.run_optimization()
        
        if config:
            print(f"\n🎯 Optimization successful! Check the generated config file.")
        else:
            print(f"\n❌ No data available for optimization. Run the app first to collect data.")
            
    except Exception as e:
        print(f"❌ Optimization failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())