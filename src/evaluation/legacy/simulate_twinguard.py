#!/usr/bin/env python3
"""
TwinGuard Simulation — Vectorized (NumPy) version for the public repository.
Generates the modeled TEE results reported in the paper (seed=42,
10 rounds × 120k requests). The physical RTX 5090 baseline is not regenerated
by this script.

Usage:
    python simulate_twinguard.py --rounds 10 --requests 120000 --seed 42
"""

import argparse
import json
import csv
import math
import os
from pathlib import Path

import numpy as np
from scipy import stats

RESULTS_DIR = Path(__file__).resolve().parents[2] / "data" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ---- CIS weights ------------------------------------------------------------
ALPHA, BETA, GAMMA, DELTA = 0.35, 0.25, 0.25, 0.15
LAMBDA_DECAY   = 0.01    # s^-1
THETA_ATT      = 0.90
DP_EPSILON_MAX = 10.0
REQUEST_RATE   = 847.0   # req/s

TEE_OVERHEAD = {
    "TDX":     (0.123, 0.011),
    "SEV-SNP": (0.089, 0.008),
    "SGX":     (0.147, 0.012),
}
# Normalized latency parameter used only by the relative-overhead model. The
# physical RTX 5090 end-to-end baseline reported in the paper is 1131.52 ms;
# this 47.3 ms value is not a physical measurement and must not be presented as
# one. The spread is likewise a model input, not a recorded baseline deviation.
MODEL_BASELINE_LAT_MS = (47.3, 2.1)

BASELINES = {
    "Plaintext":   (0.187, 0.034),
    "TLS-only":    (0.431, 0.028),
    "SecureInfer": (0.783, 0.016),
    "ConfLLM":     (0.714, 0.019),
}

THROUGHPUT = {
    "TLS-only":  {100: (1024,18), 500: (987,21), 1000: (954,24), 2000: (923,27), 5000: (878,31)},
    "TwinGuard": {100: (891,15),  500: (847,17), 1000: (821,19), 2000: (789,22), 5000: (751,25)},
}


# ---- Technical-control mapping (paper Table 3) -------------------------------
# Each control is scored per regime: 1.0 = satisfied by design, 0.5 = partial,
# 0.0 = not provided. Coverage = mean score over the eight mapped controls.
CONTROLS = [
    "hardware_memory_encryption", "remote_attestation", "output_perturbation",
    "encrypted_session", "tamper_evident_audit_log", "access_control",
    "data_minimization", "breach_detection",
]
TWINGUARD_CONTROLS = {c: {"gdpr": 1.0, "hipaa": 1.0} for c in CONTROLS}
# Query scoping cannot be fully automated without domain policy annotations.
TWINGUARD_CONTROLS["data_minimization"] = {"gdpr": 0.5, "hipaa": 0.5}
TLS_ONLY_CONTROLS = {c: {"gdpr": 0.0, "hipaa": 0.0} for c in CONTROLS}
TLS_ONLY_CONTROLS["encrypted_session"] = {"gdpr": 1.0, "hipaa": 1.0}
TLS_ONLY_CONTROLS["access_control"]    = {"gdpr": 0.5, "hipaa": 0.5}
TLS_ONLY_CONTROLS["data_minimization"] = {"gdpr": 0.5, "hipaa": 0.5}


def coverage(table: dict, regime: str) -> float:
    return sum(table[c][regime] for c in CONTROLS) / len(CONTROLS)


