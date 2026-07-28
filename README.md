# TwinGuard: Confidential AI Inference at Scale

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![IEEE TDSC](https://img.shields.io/badge/Target-IEEE%20TDSC-blue)](https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=8858)
[![DOI](https://img.shields.io/badge/DOI-pending-lightgrey)]()
[![GitHub](https://img.shields.io/badge/GitHub-ufxa%2Ftee--llm--inference-black?logo=github)](https://github.com/ufxa/tee-llm-inference)

**A TEE-Based Framework for Privacy-Preserving Large Language Model Deployment in Regulated Cloud Environments**

> Submitted to IEEE Transactions on Dependable and Secure Computing (TDSC, IF 7.3)

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

**Key results (simulated, 1.2M requests, seed=42):**
- CIS: 0.921 ± 0.012 (TwinGuard-TDX) vs 0.431 (TLS-only baseline)
- Latency overhead: 12.3% (TDX), 8.9% (SEV-SNP), 14.7% (SGX)
- GDPR compliance coverage: 98.7%; HIPAA: 97.3%
- Throughput: 847 req/s at 500 concurrent clients

---

## Repository Structure

```
tee-llm-inference/
├── README.md
├── paper/
│   ├── main.tex              # LaTeX source (IEEEtran)
│   └── references.bib        # Bibliography (50 entries)
├── src/
│   ├── agents/               # Agent implementations
│   ├── metrics/              # CIS metric implementation
│   └── evaluation/           # Evaluation scripts
├── data/
│   ├── processed/            # Processed workload traces
│   └── results/              # Simulation results (CSV/JSON)
├── notebooks/                # Jupyter notebooks for figures
├── scripts/
│   └── build.sh              # tectonic main.tex
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

### Run the Simulation

```bash
cd src/evaluation
python simulate_twinguard.py --rounds 10 --requests 120000 --seed 42
```

Results are written to `data/results/`.

---

## How to Cite

```bibtex
@article{costa2026twinguard,
  author  = {Costa, Allan Douglas},
  title   = {Confidential {AI} Inference at Scale: A {TEE}-Based Framework
             for Privacy-Preserving Large Language Model Deployment
             in Regulated Cloud Environments},
  journal = {IEEE Transactions on Dependable and Secure Computing},
  year    = {2026},
  note    = {Submitted}
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

CIS in [0, 1]. Values >= 0.90 recommended for regulated-sector deployment.

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
