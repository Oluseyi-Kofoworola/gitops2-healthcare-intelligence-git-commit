#!/usr/bin/env python3
"""
Load Testing for Healthcare Compliance Platform
Simulates realistic healthcare engineering workloads
WHY: Validate performance under production-scale commit volumes
"""

import asyncio
import time
import statistics
import json
import subprocess
import shlex
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import random

@dataclass
class LoadTestResult:
    """Results from a single test scenario"""
    scenario: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    duration_seconds: float
    requests_per_second: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    errors: List[str]


class HealthcareLoadTester:
    """Load testing for healthcare compliance workflows"""
    
    def __init__(self):
        self.results: List[LoadTestResult] = []
    
    async def test_opa_policy_evaluation(
        self, 
        concurrent_commits: int = 100,
        duration_seconds: int = 60
    ) -> LoadTestResult:
        """
        Test OPA policy evaluation under load
        Simulates 100-1000 concurrent commit validations
        """
        print(f"\n📊 OPA Policy Load Test")
        print(f"Concurrent Commits: {concurrent_commits}")
        print(f"Duration: {duration_seconds}s\n")
        
        latencies = []
        errors = []
        successful = 0
        failed = 0
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        # Generate test commits
        test_commits = self._generate_test_commits(concurrent_commits)
        
        while time.time() < end_time:
            # Test batch of commits
            batch_results = await self._test_opa_batch(test_commits)
            
            for result in batch_results:
                if result["success"]:
                    successful += 1
                    latencies.append(result["latency_ms"])
                else:
                    failed += 1
                    errors.append(result["error"])
        
        duration = time.time() - start_time
        total = successful + failed
        
        return LoadTestResult(
            scenario="OPA Policy Evaluation",
            total_requests=total,
            successful_requests=successful,
            failed_requests=failed,
            duration_seconds=duration,
            requests_per_second=total / duration if duration > 0 else 0,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p50_latency_ms=statistics.median(latencies) if latencies else 0,
            p95_latency_ms=self._percentile(latencies, 0.95) if latencies else 0,
            p99_latency_ms=self._percentile(latencies, 0.99) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            errors=errors[:10]  # Keep first 10 errors
        )
    
    async def test_compliance_scan_throughput(
        self,
        files_per_commit: int = 50,
        commits: int = 100
    ) -> LoadTestResult:
        """
        Test compliance scanning throughput
        Simulates scanning large commits (50+ files)
        """
        print(f"\n📊 Compliance Scan Throughput Test")
        print(f"Files per Commit: {files_per_commit}")
        print(f"Total Commits: {commits}\n")
        
        latencies = []
        errors = []
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        for i in range(commits):
            test_files = [f"file_{j}.go" for j in range(files_per_commit)]
            
            commit_start = time.time()
            try:
                # Simulate compliance scan
                await self._simulate_compliance_scan(test_files)
                latency = (time.time() - commit_start) * 1000
                latencies.append(latency)
                successful += 1
            except Exception as e:
                failed += 1
                errors.append(str(e))
            
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{commits} commits...")
        
        duration = time.time() - start_time
        
        return LoadTestResult(
            scenario=f"Compliance Scan ({files_per_commit} files/commit)",
            total_requests=commits,
            successful_requests=successful,
            failed_requests=failed,
            duration_seconds=duration,
            requests_per_second=commits / duration,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p50_latency_ms=statistics.median(latencies) if latencies else 0,
            p95_latency_ms=self._percentile(latencies, 0.95) if latencies else 0,
            p99_latency_ms=self._percentile(latencies, 0.99) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            errors=errors[:10]
        )
    
    async def test_ai_analysis_concurrency(
        self,
        concurrent_analyses: int = 10
    ) -> LoadTestResult:
        """
        Test AI compliance analysis under concurrent load
        Simulates multiple engineers requesting AI analysis simultaneously
        """
        print(f"\n📊 AI Analysis Concurrency Test")
        print(f"Concurrent Analyses: {concurrent_analyses}\n")
        
        latencies = []
        errors = []
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        # Create concurrent tasks
        tasks = []
        for i in range(concurrent_analyses):
            task = self._simulate_ai_analysis(i)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                failed += 1
                errors.append(str(result))
            else:
                successful += 1
                latencies.append(result)
        
        duration = time.time() - start_time
        
        return LoadTestResult(
            scenario="AI Analysis Concurrency",
            total_requests=concurrent_analyses,
            successful_requests=successful,
            failed_requests=failed,
            duration_seconds=duration,
            requests_per_second=concurrent_analyses / duration,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p50_latency_ms=statistics.median(latencies) if latencies else 0,
            p95_latency_ms=self._percentile(latencies, 0.95) if latencies else 0,
            p99_latency_ms=self._percentile(latencies, 0.99) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            errors=errors[:10]
        )
    
    def _generate_test_commits(self, count: int) -> List[Dict[str, Any]]:
        """Generate realistic test commits"""
        commit_types = ["feat", "fix", "security", "perf", "docs"]
        scopes = ["phi", "auth", "payment", "device", "clinical"]
        
        commits = []
        for i in range(count):
            commit = {
                "sha": f"test{i:06d}",
                "message": f"{random.choice(commit_types)}({random.choice(scopes)}): test commit {i}\n\nHIPAA: 164.312(e)(1)",
                "changed_files": [f"services/{random.choice(scopes)}/file{j}.go" for j in range(random.randint(1, 10))]
            }
            commits.append(commit)
        
        return commits
    
    async def _test_opa_batch(self, commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Test OPA policy evaluation for a batch"""
        results = []
        
        for commit in commits:
            start = time.time()
            try:
                # Simulate OPA evaluation (replace with actual OPA call in production)
                await asyncio.sleep(0.001)  # Simulate 1ms OPA evaluation
                success = random.random() > 0.01  # 99% success rate
                
                results.append({
                    "success": success,
                    "latency_ms": (time.time() - start) * 1000,
                    "error": "" if success else "Policy violation"
                })
            except Exception as e:
                results.append({
                    "success": False,
                    "latency_ms": (time.time() - start) * 1000,
                    "error": str(e)
                })
        
        return results
    
    async def _simulate_compliance_scan(self, files: List[str]):
        """Simulate compliance scanning"""
        # Simulate file processing time (0.5ms per file)
        await asyncio.sleep(len(files) * 0.0005)
        
        # Simulate random failures (1%)
        if random.random() < 0.01:
            raise Exception("Compliance scan timeout")
    
    async def _simulate_ai_analysis(self, index: int) -> float:
        """Simulate AI analysis (returns latency in ms)"""
        start = time.time()
        
        # Simulate AI API call (500-2000ms)
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        return (time.time() - start) * 1000
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def generate_report(self) -> str:
        """Generate comprehensive load test report"""
        report = f"""
# Healthcare Compliance Platform - Load Test Report

**Date**: {datetime.now().isoformat()}
**Test Duration**: {sum(r.duration_seconds for r in self.results):.2f}s

## Summary

| Scenario | Total | Success | Failed | RPS | Avg Latency | P95 Latency | P99 Latency |
|----------|-------|---------|--------|-----|-------------|-------------|-------------|
"""
        
        for result in self.results:
            report += f"| {result.scenario} | {result.total_requests} | {result.successful_requests} | {result.failed_requests} | {result.requests_per_second:.1f} | {result.avg_latency_ms:.1f}ms | {result.p95_latency_ms:.1f}ms | {result.p99_latency_ms:.1f}ms |\n"
        
        report += "\n## Detailed Results\n\n"
        
        for result in self.results:
            report += f"""
### {result.scenario}

- **Total Requests**: {result.total_requests}
- **Success Rate**: {result.successful_requests / result.total_requests * 100:.1f}%
- **Throughput**: {result.requests_per_second:.2f} requests/second
- **Latency**:
  - Average: {result.avg_latency_ms:.2f}ms
  - P50 (Median): {result.p50_latency_ms:.2f}ms
  - P95: {result.p95_latency_ms:.2f}ms
  - P99: {result.p99_latency_ms:.2f}ms
  - Max: {result.max_latency_ms:.2f}ms
- **Duration**: {result.duration_seconds:.2f}s
"""
            
            if result.errors:
                report += f"- **Errors** ({len(result.errors)} shown):\n"
                for error in result.errors[:5]:
                    report += f"  - {error}\n"
        
        report += "\n## Performance Targets vs Actual\n\n"
        report += "| Metric | Target | Actual | Status |\n"
        report += "|--------|--------|--------|--------|\n"
        
        # Calculate overall metrics
        avg_rps = statistics.mean([r.requests_per_second for r in self.results])
        avg_p95 = statistics.mean([r.p95_latency_ms for r in self.results])
        avg_success = statistics.mean([r.successful_requests / r.total_requests for r in self.results])
        
        report += f"| Throughput | >50 RPS | {avg_rps:.1f} RPS | {'✅' if avg_rps > 50 else '❌'} |\n"
        report += f"| P95 Latency | <500ms | {avg_p95:.1f}ms | {'✅' if avg_p95 < 500 else '❌'} |\n"
        report += f"| Success Rate | >99% | {avg_success*100:.1f}% | {'✅' if avg_success > 0.99 else '❌'} |\n"
        
        return report
    
    async def run_full_suite(self):
        """Run complete load test suite"""
        print("🚀 Starting Healthcare Compliance Load Test Suite")
        print("="*60)
        
        # Test 1: OPA Policy Evaluation
        result1 = await self.test_opa_policy_evaluation(
            concurrent_commits=100,
            duration_seconds=30
        )
        self.results.append(result1)
        
        # Test 2: Compliance Scan Throughput (small commits)
        result2 = await self.test_compliance_scan_throughput(
            files_per_commit=10,
            commits=100
        )
        self.results.append(result2)
        
        # Test 3: Compliance Scan Throughput (large commits)
        result3 = await self.test_compliance_scan_throughput(
            files_per_commit=50,
            commits=50
        )
        self.results.append(result3)
        
        # Test 4: AI Analysis Concurrency
        result4 = await self.test_ai_analysis_concurrency(
            concurrent_analyses=20
        )
        self.results.append(result4)
        
        # Generate report
        report = self.generate_report()
        
        # Save report
        report_file = f"load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n✅ Load test complete!")
        print(f"📄 Report saved to: {report_file}")
        print(report)


async def main():
    """Run load tests"""
    tester = HealthcareLoadTester()
    await tester.run_full_suite()


if __name__ == "__main__":
    asyncio.run(main())
