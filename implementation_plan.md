# Voice RAG Chatbot — PoC Implementation Plan

## Goal

Build a complete, locally-runnable proof-of-concept that demonstrates all major features from the [system design](file:///C:/Users/Ramro/.gemini/antigravity/brain/95d5d612-92dd-4d45-b0d1-65dbb868f591/voice_chatbot_system_design.md): push-to-talk voice input, STT, RAG retrieval with citations, LLM generation, TTS response, RBAC access control, document management, and observability — all running on your laptop.

## Technology Decisions

| Component | Choice | Rationale |
|---|---|---|
| **Frontend** | React (Vite) | SPA with push-to-talk, streaming audio, citation cards |
| **Backend** | Python FastAPI | Async, WebSocket support, fast prototyping |
| **Auth** | Google OAuth + Email/Password | Google SSO via OAuth 2.0; fallback email/password with JWT |
| **RBAC** | 4-level access (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED) | Per system design; enforced at retrieval layer |
| **Database** | SQLite (via SQLAlchemy) | Zero setup; stores users, roles, documents, query logs |
| **Vector Store** | ChromaDB (local, persistent) | Zero setup; hybrid search support; embedded mode |
| **Embedding Model** | `all-MiniLM-L6-v2` (sentence-transformers, local) | Runs on CPU; 384 dims; no API key needed |
| **LLM** | Ollama → `gpt-oss:120b` (cloud-hosted, local API) | User's existing setup; OpenAI-compatible API at `localhost:11434` |
| **STT** | Deepgram API (Nova-3) | Best accuracy; free tier 12K min; WebSocket streaming |
| **TTS** | ElevenLabs API | Most natural voice; free tier 10K chars/month |
| **Reranker** | `cross-encoder/ms-marco-MiniLM-L-6-v2` (local) | Runs on CPU; no API key; good quality |

## Project Structure

```
c:\Users\Ramro\OneDrive\Documents\a_code_folder\Git Projects\HanuInnoTech\
├── README.md                          # Setup & run instructions
├── .env.example                       # Template for API keys
├── docker-compose.yml                 # (Optional) for containerized run
│
├── backend/
│   ├── requirements.txt
│   ├── main.py                        # FastAPI app entry point
│   ├── config.py                      # Settings & env vars
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── models.py                  # User, Role, Permission SQLAlchemy models
│   │   ├── schemas.py                 # Pydantic schemas
│   │   ├── router.py                  # /auth/* endpoints (login, register, google SSO)
│   │   ├── dependencies.py            # get_current_user, require_role
│   │   └── google_oauth.py            # Google OAuth flow
│   │
│   ├── documents/
│   │   ├── __init__.py
│   │   ├── models.py                  # Document, Chunk SQLAlchemy models
│   │   ├── schemas.py
│   │   ├── router.py                  # /documents/* endpoints (upload, list, delete)
│   │   ├── ingestion.py               # Parse → chunk → embed → index pipeline
│   │   └── chunker.py                 # Semantic/recursive chunking
│   │
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── vector_store.py            # ChromaDB wrapper with RBAC filtering
│   │   ├── hybrid_search.py           # Dense + keyword search + RRF fusion
│   │   ├── reranker.py                # Cross-encoder reranking
│   │   └── query_processor.py         # Query rewrite, multi-query, coreference
│   │
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── llm_client.py              # Ollama client (OpenAI-compatible)
│   │   ├── prompt_templates.py        # System prompt, citation format
│   │   ├── guardrails.py              # Input sanitization, output filtering
│   │   └── streaming.py               # Sentence-level streaming + TTS pipeline
│   │
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── stt_client.py              # Deepgram STT adapter
│   │   ├── tts_client.py              # ElevenLabs TTS adapter
│   │   └── router.py                  # /voice/* WebSocket endpoints
│   │
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── models.py                  # QueryLog, EvalScore models
│   │   ├── router.py                  # /admin/observability/* endpoints
│   │   ├── evaluator.py               # Faithfulness, relevance scoring
│   │   └── metrics.py                 # Latency, token usage tracking
│   │
│   ├── database.py                    # SQLite engine + session
│   └── seed_data.py                   # Seed users, roles, sample documents
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── public/
│   │   └── favicon.ico
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css                  # Design system (dark theme, glassmorphism)
│       │
│       ├── components/
│       │   ├── ChatInterface.jsx       # Main chat area with messages
│       │   ├── PushToTalk.jsx          # PTT button with animation
│       │   ├── MessageBubble.jsx       # Message with citation chips
│       │   ├── CitationCard.jsx        # Expandable source card
│       │   ├── AudioPlayer.jsx         # TTS audio queue + playback
│       │   ├── Waveform.jsx            # Recording waveform animation
│       │   ├── Sidebar.jsx             # Session list + document management
│       │   ├── DocumentUpload.jsx      # Drag-and-drop upload
│       │   ├── AdminPanel.jsx          # User management, RBAC, observability
│       │   ├── LoginPage.jsx           # Login + Google SSO
│       │   └── Navbar.jsx              # Top bar with user info
│       │
│       ├── hooks/
│       │   ├── useAudioRecorder.js     # MediaRecorder hook
│       │   ├── useWebSocket.js         # WS connection management
│       │   └── useAuth.js              # Auth state + JWT management
│       │
│       ├── context/
│       │   └── AuthContext.jsx         # Auth provider
│       │
│       └── utils/
│           ├── api.js                  # Axios/fetch wrapper
│           └── audioUtils.js           # Audio format conversion
│
└── sample_docs/                       # Auto-generated demo corpus
    ├── product_spec_v3.pdf
    ├── hr_employee_handbook.pdf
    ├── engineering_standards.pdf
    ├── iot_sensor_manual.pdf
    ├── quarterly_report_q1.pdf
    ├── onboarding_guide.pdf
    ├── security_policy.pdf
    ├── api_documentation.pdf
    ├── data_governance_policy.pdf
    ├── meeting_notes_board.pdf
    ├── training_manual_v2.pdf
    ├── release_notes_v4.pdf
    └── ...
```

---

## Proposed Changes

### Component 1: Backend Core

#### [NEW] [main.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/main.py)
- FastAPI app with CORS, WebSocket, and router registration
- Startup events: init DB, seed data, init ChromaDB
- Health check endpoint

#### [NEW] [config.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/config.py)
- Pydantic Settings loading from `.env`
- Keys: `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`, `OLLAMA_BASE_URL`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `JWT_SECRET`

#### [NEW] [database.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/database.py)
- SQLite engine via SQLAlchemy async
- Session dependency for FastAPI

---

### Component 2: Authentication & RBAC

#### [NEW] [auth/models.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/auth/models.py)
- `User` model: id, email, name, hashed_password, auth_provider (local/google), access_level, role_id, created_at
- `Role` model: id, name (admin/manager/employee/viewer), max_access_level, can_upload_docs, can_manage_users
- Relationships: User → Role (many-to-one)

#### [NEW] [auth/router.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/auth/router.py)
- `POST /auth/register` — email/password registration (assigns "employee" role by default)
- `POST /auth/login` — email/password login → returns JWT
- `GET /auth/google` — redirect to Google OAuth consent screen
- `GET /auth/google/callback` — handle Google OAuth callback, create/link user, return JWT
- `GET /auth/me` — return current user info + role + access level
- `GET /auth/users` — admin-only: list all users
- `PUT /auth/users/{id}/role` — admin-only: change user role

#### [NEW] [auth/dependencies.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/auth/dependencies.py)
- `get_current_user(token)` — decode JWT, fetch user from DB
- `require_role(min_role)` — dependency that checks user's role level
- `require_access_level(level)` — dependency that checks access level

**RBAC Demo Configuration:**

| Role | Access Level | Can Upload Docs | Can Manage Users | Description |
|---|---|---|---|---|
| `admin` | RESTRICTED | ✅ | ✅ | Full access to all documents and admin panel |
| `manager` | CONFIDENTIAL | ✅ | ❌ | Access to confidential + internal + public docs |
| `employee` | INTERNAL | ❌ | ❌ | Access to internal + public docs only |
| `viewer` | PUBLIC | ❌ | ❌ | Access to public docs only |

**Seeded Demo Users:**

| Email | Password | Role | Purpose |
|---|---|---|---|
| admin@demo.com | admin123 | admin | Full access demo |
| manager@demo.com | manager123 | manager | Confidential access demo |
| employee@demo.com | employee123 | employee | Internal access demo |
| viewer@demo.com | viewer123 | viewer | Public-only access demo |

---

### Component 3: Document Ingestion Pipeline

#### [NEW] [documents/ingestion.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/documents/ingestion.py)
- `ingest_document(file, access_level, metadata)`:
  1. Parse document (PDF via PyMuPDF, DOCX via python-docx, TXT/MD directly)
  2. Extract text with structural metadata (headings, pages)
  3. Chunk using recursive character splitter (512 tokens, 64 overlap)
  4. Embed chunks using `all-MiniLM-L6-v2` (local, CPU)
  5. Store in ChromaDB with metadata (doc_id, page, section, access_level)
  6. Update document status in SQLite

#### [NEW] [documents/chunker.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/documents/chunker.py)
- Recursive character text splitter with sentence boundary detection
- Parent-child chunking: 1024-token parents, 256-token children
- Metadata attachment per chunk

#### [NEW] [documents/router.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/documents/router.py)
- `POST /documents/upload` — upload file, set access_level, trigger ingestion
- `GET /documents/` — list documents (filtered by user's access level)
- `GET /documents/{id}` — get document details + chunks
- `DELETE /documents/{id}` — admin/manager only: delete document + chunks
- `GET /documents/{id}/download` — download original file

---

### Component 4: Retrieval Engine

#### [NEW] [retrieval/vector_store.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/retrieval/vector_store.py)
- ChromaDB persistent client wrapper
- `search(query_embedding, access_level, top_k)` — with metadata filter: `access_level <= user.level`
- Collections: one per embedding model version

#### [NEW] [retrieval/hybrid_search.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/retrieval/hybrid_search.py)
- Dense search: ChromaDB cosine similarity (top-20)
- Sparse search: BM25 via `rank_bm25` library on chunk texts (top-20)
- RRF fusion: merge dense + sparse results with `score = Σ 1/(k + rank)` where k=60
- Return top-40 fused candidates

#### [NEW] [retrieval/reranker.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/retrieval/reranker.py)
- Local cross-encoder: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Rerank top-40 → top-5
- Runs on CPU (~200ms for 40 pairs)

#### [NEW] [retrieval/query_processor.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/retrieval/query_processor.py)
- Intent classification: factual / conversational / out-of-scope (via LLM)
- Coreference resolution using conversation history
- Multi-query expansion (generate 2-3 variants via LLM)

---

### Component 5: LLM Generation

#### [NEW] [generation/llm_client.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/generation/llm_client.py)
- Ollama client using OpenAI-compatible API (`http://localhost:11434/v1/chat/completions`)
- Streaming support via SSE
- Fallback: if Ollama is down, return "LLM unavailable" message gracefully

#### [NEW] [generation/prompt_templates.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/generation/prompt_templates.py)
- System prompt (per system design Section 5.8.3)
- Citation format enforcement
- Conversation history formatting

#### [NEW] [generation/streaming.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/generation/streaming.py)
- Token-level streaming from LLM
- Sentence boundary detection (regex: `. `, `! `, `? `, newline)
- Per-sentence TTS synthesis pipeline
- WebSocket message format: `{type: "text"|"audio"|"citation", data: ...}`

---

### Component 6: Voice Pipeline

#### [NEW] [voice/stt_client.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/voice/stt_client.py)
- Deepgram REST API (`/v1/listen`)
- Accept webm/opus audio blob
- Return transcription + confidence score
- Custom vocabulary/keyword boosting configuration

#### [NEW] [voice/tts_client.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/voice/tts_client.py)
- ElevenLabs API (`/v1/text-to-speech/{voice_id}/stream`)
- Sentence-level streaming
- Return audio chunks (mp3)
- Fallback to browser SpeechSynthesis if API key missing

#### [NEW] [voice/router.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/voice/router.py)
- `WebSocket /ws/voice` — main voice pipeline:
  1. Receive audio blob from client
  2. STT → transcription
  3. Query processing → retrieval → reranking
  4. LLM streaming → sentence detection → TTS
  5. Stream back: text chunks, audio chunks, citation data
- `POST /voice/query` — REST fallback (non-streaming, for text-only input)

---

### Component 7: Observability

#### [NEW] [observability/models.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/observability/models.py)
- `QueryLog`: user_id, query, response, latency_ms (total, stt, retrieval, llm, tts), tokens_used, timestamp
- `EvalScore`: query_log_id, faithfulness, relevance, citation_accuracy

#### [NEW] [observability/evaluator.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/observability/evaluator.py)
- Lightweight faithfulness checker: verify each claim in answer appears in context
- Citation accuracy: check cited doc/page matches retrieved chunks
- Async evaluation after response is sent

#### [NEW] [observability/router.py](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/backend/observability/router.py)
- `GET /admin/observability/dashboard` — aggregated metrics (avg latency, faithfulness, usage)
- `GET /admin/observability/queries` — paginated query log with scores
- `GET /admin/observability/queries/{id}` — full trace (query, context, response, scores)

---

### Component 8: Frontend — Premium Dark UI

#### Design System
- **Theme**: Dark mode with glassmorphism, inspired by modern AI assistants
- **Colors**: Deep slate background (#0f172a), electric blue accent (#3b82f6), emerald status (#10b981)
- **Typography**: Inter (Google Font) — clean, modern
- **Animations**: Smooth transitions, pulsing PTT button, typing indicators, waveform visualizer

#### [NEW] [LoginPage.jsx](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/frontend/src/components/LoginPage.jsx)
- Email + password form
- "Sign in with Google" button
- Registration toggle
- Glassmorphic card design

#### [NEW] [ChatInterface.jsx](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/frontend/src/components/ChatInterface.jsx)
- Main chat area with message history
- Scrollable message list
- User messages (right-aligned) + Assistant messages (left-aligned)
- Inline citation chips below each answer
- Typing indicator during LLM streaming

#### [NEW] [PushToTalk.jsx](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/frontend/src/components/PushToTalk.jsx)
- Large circular microphone button
- States: idle → recording → processing → playing
- Pulsing ring animation during recording
- Waveform visualization using canvas
- Also has a text input field for typed queries

#### [NEW] [CitationCard.jsx](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/frontend/src/components/CitationCard.jsx)
- Expandable card showing: document title, page number, section, relevance score
- Click to expand → shows full chunk text snippet
- Document icon based on file type

#### [NEW] [Sidebar.jsx](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/frontend/src/components/Sidebar.jsx)
- Session history (new chat / previous chats)
- Document list with access level badges
- Upload button (if user has permission)
- Admin panel link (if user is admin)

#### [NEW] [AdminPanel.jsx](file:///c:/Users/Ramro/OneDrive/Documents/a_code_folder/Git%20Projects/HanuInnoTech/frontend/src/components/AdminPanel.jsx)
- **User Management tab**: list users, change roles, access levels
- **Document Management tab**: view all docs, change access levels, delete
- **Observability tab**: metrics dashboard with charts
  - Average E2E latency (line chart)
  - Query volume (bar chart)
  - Faithfulness score distribution (histogram)
  - Top queried topics (word cloud / bar chart)
  - Recent queries with scores (table)

---

### Component 9: Sample Documents

Auto-generate ~12 realistic Markdown documents (converted to PDF at ingest time) covering different access levels:

| Document | Access Level | Content |
|---|---|---|
| Product Specification v3.2 | INTERNAL | IoT sensor specs, accuracy, calibration procedures |
| Employee Handbook 2026 | PUBLIC | Company policies, benefits, PTO, code of conduct |
| Engineering Standards Guide | INTERNAL | Coding standards, code review process, CI/CD |
| IoT Sensor Technical Manual | CONFIDENTIAL | Firmware details, low-level protocols, schematics |
| Q1 Quarterly Business Report | CONFIDENTIAL | Revenue, growth metrics, strategic initiatives |
| New Employee Onboarding Guide | PUBLIC | First week checklist, tools setup, team contacts |
| Information Security Policy | INTERNAL | Data classification, password policy, incident response |
| REST API Documentation v4 | INTERNAL | API endpoints, authentication, rate limits |
| Data Governance Policy | CONFIDENTIAL | Data retention, privacy, compliance procedures |
| Board Meeting Notes - June 2026 | RESTRICTED | Board-only strategic discussions, M&A considerations |
| Technical Training Manual v2 | PUBLIC | Training curriculum, skill assessments |
| Release Notes v4.0 | PUBLIC | New features, bug fixes, known issues |

---

### Component 10: Google OAuth Setup Guide

The README will include step-by-step instructions:
1. Go to Google Cloud Console → Create project
2. Enable Google+ API / People API
3. Create OAuth 2.0 credentials (Web application)
4. Set redirect URI to `http://localhost:8000/auth/google/callback`
5. Copy Client ID + Secret to `.env`

---

## User Review Required

> [!IMPORTANT]
> **Ollama Setup**: You need to have Ollama running locally and pointing to the `gpt-oss:120b` cloud model. The backend will connect to `http://localhost:11434`. Please confirm this is accessible on your machine.

> [!IMPORTANT]
> **API Keys Required**: Before running, you'll need:
> - `DEEPGRAM_API_KEY` — from [console.deepgram.com](https://console.deepgram.com)
> - `ELEVENLABS_API_KEY` — from [elevenlabs.io](https://elevenlabs.io)
> - `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` — from Google Cloud Console (instructions in README)

> [!WARNING]
> **ElevenLabs Free Tier Limit**: 10K characters/month (~2-3 minutes of speech). For extended demos, the system falls back to browser SpeechSynthesis (still functional, less natural voice). Alternatively you can use a paid API key.

## Open Questions

> [!NOTE]
> **Charting library**: For the observability dashboard, I plan to use **Recharts** (React charting library). Is that acceptable, or do you prefer a different one?

> [!NOTE]
> **Sample documents format**: I'll generate them as Markdown files that the ingestion pipeline will process. This keeps them easy to edit. The system also supports PDF/DOCX upload through the UI.

---

## Verification Plan

### Automated Tests
- Backend: `pytest` for API endpoints, auth flows, retrieval pipeline
- Run with: `cd backend && pytest tests/ -v`

### Manual Verification (Demo Script)

1. **Auth Flow**:
   - Register new user → verify JWT
   - Login with demo users (admin, employee, viewer)
   - Google SSO flow (if configured)

2. **RBAC Demo**:
   - Login as `viewer@demo.com` → ask about board meeting notes → should get "insufficient access" or no results
   - Login as `admin@demo.com` → same question → should get results from restricted docs
   - Login as `employee@demo.com` → query about sensor specs → gets INTERNAL docs but not CONFIDENTIAL

3. **Voice Pipeline**:
   - Press PTT → ask question → see transcription appear → hear answer spoken back
   - Verify citation cards appear with correct document/page references

4. **Document Management**:
   - Upload a new document via admin panel
   - Set access level
   - Query about it → verify it appears in results

5. **Observability**:
   - Make 5-10 queries
   - Open admin panel → observability tab
   - Verify latency charts, query logs, faithfulness scores

### Startup Commands
```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev

# Terminal 3: Ollama (should already be running)
ollama run gpt-oss:120b
```

Open browser at `http://localhost:5173` → Full demo ready.
