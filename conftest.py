import os
import pytest

def pytest_collection_modifyitems(config, items):
    if os.getenv("RUN_ROOT_TESTS") == "1":
        return
    # drop any tests not under backend/tests
    keep = []
    for it in items:
        if "/backend/tests/" in str(it.fspath):
            keep.append(it)
    items[:] = keep
