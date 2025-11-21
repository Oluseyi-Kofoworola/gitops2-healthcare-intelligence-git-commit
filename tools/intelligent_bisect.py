#!/usr/bin/env python3
"""Lightweight intelligent bisect helper for the payment-gateway service.

This is a teaching/demo tool inspired by the GitOps 2.0 manifesto's
"AI-driven regression detection" concept. It does NOT integrate with
Datadog/Jira, but shows the core loop:

- walk a commit range
- run targeted tests or benchmarks (here: go test and integration tests)
- capture basic latency and error signals
- summarize which commits likely introduced regressions

Example usage (from repo root):

  python tools/intelligent_bisect.py \
    --service payment-gateway \
    --test-cmd "cd services/payment-gateway && go test -run TestPerformanceCompliance ./..." \
    --baseline "HEAD~10" \
    --target "HEAD"

For real systems, this could be extended to:
- call external metrics APIs
- open tickets
- attach evidence to PRs
"""

import argparse
import json
import subprocess
import sys
import time
import shlex
from typing import List, Tuple


def run(cmd: str) -> Tuple[int, str, str, float]:
    """
    Run command safely without shell=True.
    Returns: (returncode, stdout, stderr, duration)
    """
    start = time.time()
    # Parse command safely - prevent shell injection
    cmd_parts = shlex.split(cmd)
    proc = subprocess.Popen(cmd_parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    duration = time.time() - start
    return proc.returncode, out.decode("utf-8", errors="replace"), err.decode("utf-8", errors="replace"), duration


def get_commits(range_expr: str) -> List[str]:
    """Get list of commits in range, validated input."""
    # Validate range expression to prevent injection
    if any(c in range_expr for c in [';', '&', '|', '`', '$', '(', ')']):
        raise ValueError(f"Invalid characters in range expression: {range_expr}")
    
    code, out, err, _ = run(f"git rev-list --reverse {range_expr}")
    if code != 0:
        raise RuntimeError(f"git rev-list failed: {err}")
    return [line.strip() for line in out.splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo intelligent bisect for payment-gateway.")
    parser.add_argument("--service", default="payment-gateway", help="Service under test (for labeling only)")
    parser.add_argument("--baseline", default="HEAD~10", help="Baseline commit (older) for the range")
    parser.add_argument("--target", default="HEAD", help="Target commit (newer) for the range")
    parser.add_argument(
        "--test-cmd",
        default="cd services/payment-gateway && go test -run TestPerformanceCompliance ./...",
        help="Shell command to run for each commit (performance or regression test)",
    )
    parser.add_argument("--threshold-ms", type=float, default=200.0, help="Latency threshold in ms for flagging regressions")
    parser.add_argument("--output", default="regression-report.json", help="Path to JSON report output")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary to --output path")

    args = parser.parse_args()

    commit_range = f"{args.baseline}..{args.target}"
    commits = get_commits(commit_range)

    print(f"🔍 Intelligent bisect demo for service: {args.service}")
    print(f"   Range: {commit_range} ({len(commits)} commits)\n")

    results = []

    for sha in commits:
        print(f"➡️  Checking commit {sha}...")
        
        # Checkout commit safely
        checkout_code, _, checkout_err, _ = run(f"git checkout {sha} --quiet")
        if checkout_code != 0:
            print(f"   ⚠️ Failed to checkout {sha}: {checkout_err}")
            continue
        
        # Run test command (note: this is user-provided, warn in docs)
        # For production, validate/sanitize test_cmd or use allowlist
        code, _out, err, duration = run(args.test_cmd)
        latency_ms = duration * 1000.0
        status = "pass" if code == 0 else "fail"
        regression = status == "fail" or latency_ms > args.threshold_ms

        results.append(
            {
                "commit": sha,
                "status": status,
                "latency_ms": round(latency_ms, 2),
                "regression": regression,
            }
        )

        print(f"   status={status} latency={latency_ms:.2f}ms regression={regression}")
        if code != 0:
            print("   --- stderr ---")
            sys.stdout.write(err)
        print()

    # Return to previous checkout
    return_code, _, return_err, _ = run("git checkout -")
    if return_code != 0:
        print(f"⚠️ Warning: Failed to return to previous checkout: {return_err}")

    suspected = [r for r in results if r["regression"]]

    summary_obj = {
        "service": args.service,
        "threshold_ms": args.threshold_ms,
        "commit_range": commit_range,
        "total_commits": len(results),
        "regression_detected": len(suspected) > 0,
        "suspected_commits": suspected,
        "results": results,
    }

    print("📊 Regression summary (demo):")
    print(json.dumps(summary_obj, indent=2))

    if args.json:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(summary_obj, f, indent=2)
            print(f"📝 JSON report written to {args.output}")
        except OSError as e:
            print(f"⚠️ Failed to write JSON report: {e}", file=sys.stderr)

    if suspected:
        print("\n🚨 Suspected regression-inducing commits:")
        for r in suspected:
            print(f" - {r['commit']} (status={r['status']}, latency_ms={r['latency_ms']})")
    else:
        print("\n✅ No regressions detected above threshold in this range.")


if __name__ == "__main__":
    main()
