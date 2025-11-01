# Token Architecture in ClaudeVoice 🔐

## Overview

LiveKit uses JWT (JSON Web Tokens) for authentication and authorization. Every participant in a LiveKit room needs a valid token to join and interact.

## Token Flow Diagram

```
Phone Call → SIP Trunk → Webhook → Generate Token → Join Room
                              ↓
                         Agent Dispatch
                              ↓
                    Agent Auto-Token → Join Room
```

## Token Components

### 1. Access Token Structure

```javascript
{
  // Header
  "alg": "HS256",
  "typ": "JWT",

  // Payload
  "exp": 1699999999,        // Expiration time
  "iss": "API2A6FUFEXTBGy", // API Key (issuer)
  "nbf": 1699996399,        // Not before
  "sub": "caller-1234567890", // Subject (identity)
  "video": {
    "room": "call-123456-abc",
    "roomJoin": true,
    "canPublish": true,
    "canSubscribe": true
  },
  "metadata": "{\"phone_number\":\"+1234567890\"}",
  "name": "Caller from +1 (234) 567-890"
}
```

### 2. Token Generation Methods

#### A. Manual Generation (Webhook)

```typescript
import { AccessToken } from 'livekit-server-sdk';

function generateToken(
  roomName: string,
  identity: string,
  metadata?: any
): string {
  const token = new AccessToken(
    process.env.LK_API_KEY,
    process.env.LK_API_SECRET,
    {
      identity: identity,
      ttl: 3600, // 1 hour
      metadata: JSON.stringify(metadata)
    }
  );

  token.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
    canPublishData: true
  });

  return token.toJwt();
}
```

#### B. Automatic Generation (Agent)

When running the agent with `python main.py dev`, LiveKit CLI automatically:
1. Uses API credentials from environment
2. Generates appropriate tokens for the agent
3. Manages token refresh if needed

## Token Security

### Best Practices

1. **Never expose API Secret**
   - Only generate tokens server-side
   - Never send API secret to clients

2. **Use appropriate TTL**
   ```typescript
   ttl: 3600  // 1 hour for calls
   ttl: 300   // 5 minutes for short interactions
   ```

3. **Limit permissions**
   ```typescript
   // Minimal permissions for listen-only
   token.addGrant({
     room: roomName,
     roomJoin: true,
     canSubscribe: true  // No publish
   });
   ```

4. **Include metadata**
   ```typescript
   metadata: JSON.stringify({
     user_id: userId,
     role: 'caller',
     timestamp: Date.now()
   })
   ```

## Token Validation

LiveKit validates tokens by:
1. Verifying JWT signature with API secret
2. Checking expiration time
3. Validating room permissions
4. Ensuring identity uniqueness in room

## Token Permissions

### Available Grants

| Permission | Description | Use Case |
|------------|-------------|----------|
| `roomJoin` | Can join the room | Always required |
| `canPublish` | Can send audio/video | Speakers/callers |
| `canSubscribe` | Can receive audio/video | Listeners |
| `canPublishData` | Can send data messages | Interactive features |
| `roomAdmin` | Can manage room | Moderators |
| `roomRecord` | Can record room | Recording bots |
| `ingressAdmin` | Can manage ingress | Stream management |

## Implementation in ClaudeVoice

### 1. SIP Webhook Token

Located in: `/webhook/app/api/sip/inbound/route.ts`

```typescript
// Generate token for phone caller
const token = new AccessToken(
  env.LK_API_KEY,
  env.LK_API_SECRET,
  {
    identity: `caller-${phoneNumber}`,
    ttl: 3600,
    metadata: JSON.stringify({
      phone_number: from,
      call_id: callId
    })
  }
);

token.addGrant({
  room: roomName,
  roomJoin: true,
  canPublish: true,     // Caller can speak
  canSubscribe: true,   // Caller can hear agent
  canPublishData: true  // For DTMF tones
});
```

### 2. Agent Token (Automatic)

The agent uses LiveKit CLI which handles tokens automatically:

```python
# In main_simple.py
async def entrypoint(ctx: JobContext):
    # Token is already handled by LiveKit CLI
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
```

### 3. Testing Token Generation

```bash
# Test token generation
curl -X POST http://localhost:3000/api/sip/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "from": "+1234567890",
    "to": "+0987654321"
  }' | jq '.join_room.token'
```

## Token Debugging

### Common Issues

1. **"Invalid token" error**
   - Check API key/secret match
   - Verify token hasn't expired
   - Ensure room name matches

2. **"Permission denied" error**
   - Check grant permissions
   - Verify canPublish/canSubscribe

3. **"Token expired" error**
   - Increase TTL value
   - Implement token refresh

### Debug Token Contents

```javascript
// Decode JWT to inspect
function decodeToken(token) {
  const parts = token.split('.');
  const payload = JSON.parse(
    Buffer.from(parts[1], 'base64').toString()
  );
  console.log('Token payload:', payload);
}
```

## Token Refresh

For long-running sessions:

```typescript
async function refreshToken(
  oldToken: string,
  roomName: string
): Promise<string> {
  // Decode old token to get identity
  const decoded = jwt.decode(oldToken);

  // Generate new token with same identity
  return generateToken(
    roomName,
    decoded.sub,
    decoded.metadata
  );
}
```

## Security Considerations

### Do's ✅
- Generate tokens server-side only
- Use HTTPS for token transmission
- Set appropriate expiration times
- Include identifying metadata
- Validate webhook signatures

### Don'ts ❌
- Never expose API secret in client code
- Don't use long-lived tokens (>24h)
- Avoid reusing tokens across sessions
- Don't log full token contents
- Never commit tokens to git

## Testing Tools

### Generate Test Token

```python
# Python script to generate test token
from livekit import api

token = api.AccessToken(
    'API2A6FUFEXTBGy',  # Your API key
    'your-secret',       # Your API secret
    identity='test-user',
    ttl=3600
)

token.add_grant(api.VideoGrant(
    room='test-room',
    room_join=True,
    can_publish=True,
    can_subscribe=True
))

print(token.to_jwt())
```

### Validate Token

```bash
# Validate token structure
echo $TOKEN | jwt decode -

# Or using LiveKit CLI
lk token validate --api-key YOUR_KEY --api-secret YOUR_SECRET $TOKEN
```

## Summary

ClaudeVoice handles tokens in two ways:
1. **Explicit generation** in the webhook for phone callers
2. **Automatic handling** by LiveKit CLI for the agent

This dual approach ensures secure, authenticated communication between all participants while maintaining simplicity in the agent code.