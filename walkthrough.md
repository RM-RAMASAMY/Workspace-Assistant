# Voice RAG Chatbot — Implementation Walkthrough

> [!NOTE]
> Based on the implementation plan, I have built the core backend services and the frontend React application for the Voice RAG Chatbot.

## What was built

1. **Backend Infrastructure (FastAPI + SQLite + ChromaDB)**:
   - `main.py`, `config.py`, and `database.py` are set up.
   - Authentication system with RBAC (roles: admin, manager, employee, viewer).
   - Document ingestion pipeline using `sentence-transformers` to chunk and embed documents into a local ChromaDB instance.
   - Retrieval engine with a reranker (`cross-encoder/ms-marco`).
   - Voice WebSocket endpoint integrating Deepgram (STT), ElevenLabs (TTS), and Ollama (LLM) for real-time interactions.

2. **Frontend Application (React + Vite + Tailwind)**:
   - Initialized a Vite project and configured Tailwind CSS v4.
   - Set up the Dark UI design system in `index.css`.
   - Created the `LoginPage` with mock credentials.
   - Built the `ChatInterface` which connects to the backend WebSocket.
   - Implemented the `PushToTalk` component utilizing `MediaRecorder` for audio capture.
   - Added a `Sidebar` for session and document management.
   - Implemented basic `api.js` utils and `AuthContext` for JWT handling.

3. **Sample Data**:
   - Included a `seed_data.py` script to generate roles and users.
   - Included a `create_samples.py` script to generate a few internal markdown documents matching the requested categories.

## How to Run

1. **Start the Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python seed_data.py
   python create_samples.py
   python -m uvicorn main:app --reload --port 8000
   ```

2. **Start the Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Verify API Keys**:
   Ensure you have your `.env` configured with `DEEPGRAM_API_KEY` and `ELEVENLABS_API_KEY`. The Ollama instance should be running locally at `http://localhost:11434`.

> [!TIP]
> The WebSockets endpoint assumes the React app handles recording. You can log in as `employee@demo.com` (`employee123`) to access the interface.
