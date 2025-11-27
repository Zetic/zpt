#!/usr/bin/env python3
"""
Voice Connect Module for Discord Bot

This module implements speech-to-speech interaction using OpenAI's GPT-4o Realtime API.
The bot joins a voice channel, listens to users, sends audio to the OpenAI Realtime API,
and plays back audio responses.
"""

import asyncio
import base64
import io
import json
import logging
import os
import struct
from typing import Optional

import discord
from discord.ext import commands
import websockets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_REALTIME_MODEL = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview-2024-10-01')
OPENAI_REALTIME_URL = f"wss://api.openai.com/v1/realtime?model={OPENAI_REALTIME_MODEL}"

# Audio settings for OpenAI Realtime API
# OpenAI expects PCM16 audio at 24kHz mono
OPENAI_SAMPLE_RATE = 24000
OPENAI_CHANNELS = 1
OPENAI_SAMPLE_WIDTH = 2  # 16-bit PCM

# Discord sends Opus audio at 48kHz stereo, which we decode to PCM
DISCORD_SAMPLE_RATE = 48000
DISCORD_CHANNELS = 2


class AudioBuffer:
    """Thread-safe buffer for accumulating audio data before sending to OpenAI."""
    
    def __init__(self, min_size: int = 4800):
        self._buffer = bytearray()
        self._lock = asyncio.Lock()
        self._sync_lock = __import__('threading').Lock()
        self.min_size = min_size  # Minimum bytes to accumulate before sending
    
    def add_sync(self, data: bytes) -> None:
        """Add audio data to the buffer (thread-safe, called from sync code)."""
        with self._sync_lock:
            self._buffer.extend(data)
    
    async def add(self, data: bytes) -> None:
        """Add audio data to the buffer (async version)."""
        async with self._lock:
            with self._sync_lock:
                self._buffer.extend(data)
    
    async def get(self) -> Optional[bytes]:
        """Get buffered audio if sufficient data is available."""
        async with self._lock:
            with self._sync_lock:
                if len(self._buffer) >= self.min_size:
                    data = bytes(self._buffer)
                    self._buffer.clear()
                    return data
                return None
    
    async def flush(self) -> bytes:
        """Get all remaining buffered audio."""
        async with self._lock:
            with self._sync_lock:
                data = bytes(self._buffer)
                self._buffer.clear()
                return data
    
    async def clear(self) -> None:
        """Clear the buffer."""
        async with self._lock:
            with self._sync_lock:
                self._buffer.clear()


class OpenAIAudioSource(discord.AudioSource):
    """Audio source for playing OpenAI responses in Discord voice channel."""
    
    def __init__(self):
        self._buffer = bytearray()
        self._lock = asyncio.Lock()
        self._finished = False
    
    def add_audio(self, pcm_data: bytes) -> None:
        """Add PCM audio data to be played (called from async context)."""
        # This method is called from async code but AudioSource.read() is sync
        # We use a simple bytearray which is thread-safe for these operations
        self._buffer.extend(pcm_data)
    
    def read(self) -> bytes:
        """Read next frame of audio (20ms of stereo 16-bit PCM at 48kHz)."""
        # Discord expects 20ms of stereo 16-bit PCM at 48kHz = 3840 bytes
        frame_size = 3840
        
        if len(self._buffer) >= frame_size:
            frame = bytes(self._buffer[:frame_size])
            del self._buffer[:frame_size]
            return frame
        elif self._finished and len(self._buffer) > 0:
            # Return remaining audio padded with silence
            frame = bytes(self._buffer) + b'\x00' * (frame_size - len(self._buffer))
            self._buffer.clear()
            return frame
        elif self._finished:
            return b''  # Signal end of audio
        else:
            # Not enough data yet, return silence
            return b'\x00' * frame_size
    
    def is_opus(self) -> bool:
        """Return False since we're providing raw PCM."""
        return False
    
    def finish(self) -> None:
        """Mark the audio source as finished."""
        self._finished = True
    
    def has_audio(self) -> bool:
        """Check if there is audio data available."""
        return len(self._buffer) > 0 or not self._finished


