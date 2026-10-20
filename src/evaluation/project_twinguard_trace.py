#!/usr/bin/env python3
"""Trace-driven TEE projection over the 1.2 M real RTX 5090 inference requests.

No TEE hardware is executed. The projection takes every *measured* request
latency from the physical RTX 5090 run (data/raw/rtx5090/full-1.2m-c16) and
applies a TEE cost to it:

    L_TEE,i = L_i * (1 + o_b) + a_i

where
  * L_i  is the measured end-to-end latency of request i;
  * o_b  is the relative TEE overhead of backend b, drawn uniformly from the
         range *measured in the literature* for comparable transformer
         inference (see OVERHEAD_RANGES; no author-chosen point values);
  * a_i  is the attestation cost of request i: a full attestation (187 ms,
         conservative model input) when the freshness score drops below the
         threshold, otherwise a cached-token check (6.2 ms).

Request arrival times are reconstructed from the measured per-round elapsed
time (closed loop, concurrency 16), so attestation freshness follows the real
request rate (~14 req/s), not an assumed one.

The overhead uncertainty is propagated by Monte Carlo over the literature
ranges; results are reported as a midpoint value, a 95 % interval and the
probability of each backend ranking.

Usage:  python project_twinguard_trace.py [--draws 4000] [--seed 42]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import itertools
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TRACE_DIR = ROOT / "data" / "raw" / "rtx5090" / "full-1.2m-c16"
CALIB_CSV = ROOT / "data" / "results" / "rtx5090_calibration_scalability.csv"
OUT_DIR = ROOT / "data" / "results"

# ---- CIS definition (paper Eq. 1-6) ------------------------------------------
WEIGHTS = (0.35, 0.25, 0.25, 0.15)          # alpha, beta, gamma, delta
EPSILON, EPSILON_MAX = 1.0, 10.0
LAMBDA_A, THETA_ATT = 0.01, 0.90             # freshness decay (1/s), threshold
CS_TWINGUARD = 7.5 / 8                       # deterministic mapping (Table 3)
CS_TLS_ONLY = 2.0 / 8

# ---- Attestation model inputs (conservative, not measured) -------------------
ATT_FULL_MS = 187.0
ATT_CACHED_MS = 6.2

# ---- TEE overhead ranges measured in the literature --------------------------
# (low, high) relative latency/throughput overhead, with provenance.
OVERHEAD_RANGES = {
    "SEV-SNP": (0.023, 0.160,
                "Misono et al. 2024: BERT-Large inference in an SEV-SNP VM, "
                "2.3% (idle polling) to 16% (default) vs. normal VM"),
    "TDX": (0.0551, 0.1068,
            "Chrapek et al. 2025: Llama2-7B, 1024 in / 128 out tokens, "
            "TDX 5.51-10.68% vs. bare metal"),
    "SGX": (0.0480, 0.0615,
            "Chrapek et al. 2025: Llama2-7B, 1024 in / 128 out tokens, "
            "Gramine-SGX 4.80-6.15% vs. bare metal"),
}
BACKENDS = ["SEV-SNP", "TDX", "SGX"]


def load_traces() -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Return latency (ms), arrival time (s) and per-round metadata."""
    latencies, arrivals, rounds = [], [], []
    for r in range(10):
        meta = json.loads((TRACE_DIR / f"round-{r:02d}.metrics.json").read_text())
        rows = [json.loads(line) for line in gzip.open(TRACE_DIR / f"round-{r:02d}.samples.jsonl.gz", "rt")]
        rows.sort(key=lambda row: row["request_id"])
        if not all(row["ok"] for row in rows) or len(rows) != 120_000:
            raise ValueError(f"round {r}: unexpected trace content")
        rate = len(rows) / meta["elapsed_seconds"]
        latencies.append(np.array([row["latency_ms"] for row in rows]))
        arrivals.append(np.arange(len(rows)) / rate)
        rounds.append({"round": r, "elapsed_s": meta["elapsed_seconds"], "rate_rps": rate})
    return np.concatenate(latencies), np.concatenate(arrivals), rounds


def attestation_schedule(arrivals: np.ndarray, n_rounds: int) -> tuple[np.ndarray, np.ndarray, int]:
    """Per-request attestation cost (ms) and freshness score AF.

    Each round starts a new session with a full attestation; afterwards a
    full re-attestation happens whenever AF = exp(-lambda*(t - t_att)) < theta.
    """
    per_round = len(arrivals) // n_rounds
    cost = np.full(len(arrivals), ATT_CACHED_MS)
    af = np.empty(len(arrivals))
    full = 0
    for r in range(n_rounds):
        sl = slice(r * per_round, (r + 1) * per_round)
        t = arrivals[sl]
        t_att = -math.inf
        c, a = cost[sl], af[sl]
        for i, ti in enumerate(t):
            if math.exp(-LAMBDA_A * (ti - t_att)) < THETA_ATT:
                t_att = ti
                c[i] = ATT_FULL_MS
                full += 1
            a[i] = math.exp(-LAMBDA_A * (ti - t_att))
    return cost, af, full


