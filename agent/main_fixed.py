"""
ClaudeVoice - Fixed Main Agent for LiveKit 1.2.17
Uses simplified tools without decorators
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

# Import simplified tools
from tools.tools_simple import SIMPLE_TOOLS

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

    # Set up system instructions with tool descriptions
    system_prompt = """You are Claude, a helpful and professional voice assistant.
    Keep responses concise, natural, and friendly.
    Do not use special formatting, markdown, or emojis in responses.
    Speak naturally as if in a phone conversation.

    You have access to these tools to help users:
    - get_weather: Get current weather for any location
    - check_calendar: Check calendar availability
    - create_appointment: Schedule appointments
    - query_database: Look up information
    - recommend_activity: Suggest activities based on conditions
    - calculate: Perform mathematical calculations
    - get_current_time: Get current time in any timezone
    - take_note: Save notes or reminders

    When users ask for information these tools can provide, use them to give accurate responses."""

    initial_ctx = llm.ChatContext().append(
        role="system",
        text=system_prompt
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
            max_function_calls=5
        )

        logger.info("Voice agent initialized successfully")

        # Register simplified tools
        tools_registered = 0
        for tool_name, tool_func in SIMPLE_TOOLS.items():
            try:
                # Create a wrapper that matches LiveKit's expected format
                async def tool_wrapper(*args, **kwargs):
                    result = await tool_func(*args, **kwargs)
                    return result

                # Copy the original function's attributes
                tool_wrapper.__name__ = tool_func.__name__
                tool_wrapper.__doc__ = tool_func.__doc__

                agent.add_function(tool_func)
                tools_registered += 1
                logger.info(f"Registered tool: {tool_name}")
            except Exception as e:
                logger.warning(f"Could not register tool {tool_name}: {e}")

        logger.info(f"Successfully registered {tools_registered} tools")

        # Start the agent
        agent.start(ctx.room)
        logger.info("Agent started successfully")

        # Generate greeting
        greeting = "Hello! I'm Claude, your AI assistant. I can help you with weather information, calendar management, calculations, and more. How can I help you today?"
        if is_phone_call:
            greeting = "Hello, this is Claude, your AI assistant. How may I help you?"

        await asyncio.sleep(1)  # Brief pause before greeting
        await agent.say(greeting)

        # Keep the agent running
        logger.info("Agent is ready and listening")

    except Exception as e:
        logger.error(f"Error initializing agent: {e}")
        raise


if __name__ == "__main__":
    # Load environment variables from parent directory
    from dotenv import load_dotenv
    from pathlib import Path
    import os

    # Get the absolute path to the parent directory's .env.local
    current_file = Path(__file__).resolve()
    parent_dir = current_file.parent.parent
    env_path = parent_dir / '.env.local'

    # Try to load the .env.local file
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment from: {env_path}")
    else:
        logger.error(f"Could not find .env.local at {env_path}")
        logger.error(f"Please ensure .env.local exists in {parent_dir}")
        exit(1)

    # Reload configuration after loading environment variables
    from config import Config
    config = Config()

    # Validate configuration
    logger.info(f"Configuration loaded: Config(agent_name={config.agent_name}, llm_model={config.llm_model}, tts_voice={config.tts_voice}, stt_language={config.stt_language})")

    if not config.livekit_url or not config.livekit_api_key:
        logger.error("Missing LiveKit configuration. Please check your .env.local file.")
        exit(1)

    if not config.openai_api_key:
        logger.error("Missing OpenAI API key. Please check your .env.local file.")
        exit(1)

    # Show TTS voice info
    voice_descriptions = {
        "alloy": "Neutral and balanced voice",
        "echo": "Warm and engaging voice",
        "fable": "Expressive and dynamic voice",
        "onyx": "Deep and authoritative voice",
        "nova": "Friendly and conversational voice",
        "shimmer": "Soft and pleasant voice"
    }
    logger.info(f"TTS Voice: {config.tts_voice} - {voice_descriptions.get(config.tts_voice, 'Custom voice')}")

    logger.info(f"Starting ClaudeVoice agent: {config.agent_name}")

    # Start the agent
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint
        )
    )