# April v2

FastAPI backend for April v2 AI assistant with multi-provider support and configurable routing.

## Features

- **FastAPI backend** with REST + WebSocket support
- **Config-driven provider system** using `providers.yml`
- **Multiple LLM providers**: OpenAI, DeepSeek, Claude, Grok
- **Routing layer** that respects provider weights and capabilities
- **Pluggable adapters** for:
  - Speech (TTS via ElevenLabs)
  - Image (OpenAI + DeepSeek)
  - Video (Sora/Kling API - placeholder)
- **Core orchestration layer** (April Manager) with:
  - Per-user memory tracking
  - Persona shaping per user
  - Post-system prompts and context management
- **Structured logging** with JSON output
- **Docker support** with docker-compose.yml
- **Unit tests** with pytest

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Configure providers:**
   - Copy `.env.example` to `.env`
   - Add your API keys to the `.env` file
   - Modify `providers.yml` to enable/disable providers and adjust weights

3. **Run the server:**
   ```bash
   python main.py
   ```

4. **Test the API:**
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # Chat endpoint
   curl -X POST http://localhost:8000/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"messages": [{"role": "user", "content": "Hello!"}], "user_id": "test_user"}'
   ```

## API Endpoints

### REST Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/v1/status` - System status and provider information
- `POST /api/v1/chat` - Chat with LLM providers
- `POST /api/v1/draw` - Generate images
- `POST /api/v1/speak` - Text-to-speech synthesis
- `POST /api/v1/users/{user_id}/persona` - Set user persona

### WebSocket

- `WS /ws/{user_id}` - Real-time chat interface

WebSocket message format:
```json
{
  "type": "chat",
  "content": "Your message here"
}
```

## Configuration

### Provider Configuration (providers.yml)

The `providers.yml` file controls which providers are enabled and their weights:

```yaml
providers:
  llm:
    openai:
      enabled: true
      weight: 0.4  # Higher weight = more likely to be selected
      models:
        - name: "gpt-4-turbo-preview"
          max_tokens: 4096
          capabilities: ["text", "function_calling"]
```

### Environment Variables

Key environment variables in `.env`:

```bash
# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
DEEPSEEK_API_KEY=your_deepseek_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# Application settings
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

## Docker Deployment

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **The stack includes:**
   - April v2 API server (port 8000)
   - Loki for logging (port 3100) - optional
   - Grafana for log visualization (port 3000) - optional

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run tests
python -m pytest april/tests/ -v
```

### Code Structure

```
april/
├── api/           # FastAPI endpoints and WebSocket handlers
├── core/          # Core manager and orchestration logic
├── providers/     # Provider implementations (OpenAI, Claude, etc.)
├── config/        # Configuration management
└── tests/         # Unit tests
```

### Adding New Providers

1. Create a new provider class inheriting from the appropriate base class (`LLMProvider`, `ImageProvider`, etc.)
2. Implement required methods (`chat`, `generate`, etc.)
3. Add provider configuration to `providers.yml`
4. Register the provider in the manager's `_create_*_provider` methods

## Architecture

### Core Components

1. **April Manager**: Central orchestrator that manages providers and user interactions
2. **Provider System**: Pluggable adapters for different AI services
3. **Routing Layer**: Weight-based provider selection
4. **Memory System**: Per-user conversation history and context
5. **Persona System**: Customizable AI personalities per user

### Provider Selection

Providers are selected using weighted random selection based on:
- Provider availability (healthy API connection)
- Configured weights in `providers.yml`
- Provider capabilities for the requested task

### User Context

The system maintains per-user:
- **Memory**: Recent conversation history (last 5 interactions by default)
- **Persona**: AI personality/behavior settings
- **Preferences**: User-specific configuration

## Logging

The application uses structured logging with JSON output. Logs include:
- Request/response details
- Provider selection decisions
- Error conditions
- Performance metrics

Optional Loki integration for centralized log collection and Grafana for visualization.

## First Milestone Status

✅ **Completed:**
- FastAPI app with endpoints (`/chat`, `/draw`, `/speak`)
- Config loader for `providers.yml`
- Core Manager that calls provider adapters
- Provider implementations for OpenAI, Claude, DeepSeek, ElevenLabs
- WebSocket support for real-time communication
- Docker configuration
- Unit tests with pytest
- Structured logging
- User memory and persona management

## License

This project is part of the April v2 AI assistant system.
