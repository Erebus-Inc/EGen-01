"""Benchmarking framework for the EGen platform."""

import enum
import json
import os
from typing import Dict, List, Optional, Union, Any

import torch
import numpy as np
from tqdm import tqdm

from egen.model import THL150


class BenchmarkType(enum.Enum):
    """Types of benchmarks supported by the framework."""
    
    MMLU = "mmlu"  # Massive Multitask Language Understanding
    HELLASWAG = "hellaswag"  # Commonsense reasoning
    GSM8K = "gsm8k"  # Grade school math problems
    TRUTHFULQA = "truthfulqa"  # Truthfulness in question answering
    CUSTOM = "custom"  # Custom benchmark


class BenchmarkDataset:
    """Base class for benchmark datasets."""
    
    def __init__(self, data_path: str):
        """Initialize the benchmark dataset.
        
        Args:
            data_path: Path to the benchmark data
        """
        self.data_path = data_path
        self.data = self._load_data()
    
    def _load_data(self) -> List[Dict]:
        """Load benchmark data from file.
        
        Returns:
            List of benchmark examples
        """
        raise NotImplementedError("Subclasses must implement _load_data")
    
    def get_prompt(self, example: Dict) -> str:
        """Get the prompt for a benchmark example.
        
        Args:
            example: Benchmark example
            
        Returns:
            Prompt string
        """
        raise NotImplementedError("Subclasses must implement get_prompt")
    
    def evaluate_response(self, example: Dict, response: str) -> float:
        """Evaluate the model's response for a benchmark example.
        
        Args:
            example: Benchmark example
            response: Model's response
            
        Returns:
            Score (0.0 to 1.0)
        """
        raise NotImplementedError("Subclasses must implement evaluate_response")


class MMLUDataset(BenchmarkDataset):
    """MMLU (Massive Multitask Language Understanding) benchmark dataset."""
    
    def _load_data(self) -> List[Dict]:
        """Load MMLU data from file.
        
        Returns:
            List of MMLU examples
        """
        examples = []
        
        # Load MMLU data from JSON file
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for item in data:
            examples.append({
                "question": item["question"],
                "choices": item["choices"],
                "answer": item["answer"],
                "subject": item.get("subject", "unknown")
            })
        
        return examples
    
    def get_prompt(self, example: Dict) -> str:
        """Get the prompt for an MMLU example.
        
        Args:
            example: MMLU example
            
        Returns:
            Prompt string
        """
        prompt = f"Question: {example['question']}\n\n"
        
        for i, choice in enumerate(example["choices"]):
            prompt += f"{chr(65 + i)}. {choice}\n"
        
        prompt += "\nAnswer with the letter corresponding to the correct choice."
        
        return prompt
    
    def evaluate_response(self, example: Dict, response: str) -> float:
        """Evaluate the model's response for an MMLU example.
        
        Args:
            example: MMLU example
            response: Model's response
            
        Returns:
            Score (0.0 or 1.0)
        """
        # Extract the answer letter (A, B, C, D) from the response
        response = response.strip().upper()
        
        # Check if the first letter in the response matches the correct answer
        correct_letter = chr(65 + example["answer"])
        
        if response and response[0] == correct_letter:
            return 1.0
        
        return 0.0


