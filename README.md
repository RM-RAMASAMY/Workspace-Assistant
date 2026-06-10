# Voice RAG Chatbot

An internal voice-enabled chatbot that uses local RAG (Retrieval-Augmented Generation) to answer questions based on internal documents.

## Prerequisites

- **Docker** (for building images)
- **Kubernetes** (Docker Desktop K8s, Minikube, or similar)
- **kubectl**
- **Ollama Desktop** running on the host with `gpt-oss:120b-cloud` available at `http://localhost:11434`

## Setup

### 1. Configure secrets

On first run, `./start.sh` creates `k8s/secret.yaml` from the example. Edit it with your API keys:

- `DEEPGRAM_API_KEY` — Speech-to-Text
- `ELEVENLABS_API_KEY` — Text-to-Speech
- *(Optional)* `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — Google SSO

### 2. Start

```bash
./start.sh
```

This builds the Docker images and deploys to the `voice-rag` Kubernetes namespace.

- **NodePort:** http://localhost:30080
- **Ingress** (if nginx IngressClass is installed): http://voice-rag.local — add `127.0.0.1 voice-rag.local` to your hosts file

### 3. Stop

```bash
./stop.sh
```

## How to Test

1. Open the app URL (see above).
2. **Log In** with the demo account:
   - **Email:** `employee@demo.com`
   - **Password:** `employee123`
   - *(Other accounts: `admin@demo.com` / `admin123`, `manager@demo.com` / `manager123`)*
3. **Use the Chatbot** — hold the microphone button to ask a question.

## Notes

- Ollama runs on the **host** via Ollama Desktop (not in Kubernetes). The backend reaches it at `host.docker.internal:11434`.
- Check pod status: `kubectl get pods -n voice-rag`
- Seed demo data (one-time, after backend pod is running):
  ```bash
  kubectl exec -n voice-rag deploy/backend -- python seed_data.py
  kubectl exec -n voice-rag deploy/backend -- python create_samples.py
  ```
