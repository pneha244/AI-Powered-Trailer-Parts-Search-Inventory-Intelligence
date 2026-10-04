#!/usr/bin/env python3
"""
Setup script for Trailer Parts Intelligent Search System
This script automates the installation and setup process.
"""

import subprocess
import sys
import os
import platform

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_requirements():
    """Install required packages."""
    print("📦 Installing required packages...")
    try:
        # Try parent directory first, then current directory
        req_file = "../requirements.txt"
        if not os.path.exists(req_file):
            req_file = "requirements.txt"
        
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def check_streamlit():
    """Check if Streamlit is installed correctly."""
    try:
        result = subprocess.run([sys.executable, "-m", "streamlit", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Streamlit is installed correctly!")
            return True
        else:
            print("❌ Streamlit installation check failed.")
            return False
    except Exception as e:
        print(f"❌ Error checking Streamlit: {e}")
        return False

def create_directories():
    """Create necessary directories if they don't exist."""
    directories = ["parts_db", "pages"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Created directory: {directory}")

def main():
    """Main setup function."""
    print("🚛 Trailer Parts Intelligent Search System Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Check Streamlit
    if not check_streamlit():
        print("⚠️  Streamlit check failed, but continuing...")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run the application: streamlit run Home.py")
    print("2. Open your browser to: http://localhost:8501")
    print("3. Start searching for trailer parts!")
    
    # Ask if user wants to run the app now
    try:
        response = input("\n🤔 Would you like to start the application now? (y/n): ").lower()
        if response in ['y', 'yes']:
            print("🚀 Starting the application...")
            subprocess.run([sys.executable, "-m", "streamlit", "run", "Home.py"])
    except KeyboardInterrupt:
        print("\n👋 Setup completed. Run 'streamlit run Home.py' when ready!")

if __name__ == "__main__":
    main() 