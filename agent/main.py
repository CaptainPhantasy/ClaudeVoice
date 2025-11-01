"""
ClaudeVoice - Main Agent Implementation
A production-ready voice AI agent with tool-calling capabilities
Built with LiveKit Agents Framework
"""

import asyncio
import logging
import os
from typing import Optional
from datetime import datetime

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    JobRequest,
    JobInfo
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, silero
from livekit.agents.voice_assistant import AssistantCallContext

# Import custom tools
from tools.weather import weather_tool
from tools.calendar import calendar_tool, check_availability
from tools.database import database_query
from tools.voicemail import detect_voicemail

# Import configuration
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClaudeVoiceAgent:
    """Main voice agent class with tool-calling capabilities"""

    def __init__(self):
        self.agent_name = config.agent_name
        self.is_telephony = False
        self.call_metadata = {}
        self.config = config

    def get_system_instructions(self, is_phone_call: bool = False) -> str:
        """Get system instructions based on context"""
        base_instructions = """You are Claude, a helpful and professional voice assistant.
        Keep responses concise, natural, and friendly.
        Do not use special formatting, markdown, or emojis in responses.
        Speak naturally as if in a phone conversation."""

        if is_phone_call:
            return base_instructions + """
            You are handling a phone call. Be extra clear and professional.
            If you detect a voicemail system, leave a brief message and hang up.
            Always confirm important information by repeating it back."""

        return base_instructions + """
        You have access to various tools to help users:
        - Weather information
        - Calendar management
        - Database queries
        - General assistance"""

    async def handle_tool_calls(self, assistant: VoicePipelineAgent, tool_calls):
        """Process and execute tool calls from the LLM"""
        try:
            for tool_call in tool_calls:
                logger.info(f"Executing tool: {tool_call.name}")

                if tool_call.name == "detect_voicemail":
                    is_voicemail = await detect_voicemail(assistant)
                    if is_voicemail:
                        await assistant.say(
                            "Hi, this is Claude calling on behalf of the user. "
                            "Please call back at your earliest convenience. Thank you."
                        )
                        # Terminate the call if voicemail
                        return True

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            await assistant.say("I encountered an issue. Let me try a different approach.")

        return False

async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent"""
    logger.info(f"Agent starting for room: {ctx.room.name}")

    # Initialize agent instance
    agent = ClaudeVoiceAgent()

    # Check if this is a phone call
    is_phone_call = ctx.room.name.startswith("call-")
    if is_phone_call:
        agent.is_telephony = True
        logger.info("Handling telephony call")

    # Parse room metadata if available
    if ctx.room.metadata:
        try:
            import json
            agent.call_metadata = json.loads(ctx.room.metadata)
            logger.info(f"Call metadata: {agent.call_metadata}")
        except:
            pass

    # Set up system instructions
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=agent.get_system_instructions(is_phone_call)
    )

    # Connect to room with audio-only subscription for phone calls
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    logger.info("Connected to room, initializing voice pipeline")

    # Configure noise cancellation based on call type
    from livekit.agents.pipeline import RoomInputOptions
    from livekit.plugins.bvc import BVCTelephony, BVC

    noise_cancellation = BVCTelephony() if is_phone_call else BVC()

    # Create voice pipeline agent with optimized settings
    try:
        assistant = VoicePipelineAgent(
            vad=silero.VAD.load(
                min_speech_duration=config.vad_min_speech_duration,
                min_silence_duration=config.vad_min_silence_duration_phone if is_phone_call else config.vad_min_silence_duration
            ),
            stt=openai.STT(
                model=config.stt_model,
                language=config.stt_language if config.stt_language != "auto" else None
            ),
            llm=openai.LLM(
                model=config.llm_model,
                temperature=config.llm_temperature,
                max_tokens=config.llm_max_tokens,
            ),
            tts=openai.TTS(
                model=config.tts_model,
                voice=config.tts_voice,
                speed=config.tts_speed
            ),
            chat_ctx=initial_ctx,
            room_input_opts=RoomInputOptions(
                noise_cancellation=noise_cancellation if config.enable_noise_cancellation else None
            )
        )

        logger.info("Voice pipeline initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize voice pipeline: {e}")
        raise

    # Register tool functions
    logger.info("Registering tool functions")
    assistant.llm.register_tool(weather_tool)
    assistant.llm.register_tool(calendar_tool)
    assistant.llm.register_tool(check_availability)
    assistant.llm.register_tool(database_query)

    # Register voicemail detection for phone calls
    if is_phone_call:
        assistant.llm.register_tool(detect_voicemail)

    # Set up tool call handler
    @assistant.on("tool_calls")
    async def on_tool_calls(tool_calls):
        should_hangup = await agent.handle_tool_calls(assistant, tool_calls)
        if should_hangup and is_phone_call:
            # End the call
            await ctx.room.disconnect()

    # Start the assistant
    assistant.start(ctx.room)
    logger.info("Assistant started successfully")

    # Generate appropriate greeting
    if is_phone_call:
        from_number = agent.call_metadata.get("from_number", "unknown")
        greeting = (
            "Hello, this is Claude, your AI assistant. "
            "How may I help you today?"
        )
    else:
        greeting = (
            "Hi! I'm Claude, your voice assistant. "
            "I can help you check the weather, manage your calendar, "
            "or answer questions. What can I do for you?"
        )

    await asyncio.sleep(1)  # Brief pause before greeting
    await assistant.say(greeting)

    # Handle conversation until room closes
    @ctx.room.on("room_closed")
    async def on_room_closed():
        logger.info("Room closed, shutting down agent")
        await assistant.aclose()

    # Keep the agent running
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        logger.info("Agent cancelled, cleaning up")
        await assistant.aclose()

async def request_fnc(req: JobRequest) -> JobInfo:
    """Handle job requests for explicit dispatch"""
    logger.info(f"Received job request for room: {req.room.name}")

    # Accept all requests for rooms starting with "call-"
    if req.room.name.startswith("call-"):
        return JobInfo(
            accept=True,
            metadata={"type": "telephony_call"}
        )

    # Accept other requests by default
    return JobInfo(accept=True)

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(".env.local")

    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)

    # Log configuration
    logger.info(f"Configuration loaded: {config}")
    voice_info = config.get_tts_voice_info()
    logger.info(f"TTS Voice: {voice_info['voice']} - {voice_info['description']}")

    # Configure worker options
    worker_options = WorkerOptions(
        entrypoint_fnc=entrypoint,
        request_fnc=request_fnc,
        agent_name=config.agent_name,
        worker_type="voice",
        max_idle_time=60,  # Disconnect after 60s of inactivity
        num_idle_workers=2,  # Keep 2 workers ready
        max_workers=10  # Scale up to 10 concurrent calls
    )

    logger.info(f"Starting ClaudeVoice agent: {worker_options.agent_name}")

    # Run the agent
    cli.run_app(worker_options)