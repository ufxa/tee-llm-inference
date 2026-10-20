FROM nvidia/cuda:12.8.1-base-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive

ENV TZ=UTC \
    DEBIAN_FRONTEND=noninteractive \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    HF_HOME=/workspace/.cache/huggingface \
    TRANSFORMERS_CACHE=/workspace/.cache/huggingface \
    MODEL_PATH=/workspace/models/llama-2-7b-gptq \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    git-lfs \
    htop \
    tini \
    tmux \
    wget \
    python3.10 \
    python3.10-dev \
    python3.10-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install --system

RUN ln -sf /usr/bin/python3.10 /usr/local/bin/python \
    && ln -sf /usr/bin/python3.10 /usr/local/bin/python3 \
    && python -m venv "$VIRTUAL_ENV" \
    && python -m pip install --no-cache-dir --upgrade pip setuptools wheel

# CUDA 12.8 wheels are required for the RTX 5090/Blackwell architecture.
RUN python -m pip install --no-cache-dir \
    torch==2.9.0 \
    --index-url https://download.pytorch.org/whl/cu128

# vLLM is pinned to the version used by the reproducible benchmark worktree.
RUN python -m pip install --no-cache-dir \
    vllm==0.11.1 \
    huggingface_hub==0.36.2 \
    numpy==2.2.6 \
    scipy==1.15.3 \
    pandas \
    scikit-learn \
    safetensors \
    sentencepiece \
    transformers \
    accelerate \
    openai

RUN mkdir -p /workspace/models /workspace/.cache/huggingface /workspace/twinguard

COPY docker/entrypoint.sh /usr/local/bin/twinguard-entrypoint
RUN chmod +x /usr/local/bin/twinguard-entrypoint

COPY src /workspace/twinguard/src
COPY data /workspace/twinguard/data
COPY README.md /workspace/twinguard/README.md

WORKDIR /workspace/twinguard

EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/twinguard-entrypoint"]
CMD ["serve"]
