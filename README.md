# Dotson Super AI

## Mission

Dotson Super AI is the flagship project of Dotson Labs.

The objective is to build a next-generation AI platform that intelligently combines the strongest capabilities of today's leading AI systems into one unified assistant. Rather than being another chatbot, Dotson Super AI is designed to reason, plan, remember, create, research, automate tasks, and continually improve through a modular architecture.

## Core Principles

- Intelligence before complexity
- Privacy by design
- Modular architecture
- Long-term memory
- Multi-model reasoning
- Local-first capabilities when possible
- Extensible plugin and tool ecosystem

## Planned Components

- Conversation Engine
- Memory System
- Reasoning Engine
- Model Router
- Tool & Plugin Framework
- Voice Interface
- Image & Video Generation
- Research Engine
- Automation System
- Developer Framework

## Status

Project officially restarted on August 10, 2026.

This repository will serve as the permanent home of Dotson Super AI and its development.

## Run ODB Shady 6.9

For Render, use the repository Dockerfile with a blank Root Directory and set `GROQ_API_KEY` in the server environment. `GROQ_MODEL` optionally overrides the existing model. The container builds and serves the chat interface and API on one origin, using Render's `PORT`. `/health` reports whether the provider key is configured; it does not verify provider quota.

For separate frontend hosting, set `VITE_API_URL` to the backend's HTTPS URL before building. For local work, run uvicorn from `backend`, and use `VITE_API_URL=http://localhost:8000` with the Vite development server.

Chats use a random session per browser tab. New chat clears its server history. Memory is still held in RAM and is lost when the service restarts. The current functional engine is Groq text chat; role descriptions and capability labels do not implement authentication, billing, web browsing, voice, or image generation. These remain separate development work.

Validation: `python -m pytest tests -q` with backend requirements and pytest installed; `cd frontend && npm ci && npm run build`.