def resample_audio(pcm_data: bytes, from_rate: int, to_rate: int, 
                   from_channels: int, to_channels: int) -> bytes:
    """
    Simple audio resampling using linear interpolation.
    Converts PCM16 audio between different sample rates and channel counts.
    """
    if from_rate == to_rate and from_channels == to_channels:
        return pcm_data
    
    # Convert bytes to samples (16-bit signed)
    samples = struct.unpack(f'<{len(pcm_data) // 2}h', pcm_data)
    
    # Convert to mono if needed
    if from_channels == 2 and to_channels == 1:
        # Average stereo channels
        samples = [(samples[i] + samples[i + 1]) // 2 
                   for i in range(0, len(samples), 2)]
    elif from_channels == 1 and to_channels == 2:
        # Duplicate mono to stereo
        samples = [sample for s in samples for sample in (s, s)]
    
    # Resample if rates differ
    if from_rate != to_rate:
        ratio = from_rate / to_rate
        new_length = int(len(samples) / ratio)
        resampled = []
        for i in range(new_length):
            src_idx = i * ratio
            idx_low = int(src_idx)
            idx_high = min(idx_low + 1, len(samples) - 1)
            frac = src_idx - idx_low
            # Linear interpolation
            sample = int(samples[idx_low] * (1 - frac) + samples[idx_high] * frac)
            resampled.append(max(-32768, min(32767, sample)))
        samples = resampled
    
    # Convert back to bytes
    return struct.pack(f'<{len(samples)}h', *samples)


class VoiceSession:
    """Manages a single voice session with OpenAI Realtime API."""
    
    def __init__(self, guild_id: int, voice_client: discord.VoiceClient):
        self.guild_id = guild_id
        self.voice_client = voice_client
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.audio_buffer = AudioBuffer()
        self.audio_source: Optional[OpenAIAudioSource] = None
        self._running = False
        self._tasks: list = []
        self._response_in_progress = False
    
    async def connect_to_openai(self) -> bool:
        """Establish WebSocket connection to OpenAI Realtime API."""
        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY not configured")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            self.ws = await websockets.connect(
                OPENAI_REALTIME_URL,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=20
            )
            
            logger.info(f"Connected to OpenAI Realtime API for guild {self.guild_id}")
            
            # Configure the session
            await self._configure_session()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI Realtime API: {e}")
            return False
    
    async def _configure_session(self) -> None:
        """Send session configuration to OpenAI."""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "You are a helpful voice assistant in a Discord voice chat. "
                               "Keep responses concise and conversational. "
                               "Respond naturally to questions and participate in conversations.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                }
            }
        }
        
        await self.ws.send(json.dumps(config))
        logger.debug("Sent session configuration to OpenAI")
    
    async def start(self) -> None:
        """Start the voice session processing."""
        self._running = True
        
        # Start the tasks for processing
        self._tasks = [
            asyncio.create_task(self._receive_from_openai()),
            asyncio.create_task(self._send_audio_to_openai()),
        ]
        
        logger.info(f"Voice session started for guild {self.guild_id}")
    
    async def stop(self) -> None:
        """Stop the voice session."""
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._tasks.clear()
        
        # Close WebSocket
        if self.ws:
            await self.ws.close()
            self.ws = None
        
        # Stop audio playback
        if self.audio_source:
            self.audio_source.finish()
        
        logger.info(f"Voice session stopped for guild {self.guild_id}")
    
    async def _send_audio_to_openai(self) -> None:
        """Send buffered audio to OpenAI."""
        while self._running:
            try:
                audio_data = await self.audio_buffer.get()
                if audio_data and self.ws:
                    # Convert Discord audio format to OpenAI format
                    # Discord: 48kHz stereo -> OpenAI: 24kHz mono
                    resampled = resample_audio(
                        audio_data,
                        DISCORD_SAMPLE_RATE, OPENAI_SAMPLE_RATE,
                        DISCORD_CHANNELS, OPENAI_CHANNELS
                    )
                    
                    # Encode as base64 for the API
                    encoded = base64.b64encode(resampled).decode('utf-8')
                    
                    message = {
                        "type": "input_audio_buffer.append",
                        "audio": encoded
                    }
                    
                    await self.ws.send(json.dumps(message))
                    
                await asyncio.sleep(0.02)  # 20ms intervals
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error sending audio to OpenAI: {e}")
                await asyncio.sleep(0.1)
    
    async def _receive_from_openai(self) -> None:
        """Receive and process messages from OpenAI."""
        while self._running and self.ws:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                
                event_type = data.get("type", "")
                
                if event_type == "response.audio.delta":
                    # Received audio chunk from OpenAI
                    audio_b64 = data.get("delta", "")
                    if audio_b64:
                        audio_bytes = base64.b64decode(audio_b64)
                        
                        # Convert OpenAI format to Discord format
                        # OpenAI: 24kHz mono -> Discord: 48kHz stereo
                        resampled = resample_audio(
                            audio_bytes,
                            OPENAI_SAMPLE_RATE, DISCORD_SAMPLE_RATE,
                            OPENAI_CHANNELS, DISCORD_CHANNELS
                        )
                        
                        # Add to playback buffer
                        if self.audio_source:
                            self.audio_source.add_audio(resampled)
                
                elif event_type == "response.audio.done":
                    logger.debug("OpenAI audio response complete")
                    self._response_in_progress = False
                
                elif event_type == "response.created":
                    self._response_in_progress = True
                    # Start playing audio if not already
                    if self.voice_client and not self.voice_client.is_playing():
                        self.audio_source = OpenAIAudioSource()
                        self.voice_client.play(
                            self.audio_source,
                            after=lambda e: logger.debug("Finished playing audio")
                        )
                
                elif event_type == "error":
                    error_msg = data.get("error", {}).get("message", "Unknown error")
                    logger.error(f"OpenAI error: {error_msg}")
                
                elif event_type == "input_audio_buffer.speech_started":
                    logger.debug("Speech detected")
                
                elif event_type == "input_audio_buffer.speech_stopped":
                    logger.debug("Speech ended")
                
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = data.get("transcript", "")
                    if transcript:
                        logger.info(f"User said: {transcript}")
                
            except asyncio.CancelledError:
                break
            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                break
            except Exception as e:
                logger.error(f"Error receiving from OpenAI: {e}")
                await asyncio.sleep(0.1)
    
    def receive_audio(self, pcm_data: bytes) -> None:
        """
        Receive audio data from Discord voice.
        This is called synchronously when audio is received from users in the voice channel.
        Uses thread-safe sync method to avoid creating async tasks for each packet.
        """
        self.audio_buffer.add_sync(pcm_data)


