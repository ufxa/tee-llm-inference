# Reproducibility guide

## What this release reproduces

This release supports independent verification of the reported non-TEE RTX
5090 baseline from its archived per-request traces and reproduction of the
trace-driven TEE projections, CIS analysis, and derived figures. It does not
claim to reproduce a physical SGX, TDX, or SEV-SNP deployment.

The historical inference service was a vLLM OpenAI-compatible endpoint bound
to `127.0.0.1:8000` inside the benchmark instance. It was an execution-local
endpoint, not a public service, and is not expected to remain online.

## Release contents

- `data/raw/rtx5090/`: non-TEE traces, round metrics, summaries, calibration
  outputs, and workload manifests.
- `data/results/`: checked-in projection outputs and provenance notes.
- `src/evaluation/`: projection, sensitivity, and figure-generation scripts.
- `paper/`: IEEE Access manuscript source and figures.
- `data/SHA256SUMS`: integrity snapshot for raw and derived data.

## Software requirements

The projection and figure scripts require Python 3.10 or newer and the
packages pinned in `requirements.txt`.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

The archived physical run used Ubuntu 22.04, CUDA 12.8.1, PyTorch 2.9.0, and
vLLM 0.11.1. Those components are not required to reproduce the projections
from the archived traces. `Dockerfile` documents an optional environment for
recreating a comparable serving setup, but it does not recreate the historical
instance or establish a physical TEE result.

## Verify and reproduce

Run these commands from the repository root:

```bash
sha256sum -c data/SHA256SUMS
python src/evaluation/project_twinguard_trace.py --draws 4000 --seed 42
python src/evaluation/cis_weight_sensitivity.py
python src/evaluation/generate_figure4_latency.py
python src/evaluation/generate_figure5_cis.py
python src/evaluation/generate_figure6_scalability.py
python src/evaluation/generate_figure7_uncertainty.py
```

The commands write derived JSON/CSV files to `data/results/` and figures to
`paper/imagens/`. Review the resulting Git diff before retaining regenerated
outputs.

## Evidence limits

The physical baseline is supported by preserved traces, manifests, summaries,
and hashes. The complete launch command, provider job record, runtime package
dump, GPU/CPU inspection output, model checksum, and server-start log were not
archived. These missing artifacts prevent an independent clean-environment
rerun of the exact historical GPU benchmark. The detailed provenance record is
in `data/results/vast_baseline_manifest.md`.

All SGX, TDX, and SEV-SNP values in the manuscript are trace-driven
projections using literature-derived overhead ranges. They are not hardware
measurements.

## Before publishing a GitHub release

1. Run the integrity command above and retain its output.
2. Confirm that no credentials, provider tokens, model weights, or personal
   data have entered the staged files.
3. Commit the raw traces, derived results, scripts, manifests, this guide, and
   `data/SHA256SUMS` together.
4. Create and publish an annotated Git tag tied to the manuscript version.
5. Select an explicit repository/data license before making the release public.
