import os
import csv
import sys
import argparse
from collections import defaultdict

def compute_metrics(csv_path):
    if not os.path.exists(csv_path):
        print(f"[Error] CSV file not found at: {csv_path}")
        sys.exit(1)

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    total_cases = len(rows)
    if total_cases == 0:
        print("[Error] CSV file is empty.")
        sys.exit(1)

    # Convert types
    for r in rows:
        r["correct"] = (r["correct"].lower() == "true")
        r["tool_executed"] = (r["tool_executed"].lower() == "true")
        r["tampered_blocked"] = (r["tampered_blocked"].lower() == "true")
        r["latency_with_gateway_ms"] = float(r["latency_with_gateway_ms"])
        r["latency_agent_a_only_ms"] = float(r["latency_agent_a_only_ms"])

    # Overall Metrics
    total_correct = sum(1 for r in rows if r["correct"])
    overall_accuracy = (total_correct / total_cases) * 100

    # False Allow & False Block
    false_allows = sum(1 for r in rows if r["expected_decision"] in ("BLOCK", "ESCALATE", "MODIFY") and r["actual_decision"] == "ALLOW")
    false_allow_rate = (false_allows / total_cases) * 100

    false_blocks = sum(1 for r in rows if r["expected_decision"] == "ALLOW" and r["actual_decision"] in ("BLOCK", "ESCALATE"))
    false_block_rate = (false_blocks / total_cases) * 100

    # Latencies
    latencies_gw = [r["latency_with_gateway_ms"] for r in rows]
    latencies_base = [r["latency_agent_a_only_ms"] for r in rows]

    mean_gw_latency = sum(latencies_gw) / len(latencies_gw)
    mean_base_latency = sum(latencies_base) / len(latencies_base)
    sorted_gw = sorted(latencies_gw)
    p50_gw = sorted_gw[int(len(sorted_gw) * 0.50)]
    p90_gw = sorted_gw[int(len(sorted_gw) * 0.90)]
    p95_gw = sorted_gw[int(len(sorted_gw) * 0.95)]
    latency_overhead_pct = ((mean_gw_latency - mean_base_latency) / mean_base_latency) * 100 if mean_base_latency > 0 else 0

    # Tampered Invariant
    tampered_cases = [r for r in rows if r.get("tampered_blocked") is not None]
    tampered_blocked_count = sum(1 for r in tampered_cases if r["tampered_blocked"])
    tamper_block_rate = (tampered_blocked_count / len(tampered_cases) * 100) if tampered_cases else 100.0

    # Per Category breakdown
    cat_groups = defaultdict(list)
    for r in rows:
        cat_groups[r["category"]].append(r)

    print("\n" + "=" * 80)
    print("      AEGISAI + SHOPSPHERE REAL BENCHMARK EVALUATION RESULTS (N = 40)")
    print("=" * 80)

    print("\n### 1. Overall Policy Enforcement Accuracy & Security Rates\n")
    print(f"- Total Labeled Test Cases: {total_cases}")
    print(f"- Correct Decision Count:   {total_correct} / {total_cases}")
    print(f"- Overall Decision Accuracy: {overall_accuracy:.1f}%")
    print(f"- False-Allow Rate:          {false_allow_rate:.1f}% ({false_allows}/{total_cases})")
    print(f"- False-Block Rate:          {false_block_rate:.1f}% ({false_blocks}/{total_cases})")
    print(f"- Argument Invariant Rate:   {tamper_block_rate:.1f}% (Tampered arguments blocked)")

    print("\n### 2. Latency & Gateway Overhead Analysis\n")
    print(f"- Mean Baseline Latency (Agent A only): {mean_base_latency:.2f} ms")
    print(f"- Mean Latency with AegisAI Gateway:   {mean_gw_latency:.2f} ms")
    print(f"- Median (P50) Gateway Latency:        {p50_gw:.2f} ms")
    print(f"- 90th Percentile (P90) Latency:       {p90_gw:.2f} ms")
    print(f"- 95th Percentile (P95) Latency:       {p95_gw:.2f} ms")
    print(f"- Gateway Interception Overhead:       +{mean_gw_latency - mean_base_latency:.2f} ms")

    print("\n### 3. Per-Category Breakdown Table (Markdown Format)\n")
    header = "| Policy Category | Total Cases | Correct | Accuracy (%) | False Allows | False Blocks | Mean Latency (ms) |"
    sep = "|---|---|---|---|---|---|---|"
    print(header)
    print(sep)

    for cat, items in sorted(cat_groups.items()):
        c_tot = len(items)
        c_cor = sum(1 for x in items if x["correct"])
        c_acc = (c_cor / c_tot) * 100
        c_fa = sum(1 for x in items if x["expected_decision"] in ("BLOCK", "ESCALATE", "MODIFY") and x["actual_decision"] == "ALLOW")
        c_fb = sum(1 for x in items if x["expected_decision"] == "ALLOW" and x["actual_decision"] in ("BLOCK", "ESCALATE"))
        c_lat = sum(x["latency_with_gateway_ms"] for x in items) / c_tot
        print(f"| `{cat}` | {c_tot} | {c_cor} | {c_acc:.1f}% | {c_fa} | {c_fb} | {c_lat:.2f} ms |")

    print(f"| **TOTAL / OVERALL** | **{total_cases}** | **{total_correct}** | **{overall_accuracy:.1f}%** | **{false_allows}** | **{false_blocks}** | **{mean_gw_latency:.2f} ms** |")
    print("=" * 80 + "\n")

    return {
        "total_cases": total_cases,
        "overall_accuracy": overall_accuracy,
        "false_allow_rate": false_allow_rate,
        "false_block_rate": false_block_rate,
        "mean_base_latency_ms": mean_base_latency,
        "mean_gw_latency_ms": mean_gw_latency,
        "p95_gw_ms": p95_gw,
        "tamper_block_rate": tamper_block_rate
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute evaluation metrics from AegisAI benchmark CSV.")
    default_csv = os.path.join(os.path.dirname(os.path.dirname(__file__)), "eval_results.csv")
    parser.add_argument("--csv", default=default_csv, help="Path to eval_results.csv")
    args = parser.parse_args()
    compute_metrics(args.csv)
