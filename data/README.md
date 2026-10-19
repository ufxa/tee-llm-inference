# Data package

This directory contains the evidence used by the TwinGuard manuscript and the
derived outputs used to produce its reported trace-driven projections.

## Scope and provenance

`raw/rtx5090/` preserves the completed non-TEE RTX 5090 benchmark. The full
run contains 1,200,000 requests in ten rounds at concurrency 16; the
`calibration/` subtree contains ten 1,000-request runs for each concurrency
level 1, 2, 4, 8, and 16. The endpoint was local to the historical execution
environment and is no longer expected to be reachable.

The workload manifest records a synthetic 42-token pool, deterministic seeds,
and no personal data. No physical TEE execution, attestation measurement, or
GPU confidential-computing measurement is contained in this package.

## Layout

| Path | Contents | Role |
| --- | --- | --- |
| `raw/rtx5090/full-1.2m-c16/` | Per-request compressed traces, round metrics, run manifest, and summary | Physical non-TEE baseline |
| `raw/rtx5090/calibration/` | Concurrency calibration traces and summaries | Figure 6 and scalability context |
| `raw/rtx5090/twinguard-1.2m.manifest.json` | Workload, tokenizer, seed, and hash metadata | Workload provenance |
| `results/` | Trace-driven projection, CIS sensitivity, comparison, and provenance files | Derived manuscript results |
| `SHA256SUMS` | SHA-256 snapshot for files under `raw/` and `results/` | Integrity verification |

## Integrity check

From the repository root, verify the released snapshot with:

```bash
sha256sum -c data/SHA256SUMS
```

The checksum file is a release snapshot. Regenerate it only when intentionally
changing raw data or a checked-in derived result.

## Reproduction boundary

The scripts can reproduce the trace-driven projections from the archived
traces. They do not recreate the historical GPU execution: the original
Vast.ai instance, launch transcript, and complete runtime dump are not part of
this repository. See `REPRODUCIBILITY.md` and
`results/vast_baseline_manifest.md` for the remaining provenance limitations.
