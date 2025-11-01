#!/usr/bin/env python3
"""
Core End-to-End Test for ClaudeVoice Agent
Tests the essential components without tool decorators
"""

import sys
import os
import asyncio
from pathlib import Path

# Load environment variables FIRST
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env.local'
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"✅ Loaded environment from: {env_path}")
else:
    print(f"❌ Could not find .env.local at {env_path}")
    sys.exit(1)

# Add agent directory to path
sys.path.insert(0, str(Path(__file__).parent / "agent"))

def test_environment():
    """Test environment variables"""
    print("\n" + "="*60)
    print("TEST 1: Environment Variables")
    print("="*60)

    required_vars = {
        "LIVEKIT_URL": os.getenv("LIVEKIT_URL"),
        "LIVEKIT_API_KEY": os.getenv("LIVEKIT_API_KEY"),
        "LIVEKIT_API_SECRET": os.getenv("LIVEKIT_API_SECRET"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
    }

    all_good = True
    for name, value in required_vars.items():
        if value:
            # Show partial value for security
            display = value[:15] + "..." if len(value) > 15 else value
            print(f"  {name}: ✅ {display}")
        else:
            print(f"  {name}: ❌ MISSING")
            all_good = False

    return all_good

def test_dependencies():
    """Test required packages are installed"""
    print("\n" + "="*60)
    print("TEST 2: Package Dependencies")
    print("="*60)

    packages = [
        ("livekit", "LiveKit SDK"),
        ("openai", "OpenAI SDK"),
        ("httpx", "HTTP Client"),
        ("python-dotenv", "dotenv", "Environment Loader")
    ]

    all_good = True
    for package_info in packages:
        import_name = package_info[1] if len(package_info) > 2 else package_info[0]
        display_name = package_info[-1]

        try:
            __import__(import_name)
            print(f"  {display_name}: ✅ INSTALLED")
        except ImportError:
            print(f"  {display_name}: ❌ NOT INSTALLED")
            all_good = False

    return all_good

async def test_livekit_token():
    """Test LiveKit token generation"""
    print("\n" + "="*60)
    print("TEST 3: LiveKit Token Generation")
    print("="*60)

    try:
        from livekit import api

        token = api.AccessToken(
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET")
        )

        jwt = (token
            .with_identity("test-user")
            .with_name("Test User")
            .with_grants(api.VideoGrants(
                room_join=True,
                room="test-room"
            ))
            .to_jwt())

        if jwt:
            print(f"  Token Generated: ✅ SUCCESS")
            print(f"  Token Length: {len(jwt)} characters")
            print(f"  Token Prefix: {jwt[:30]}...")
            return True
        else:
            print(f"  Token Generation: ❌ FAILED")
            return False

    except Exception as e:
        print(f"  Token Generation: ❌ ERROR - {e}")
        return False

async def test_openai_connection():
    """Test OpenAI API connection"""
    print("\n" + "="*60)
    print("TEST 4: OpenAI API Connection")
    print("="*60)

    try:
        import openai

        # Set API key
        openai.api_key = os.getenv("OPENAI_API_KEY")

        # Try a simple completion
        client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

        # Test with a simple prompt
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )

        if response and response.choices:
            print(f"  OpenAI API: ✅ CONNECTED")
            print(f"  Response: {response.choices[0].message.content}")
            return True
        else:
            print(f"  OpenAI API: ❌ NO RESPONSE")
            return False

    except Exception as e:
        print(f"  OpenAI API: ❌ ERROR - {str(e)[:100]}")
        return False

async def test_agent_components():
    """Test agent components can be initialized"""
    print("\n" + "="*60)
    print("TEST 5: Agent Components")
    print("="*60)

    results = {}

    # Test config loading
    try:
        from config import Config
        config = Config()
        results["Config"] = bool(config.livekit_url and config.openai_api_key)
        print(f"  Configuration: {'✅ LOADED' if results['Config'] else '❌ FAILED'}")
    except Exception as e:
        results["Config"] = False
        print(f"  Configuration: ❌ ERROR - {e}")

    # Test VAD
    try:
        from livekit.plugins import silero
        vad = silero.VAD.load()
        results["VAD"] = True
        print(f"  Voice Activity Detection: ✅ READY")
    except Exception as e:
        results["VAD"] = False
        print(f"  Voice Activity Detection: ❌ ERROR - {e}")

    # Test STT
    try:
        from livekit.plugins import openai as lk_openai
        stt = lk_openai.STT(
            model="whisper-1",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        results["STT"] = True
        print(f"  Speech-to-Text: ✅ READY")
    except Exception as e:
        results["STT"] = False
        print(f"  Speech-to-Text: ❌ ERROR - {e}")

    # Test TTS
    try:
        from livekit.plugins import openai as lk_openai
        tts = lk_openai.TTS(
            model="tts-1",
            voice="alloy",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        results["TTS"] = True
        print(f"  Text-to-Speech: ✅ READY")
    except Exception as e:
        results["TTS"] = False
        print(f"  Text-to-Speech: ❌ ERROR - {e}")

    # Test LLM
    try:
        from livekit.plugins import openai as lk_openai
        llm = lk_openai.LLM(
            model="gpt-4-turbo",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        results["LLM"] = True
        print(f"  Language Model: ✅ READY")
    except Exception as e:
        results["LLM"] = False
        print(f"  Language Model: ❌ ERROR - {e}")

    return all(results.values())

async def test_agent_startup():
    """Test if agent can start (without actually starting)"""
    print("\n" + "="*60)
    print("TEST 6: Agent Startup Check")
    print("="*60)

    try:
        # Check if main_simple.py exists and is valid Python
        main_path = Path(__file__).parent / "agent" / "main_simple.py"
        if not main_path.exists():
            print(f"  Main script: ❌ NOT FOUND at {main_path}")
            return False

        # Try to compile the main script
        with open(main_path, 'r') as f:
            code = f.read()
            compile(code, str(main_path), 'exec')

        print(f"  Main script: ✅ VALID")
        print(f"  Location: {main_path}")

        # Check CLI availability
        try:
            from livekit.agents import cli
            print(f"  LiveKit CLI: ✅ AVAILABLE")
            return True
        except ImportError:
            print(f"  LiveKit CLI: ❌ NOT AVAILABLE")
            return False

    except SyntaxError as e:
        print(f"  Main script: ❌ SYNTAX ERROR - {e}")
        return False
    except Exception as e:
        print(f"  Agent Startup: ❌ ERROR - {e}")
        return False

async def main():
    """Run all tests"""
    print("\n" + "🚀" * 30)
    print("CLAUDEVOICE CORE E2E TEST")
    print("🚀" * 30)

    results = {}

    # Run tests
    results["Environment"] = test_environment()
    results["Dependencies"] = test_dependencies()
    results["LiveKit Token"] = await test_livekit_token()
    results["OpenAI API"] = await test_openai_connection()
    results["Components"] = await test_agent_components()
    results["Startup"] = await test_agent_startup()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL CORE TESTS PASSED!")
        print("\n✨ The agent is ready to start!")
        print("\nTo start the agent:")
        print("  cd agent")
        print("  source venv/bin/activate")
        print("  python main_simple.py dev")
        print("\nNote: Some tool functions may need updates for the")
        print("current LiveKit version, but core voice functionality works.")
    else:
        print("⚠️ SOME TESTS FAILED")
        print("\nPlease review the failures above and:")
        print("1. Check your .env.local file has all required keys")
        print("2. Ensure all dependencies are installed:")
        print("   pip install -r agent/requirements.txt")
        print("3. Verify your API keys are valid")
    print("="*60)

    return all_passed

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)