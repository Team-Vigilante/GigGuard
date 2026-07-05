# GigGuard 🛡️
### The Agentic AI Advocate for India's Gig Workers

> *"Gig workers build the foundation of our delivery economy. It's time AI built the foundation for their rights."*

Built at **HackArena 2.0** | Powered by LangGraph, Claude API, Groq, Gemini, and a deep belief that every worker deserves a fair shot at justice.

---

## The Problem

India's 12 million gig workers — delivery drivers, ride-share operators, on-demand service providers — are one algorithmic decision away from financial ruin. Platforms silently deactivate accounts, withhold wages, and impose penalties with zero explanation and zero recourse.

- **83–87%** of gig workers face unexplained account deactivations
- **<1%** successfully appeal their deactivation
- **₹8,000–₹15,000** in lost wages per deactivation event
- **25–30** deactivation cases per week in Telangana alone
- Workers receive no notice, no reason, and no path to appeal

The Code on Social Security 2020 and the new Social Security Rules (May 2026) grant workers real legal rights — but 95% of workers don't know these rights exist, and even fewer know how to use them.

---

## The Solution

GigGuard is a **multilingual, autonomous, multi-agent AI system** that stands on the worker's side. It is not a chatbot. It is an agent that detects, reasons, acts, and persists.

A worker sends a WhatsApp message. GigGuard handles everything else:

1. **Parses** the complaint — extracts structured case data from screenshots or text using Claude Vision / Gemini
2. **Researches** the legal basis — queries platform terms of service and Indian labour law via ChromaDB RAG
3. **Drafts** a formal grievance — generates a legally-sound letter in Hindi and English with proper citations
4. **Files** the complaint — routes to the correct channel (platform portal → Labour Department → Social Security Board)
5. **Tracks** the case — auto-escalates if no response in 7 days, follows up until resolved

**Total worker effort: approve three steps on WhatsApp.**

---

## Architecture

```
Worker (WhatsApp)
        ↓
Twilio WhatsApp API
        ↓
FastAPI Backend (POST /webhook/whatsapp)
        ↓
LangGraph Orchestration
        ↓
┌─────────────────────────────────────────────┐
│  Agent 1 — Parser                           │
│  Gemini Vision OCR + Groq text extraction   │
│  Multilingual: Hindi, Tamil, Kannada, EN    │
└─────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────┐
│  Agent 2 — Legal Researcher                 │
│  ChromaDB RAG over platform ToS + labour law│
│  Case strength: STRONG / MODERATE / WEAK    │
└─────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────┐
│  Agent 3 — Drafter                          │
│  Formal grievance in Hindi + English        │
│  Citations strictly from retrieved context  │
└─────────────────────────────────────────────┘
        ↓
  [Worker Reviews & Approves via WhatsApp]
        ↓
┌─────────────────────────────────────────────┐
│  Agent 4 — Navigator                        │
│  Files to correct channel                   │
│  Tracks status + auto-escalates             │
└─────────────────────────────────────────────┘
        ↓
WhatsApp updates to worker (every 7 days or on status change)
```

### Escalation Tiers

| Tier | Channel | Response Window |
|------|---------|----------------|
| 1 | Platform Grievance Officer | 7 days |
| 2 | State Labour Department | 30 days |
| 3 | National Social Security Board | 45 days |
| 4 | Consumer Protection Authority | 60 days |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | FastAPI (Python 3.12) |
| Agent Orchestration | LangGraph 0.2+ |
| Primary LLM (Text) | Groq — LLaMA 3.3 70B |
| Vision / OCR | Google Gemini 1.5 Flash |
| Fallback LLM | Anthropic Claude API |
| Vector Database | ChromaDB |
| Relational Database | SQLite (→ PostgreSQL in production) |
| WhatsApp Integration | Twilio WhatsApp Business API |
| Deployment | Render |
| Version Control | GitHub |

---

## Team

