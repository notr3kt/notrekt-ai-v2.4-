import os
import pytest
import json
import tempfile
from pathlib import Path
from unittest import mock

# Import the download_simple module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import download_simple

def test_registry_enforcement_skips_unregistered(tmp_path):
    # Create a fake model registry with only one allowed model
    model_registry = tmp_path / "model_registry.json"
    with open(model_registry, "w", encoding="utf-8") as f:
        json.dump(["allowed/model-1"], f)
    sop_registry = tmp_path / "sop_registry.json"
    with open(sop_registry, "w", encoding="utf-8") as f:
        json.dump(["allowed/model-1"], f)
    # Patch paths in the module
    download_simple.MODEL_REGISTRY_PATH = str(model_registry)
    download_simple.SOP_REGISTRY_PATH = str(sop_registry)
    # Patch download_model to avoid real downloads
    with mock.patch("download_simple.download_model", return_value=True) as mock_dl:
        args = mock.Mock()
        args.models = ["allowed/model-1", "not-allowed/model-2"]
        args.min_disk_gb = 1
        args.min_ram_gb = 1
        args.dvc_track = False
        args.logfile = "test.log"
        # Patch parse_args to return our args
        with mock.patch("download_simple.parse_args", return_value=args):
            with mock.patch("download_simple.setup_logger"):
                download_simple.main()
        # Only the allowed model should be attempted
        mock_dl.assert_called_once_with("allowed/model-1", min_disk_gb=1, min_ram_gb=1)

def test_download_model_retries_on_failure():
    # Patch check_resources to always return True
    with mock.patch("download_simple.check_resources", return_value=True):
        # Patch transformers to raise on first two calls, then succeed
        call_count = {"count": 0}
        def fake_from_pretrained(*a, **kw):
            if call_count["count"] < 2:
                call_count["count"] += 1
                raise RuntimeError("Simulated failure")
            return mock.Mock()
        with mock.patch("download_simple.AutoTokenizer.from_pretrained", side_effect=fake_from_pretrained):
            with mock.patch("download_simple.AutoModelForCausalLM.from_pretrained", side_effect=fake_from_pretrained):
                result = download_simple.download_model("any/model", max_retries=3)
                assert result is True
                assert call_count["count"] == 2

def test_is_model_registered_partial_match():
    registry = {"foo/bar-model", "baz/qux"}
    assert download_simple.is_model_registered("foo/bar-model", registry)
    assert download_simple.is_model_registered("bar-model", registry)
    assert not download_simple.is_model_registered("not-in-registry", registry)

def test_is_sop_registered_empty_registry():
    assert download_simple.is_sop_registered("any/model", set())

def test_is_sop_registered_partial_match():
    registry = {"foo/bar-model", "baz/qux"}
    assert download_simple.is_sop_registered("foo/bar-model", registry)
    assert download_simple.is_sop_registered("bar-model", registry)
    assert not download_simple.is_sop_registered("not-in-registry", registry)
