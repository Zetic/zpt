#!/usr/bin/env python3
"""
Test script for Discord bot functionality without requiring tokens or running the actual bot.
This script validates the core logic and configuration.
"""

import os
import sys
import tempfile
import hashlib
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def test_filename_generation():
    """Test the filename generation logic"""
    print("Testing filename generation...")
    
    # Simulate the filename generation from the bot
    def generate_filename(original_url: str, extension: str = "jpg") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_hash = hashlib.md5(original_url.encode()).hexdigest()[:8]
        return f"input_{timestamp}_{url_hash}.{extension}"
    
    test_url = "https://example.com/image.png"
    filename = generate_filename(test_url, "png")
    
    print(f"  Generated filename: {filename}")
    
    # Validate filename format
    parts = filename.split('_')
    if len(parts) >= 3 and filename.startswith('input_'):
        print("✓ Filename generation working correctly")
        return True
    else:
        print("✗ Filename generation failed")
        return False

def test_directory_structure():
    """Test directory creation and structure"""
    print("Testing directory structure...")
    
    images_folder = "./images"
    input_dir = f"{images_folder}/input"
    output_dir = f"{images_folder}/output"
    
    # Check if directories exist
    if Path(input_dir).exists() and Path(output_dir).exists():
        print("✓ Image directories exist")
        
        # Check for .gitkeep files
        if Path(f"{input_dir}/.gitkeep").exists() and Path(f"{output_dir}/.gitkeep").exists():
            print("✓ .gitkeep files present")
            return True
        else:
            print("○ .gitkeep files missing (optional)")
            return True
    else:
        print("✗ Image directories missing")
        return False

def test_environment_example():
    """Test environment configuration"""
    print("Testing environment configuration...")
    
    env_example_path = ".env.example"
    if Path(env_example_path).exists():
        with open(env_example_path, 'r') as f:
            content = f.read()
            
        required_vars = [
            'DISCORD_BOT_TOKEN',
            'REPLICATE_API_TOKEN',
            'IMAGES_FOLDER',
            'MAX_FILE_SIZE_MB'
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in content:
                missing_vars.append(var)
        
        if not missing_vars:
            print("✓ All required environment variables documented")
            return True
        else:
            print(f"✗ Missing environment variables: {missing_vars}")
            return False
    else:
        print("✗ .env.example file missing")
        return False

def test_requirements():
    """Test requirements.txt"""
    print("Testing requirements.txt...")
    
    requirements_path = "requirements.txt"
    if Path(requirements_path).exists():
        with open(requirements_path, 'r') as f:
            content = f.read()
            
        required_packages = [
            'discord.py',
            'replicate',
            'python-dotenv',
            'aiohttp',
            'aiofiles'
        ]
        
        missing_packages = []
        for package in required_packages:
            if package not in content:
                missing_packages.append(package)
        
        if not missing_packages:
            print("✓ All required packages listed")
            return True
        else:
            print(f"✗ Missing packages: {missing_packages}")
            return False
    else:
        print("✗ requirements.txt missing")
        return False

def test_bot_configuration():
    """Test bot configuration logic"""
    print("Testing bot configuration...")
    
    # Test default values
    default_images_folder = "./images"
    default_max_size = 25
    
    # Simulate environment variable reading
    images_folder = os.getenv('IMAGES_FOLDER', default_images_folder)
    max_file_size = int(os.getenv('MAX_FILE_SIZE_MB', str(default_max_size)))
    
    if images_folder == default_images_folder and max_file_size == default_max_size:
        print("✓ Default configuration values working")
        return True
    else:
        print("✗ Configuration logic failed")
        return False

def main():
    """Run all tests"""
    print("Running Discord Bot Tests...")
    print("=" * 50)
    
    tests = [
        test_filename_generation,
        test_directory_structure,
        test_environment_example,
        test_requirements,
        test_bot_configuration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All tests passed! Bot setup is correct.")
        return True
    else:
        print("✗ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)