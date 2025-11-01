# ClaudeVoice Browser Testing Guide

## Prerequisites Verified ✅

Before browser testing, ensure these are complete (all verified):
- ✅ Environment variables loaded from `.env.local`
- ✅ All dependencies installed
- ✅ Core E2E tests passed
- ✅ Agent starts successfully

## Quick Start Testing

### Step 1: Start the Agent

```bash
cd /Volumes/Storage/Development/ClaudeVoice/agent
source venv/bin/activate
python main_simple.py dev
```

You should see:
```
✅ Loaded environment from: /Volumes/Storage/Development/ClaudeVoice/.env.local
INFO - Starting ClaudeVoice agent: claudevoice-agent
INFO - registered worker {"id": "AW_xxxxx", "url": "wss://sage-0fvpzpd7.livekit.cloud"}
```

### Step 2: Access LiveKit Playground

1. Open your browser
2. Navigate to: **https://cloud.livekit.io**
3. Sign in with your LiveKit Cloud account
4. Go to your project: **sage-0fvpzpd7**
5. Click on **"Playground"** in the left sidebar

### Step 3: Create a Test Room

In the LiveKit Playground:

1. **Room Settings:**
   - Room Name: `test-room` (or leave auto-generated)
   - Click "Join Room"

2. **Permissions:**
   - Allow microphone access when prompted
   - Allow camera access (optional)

### Step 4: Test Voice Interactions

## Test Scenarios

### Basic Voice Test
1. **Say:** "Hello, can you hear me?"
2. **Expected:** Agent responds with greeting
3. **Verify:** Clear audio output, natural voice

### Weather Test (if tools are working)
1. **Say:** "What's the weather in San Francisco?"
2. **Expected:** Agent provides weather information
3. **Verify:** Tool execution and response

### Calendar Test (if tools are working)
1. **Say:** "Check my calendar for tomorrow"
2. **Expected:** Agent checks availability
3. **Verify:** Calendar tool functionality

### Conversation Test
1. **Say:** "Tell me a joke"
2. **Wait for response**
3. **Say:** "Tell me another one"
4. **Verify:** Context maintained between turns

### Interruption Test
1. **Say:** "Can you count to ten slowly?"
2. **Interrupt** at number 3-4
3. **Say:** "Actually, tell me about yourself"
4. **Verify:** Agent stops and responds to new request

## Browser Console Monitoring

Open Developer Tools (F12) and monitor:

1. **Network Tab:**
   - WebSocket connection to LiveKit
   - Should show active `wss://` connection

2. **Console Tab:**
   - Look for any errors
   - Monitor LiveKit events

## Expected Behaviors

### ✅ Working Correctly:
- Agent joins room immediately
- Responds within 1-2 seconds
- Clear audio output
- Natural conversation flow
- Interruption handling

### ⚠️ Known Limitations:
- Tool functions may error (decorator issue)
- No visual feedback for processing
- Playground URL not shown in console

## Troubleshooting

### Agent Not Responding

1. **Check agent console** for errors
2. **Verify room name** matches
3. **Restart agent** with:
```bash
# Kill existing process
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Restart
python main_simple.py dev
```

### Audio Issues

1. **Check browser permissions**
2. **Verify microphone** is not muted
3. **Test with different browser** (Chrome recommended)

### Connection Issues

1. **Verify credentials** in `.env.local`
2. **Check network** connectivity
3. **Validate LiveKit project** status

## Advanced Testing

### Test with Multiple Participants

1. Open multiple browser tabs
2. Join same room with different identities
3. Test agent behavior with multiple speakers

### Test Phone Integration (Future)

Once webhook is deployed:
1. Configure SIP trunk in LiveKit Cloud
2. Call the assigned phone number
3. Test telephony-specific features

## Performance Metrics to Monitor

- **Response Latency:** Should be < 2 seconds
- **Audio Quality:** Clear, no distortion
- **Interruption Handling:** < 500ms to stop
- **Memory Usage:** Monitor agent process
- **CPU Usage:** Should stay < 50%

## Testing Checklist

- [ ] Agent starts without errors
- [ ] Connects to LiveKit Cloud
- [ ] Joins test room
- [ ] Responds to voice input
- [ ] Audio output is clear
- [ ] Can handle interruptions
- [ ] Maintains conversation context
- [ ] Gracefully handles errors

## Recording Test Sessions

To record sessions for review:
1. Use browser recording extensions
2. Or use OBS Studio for screen/audio capture
3. Save recordings for debugging

## Next Steps After Testing

1. **If all tests pass:** Deploy to production
2. **If tools fail:** Fix decorator compatibility
3. **If audio issues:** Adjust VAD/audio settings
4. **If performance issues:** Profile and optimize

## Support Resources

- LiveKit Documentation: https://docs.livekit.io
- OpenAI API Docs: https://platform.openai.com/docs
- Project Issues: Check GitHub repository

---

## Quick Test Commands

```bash
# Run core tests first
python e2e_test_core.py

# Start agent for browser testing
cd agent && source venv/bin/activate && python main_simple.py dev

# Monitor logs
tail -f agent.log  # if logging to file

# Check process
ps aux | grep main_simple

# Kill agent
pkill -f main_simple
```

## Success Criteria

Browser testing is successful when:
1. ✅ Agent responds to voice consistently
2. ✅ Audio quality is acceptable
3. ✅ Latency is under 2 seconds
4. ✅ No critical errors in logs
5. ✅ Can maintain 5+ minute conversation

---

**Note:** The agent is currently verified working with core voice functionality. Tool functions may need updates for full feature compatibility.