
# April Core v2

A FastAPI-based AI service orchestration platform with multi-provider support for chat, image generation, and text-to-speech capabilities.

## Features

- **Multi-Provider Support**: OpenAI, DeepSeek, and ElevenLabs integration
- **Capability-Based Routing**: Automatic provider selection based on capabilities and weights
- **Per-User Memory Logging**: Loki integration for centralized logging and user interaction tracking
- **RESTful API**: Clean FastAPI endpoints for chat, draw, speak, and health
- **Configuration-Driven**: YAML-based provider configuration with environment variable substitution
- **Docker Support**: Complete containerization with docker-compose
- **Monitoring**: Grafana dashboard integration for log visualization

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd aprilv2
```

2. Copy environment configuration:
```bash
cp .env.example .env
```

3. Edit `.env` with your API keys:
```bash
OPENAI_API_KEY=your_openai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

4. Start the services:
```bash
docker-compose up -d
```

5. Access the services:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/admin)
- Loki: http://localhost:3100

### Local Development

# AprilV2 API Server

A FastAPI-based API server providing endpoints for chat, image generation, speech synthesis, and health monitoring.

## Features

- **Chat**: Process messages with configurable personas
- **Draw**: Generate images from text prompts  
- **Speak**: Convert text to speech with different voices
- **Health**: Monitor service status

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```


2. Set environment variables:
```bash
export OPENAI_API_KEY=your_key_here
export DEEPSEEK_API_KEY=your_key_here
export ELEVENLABS_API_KEY=your_key_here
```

3. Run the application:
```bash
python -m uvicorn src.main:app --reload
```
=======
2. Run the server:
```bash
python main.py
# or
./run.sh
```

The server will start on `http://localhost:8000`


## API Endpoints

### POST /chat

Chat completion with automatic provider selection.

```json
{
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "max_tokens": 1000,
  "temperature": 0.7
}
```

### POST /draw
Image generation using available providers.

```json
{
  "prompt": "A beautiful sunset over the mountains",
  "size": "1024x1024",
  "quality": "standard",
  "n": 1
}
```

### POST /speak
Text-to-speech conversion.

```json
{
  "text": "Hello, this is a test message",
  "voice": "21m00Tcm4TlvDq8ikWAM",
  "stability": 0.5,
  "similarity_boost": 0.5
}
```

### GET /health
Service health check and provider status.

## Configuration

### Provider Configuration (`config/providers.yml`)

The service uses a YAML configuration file to define providers, their capabilities, and model weights:

```yaml
providers:
  openai:
    enabled: true
    api_key: ${OPENAI_API_KEY}
    base_url: https://api.openai.com/v1
    capabilities:
      - chat
      - draw
    models:
      chat:
        - name: gpt-4
          weight: 100
        - name: gpt-3.5-turbo
          weight: 80
```

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key
- `DEEPSEEK_API_KEY`: DeepSeek API key  
- `ELEVENLABS_API_KEY`: ElevenLabs API key
- `LOKI_URL`: Loki logging endpoint (default: http://localhost:3100)

## Architecture

### Core Components

- **`src/core/manager.py`**: Main orchestration engine handling provider selection and routing
- **`src/core/config.py`**: Configuration management with environment variable substitution
- **`src/core/logging.py`**: Loki integration for per-user memory logging
- **`src/providers/`**: Provider adapters for OpenAI, DeepSeek, and ElevenLabs
- **`src/main.py`**: FastAPI application with REST endpoints

### Provider Selection

The system uses weighted random selection for model choice within providers:
1. Filter providers by capability (chat, draw, speak)
2. Select provider randomly from available options
3. Select model based on configured weights
4. Log all interactions with user ID for memory tracking

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src
```

## Monitoring

### Loki Logging

All user interactions are logged to Loki with structured data:
- User ID
- Endpoint accessed
- Provider and model used
- Request/response data
- Performance metrics

### Grafana Dashboards

Access Grafana at http://localhost:3000 to visualize:
- User interaction patterns
- Provider performance metrics
- Error rates and debugging information
- Usage statistics per endpoint

## Development

### Project Structure

```
aprilv2/
├── src/
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── manager.py         # Provider orchestration
│   │   └── logging.py         # Loki integration
│   ├── providers/
│   │   ├── base.py            # Base provider interface
│   │   ├── openai_provider.py # OpenAI implementation
│   │   ├── deepseek_provider.py # DeepSeek implementation
│   │   └── elevenlabs_provider.py # ElevenLabs implementation
│   └── main.py                # FastAPI application
├── tests/                     # Test suite
├── config/
│   ├── providers.yml          # Provider configuration
│   └── grafana-datasources.yml # Grafana setup
├── docker-compose.yml         # Container orchestration
├── Dockerfile                 # Container definition
└── requirements.txt           # Python dependencies
```

### Adding New Providers

1. Create a new provider class inheriting from `BaseProvider`
2. Implement required methods: `chat()`, `draw()`, `speak()`
3. Add provider configuration to `providers.yml`
4. Register provider in `manager.py`

## License

[Add your license information here]

Process chat messages with specified persona.

**Request:**
```json
{
  "user_id": "u1",
  "message": "Hello",
  "persona": "default"
}
```

**Response:**
```json
{
  "response": "Hello u1! I received your message: 'Hello'. I'm responding as the 'default' persona.",
  "persona": "default",
  "user_id": "u1"
}
```

### POST /draw
Generate images from text prompts.

**Request:**
```json
{
  "prompt": "a cat astronaut",
  "width": 1024,
  "height": 1024
}
```

**Response:**
```json
{
  "image_url": "https://placeholder.com/1024x1024",
  "prompt": "a cat astronaut",
  "width": 1024,
  "height": 1024
}
```

### POST /speak
Convert text to speech.

**Request:**
```json
{
  "text": "Hello",
  "voice": "Rachel"
}
```

**Response:**
```json
{
  "audio_url": "https://audio.example.com/speech/-4038929456969297631.mp3",
  "voice": "Rachel",
  "text": "Hello"
}
```

### GET /health
Check service health status.

**Response:**
```json
{
  "status": "ok"
}
```

## Configuration

### providers.yml
Defines enabled providers, weights, and capabilities for different services (chat, image, speech).

### config.yml  
Defines service options including:
- Server settings (host, port, workers)
- Logging configuration
- Loki integration for log aggregation
- Rate limits and service limits
- CORS settings
- Monitoring options

## API Documentation

When the server is running, interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

The server provides mock responses for all endpoints. In a production environment, these would integrate with actual AI/ML service providers as configured in `providers.yml`.

