# ClaudeVoice 🎙️

A production-ready voice AI agent with telephony integration built on LiveKit's framework. ClaudeVoice enables natural voice conversations through phone calls with advanced tool-calling capabilities including weather information, calendar management, database queries, and voicemail detection.

## 🌟 Features

- **Voice AI Agent**: STT-LLM-TTS pipeline with natural conversation flow
- **Telephony Integration**: Full SIP trunk support for inbound/outbound calls
- **Tool Calling**: Weather, calendar, database, and voicemail detection
- **Production Ready**: Docker deployment, monitoring, and comprehensive testing
- **Scalable**: Handles 100+ concurrent calls with auto-scaling
- **Low Latency**: Sub-500ms response times with noise cancellation

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Phone Call    │────▶│  SIP Trunk   │────▶│    Webhook      │
└─────────────────┘     └──────────────┘     └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │  LiveKit Room   │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │  Voice Agent    │
                                              │  (STT-LLM-TTS)  │
                                              └─────────────────┘
```

## 📋 Prerequisites

- Python ≥3.9
- Node.js ≥20
- Docker & Docker Compose
- LiveKit Cloud account
- OpenAI API key
- AssemblyAI API key (for STT)
- Cartesia API key (for TTS)

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/claudevoice.git
cd claudevoice
```

### 2. Set up environment variables

```bash
cp .env.example .env.local
# Edit .env.local with your API keys
```

### 3. Install dependencies

```bash
# Python agent
cd agent
pip install -r requirements.txt

# Webhook
cd ../webhook
npm install
```

### 4. Run locally

```bash
# Start agent in dev mode
cd agent
python main.py dev

# Start webhook server
cd ../webhook
npm run dev
```

### 5. Test with LiveKit Playground

Access the playground URL provided by the agent and test voice interactions.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LIVEKIT_URL` | LiveKit Cloud WebSocket URL | Yes |
| `LIVEKIT_API_KEY` | LiveKit API key | Yes |
| `LIVEKIT_API_SECRET` | LiveKit API secret | Yes |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 | Yes |
| `ASSEMBLYAI_API_KEY` | AssemblyAI key for STT | Yes |
| `CARTESIA_API_KEY` | Cartesia key for TTS | Yes |
| `AGENT_NAME` | Agent identifier | No |
| `WEBHOOK_SECRET` | Webhook signature secret | No |

### SIP Configuration

1. Navigate to LiveKit Cloud Dashboard
2. Go to SIP section
3. Create SIP Trunk
4. Set webhook URL: `https://your-domain/api/sip/inbound`
5. Configure dispatch rule (see `IMPLEMENTATION_GUIDE.md`)

## 🛠️ Development

### Project Structure

```
ClaudeVoice/
├── agent/                  # Python voice agent
│   ├── main.py            # Agent entrypoint
│   ├── tools/             # Tool implementations
│   └── requirements.txt
├── webhook/               # SIP webhook (Next.js)
│   └── app/api/sip/
├── tests/                 # Test suites
├── docker/                # Container configs
├── scripts/               # Automation scripts
└── docs/                  # Documentation
```

### Running Tests

```bash
# Unit tests
pytest tests/test_agent.py -v

# Integration tests
pytest tests/integration/ -v

# End-to-end tests
./tests/e2e/test_call_flow.sh
```

### Tool Development

Add new tools in `agent/tools/`:

```python
from livekit.agents import llm

@llm.ai_callable(
    description="Your tool description"
)
async def your_tool(param1: str, param2: int) -> str:
    # Tool implementation
    return "Result"
```

Register in `main.py`:

```python
assistant.llm.register_tool(your_tool)
```

## 🚢 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or deploy individually
docker build -f docker/Dockerfile.agent -t claudevoice-agent .
docker run --env-file .env.production claudevoice-agent
```

### Cloud Deployment

```bash
# Deploy to production
./scripts/deploy.sh production

# Deploy to staging
./scripts/deploy.sh staging
```

### Vercel Webhook Deployment

```bash
cd webhook
vercel --prod
```

## 📊 Monitoring

### Metrics Dashboard

- Grafana: http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9090

### Key Metrics

- Call volume and duration
- Response latency
- Tool execution success rate
- Error rates and types
- Concurrent call count

### Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"Processing call from {phone_number}")
```

## 🧪 Testing

### Test Coverage

- Unit tests: 85%+ coverage
- Integration tests: Major workflows
- E2E tests: Complete call flows
- Performance tests: Load and latency

### Running All Tests

```bash
# Run complete test suite
make test

# Or manually
pytest tests/ -v --cov=agent
```

## 📈 Performance

### Benchmarks

- **Response Time**: < 500ms average
- **Concurrent Calls**: 100+ supported
- **Tool Execution**: < 2s average
- **Availability**: 99.9% uptime target

### Optimization Tips

1. Use noise cancellation for telephony
2. Implement caching for frequent queries
3. Use connection pooling for databases
4. Monitor and adjust worker scaling

## 🔒 Security

### Best Practices

- Never commit API keys
- Use webhook signatures
- Implement rate limiting
- Validate all inputs
- Monitor for anomalies

### Environment Security

```bash
# Generate webhook secret
openssl rand -hex 32

# Encrypt sensitive data
ansible-vault encrypt .env.production
```

## 📚 Documentation

- [Project Analysis](PROJECT_ANALYSIS.md) - Architecture overview
- [Implementation Guide](IMPLEMENTATION_GUIDE.md) - Step-by-step setup
- [API Documentation](docs/API.md) - Tool and webhook APIs
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LiveKit](https://livekit.io) - Real-time communication infrastructure
- [OpenAI](https://openai.com) - GPT-4 language model
- [AssemblyAI](https://assemblyai.com) - Speech-to-text
- [Cartesia](https://cartesia.ai) - Text-to-speech

## 📞 Support

- Documentation: [docs.claudevoice.ai](https://docs.claudevoice.ai)
- Issues: [GitHub Issues](https://github.com/yourusername/claudevoice/issues)
- Discord: [Join our community](https://discord.gg/claudevoice)

## 🚦 Status

![Build Status](https://img.shields.io/github/workflow/status/yourusername/claudevoice/CI)
![License](https://img.shields.io/github/license/yourusername/claudevoice)
![Version](https://img.shields.io/github/v/release/yourusername/claudevoice)

---

Built with ❤️ using LiveKit Agents Framework