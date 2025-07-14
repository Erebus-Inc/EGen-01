#!/usr/bin/env python
"""Benchmark runner for EGen models.

This script runs benchmarks on EGen models using the evaluation framework.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import torch

# Add the parent directory to the path so we can import egen
sys.path.insert(0, str(Path(__file__).parent.parent))

from egen.evaluation import run_benchmark, BenchmarkType, calculate_metrics
from egen.model import THL150, ModelConfig


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run benchmarks on EGen models")
    parser.add_argument(
        "--model_path",
        type=str,
        required=True,
        help="Path to the model checkpoint",
    )
    parser.add_argument(
        "--config_path",
        type=str,
        required=True,
        help="Path to the model configuration file",
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        choices=[b.value for b in BenchmarkType],
        default=BenchmarkType.MMLU.value,
        help="Benchmark to run",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="benchmark_results",
        help="Directory to save benchmark results",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device to run the benchmark on",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=4,
        help="Batch size for evaluation",
    )
    parser.add_argument(
        "--num_samples",
        type=int,
        default=None,
        help="Number of samples to evaluate (None for all)",
    )
    parser.add_argument(
        "--custom_dataset_path",
        type=str,
        default=None,
        help="Path to custom dataset (only used if benchmark is CUSTOM)",
    )
    return parser.parse_args()


def load_model(model_path, config_path, device):
    """Load a model from a checkpoint."""
    print(f"Loading model from {model_path} with config {config_path}")
    
    # Load configuration
    with open(config_path, "r") as f:
        config_dict = json.load(f)
    
    config = ModelConfig(**config_dict)
    
    # Initialize model
    model = THL150(config)
    
    # Load checkpoint
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    
    # Move model to device
    model = model.to(device)
    model.eval()
    
    return model


def main():
    """Run the benchmark."""
    args = parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load model
    model = load_model(args.model_path, args.config_path, args.device)
    
    # Run benchmark
    benchmark_type = BenchmarkType(args.benchmark)
    print(f"Running {benchmark_type.value} benchmark...")
    
    start_time = time.time()
    
    results = run_benchmark(
        model=model,
        benchmark_type=benchmark_type,
        batch_size=args.batch_size,
        device=args.device,
        num_samples=args.num_samples,
        custom_dataset_path=args.custom_dataset_path,
    )
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # Add timing information to results
    results["timing"] = {
        "start_time": start_time,
        "end_time": end_time,
        "elapsed_time": elapsed_time,
    }
    
    # Save results
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_path = os.path.join(
        args.output_dir, f"{benchmark_type.value}_{timestamp}.json"
    )
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Benchmark completed in {elapsed_time:.2f} seconds")
    print(f"Results saved to {output_path}")
    
    # Print summary
    print("\nSummary:")
    print(f"Overall accuracy: {results['overall_accuracy']:.4f}")
    
    if "subject_accuracies" in results:
        print("\nSubject accuracies:")
        for subject, accuracy in sorted(
            results["subject_accuracies"].items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            print(f"{subject}: {accuracy:.4f}")


if __name__ == "__main__":
    main()