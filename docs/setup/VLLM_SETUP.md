# vLLM Setup Guide

**Enhancement 017: Production Architecture - Phase 1**

This guide covers setting up vLLM (Very Large Language Model) for high-performance local LLM inference with the AI Orchestrator.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Deployment Methods](#deployment-methods)
6. [Model Selection](#model-selection)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)
9. [Monitoring](#monitoring)

---

## Overview

### What is vLLM?

vLLM is a fast and easy-to-use library for LLM inference and serving, featuring:

- **High Performance**: Up to 24x faster than HuggingFace Transformers
- **PagedAttention**: Efficient memory management for long sequences
- **Continuous Batching**: Improved throughput for concurrent requests
- **OpenAI-Compatible API**: Drop-in replacement for OpenAI API
- **Multi-GPU Support**: Tensor parallelism for large models
- **Streaming Support**: Native SSE streaming for real-time responses

### Why Use vLLM in AI Orchestrator?

- **FREE Unlimited Inference**: No API costs for local models
- **Production-Ready Performance**: 10-20x faster than Ollama
- **GPU Acceleration**: Optimized for NVIDIA GPUs
- **High Throughput**: Handle multiple concurrent requests efficiently
- **Privacy-First**: All data stays on your infrastructure
- **Cost Optimization**: Maximize free tier usage before paid APIs

---

## Prerequisites

### Hardware Requirements

**Minimum:**
- NVIDIA GPU with 8GB+ VRAM (e.g., RTX 3070, A4000)
- 16GB System RAM
- 50GB+ free disk space (for models)

**Recommended:**
- NVIDIA GPU with 24GB+ VRAM (e.g., RTX 4090, A100)
- 32GB+ System RAM
- 100GB+ free SSD storage
- PCIe 4.0 x16 slot

**GPU Memory Requirements by Model:**
| Model | FP16 VRAM | Quantized (8-bit) |
|-------|-----------|-------------------|
| Llama 2 7B | ~7GB | ~4GB |
| Llama 2 13B | ~13GB | ~7GB |
| CodeLlama 13B | ~13GB | ~7GB |
| Mistral 7B | ~7GB | ~4GB |
| Llama 2 70B | ~70GB (4x A100) | ~35GB (2x A100) |

### Software Requirements

- **Operating System**: Linux (Ubuntu 20.04+, Debian 11+) or Windows 11 with WSL2
- **Docker**: 20.10+
- **Docker Compose**: 1.28+
- **NVIDIA Driver**: 525.60.13+ (CUDA 12.0+)
- **nvidia-docker2**: For GPU passthrough in containers

### Verify Prerequisites

```bash
# Check NVIDIA driver
nvidia-smi

# Expected output:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 525.60.13   Driver Version: 525.60.13   CUDA Version: 12.0      |
# +-----------------------------------------------------------------------------+

# Check Docker
docker --version
# Docker version 20.10.0+

# Check nvidia-docker
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
# Should show GPU info
```

---

## Installation

### 1. Install NVIDIA Container Toolkit

**Ubuntu/Debian:**
```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-docker2
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Restart Docker
sudo systemctl restart docker

# Verify installation
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

**Other Distributions:**
See: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

### 2. Clone or Update AI Orchestrator

```bash
cd /Users/shiva/Projects/ai-orchestrator
git pull  # If using git

# Verify vLLM files exist
ls -l docker-compose.vllm.yml
ls -l src/providers/vllm_provider.py
```

### 3. Create Docker Network

```bash
docker network create ai-orchestrator-network
```

---

## Configuration

### 1. Create Environment File

Create `.env.vllm` file in the project root:

```bash
# vLLM Server Configuration
VLLM_MODEL=meta-llama/Llama-2-13b-chat-hf
VLLM_TENSOR_PARALLEL=1  # Set to number of GPUs
VLLM_GPU_MEMORY=0.9     # Use 90% of GPU memory
VLLM_MAX_LEN=4096       # Max sequence length
VLLM_SWAP_SPACE=4       # GB of CPU swap space
VLLM_PREFIX_CACHE=true  # Enable prefix caching

# HuggingFace Configuration
HF_TOKEN=your_huggingface_token  # Optional: for gated models

# OpenTelemetry (Optional)
OTEL_ENDPOINT=http://monitoring-hub-otel-collector:4317

# AI Orchestrator Integration
VLLM_ENABLED=true
VLLM_BASE_URL=http://localhost:8001
VLLM_TIMEOUT=120
```

### 2. Update AI Orchestrator .env

Add vLLM settings to your main `.env` file:

```bash
# vLLM Configuration (Enhancement 017)
VLLM_ENABLED=true
VLLM_BASE_URL=http://localhost:8001
VLLM_MODEL=meta-llama/Llama-2-13b-chat-hf
VLLM_TIMEOUT=120
```

### 3. Update Routing Configuration

Edit `config/providers_dev.yaml` to enable vLLM:

```yaml
  vllm:
    enabled: true  # Changed from false
    priority: highest
    tier: free
    # ... rest of config
```

Update routing chain to prioritize vLLM:

```yaml
routing:
  default_chain:
    - vllm        # Highest priority for general tasks
    - deepseek    # Code tasks
    - local       # Backup
    - gemini      # Free tier backup
    - chatgpt     # Paid fallback
```

---

## Deployment Methods

### Method 1: Docker Compose (Recommended)

**Step 1: Download Models (Optional but Recommended)**

Pre-download models to avoid slow startup:

```bash
docker-compose -f docker-compose.vllm.yml --profile download up vllm-model-downloader

# This downloads the model to a Docker volume
# Subsequent starts will be much faster
```

**Step 2: Start vLLM Server**

```bash
docker-compose -f docker-compose.vllm.yml up -d

# View logs
docker-compose -f docker-compose.vllm.yml logs -f vllm

# Expected output:
# INFO:     Started server process
# INFO:     Waiting for application startup
# INFO:     Loading model meta-llama/Llama-2-13b-chat-hf
# INFO:     Model loaded successfully
# INFO:     Application startup complete
```

**Step 3: Verify Server**

```bash
# Check health endpoint
curl http://localhost:8001/v1/models

# Expected response:
# {
#   "object": "list",
#   "data": [
#     {
#       "id": "meta-llama/Llama-2-13b-chat-hf",
#       "object": "model",
#       "created": 1234567890,
#       "owned_by": "vllm"
#     }
#   ]
# }

# Test completion
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-2-13b-chat-hf",
    "messages": [{"role": "user", "content": "Hello! What is 2+2?"}],
    "max_tokens": 100
  }'
```

**Step 4: Integrate with AI Orchestrator**

```bash
# Restart orchestrator to load vLLM provider
docker-compose restart ai-orchestrator

# Or if running locally:
poetry run uvicorn src.api.main:app --reload
```

**Step 5: Test Integration**

```bash
# Test vLLM through orchestrator
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "@vllm: What is the capital of France?",
    "session_id": "test-vllm-integration"
  }'

# Check provider health
curl http://localhost:8000/api/health

# Expected to see vllm provider as healthy
```

### Method 2: Native Installation (Advanced)

For maximum performance without containerization:

```bash
# Install vLLM
pip install vllm

# Start server
vllm serve meta-llama/Llama-2-13b-chat-hf \
  --host 0.0.0.0 \
  --port 8001 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.9

# Or with more options
vllm serve meta-llama/Llama-2-13b-chat-hf \
  --host 0.0.0.0 \
  --port 8001 \
  --tensor-parallel-size 2 \
  --gpu-memory-utilization 0.95 \
  --max-model-len 4096 \
  --enable-prefix-caching \
  --swap-space 4 \
  --trust-remote-code
```

---

## Model Selection

### Recommended Models

| Model | Use Case | VRAM | Context | Speed |
|-------|----------|------|---------|-------|
| **Llama 2 7B Chat** | General chat | 7GB | 4K | Fast |
| **Llama 2 13B Chat** | General chat (better quality) | 13GB | 4K | Medium |
| **CodeLlama 13B Instruct** | Code generation | 13GB | 16K | Medium |
| **Mistral 7B Instruct** | General instruct tasks | 7GB | 8K | Fast |
| **DeepSeek Coder 33B** | Advanced code (multi-GPU) | 33GB | 16K | Slow |

### Downloading Models

Models are automatically downloaded on first use, but you can pre-download:

```bash
# Using HuggingFace CLI
pip install huggingface-hub
huggingface-cli download meta-llama/Llama-2-13b-chat-hf

# Or using Python
from huggingface_hub import snapshot_download
snapshot_download("meta-llama/Llama-2-13b-chat-hf")
```

### Gated Models (Llama, CodeLlama)

Some models require HuggingFace authentication:

1. Create account at https://huggingface.co
2. Request access to gated model (e.g., Llama 2)
3. Create access token: https://huggingface.co/settings/tokens
4. Set `HF_TOKEN` environment variable

```bash
export HF_TOKEN=hf_your_token_here
# Or add to .env.vllm file
```

---

## Performance Tuning

### GPU Memory Optimization

```bash
# Conservative (safe for shared GPU)
VLLM_GPU_MEMORY=0.7

# Balanced (recommended)
VLLM_GPU_MEMORY=0.9

# Aggressive (max performance, dedicated GPU)
VLLM_GPU_MEMORY=0.95
```

### Multi-GPU Configuration

For models larger than single GPU memory:

```yaml
environment:
  - VLLM_TENSOR_PARALLEL_SIZE=2  # Split across 2 GPUs
  - NVIDIA_VISIBLE_DEVICES=0,1   # Use GPU 0 and 1
```

```bash
# Check GPU utilization
nvidia-smi -l 1  # Update every second

# Verify both GPUs are used
docker exec ai-orchestrator-vllm nvidia-smi
```

### Throughput Optimization

**Prefix Caching** (for repeated prompts):
```bash
VLLM_PREFIX_CACHE=true
```

**Increase Batch Size** (for high concurrency):
```bash
# In docker-compose.vllm.yml command:
--max-num-batched-tokens 8192
--max-num-seqs 256
```

**Swap Space** (trade memory for latency):
```bash
# Offload some KV cache to CPU RAM
VLLM_SWAP_SPACE=8  # 8GB swap
```

### Benchmarking

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test throughput (10 concurrent requests, 100 total)
ab -n 100 -c 10 -p request.json -T "application/json" \
  http://localhost:8001/v1/chat/completions

# request.json content:
# {"model":"meta-llama/Llama-2-13b-chat-hf","messages":[{"role":"user","content":"Hello"}]}
```

---

## Troubleshooting

### Issue: Out of Memory (OOM)

**Symptoms:**
- Container crashes with "CUDA out of memory"
- `nvidia-smi` shows 100% memory usage

**Solutions:**
```bash
# 1. Reduce GPU memory utilization
VLLM_GPU_MEMORY=0.7  # Instead of 0.9

# 2. Use smaller model
VLLM_MODEL=meta-llama/Llama-2-7b-chat-hf  # Instead of 13B

# 3. Reduce max sequence length
VLLM_MAX_LEN=2048  # Instead of 4096

# 4. Enable CPU swap
VLLM_SWAP_SPACE=8
```

### Issue: Slow Startup (Model Loading)

**Solutions:**
```bash
# 1. Pre-download models
docker-compose -f docker-compose.vllm.yml --profile download up vllm-model-downloader

# 2. Mount local model cache
# In docker-compose.vllm.yml:
volumes:
  - /path/to/local/models:/root/.cache/huggingface

# 3. Use SSD storage for model cache
```

### Issue: Low Throughput

**Check:**
```bash
# Monitor GPU utilization
nvidia-smi dmon -s u

# Should be 80-100% during inference
# If low (<50%), check:
```

**Solutions:**
```bash
# 1. Increase GPU memory
VLLM_GPU_MEMORY=0.95

# 2. Enable prefix caching
VLLM_PREFIX_CACHE=true

# 3. Increase batch size
--max-num-batched-tokens 8192

# 4. Check CPU bottleneck
htop  # Should not be at 100%
```

### Issue: Connection Refused

**Check:**
```bash
# 1. Verify container is running
docker ps | grep vllm

# 2. Check logs
docker logs ai-orchestrator-vllm

# 3. Verify port binding
docker port ai-orchestrator-vllm

# 4. Test inside container
docker exec ai-orchestrator-vllm curl localhost:8001/v1/models
```

### Issue: Model Not Found

**Solutions:**
```bash
# 1. Check HuggingFace authentication (for gated models)
echo $HF_TOKEN

# 2. Manually download model
huggingface-cli download meta-llama/Llama-2-13b-chat-hf

# 3. Check disk space
df -h

# 4. Verify model name (case-sensitive)
# Correct: meta-llama/Llama-2-13b-chat-hf
# Wrong: Meta-Llama/llama-2-13b-chat-hf
```

---

## Monitoring

### Logs

```bash
# Real-time logs
docker-compose -f docker-compose.vllm.yml logs -f vllm

# Last 100 lines
docker-compose -f docker-compose.vllm.yml logs --tail 100 vllm

# Search logs
docker logs ai-orchestrator-vllm 2>&1 | grep "error"
```

### Metrics

**GPU Metrics:**
```bash
# Real-time monitoring
watch -n 1 nvidia-smi

# GPU utilization over time
nvidia-smi dmon -s puct -c 60  # 60 samples, 1/sec
```

**vLLM Metrics:**
```bash
# Request statistics (from vLLM logs)
docker logs ai-orchestrator-vllm 2>&1 | grep "request"

# Throughput (tokens/second)
docker logs ai-orchestrator-vllm 2>&1 | grep "throughput"
```

**AI Orchestrator Metrics:**
```bash
# Provider statistics
curl http://localhost:8000/api/models/statistics

# Health check
curl http://localhost:8000/api/health | jq '.providers.vllm'
```

### Prometheus Integration

vLLM exposes Prometheus metrics at `/metrics`:

```bash
# Check metrics endpoint
curl http://localhost:8001/metrics

# Add to monitoring-hub prometheus.yml:
scrape_configs:
  - job_name: 'vllm'
    static_configs:
      - targets: ['ai-orchestrator-vllm:8001']
```

---

## Production Deployment Checklist

- [ ] GPU drivers installed and verified (nvidia-smi)
- [ ] nvidia-docker2 installed and tested
- [ ] Models pre-downloaded to avoid cold start delays
- [ ] Environment variables configured in .env.vllm
- [ ] Resource limits set appropriately in docker-compose
- [ ] Health checks configured and passing
- [ ] Monitoring and logging enabled
- [ ] Backup plan for GPU failure (fallback to Ollama or paid APIs)
- [ ] Load testing performed with expected traffic
- [ ] Documentation updated with deployment specifics

---

## Next Steps

After successfully setting up vLLM:

1. **Test Different Models**: Experiment with model selection for your use case
2. **Optimize Performance**: Tune GPU memory and throughput settings
3. **Integrate Monitoring**: Add vLLM metrics to Grafana dashboards
4. **Enable in Production**: Update routing to prioritize vLLM for production workloads

For more information:
- vLLM Documentation: https://docs.vllm.ai/
- HuggingFace Models: https://huggingface.co/models
- AI Orchestrator: /docs/README.md

---

**Last Updated:** 2025-11-28
**Enhancement:** 017 - Production Architecture - Phase 1
**Status:** Complete
