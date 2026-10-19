# Proveniência local dos experimentos RTX 5090 na Vast.ai

Este documento reúne somente informações encontradas nos artefatos locais e no
launcher versionado do projeto. Itens marcados como ausentes não devem ser
reconstruídos como se fossem logs históricos.

## 1. Ambiente declarado nos registros locais

| Campo | Valor | Evidência/status |
|---|---|---|
| Provedor | Vast.ai | declaração do manuscrito e manifesto local |
| GPU | NVIDIA RTX 5090, 32 GB | declaração do manuscrito/contexto; sem dump bruto de `nvidia-smi` |
| CPU | AMD EPYC 7R32, 192 threads lógicas | declaração do manuscrito/contexto; sem dump bruto de `lscpu` |
| Sistema | Ubuntu 22.04 LTS | especificação de ambiente registrada |
| Kernel | Linux 5.15.0 | especificação de ambiente registrada |
| CUDA | 12.8.1 | especificação de ambiente registrada |
| PyTorch | 2.9.0 com CUDA 12.8 | especificação de ambiente registrada |
| vLLM | 0.11.1 | especificação/Dockerfile local; não há `pip freeze` histórico da Vast |
| Modelo | LLaMA-2-7B GPTQ 4-bit | manifests e resultados |
| Caminho do modelo | `/workspace/models/llama-2-7b-gptq` | Dockerfile/launcher local |
| Endpoint | `http://127.0.0.1:8000/v1/completions` | manifesto final |

## 2. Configuração registrada do benchmark final

| Campo | Valor |
|---|---:|
| Requisições totais | 1.200.000 |
| Rodadas | 10 |
| Requisições por rodada | 120.000 |
| Concorrência | 16 |
| Batch size | 1024 |
| Máximo de tokens de saída | 128 |
| Temperatura | 0.0 |
| Timeout | 120 s |
| Seed | 42 |
| Comprimento das consultas | 50–512 tokens, distribuição uniforme inclusiva |
| Dataset SHA-256 | `74970d84b886a4a388100db125155a80972492f846e16ec00c4acf6d8f3f260e` |
| TEE físico | Não; `hardware_tee_execution: false` |
| Data de criação do manifesto | 2026-10-06 23:32:41 UTC |

## 3. Resultado final registrado

- Requisições processadas: **1.200.000**
- Sucessos: **1.200.000**
- Falhas: **0**
- Taxa de sucesso: **100%**
- Latência média: **1.131,522875977 ms**
- Throughput agregado: **aproximadamente 14,1168 requisições/s**
- Duração agregada: **aproximadamente 23,61 horas**
- Dez rodadas concluídas integralmente.

O arquivo de resumo contém as métricas por rodada, incluindo média, p50, p95,
p99, throughput e tokens/s.

## 4. Launcher local versionado

O `docker/entrypoint.sh` registra o seguinte padrão de inicialização:

```text
vllm serve /workspace/models/llama-2-7b-gptq \
  --served-model-name Llama-2-7B-GPTQ \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.80 \
  --max-model-len 2048
```

Esse é o comando definido pelo launcher local e deve ser descrito como
**configuração de lançamento versionada**. Não há no arquivo local um terminal
histórico comprovando que essa linha exata foi digitada manualmente na Vast.

## 5. Arquivos locais que sustentam os resultados

- Manifesto de proveniência: `data/results/vast_baseline_manifest.md`
- Manifesto desta consolidação: `data/results/vast_provenance_local_records.md`
- Manifesto da execução final: `artifacts/rtx5090/final-results/data/results/rtx5090/full-1.2m/workload-rtx5090-1.2m-c16/run_manifest.json`
- Resumo final: `artifacts/rtx5090/final-results/data/results/rtx5090/full-1.2m/workload-rtx5090-1.2m-c16/summary.json`
- Metadados do servidor: `artifacts/rtx5090/final-results/data/results/rtx5090/vllm-rtx5090-full-20261006T212346Z/metadata.json`
- Arquivo final de resultados: `artifacts/rtx5090/final-results/rtx5090-all-final-results.tar.gz`

SHA-256 do arquivo final de resultados:

```text
e56fa09418bb2ad3527704db66efc091df7f5c6af851af9de1d164d4ff14e3a0
```

## 6. Informações que não foram encontradas localmente

- dump completo de `nvidia-smi`;
- dump completo de `lscpu`;
- UUID da GPU;
- identificador da instância Vast;
- log bruto de inicialização do vLLM;
- `pip freeze` capturado durante a execução;
- checksum dos arquivos do modelo;
- comando histórico completo usado para iniciar o container;
- vínculo criptográfico entre cada resultado e um commit específico do código.

## 7. Formulação editorial recomendada

> The physical RTX 5090 baseline is supported by local workload manifests,
> per-round metrics, raw samples, dataset hashes, and a versioned container
> launcher. However, the archived package does not include the original
> `nvidia-smi` dump, `pip freeze`, provider instance identifier, or raw vLLM
> startup transcript. Therefore, the baseline is reported as a documented
> physical run with partial provenance, while TDX, SGX, and SEV-SNP remain
> modeled rather than physically attested executions.
