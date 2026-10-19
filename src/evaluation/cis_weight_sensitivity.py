#!/usr/bin/env python3
"""Offline sensitivity analysis for the TwinGuard CIS weight vector.

The analysis uses the published aggregate model output in
``data/results/twinguard_results_seed42.json``.  The public result file stores
aggregate CIS, overhead, and technical-control coverage, but not the aggregate
attestation-freshness sub-score.  That missing sub-score is reconstructed from
the published CIS equation at the reference weights, so the sensitivity
analysis reproduces the published CIS values before varying the weights.

This script does not access Vast.ai and does not claim a physical TEE result.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "data" / "results" / "twinguard_results_seed42.json"
DEFAULT_DETAIL = ROOT / "data" / "results" / "cis_weight_sensitivity.csv"
DEFAULT_SUMMARY = ROOT / "data" / "results" / "cis_weight_sensitivity_summary.csv"
DEFAULT_FIGURE = ROOT / "paper" / "output" / "raster" / "twinguard-cis-weight-sensitivity-v2.pdf"

REFERENCE_WEIGHTS = (0.35, 0.25, 0.25, 0.15)
BACKEND_ORDER = ("TDX", "SEV-SNP", "SGX")


def load_model(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        payload = json.load(stream)
    return payload


def reconstruct_subscores(payload: dict) -> dict[str, dict[str, float]]:
    """Recover aggregate CIS components from the published model output."""

    alpha, beta, gamma, delta = REFERENCE_WEIGHTS
    epsilon = float(payload["config"]["epsilon"])
    pg = 1.0 - epsilon / 10.0
    components: dict[str, dict[str, float]] = {}

    for backend in BACKEND_ORDER:
        values = payload["aggregate"][backend]
        cs = (float(values["gdpr_coverage"]) + float(values["hipaa_coverage"])) / 2.0
        overhead = float(values["overhead_mean"])
        published_cis = float(values["cis_mean"])
        af = (published_cis - alpha * pg - gamma * (1.0 - overhead) - delta * cs) / beta
        components[backend] = {
            "pg": pg,
            "af": af,
            "overhead_penalty": overhead,
            "technical_coverage": cs,
            "published_cis": published_cis,
        }

    return components


def score(weights: tuple[float, float, float, float], components: dict[str, float]) -> float:
    alpha, beta, gamma, delta = weights
    return (
        alpha * components["pg"]
        + beta * components["af"]
        + gamma * (1.0 - components["overhead_penalty"])
        + delta * components["technical_coverage"]
    )


def ranking(scores: dict[str, float]) -> str:
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    groups: list[list[str]] = []
    group_score: float | None = None
    for backend, value in ordered:
        if group_score is None or not math.isclose(value, group_score, abs_tol=1e-10):
            groups.append([backend])
            group_score = value
        else:
            groups[-1].append(backend)
    return ">".join("=".join(group) for group in groups)


def winner_label(scores: dict[str, float]) -> str:
    best = max(scores.values())
    winners = [backend for backend, value in scores.items()
               if math.isclose(value, best, abs_tol=1e-10)]
    return winners[0] if len(winners) == 1 else "TIE"


def weight_grid(step: float) -> list[tuple[float, float, float, float]]:
    units = round(1.0 / step)
    if not math.isclose(units * step, 1.0, abs_tol=1e-9):
        raise ValueError("step must divide 1.0 exactly, e.g. 0.01 or 0.05")

    result = []
    for alpha_i in range(units + 1):
        for beta_i in range(units - alpha_i + 1):
            for gamma_i in range(units - alpha_i - beta_i + 1):
                delta_i = units - alpha_i - beta_i - gamma_i
                result.append(tuple(
                    round(value / units, 10)
                    for value in (alpha_i, beta_i, gamma_i, delta_i)
                ))
    return result


def in_reference_neighborhood(weights: tuple[float, float, float, float], radius: float = 0.10) -> bool:
    return all(abs(value - reference) <= radius + 1e-9
               for value, reference in zip(weights, REFERENCE_WEIGHTS))


def in_claimed_region(weights: tuple[float, float, float, float]) -> bool:
    """Region used by the manuscript's earlier sensitivity claim."""

    alpha, _, _, delta = weights
    return alpha >= 0.20 - 1e-9 and delta <= 0.30 + 1e-9


