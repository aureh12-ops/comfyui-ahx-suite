import importlib.util
import json
import os
import sys

from prompt_style import node
from prompt_style.library import PROMPT, load_library

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def inputs():
    return {s.args[0]: s for s in node.PromptStyle.define_schema().kwargs["inputs"]}


def schema_library():
    return inputs()["styles"].kwargs["extra_dict"]["library"]


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


def test_schema(user_dir):
    assert list(inputs()) == ["prompt", "seed", "styles"]
    assert inputs()["seed"].kwargs["control_after_generate"] is True
    assert node.StyleStack.io_type == "AHX_STYLE_STACK"
    # The JS gets the library in file order, as [name, text] pairs.
    library = load_library(node.BUILTIN_STYLES)
    assert schema_library() == {kind: list(styles.items()) for kind, styles in library.items()}


def test_new_style_files_show_up_without_restart(user_dir):
    add_style_file("My styles.json", [{"name": "Test", "text": "my style"}])
    assert schema_library()["My styles"] == [("Test", "my style")]


def test_execute(user_dir):
    rows = [{"type": "Lighting", "style": "Golden hour"}, {"type": PROMPT}, {"type": "View angle", "style": "Low angle"}]
    out = node.PromptStyle.execute("a cat", 0, rows)
    assert out.args == (
        "golden hour sunlight, warm low sun, long soft shadows, a cat, low-angle shot from below, looking up, towering perspective",
        "Lighting / Golden hour, View angle / Low angle",
    )
    # The node shows the style texts, one per line.
    assert out.kwargs["ui"].args == (
        "golden hour sunlight, warm low sun, long soft shadows\nlow-angle shot from below, looking up, towering perspective",)


def test_pack_registers_the_node(user_dir, monkeypatch):
    spec = importlib.util.spec_from_file_location("ahx_suite", os.path.join(ROOT, "__init__.py"), submodule_search_locations=[ROOT])
    pack = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "ahx_suite", pack)
    spec.loader.exec_module(pack)
    for node_id, cls in pack.NODE_CLASS_MAPPINGS.items():
        assert cls.define_schema().kwargs["node_id"] == node_id
    assert list(pack.NODE_CLASS_MAPPINGS) == ["AHX_PromptStyle"]
    assert os.path.isdir(os.path.join(ROOT, pack.WEB_DIRECTORY))
