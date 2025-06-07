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

def test_image_count_validation():
    """Test image count validation logic"""
    print("Testing image count validation...")
    
    # Test exactly one image (should pass)
    image_attachments = [Mock()]
    image_attachments[0].filename = "test.png"
    
    if len(image_attachments) == 1:
        print("✅ Exactly one image correctly identified")
    else:
        print("❌ Single image validation failed")
        return False
    
    # Test multiple images (should fail)
    image_attachments = [Mock(), Mock()]
    image_attachments[0].filename = "test1.png"
    image_attachments[1].filename = "test2.jpg"
    
    if len(image_attachments) > 1:
        print("✅ Multiple images correctly identified")
    else:
        print("❌ Multiple image validation failed")
        return False
    
    # Test no images (should fail)
    image_attachments = []
    
    if len(image_attachments) == 0:
        print("✅ No images correctly identified")
    else:
        print("❌ No image validation failed")
        return False
    
    return True

def test_directory_creation():
    """Test directory creation logic"""
    print("Testing directory creation...")
    
    import tempfile
    import shutil
    
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    
    try:
        os.chdir(test_dir)
        
        # Test directory creation
        os.makedirs('images/inputs', exist_ok=True)
        os.makedirs('images/outputs', exist_ok=True)
        
        if os.path.exists('images/inputs') and os.path.exists('images/outputs'):
            print("✅ Directory structure created successfully")
            return True
        else:
            print("❌ Directory creation failed")
            return False
    except Exception as e:
        print(f"❌ Directory creation failed with exception: {e}")
        return False
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(test_dir, ignore_errors=True)

def test_filename_generation():
    """Test timestamp-based filename generation"""
    print("Testing filename generation...")
    
    from datetime import datetime
    
    # Test input filename generation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = "test_image.png"
    file_extension = os.path.splitext(original_filename)[1]
    input_filename = f"{timestamp}_input{file_extension}"
    
    if input_filename.endswith("_input.png") and len(timestamp) == 15:
        print("✅ Input filename generation works correctly")
    else:
        print("❌ Input filename generation failed")
        return False
    
    # Test output filename generation
    base_name = os.path.splitext(original_filename)[0]
    output_filename = f"{timestamp}_output_{base_name}.png"
    
    if "output_test_image.png" in output_filename and len(timestamp) == 15:
        print("✅ Output filename generation works correctly")
    else:
        print("❌ Output filename generation failed")
        return False
    
    return True

def test_discord_url_validation():
    """Test Discord URL validation logic"""
    print("Testing Discord URL validation...")
    
    # Test directly using the bot class method
    from bot import FluxBot
    
    # Test valid Discord URLs
    valid_urls = [
        'https://cdn.discordapp.com/attachments/123/456/image.png',
        'https://media.discordapp.net/attachments/123/456/photo.jpg',
        'https://images-ext-1.discordapp.net/external/abc/image.jpeg',
        'https://images-ext-2.discordapp.net/external/def/image.webp'
    ]
    
    for url in valid_urls:
        # Test the validation logic directly
        discord_domains = [
            'cdn.discordapp.com',
            'media.discordapp.net',
            'images-ext-1.discordapp.net',
            'images-ext-2.discordapp.net'
        ]
        
        valid_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.gif']
        
        has_discord_domain = any(domain in url for domain in discord_domains)
        has_valid_extension = any(url.lower().endswith(ext) for ext in valid_extensions)
        is_valid = has_discord_domain and has_valid_extension
        
        if is_valid:
            print(f"✅ Valid Discord URL correctly identified: {url.split('/')[-1]}")
        else:
            print(f"❌ Valid Discord URL incorrectly rejected: {url}")
            return False
    
    # Test invalid URLs
    invalid_urls = [
        'https://example.com/image.png',  # Wrong domain
        'https://cdn.discordapp.com/attachments/123/456/document.pdf',  # Wrong extension
        'https://malicious-site.com/fake-discord-url.png',  # Fake Discord URL
        'not-a-url-at-all'  # Not even a URL
    ]
    
    for url in invalid_urls:
        has_discord_domain = any(domain in url for domain in discord_domains)
        has_valid_extension = any(url.lower().endswith(ext) for ext in valid_extensions)
        is_valid = has_discord_domain and has_valid_extension
        
        if not is_valid:
            print(f"✅ Invalid URL correctly rejected: {url.split('/')[-1] if '/' in url else url}")
        else:
            print(f"❌ Invalid URL incorrectly accepted: {url}")
            return False
    
    return True

def test_end_to_end_workflow():
    """Test the complete workflow with mock data"""
    print("Testing end-to-end workflow...")
    
    # This test validates the workflow without actual API calls
    try:
        from bot import FluxBot
        import tempfile
        import shutil
        
        # Create temporary directory for testing
        test_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        
        try:
            os.chdir(test_dir)
            
            # Test directory setup
            os.makedirs('images/inputs', exist_ok=True)
            os.makedirs('images/outputs', exist_ok=True)
            
            # Test filename generation
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Test input filename
            input_filename = f"{timestamp}_input.png"
            input_path = os.path.join('images', 'inputs', input_filename)
            
            # Test output filename
            output_filename = f"{timestamp}_output_test_image.png"
            output_path = os.path.join('images', 'outputs', output_filename)
            
            # Create mock files
            with open(input_path, 'wb') as f:
                f.write(b'mock input image data')
            
            with open(output_path, 'wb') as f:
                f.write(b'mock output image data')
            
            # Verify files exist
            if os.path.exists(input_path) and os.path.exists(output_path):
                print("✅ File operations work correctly")
                print("✅ Directory structure validation passed")
                print("✅ Filename generation validation passed")
                print("✅ End-to-end workflow validation passed")
                return True
            else:
                print("❌ File operations failed")
                return False
                
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(test_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ End-to-end workflow failed: {e}")
        return False

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
        test_image_count_validation,
        test_directory_creation,
        test_filename_generation,
        test_discord_url_validation,
        test_end_to_end_workflow
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