class VoiceSink:
    """
    Audio sink for receiving voice data from Discord.
    Note: This requires voice receive capability in discord.py or Pycord.
    Standard discord.py doesn't have native voice receive, but Pycord does.
    """
    
    def __init__(self, session: VoiceSession):
        self.session = session
    
    def write(self, data) -> None:
        """Called when audio data is received."""
        if hasattr(data, 'pcm'):
            self.session.receive_audio(data.pcm)
        elif isinstance(data, bytes):
            self.session.receive_audio(data)
    
    def cleanup(self) -> None:
        """Clean up resources."""
        pass


class VoiceConnectCog(commands.Cog):
    """Cog for voice connect functionality."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions: dict[int, VoiceSession] = {}  # guild_id -> VoiceSession
    
    async def cog_unload(self) -> None:
        """Clean up when cog is unloaded."""
        for session in list(self.sessions.values()):
            await session.stop()
        self.sessions.clear()
    
    @discord.app_commands.command(
        name="connect",
        description="Join your voice channel and start speech-to-speech interaction"
    )
    async def connect(self, interaction: discord.Interaction) -> None:
        """Join the user's voice channel and start listening."""
        # Check if user is in a voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                "❌ You need to be in a voice channel to use this command!",
                ephemeral=True
            )
            return
        
        voice_channel = interaction.user.voice.channel
        guild_id = interaction.guild_id
        
        # Check if already connected in this guild
        if guild_id in self.sessions:
            await interaction.response.send_message(
                "❌ I'm already connected to a voice channel in this server. "
                "Use `/disconnect` first.",
                ephemeral=True
            )
            return
        
        # Check for OpenAI API key
        if not OPENAI_API_KEY:
            await interaction.response.send_message(
                "❌ OpenAI API key is not configured. Please set OPENAI_API_KEY in the environment.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Connect to voice channel
            voice_client = await voice_channel.connect()
            
            # Create voice session
            session = VoiceSession(guild_id, voice_client)
            
            # Connect to OpenAI
            if not await session.connect_to_openai():
                await voice_client.disconnect()
                await interaction.followup.send(
                    "❌ Failed to connect to OpenAI Realtime API. Please check the logs.",
                    ephemeral=True
                )
                return
            
            # Start the session
            await session.start()
            
            # Store the session
            self.sessions[guild_id] = session
            
            # Attempt to set up voice receiving if the library supports it
            # Note: Standard discord.py doesn't have native voice receive.
            # For full voice receive support, use Pycord or discord-ext-voice-recv.
            voice_receive_enabled = False
            if hasattr(voice_client, 'listen'):
                # Pycord-style voice receive
                try:
                    sink = VoiceSink(session)
                    voice_client.listen(sink)
                    voice_receive_enabled = True
                    logger.info("Voice receive enabled using Pycord-style API")
                except Exception as e:
                    logger.warning(f"Failed to enable voice receive: {e}")
            elif hasattr(voice_client, 'start_recording'):
                # Alternative voice receive API
                try:
                    sink = VoiceSink(session)
                    voice_client.start_recording(sink, lambda e: None)
                    voice_receive_enabled = True
                    logger.info("Voice receive enabled using start_recording API")
                except Exception as e:
                    logger.warning(f"Failed to enable voice receive: {e}")
            
            status_msg = f"✅ Connected to **{voice_channel.name}**!\n\n"
            if voice_receive_enabled:
                status_msg += "🎙️ I'm now listening. Speak naturally and I'll respond.\n"
            else:
                status_msg += ("⚠️ Voice receive is not available with this discord.py version.\n"
                              "For full voice input support, install Pycord or discord-ext-voice-recv.\n"
                              "Audio output is still available.\n")
            status_msg += "Use `/disconnect` to end the session."
            
            await interaction.followup.send(status_msg)
            
            logger.info(f"Connected to voice channel {voice_channel.name} in guild {guild_id}")
            
        except discord.ClientException as e:
            logger.error(f"Discord client error: {e}")
            await interaction.followup.send(
                "❌ Failed to connect to voice channel. I may already be connected elsewhere.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error connecting to voice: {e}")
            await interaction.followup.send(
                f"❌ An error occurred while connecting: {str(e)}",
                ephemeral=True
            )
    
    @discord.app_commands.command(
        name="disconnect",
        description="Leave the voice channel and end the speech session"
    )
    async def disconnect(self, interaction: discord.Interaction) -> None:
        """Disconnect from voice channel and cleanup."""
        guild_id = interaction.guild_id
        
        if guild_id not in self.sessions:
            await interaction.response.send_message(
                "❌ I'm not connected to a voice channel in this server.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            session = self.sessions.pop(guild_id)
            await session.stop()
            
            # Disconnect from voice
            if session.voice_client and session.voice_client.is_connected():
                await session.voice_client.disconnect()
            
            await interaction.followup.send(
                "✅ Disconnected from voice channel. Goodbye! 👋"
            )
            
            logger.info(f"Disconnected from voice in guild {guild_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            await interaction.followup.send(
                f"❌ Error while disconnecting: {str(e)}",
                ephemeral=True
            )
    
    @commands.Cog.listener()
    async def on_voice_state_update(
        self, 
        member: discord.Member, 
        before: discord.VoiceState, 
        after: discord.VoiceState
    ) -> None:
        """Handle voice state changes."""
        guild_id = member.guild.id
        
        # Check if we have a session in this guild
        if guild_id not in self.sessions:
            return
        
        session = self.sessions[guild_id]
        
        # If the bot was disconnected (kicked, moved, etc.)
        if member.id == self.bot.user.id and after.channel is None:
            logger.info(f"Bot was disconnected from voice in guild {guild_id}")
            await session.stop()
            self.sessions.pop(guild_id, None)


async def setup(bot: commands.Bot) -> None:
    """Set up the voice connect cog."""
    await bot.add_cog(VoiceConnectCog(bot))
    logger.info("VoiceConnectCog loaded")
