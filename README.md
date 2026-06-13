# GigGuard

Agentic AI Advocate for India's Gig Workers.

## Setup

1. Clone the repo
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in your keys
6. Run: `python main.py`

## Endpoints

- `GET /health` — Health check

## Team

- Person 1 (Anand) — Backend Core
- Person 2 — Agents (Researcher, Drafter)
- Person 3 — Twilio Integration
- Person 4 — Database Layer

## Branch Strategy

- `feature/backend-core` — Person 1's work
- `dev` — integration branch
- `main` — stable only
