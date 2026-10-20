# Vast.ai physical baseline — provenance manifest

## Status

This file records the provenance boundary for the physical RTX 5090 baseline.
The supplied artifact directory has now been inspected and contains the full
workload traces, per-round metrics, calibration runs, CPU ablation runs, and
archive hashes. It still does not contain a complete hardware/runtime dump or
the exact launch transcript, so independent reproduction is not yet complete.

## Values currently declared by the manuscript

| Field | Declared value | Status |
|---|---|---|
| Provider | Vast.ai | Reported in `paper/main.tex` |
| GPU | NVIDIA RTX 5090, 32 GB | Reported in `paper/main.tex` |
| CPU | AMD EPYC 7R32, up to 192 threads | Reported in `paper/main.tex` |
| Model | LLaMA-2-7B, GPTQ 4-bit | Reported in `paper/main.tex` |
| Serving | vLLM 0.11.1 | Recorded in the supplied Vast.ai environment specification; raw package dump is not in the final archive |
| Requests | 1,200,000 over 10 rounds × 120,000 | Reported in `paper/main.tex` |
| Successes | 1,200,000; zero failures | Reported in `paper/main.tex` |
| Mean latency | 1,131.52 ms | Reported in `paper/main.tex` |
| Mean throughput | Approximately 14.12 req/s | Reported in `paper/main.tex` |
| CPU-thread ablation | 16, 32, 64 and 192 threads | Reported in `paper/main.tex` |
| TEE status | No physical TDX, SGX or SEV-SNP execution/attestation reported | Explicit boundary in `paper/main.tex` |

## Runtime artifacts still missing after inspection

- [ ] exact command and launch configuration;
- [ ] Vast instance identifier/provider job record;
- [ ] raw `nvidia-smi`, `lscpu`, OS, CUDA-driver, GPU UUID and RAM dump (the supplied environment specification records Ubuntu 22.04, kernel 5.15.0, CUDA 12.8.1, driver check and RAM check);
- [ ] model-file checksum and vLLM server startup log;
- [ ] runtime package/environment manifest (`pip freeze` or equivalent);
- [ ] explanation of the empty-PID `taskset` messages in the CPU ablation log;
- [ ] explicit binding between the final artifacts and the source commit.

The raw workload samples, per-round reports, generator manifests, seeds and
archive hashes are present in the supplied artifact directory. The remaining
items above are the provenance gaps that prevent a clean-environment rerun and
independent attribution to a specific Vast instance.

## Artifact package inspected

Root inspected:

The original RTX 5090 artifact package retrieved from the Vast.ai instance
(the curated subset is published under `data/raw/rtx5090/`).

The root contains 633 files and is approximately 778 MB: 363 JSON files, 250
compressed sample files, 13 CSV files, and 7 log files. The preferred result
tree is `final-results/`; `all-results/` and `current/` contain duplicated or
intermediate copies.

The final 1.2M run is under
`final-results/data/results/rtx5090/full-1.2m/`. Its manifest records
concurrency 16, batch size 1024, max output 128, temperature 0, timeout 120 s,
seed 42, the local OpenAI-compatible endpoint, and the canonical workload hash.
Its summary records 1,200,000/1,200,000 successful requests, zero failures,
mean latency 1,131.522875977 ms, latency SD 64.833960742 ms, and ten completed
rounds. Aggregated elapsed-time throughput is 14.1168 requests/s, which justifies
the manuscript's rounded 14.12 requests/s.

The package also contains:

- the canonical workload manifest with 50--512 token queries, seed streams
  42/43/44, a 960,000/240,000 evaluation/ablation split, and dataset SHA-256
  `74970d84b886a4a388100db125155a80972492f846e16ec00c4acf6d8f3f260e`;
- ten 1,000-request calibration runs at concurrency 1, 2, 4, 8, and 16;
- CPU-thread ablations at 16, 32, 64, and 192 threads, all with 100% success;
- raw `.samples.jsonl.gz` files for the full run, calibration, and ablation;
- a modeled TEE output that explicitly records `hardware_execution: false`.

## Important distinctions and inconsistencies

The final package contains two physical baselines. The full 1.2M run has mean
latency 1,131.522875977 ms. The separate 1,000-request calibration at
concurrency 16 has mean latency 1,119.204381419 ms and SD 148.101092249 ms;
`modeled_tee_overheads_rtx5090_c16_seed42.json` uses the latter as its model
input and reports only modeled TEE overheads. It is not a TEE measurement.

The public CIS simulator in the main repository uses a separate normalized
model latency of 47.3 ms mean and 2.1 ms spread. These model/data paths must
remain separate in the paper.

The supplied Vast.ai environment specification identifies Ubuntu 22.04 LTS,
Linux kernel 5.15.0, CUDA 12.8.1, PyTorch 2.9.0 with CUDA 12.8, and vLLM
0.11.1. The vLLM metadata contains a stale `evaluation_type` label inherited from an
earlier benchmark template; the system label is `RTX5090-vLLM`, and all runs
were executed on the RTX 5090. The artifact set does not record the vLLM package version. The
raw final-run package dump is still absent, so the 0.11.1 value is an
environment specification rather than a version string emitted by the final
run metadata. The manuscript now uses vLLM 0.11.1 consistently.

The artifact set also lacks direct runtime hardware inspection. The RTX 5090
and EPYC 7R32 labels are present in the manuscript/context, but no `nvidia-smi`,
`lscpu`, GPU UUID, OS, CUDA-driver, RAM, Vast instance ID, or provider job
record was archived.

Finally, `cpu_ablation.log` records `taskset: invalid PID argument: ''` for
each setting before changing affinity for `engine_pid=4440`. The ablation
outputs completed successfully, but the process-affinity target must be
explained before making a strong CPU-isolation claim.

## Archive hashes

| Bundle | SHA-256 |
|---|---|
| `dataset/twinguard-canonical-dataset.tar.gz` | `7768305ecc058e046659e5ef7ca29554b9bd1d714f2f06f377a160bcbff30db5` |
| `final-results/rtx5090-all-final-results.tar.gz` | `e56fa09418bb2ad3527704db66efc091df7f5c6af851af9de1d164d4ff14e3a0` |
| `all-results/rtx5090-results.tar.gz` | `8f0188df6a43d3f363d4221aa10819175cc3a1a3d86b8c86fde515041c57e8e6` |
| `cpu-ablation/rtx5090-cpu-ablation.tar.gz` | `8e7a8f78fa9b085a30394a32095b6ff05b1d00151b35db51a9282296ec3d2082` |

The benchmark worktree resolves to source revision
`c27e16befb8d7ff2d883ffe81f93f43642792e13`, but it contains uncommitted
benchmark-script changes; the exact source revision used for each result is
not independently bound by the run manifests.
