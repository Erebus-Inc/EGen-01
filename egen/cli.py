#!/usr/bin/env python
"""Command-line interface for the EGen platform."""

import argparse
import sys
from typing import List, Optional

from egen import __version__
from egen.model import THL150
from egen.self_healing import agent as healing_agent
from egen.self_optimization import nas_runner
from egen.assistant.core import EGen01


def main(args: Optional[List[str]] = None) -> int:
    """Run the EGen CLI with the given arguments."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="EGen Platform: Unified AI Ecosystem with THL-150 architecture"
    )
    parser.add_argument(
        "--version", action="version", version=f"EGen {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Model subcommand
    model_parser = subparsers.add_parser("model", help="Interact with the THL-150 model")
    model_parser.add_argument(
        "--load", help="Load a model checkpoint", metavar="PATH"
    )
    model_parser.add_argument(
        "--inference", help="Run inference with the model", action="store_true"
    )
    model_parser.add_argument(
        "--prompt", help="Prompt for inference", metavar="TEXT"
    )

    # Self-healing subcommand
    healing_parser = subparsers.add_parser(
        "self-healing", help="Run the self-healing agent"
    )
    healing_parser.add_argument(
        "--monitor", help="Monitor the system for faults", action="store_true"
    )
    healing_parser.add_argument(
        "--repair", help="Repair detected faults", action="store_true"
    )

    # Self-optimization subcommand
    optimization_parser = subparsers.add_parser(
        "self-optimization", help="Run the self-optimization system"
    )
    optimization_parser.add_argument(
        "--nas", help="Run neural architecture search", action="store_true"
    )
    optimization_parser.add_argument(
        "--tune", help="Tune hyperparameters", action="store_true"
    )

    # Assistant subcommand
    assistant_parser = subparsers.add_parser(
        "assistant", help="Interact with the EGen-01 assistant"
    )
    assistant_parser.add_argument(
        "--query", help="Query the assistant", metavar="TEXT"
    )
    assistant_parser.add_argument(
        "--interactive", help="Start interactive mode", action="store_true"
    )

    # Parse arguments
    parsed_args = parser.parse_args(args)

    if parsed_args.command is None:
        parser.print_help()
        return 1

    # Execute command
    if parsed_args.command == "model":
        return handle_model_command(parsed_args)
    elif parsed_args.command == "self-healing":
        return handle_healing_command(parsed_args)
    elif parsed_args.command == "self-optimization":
        return handle_optimization_command(parsed_args)
    elif parsed_args.command == "assistant":
        return handle_assistant_command(parsed_args)

    return 0


def handle_model_command(args: argparse.Namespace) -> int:
    """Handle the model subcommand."""
    print("Initializing THL-150 model...")
    model = THL150()

    if args.load:
        print(f"Loading model checkpoint from {args.load}...")
        model.load_checkpoint(args.load)

    if args.inference:
        if not args.prompt:
            print("Error: --prompt is required for inference")
            return 1

        print(f"Running inference with prompt: {args.prompt}")
        output = model.generate(args.prompt)
        print(f"Output: {output}")

    return 0


def handle_healing_command(args: argparse.Namespace) -> int:
    """Handle the self-healing subcommand."""
    if args.monitor:
        print("Starting self-healing monitoring...")
        healing_agent.start_monitoring()

    if args.repair:
        print("Starting self-healing repair...")
        healing_agent.repair_faults()

    return 0


def handle_optimization_command(args: argparse.Namespace) -> int:
    """Handle the self-optimization subcommand."""
    if args.nas:
        print("Starting neural architecture search...")
        nas_runner.start_nas()

    if args.tune:
        print("Starting hyperparameter tuning...")
        nas_runner.tune_hyperparameters()

    return 0


def handle_assistant_command(args: argparse.Namespace) -> int:
    """Handle the assistant subcommand."""
    assistant = EGen01()

    if args.query:
        print(f"Querying assistant: {args.query}")
        response = assistant.query(args.query)
        print(f"Response: {response}")

    if args.interactive:
        print("Starting interactive mode with EGen-01 assistant...")
        print("Type 'exit' to quit.")

        while True:
            try:
                user_input = input("> ")
                if user_input.lower() == "exit":
                    break

                response = assistant.query(user_input)
                print(f"EGen-01: {response}")

            except KeyboardInterrupt:
                print("\nExiting interactive mode...")
                break

    return 0


if __name__ == "__main__":
    sys.exit(main())