def simulate_round(rng: np.random.Generator, n: int, backend: str,
                   epsilon: float = 1.0) -> dict:
    overhead_mu, overhead_sig = TEE_OVERHEAD[backend]

    # Time progression
    t = np.cumsum(rng.exponential(1.0 / REQUEST_RATE, n))
    # Attestation events: full re-att when AF < theta
    att_times   = np.zeros(n)
    att_initial = 0
    last_att    = 0.0
    for i in range(n):
        delta_t = t[i] - last_att
        af_val  = math.exp(-LAMBDA_DECAY * delta_t)
        if af_val < THETA_ATT:
            last_att      = t[i]
            att_times[i]  = 1.0   # mark as full re-att
            att_initial  += 1
    att_cache_hits = n - att_initial

    # Recompute AF per request (vectorized)
    last_att_vec = np.zeros(n)
    last_t = 0.0
    for i in range(n):
        last_att_vec[i] = last_t
        if att_times[i]:
            last_t = t[i]
    delta_t_arr = t - last_att_vec
    AF = np.exp(-LAMBDA_DECAY * delta_t_arr)

    # Overhead & latency
    overhead = np.clip(rng.normal(overhead_mu, overhead_sig, n), 0, 1)
    base_lat = rng.normal(*MODEL_BASELINE_LAT_MS, n)
    tee_lat  = base_lat * (1.0 + overhead)

    # Privacy scores
    PG = np.full(n, (1.0 - epsilon / DP_EPSILON_MAX))  # MEE always active

    # Technical-control coverage: deterministic, control by control (Table 3)
    GDPR_COV  = np.full(n, coverage(TWINGUARD_CONTROLS, "gdpr"))
    HIPAA_COV = np.full(n, coverage(TWINGUARD_CONTROLS, "hipaa"))
    CS = (GDPR_COV + HIPAA_COV) / 2.0

    # Overhead penalty
    OP = np.clip((tee_lat - MODEL_BASELINE_LAT_MS[0]) /
                 MODEL_BASELINE_LAT_MS[0], 0, 1)

    # CIS
    CIS = ALPHA * PG + BETA * AF + GAMMA * (1.0 - OP) + DELTA * CS

    return {
        "tee_backend":       backend,
        "epsilon":           epsilon,
        "n_requests":        n,
        "cis_mean":          float(CIS.mean()),
        "cis_std":           float(CIS.std(ddof=1)),
        "latency_mean_ms":   float(tee_lat.mean()),
        "latency_std_ms":    float(tee_lat.std(ddof=1)),
        "overhead_mean":     float(overhead.mean()),
        "pg_mean":           float(PG.mean()),
        "af_mean":           float(AF.mean()),
        "gdpr_coverage":     float(GDPR_COV.mean()),
        "hipaa_coverage":    float(HIPAA_COV.mean()),
        "att_cache_hit_rate": att_cache_hits / n,
        "audit_integrity":   1.0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds",   type=int,   default=10)
    parser.add_argument("--requests", type=int,   default=120_000)
    parser.add_argument("--seed",     type=int,   default=42)
    parser.add_argument("--epsilon",  type=float, default=1.0)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    print(f"[TwinGuard] Seed={args.seed} Rounds={args.rounds} "
          f"Req/round={args.requests:,} epsilon={args.epsilon}")

    all_rounds = {b: [] for b in TEE_OVERHEAD}

    for r in range(1, args.rounds + 1):
        print(f"  Round {r}/{args.rounds}")
        for backend in TEE_OVERHEAD:
            res = simulate_round(rng, args.requests, backend, args.epsilon)
            all_rounds[backend].append(res)
            print(f"    {backend}: CIS={res['cis_mean']:.4f}+-{res['cis_std']:.4f} "
                  f"OH={res['overhead_mean']*100:.1f}% "
                  f"GDPR={res['gdpr_coverage']*100:.1f}%")

    # Aggregate across rounds
    agg = {}
    for backend, rounds in all_rounds.items():
        cis_list = [r["cis_mean"] for r in rounds]
        n = len(cis_list)
        mu  = np.mean(cis_list)
        sig = np.std(cis_list, ddof=1)
        # 95% CI (t-distribution, df=n-1)
        t95 = stats.t.ppf(0.975, df=n - 1)
        ci95 = t95 * sig / math.sqrt(n)
        agg[backend] = {
            "cis_mean":       float(mu),
            "cis_std":        float(sig),
            "cis_ci95_half":  float(ci95),
            "cis_ci95_lo":    float(mu - ci95),
            "cis_ci95_hi":    float(mu + ci95),
            "overhead_mean":  float(np.mean([r["overhead_mean"] for r in rounds])),
            "gdpr_coverage":  float(np.mean([r["gdpr_coverage"] for r in rounds])),
            "hipaa_coverage": float(np.mean([r["hipaa_coverage"] for r in rounds])),
        }

    # Save JSON
    out = RESULTS_DIR / f"twinguard_results_seed{args.seed}.json"
    with open(out, "w") as f:
        json.dump({
            "config": vars(args),
            "model": {
                "baseline_latency_mean_ms": MODEL_BASELINE_LAT_MS[0],
                "baseline_latency_std_ms": MODEL_BASELINE_LAT_MS[1],
                "baseline_latency_is_normalized": True,
                "physical_baseline_latency_ms": 1131.52,
                "note": "The physical baseline is provenance context; TEE outputs use the normalized model parameter."
            },
            "aggregate": agg,
            "technical_coverage": {
                "method": "deterministic per-control scores (1/0.5/0) over 8 controls",
                "twinguard": {"gdpr": coverage(TWINGUARD_CONTROLS, "gdpr"),
                              "hipaa": coverage(TWINGUARD_CONTROLS, "hipaa")},
                "tls_only": {"gdpr": coverage(TLS_ONLY_CONTROLS, "gdpr"),
                             "hipaa": coverage(TLS_ONLY_CONTROLS, "hipaa")},
            }
        }, f, indent=2)
    print(f"\n[OK] JSON: {out}")

    # Save CIS CSV
    cis_csv = RESULTS_DIR / "cis_comparison.csv"
    with open(cis_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["system", "cis_mean", "cis_std", "overhead_pct"])
        for bname, (bmu, bsig) in BASELINES.items():
            w.writerow([bname, f"{bmu:.4f}", f"{bsig:.4f}", ""])
        for backend, vals in agg.items():
            w.writerow([f"TwinGuard-{backend}", f"{vals['cis_mean']:.4f}",
                        f"{vals['cis_std']:.8f}", f"{vals['overhead_mean']*100:.1f}"])
    print(f"[OK] CSV: {cis_csv}")

    # Save throughput CSV
    tp_csv = RESULTS_DIR / "throughput_scalability.csv"
    with open(tp_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["system", "concurrent_clients", "throughput_mean", "throughput_std"])
        for sys_name, data in THROUGHPUT.items():
            for clients, (mu, sig) in data.items():
                w.writerow([sys_name, clients, mu, sig])
    print(f"[OK] CSV: {tp_csv}")

    # Print summary
    print("\n=== AGGREGATE RESULTS (10 rounds x {:,} requests) ===".format(args.requests))
    for backend, vals in agg.items():
        print(f"  TwinGuard-{backend}: CIS={vals['cis_mean']:.4f} "
              f"[{vals['cis_ci95_lo']:.4f}, {vals['cis_ci95_hi']:.4f}] "
              f"OH={vals['overhead_mean']*100:.1f}%")


if __name__ == "__main__":
    main()
