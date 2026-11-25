import json
import logging
import os

import pytest

from prompt_style.library import CHOICES, CYCLE, PROMPT, RANDOM, apply_styles, join, load_library

BUILTIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompt_style", "styles")

LIBRARY = {
    "Look": {"Film": "film photo", "Ink": "ink drawing"},
    "Place": {"Forest": "in a {pine|birch|fir} forest", "Beach": "on a beach"},
}
YOUR_PROMPT = {"type": PROMPT}


def row(kind, style, index=None):
    return {"type": kind, "style": style} | ({} if index is None else {"index": index})


def test_rows_are_joined_top_to_bottom_around_the_prompt():
    rows = [row("Look", "Film"), YOUR_PROMPT, row("Place", "Beach")]
    assert apply_styles(LIBRARY, "a cat", rows, 0) == (
        "film photo, a cat, on a beach", ["Look / Film", "Place / Beach"], ["film photo", "on a beach"])
    assert apply_styles(LIBRARY, "a cat", [YOUR_PROMPT, row("Look", "Ink"), row("Look", "Film")], 0)[0] == (
        "a cat, ink drawing, film photo")


def test_without_a_prompt_row_the_prompt_comes_first():
    assert apply_styles(LIBRARY, "a cat", [row("Look", "Film")], 0)[0] == "a cat, film photo"


def test_empty_prompt_or_no_styles():
    assert apply_styles(LIBRARY, "", [YOUR_PROMPT, row("Look", "Film")], 0)[0] == "film photo"
    assert apply_styles(LIBRARY, "a cat", [YOUR_PROMPT], 0) == ("a cat", [], [])


@pytest.mark.parametrize("first, second, expected", [
    ("a cat", "film photo", "a cat, film photo"),
    ("A cat sleeps.", "Film photo.", "A cat sleeps. Film photo."),
    ("a cat, ", "film photo", "a cat, film photo"),
    ("  a cat\n", "film photo", "a cat, film photo"),
    ("", "film photo", "film photo"),
    ("a cat", "  ", "a cat"),
])
def test_join(first, second, expected):
    assert join(first, second) == expected


def test_choices_follow_the_seed():
    rows = [row("Place", "Forest")]
    assert {apply_styles(LIBRARY, "", rows, seed)[0] for seed in range(50)} == {
        "in a pine forest", "in a birch forest", "in a fir forest"}
    assert apply_styles(LIBRARY, "", rows, 7) == apply_styles(LIBRARY, "", rows, 7)


def test_choices_ignore_spaces_around_options():
    library = {"G": {"S": "{ red | blue }"}}
    assert {apply_styles(library, "", [row("G", "S")], seed)[0] for seed in range(20)} == {"red", "blue"}


def test_random_is_reproducible_and_stays_in_its_type():
    rows = [row("Look", RANDOM)]
    assert {apply_styles(LIBRARY, "", rows, seed)[1][0] for seed in range(50)} == {"Look / Film", "Look / Ink"}
    assert apply_styles(LIBRARY, "x", rows, 3) == apply_styles(LIBRARY, "x", rows, 3)


def test_random_rows_pick_independently():
    pairs = {tuple(apply_styles(LIBRARY, "", [row("Look", RANDOM), row("Look", RANDOM)], seed)[1]) for seed in range(100)}
    assert len(pairs) == 4


def test_random_style_still_varies_its_choices():
    # The style pick and its {a|b} choices must not be tied together.
    library = {"G": {"A": "{1|2|3}", "B": "{1|2|3}"}}
    seen = {}
    for seed in range(200):
        text, labels, _ = apply_styles(library, "", [row("G", RANDOM)], seed)
        seen.setdefault(labels[0], set()).add(text)
    assert seen == {"G / A": {"1", "2", "3"}, "G / B": {"1", "2", "3"}}


def test_cycle_walks_its_type_in_order_and_wraps():
    labels = [apply_styles(LIBRARY, "", [row("Look", CYCLE, i)], 0)[1][0] for i in range(3)]
    assert labels == ["Look / Film", "Look / Ink", "Look / Film"]
    assert apply_styles(LIBRARY, "", [row("Place", CYCLE)], 0)[1] == ["Place / Forest"]


def test_each_row_has_its_own_cycle():
    rows = [row("Look", CYCLE, 1), row("Place", CYCLE, 0)]
    assert apply_styles(LIBRARY, "", rows, 0)[1] == ["Look / Ink", "Place / Forest"]


@pytest.mark.parametrize("bad, message", [
    (row("Gone", "Film"), "the style type 'Gone' is not in your style library. Pick another type on that row."),
    (row("Look", "Gone"), "the style 'Gone' is not in 'Look'. Pick another style on that row."),
])
def test_missing_styles_are_named_in_the_error(bad, message):
    with pytest.raises(ValueError, match=message):
        apply_styles(LIBRARY, "", [bad], 0)


def write(folder, name, content, encoding="utf-8"):
    (folder / name).write_text(content, encoding=encoding)


def test_load_library_reads_types_in_name_order(tmp_path):
    write(tmp_path, "b.json", json.dumps([{"name": "B1", "text": "b1"}]))
    write(tmp_path, "A.json", json.dumps([{"name": "A1", "text": "a1", "extra": "ignored"}]))
    write(tmp_path, "notes.txt", "not a style file")
    write(tmp_path, "Bom.json", json.dumps([{"name": "C1", "text": "c1"}]), encoding="utf-8-sig")
    library = load_library(tmp_path)
    assert list(library) == ["A", "b", "Bom"]
    assert library["A"] == {"A1": "a1"}


def test_broken_files_are_skipped_with_a_warning(tmp_path, caplog):
    write(tmp_path, "Typo.json", '[{"name": "x", "text": "y"},]')
    write(tmp_path, "Missing.json", '[{"name": "x"}]')
    write(tmp_path, "Empty.json", "[]")
    write(tmp_path, "Good.json", json.dumps([{"name": "x", "text": "y"}]))
    with caplog.at_level(logging.WARNING):
        assert list(load_library(tmp_path)) == ["Good"]
    assert "Typo.json" in caplog.text and "Missing.json" in caplog.text and "Empty.json" not in caplog.text


def test_builtin_library():
    assert list(load_library(BUILTIN)) == [
        "3D render", "Cartoon & Anime", "Cinematic", "Color tone", "Composition", "Drawing & Painting", "Era",
        "Lens & focus", "Lighting", "Location", "Medium", "Mood", "Photo", "Season", "Shot size", "Time of day",
        "View angle", "Weather",
    ]
    for file in os.listdir(BUILTIN):
        with open(os.path.join(BUILTIN, file), encoding="utf-8") as f:
            entries = json.load(f)
        names = [e["name"] for e in entries]
        assert len(names) == len(set(names)), file
        for e in entries:
            text = e["text"]
            assert set(e) == {"name", "text"} and text.strip(), (file, e)
            # Names can't clash with the stack's own row values.
            assert e["name"] not in (PROMPT, RANDOM, CYCLE), (file, e)
            # Every brace is a complete {a|b} choice.
            choices = CHOICES.findall(text)
            assert text.count("{") == text.count("}") == len(choices), (file, text)
            assert all("|" in c for c in choices), (file, text)
