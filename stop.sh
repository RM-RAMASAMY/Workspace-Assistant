#!/usr/bin/env bash
# =============================================================================
# Voice RAG Chatbot — Kubernetes Stop Script
# =============================================================================
#
# Tears down the entire application stack from Kubernetes.
#
# What gets removed:
#   - backend Deployment and Service
#   - frontend Deployment and Service
#   - Ingress (if it was applied)
#   - ConfigMap and Secret
#   - PersistentVolumeClaim (and its data — SQLite DB, ChromaDB, uploads)
#
# What is NOT affected:
#   - Docker images (voice-rag-backend:latest, voice-rag-frontend:latest)
#     remain in your local Docker cache for faster re-deploys.
#   - Ollama Desktop on the host — it runs independently of Kubernetes.
#   - k8s/secret.yaml on disk — your API keys are preserved for next start.
#
# Usage:
#   ./stop.sh
#
# To restart:
#   ./start.sh
#   (skips image rebuild if you haven't changed code — or rebuilds if you have)
#
# To also remove Docker images (free disk space):
#   docker rmi voice-rag-backend:latest voice-rag-frontend:latest
# =============================================================================

set -euo pipefail

# Deleting the namespace cascades to every resource inside it:
# Deployments, Services, Ingress, ConfigMap, Secret, and PVC.
# --ignore-not-found prevents an error if the namespace was already removed.
kubectl delete namespace voice-rag --ignore-not-found

echo "Services stopped."
