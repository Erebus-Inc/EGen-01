"""Evaluation and benchmarking framework for the EGen platform."""

from egen.evaluation.benchmarks import run_benchmark, BenchmarkType
from egen.evaluation.metrics import calculate_metrics

__all__ = ["run_benchmark", "BenchmarkType", "calculate_metrics"]