def create_sample_dataset(data_path: str, benchmark_type: BenchmarkType) -> None:
    """Create a sample dataset for testing.
    
    Args:
        data_path: Path to save the dataset
        benchmark_type: Type of benchmark
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    # Create sample data based on benchmark type
    if benchmark_type == BenchmarkType.MMLU:
        sample_data = [
            {
                "question": "What is the capital of France?",
                "choices": ["London", "Berlin", "Paris", "Madrid"],
                "answer": 2,  # Paris (0-indexed)
                "subject": "geography"
            },
            {
                "question": "What is 2 + 2?",
                "choices": ["3", "4", "5", "6"],
                "answer": 1,  # 4 (0-indexed)
                "subject": "mathematics"
            },
            {
                "question": "Who wrote 'Romeo and Juliet'?",
                "choices": ["Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain"],
                "answer": 1,  # William Shakespeare (0-indexed)
                "subject": "literature"
            }
        ]
    elif benchmark_type == BenchmarkType.HELLASWAG:
        sample_data = [
            {
                "context": "A man is playing a guitar.",
                "endings": [
                    "He puts it down and walks away.",
                    "He smashes it on the ground.",
                    "He continues playing a beautiful melody.",
                    "He eats the guitar."
                ],
                "answer": 2,  # He continues playing a beautiful melody. (0-indexed)
            }
        ]
    elif benchmark_type == BenchmarkType.GSM8K:
        sample_data = [
            {
                "question": "John has 5 apples. He gives 2 apples to his friend. How many apples does John have now?",
                "answer": "John has 5 - 2 = 3 apples."
            }
        ]
    elif benchmark_type == BenchmarkType.TRUTHFULQA:
        sample_data = [
            {
                "question": "Do vaccines cause autism?",
                "answer": "No, there is no scientific evidence that vaccines cause autism."
            }
        ]
    else:
        sample_data = []
    
    # Save sample data to file
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"Created sample dataset at {data_path}")


def get_benchmark_dataset(benchmark_type: BenchmarkType, data_path: str) -> BenchmarkDataset:
    """Get the appropriate benchmark dataset based on type.
    
    Args:
        benchmark_type: Type of benchmark
        data_path: Path to benchmark data
        
    Returns:
        Benchmark dataset
    """
    if benchmark_type == BenchmarkType.MMLU:
        return MMLUDataset(data_path)
    
    # Add more benchmark types as needed
    
    raise ValueError(f"Unsupported benchmark type: {benchmark_type}")


def run_benchmark(
    model: THL150,
    benchmark_type: BenchmarkType,
    batch_size: int = 1,
    device: str = "cuda",
    num_samples: Optional[int] = None,
    custom_dataset_path: Optional[str] = None,
) -> Dict[str, Union[float, Dict[str, float]]]:
    """Run a benchmark on the model.
    
    Args:
        model: THL-150 model
        benchmark_type: Type of benchmark
        data_path: Path to benchmark data
        num_examples: Number of examples to evaluate (None for all)
        device: Device to run on
        
    Returns:
        Dictionary of benchmark results
    """
    # Convert device string to torch.device
    device = torch.device(device)
    
    # Determine data path based on benchmark type
    if benchmark_type == BenchmarkType.CUSTOM and custom_dataset_path:
        data_path = custom_dataset_path
    else:
        # Default paths for standard benchmarks
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "benchmarks")
        data_path = os.path.join(base_dir, f"{benchmark_type.value}.json")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        
        # Check if file exists
        if not os.path.exists(data_path):
            # Create a small sample dataset for testing if the real one doesn't exist
            create_sample_dataset(data_path, benchmark_type)
    
    # Get benchmark dataset
    dataset = get_benchmark_dataset(benchmark_type, data_path)
    
    # Limit number of examples if specified
    examples = dataset.data
    if num_samples is not None:
        examples = examples[:num_samples]
    
    # Set model to evaluation mode
    model.eval()
    model.to(device)
    
    # Run benchmark
    scores = []
    subject_scores = {}
    
    # Process examples in batches
    for i in tqdm(range(0, len(examples), batch_size), desc=f"Running {benchmark_type.value} benchmark"):
        batch = examples[i:i + batch_size]
        for example in batch:
            # Get prompt
            prompt = dataset.get_prompt(example)
            
            # Generate response
            with torch.no_grad():
                response = model.generate(prompt, max_length=100)
            
            # Evaluate response
            score = dataset.evaluate_response(example, response)
            scores.append(score)
            
            # Track scores by subject if available
            subject = example.get("subject")
            if subject:
                if subject not in subject_scores:
                    subject_scores[subject] = []
                subject_scores[subject].append(score)
    
    # Calculate overall accuracy
    accuracy = np.mean(scores) if scores else 0.0
    
    # Calculate subject accuracies
    subject_accuracies = {}
    for subject, subj_scores in subject_scores.items():
        subject_accuracies[subject] = np.mean(subj_scores) if subj_scores else 0.0
    
    # Return results
    results = {
        "overall_accuracy": float(accuracy),
        "num_examples": len(scores),
    }
    
    # Add subject accuracies if available
    if subject_accuracies:
        results["subject_accuracies"] = {k: float(v) for k, v in subject_accuracies.items()}
    
    return results