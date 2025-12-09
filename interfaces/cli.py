"""
Command-line interface for nexus_evo
"""
import sys
from agents.orchestrator import orchestrator
from macros import recorder, player, library
from tools import registry, register_default_tools
from utils import get_logger
from app_config import config


logger = get_logger(__name__, config.log_file, config.log_level)


def run_cli():
    """Run interactive CLI"""
    # Initialize
    register_default_tools()
    
    print("\n" + "="*60)
    print("Nexus EVO - Autonomous AI Agent")
    print("="*60)
    print(f"Tools: {len(registry.list_tools())}")
    print(f"Macros: {library.get_count()}")
    print("="*60)
    
    # Run orchestrator interactive mode
    orchestrator.interactive_mode()


if __name__ == "__main__":
    run_cli()