def write_detail(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "alpha", "beta", "gamma", "delta", "local_neighborhood", "claimed_region",
        "cis_tdx", "cis_sev_snp", "cis_sgx", "winner", "ranking",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, payload: dict, components: dict[str, dict[str, float]], rows: list[dict[str, object]]) -> None:
    local = [row for row in rows if row["local_neighborhood"] == "yes"]
    claimed = [row for row in rows if row["claimed_region"] == "yes"]
    local_winners = Counter(row["winner"] for row in local)
    local_rankings = Counter(row["ranking"] for row in local)
    claimed_winners = Counter(row["winner"] for row in claimed)
    claimed_rankings = Counter(row["ranking"] for row in claimed)
    all_rankings = Counter(row["ranking"] for row in rows)

    baseline_scores = {
        backend: score(REFERENCE_WEIGHTS, values)
        for backend, values in components.items()
    }
    fields = ["metric", "value"]
    output = [
        {"metric": "input_file", "value": str(DEFAULT_INPUT.relative_to(ROOT))},
        {"metric": "seed", "value": payload["config"]["seed"]},
        {"metric": "grid_step", "value": "0.01"},
        {"metric": "total_weight_vectors", "value": len(rows)},
        {"metric": "local_neighborhood_radius", "value": "0.10"},
        {"metric": "local_weight_vectors", "value": len(local)},
        {"metric": "claimed_region_definition", "value": "alpha>=0.20 and delta<=0.30"},
        {"metric": "claimed_region_weight_vectors", "value": len(claimed)},
        {"metric": "baseline_ranking", "value": ranking(baseline_scores)},
        {"metric": "local_ranking_count", "value": len(local_rankings)},
        {"metric": "claimed_region_ranking_count", "value": len(claimed_rankings)},
        {"metric": "all_grid_ranking_count", "value": len(all_rankings)},
        {"metric": "local_winner_TDX", "value": local_winners.get("TDX", 0)},
        {"metric": "local_winner_SEV-SNP", "value": local_winners.get("SEV-SNP", 0)},
        {"metric": "local_winner_SGX", "value": local_winners.get("SGX", 0)},
        {"metric": "claimed_region_winner_TDX", "value": claimed_winners.get("TDX", 0)},
        {"metric": "claimed_region_winner_SEV-SNP", "value": claimed_winners.get("SEV-SNP", 0)},
        {"metric": "claimed_region_winner_SGX", "value": claimed_winners.get("SGX", 0)},
        {"metric": "claimed_region_winner_TIE", "value": claimed_winners.get("TIE", 0)},
    ]
    for backend in BACKEND_ORDER:
        output.extend([
            {"metric": f"baseline_cis_{backend}", "value": f"{baseline_scores[backend]:.10f}"},
            {"metric": f"local_min_cis_{backend}", "value": f"{min(float(row[f'cis_{backend.lower().replace('-', '_')}']) for row in local):.10f}"},
            {"metric": f"local_max_cis_{backend}", "value": f"{max(float(row[f'cis_{backend.lower().replace('-', '_')}']) for row in local):.10f}"},
        ])

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)


