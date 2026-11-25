import json
import os

import pytest

from prompt_style.library import apply_styles, load_library

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(ROOT, "example_workflows")
LIBRARY = load_library(os.path.join(ROOT, "prompt_style", "styles"))


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
        # Saved order: prompt, seed and its control, then the style rows.
        prompt, seed, control, rows = n["widgets_values"]
        assert control in ("fixed", "increment", "decrement", "randomize")
        apply_styles(LIBRARY, prompt, rows, seed)  # every saved type and style still exists
