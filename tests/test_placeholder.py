"""Smoke test — verifies the keel package is importable and version is set."""

import keel


def test_package_importable() -> None:
    assert keel.__version__ == "0.1.0"
