#!/usr/bin/env python3
"""
Setup script for Medieval RPG Learning Game with Teacher Portal
This script helps configure the environment and check dependencies.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ["uploads", "data", "static", "templates"]
    print("\n📁 Creating directories...")
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ {directory}/ directory ready")

def check_data_files():
    """Check if required data files exist"""
    print("\n📋 Checking data files...")
    
    required_files = {
        "data/questions.json": "questions data",
        "data/levels.json": "levels data",
        "data/enemies.json": "enemies data",
        "data/leaderboard.json": "leaderboard data"
    }
    
    all_exist = True
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            print(f"✅ {description} found")
        else:
            print(f"⚠️  {description} missing at {file_path}")
            all_exist = False
    
    return all_exist

def setup_config():
    """Help user setup configuration"""
    print("\n⚙️  Configuration Setup")
    
    if os.path.exists("config.py"):
        print("✅ config.py already exists")
        
        # Read existing config to check if it needs updates
        with open("config.py", "r") as f:
            content = f.read()
            
        if "your-openai-api-key-here" in content:
            print("⚠️  Please update your OpenAI API key in config.py")
        if "teacher1" in content and "password123" in content:
            print("⚠️  Please update default teacher credentials in config.py")
    else:
        print("❌ config.py not found")
        print("Please create config.py with your settings")

def test_imports():
    """Test if all required modules can be imported"""
    print("\n🧪 Testing imports...")
    
    modules = [
        ("flask", "Flask"),
        ("whoosh", "Whoosh search"),
        ("requests", "HTTP requests"),
        ("openai", "OpenAI API"),
        ("docx", "Word document processing"),
        ("PyPDF2", "PDF processing"),
        ("bs4", "HTML parsing"),
        ("markdown", "Markdown processing")
    ]
    
    all_imported = True
    for module, description in modules:
        try:
            __import__(module)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} - Module '{module}' not found")
            all_imported = False
    
    return all_imported

def check_permissions():
    """Check file permissions"""
    print("\n🔐 Checking permissions...")
    
    # Check if we can write to data directory
    test_file = "data/test_write.tmp"
    try:
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Data directory is writable")
    except (PermissionError, FileNotFoundError):
        print("❌ Cannot write to data directory")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🏰 Medieval RPG Learning Game - Setup Assistant")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    install_success = install_dependencies()
    
    # Test imports
    if install_success:
        import_success = test_imports()
    else:
        import_success = False
    
    # Check data files
    data_files_exist = check_data_files()
    
    # Check permissions
    permissions_ok = check_permissions()
    
    # Setup configuration
    setup_config()
    
    # Final summary
    print("\n" + "=" * 50)
    print("📋 Setup Summary:")
    print(f"Dependencies: {'✅' if install_success else '❌'}")
    print(f"Imports: {'✅' if import_success else '❌'}")
    print(f"Data files: {'✅' if data_files_exist else '⚠️'}")
    print(f"Permissions: {'✅' if permissions_ok else '❌'}")
    
    if all([install_success, import_success, data_files_exist, permissions_ok]):
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Update config.py with your settings")
        print("2. Run: python app.py")
        print("3. Visit: http://localhost:5000")
        print("4. Teacher portal: http://localhost:5000/teacher/login")
    else:
        print("\n⚠️  Setup completed with warnings")
        print("Please address the issues above before running the application")

if __name__ == "__main__":
    main()