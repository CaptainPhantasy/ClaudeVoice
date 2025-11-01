"""
ClaudeVoice - Simplified Main Agent for LiveKit 1.2.17
Uses the new API structure
"""

import asyncio
import logging
import os
from typing import Optional
from datetime import datetime

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent
from livekit.plugins import openai, silero

# Import configuration
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent"""
    logger.info(f"Agent starting for room: {ctx.room.name}")

    # Check if this is a phone call
    is_phone_call = ctx.room.name.startswith("call-")
    if is_phone_call:
        logger.info("Handling telephony call")

    # Set up system instructions
    initial_ctx = llm.ChatContext().append(
        role="system",
        text="""You are Claude, a helpful and professional voice assistant.
        Keep responses concise, natural, and friendly.
        Do not use special formatting, markdown, or emojis in responses.
        Speak naturally as if in a phone conversation.
        You have access to tools to help with weather, calendar, and database queries."""
    )

    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info("Connected to room")

    # Create voice agent with OpenAI services
    try:
        agent = Agent(
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
                temperature=config.llm_temperature
            ),
            tts=openai.TTS(
                model=config.tts_model,
                voice=config.tts_voice,
                speed=config.tts_speed
            ),
            initial_ctx=initial_ctx,
            max_function_calls=5  # Allow up to 5 tool calls per turn
        )

        logger.info("Voice agent initialized successfully")

        # Import and register tools
        try:
            from tools.weather import weather_tool
            from tools.calendar import calendar_tool, check_availability
            from tools.database import database_query

            agent.add_function(weather_tool)
            agent.add_function(calendar_tool)
            agent.add_function(check_availability)
            agent.add_function(database_query)

            logger.info("Tools registered successfully")
        except Exception as e:
            logger.warning(f"Some tools could not be loaded: {e}")

        # Start the agent
        agent.start(ctx.room)
        logger.info("Agent started")

        # Generate greeting
        greeting = "Hello! I'm Claude, your AI assistant. How can I help you today?"
        if is_phone_call:
            greeting = "Hello, this is Claude, your AI assistant. How may I help you?"

        await asyncio.sleep(1)  # Brief pause before greeting
        await agent.say(greeting, add_to_history=True)

    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        raise

    # Keep the agent running
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        logger.info("Agent cancelled, cleaning up")
        await agent.close()


if __name__ == "__main__":
    # Load environment variables from parent directory
    from dotenv import load_dotenv
    import os

    # Try multiple possible locations for .env.local
    env_locations = [
        "../.env.local",  # Parent directory
        ".env.local",     # Current directory
        ".env"            # Standard .env file
    ]

    env_loaded = False
    for env_path in env_locations:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"Loaded environment from: {env_path}")
            env_loaded = True
            break

    if not env_loaded:
        logger.warning("No .env file found, using system environment variables")

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

    # Configure worker options (simplified for new API)
    worker_options = WorkerOptions(
        entrypoint_fnc=entrypoint
    )

    logger.info(f"Starting ClaudeVoice agent: {config.agent_name}")

    # Run the agent
    cli.run_app(worker_options)