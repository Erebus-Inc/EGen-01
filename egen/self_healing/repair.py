"""Repair engine for the EGen platform."""

import json
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RepairEngine:
    """Repair engine for the EGen platform.
    
    This class is responsible for repairing faults detected by the SystemMonitor.
    It applies predefined repair strategies and can use web search to find solutions
    for unknown issues.
    """

    def __init__(
        self,
        repair_strategies: Optional[Dict[str, Dict[str, any]]] = None,
        repair_log_path: str = "./logs/repairs.json",
        sandbox_dir: str = "./sandbox",
        enable_web_search: bool = False,
        auto_apply_web_solutions: bool = False,
        patch_validation: bool = True,
    ):
        """Initialize the repair engine.
        
        Args:
            repair_strategies: Dictionary of repair strategies
            repair_log_path: Path to JSON file for logging repairs
            sandbox_dir: Directory for testing repairs in isolation
            enable_web_search: Whether to enable web search for unknown issues
            auto_apply_web_solutions: Whether to automatically apply web solutions
            patch_validation: Whether to validate patches before applying
        """
        self.repair_log_path = repair_log_path
        self.sandbox_dir = sandbox_dir
        self.enable_web_search = enable_web_search
        self.auto_apply_web_solutions = auto_apply_web_solutions
        self.patch_validation = patch_validation
        
        # Load repair strategies
        self.repair_strategies = self._load_repair_strategies(repair_strategies_path)
        
        # Ensure repair log directory exists
        os.makedirs(os.path.dirname(repair_log_path), exist_ok=True)
        
        # Ensure sandbox directory exists
        os.makedirs(sandbox_dir, exist_ok=True)
    
    def _load_repair_strategies(self, path: Optional[str]) -> Dict[str, Dict[str, Any]]:
        """Load repair strategies from a JSON file.
        
        If path is None or the file doesn't exist, return default strategies.
        
        Args:
            path: Path to JSON file containing repair strategies
            
        Returns:
            Dictionary mapping fault types to repair strategy dictionaries
        """
        default_strategies = {
            "out_of_memory": {
                "description": "Out of memory error",
                "actions": [
                    {
                        "type": "config_update",
                        "target": "model_config.json",
                        "updates": {
                            "batch_size": "batch_size * 0.5",  # Reduce batch size by half
                            "gradient_accumulation_steps": "gradient_accumulation_steps * 2",  # Double gradient accumulation
                        },
                        "description": "Reduce batch size and increase gradient accumulation",
                    },
                    {
                        "type": "config_update",
                        "target": "training_config.json",
                        "updates": {
                            "mixed_precision": "true",  # Enable mixed precision
                        },
                        "description": "Enable mixed precision training",
                    },
                ],
            },
            "cuda_error": {
                "description": "CUDA error",
                "actions": [
                    {
                        "type": "command",
                        "command": "nvidia-smi -r",  # Reset GPU
                        "description": "Reset NVIDIA GPU",
                    },
                    {
                        "type": "config_update",
                        "target": "model_config.json",
                        "updates": {
                            "batch_size": "batch_size * 0.5",  # Reduce batch size by half
                        },
                        "description": "Reduce batch size",
                    },
                ],
            },
            "training_divergence": {
                "description": "Training divergence",
                "actions": [
                    {
                        "type": "config_update",
                        "target": "training_config.json",
                        "updates": {
                            "learning_rate": "learning_rate * 0.1",  # Reduce learning rate
                            "gradient_clip_val": "1.0",  # Set gradient clipping
                        },
                        "description": "Reduce learning rate and enable gradient clipping",
                    },
                    {
                        "type": "checkpoint_rollback",
                        "steps": 1,  # Rollback to previous checkpoint
                        "description": "Rollback to previous checkpoint",
                    },
                ],
            },
            "file_not_found": {
                "description": "File not found",
                "actions": [
                    {
                        "type": "file_restore",
                        "source": "backup",  # Restore from backup
                        "description": "Restore file from backup",
                    },
                ],
            },
            "permission_error": {
                "description": "Permission error",
                "actions": [
                    {
                        "type": "command",
                        "command": "chmod -R 755 .",  # Fix permissions
                        "description": "Fix file permissions",
                    },
                ],
            },
            "network_error": {
                "description": "Network error",
                "actions": [
                    {
                        "type": "retry",
                        "max_retries": 3,
                        "delay": 5,  # 5 seconds
                        "description": "Retry operation with exponential backoff",
                    },
                ],
            },
            "import_error": {
                "description": "Import error",
                "actions": [
                    {
                        "type": "command",
                        "command": "pip install -r requirements.txt",  # Reinstall dependencies
                        "description": "Reinstall dependencies",
                    },
                ],
            },
        }
        
        if path is None or not os.path.exists(path):
            return default_strategies
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                strategies = json.load(f)
            return strategies
        except Exception as e:
            logger.error(f"Error loading repair strategies: {e}", exc_info=True)
            return default_strategies
    
    def repair_fault(self, fault: Dict[str, Any]) -> Dict[str, Any]:
        """Repair a detected fault.
        
        Args:
            fault: Fault dictionary from SystemMonitor
            
        Returns:
            Dictionary with repair results
        """
        fault_type = fault["type"]
        repair_result = {
            "fault": fault,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "actions_taken": [],
            "error": None,
        }
        
        # Check if we have a repair strategy for this fault type
        if fault_type in self.repair_strategies:
            strategy = self.repair_strategies[fault_type]
            
            # Apply each action in the strategy
            for action in strategy["actions"]:
                action_result = self._apply_action(action, fault)
                repair_result["actions_taken"].append(action_result)
                
                # If action was successful, mark repair as successful
                if action_result["success"]:
                    repair_result["success"] = True
                    break
        else:
            # No known strategy, try web search if enabled
            if self.enable_web_search:
                web_search_result = self._search_for_solution(fault)
                repair_result["actions_taken"].append(web_search_result)
                repair_result["success"] = web_search_result["success"]
            else:
                repair_result["error"] = f"No repair strategy found for fault type: {fault_type}"
        
        # Log the repair
        self._log_repair(repair_result)
        
        return repair_result
    
    def _apply_action(self, action: Dict[str, Any], fault: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a repair action.
        
        Args:
            action: Action dictionary from repair strategy
            fault: Fault dictionary from SystemMonitor
            
        Returns:
            Dictionary with action results
        """
        action_type = action["type"]
        action_result = {
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "output": None,
        }
        
        try:
            # Apply action based on type
            if action_type == "command":
                action_result = self._apply_command_action(action, action_result)
            elif action_type == "config_update":
                action_result = self._apply_config_update_action(action, action_result)
            elif action_type == "checkpoint_rollback":
                action_result = self._apply_checkpoint_rollback_action(action, action_result)
            elif action_type == "file_restore":
                action_result = self._apply_file_restore_action(action, fault, action_result)
            elif action_type == "retry":
                action_result = self._apply_retry_action(action, fault, action_result)
            else:
                action_result["error"] = f"Unknown action type: {action_type}"
        except Exception as e:
            action_result["error"] = str(e)
            logger.error(f"Error applying action: {e}", exc_info=True)
        
        return action_result
    
    def _apply_command_action(self, action: Dict[str, Any], action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a command action.
        
        Args:
            action: Action dictionary
            action_result: Action result dictionary to update
            
        Returns:
            Updated action result dictionary
        """
        command = action["command"]
        
        try:
            # Run command in sandbox if available
            if os.path.exists(self.sandbox_dir):
                # Create a temporary script file
                with tempfile.NamedTemporaryFile(dir=self.sandbox_dir, delete=False, suffix=".sh") as f:
                    script_path = f.name
                    f.write(f"#!/bin/bash\n{command}\n".encode("utf-8"))
                
                # Make script executable
                os.chmod(script_path, 0o755)
                
                # Run script in sandbox
                result = subprocess.run(
                    [script_path],
                    capture_output=True,
                    text=True,
                    cwd=self.sandbox_dir,
                )
                
                # Clean up script
                os.unlink(script_path)
            else:
                # Run command directly
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                )
            
            # Update action result
            action_result["output"] = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }
            
            # Mark as successful if return code is 0
            action_result["success"] = result.returncode == 0
            
            # Set error if return code is not 0
            if result.returncode != 0:
                action_result["error"] = f"Command failed with return code {result.returncode}: {result.stderr}"
        except Exception as e:
            action_result["error"] = str(e)
            logger.error(f"Error running command: {e}", exc_info=True)
        
        return action_result
    
    def _apply_config_update_action(self, action: Dict[str, Any], action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a config update action.
        
        Args:
            action: Action dictionary
            action_result: Action result dictionary to update
            
        Returns:
            Updated action result dictionary
        """
        target = action["target"]
        updates = action["updates"]
        
        try:
            # Check if target file exists
            if not os.path.exists(target):
                action_result["error"] = f"Target file not found: {target}"
                return action_result
            
            # Load config file
            with open(target, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Create backup
            backup_path = f"{target}.bak"
            shutil.copy2(target, backup_path)
            
            # Apply updates
            for key, value in updates.items():
                # Handle dynamic values (e.g., "batch_size * 0.5")
                if isinstance(value, str) and "*" in value:
                    # Extract variable and factor
                    var_name, factor = value.split("*")
                    var_name = var_name.strip()
                    factor = float(factor.strip())
                    
                    # Get current value
                    current_value = config.get(var_name, 0)
                    
                    # Calculate new value
                    new_value = current_value * factor
                    
                    # Update config
                    config[key] = new_value
                else:
                    # Handle boolean values
                    if value == "true":
                        value = True
                    elif value == "false":
                        value = False
                    # Handle numeric values
                    elif isinstance(value, str) and value.replace(".", "").isdigit():
                        value = float(value)
                        if value.is_integer():
                            value = int(value)
                    
                    # Update config
                    config[key] = value
            
            # Save updated config
            with open(target, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            
            # Mark as successful
            action_result["success"] = True
            action_result["output"] = {
                "updated_keys": list(updates.keys()),
                "backup_path": backup_path,
            }
        except Exception as e:
            action_result["error"] = str(e)
            logger.error(f"Error updating config: {e}", exc_info=True)
            
            # Restore backup if it exists
            if "backup_path" in locals() and os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, target)
                except Exception as restore_error:
                    logger.error(f"Error restoring backup: {restore_error}", exc_info=True)
        
        return action_result
    
    def _apply_checkpoint_rollback_action(self, action: Dict[str, Any], action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a checkpoint rollback action.
        
        Args:
            action: Action dictionary
            action_result: Action result dictionary to update
            
        Returns:
            Updated action result dictionary
        """
        steps = action.get("steps", 1)
        checkpoint_dir = action.get("checkpoint_dir", "./checkpoints")
        
        try:
            # Check if checkpoint directory exists
            if not os.path.exists(checkpoint_dir):
                action_result["error"] = f"Checkpoint directory not found: {checkpoint_dir}"
                return action_result
            
            # Get list of checkpoints
            checkpoints = []
            for item in os.listdir(checkpoint_dir):
                item_path = os.path.join(checkpoint_dir, item)
                if os.path.isdir(item_path) and "checkpoint" in item:
                    checkpoints.append(item_path)
            
            # Sort checkpoints by modification time (newest first)
            checkpoints.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Check if we have enough checkpoints
            if len(checkpoints) <= steps:
                action_result["error"] = f"Not enough checkpoints to rollback {steps} steps"
                return action_result
            
            # Get target checkpoint
            target_checkpoint = checkpoints[steps]
            
            # Get current checkpoint
            current_checkpoint = checkpoints[0]
            
            # Create symlink or copy files
            current_link_path = os.path.join(checkpoint_dir, "current")
            
            # Remove current symlink if it exists
            if os.path.exists(current_link_path):
                if os.path.islink(current_link_path):
                    os.unlink(current_link_path)
                else:
                    shutil.rmtree(current_link_path)
            
            # Create new symlink
            os.symlink(target_checkpoint, current_link_path)
            
            # Mark as successful
            action_result["success"] = True
            action_result["output"] = {
                "previous_checkpoint": current_checkpoint,
                "new_checkpoint": target_checkpoint,
            }
        except Exception as e:
            action_result["error"] = str(e)
            logger.error(f"Error rolling back checkpoint: {e}", exc_info=True)
        
        return action_result
    
    def _apply_file_restore_action(self, action: Dict[str, Any], fault: Dict[str, Any], action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a file restore action.
        
        Args:
            action: Action dictionary
            fault: Fault dictionary
            action_result: Action result dictionary to update
            
        Returns:
            Updated action result dictionary
        """
        source = action["source"]
        
        try:
            # Get missing file path from fault
            if "file" not in fault:
                action_result["error"] = "Fault does not contain file information"
                return action_result
            
            missing_file = fault["file"]
            
            # Check if source is "backup"
            if source == "backup":
                # Check if backup file exists
                backup_file = f"{missing_file}.bak"
                if not os.path.exists(backup_file):
                    action_result["error"] = f"Backup file not found: {backup_file}"
                    return action_result
                
                # Restore from backup
                shutil.copy2(backup_file, missing_file)
                
                # Mark as successful
                action_result["success"] = True
                action_result["output"] = {
                    "restored_file": missing_file,
                    "source": backup_file,
                }
            else:
                # Assume source is a directory
                source_file = os.path.join(source, os.path.basename(missing_file))
                if not os.path.exists(source_file):
                    action_result["error"] = f"Source file not found: {source_file}"
                    return action_result
                
                # Restore from source
                shutil.copy2(source_file, missing_file)
                
                # Mark as successful
                action_result["success"] = True
                action_result["output"] = {
                    "restored_file": missing_file,
                    "source": source_file,
                }
        except Exception as e:
            action_result["error"] = str(e)
            logger.error(f"Error restoring file: {e}", exc_info=True)
        
        return action_result
    
    def _apply_retry_action(self, action: Dict[str, Any], fault: Dict[str, Any], action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a retry action.
        
        Args:
            action: Action dictionary
            fault: Fault dictionary
            action_result: Action result dictionary to update
            
        Returns:
            Updated action result dictionary
        """
        max_retries = action.get("max_retries", 3)
        delay = action.get("delay", 5)
        
        try:
            # Get command from fault
            if "command" not in fault:
                action_result["error"] = "Fault does not contain command information"
                return action_result
            
            command = fault["command"]
            
            # Retry command with exponential backoff
            import time
            
            for retry in range(max_retries):
                # Run command
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                )
                
                # Check if command succeeded
                if result.returncode == 0:
                    # Mark as successful
                    action_result["success"] = True
                    action_result["output"] = {
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "return_code": result.returncode,
                        "retry": retry + 1,
                    }
                    return action_result
                
                # Wait before retrying
                time.sleep(delay * (2 ** retry))
            
            # All retries failed
            action_result["error"] = f"All {max_retries} retries failed"
            action_result["output"] = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "retries": max_retries,
            }
        except Exception as e:
            action_result["error"] = str(e)
            logger.error(f"Error retrying command: {e}", exc_info=True)
        
        return action_result
    
    def _search_for_solution(self, fault: Dict[str, Any]) -> Dict[str, Any]:
        """Search for a solution to an unknown fault.
        
        Args:
            fault: Fault dictionary
            
        Returns:
            Dictionary with search results
        """
        search_result = {
            "action": {
                "type": "web_search",
                "description": "Search for solution online",
            },
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "output": None,
        }
        
        try:
            # Construct search query from fault information
            query_parts = []
            
            # Add fault type
            if "type" in fault:
                query_parts.append(fault["type"])
            
            # Add error message if available
            if "matches" in fault and fault["matches"]:
                # Take first match as primary error
                error_msg = fault["matches"][0]
                # Clean up error message for search
                error_msg = re.sub(r'[^\w\s]', ' ', error_msg)
                query_parts.append(error_msg)
            
            # Add context keywords
            query_parts.extend(["python", "machine learning", "fix", "solution"])
            
            search_query = " ".join(query_parts)
            
            # Perform web search using requests (fallback implementation)
            import requests
            from urllib.parse import quote
            
            # Use DuckDuckGo Instant Answer API as a simple search option
            encoded_query = quote(search_query)
            search_url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            response = requests.get(search_url, timeout=10)
            response.raise_for_status()
            
            search_data = response.json()
            
            # Extract relevant information
            solutions = []
            
            # Check abstract
            if search_data.get("Abstract"):
                solutions.append({
                    "source": "abstract",
                    "content": search_data["Abstract"],
                    "url": search_data.get("AbstractURL", "")
                })
            
            # Check related topics
            if search_data.get("RelatedTopics"):
                for topic in search_data["RelatedTopics"][:3]:  # Limit to 3 topics
                    if isinstance(topic, dict) and "Text" in topic:
                        solutions.append({
                            "source": "related_topic",
                            "content": topic["Text"],
                            "url": topic.get("FirstURL", "")
                        })
            
            # Generate repair suggestions based on search results
            repair_suggestions = self._generate_repair_suggestions(fault, solutions)
            
            search_result["success"] = len(solutions) > 0
            search_result["output"] = {
                "query": search_query,
                "solutions": solutions,
                "repair_suggestions": repair_suggestions
            }
            
            # Try to apply the first viable repair suggestion
            if repair_suggestions and self.auto_apply_web_solutions:
                for suggestion in repair_suggestions:
                    if self._validate_repair_suggestion(suggestion):
                        apply_result = self._apply_web_solution(suggestion, fault)
                        search_result["output"]["applied_solution"] = apply_result
                        search_result["success"] = apply_result["success"]
                        break
            
        except Exception as e:
            search_result["error"] = f"Web search failed: {str(e)}"
            logger.error(f"Web search error: {e}", exc_info=True)
        
        return search_result
    
    def _log_repair(self, repair_result: Dict[str, Any]) -> None:
        """Log a repair result.
        
        Args:
            repair_result: Repair result dictionary
        """
        try:
            # Create log directory if it doesn't exist
            log_dir = os.path.dirname(self.repair_log_path)
            os.makedirs(log_dir, exist_ok=True)
            
            # Load existing log if it exists
            repairs = []
            if os.path.exists(self.repair_log_path):
                try:
                    with open(self.repair_log_path, "r", encoding="utf-8") as f:
                        repairs = json.load(f)
                except json.JSONDecodeError:
                    # File exists but is not valid JSON, start with empty list
                    repairs = []
            
            # Add new repair result
            repairs.append(repair_result)
            
            # Write updated log
            with open(self.repair_log_path, "w", encoding="utf-8") as f:
                json.dump(repairs, f, indent=2)
        except Exception as e:
            logger.error(f"Error logging repair: {e}", exc_info=True)
    
    def _generate_repair_suggestions(self, fault: Dict[str, Any], solutions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate repair suggestions based on web search results.
        
        Args:
            fault: Fault dictionary
            solutions: List of solutions from web search
            
        Returns:
            List of repair suggestion dictionaries
        """
        suggestions = []
        
        try:
            for solution in solutions:
                content = solution.get("content", "")
                
                # Look for common repair patterns in the content
                suggestion = {
                    "type": "web_solution",
                    "source": solution.get("source", ""),
                    "url": solution.get("url", ""),
                    "content": content,
                    "actions": []
                }
                
                # Extract actionable items from content
                if "pip install" in content.lower():
                    suggestion["actions"].append({
                        "type": "command",
                        "command": self._extract_pip_command(content),
                        "description": "Install missing package"
                    })
                
                if "config" in content.lower() and "update" in content.lower():
                    suggestion["actions"].append({
                        "type": "config_update",
                        "description": "Update configuration based on web solution"
                    })
                
                if "restart" in content.lower() or "reboot" in content.lower():
                    suggestion["actions"].append({
                        "type": "command",
                        "command": "sudo systemctl restart",
                        "description": "Restart service"
                    })
                
                if suggestion["actions"]:
                    suggestions.append(suggestion)
        
        except Exception as e:
            logger.error(f"Error generating repair suggestions: {e}", exc_info=True)
        
        return suggestions
    
    def _extract_pip_command(self, content: str) -> str:
        """Extract pip install command from content.
        
        Args:
            content: Text content containing pip command
            
        Returns:
            Extracted pip command
        """
        import re
        
        # Look for pip install patterns
        patterns = [
            r'pip install ([\w\-\.]+)',
            r'pip3 install ([\w\-\.]+)',
            r'python -m pip install ([\w\-\.]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                package = match.group(1)
                return f"pip install {package}"
        
        return "pip install -r requirements.txt"
    
    def _validate_repair_suggestion(self, suggestion: Dict[str, Any]) -> bool:
        """Validate a repair suggestion before applying.
        
        Args:
            suggestion: Repair suggestion dictionary
            
        Returns:
            True if suggestion is valid and safe to apply
        """
        if not self.patch_validation:
            return True
        
        try:
            # Check if suggestion has actions
            if not suggestion.get("actions"):
                return False
            
            # Validate each action
            for action in suggestion["actions"]:
                action_type = action.get("type")
                
                # Validate command actions
                if action_type == "command":
                    command = action.get("command", "")
                    
                    # Block dangerous commands
                    dangerous_patterns = [
                        r'rm\s+-rf\s+/',
                        r'sudo\s+rm',
                        r'format\s+',
                        r'mkfs\.',
                        r'dd\s+if=',
                        r'chmod\s+777'
                    ]
                    
                    for pattern in dangerous_patterns:
                        if re.search(pattern, command, re.IGNORECASE):
                            logger.warning(f"Blocked dangerous command: {command}")
                            return False
                
                # Validate config update actions
                elif action_type == "config_update":
                    # Ensure we have proper config update structure
                    if not action.get("target") and not action.get("updates"):
                        return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating repair suggestion: {e}", exc_info=True)
            return False
    
    def _apply_web_solution(self, suggestion: Dict[str, Any], fault: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a web-based repair solution.
        
        Args:
            suggestion: Repair suggestion from web search
            fault: Original fault dictionary
            
        Returns:
            Dictionary with application results
        """
        apply_result = {
            "suggestion": suggestion,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "actions_taken": [],
            "error": None
        }
        
        try:
            # Apply each action in the suggestion
            for action in suggestion.get("actions", []):
                action_result = self._apply_action(action, fault)
                apply_result["actions_taken"].append(action_result)
                
                # If any action succeeds, mark as successful
                if action_result["success"]:
                    apply_result["success"] = True
                    break
            
            # If no actions succeeded, mark as failed
            if not apply_result["success"] and apply_result["actions_taken"]:
                apply_result["error"] = "All web solution actions failed"
        
        except Exception as e:
            apply_result["error"] = str(e)
            logger.error(f"Error applying web solution: {e}", exc_info=True)
        
        return apply_result