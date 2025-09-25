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

2. Run the server:
```bash
python main.py
# or
./run.sh
```

The server will start on `http://localhost:8000`

## API Endpoints

### POST /chat
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
