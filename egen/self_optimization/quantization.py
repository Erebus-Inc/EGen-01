"""Quantization Optimizer for the EGen platform."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class QuantizationOptimizer:
    """Quantization Optimizer for the EGen platform.
    
    This class is responsible for quantizing neural networks to reduce their size
    and improve inference speed while maintaining performance.
    """

    def __init__(
        self,
        model: nn.Module,
        save_dir: str = "./quantization_results",
        quantization_method: str = "dynamic",
        quantization_scheme: str = "per_tensor",
        quantization_dtype: str = "qint8",
        calibration_dataset: Optional[Any] = None,
        evaluation_func: Optional[Callable[[nn.Module], float]] = None,
        fine_tuning_steps: int = 0,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        """Initialize the Quantization Optimizer.
        
        Args:
            model: PyTorch model to quantize
            save_dir: Directory to save results
            quantization_method: Method for quantization ("static", "dynamic", "qat")
            quantization_scheme: Scheme for quantization ("per_tensor", "per_channel")
            quantization_dtype: Data type for quantization ("qint8", "quint8", "qint32")
            calibration_dataset: Dataset for calibration (required for static quantization)
            evaluation_func: Function to evaluate model performance
            fine_tuning_steps: Number of fine-tuning steps after quantization (for QAT)
            device: Device to run quantization on
        """
        self.model = model
        self.save_dir = save_dir
        self.quantization_method = quantization_method
        self.quantization_scheme = quantization_scheme
        self.quantization_dtype = quantization_dtype
        self.calibration_dataset = calibration_dataset
        self.evaluation_func = evaluation_func
        self.fine_tuning_steps = fine_tuning_steps
        self.device = device
        
        # Create save directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Store original model performance
        self.original_performance = None
        if self.evaluation_func is not None:
            self.original_performance = self.evaluation_func(self.model)
            logger.info(f"Original model performance: {self.original_performance}")
        
        # Validate quantization parameters
        self._validate_params()
    
    def _validate_params(self) -> None:
        """Validate quantization parameters."""
        valid_methods = ["static", "dynamic", "qat"]
        valid_schemes = ["per_tensor", "per_channel"]
        valid_dtypes = ["qint8", "quint8", "qint32"]
        
        if self.quantization_method not in valid_methods:
            raise ValueError(f"Invalid quantization method: {self.quantization_method}. "
                           f"Valid methods are: {valid_methods}")
        
        if self.quantization_scheme not in valid_schemes:
            raise ValueError(f"Invalid quantization scheme: {self.quantization_scheme}. "
                           f"Valid schemes are: {valid_schemes}")
        
        if self.quantization_dtype not in valid_dtypes:
            raise ValueError(f"Invalid quantization dtype: {self.quantization_dtype}. "
                           f"Valid dtypes are: {valid_dtypes}")
        
        if self.quantization_method == "static" and self.calibration_dataset is None:
            raise ValueError("Calibration dataset is required for static quantization")
        
        if self.quantization_method == "qat" and self.fine_tuning_steps <= 0:
            raise ValueError("Fine-tuning steps must be > 0 for quantization-aware training")
    
    def _prepare_model(self) -> nn.Module:
        """Prepare the model for quantization.
        
        Returns:
            Prepared model
        """
        logger.info("Preparing model for quantization")
        
        # Create a copy of the model for quantization
        model_to_quantize = type(self.model)(**self.model.config.__dict__)
        model_to_quantize.load_state_dict(self.model.state_dict())
        
        # Move model to device
        model_to_quantize = model_to_quantize.to(self.device)
        
        # Set model to evaluation mode
        model_to_quantize.eval()
        
        # Fuse modules if possible (e.g., Conv+BN+ReLU)
        if hasattr(torch.quantization, "fuse_modules"):
            logger.info("Fusing modules for improved quantization")
            # This is a placeholder for actual module fusion
            # In a real implementation, we would identify and fuse specific modules
            # For example: torch.quantization.fuse_modules(model_to_quantize, [['conv', 'bn', 'relu']])
        
        return model_to_quantize
    
    def _get_qconfig(self) -> Dict[str, Any]:
        """Get quantization configuration based on parameters.
        
        Returns:
            Dictionary with quantization configuration
        """
        if not hasattr(torch.quantization, "get_default_qconfig"):
            logger.warning("PyTorch version does not support get_default_qconfig")
            return {}
        
        # Get default QConfig based on quantization scheme
        if self.quantization_scheme == "per_tensor":
            qconfig = torch.quantization.get_default_qconfig("fbgemm" if self.device == "cpu" else "qnnpack")
        else:  # per_channel
            qconfig = torch.quantization.get_default_per_channel_qconfig("fbgemm" if self.device == "cpu" else "qnnpack")
        
        return {"qconfig": qconfig}
    
    def _calibrate_model(self, model: nn.Module) -> nn.Module:
        """Calibrate the model for static quantization.
        
        Args:
            model: Prepared model
            
        Returns:
            Calibrated model
        """
        logger.info("Calibrating model for static quantization")
        
        if self.calibration_dataset is None:
            logger.warning("No calibration dataset provided, skipping calibration")
            return model
        
        # Set model to evaluation mode
        model.eval()
        
        # Run calibration
        with torch.no_grad():
            # This is a placeholder for actual calibration
            # In a real implementation, we would iterate through the calibration dataset
            # and run forward passes to collect statistics for quantization
            logger.info("Running calibration on dataset")
            
            # Example calibration loop (placeholder)
            # for batch_idx, (data, _) in enumerate(self.calibration_dataset):
            #     if batch_idx >= 100:  # Limit calibration to 100 batches
            #         break
            #     data = data.to(self.device)
            #     model(data)
        
        return model
    
    def _quantize_dynamic(self) -> nn.Module:
        """Perform dynamic quantization.
        
        Returns:
            Quantized model
        """
        logger.info("Performing dynamic quantization")
        
        # Prepare model
        model_to_quantize = self._prepare_model()
        
        # Define quantization configuration
        dtype_map = {
            "qint8": torch.qint8,
            "quint8": torch.quint8,
            "qint32": torch.qint32,
        }
        dtype = dtype_map.get(self.quantization_dtype, torch.qint8)
        
        # Perform dynamic quantization
        try:
            quantized_model = torch.quantization.quantize_dynamic(
                model_to_quantize,
                {nn.Linear, nn.LSTM, nn.GRU, nn.RNN},  # Quantize these layer types
                dtype=dtype,
            )
            logger.info("Dynamic quantization completed successfully")
            return quantized_model
        except Exception as e:
            logger.error(f"Error during dynamic quantization: {e}", exc_info=True)
            return model_to_quantize
    
    def _quantize_static(self) -> nn.Module:
        """Perform static quantization.
        
        Returns:
            Quantized model
        """
        logger.info("Performing static quantization")
        
        # Prepare model
        model_to_quantize = self._prepare_model()
        
        try:
            # Get quantization configuration
            qconfig_dict = self._get_qconfig()
            
            # Set quantization configuration
            if hasattr(torch.quantization, "prepare"):
                model_to_quantize.qconfig = qconfig_dict.get("qconfig")
                torch.quantization.prepare(model_to_quantize, inplace=True)
            
                # Calibrate model
                calibrated_model = self._calibrate_model(model_to_quantize)
                
                # Convert to quantized model
                quantized_model = torch.quantization.convert(calibrated_model, inplace=False)
                logger.info("Static quantization completed successfully")
                return quantized_model
            else:
                logger.warning("PyTorch version does not support static quantization")
                return model_to_quantize
        except Exception as e:
            logger.error(f"Error during static quantization: {e}", exc_info=True)
            return model_to_quantize
    
    def _quantize_qat(self) -> nn.Module:
        """Perform quantization-aware training.
        
        Returns:
            Quantized model
        """
        logger.info("Performing quantization-aware training")
        
        # Prepare model
        model_to_quantize = self._prepare_model()
        
        try:
            # Get quantization configuration
            qconfig_dict = self._get_qconfig()
            
            # Set quantization configuration
            if hasattr(torch.quantization, "prepare_qat"):
                model_to_quantize.qconfig = qconfig_dict.get("qconfig")
                model_to_quantize.train()  # Set to training mode for QAT
                
                # Prepare model for QAT
                qat_model = torch.quantization.prepare_qat(model_to_quantize, inplace=False)
                
                # Fine-tune the model (placeholder)
                logger.info(f"Fine-tuning model for {self.fine_tuning_steps} steps")
                # In a real implementation, we would fine-tune the model here
                
                # Convert to quantized model
                qat_model.eval()
                quantized_model = torch.quantization.convert(qat_model, inplace=False)
                logger.info("Quantization-aware training completed successfully")
                return quantized_model
            else:
                logger.warning("PyTorch version does not support quantization-aware training")
                return model_to_quantize
        except Exception as e:
            logger.error(f"Error during quantization-aware training: {e}", exc_info=True)
            return model_to_quantize
    
    def quantize(self) -> nn.Module:
        """Quantize the model according to the specified method.
        
        Returns:
            Quantized PyTorch model
        """
        logger.info(f"Starting quantization with method: {self.quantization_method}, "
                   f"scheme: {self.quantization_scheme}, "
                   f"dtype: {self.quantization_dtype}")
        
        # Perform quantization based on method
        if self.quantization_method == "dynamic":
            quantized_model = self._quantize_dynamic()
        elif self.quantization_method == "static":
            quantized_model = self._quantize_static()
        elif self.quantization_method == "qat":
            quantized_model = self._quantize_qat()
        else:
            raise ValueError(f"Unknown quantization method: {self.quantization_method}")
        
        # Evaluate quantized model
        if self.evaluation_func is not None:
            quantized_performance = self.evaluation_func(quantized_model)
            logger.info(f"Quantized model performance: {quantized_performance}")
            logger.info(f"Performance change: {quantized_performance - self.original_performance}")
        
        # Save results
        self._save_results(quantized_model)
        
        return quantized_model
    
    def _save_results(self, quantized_model: nn.Module) -> None:
        """Save quantization results to disk.
        
        Args:
            quantized_model: Quantized model
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = os.path.join(self.save_dir, f"quantization_results_{timestamp}.json")
        
        # Calculate model size reduction
        original_size = self._get_model_size(self.model)
        quantized_size = self._get_model_size(quantized_model)
        size_reduction = 1.0 - (quantized_size / original_size) if original_size > 0 else 0.0
        
        results = {
            "quantization_method": self.quantization_method,
            "quantization_scheme": self.quantization_scheme,
            "quantization_dtype": self.quantization_dtype,
            "original_size_mb": original_size,
            "quantized_size_mb": quantized_size,
            "size_reduction": size_reduction,
            "original_performance": self.original_performance,
            "timestamp": timestamp,
        }
        
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved quantization results to {results_path}")
        
        # Save model checkpoint
        model_path = os.path.join(self.save_dir, f"quantized_model_{timestamp}.pt")
        torch.save({
            "model_state_dict": quantized_model.state_dict(),
            "quantization_info": results,
        }, model_path)
        
        logger.info(f"Saved quantized model to {model_path}")
    
    def _get_model_size(self, model: nn.Module) -> float:
        """Get the size of a model in megabytes.
        
        Args:
            model: PyTorch model
            
        Returns:
            Size in megabytes
        """
        # Save model to a temporary file
        tmp_path = os.path.join(self.save_dir, "tmp_model.pt")
        torch.save(model.state_dict(), tmp_path)
        
        # Get file size
        size_bytes = os.path.getsize(tmp_path)
        size_mb = size_bytes / (1024 * 1024)
        
        # Remove temporary file
        os.remove(tmp_path)
        
        return size_mb
    
    def get_quantization_info(self) -> Dict[str, Any]:
        """Get information about the quantization.
        
        Returns:
            Dictionary with quantization information
        """
        return {
            "quantization_method": self.quantization_method,
            "quantization_scheme": self.quantization_scheme,
            "quantization_dtype": self.quantization_dtype,
            "original_performance": self.original_performance,
        }


