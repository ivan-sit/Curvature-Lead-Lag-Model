"""Smoke test: the package imports and version is exposed."""

import cllm


def test_import_and_version():
    assert isinstance(cllm.__version__, str)
    assert cllm.__version__.count(".") >= 1
