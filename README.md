# TwinGuard: Confidential AI Inference at Scale

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![IEEE Access](https://img.shields.io/badge/Target-IEEE%20Access-blue)](https://ieeeaccess.ieee.org)
[![DOI](https://img.shields.io/badge/DOI-pending-lightgrey)]()
[![GitHub](https://img.shields.io/badge/GitHub-ufxa%2Ftee--llm--inference-black?logo=github)](https://github.com/ufxa/tee-llm-inference)

**Confidential AI Inference at Scale: A TEE-Based Framework for Large Language Models in Regulated Cloud Environments, with a Trace-Driven Projection over 1.2 Million Real Requests**

> Prepared for submission to IEEE Access

---

## Abstract

Large language models are increasingly deployed in regulated sectors, yet
existing cloud inference pipelines expose sensitive data to untrusted
infrastructure operators. TwinGuard is a three-layer framework for confidential
LLM inference at scale, coordinating an Attestation Agent, Inference Agent, and
Audit Agent within hardware-isolated TEE boundaries (Intel TDX, AMD SEV-SNP,
Intel SGX). We introduce the Confidential Inference Score (CIS), a novel
composite metric quantifying the joint privacy, attestation freshness, overhead,
and regulatory compliance posture of a confidential inference deployment.

**Key results:**
- Physical benchmark (no TEE): 1.2M real requests (Llama-2-7B GPTQ, vLLM) on an NVIDIA RTX 5090, 0 failures, 1,131.52 ms mean latency, 14.12 req/s; per-request traces in `data/raw/rtx5090/`
- Trace-driven TEE projection, overheads from measured literature ranges (Chrapek et al. 2025; Misono et al. 2024), 4,000 Monte Carlo draws:
  - projected mean latency 1,201 ms (SGX), 1,231 ms (TDX), 1,242 ms (SEV-SNP)
  - CIS 0.928 (SGX), 0.921 (TDX), 0.918 (SEV-SNP); TLS-only 0.288, plaintext 0.250
  - ranking uncertain: SGX ranks first in 74% of draws
- Attestation with freshness-aware caching at the measured rate: 99.33% cache hits, 0.66% of latency
- Design-level technical-control coverage: 93.8% (7.5/8) vs. 25.0% (2/8) for TLS-only

No SGX, TDX or SEV-SNP hardware was executed. All TEE values are projections
from the measured traces; coverage values are technical mappings, not legal
compliance certifications.

---

## Repository Structure

```
tee-llm-inference/
├── README.md
├── paper/
│   ├── main.tex              # IEEE Access LaTeX source
│   ├── references.bib        # Bibliography
│   └── imagens/              # Figures and author biographies
├── src/
│   └── evaluation/           # Projection and figure-generation scripts
├── data/
│   ├── raw/rtx5090/          # Baseline traces and manifests
│   └── results/              # Derived results (CSV/JSON)
├── REPRODUCIBILITY.md        # Release scope, checks, and limitations
├── requirements.txt          # Reproduction dependencies
└── LICENSE
```

> **Note:** `codeA100/` (remote GPU server scripts) is excluded from
> this repository via `.gitignore` for security reasons.

---

## Reproducing the Paper

### Build the PDF

Requires [tectonic](https://tectonic-typesetting.github.io):

```bash
./scripts/build.sh
# or directly:
cd paper && tectonic main.tex
```

### Reproduce the results and figures

```bash
python src/evaluation/project_twinguard_trace.py      # trace-driven TEE projection
python src/evaluation/cis_weight_sensitivity.py       # CIS weight sweep
python src/evaluation/generate_figure4_latency.py
python src/evaluation/generate_figure5_cis.py
python src/evaluation/generate_figure6_scalability.py
python src/evaluation/generate_figure7_uncertainty.py
```

Inputs: the measured traces in `data/raw/rtx5090/` (10 rounds x 120,000
requests, plus the calibration sweep). Outputs go to `data/results/` and
`paper/output/raster/`. The earlier parameterized simulator is kept in
`src/evaluation/legacy/` for history only and is not used by the paper.

Before submission, the repository will be tagged with the manuscript version.
The tag will include the raw baseline traces, manifests, source hashes, derived
results, and all scripts required to reproduce the trace-driven projection. No
physical TEE measurements are claimed or included.

See `REPRODUCIBILITY.md` for the reproduction boundary and `data/README.md`
for the data inventory and integrity checks.

---

## How to Cite

```bibtex
@article{barbosa2026twinguard,
  author  = {Barbosa, Carlos Lucas Vieira and de Souza Junior, Jos\'{e} and Costa, Allan Douglas},
  title   = {Confidential {AI} Inference at Scale: A {TEE}-Based Framework for
             Large Language Models in Regulated Cloud Environments, with a
             Trace-Driven Projection over 1.2 Million Real Requests},
  journal = {IEEE Access},
  year    = {2026},
  note    = {Under preparation}
}
```

---

## Novel Metric: Confidential Inference Score (CIS)

The CIS combines four sub-scores:

```
CIS(q) = 0.35 * PG(q)        # Privacy Guarantee (differential privacy strength)
        + 0.25 * AF(q)        # Attestation Freshness (exponential decay)
        + 0.25 * (1 - OP(q)) # Overhead Penalty (normalized latency overhead)
        + 0.15 * CS(q)        # Compliance Score (GDPR/HIPAA coverage fraction)
```

CIS in [0, 1]. The value 0.90 is an illustrative decision threshold within
the proposed model, not a regulatory or deployment certification threshold.

---

## Author

**Allan Douglas Costa**, Ph.D.
Professor, UFRA — Federal Rural University of the Amazon
ICIBE Institute | LICA Laboratory | CCAD-IA
ORCID: 0000-0002-7068-8889
Email: allan.costa@ufra.edu.br

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Acknowledgments

Partially supported by FAPESPA, PRODEPA, SEC365 Cybersecurity Solutions,
LICA, CCAD-IA, RNP, and INCT iAmazonia.
