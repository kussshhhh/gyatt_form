#!/bin/bash
# Convenience script to run the GYATT Form demo with virtual environment

echo "🚀 Starting GYATT Form Demo..."
echo "📦 Activating virtual environment..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: uv venv && uv pip install -r requirements.txt"
    exit 1
fi

# Check if no arguments provided, default to UI mode
if [ $# -eq 0 ]; then
    echo "🖥️  Using graphical interface to select input source..."
    echo "💡 Tip: You can also use --video file.mp4 or --export output.mp4"
    source .venv/bin/activate
    python3 -m gyatt_form.main --ui
else
    # Pass through all arguments
    source .venv/bin/activate
    python3 -m gyatt_form.main "$@"
fi