# ClaudeVoice Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the ClaudeVoice project using LiveKit's voice AI framework with telephony integration.

## Prerequisites

### Required Accounts
- [ ] LiveKit Cloud account (https://cloud.livekit.io)
- [ ] OpenAI API account (for GPT-4 and Whisper)
- [ ] AssemblyAI account (for STT)
- [ ] Cartesia account (for TTS)
- [ ] Vercel account (for webhook deployment)

### Development Environment
- [ ] Python ≥3.9 with uv package manager
- [ ] Node.js ≥20 with pnpm
- [ ] Docker Desktop
- [ ] LiveKit CLI (`brew install livekit-cli`)
- [ ] Git

## Phase 1: Core Agent Development

### Step 1: Initialize Python Project

```bash
cd agent/
python -m venv venv
source venv/bin/activate
pip install uv
uv pip install livekit-agents[openai,silero,cartesia,assemblyai]
```

### Step 2: Configure Environment

Create `.env.local`:
```env
# LiveKit Configuration
LK_API_KEY=your_api_key
LK_API_SECRET=your_api_secret
LK_URL=wss://your-project.livekit.cloud

# AI Service Keys
OPENAI_API_KEY=your_openai_key
ASSEMBLYAI_API_KEY=your_assemblyai_key
CARTESIA_API_KEY=your_cartesia_key

# Agent Configuration
AGENT_NAME=claudevoice-agent
AGENT_PORT=8080
```

### Step 3: Implement Core Agent

```python
# agent/main.py
import asyncio
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, silero, cartesia, assemblyai

async def entrypoint(ctx: JobContext):
    # Initialize the agent with system instructions
    initial_ctx = llm.ChatContext().append(
        role="system",
        text="""You are Claude, a helpful voice assistant with tool-calling capabilities.
        Keep responses concise and natural. You can:
        - Check weather information
        - Manage calendar appointments
        - Query databases
        - Make API calls
        Always be friendly and professional."""
    )

    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Create the voice pipeline agent
    assistant = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=assemblyai.STT(),
        llm=openai.LLM(model="gpt-4-turbo"),
        tts=cartesia.TTS(),
        chat_ctx=initial_ctx,
    )

    # Register tool functions
    assistant.llm.register_tool(weather_tool)
    assistant.llm.register_tool(calendar_tool)
    assistant.llm.register_tool(database_tool)

    # Start the agent
    assistant.start(ctx.room)

    # Generate initial greeting
    await assistant.say("Hello! I'm Claude, your voice assistant. How can I help you today?")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="claudevoice-agent"
    ))
```

### Step 4: Implement Tool Functions

```python
# agent/tools/weather.py
from livekit.agents import llm
import httpx

@llm.ai_callable()
async def weather_tool(location: str) -> str:
    """Get current weather for a location"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.weatherapi.com/v1/current.json",
            params={"q": location, "key": "YOUR_API_KEY"}
        )
        data = response.json()
        return f"The weather in {location} is {data['current']['condition']['text']} with a temperature of {data['current']['temp_c']}°C"
```

### Step 5: Test with Sandbox

```bash
# Authenticate with LiveKit CLI
lk app auth

# Run the agent in dev mode
python agent/main.py dev

# Access the playground at the provided URL
```

## Phase 2: Telephony Integration

### Step 1: Create Webhook Infrastructure

```typescript
// webhook/app/api/sip/inbound/route.ts
import { NextRequest, NextResponse } from "next/server";
import { AccessToken, RoomServiceClient, AgentClient } from "@livekit/server-sdk";

const lkHost = process.env.LK_URL!;
const lkApiKey = process.env.LK_API_KEY!;
const lkApiSecret = process.env.LK_API_SECRET!;

const roomService = new RoomServiceClient(lkHost, lkApiKey, lkApiSecret);
const agentClient = new AgentClient(lkHost, lkApiKey, lkApiSecret);

export async function POST(req: NextRequest) {
    const body = await req.json();
    const { from, to } = body;

    // Create unique room for this call
    const roomName = `call-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Create the room
    await roomService.createRoom({
        name: roomName,
        metadata: JSON.stringify({
            from_number: from,
            to_number: to,
            call_started: new Date().toISOString()
        })
    });

    // Dispatch agent to the room
    await agentClient.createJob({
        agent_name: "claudevoice-agent",
        room: roomName,
        metadata: JSON.stringify({
            type: "inbound_call",
            from: from,
            to: to
        })
    });

    // Create token for SIP participant
    const at = new AccessToken(lkApiKey, lkApiSecret, {
        identity: `caller-${from}`,
        ttl: '1h',
    });

    at.addGrant({
        room: roomName,
        roomJoin: true,
        canPublish: true,
        canSubscribe: true,
    });

    // Return response for LiveKit SIP
    return NextResponse.json({
        join_room: {
            room: roomName,
            token: at.toJwt(),
            participant_identity: `caller-${from}`,
            participant_name: `Caller from ${from}`,
            participant_metadata: JSON.stringify({
                phone_number: from
            })
        }
    });
}
```

### Step 2: Deploy Webhook

```bash
# Deploy to Vercel
cd webhook/
vercel deploy --prod

