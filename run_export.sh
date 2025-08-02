#!/bin/bash
# Convenience script to run the GYATT Form Video Exporter with virtual environment

echo "📹 Starting GYATT Form Video Exporter..."
echo "📦 Activating virtual environment..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: uv venv && uv pip install -r requirements.txt"
    exit 1
fi

source .venv/bin/activate

if [ $# -eq 0 ]; then
    echo "🎬 GYATT Form Video Exporter"
    echo "Usage: ./run_export.sh <input_video> [output_filename]"
    echo "Example: ./run_export.sh /path/to/video.mp4"
    echo "Example: ./run_export.sh /path/to/video.mp4 my_analysis.avi"
    echo ""
    echo "📁 Output will be saved to ~/Downloads/"
else
    python3 export_video.py "$@"
fi