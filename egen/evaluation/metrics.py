"""Evaluation metrics for the EGen platform."""

import math
from typing import Dict, List, Optional, Union

import numpy as np
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


def calculate_perplexity(loss: float) -> float:
    """Calculate perplexity from loss.
    
    Args:
        loss: Cross-entropy loss
        
    Returns:
        Perplexity
    """
    return math.exp(loss)


def calculate_classification_metrics(
    predictions: List[int],
    labels: List[int],
    average: str = "weighted",
) -> Dict[str, float]:
    """Calculate classification metrics.
    
    Args:
        predictions: Predicted class indices
        labels: Ground truth class indices
        average: Averaging method for precision/recall/f1
        
    Returns:
        Dictionary of metrics
    """
    # Calculate accuracy
    accuracy = accuracy_score(labels, predictions)
    
    # Calculate precision, recall, and F1
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average=average
    )
    
    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }


def calculate_generation_metrics(
    predictions: List[str],
    references: List[str],
    use_rouge: bool = True,
    use_bleu: bool = True,
    use_bertscore: bool = False,
) -> Dict[str, float]:
    """Calculate text generation metrics.
    
    Args:
        predictions: Generated text
        references: Reference text
        use_rouge: Whether to calculate ROUGE scores
        use_bleu: Whether to calculate BLEU scores
        use_bertscore: Whether to calculate BERTScore
        
    Returns:
        Dictionary of metrics
    """
    metrics = {}
    
    # Import metrics libraries only when needed
    if use_rouge:
        try:
            from rouge import Rouge
            rouge = Rouge()
            scores = rouge.get_scores(predictions, references, avg=True)
            
            metrics.update({
                "rouge-1-f": float(scores["rouge-1"]["f"]),
                "rouge-2-f": float(scores["rouge-2"]["f"]),
                "rouge-l-f": float(scores["rouge-l"]["f"]),
            })
        except ImportError:
            print("Warning: rouge package not installed. Skipping ROUGE metrics.")
    
    if use_bleu:
        try:
            from nltk.translate.bleu_score import corpus_bleu
            import nltk
            
            # Download NLTK data if needed
            try:
                nltk.data.find("tokenizers/punkt")
            except LookupError:
                nltk.download("punkt")
            
            # Tokenize references and predictions
            tokenized_refs = [[ref.split()] for ref in references]
            tokenized_preds = [pred.split() for pred in predictions]
            
            # Calculate BLEU score
            bleu = corpus_bleu(tokenized_refs, tokenized_preds)
            metrics["bleu"] = float(bleu)
        except ImportError:
            print("Warning: nltk package not installed. Skipping BLEU metrics.")
    
    if use_bertscore:
        try:
            from bert_score import score
            
            # Calculate BERTScore
            P, R, F1 = score(predictions, references, lang="en")
            
            metrics.update({
                "bertscore-precision": float(P.mean()),
                "bertscore-recall": float(R.mean()),
                "bertscore-f1": float(F1.mean()),
            })
        except ImportError:
            print("Warning: bert_score package not installed. Skipping BERTScore metrics.")
    
    return metrics


def calculate_metrics(
    loss: Optional[float] = None,
    predictions: Optional[Union[List[int], List[str]]] = None,
    labels: Optional[Union[List[int], List[str]]] = None,
    task_type: str = "classification",
    **kwargs,
) -> Dict[str, float]:
    """Calculate metrics based on task type.
    
    Args:
        loss: Loss value
        predictions: Model predictions
        labels: Ground truth labels
        task_type: Type of task ("classification" or "generation")
        **kwargs: Additional arguments for specific metric functions
        
    Returns:
        Dictionary of metrics
    """
    metrics = {}
    
    # Add loss and perplexity if provided
    if loss is not None:
        metrics["loss"] = float(loss)
        metrics["perplexity"] = calculate_perplexity(loss)
    
    # Calculate task-specific metrics if predictions and labels are provided
    if predictions is not None and labels is not None:
        if task_type == "classification":
            task_metrics = calculate_classification_metrics(
                predictions, labels, **kwargs
            )
        elif task_type == "generation":
            task_metrics = calculate_generation_metrics(
                predictions, labels, **kwargs
            )
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
        
        metrics.update(task_metrics)
    
    return metrics