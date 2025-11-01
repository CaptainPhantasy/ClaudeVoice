"""
ClaudeVoice - Fixed Main Agent for LiveKit 1.2.17
Uses OpenAI Assistants API via the plugin
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

# Import simplified (mock) tools
from tools.tools_simple import SIMPLE_TOOLS

# Import NEW real API tools
from tools.courtreserve_tools import get_ipc_event_list

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent"""
    logger.info(f"Agent starting for room: {ctx.room.name}")

    is_phone_call = ctx.room.name.startswith("call-")
    if is_phone_call:
        logger.info("Handling telephony call")

    # --- System Prompt is NO LONGER NEEDED HERE ---
    # The OpenAI Assistant's "Instructions" field now handles this.
    # We pass None to the agent's initial_ctx.

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info("Connected to room")

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
                assistant_id=config.openai_assistant_id  # <-- THIS IS THE KEY CHANGE
            ),
            tts=openai.TTS(
                model=config.tts_model,
                voice=config.tts_voice,
                speed=config.tts_speed
            ),
            initial_ctx=None,  # <-- Assistant handles the prompt
            max_function_calls=5
        )

        logger.info(f"Voice agent initialized with Assistant ID: {config.openai_assistant_id}")

        # --- TOOL REGISTRATION ---
        # This remains the same. The LLM plugin is smart enough
        # to match these functions to the ones defined in your
        # OpenAI Assistant dashboard.

        tools_registered = 0

        # 1. Register the REAL API tool
        try:
            agent.add_function("get_ipc_event_list", get_ipc_event_list)
            tools_registered += 1
            logger.info("Registered REAL tool: get_ipc_event_list")
        except Exception as e:
            logger.warning(f"Could not register REAL tool get_ipc_event_list: {e}")

        # 2. Register the other SIMPLE_TOOLS
        for tool_name, tool_func in SIMPLE_TOOLS.items():
            if "calendar" in tool_name or "appointment" in tool_name:
                continue

            try:
                agent.add_function(tool_name, tool_func)
                tools_registered += 1
                logger.info(f"Registered simple tool: {tool_name}")
            except Exception as e:
                logger.warning(f"Could not register simple tool {tool_name}: {e}")

        logger.info(f"Successfully registered {tools_registered} total tools")
        # ---------------------------------

        agent.start(ctx.room)
        logger.info("Agent started successfully")

        # The greeting is still good to have, as the Assistant
        # won't speak until the user speaks first.
        greeting = "Hello! This is ACE from the Indianapolis Pickleball Club. How can I help you today?"
        if not is_phone_call:
             greeting = "Hello! I'm ACE, your voice assistant for the Indianapolis Pickleball Club. How can I help?"

        await asyncio.sleep(1)
        # We set add_to_history=False because the Assistant API
        # will get this from the STT stream anyway.
        await agent.say(greeting, add_to_history=False)

        logger.info("Agent is ready and listening")

    except Exception as e:
        logger.error(f"Error initializing agent: {e}")
        raise

    # Keep the agent running
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        logger.info("Agent cancelled, cleaning up")
        await agent.close()


if __name__ == "__main__":
    from dotenv import load_dotenv
    from pathlib import Path
    import os

    current_file = Path(__file__).resolve()
    parent_dir = current_file.parent.parent
    env_path = parent_dir / '.env.local'

    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment from: {env_path}")
    else:
        logger.error(f"Could not find .env.local at {env_path}")
        logger.error(f"Please ensure .env.local exists in {parent_dir}")
        exit(1)

    from config import Config
    config = Config()

    try:
        config.validate()  # This will now check for all keys
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env.local file")
        exit(1)

    logger.info(f"Configuration loaded: Config(agent_name={config.agent_name}, assistant_id={config.openai_assistant_id})")

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

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint
        )
    )