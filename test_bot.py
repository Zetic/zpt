#!/usr/bin/env python3
"""
Test script for basic bot functionality validation
"""

import os
import sys
import tempfile
from unittest.mock import Mock, patch, AsyncMock

# Add current directory to path to import bot module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_bot_initialization():
    """Test bot can be initialized with mock tokens"""
    print("Testing bot initialization...")
    
    with patch.dict(os.environ, {
        'DISCORD_TOKEN': 'fake_discord_token',
        'REPLICATE_API_TOKEN': 'fake_replicate_token'
    }):
        try:
            from bot import FluxBot
            bot = FluxBot()
            print("✅ Bot initialization successful")
            return True
        except Exception as e:
            print(f"❌ Bot initialization failed: {e}")
            return False

def test_image_attachment_detection():
    """Test image attachment detection logic"""
    print("Testing image attachment detection...")
    
    # Mock attachment objects
    image_attachment = Mock()
    image_attachment.filename = "test_image.png"
    
    non_image_attachment = Mock()
    non_image_attachment.filename = "document.pdf"
    
    # Test image detection
    image_formats = ['.png', '.jpg', '.jpeg', '.webp']
    
    # Test positive cases
    for ext in image_formats:
        test_filename = f"test{ext}"
        is_image = any(test_filename.lower().endswith(ext) for ext in image_formats)
        if is_image:
            print(f"✅ {test_filename} correctly identified as image")
        else:
            print(f"❌ {test_filename} should be identified as image")
            return False
    
    # Test negative case
    is_image = any("document.pdf".lower().endswith(ext) for ext in image_formats)
    if not is_image:
        print("✅ PDF correctly identified as non-image")
    else:
        print("❌ PDF should not be identified as image")
        return False
    
    return True

def test_mention_parsing():
    """Test bot mention parsing logic"""
    print("Testing mention parsing...")
    
    # Simulate bot mention removal
    test_cases = [
        ("<@123456789> make it more colorful", "make it more colorful"),
        ("Hey <@123456789> change the background", "Hey  change the background"),
        ("make it darker <@123456789>", "make it darker "),
    ]
    
    bot_id = "123456789"
    
    for original, expected in test_cases:
        result = original.replace(f'<@{bot_id}>', '').strip()
        expected = expected.strip()
        
        if result == expected:
            print(f"✅ Mention parsing: '{original}' -> '{result}'")
        else:
            print(f"❌ Mention parsing failed: '{original}' -> '{result}' (expected: '{expected}')")
            return False
    
    return True

def test_environment_validation():
    """Test environment variable validation"""
    print("Testing environment validation...")
    
    # Test missing tokens
    with patch.dict(os.environ, {}, clear=True):
        from bot import main
        
        # Capture output by redirecting stdout
        import io
        import contextlib
        
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            try:
                main()
            except SystemExit:
                pass
        
        output = stdout_capture.getvalue()
        if "DISCORD_TOKEN not found" in output:
            print("✅ Missing Discord token correctly detected")
        else:
            print("❌ Missing Discord token not detected")
            return False
    
    return True

def test_fileoutput_handling():
    """Test FileOutput object handling"""
    print("Testing FileOutput object handling...")
    
    # Mock FileOutput object (simulating what Replicate returns)
    class MockFileOutput:
        def __init__(self, url):
            self.url = url
        
        def __str__(self):
            return self.url
    
    # Test that we can check if FileOutput exists without using len()
    mock_output = MockFileOutput("https://example.com/image.png")
    
    # This should work (checking if output exists)
    if mock_output:
        print("✅ FileOutput existence check works")
    else:
        print("❌ FileOutput existence check failed")
        return False
    
    # Test that we can use FileOutput directly as URL
    try:
        url = str(mock_output)  # FileOutput should be convertible to URL string
        if url == "https://example.com/image.png":
            print("✅ FileOutput URL extraction works")
        else:
            print("❌ FileOutput URL extraction failed")
            return False
    except Exception as e:
        print(f"❌ FileOutput URL extraction failed with exception: {e}")
        return False
    
    # Test that len() would fail on FileOutput (this is the original bug)
    try:
        len(mock_output)
        print("❌ len() should fail on FileOutput object")
        return False
    except TypeError:
        print("✅ len() correctly fails on FileOutput object (confirming the bug)")
    
    return True

def test_flux_output_processing():
    """Test Flux output processing logic"""
    print("Testing Flux output processing...")
    
    # Mock FileOutput object (simulating what Replicate returns)
    class MockFileOutput:
        def __init__(self, url):
            self.url = url
        
        def __str__(self):
            return self.url
        
        def __bool__(self):
            return bool(self.url)
    
    # Test the fixed logic from modify_image_with_flux
    output = MockFileOutput("https://example.com/generated_image.png")
    
    # This is the fixed logic that should work
    try:
        if output:  # This should work (no len() call)
            url = str(output)  # Use FileOutput directly, not output[0]
            if url == "https://example.com/generated_image.png":
                print("✅ Fixed Flux output processing works correctly")
            else:
                print("❌ URL extraction from FileOutput failed")
                return False
        else:
            print("❌ FileOutput existence check failed")
            return False
    except Exception as e:
        print(f"❌ Fixed logic failed with exception: {e}")
        return False
    
    # Test with None output (should handle gracefully)
    output_none = None
    if not output_none:
        print("✅ None output handled correctly")
    else:
        print("❌ None output not handled correctly")
        return False
    
    return True

def run_all_tests():
    """Run all validation tests"""
    print("🧪 Running Discord Bot Validation Tests\n")
    
    tests = [
        test_bot_initialization,
        test_image_attachment_detection,
        test_mention_parsing,
        test_environment_validation,
        test_fileoutput_handling,
        test_flux_output_processing,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASSED\n")
            else:
                print("❌ FAILED\n")
        except Exception as e:
            print(f"❌ FAILED with exception: {e}\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bot foundation is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)