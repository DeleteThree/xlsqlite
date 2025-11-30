"""
Pytest configuration for integration tests.

Handles module imports for testing.
"""

import sys
import os
from pathlib import Path

# Add the current directory to the path
test_dir = Path(__file__).parent
sys.path.insert(0, str(test_dir))


def pytest_configure(config):
    """Configure pytest to handle module imports."""
    # Import modules and register them
    import importlib
    import importlib.util

    # Order matters - import in dependency order
    modules_to_fix = ['errors', 'parser', 'executor', 'output', 'schema', 'main']

    for module_name in modules_to_fix:
        module_path = test_dir / f'{module_name}.py'
        if module_path.exists():
            # Read the module
            with open(module_path, 'r', encoding='utf-8') as f:
                source = f.read()

            # Fix relative imports
            source = source.replace('from .parser import', 'from parser import')
            source = source.replace('from .schema import', 'from schema import')
            source = source.replace('from .executor import', 'from executor import')
            source = source.replace('from .output import', 'from output import')
            source = source.replace('from .errors import', 'from errors import')

            # Create module
            spec = importlib.util.spec_from_loader(module_name, loader=None)
            module = importlib.util.module_from_spec(spec)

            # Execute module code
            exec(source, module.__dict__)

            # Register module
            sys.modules[module_name] = module
