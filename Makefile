.PHONY: setup test

setup:
	pip install --upgrade pip
	pip install -r requirements-dev.txt

test:
	pytest -q 