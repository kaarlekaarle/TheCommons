"""
Test to ensure no FastAPI route handlers import cached settings at module scope.
All handlers must call get_settings() inside the function.
"""

import os
import pytest
from pathlib import Path


def test_no_module_level_settings_imports():
    """Test that no endpoint modules import settings at module level."""
    backend_dir = Path(__file__).parent.parent
    api_dir = backend_dir / "api"
    
    # Find all Python files in the API directory
    api_files = list(api_dir.rglob("*.py"))
    
    # Files that are allowed to import settings at module level (non-endpoint modules)
    allowed_files = {
        # Add any non-endpoint modules here if needed
    }
    
    violations = []
    
    for file_path in api_files:
        if file_path.name in allowed_files:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for problematic imports
            if "from backend.config import settings" in content:
                # Check if this file defines FastAPI routes
                if "@router." in content or "@public_router." in content:
                    violations.append(str(file_path))
                    
        except Exception as e:
            # Skip files that can't be read
            continue
    
    if violations:
        violation_list = "\n".join(f"  - {v}" for v in violations)
        pytest.fail(
            f"The following endpoint modules import settings at module level:\n{violation_list}\n"
            f"All route handlers must call get_settings() inside the function instead."
        )


def test_no_module_level_settings_assignments():
    """Test that no endpoint modules assign settings at module level."""
    backend_dir = Path(__file__).parent.parent
    api_dir = backend_dir / "api"
    
    # Find all Python files in the API directory
    api_files = list(api_dir.rglob("*.py"))
    
    violations = []
    
    for file_path in api_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Check for module-level settings assignments
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("settings = ") and "get_settings()" not in line:
                    # Check if this file defines FastAPI routes
                    file_content = "".join(lines)
                    if "@router." in file_content or "@public_router." in file_content:
                        violations.append(f"{file_path}:{line_num}")
                        
        except Exception as e:
            # Skip files that can't be read
            continue
    
    if violations:
        violation_list = "\n".join(f"  - {v}" for v in violations)
        pytest.fail(
            f"The following endpoint modules assign settings at module level:\n{violation_list}\n"
            f"All route handlers must call get_settings() inside the function instead."
        )