def write_figure(path: Path, rows: list[dict[str, object]], components: dict[str, dict[str, float]]) -> None:
    """Column-width vector figure in the shared paper style (figstyle.py)."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    import figstyle
    import matplotlib.pyplot as plt
    figstyle.apply()
    ink = figstyle.INK

    local = [row for row in rows if row["local_neighborhood"] == "yes"]
    claimed = [row for row in rows if row["claimed_region"] == "yes"]
    names = ["SEV-SNP", "TDX", "SGX"]
    columns = {"TDX": "cis_tdx", "SEV-SNP": "cis_sev_snp", "SGX": "cis_sgx"}
    baseline = {n: score(REFERENCE_WEIGHTS, components[n]) for n in names}
    lo = {n: min(float(r[columns[n]]) for r in local) for n in names}
    hi = {n: max(float(r[columns[n]]) for r in local) for n in names}
    counts = Counter(row["ranking"] for row in claimed)
    order = [k for k, _ in counts.most_common()]
    total = len(claimed)

    fig, (ra, rb) = plt.subplots(2, 1, figsize=(figstyle.COLUMN_IN, 3.3),
                                 gridspec_kw={"height_ratios": [1.0, 1.15], "hspace": 0.75})
    for i, n in enumerate(names):
        face, _, marker = figstyle.SERIES[n]
        ra.plot([lo[n], hi[n]], [i, i], color=figstyle.GRAY, lw=3.2, alpha=0.6, solid_capstyle="butt")
        ra.plot([lo[n], hi[n]], [i, i], "|", color=ink, ms=6, mew=0.8)
        ra.plot(baseline[n], i, marker, ms=5.5, mfc=face, mec=ink, mew=0.6, zorder=3)
        ra.text(baseline[n], i - 0.28, f"{baseline[n]:.3f}", ha="center", va="bottom", fontsize=7)
    ra.set_yticks(range(len(names)), names)
    ra.set_ylim(len(names) - 0.4, -0.75)
    ra.set_xlim(min(lo.values()) - 0.004, max(hi.values()) + 0.004)
    ra.set_xlabel("CIS")
    ra.grid(axis="x"); ra.grid(axis="y", visible=False)
    ra.tick_params(axis="y", length=0)
    figstyle.panel_label(ra, "(a)", x=-0.22, y=1.04)

    labels = [o.replace("SEV-SNP", "SEV").replace(">", " > ").replace("=", " = ") for o in order]
    for y, o in enumerate(order):
        first = o.split(">")[0].split("=")[0]
        strict = ">" in o
        face, hatch, _ = figstyle.SERIES[first] if strict else (figstyle.GRAY, "....", "")
        rb.barh(y, 100 * counts[o] / total, 0.62, color=face, hatch=hatch, edgecolor=ink, linewidth=0.6)
        rb.text(100 * counts[o] / total + 1.5, y, f"{100 * counts[o] / total:.2f}",
                va="center", fontsize=7)
    rb.set_yticks(range(len(order)), labels)
    rb.invert_yaxis()
    rb.set_xlim(0, 112)
    rb.set_xticks([0, 25, 50, 75, 100])
    rb.set_xlabel("Weight vectors (%)")
    rb.grid(axis="x"); rb.grid(axis="y", visible=False)
    rb.tick_params(axis="y", length=0)
    figstyle.panel_label(rb, "(b)", x=-0.22, y=1.04)

    path.parent.mkdir(parents=True, exist_ok=True)
    figstyle.save(fig, path)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--detail-output", type=Path, default=DEFAULT_DETAIL)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--figure-output", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()

    payload = load_model(args.input)
    components = reconstruct_subscores(payload)
    weights = weight_grid(0.01)
    rows = []

    for vector in weights:
        scores = {backend: score(vector, components[backend]) for backend in BACKEND_ORDER}
        rows.append({
            "alpha": f"{vector[0]:.2f}",
            "beta": f"{vector[1]:.2f}",
            "gamma": f"{vector[2]:.2f}",
            "delta": f"{vector[3]:.2f}",
            "local_neighborhood": "yes" if in_reference_neighborhood(vector) else "no",
            "claimed_region": "yes" if in_claimed_region(vector) else "no",
            "cis_tdx": f"{scores['TDX']:.10f}",
            "cis_sev_snp": f"{scores['SEV-SNP']:.10f}",
            "cis_sgx": f"{scores['SGX']:.10f}",
            "winner": winner_label(scores),
            "ranking": ranking(scores),
        })

    reference_scores = {
        backend: score(REFERENCE_WEIGHTS, components[backend])
        for backend in BACKEND_ORDER
    }
    for backend in BACKEND_ORDER:
        if not math.isclose(reference_scores[backend], components[backend]["published_cis"], abs_tol=1e-9):
            raise AssertionError(f"reference CIS mismatch for {backend}")
    if any(not math.isclose(sum(float(row[name]) for name in ("alpha", "beta", "gamma", "delta")), 1.0, abs_tol=1e-9) for row in rows):
        raise AssertionError("a generated weight vector does not sum to one")

    write_detail(args.detail_output, rows)
    write_summary(args.summary_output, payload, components, rows)
    write_figure(args.figure_output, rows, components)

    local = [row for row in rows if row["local_neighborhood"] == "yes"]
    print(f"[OK] generated {len(rows):,} weight vectors")
    print(f"[OK] local ±0.10 neighborhood: {len(local):,} vectors")
    print(f"[OK] reference ranking: {ranking(reference_scores)}")
    print(f"[OK] local rankings: {sorted({row['ranking'] for row in local})}")
    claimed = [row for row in rows if row["claimed_region"] == "yes"]
    print(f"[OK] claimed region (alpha>=0.20, delta<=0.30): {len(claimed):,} vectors")
    print(f"[OK] claimed-region rankings: {sorted({row['ranking'] for row in claimed})}")
    print(f"[OK] detail CSV: {args.detail_output}")
    print(f"[OK] summary CSV: {args.summary_output}")
    print(f"[OK] figure: {args.figure_output}")


if __name__ == "__main__":
    main()
