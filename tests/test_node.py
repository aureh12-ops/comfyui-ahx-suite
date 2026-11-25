import importlib.util
import json
import os
import sys

from prompt_style import node
from prompt_style.library import ALL, labels, load_library

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def by_id(specs):
    return {s.args[0]: s for s in specs}


def mode_options():
    mode = by_id(node.PromptStyle.define_schema().kwargs["inputs"])["mode"]
    return {o.args[0]: by_id(o.args[1]) for o in mode.kwargs["options"]}


def add_style_file(name, entries):
    with open(os.path.join(node.styles_folder(), name), "w", encoding="utf-8") as f:
        json.dump(entries, f)


def test_first_use_copies_the_builtin_styles(user_dir):
    folder = node.styles_folder()
    assert folder == str(user_dir / "default" / "ahx-styles")
    assert sorted(os.listdir(folder)) == sorted(os.listdir(node.BUILTIN_STYLES))


def test_user_edits_are_kept(user_dir):
    add_style_file("Lighting.json", [{"name": "Mine", "text": "my light"}])
    assert load_library(node.styles_folder())["Lighting"] == {"Mine": "my light"}


def test_schema_offers_the_library(user_dir):
    library = load_library(node.BUILTIN_STYLES)
    options = mode_options()
    assert list(options) == ["pick", "random", "cycle"]
    assert options["pick"]["style"].kwargs["options"] == labels(library)
    assert options["random"]["group"].kwargs["options"] == options["cycle"]["group"].kwargs["options"] == [ALL, *library]
    # pick stays put, random changes at every run, cycle steps through the group.
    assert options["pick"]["seed"].kwargs["control_after_generate"] == "fixed"
    assert options["random"]["seed"].kwargs["control_after_generate"] is True
    assert options["cycle"]["index"].kwargs["control_after_generate"] == "increment"


def test_new_style_files_show_up_without_restart(user_dir):
    add_style_file("My styles.json", [{"name": "Test", "text": "my style"}])
    options = mode_options()
    assert "My styles / Test" in options["pick"]["style"].kwargs["options"]
    assert "My styles" in options["random"]["group"].kwargs["options"]


def test_execute(user_dir):
    out = node.PromptStyle.execute("a cat", "after", {"mode": "pick", "style": "Lighting / Golden hour", "seed": 0})
    assert out.args == ("a cat, golden hour sunlight, warm low sun, long soft shadows", "Lighting / Golden hour")


def test_pack_registers_the_node(user_dir, monkeypatch):
    spec = importlib.util.spec_from_file_location("ahx_suite", os.path.join(ROOT, "__init__.py"), submodule_search_locations=[ROOT])
    pack = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "ahx_suite", pack)
    spec.loader.exec_module(pack)
    for node_id, cls in pack.NODE_CLASS_MAPPINGS.items():
        assert cls.define_schema().kwargs["node_id"] == node_id
    assert list(pack.NODE_CLASS_MAPPINGS) == ["AHX_PromptStyle"]
