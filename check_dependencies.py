#!/usr/bin/env python3
"""
Check if all required dependencies are installed.
"""

def check_dependency(package_name, import_name=None):
    """Check if a dependency is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} - OK")
        return True
    except ImportError:
        print(f"❌ {package_name} - NOT INSTALLED")
        return False

def main():
    """Check all dependencies."""
    print("=== GYATT Form Dependency Check ===\n")
    
    dependencies = [
        ("opencv-python", "cv2"),
        ("mediapipe", "mediapipe"),
        ("numpy", "numpy"),
        ("scipy", "scipy")
    ]
    
    all_ok = True
    for package, import_name in dependencies:
        if not check_dependency(package, import_name):
            all_ok = False
    
    print()
    if all_ok:
        print("🎉 All dependencies are installed!")
        print("You can now run: python3 demo.py")
    else:
        print("❗ Missing dependencies. Install them with:")
        print("pip install opencv-python mediapipe numpy scipy")
        print("\nOr install from requirements.txt:")
        print("pip install -r requirements.txt")

if __name__ == "__main__":
    main()