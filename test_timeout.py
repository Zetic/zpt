#!/usr/bin/env python3
"""
Test script for Discord bot timeout functionality.
Tests the ImageProcessingView timeout behavior without requiring Discord connection.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from PIL import Image

# Add current directory to path
sys.path.insert(0, '.')

# Import after path setup
from discord_bot import ImageProcessingView, OutputImage

def create_test_image(color='red', size=(100, 100)):
    """Create a test image and save it to a temporary file"""
    temp_dir = Path(tempfile.mkdtemp())
    image = Image.new('RGB', size, color=color)
    image_path = temp_dir / f"test_{color}.png"
    image.save(image_path)
    return str(image_path)

async def test_timeout_with_no_outputs():
    """Test timeout behavior when no outputs are generated"""
    print("Testing timeout with no outputs...")
    
    view = ImageProcessingView(timeout=0.1)  # Very short timeout for testing
    
    # Mock the message
    mock_message = AsyncMock()
    view.message = mock_message
    
    # Trigger timeout
    await view.on_timeout()
    
    # Verify message was edited
    assert mock_message.edit.called, "Message should be edited on timeout"
    
    # Check the call arguments
    call_args = mock_message.edit.call_args
    assert "Timed out" in call_args[1]['content'], "Content should indicate timeout"
    assert call_args[1]['view'] is None, "View should be removed"
    
    embeds = call_args[1]['embeds']
    assert len(embeds) == 1, "Should have one embed for no outputs"
    assert "No output images" in embeds[0].description, "Should indicate no outputs"
    
    print("✓ Timeout with no outputs working correctly")
    return True

async def test_timeout_with_outputs():
    """Test timeout behavior when outputs are generated"""
    print("Testing timeout with outputs...")
    
    view = ImageProcessingView(timeout=0.1)  # Very short timeout for testing
    
    # Create test images
    image_path1 = create_test_image('red')
    image_path2 = create_test_image('blue')
    
    try:
        # Add sample outputs
        output1 = OutputImage(image_path1, "Test prompt 1", "test1.png")
        output2 = OutputImage(image_path2, "Test prompt 2 with a very long description that should be truncated", "test2.png")
        
        view.add_output(output1)
        view.add_output(output2)
        
        # Mock the message
        mock_message = AsyncMock()
        view.message = mock_message
        
        # Trigger timeout
        await view.on_timeout()
        
        # Verify message was edited
        assert mock_message.edit.called, "Message should be edited on timeout"
        
        # Check the call arguments
        call_args = mock_message.edit.call_args
        assert "Timed out" in call_args[1]['content'], "Content should indicate timeout"
        assert call_args[1]['view'] is None, "View should be removed"
        
        embeds = call_args[1]['embeds']
        files = call_args[1]['attachments']
        
        # Should have embeds for each output
        assert len(embeds) == 2, f"Should have 2 embeds for outputs, got {len(embeds)}"
        assert len(files) == 2, f"Should have 2 files for outputs, got {len(files)}"
        
        # Check embed content
        for i, embed in enumerate(embeds):
            assert "Final Output" in embed.title, f"Embed {i} should indicate final output"
            assert "Timed Out" in embed.title, f"Embed {i} should indicate timeout"
            assert "Test prompt" in embed.description, f"Embed {i} should contain prompt"
        
        print("✓ Timeout with outputs working correctly")
        return True
        
    finally:
        # Clean up test files
        try:
            os.unlink(image_path1)
            os.unlink(image_path2)
        except:
            pass

def test_output_image_creation():
    """Test OutputImage class functionality"""
    print("Testing OutputImage class...")
    
    # Create test image
    image_path = create_test_image('green')
    
    try:
        output = OutputImage(image_path, "Test prompt", "test.png")
        
        assert output.image_path == image_path, "Image path should be set correctly"
        assert output.prompt == "Test prompt", "Prompt should be set correctly"
        assert output.filename == "test.png", "Filename should be set correctly"
        assert output.image is None, "Image should not be loaded initially"
        
        # Test image loading
        img = output.load_image()
        assert img is not None, "Image should load successfully"
        assert output.image is img, "Image should be cached"
        
        # Test loading again (should use cache)
        img2 = output.load_image()
        assert img2 is img, "Should return cached image"
        
        print("✓ OutputImage class working correctly")
        return True
        
    finally:
        # Clean up
        try:
            os.unlink(image_path)
        except:
            pass

def test_view_output_management():
    """Test output management in the view"""
    print("Testing view output management...")
    
    view = ImageProcessingView()
    
    # Initially no outputs
    assert len(view.outputs) == 0, "Should start with no outputs"
    
    # Add outputs
    image_path = create_test_image('yellow')
    try:
        output1 = OutputImage(image_path, "Prompt 1", "test1.png")
        output2 = OutputImage(image_path, "Prompt 2", "test2.png")
        
        view.add_output(output1)
        assert len(view.outputs) == 1, "Should have 1 output after adding"
        
        view.add_output(output2)
        assert len(view.outputs) == 2, "Should have 2 outputs after adding"
        
        assert view.outputs[0] is output1, "First output should be correct"
        assert view.outputs[1] is output2, "Second output should be correct"
        
        print("✓ View output management working correctly")
        return True
        
    finally:
        try:
            os.unlink(image_path)
        except:
            pass

async def main():
    """Run all tests"""
    print("Running Discord Bot Timeout Tests...")
    print("=" * 50)
    
    tests = [
        test_output_image_creation,
        test_view_output_management,
        test_timeout_with_no_outputs,
        test_timeout_with_outputs,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()
                
            if result:
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
        print("✓ All timeout tests passed! Timeout functionality is working.")
        return True
    else:
        print("✗ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)