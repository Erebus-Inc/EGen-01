"""Tests for the evaluation framework."""

import os
import json
import tempfile

import pytest
import torch
import numpy as np

from egen.evaluation import (
    BenchmarkType,
    calculate_metrics,
    run_benchmark,
    benchmarks,
)
from egen.model import THL150, ModelConfig


@pytest.fixture
def model_config():
    """Create a test model configuration."""
    return ModelConfig(
        hidden_size=128,
        num_layers=2,
        num_attention_heads=4,
        intermediate_size=256,
        max_position_embeddings=512,
        vocab_size=1000,
        domain_routing=True,
        domain_types=["general", "code"],
        domain_layer_allocation={
            "general": [0, 1],
            "code": [0, 1],
        },
    )


@pytest.fixture
def model(model_config):
    """Create a test model."""
    model = THL150(model_config)
    
    # Mock the generate method to always return a fixed response
    def mock_generate(prompt, max_length=None):
        if "capital of France" in prompt:
            return "C"
        elif "2 + 2" in prompt:
            return "B"
        elif "Romeo and Juliet" in prompt:
            return "B"
        else:
            return "A"
    
    model.generate = mock_generate
    return model


@pytest.fixture
def sample_mmlu_data():
    """Create sample MMLU data."""
    return [
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


def test_create_sample_dataset():
    """Test creating a sample dataset."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_path = os.path.join(tmp_dir, "mmlu.json")
        benchmarks.create_sample_dataset(data_path, BenchmarkType.MMLU)
        
        # Check that the file was created
        assert os.path.exists(data_path)
        
        # Check that the file contains valid JSON
        with open(data_path, "r") as f:
            data = json.load(f)
        
        # Check that the data has the expected structure
        assert isinstance(data, list)
        assert len(data) > 0
        assert "question" in data[0]
        assert "choices" in data[0]
        assert "answer" in data[0]


def test_mmlu_dataset(sample_mmlu_data):
    """Test the MMLU dataset."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_path = os.path.join(tmp_dir, "mmlu.json")
        
        # Write sample data to file
        with open(data_path, "w") as f:
            json.dump(sample_mmlu_data, f)
        
        # Create dataset
        dataset = benchmarks.MMLUDataset(data_path)
        
        # Check that data was loaded correctly
        assert len(dataset.data) == len(sample_mmlu_data)
        
        # Test get_prompt
        prompt = dataset.get_prompt(dataset.data[0])
        assert "What is the capital of France?" in prompt
        assert "A. London" in prompt
        assert "B. Berlin" in prompt
        assert "C. Paris" in prompt
        assert "D. Madrid" in prompt
        
        # Test evaluate_response
        score = dataset.evaluate_response(dataset.data[0], "C")
        assert score == 1.0
        
        score = dataset.evaluate_response(dataset.data[0], "A")
        assert score == 0.0


def test_run_benchmark(model, sample_mmlu_data):
    """Test running a benchmark."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_path = os.path.join(tmp_dir, "mmlu.json")
        
        # Write sample data to file
        with open(data_path, "w") as f:
            json.dump(sample_mmlu_data, f)
        
        # Run benchmark
        results = run_benchmark(
            model=model,
            benchmark_type=BenchmarkType.MMLU,
            batch_size=1,
            device="cpu",
            custom_dataset_path=data_path,
        )
        
        # Check results
        assert "overall_accuracy" in results
        assert "num_examples" in results
        assert "subject_accuracies" in results
        
        # Check that the number of examples is correct
        assert results["num_examples"] == len(sample_mmlu_data)
        
        # Check that subject accuracies are present
        assert "geography" in results["subject_accuracies"]
        assert "mathematics" in results["subject_accuracies"]
        assert "literature" in results["subject_accuracies"]


def test_calculate_perplexity():
    """Test calculating perplexity from loss."""
    loss = 2.0
    perplexity = calculate_metrics(loss=loss)["perplexity"]
    assert perplexity == pytest.approx(7.389, 0.001)  # e^2


def test_calculate_classification_metrics():
    """Test calculating classification metrics."""
    predictions = [0, 1, 0, 1, 1]
    labels = [0, 1, 1, 1, 0]
    
    metrics = calculate_metrics(
        predictions=predictions,
        labels=labels,
        task_type="classification",
    )
    
    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics
    
    # 3 out of 5 correct
    assert metrics["accuracy"] == pytest.approx(0.6)