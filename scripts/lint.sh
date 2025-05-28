#!/bin/bash

# Exit on error
set -e

echo "Running black..."
black backend tests

echo "Running isort..."
isort backend tests

echo "Running flake8..."
flake8 backend tests

echo "Running pydocstyle..."
pydocstyle backend tests

echo "Running mypy..."
mypy backend tests

echo "All checks passed! 🎉"