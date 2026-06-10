#!/usr/bin/env bash
# =============================================================================
# Voice RAG Chatbot — Kubernetes Start Script
# =============================================================================
#
# Builds Docker images and deploys the full application stack to Kubernetes.
#
# What gets deployed:
#   - backend  (FastAPI + RAG pipeline)  → ClusterIP service on port 8000
#   - frontend (React + nginx proxy)    → NodePort 30080, or Ingress if available
#   - PVC      (persistent volume)        → SQLite DB, ChromaDB vectors, uploads
#
# What stays OUTSIDE Kubernetes:
#   - Ollama Desktop on your host machine, serving gpt-oss:120b-cloud via
#     Ollama Cloud. The backend reaches it at host.docker.internal:11434.
#     No local GPU/RAM is needed for the LLM — inference runs in the cloud.
#
# Prerequisites:
#   1. Docker installed and running
#   2. A local Kubernetes cluster (Docker Desktop K8s, Minikube, Kind, etc.)
#   3. kubectl configured to point at that cluster
#   4. Ollama Desktop running with gpt-oss:120b-cloud pulled/available
#   5. k8s/secret.yaml filled in with API keys (created on first run)
#
# Usage:
#   ./start.sh
#
# First-time setup:
#   1. Run this script once — it creates k8s/secret.yaml from the example
#   2. Edit k8s/secret.yaml with your Deepgram and ElevenLabs API keys
#   3. Run ./start.sh again
#
# After deploy (optional, one-time seed data):
#   kubectl exec -n voice-rag deploy/backend -- python seed_data.py
#   kubectl exec -n voice-rag deploy/backend -- python create_samples.py
#
# Access the app:
#   - NodePort (default):  http://localhost:30080
#   - Ingress (if nginx):  http://voice-rag.local  (add to hosts file)
#
# Useful commands:
#   kubectl get pods -n voice-rag                          # check pod status
#   kubectl logs -n voice-rag deploy/backend -f            # backend logs
#   kubectl logs -n voice-rag deploy/frontend -f           # frontend logs
#   kubectl port-forward -n voice-rag svc/backend 8000:8000  # direct backend access
#
# Stop:
#   ./stop.sh
# =============================================================================

set -euo pipefail

# Resolve project root so the script works regardless of the current directory.
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="$PROJECT_ROOT/k8s"
SECRET_FILE="$K8S_DIR/secret.yaml"

# -----------------------------------------------------------------------------
# Step 1: Ensure secrets exist
# -----------------------------------------------------------------------------
# API keys (Deepgram, ElevenLabs, JWT) are stored in a Kubernetes Secret.
# On first run we copy the example file and ask you to fill in real values.
# k8s/secret.yaml is gitignored — never commit it.
if [[ ! -f "$SECRET_FILE" ]]; then
  echo "Creating $SECRET_FILE from secret.example.yaml"
  cp "$K8S_DIR/secret.example.yaml" "$SECRET_FILE"
  echo ""
  echo "Edit $SECRET_FILE with your API keys, then re-run ./start.sh"
  exit 1
fi

# -----------------------------------------------------------------------------
# Step 2: Build Docker images
# -----------------------------------------------------------------------------
# Images are tagged :latest and loaded into the local Docker daemon.
# Docker Desktop K8s shares the same daemon, so pods can pull them directly.
# The backend image is large (~2-4 GB) due to PyTorch + sentence-transformers;
# first build may take several minutes.
echo "Building Docker images..."
docker build -t voice-rag-backend:latest "$PROJECT_ROOT/backend"
docker build -t voice-rag-frontend:latest "$PROJECT_ROOT/frontend"

# -----------------------------------------------------------------------------
# Step 3: Apply Kubernetes manifests
# -----------------------------------------------------------------------------
# Resources are applied in dependency order:
#   namespace  → isolates all resources under "voice-rag"
#   configmap  → non-secret config (Ollama URL, model name, DB paths)
#   secret     → API keys and JWT secret
#   pvc        → persistent storage for SQLite, ChromaDB, and uploads
#   deployments + services → backend and frontend workloads
echo "Applying Kubernetes manifests..."
kubectl apply -f "$K8S_DIR/namespace.yaml"
kubectl apply -f "$K8S_DIR/configmap.yaml"
kubectl apply -f "$SECRET_FILE"
kubectl apply -f "$K8S_DIR/backend-pvc.yaml"
kubectl apply -f "$K8S_DIR/backend-deployment.yaml"
kubectl apply -f "$K8S_DIR/backend-service.yaml"
kubectl apply -f "$K8S_DIR/frontend-deployment.yaml"
kubectl apply -f "$K8S_DIR/frontend-service.yaml"

# -----------------------------------------------------------------------------
# Step 4: Ingress (optional)
# -----------------------------------------------------------------------------
# If an nginx IngressClass is installed, route traffic through voice-rag.local.
# Otherwise the frontend is exposed via NodePort 30080 (see frontend-service.yaml).
if kubectl get ingressclass nginx >/dev/null 2>&1; then
  kubectl apply -f "$K8S_DIR/ingress.yaml"
  echo ""
  echo "Ingress enabled. Add this line to your hosts file:"
  echo "  127.0.0.1 voice-rag.local"
  echo "  App: http://voice-rag.local"
else
  echo ""
  echo "No nginx IngressClass found — using NodePort instead."
  echo "  App: http://localhost:30080"
fi

# -----------------------------------------------------------------------------
# Done — print next steps
# -----------------------------------------------------------------------------
echo ""
echo "Voice RAG Chatbot is deploying to Kubernetes."
echo ""
echo "  Check pods:     kubectl get pods -n voice-rag"
echo "  Backend health: kubectl port-forward -n voice-rag svc/backend 8000:8000"
echo "                  then open http://localhost:8000/health"
echo ""
echo "  Ensure Ollama Desktop is running with gpt-oss:120b-cloud."
echo "  Stop with: ./stop.sh"
