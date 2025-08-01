"""
GYATT Form - Exercise Form Analysis System

A computer vision-based system for analyzing and providing feedback on exercise form,
specifically designed for push-up analysis using pose estimation.
"""

__version__ = "0.1.0"
__author__ = "GYATT Form Team"

__all__ = [
    "Keypoint",
    "PoseData", 
    "PushUpState",
    "ProcessingConfig",
    "FormValidationConfig",
]

# Lazy imports to avoid circular dependencies
def __getattr__(name: str):
    if name == "Keypoint":
        from .data.models import Keypoint
        return Keypoint
    elif name == "PoseData":
        from .data.models import PoseData
        return PoseData
    elif name == "PushUpState":
        from .data.models import PushUpState
        return PushUpState
    elif name == "ProcessingConfig":
        from .config.processing import ProcessingConfig
        return ProcessingConfig
    elif name == "FormValidationConfig":
        from .config.validation import FormValidationConfig
        return FormValidationConfig
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")