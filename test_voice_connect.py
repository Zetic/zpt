#!/usr/bin/env python3
"""
Test script for Voice Connect functionality.
Tests the voice module components without requiring Discord connection.
"""

import asyncio
import base64
import struct
import sys
import os

# Add current directory to path
sys.path.insert(0, '.')


def test_audio_buffer():
    """Test AudioBuffer class functionality"""
    print("Testing AudioBuffer class...")
    
    from voice_connect import AudioBuffer
    
    async def run_test():
        buffer = AudioBuffer(min_size=100)
        
        # Initially empty
        result = await buffer.get()
        assert result is None, "Empty buffer should return None"
        
        # Test sync add
        buffer.add_sync(b'x' * 50)
        result = await buffer.get()
        assert result is None, "Not enough data should return None"
        
        # Add more data to exceed minimum
        buffer.add_sync(b'y' * 60)
        result = await buffer.get()
        assert result is not None, "Should return data when min_size exceeded"
        assert len(result) == 110, f"Should return all buffered data, got {len(result)}"
        
        # Buffer should be empty now
        result = await buffer.get()
        assert result is None, "Buffer should be empty after get()"
        
        # Test async add
        await buffer.add(b'a' * 120)
        result = await buffer.get()
        assert result is not None and len(result) == 120, "Async add should work"
        
        # Test flush
        buffer.add_sync(b'z' * 30)
        result = await buffer.flush()
        assert len(result) == 30, "Flush should return all data"
        
        # Test clear
        buffer.add_sync(b'w' * 50)
        await buffer.clear()
        result = await buffer.flush()
        assert len(result) == 0, "Buffer should be empty after clear()"
    
    asyncio.run(run_test())
    print("✓ AudioBuffer class working correctly")
    return True


def test_resample_audio():
    """Test audio resampling functionality"""
    print("Testing audio resampling...")
    
    from voice_connect import resample_audio
    
    # Create test audio: 100 samples of stereo 16-bit PCM
    samples = [1000, -1000] * 100  # Alternating L/R channels
    test_audio = struct.pack(f'<{len(samples)}h', *samples)
    
    # Test stereo to mono conversion
    mono = resample_audio(
        test_audio,
        from_rate=48000, to_rate=48000,
        from_channels=2, to_channels=1
    )
    # Mono should have half the samples
    mono_samples = struct.unpack(f'<{len(mono) // 2}h', mono)
    assert len(mono_samples) == 100, f"Mono should have 100 samples, got {len(mono_samples)}"
    # Each mono sample should be average of stereo pair (0 in this case)
    assert all(s == 0 for s in mono_samples), "Mono average should be 0"
    
    # Test mono to stereo conversion
    mono_input = struct.pack('<10h', *([500] * 10))
    stereo = resample_audio(
        mono_input,
        from_rate=48000, to_rate=48000,
        from_channels=1, to_channels=2
    )
    stereo_samples = struct.unpack(f'<{len(stereo) // 2}h', stereo)
    assert len(stereo_samples) == 20, f"Stereo should have 20 samples, got {len(stereo_samples)}"
    
    # Test sample rate conversion (48kHz to 24kHz = half the samples)
    test_24k = struct.pack('<100h', *range(100))
    result = resample_audio(
        test_24k,
        from_rate=48000, to_rate=24000,
        from_channels=1, to_channels=1
    )
    result_samples = struct.unpack(f'<{len(result) // 2}h', result)
    assert len(result_samples) == 50, f"Should have 50 samples, got {len(result_samples)}"
    
    # Test no-op (same rate and channels)
    same = resample_audio(
        test_audio,
        from_rate=48000, to_rate=48000,
        from_channels=2, to_channels=2
    )
    assert same == test_audio, "No conversion should return same data"
    
    print("✓ Audio resampling working correctly")
    return True


