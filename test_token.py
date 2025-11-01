#!/usr/bin/env python3
"""
Test token generation for ClaudeVoice
This script demonstrates how tokens are generated for LiveKit
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
import sys

# Try to find .env.local
if os.path.exists('.env.local'):
    load_dotenv('.env.local')
elif os.path.exists('../.env.local'):
    load_dotenv('../.env.local')
else:
    print("Warning: .env.local not found")

try:
    from livekit import api
except ImportError:
    print("Installing livekit-api package...")
    os.system("pip install livekit-api")
    from livekit import api


def generate_test_token(
    room_name: str = "test-room",
    identity: str = "test-user",
    ttl_hours: int = 1
) -> str:
    """
    Generate a test token for LiveKit

    Args:
        room_name: Name of the room to join
        identity: Unique identifier for the participant
        ttl_hours: Token lifetime in hours

    Returns:
        JWT token string
    """

    # Get credentials from environment
    api_key = os.getenv('LK_API_KEY') or os.getenv('LIVEKIT_API_KEY')
    api_secret = os.getenv('LK_API_SECRET') or os.getenv('LIVEKIT_API_SECRET')

    if not api_key or not api_secret:
        raise ValueError("Missing LiveKit API credentials in environment")

    # Create access token (updated API)
    token = api.AccessToken(
        api_key,
        api_secret
    )

    # Set identity and metadata
    token.identity = identity
    token.ttl = timedelta(hours=ttl_hours)
    token.metadata = f'{{"generated_at": "{datetime.now().isoformat()}"}}'

    # Add grants (permissions)
    grant = api.VideoGrant()
    grant.room = room_name
    grant.room_join = True
    grant.can_publish = True
    grant.can_subscribe = True
    grant.can_publish_data = True

    token.add_grant(grant)

    return token.to_jwt()


def decode_token(token: str) -> dict:
    """
    Decode and display token contents (for debugging)

    Args:
        token: JWT token string

    Returns:
        Decoded token payload
    """
    import base64
    import json

    # JWT has 3 parts: header.payload.signature
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")

    # Decode payload (add padding if needed)
    payload = parts[1]
    payload += '=' * (4 - len(payload) % 4)  # Add padding

    decoded = base64.b64decode(payload)
    return json.loads(decoded)


def test_webhook_token():
    """Simulate token generation as done in the webhook"""

    # Simulate incoming phone call
    phone_number = "+1234567890"
    room_name = f"call-{datetime.now().timestamp():.0f}-test"

    # Generate caller token
    token = generate_test_token(
        room_name=room_name,
        identity=f"caller-{phone_number.replace('+', '')}",
        ttl_hours=1
    )

    print(f"📞 Phone Caller Token Generated:")
    print(f"  Room: {room_name}")
    print(f"  Identity: caller-{phone_number.replace('+', '')}")
    print(f"  Token (first 50 chars): {token[:50]}...")

    return token, room_name


def test_agent_connection():
    """Test agent connection (normally handled by LiveKit CLI)"""

    # Agent would use these credentials automatically
    api_key = os.getenv('LK_API_KEY')
    url = os.getenv('LK_URL')

    print(f"\n🤖 Agent Connection Info:")
    print(f"  URL: {url}")
    print(f"  API Key: {api_key[:20]}..." if api_key else "  API Key: Not found")
    print(f"  Note: Agent tokens are generated automatically by LiveKit CLI")


def main():
    """Run token generation tests"""

    print("=" * 50)
    print("🔐 ClaudeVoice Token Generation Test")
    print("=" * 50)

    # Test 1: Generate a basic test token
    print("\n1️⃣ Basic Test Token:")
    try:
        token = generate_test_token()
        print(f"  ✅ Token generated: {token[:50]}...")

        # Decode and show contents
        payload = decode_token(token)
        print(f"  📋 Token expires: {datetime.fromtimestamp(payload.get('exp', 0))}")
        print(f"  👤 Identity: {payload.get('sub')}")
        print(f"  🏠 Room access: {payload.get('video', {}).get('room', 'N/A')}")

    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Test 2: Simulate webhook token
    print("\n2️⃣ Webhook Token Simulation:")
    try:
        token, room = test_webhook_token()

        # Show how to use the token
        print(f"\n  To join this room:")
        print(f"    Room: {room}")
        print(f"    Token: Use the generated token")
        print(f"    URL: {os.getenv('LK_URL')}")

    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Test 3: Show agent info
    test_agent_connection()

    # Test 4: Validate permissions
    print("\n3️⃣ Token Permissions:")
    if 'token' in locals():
        payload = decode_token(token)
        grants = payload.get('video', {})

        print(f"  ✅ Can Join: {grants.get('roomJoin', False)}")
        print(f"  ✅ Can Publish Audio: {grants.get('canPublish', False)}")
        print(f"  ✅ Can Subscribe: {grants.get('canSubscribe', False)}")
        print(f"  ✅ Can Send Data: {grants.get('canPublishData', False)}")

    print("\n" + "=" * 50)
    print("✅ Token generation test complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()