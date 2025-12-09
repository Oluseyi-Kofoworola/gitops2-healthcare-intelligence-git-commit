#!/usr/bin/env python3
"""
Regression Simulator for Demo
Creates a series of commits with performance metrics for bisect testing.

Status: Production-ready for demo purposes
"""

import argparse
import json
import random
from pathlib import Path
from datetime import datetime, timedelta


def simulate_regression(num_commits: int, inject_at: int):
    """Create simulated commits with latency metrics."""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    print(f"Creating {num_commits} simulated commits...")
    print(f"Injecting regression at commit-{inject_at:02d}\n")

    base_time = datetime(2024, 12, 1, 10, 0, 0)

    for i in range(1, num_commits + 1):
        # Base latency: 100-150ms
        base_latency = random.uniform(100, 150)

        # Inject regression at specified commit
        if i >= inject_at:
            # Spike to 350-500ms
            latency = base_latency + random.uniform(250, 350)
        else:
            latency = base_latency

        commit_time = base_time + timedelta(hours=i)

        commit_data = {
            "commit_id": f"commit-{i:02d}",
            "timestamp": commit_time.isoformat() + "Z",
            "author": "demo-user",
            "message": f"feat: update service component {i}",
            "metrics": {
                "latency_ms": round(latency, 2),
                "error_rate": 0.001,
                "throughput_rps": 1000,
                "cpu_percent": round(random.uniform(40, 60), 1),
                "memory_mb": round(random.uniform(500, 700), 1)
            },
            "health_status": "degraded" if i >= inject_at else "healthy"
        }

        # Save commit data
        filename = reports_dir / f"commit-{i:02d}.json"
        with open(filename, "w") as f:
            json.dump(commit_data, f, indent=2)

        status = "⚠️  REGRESSION" if i >= inject_at else "✓ Normal"
        print(f"  {commit_data['commit_id']}: {latency:.1f}ms {status}")

    print(f"\n✅ Created {num_commits} commits in reports/")
    print(f"   Regression starts at commit-{inject_at:02d}")
    print(f"   Expected bisect steps: ~{num_commits.bit_length()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate performance regression")
    parser.add_argument("--commits", type=int, default=20, help="Number of commits")
    parser.add_argument("--inject-at", type=int, default=15, help="Where to inject regression")

    args = parser.parse_args()
    
    if args.inject_at > args.commits:
        print(f"Error: inject-at ({args.inject_at}) must be <= commits ({args.commits})")
        exit(1)

    simulate_regression(args.commits, args.inject_at)