def test_openai_audio_source():
    """Test OpenAIAudioSource class functionality"""
    print("Testing OpenAIAudioSource class...")
    
    from voice_connect import OpenAIAudioSource
    
    source = OpenAIAudioSource()
    
    # Initially should return silence (not finished, no data)
    frame = source.read()
    assert len(frame) == 3840, "Frame should be 3840 bytes (20ms stereo PCM)"
    assert frame == b'\x00' * 3840, "Should return silence when no data"
    
    # Add some audio
    test_audio = b'\x01' * 3840
    source.add_audio(test_audio)
    
    # Should return the audio
    frame = source.read()
    assert frame == test_audio, "Should return added audio"
    
    # Back to silence
    frame = source.read()
    assert frame == b'\x00' * 3840, "Should return silence again"
    
    # Test finish behavior
    source.add_audio(b'\x02' * 1000)  # Less than a full frame
    source.finish()
    
    frame = source.read()
    assert len(frame) == 3840, "Should pad to full frame size"
    assert frame.startswith(b'\x02' * 1000), "Should contain the audio data"
    
    # After finish with no data, should return empty
    frame = source.read()
    assert frame == b'', "Should return empty after finished"
    
    # Test is_opus
    source2 = OpenAIAudioSource()
    assert source2.is_opus() is False, "Should not be opus"
    
    print("✓ OpenAIAudioSource class working correctly")
    return True


def test_voice_session_creation():
    """Test VoiceSession class initialization"""
    print("Testing VoiceSession class...")
    
    from voice_connect import VoiceSession
    
    # Create with mock voice client
    class MockVoiceClient:
        def is_connected(self):
            return True
        def is_playing(self):
            return False
    
    mock_vc = MockVoiceClient()
    session = VoiceSession(guild_id=12345, voice_client=mock_vc)
    
    assert session.guild_id == 12345, "Guild ID should be set"
    assert session.voice_client is mock_vc, "Voice client should be set"
    assert session.ws is None, "WebSocket should start as None"
    assert session._running is False, "Should not be running initially"
    
    print("✓ VoiceSession class working correctly")
    return True


def test_voice_cog_initialization():
    """Test VoiceConnectCog initialization"""
    print("Testing VoiceConnectCog class...")
    
    from voice_connect import VoiceConnectCog
    
    # Create mock bot
    class MockBot:
        user = None
    
    mock_bot = MockBot()
    cog = VoiceConnectCog(mock_bot)
    
    assert cog.bot is mock_bot, "Bot should be set"
    assert len(cog.sessions) == 0, "Sessions should be empty initially"
    
    print("✓ VoiceConnectCog class working correctly")
    return True


def test_environment_variables():
    """Test environment variable documentation"""
    print("Testing environment variable documentation...")
    
    with open('.env.example', 'r') as f:
        content = f.read()
    
    required_vars = [
        'DISCORD_BOT_TOKEN',
        'REPLICATE_API_TOKEN',
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if var not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"✗ Missing environment variables: {missing_vars}")
        return False
    
    print("✓ All required environment variables documented")
    return True


def test_requirements():
    """Test requirements.txt includes voice dependencies"""
    print("Testing requirements.txt for voice dependencies...")
    
    with open('requirements.txt', 'r') as f:
        content = f.read()
    
    required_packages = [
        'discord.py',
        'PyNaCl',
        'websockets'
    ]
    
    missing_packages = []
    for package in required_packages:
        if package not in content:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"✗ Missing packages: {missing_packages}")
        return False
    
    print("✓ All voice dependencies listed")
    return True


def main():
    """Run all tests"""
    print("Running Voice Connect Tests...")
    print("=" * 50)
    
    tests = [
        test_environment_variables,
        test_requirements,
        test_audio_buffer,
        test_resample_audio,
        test_openai_audio_source,
        test_voice_session_creation,
        test_voice_cog_initialization,
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
            import traceback
            traceback.print_exc()
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All voice connect tests passed!")
        return True
    else:
        print("✗ Some tests failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
