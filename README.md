# TwinGuard: Confidential AI Inference at Scale

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Target](https://img.shields.io/badge/Target-IEEE%20Access-blue)](https://ieeeaccess.ieee.org)
[![DOI](https://img.shields.io/badge/DOI-pending-lightgrey)]()
[![GitHub](https://img.shields.io/badge/GitHub-ufxa%2Ftee--llm--inference-black?logo=github)](https://github.com/ufxa/tee-llm-inference)

## A TEE-Based Framework for Large Language Models in Regulated Cloud Environments, with a Trace-Driven Projection over 1.2 Million Real Requests

Prepared for submission to *IEEE Access* as a Research Article.

## Abstract

Large language models are increasingly deployed in regulated sectors, yet
existing cloud-inference pipelines expose sensitive data to untrusted
infrastructure operators. TwinGuard is a three-layer framework for
confidential LLM inference at scale, coordinating an Attestation Agent,
Inference Agent, and Audit Agent within hardware-isolated TEE boundaries
(Intel TDX, AMD SEV-SNP, and Intel SGX). We introduce the Confidential
Inference Score (CIS), a composite metric that combines privacy,
attestation freshness, overhead, and technical-control coverage.

### Key results

- **Physical baseline:** 1.2 million real requests to Llama-2-7B GPTQ through
  vLLM on an NVIDIA RTX 5090; 1,131.52 ms mean latency and 14.12 req/s.
- **Trace-driven TEE projections:** 4,000 Monte Carlo draws yield projected
  means of 1,201 ms (SGX), 1,231 ms (TDX), and 1,242 ms (SEV-SNP).
- **CIS:** 0.928 (SGX), 0.921 (TDX), and 0.918 (SEV-SNP), versus 0.288 for the
  TLS-only baseline.
- **Attestation cache:** 99.33% measured cache-hit rate; attestation accounts
  for 0.66% of projected latency.
- **Technical-control coverage:** 93.8% (7.5/8 controls) for TwinGuard versus
  25.0% (2/8) for TLS-only.

> **Important:** no SGX, TDX, or SEV-SNP hardware was executed. All TEE
> values are trace-driven projections calibrated from the measured baseline
> and published overhead ranges; they are not physical TEE measurements or
> legal compliance certifications.

## Repository Structure

```text
tee-llm-inference/
├── README.md
├── LICENSE
├── paper/
│   ├── main.tex              # IEEE Access LaTeX source
│   ├── references.bib        # Bibliography
│   └── imagens/              # Figures and author biographies
├── src/
│   └── evaluation/           # Projection and figure-generation scripts
├── data/
│   ├── raw/rtx5090/          # Baseline traces and manifests
│   └── results/              # Derived results (CSV/JSON)
├── scripts/
│   └── build.sh              # Paper build helper
├── requirements.txt          # Reproduction dependencies
└── REPRODUCIBILITY.md        # Scope, checks, and limitations
```

## Reproducing the Paper

### Build the PDF

```bash
./scripts/build.sh
# or directly:
cd paper && tectonic main.tex
```

### Reproduce the projections and figures

```bash
python src/evaluation/project_twinguard_trace.py --draws 4000 --seed 42
python src/evaluation/cis_weight_sensitivity.py
python src/evaluation/generate_figure4_latency.py
python src/evaluation/generate_figure5_cis.py
python src/evaluation/generate_figure6_scalability.py
python src/evaluation/generate_figure7_uncertainty.py
```

Inputs are the measured baseline traces in `data/raw/rtx5090/`; outputs are
written to `data/results/` and `paper/output/raster/`. Run the integrity check
before reproduction:

```bash
sha256sum -c data/SHA256SUMS
```

See `REPRODUCIBILITY.md` and `data/README.md` for the release boundary,
environment, and validation procedure.

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

## Novel Metric: Confidential Inference Score (CIS)

```text
CIS(q) = 0.35 * PG(q)        # Privacy Guarantee
       + 0.25 * AF(q)        # Attestation Freshness
       + 0.25 * (1 - OP(q))  # Overhead Penalty
       + 0.15 * CS(q)        # Technical-control coverage
```

CIS is in [0, 1]. The 0.90 value is an illustrative decision threshold in the
proposed model; it is not a regulatory or deployment-certification threshold.

## Authors

- Carlos Lucas Vieira Barbosa — Federal University of Pará (UFPA)
- José de Souza Junior — Federal University of Pará (UFPA)
- Allan Douglas Costa, Ph.D. — Federal Rural University of the Amazon (UFRA)

## License

Distributed under the [MIT License](LICENSE).

## Acknowledgments

Partially supported by FAPESPA, PRODEPA, SEC365 Cybersecurity Solutions, LICA,
CCAD-IA, RNP, and INCT iAmazonia.
