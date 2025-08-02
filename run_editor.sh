#!/bin/bash
# Convenience script to run the GYATT Form Video Editor with virtual environment

echo "🎬 Starting GYATT Form Video Editor..."
echo "📦 Activating virtual environment..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: uv venv && uv pip install -r requirements.txt"
    exit 1
fi

# Install additional dependencies for the editor
source .venv/bin/activate
pip install pillow > /dev/null 2>&1

# Run the video editor
if [ $# -eq 0 ]; then
    echo "🖥️  Opening video editor..."
    python3 video_editor.py
else
    echo "📹 Loading video: $1"
    python3 video_editor.py "$@"
fi