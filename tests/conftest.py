"""The pack folder on sys.path, plus small stand-ins for the ComfyUI modules the nodes import.

The real comfy_api pulls in ComfyUI's model and video stack, which these tests don't need.
"""

import os
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class Spec:
    """Stands in for any comfy_api io object: keeps the arguments it was built with."""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


io = types.SimpleNamespace(
    ComfyNode=object,
    Schema=Spec,
    NodeOutput=Spec,
    String=types.SimpleNamespace(Input=Spec, Output=Spec),
    Int=types.SimpleNamespace(Input=Spec),
    Custom=lambda io_type: types.SimpleNamespace(io_type=io_type, Input=Spec),
)
latest = types.ModuleType("comfy_api.latest")
latest.io = io
latest.ui = types.SimpleNamespace(PreviewText=Spec)
sys.modules["comfy_api"] = types.ModuleType("comfy_api")
sys.modules["comfy_api.latest"] = latest
folder_paths = sys.modules["folder_paths"] = types.ModuleType("folder_paths")


@pytest.fixture
def user_dir(tmp_path, monkeypatch):
    """An empty ComfyUI user folder."""
    monkeypatch.setattr(folder_paths, "get_user_directory", lambda: str(tmp_path), raising=False)
    return tmp_path
