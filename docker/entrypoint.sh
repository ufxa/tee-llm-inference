#!/usr/bin/env bash
set -Eeuo pipefail

command_name="${1:-serve}"
MODEL_PATH="${MODEL_PATH:-/workspace/models/llama-2-7b-gptq}"
MODEL_ID="${MODEL_ID:-}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-Llama-2-7B-GPTQ}"
VLLM_HOST="${VLLM_HOST:-0.0.0.0}"
VLLM_PORT="${VLLM_PORT:-8000}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.80}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-2048}"

download_model() {
    if [[ -f "$MODEL_PATH/config.json" ]]; then
        echo "[TwinGuard] Modelo encontrado em $MODEL_PATH"
        return 0
    fi

    if [[ -z "$MODEL_ID" ]]; then
        echo "[TwinGuard] MODEL_ID não foi definido e o modelo não está instalado." >&2
        echo "Defina MODEL_ID e, se necessário, HF_TOKEN; ou monte o modelo em $MODEL_PATH." >&2
        exit 2
    fi

    mkdir -p "$MODEL_PATH"
    hf_args=(download "$MODEL_ID" --local-dir "$MODEL_PATH")
    if [[ -n "${HF_TOKEN:-}" ]]; then
        hf_args+=(--token "$HF_TOKEN")
    fi

    echo "[TwinGuard] Baixando $MODEL_ID para $MODEL_PATH"
    hf "${hf_args[@]}"
}

case "$command_name" in
    shell)
        exec bash
        ;;
    download)
        download_model
        ;;
    check)
        python - <<'PY'
import torch
print("CUDA disponível:", torch.cuda.is_available())
if torch.cuda.is_available():
    props = torch.cuda.get_device_properties(0)
    print("GPU:", props.name)
    print("VRAM GB:", round(props.total_memory / 1024**3, 2))
PY
        vllm --version
        nvidia-smi
        ;;
    serve)
        download_model
        echo "[TwinGuard] Iniciando vLLM"
        echo "[TwinGuard] Modelo: $MODEL_PATH"
        echo "[TwinGuard] Endpoint: http://$VLLM_HOST:$VLLM_PORT"
        echo "[TwinGuard] GPU memory utilization: $GPU_MEMORY_UTILIZATION"
        echo "[TwinGuard] Max model length: $MAX_MODEL_LEN"
        exec vllm serve "$MODEL_PATH" \
            --served-model-name "$SERVED_MODEL_NAME" \
            --host "$VLLM_HOST" \
            --port "$VLLM_PORT" \
            --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
            --max-model-len "$MAX_MODEL_LEN"
        ;;
    *)
        exec "$@"
        ;;
esac