| Person | Role | Branch |
|--------|------|--------|
| Anand Kashyap | Backend Core — FastAPI, Twilio Webhook, LangGraph Pipeline, Parser Agent, Dashboard API, Deployment | `feature/backend-core` |
| Rudra Pratap | AI Agents — Legal Researcher (RAG), Drafter (Multilingual), Prompt Engineering | `feature/ai-agents` |
| Zaid Ali | Twilio Integration — WhatsApp sandbox, message routing, media handling | [branch] |
| Prashasti Shrivastava | Database + Navigator + Dashboard — SQLite schema, Agent 4, frontend dashboard | `feature/knowledge-base` |

---

## Repository Structure

```
gigguard/
├── app/
│   ├── agents/
│   │   ├── state.py              # GigGuardState TypedDict (shared schema)
│   │   ├── graph.py              # LangGraph compiled graph
│   │   ├── parser.py             # Agent 1 — Parser (Gemini Vision + Groq)
│   │   ├── researcher_node.py    # Agent 2 — Legal Researcher (ChromaDB RAG)
│   │   ├── drafter_node.py       # Agent 3 — Drafter (multilingual letters)
│   │   ├── navigator.py          # Agent 4 — Navigator (filing + escalation)
│   │   └── chromadb_query.py     # ChromaDB query utilities
│   ├── api/
│   │   ├── health.py             # GET /health
│   │   ├── webhook.py            # POST /webhook/whatsapp
│   │   └── dashboard.py          # GET /dashboard/{case_id}
│   ├── db/
│   │   ├── database.py           # SQLite CRUD functions (Person 4)
│   │   └── schema.sql            # Database schema
│   ├── router.py                 # WhatsApp conversation state machine
│   └── config.py                 # Environment variable loader
├── knowledge_base/
│   ├── documents/                # Legal chunks (platform ToS + labour law)
│   └── scripts/                  # ChromaDB ingestion scripts
├── demo/
│   ├── screenshots/              # Demo screenshots
│   └── scripts/                  # Demo helper scripts
├── tests/                        # Test files
├── render.yaml                   # Render deployment config
├── Procfile                      # Process definition
├── requirements.txt
├── .env.example
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/webhook/whatsapp` | Twilio webhook — receives WhatsApp messages |
| GET | `/dashboard/{case_id}` | Case status and timeline |

### Dashboard Response Schema

```json
{
  "case_id": "string",
  "worker_phone": "string (masked)",
  "platform": "string",
  "status": "string",
  "filed_at": "string (ISO 8601)",
  "reference_id": "string",
  "next_action": "string",
  "expected_response_date": "string",
  "days_pending": "integer",
  "timeline": "list"
}
```

### GigGuardState Schema

```python
class GigGuardState(TypedDict):
    phone: str
    message: str
    media_url: Optional[str]
    conversation_state: str          # NEW → AWAITING_SCREENSHOT → AWAITING_CONFIRMATION → IN_PROGRESS → FILED → RESOLVED
    parsed_data: Optional[dict]      # Agent 1 output
    legal_analysis: Optional[dict]   # Agent 2 output
    grievance_letter: Optional[dict] # Agent 3 output
    filing_result: Optional[dict]    # Agent 4 output
    confirmation_pending: bool
    case_id: Optional[str]
    error: Optional[str]
```

---

## Local Setup

### Prerequisites

- Python 3.12+
- A Twilio account with WhatsApp sandbox enabled
- Groq API key (free at console.groq.com)
- Google Gemini API key (free at aistudio.google.com)
- ngrok (for local webhook testing)

### Installation

```bash
# Clone the repository
git clone https://github.com/Team-Vigilante/GigGuard.git
cd GigGuard

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Fill in your API keys in .env

# Run the server
uvicorn main:app --reload --port 8000
```

### Environment Variables

```env
ANTHROPIC_API_KEY=          # Anthropic API key (optional fallback)
GROQ_API_KEY=               # Groq API key (required — free)
GEMINI_API_KEY=             # Google Gemini API key (required — free)
TWILIO_ACCOUNT_SID=         # Twilio Account SID
TWILIO_AUTH_TOKEN=          # Twilio Auth Token
TWILIO_WHATSAPP_NUMBER=     # Twilio WhatsApp number (format: whatsapp:+1xxxxxxxxxx)
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
```