class OverheadPenalty:
    """Fast mean of OP_i = min(1, o + a_i/L_i) for many values of o."""

    def __init__(self, x: np.ndarray):
        self.x = np.sort(x)
        self.csum = np.concatenate([[0.0], np.cumsum(self.x)])
        self.n = len(x)

    def mean(self, o: float) -> float:
        k = np.searchsorted(self.x, 1.0 - o, side="right")   # entries not clipped
        return (k * o + self.csum[k] + (self.n - k)) / self.n


def cis(pg: float, af: float, op: float, cs: float) -> float:
    a, b, g, d = WEIGHTS
    return a * pg + b * af + g * (1.0 - op) + d * cs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    lat, arr, rounds = load_traces()
    att, af, full_att = attestation_schedule(arr, len(rounds))
    n = len(lat)
    mean_af = float(af.mean())
    pg = 1.0 - EPSILON / EPSILON_MAX
    op = OverheadPenalty(att / lat)
    measured_rate = n / sum(r["elapsed_s"] for r in rounds)

    def project(o: float) -> dict:
        tee = lat * (1.0 + o) + att
        return {
            "overhead_rel": o,
            "op_mean": float(op.mean(o)),
            "cis": cis(pg, mean_af, op.mean(o), CS_TWINGUARD),
            "latency_mean_ms": float(tee.mean()),
            "latency_p95_ms": float(np.percentile(tee, 95)),
            "latency_p99_ms": float(np.percentile(tee, 99)),
            "throughput_rps": measured_rate * lat.mean() / tee.mean(),
        }

    rng = np.random.default_rng(args.seed)
    draws = {b: rng.uniform(OVERHEAD_RANGES[b][0], OVERHEAD_RANGES[b][1], args.draws) for b in BACKENDS}
    cis_draws = {b: np.array([cis(pg, mean_af, op.mean(o), CS_TWINGUARD) for o in draws[b]]) for b in BACKENDS}

    ranking_counts: dict[str, int] = {}
    for i in range(args.draws):
        order = sorted(BACKENDS, key=lambda b: -cis_draws[b][i])
        key = ">".join(order)
        ranking_counts[key] = ranking_counts.get(key, 0) + 1
    rankings = {k: v / args.draws for k, v in sorted(ranking_counts.items(), key=lambda kv: -kv[1])}
    best = {b: float(np.mean([max(BACKENDS, key=lambda x: cis_draws[x][i]) == b for i in range(args.draws)]))
            for b in BACKENDS}

    results = {}
    for b in BACKENDS:
        lo, hi, src = OVERHEAD_RANGES[b]
        mid = project((lo + hi) / 2)
        results[b] = {
            "overhead_range": [lo, hi],
            "overhead_source": src,
            "midpoint": mid,
            "low_end": project(lo),
            "high_end": project(hi),
            "cis_mc_mean": float(cis_draws[b].mean()),
            "cis_mc_ci95": [float(np.percentile(cis_draws[b], 2.5)), float(np.percentile(cis_draws[b], 97.5))],
            "cis_mc_quantiles": {str(q): float(np.percentile(cis_draws[b], q)) for q in (2.5, 25, 50, 75, 97.5)},
            "prob_best": best[b],
        }

    baselines = {
        "Plaintext": {"cis": cis(0.0, 0.0, 0.0, 0.0),
                      "derivation": "PG=0 (no memory encryption), AF=0 (no attestation), OP=0, CS=0"},
        "TLS-only": {"cis": cis(0.0, 0.0, 0.0, CS_TLS_ONLY),
                     "derivation": "PG=0, AF=0, OP~0 (TLS record protection is negligible against ~1.1 s inference), CS=2/8"},
    }

    out = {
        "evaluation_type": "trace_driven_tee_projection",
        "hardware_tee_execution": False,
        "trace": {
            "source": str(TRACE_DIR.relative_to(ROOT)),
            "requests": n,
            "rounds": len(rounds),
            "measured_latency_mean_ms": float(lat.mean()),
            "measured_latency_p95_ms": float(np.percentile(lat, 95)),
            "measured_latency_p99_ms": float(np.percentile(lat, 99)),
            "measured_rate_rps": measured_rate,
        },
        "attestation": {
            "full_ms": ATT_FULL_MS, "cached_ms": ATT_CACHED_MS,
            "lambda_a": LAMBDA_A, "theta_att": THETA_ATT,
            "threshold_time_s": -math.log(THETA_ATT) / LAMBDA_A,
            "full_attestations": full_att,
            "cache_hit_rate": 1.0 - full_att / n,
            "mean_cost_ms": float(att.mean()),
            "mean_cost_share_of_latency": float(att.mean() / lat.mean()),
            "mean_af": mean_af,
        },
        "cis_inputs": {"weights": WEIGHTS, "pg": pg, "epsilon": EPSILON, "epsilon_max": EPSILON_MAX,
                       "cs_twinguard": CS_TWINGUARD, "cs_tls_only": CS_TLS_ONLY},
        "monte_carlo": {"draws": args.draws, "seed": args.seed, "distribution": "uniform over literature range"},
        "backends": results,
        "ranking_probability": rankings,
        "baselines": baselines,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "twinguard_trace_projection.json").write_text(json.dumps(out, indent=2))

    # Compatibility file for the weight-sensitivity script (midpoint values).
    compat = {"config": {"epsilon": EPSILON, "seed": args.seed, "rounds": len(rounds), "requests": n // len(rounds)},
              "aggregate": {b: {"cis_mean": results[b]["midpoint"]["cis"],
                                "overhead_mean": results[b]["midpoint"]["op_mean"],
                                "gdpr_coverage": CS_TWINGUARD, "hipaa_coverage": CS_TWINGUARD,
                                "cis_ci95_lo": results[b]["cis_mc_ci95"][0],
                                "cis_ci95_hi": results[b]["cis_mc_ci95"][1]} for b in BACKENDS}}
    (OUT_DIR / "twinguard_results_seed42.json").write_text(json.dumps(compat, indent=2))

    with (OUT_DIR / "cis_comparison.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["system", "cis", "cis_ci95_lo", "cis_ci95_hi", "overhead_lo_pct", "overhead_mid_pct", "overhead_hi_pct"])
        for name, v in baselines.items():
            w.writerow([name, f"{v['cis']:.4f}", "", "", "", "0.0", ""])
        for b in BACKENDS:
            r = results[b]
            lo, hi = r["overhead_range"]
            w.writerow([f"TwinGuard-{b}", f"{r['midpoint']['cis']:.4f}", f"{r['cis_mc_ci95'][0]:.4f}",
                        f"{r['cis_mc_ci95'][1]:.4f}", f"{100*r['low_end']['op_mean']:.2f}",
                        f"{100*r['midpoint']['op_mean']:.2f}", f"{100*r['high_end']['op_mean']:.2f}"])

    # Projected throughput over the measured calibration curve (Fig. 6c).
    calib = list(csv.DictReader(CALIB_CSV.open()))
    with (OUT_DIR / "tee_projected_throughput.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["concurrency", "measured_rps"] + [f"{b}_{k}" for b in BACKENDS for k in ("lo", "mid", "hi")])
        for row in calib:
            x, l = float(row["requests_per_second"]), float(row["mean_latency_ms"])
            vals = []
            for b in BACKENDS:
                lo, hi = OVERHEAD_RANGES[b][:2]
                for o in (hi, (lo + hi) / 2, lo):   # high overhead -> low throughput
                    vals.append(f"{x * l / (l * (1 + o) + att.mean()):.4f}")
            w.writerow([row["concurrency"], f"{x:.4f}"] + vals)

    a = out["attestation"]
    print(f"[trace] {n:,} requests, mean {lat.mean():.2f} ms, rate {measured_rate:.3f} req/s")
    print(f"[att] full={full_att} hit={100*a['cache_hit_rate']:.4f}% mean cost={a['mean_cost_ms']:.3f} ms "
          f"({100*a['mean_cost_share_of_latency']:.3f}% of latency) meanAF={mean_af:.4f}")
    for b in BACKENDS:
        r = results[b]
        print(f"[{b}] o={r['overhead_range']} CISmid={r['midpoint']['cis']:.4f} "
              f"CI95={r['cis_mc_ci95'][0]:.4f}-{r['cis_mc_ci95'][1]:.4f} "
              f"OPmid={100*r['midpoint']['op_mean']:.2f}% lat={r['midpoint']['latency_mean_ms']:.1f} ms "
              f"p95={r['midpoint']['latency_p95_ms']:.1f} thr={r['midpoint']['throughput_rps']:.2f} "
              f"P(best)={r['prob_best']:.3f}")
    print("[rank]", {k: round(v, 3) for k, v in rankings.items()})
    print("[base]", {k: round(v['cis'], 4) for k, v in baselines.items()})


if __name__ == "__main__":
    main()
