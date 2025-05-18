# CI/CD Workflow with Tekton Cluster

## Overview

This workflow demonstrates how to use a **Tekton Cluster** (running on a spare machine) to automate CI/CD tasks triggered from a main desktop. The pipeline pulls code, processes it, and pushes the results to GitHub or a DVC remote.

---

## Workflow Diagram

```plaintext
[Main Desktop]
     |
     | 1. Push code / trigger pipeline (e.g., via SSH, webhook, etc.)
     ↓
[Spare Machine (Tekton Cluster)]
     |
     | 2. Pull code from main desktop / repo
     | 3. Run pipeline steps (build, test, dvc push, etc.)
     | 4. Push final code/results to GitHub or remote storage
     ↓
[GitHub / DVC Remote]
```
---

## 🧩 Components Needed
1. Kubernetes on spare machine (e.g., Minikube, kind, or k3s)
2. Tekton Pipelines installed in Kubernetes
3. Git installed and authorized to push to GitHub

---