### Twilio Sandbox Setup

```bash
# Start ngrok tunnel
ngrok http 8000

# Copy the https URL and set it in Twilio console:
# Sandbox Settings → "When a message comes in" → https://your-url.ngrok-free.app/webhook/whatsapp
# Method: HTTP POST
```

---

## Conversation Flow

```
Worker: "Mera Swiggy account band ho gaya"
        ↓
GigGuard: "Namaste! Screenshot bhejein ya details type karein."
        ↓
Worker: [sends screenshot]
        ↓
GigGuard: "Platform: Swiggy | Event: Deactivation | ₹1,840 withheld. Sahi hai?"
        ↓
Worker: "Haan"
        ↓
GigGuard: "3 policy violations found. Complaint draft ho rahi hai..."
        ↓
GigGuard: [sends formal grievance letter in Hindi + English]
        ↓
GigGuard: "Filed with Swiggy Grievance Officer. Reference: SWG-2026-061847. 7 din mein jawab expected."
        ↓
[Day 7 — auto follow-up]
        ↓
GigGuard: "No response. Escalating to Labour Department..."
```

---

## Database Schema

```sql
CREATE TABLE sessions (
    id                   TEXT PRIMARY KEY,
    phone_number         TEXT NOT NULL UNIQUE,
    worker_name          TEXT,
    state                TEXT NOT NULL DEFAULT 'intake',
    language             TEXT NOT NULL DEFAULT 'en',
    created_at           TEXT NOT NULL,
    last_active          TEXT NOT NULL,
    conversation_history TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE cases (
    id               TEXT PRIMARY KEY,
    session_id       TEXT NOT NULL,
    platform         TEXT,
    event_type       TEXT,
    date_occurred    TEXT,
    amount_affected  REAL,
    case_status      TEXT NOT NULL DEFAULT 'open',
    filing_channel   TEXT,
    reference_id     TEXT,
    created_at       TEXT NOT NULL,
    resolved_at      TEXT,
    resolution_type  TEXT,
    outcome          TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE evidence (
    id             TEXT PRIMARY KEY,
    case_id        TEXT NOT NULL,
    evidence_type  TEXT,
    file_url       TEXT,
    extracted_data TEXT NOT NULL DEFAULT '{}',
    created_at     TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);
```

---

## Branch Strategy

```
main
  └── dev (integration branch)
        ├── feature/backend-core     (Person 1 — FastAPI, LangGraph, Parser, Dashboard)
        ├── feature/ai-agents        (Person 2 — Researcher, Drafter, Prompts)
        ├── feature/knowledge-base   (Person 4 — DB, Navigator, Dashboard UI)
        └── feature/demo-infra       (Demo scripts, PDF generator, Chat UI)
```

**Rules:**
- No direct pushes to `main` or `dev`
- All work goes to feature branches
- PRs opened to `dev` for review
- Maintainer merges `dev` → `main` at milestones

---

## Impact Targets (12 months)

| Metric | Target |
|--------|--------|
| Active workers | 50,000 |
| Cases filed | 20,000 |
| Cases resolved | 12,000 (60%) |
| Compensation recovered | ₹5 Crore |
| Appeal success rate | 68% |
| Languages supported | 5+ |

---

## Legal Basis

GigGuard operates on the framework established by:

- **Code on Social Security 2020** — mandates written notice before deactivation, protects earned wages
- **Social Security (Central) Rules 2026** — notified May 8, 2026, places direct compliance obligations on platforms
- **Platform Terms of Service** — Swiggy, Zomato, Ola, Uber (all require warnings before deactivation)
- **Fairwork India Standards** — fair pay, fair conditions, fair contracts, fair management, fair representation
- **Karnataka Gig Workers Act 2025** — state-level protections for platform workers

---

## License

[License]

---

## Acknowledgements

Built at HackArena 2.0. Data sources: PAIGAM, Fairwork India, TGPWU, Human Rights Watch, Ministry of Labour and Employment (India).

*12 million workers. One AI advocate.*
