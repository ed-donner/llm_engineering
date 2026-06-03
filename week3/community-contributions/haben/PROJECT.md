# Real-Time Call Center AI

A real-time AI system for live call transcription and analysis, demonstrating distributed architecture and streaming LLM patterns.

## Overview

**Real-Time Call Center AI** processes live audio conversations through a distributed pipeline, delivering real-time transcription, sentiment analysis, intent detection, and actionable insights.

Built during the **Andela LLM Engineering Bootcamp**, this project demonstrates enterprise-grade architecture patterns for real-time AI applications, including horizontal scalability, multi-LLM provider support, and production deployment configurations.

## Key Capabilities

- **Real-Time Audio Processing**: Browser-based capture with 200ms chunking and WebSocket streaming
- **Live Transcription**: Streaming ASR using Faster-Whisper with speaker diarization
- **Intelligent Analysis**: Multi-LLM powered intent detection, sentiment analysis, and dynamic summarization
- **Actionable Intelligence**: Automatic extraction of action items, complaint classification, and key topic identification
- **Scalable Architecture**: Redis Streams for asynchronous message queuing and horizontal worker scaling
- **Production Ready**: Complete Docker Compose setup with PostgreSQL persistence and comprehensive error handling

## Architecture

Microservices architecture with FastAPI, Redis Streams, and PostgreSQL:

```
Frontend (React) → API Gateway (FastAPI) → Redis Streams → 
Streaming Processor (ASR/VAD) → PostgreSQL → LLM Processor → Real-Time Updates
```

## Technology Stack

**Backend**: FastAPI, Redis Streams, PostgreSQL, SQLAlchemy  
**Frontend**: React, Vite, WebSocket API  
**AI/ML**: Faster-Whisper (ASR), Multi-LLM (Ollama, Hugging Face, OpenRouter, OpenAI)  
**Infrastructure**: Docker, Docker Compose, Nginx

## Why Separate Repository?

Because the project includes 44 files (~7,000 LOC), Docker infrastructure, and a full frontend, it is maintained separately to keep the main bootcamp repository lightweight and focused on core curriculum content.

**Note:** This PR contains a summary only; the full implementation is maintained in the repository linked below.

## Implementation Repository

The complete source code, detailed documentation, setup instructions, and deployment guides are available in:

**🔗 [realtime-call-center-ai](https://github.com/habeneyasu/realtime-call-center-ai)**

The repository includes:
- Complete source code with production-ready error handling
- Comprehensive README with architecture diagrams
- Docker Compose configuration for one-command deployment
- Environment configuration templates
- API documentation and integration examples
- Multi-LLM provider setup guides (Ollama, Hugging Face, OpenRouter, OpenAI)
