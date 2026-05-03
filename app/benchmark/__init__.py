"""Benchmark utilities for CPU vs GPU comparisons."""

from app.benchmark.compare import compare_cpu_vs_gpu
from app.benchmark.metrics import RunMetrics, summarize_run
from app.benchmark.reports import write_csv, write_json_report
from app.benchmark.runner import BenchmarkSpec, run_benchmark_suite

__all__ = [
    "BenchmarkSpec",
    "RunMetrics",
    "compare_cpu_vs_gpu",
    "run_benchmark_suite",
    "summarize_run",
    "write_csv",
    "write_json_report",
]
