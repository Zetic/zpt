#!/usr/bin/env python3
"""
Demo script showing the timeout functionality in action.
This demonstrates the key features implemented for the timeout handling.
"""

import asyncio
import tempfile
from PIL import Image
from discord_bot import ImageProcessingView, OutputImage

async def demo_timeout_behavior():
    """Demonstrate the timeout behavior with sample outputs"""
    print("🎯 Discord Bot Timeout Functionality Demo")
    print("=" * 50)
    print()
    
    print("1. Creating a sample interactive view...")
    view = ImageProcessingView(timeout=2.0)  # 2-second timeout for demo
    
    print("2. Generating sample output images...")
    
    # Create temporary images
    temp_images = []
    for i, color in enumerate(['red', 'green', 'blue'], 1):
        # Create sample image
        img = Image.new('RGB', (100, 100), color=color)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=f'_{color}.png', delete=False)
        img.save(temp_file.name)
        temp_images.append(temp_file.name)
        
        # Create OutputImage object
        output = OutputImage(
            temp_file.name, 
            f"Sample prompt {i}: Make this image {color} and awesome",
            f"output_{color}_{i}.png"
        )
        view.add_output(output)
        print(f"   ✅ Added output {i}: {color} image")
    
    print(f"\n3. View now has {len(view.outputs)} output images stored")
    
    print("4. Simulating timeout behavior...")
    print("   (In real Discord, this would happen after 30 minutes of inactivity)")
    
    # Mock message object to simulate Discord message editing
    class MockMessage:
        def __init__(self):
            self.edit_calls = []
            
        async def edit(self, *, content=None, embeds=None, attachments=None, view=None):
            self.edit_calls.append({
                'content': content,
                'embeds': embeds,
                'attachments': attachments,
                'view': view
            })
            print(f"   📝 Message edited:")
            print(f"      Content: {content}")
            print(f"      Embeds: {len(embeds) if embeds else 0}")
            print(f"      Attachments: {len(attachments) if attachments else 0}")
            print(f"      View removed: {view is None}")
    
    # Set up the mock message
    view.message = MockMessage()
    
    print("\n5. Triggering timeout handler...")
    await view.on_timeout()
    
    print("\n6. Analyzing timeout behavior:")
    edit_call = view.message.edit_calls[0]
    
    # Verify timeout message
    assert "Timed out" in edit_call['content'], "Should indicate timeout"
    print("   ✅ Timeout message correctly displayed")
    
    # Verify embeds for each output
    embeds = edit_call['embeds']
    assert len(embeds) == 3, f"Should have 3 embeds, got {len(embeds)}"
    print(f"   ✅ {len(embeds)} embeds created for output images")
    
    # Verify each embed content
    for i, embed in enumerate(embeds):
        assert "Final Output" in embed.title, f"Embed {i} should indicate final output"
        assert "Timed Out" in embed.title, f"Embed {i} should indicate timeout"
        print(f"   ✅ Embed {i+1}: {embed.title}")
    
    # Verify attachments
    attachments = edit_call['attachments']
    assert len(attachments) == 3, f"Should have 3 attachments, got {len(attachments)}"
    print(f"   ✅ {len(attachments)} image files attached")
    
    # Verify view is removed
    assert edit_call['view'] is None, "View should be removed on timeout"
    print("   ✅ Interactive view components disabled and removed")
    
    print("\n🎉 Timeout functionality working correctly!")
    print("\nKey features implemented:")
    print("• ✅ Automatic timeout after 30 minutes (configurable)")
    print("• ✅ All output images displayed when session times out")
    print("• ✅ Interactive components properly disabled")
    print("• ✅ Clear timeout indication in the message")
    print("• ✅ Multiple outputs handled correctly (up to Discord's 10-embed limit)")
    print("• ✅ Image attachments properly created from stored outputs")
    
    # Cleanup
    import os
    for temp_file in temp_images:
        try:
            os.unlink(temp_file)
        except:
            pass

if __name__ == "__main__":
    asyncio.run(demo_timeout_behavior())