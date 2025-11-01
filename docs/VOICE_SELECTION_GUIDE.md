# OpenAI Voice Selection Guide 🎤

## Overview

ClaudeVoice uses OpenAI's Text-to-Speech (TTS) API, which offers 6 distinct voices and 2 quality models. This guide helps you choose the best configuration for your use case.

## Available Voices

### 🔵 Alloy (Default)
- **Character**: Neutral and balanced
- **Best for**: General purpose, professional calls
- **Gender**: Androgynous
- **Tone**: Clear and articulate

### 🟢 Echo
- **Character**: Warm and engaging
- **Best for**: Customer service, friendly interactions
- **Gender**: Masculine-leaning
- **Tone**: Welcoming and approachable

### 🟡 Fable
- **Character**: Expressive and dynamic
- **Best for**: Storytelling, engaging presentations
- **Gender**: Feminine-leaning
- **Tone**: Animated and enthusiastic

### 🔴 Onyx
- **Character**: Deep and authoritative
- **Best for**: Professional announcements, serious topics
- **Gender**: Masculine
- **Tone**: Commanding and confident

### 🟣 Nova
- **Character**: Friendly and conversational
- **Best for**: Casual interactions, help desk
- **Gender**: Feminine-leaning
- **Tone**: Warm and personable

### ⚪ Shimmer
- **Character**: Soft and pleasant
- **Best for**: Calming interactions, meditation apps
- **Gender**: Feminine
- **Tone**: Gentle and soothing

## Model Selection

### TTS-1 (Standard)
- **Latency**: Lower (~100ms)
- **Quality**: Good
- **Best for**: Real-time phone calls
- **Cost**: Standard pricing

### TTS-1-HD (High Definition)
- **Latency**: Slightly higher (~150ms)
- **Quality**: Excellent
- **Best for**: High-quality applications
- **Cost**: Premium pricing

## Configuration Examples

### For Customer Service
```env
TTS_MODEL=tts-1
TTS_VOICE=nova
TTS_SPEED=1.0
```

### For Professional/Business Calls
```env
TTS_MODEL=tts-1
TTS_VOICE=alloy
TTS_SPEED=1.0
```

### For Authority/Executive Assistant
```env
TTS_MODEL=tts-1-hd
TTS_VOICE=onyx
TTS_SPEED=0.95
```

### For Friendly Support
```env
TTS_MODEL=tts-1
TTS_VOICE=echo
TTS_SPEED=1.05
```

### For Calm/Healthcare
```env
TTS_MODEL=tts-1-hd
TTS_VOICE=shimmer
TTS_SPEED=0.9
```

## Speed Settings

The `TTS_SPEED` parameter controls speech rate:
- **0.25**: Very slow (for accessibility)
- **0.5**: Slow
- **0.75**: Slightly slow
- **1.0**: Normal (default)
- **1.25**: Slightly fast
- **1.5**: Fast
- **2.0**: Very fast
- **4.0**: Maximum speed

## Testing Voices

To test different voices before deploying:

```python
# Quick test script
import openai
from openai import OpenAI

client = OpenAI(api_key="your-key")

voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

for voice in voices:
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input="Hello, this is a test of the voice."
    )

    response.stream_to_file(f"test_{voice}.mp3")
```

## Use Case Recommendations

### Telephony/Phone Calls
- **Model**: `tts-1` (lower latency)
- **Voices**: `alloy`, `nova`, `echo`
- **Speed**: `1.0`

### Virtual Assistant
- **Model**: `tts-1`
- **Voices**: `nova`, `alloy`
- **Speed**: `1.0-1.1`

### Professional Services
- **Model**: `tts-1-hd`
- **Voices**: `onyx`, `alloy`
- **Speed**: `0.95-1.0`

### Healthcare/Wellness
- **Model**: `tts-1-hd`
- **Voices**: `shimmer`, `nova`
- **Speed**: `0.9-1.0`

## Language Support

While the voices are optimized for English, they support multiple languages:

```env
# For multilingual support
STT_LANGUAGE=auto  # Auto-detect language
TTS_VOICE=alloy    # Most neutral for multiple languages
```

## Performance Considerations

1. **Latency**: For phone calls, use `tts-1` model
2. **Quality**: For recorded messages, use `tts-1-hd`
3. **Cost**: `tts-1` is more cost-effective for high volume
4. **Caching**: Consider caching common phrases

## Switching Voices Dynamically

You can change voices during runtime by modifying environment variables and restarting the agent:

```bash
# Update voice
export TTS_VOICE=nova

# Restart agent
python agent/main.py start
```

## Troubleshooting

### Voice sounds robotic
- Try `tts-1-hd` model
- Adjust speed to 0.95
- Consider `echo` or `nova` voices

### Too fast/slow
- Adjust `TTS_SPEED`
- Test with values between 0.8-1.2

### Wrong tone for use case
- Review voice descriptions above
- Test multiple voices
- Consider user feedback

## Cost Optimization

- Use `tts-1` for real-time calls
- Cache frequently used phrases
- Monitor usage via OpenAI dashboard
- Set appropriate `LLM_MAX_TOKENS` to control response length

---

For more information, see [OpenAI TTS Documentation](https://platform.openai.com/docs/guides/text-to-speech)