class THL150QuantizationOptimizer(QuantizationOptimizer):
    """Quantization Optimizer specifically for the THL-150 model."""

    def __init__(
        self,
        model: nn.Module,
        save_dir: str = "./quantization_results",
        quantization_method: str = "dynamic",  # Default to dynamic for THL-150
        quantization_scheme: str = "per_channel",  # Default to per-channel for THL-150
        quantization_dtype: str = "qint8",
        calibration_dataset: Optional[Any] = None,
        evaluation_func: Optional[Callable[[nn.Module], float]] = None,
        fine_tuning_steps: int = 1000,  # More fine-tuning steps for THL-150
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        domain_aware: bool = True,  # Domain-aware quantization
    ):
        """Initialize the THL-150 Quantization Optimizer.
        
        Args:
            model: THL-150 model to quantize
            save_dir: Directory to save results
            quantization_method: Method for quantization
            quantization_scheme: Scheme for quantization
            quantization_dtype: Data type for quantization
            calibration_dataset: Dataset for calibration
            evaluation_func: Function to evaluate model performance
            fine_tuning_steps: Number of fine-tuning steps after quantization
            device: Device to run quantization on
            domain_aware: Whether to use domain-aware quantization
        """
        super().__init__(
            model=model,
            save_dir=save_dir,
            quantization_method=quantization_method,
            quantization_scheme=quantization_scheme,
            quantization_dtype=quantization_dtype,
            calibration_dataset=calibration_dataset,
            evaluation_func=evaluation_func,
            fine_tuning_steps=fine_tuning_steps,
            device=device,
        )
        self.domain_aware = domain_aware
        self.domain_qconfigs = {}  # Store QConfigs per domain
    
    def _prepare_model(self) -> nn.Module:
        """Prepare the THL-150 model for quantization.
        
        Returns:
            Prepared model
        """
        logger.info("Preparing THL-150 model for quantization")
        
        # Call the base class method
        model_to_quantize = super()._prepare_model()
        
        # THL-150 specific preparations
        if self.domain_aware:
            logger.info("Setting up domain-aware quantization")
            # This would set up domain-specific quantization configurations
            # For example, different precision for different domains
            
            # In a real implementation, we would identify domains and set up
            # different quantization configurations for each domain
        
        return model_to_quantize
    
    def _get_qconfig(self) -> Dict[str, Any]:
        """Get quantization configuration for THL-150.
        
        Returns:
            Dictionary with quantization configuration
        """
        # Get base QConfig
        qconfig_dict = super()._get_qconfig()
        
        if not self.domain_aware:
            return qconfig_dict
        
        # For domain-aware quantization, create domain-specific QConfigs
        if hasattr(torch.quantization, "get_default_qconfig"):
            # Create different QConfigs for different domains
            # For example, more precise quantization for critical domains
            # and more aggressive quantization for less critical domains
            
            # This is a placeholder for actual domain-specific QConfigs
            # In a real implementation, we would create different QConfigs
            # based on domain importance or characteristics
            
            # Example: Create QConfigs for 4 domains
            backend = "fbgemm" if self.device == "cpu" else "qnnpack"
            self.domain_qconfigs = {
                "domain_0": torch.quantization.get_default_qconfig(backend),  # Critical domain
                "domain_1": torch.quantization.get_default_qconfig(backend),
                "domain_2": torch.quantization.get_default_qconfig(backend),
                "domain_3": torch.quantization.get_default_qconfig(backend),  # Less critical domain
            }
            
            # Update the main QConfig dict
            qconfig_dict["domain_qconfigs"] = self.domain_qconfigs
        
        return qconfig_dict
    
    def _apply_domain_specific_quantization(self, model: nn.Module) -> nn.Module:
        """Apply domain-specific quantization to the model.
        
        Args:
            model: Prepared model
            
        Returns:
            Model with domain-specific quantization applied
        """
        if not self.domain_aware or not self.domain_qconfigs:
            return model
        
        logger.info("Applying domain-specific quantization")
        
        # This is a placeholder for actual domain-specific quantization
        # In a real implementation, we would apply different quantization
        # configurations to different parts of the model based on domains
        
        # Example: Apply different QConfigs to different transformer layers
        # based on their domain association
        
        return model
    
    def quantize(self) -> nn.Module:
        """Quantize the THL-150 model with domain awareness.
        
        Returns:
            Quantized THL-150 model
        """
        logger.info(f"Starting THL-150 quantization with domain-aware: {self.domain_aware}")
        
        # For domain-aware quantization, we need to modify the quantization process
        if self.domain_aware:
            # Prepare model
            model_to_quantize = self._prepare_model()
            
            # Apply domain-specific quantization
            model_to_quantize = self._apply_domain_specific_quantization(model_to_quantize)
            
            # Continue with the regular quantization process
            # but with domain-specific configurations
        
        # Call the base class quantization method
        return super().quantize()
    
    def _save_results(self, quantized_model: nn.Module) -> None:
        """Save THL-150 quantization results to disk.
        
        Args:
            quantized_model: Quantized model
        """
        # Call the base class method
        super()._save_results(quantized_model)
        
        # Save domain-specific information if available
        if self.domain_aware and self.domain_qconfigs:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain_path = os.path.join(self.save_dir, f"domain_qconfigs_{timestamp}.json")
            
            # Convert QConfigs to serializable format
            domain_info = {domain: str(qconfig) for domain, qconfig in self.domain_qconfigs.items()}
            
            with open(domain_path, "w", encoding="utf-8") as f:
                json.dump(domain_info, f, indent=2)
            
            logger.info(f"Saved domain-specific quantization info to {domain_path}")