# Note the deployment URL
# Example: https://claudevoice-webhook.vercel.app
```

### Step 3: Configure SIP Trunk

1. Navigate to LiveKit Cloud Dashboard
2. Go to SIP section
3. Create new SIP Trunk
4. Configure inbound webhook URL: `https://your-webhook.vercel.app/api/sip/inbound`
5. Purchase phone number
6. Create dispatch rule:

```json
{
  "dispatch_rule": {
    "rule": {
      "dispatchRuleIndividual": {
        "roomPrefix": "call-"
      }
    },
    "roomConfig": {
      "agents": [
        {
          "agentName": "claudevoice-agent"
        }
      ]
    }
  }
}
```

## Phase 3: Production Deployment

### Step 1: Dockerize Agent

```dockerfile
# docker/Dockerfile.agent
FROM python:3.11-slim

WORKDIR /app

COPY agent/requirements.txt .
RUN pip install -r requirements.txt

COPY agent/ .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py", "start"]
```

### Step 2: Deploy to Cloud Run

```bash
# Build and push Docker image
docker build -f docker/Dockerfile.agent -t gcr.io/your-project/claudevoice-agent .
docker push gcr.io/your-project/claudevoice-agent

# Deploy to Cloud Run
gcloud run deploy claudevoice-agent \
  --image gcr.io/your-project/claudevoice-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars-from-file .env.prod
```

### Step 3: Register Agent

1. Go to LiveKit Cloud Dashboard
2. Navigate to Agents tab
3. Click "Register Agent"
4. Provide Cloud Run URL
5. Test with production phone number

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_tools.py
import pytest
from agent.tools.weather import weather_tool

@pytest.mark.asyncio
async def test_weather_tool():
    result = await weather_tool("London")
    assert "weather" in result.lower()
    assert "London" in result
```

### Integration Tests

```python
# tests/integration/test_agent.py
import pytest
from livekit.agents.testing import TestContext
from agent.main import entrypoint

@pytest.mark.asyncio
async def test_agent_initialization():
    ctx = TestContext()
    await entrypoint(ctx)
    assert ctx.room is not None
```

### End-to-End Tests

```bash
# tests/e2e/test_call_flow.sh
#!/bin/bash

# Test inbound call
curl -X POST https://your-webhook.vercel.app/api/sip/inbound \
  -H "Content-Type: application/json" \
  -d '{"from": "+1234567890", "to": "+0987654321"}'

# Verify room creation
lk room list | grep "call-"

# Check agent logs
gcloud logging read "resource.type=cloud_run_revision"
```

## Monitoring & Debugging

### LiveKit Dashboard
- Monitor active rooms
- View participant connections
- Check agent status
- Review call quality metrics

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Use throughout your code
logger.info(f"Processing call from {from_number}")
logger.error(f"Tool execution failed: {error}")
```

### Error Handling

```python
try:
    result = await tool_function(params)
except Exception as e:
    logger.error(f"Tool error: {e}")
    await assistant.say("I encountered an error. Let me try another approach.")
    # Fallback logic
```

## Performance Optimization

### Reduce Latency
1. Use noise cancellation (BVCTelephony)
2. Enable VAD for better turn detection
3. Optimize tool response times
4. Use caching for frequent queries

### Scale Considerations
1. Use Cloud Run autoscaling
2. Implement connection pooling
3. Cache tool responses
4. Monitor and adjust resource limits

## Security Best Practices

1. **Never commit secrets**
   - Use environment variables
   - Implement secret management

2. **Validate inputs**
   - Sanitize phone numbers
   - Validate tool parameters
   - Rate limit API calls

3. **Secure webhooks**
   - Implement webhook signatures
   - Use HTTPS only
   - Validate request origins

4. **Monitor usage**
   - Set up alerts
   - Track API usage
   - Implement cost controls

## Troubleshooting

### Common Issues

1. **Agent not connecting**
   - Check API credentials
   - Verify network connectivity
   - Review agent logs

2. **Poor audio quality**
   - Enable noise cancellation
   - Check network bandwidth
   - Adjust audio settings

3. **Tool failures**
   - Verify API keys
   - Check rate limits
   - Review error logs

4. **SIP issues**
   - Verify trunk configuration
   - Check webhook URL
   - Review dispatch rules

## Conclusion

Following this guide will result in a production-ready voice AI agent with telephony capabilities. Remember to:

1. Test thoroughly in Sandbox before production
2. Monitor performance and costs
3. Implement proper error handling
4. Keep documentation updated

For support, consult:
- LiveKit Documentation: https://docs.livekit.io
- Community Discord: https://livekit.io/discord
- GitHub Issues: https://github.com/livekit/agents-py

---

*Version: 1.0*
*Last Updated: November 2025*