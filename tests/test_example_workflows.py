import json
import os

import pytest

from prompt_style.library import ALL, apply_style, labels, load_library

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(ROOT, "example_workflows")
LIBRARY = load_library(os.path.join(ROOT, "prompt_style", "styles"))
# Saved order: prompt, position, mode, then the mode's own widgets (a seed is followed by its control).
MODE_WIDGETS = {"pick": ("style", "seed"), "random": ("group", "seed"), "cycle": ("group", "index")}


@pytest.mark.parametrize("name", sorted(os.listdir(FOLDER)))
def test_example_workflow(name):
    with open(os.path.join(FOLDER, name), encoding="utf-8") as f:
        workflow = json.load(f)
    nodes = {n["id"]: n for n in workflow["nodes"]}

    for link_id, origin, origin_slot, target, target_slot, _ in workflow["links"]:
        assert link_id in nodes[origin]["outputs"][origin_slot]["links"]
        assert nodes[target]["inputs"][target_slot]["link"] == link_id

    for n in nodes.values():
        if n["type"] != "AHX_PromptStyle":
            continue
        prompt, position, kind, choice, seed, control = n["widgets_values"]
        assert position in ("before", "after")
        mode = dict(zip(("mode", *MODE_WIDGETS[kind]), (kind, choice, seed)))
        assert choice in (labels(LIBRARY) if kind == "pick" else [ALL, *LIBRARY])
        assert control in ("fixed", "increment", "decrement", "randomize")
        apply_style(LIBRARY, prompt, position, mode)
