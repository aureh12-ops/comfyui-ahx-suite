import json
import logging
import os

import pytest

from prompt_style.library import ALL, CHOICES, apply_style, join, labels, load_library

BUILTIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompt_style", "styles")

LIBRARY = {
    "Look": {"Film": "film photo", "Ink": "ink drawing"},
    "Place": {"Forest": "in a {pine|birch|fir} forest", "Beach": "on a beach"},
}


def pick(style, seed=0):
    return {"mode": "pick", "style": style, "seed": seed}


def rand(group, seed):
    return {"mode": "random", "group": group, "seed": seed}


def cycle(group, index):
    return {"mode": "cycle", "group": group, "index": index}


def test_style_goes_before_or_after_the_prompt():
    assert apply_style(LIBRARY, "a cat", "after", pick("Look / Film")) == ("a cat, film photo", "Look / Film")
    assert apply_style(LIBRARY, "a cat", "before", pick("Look / Film")) == ("film photo, a cat", "Look / Film")


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
    texts = {apply_style(LIBRARY, "", "after", pick("Place / Forest", seed))[0] for seed in range(50)}
    assert texts == {"in a pine forest", "in a birch forest", "in a fir forest"}
    assert apply_style(LIBRARY, "", "after", pick("Place / Forest", 7)) == apply_style(LIBRARY, "", "after", pick("Place / Forest", 7))


def test_choices_ignore_spaces_around_options():
    library = {"G": {"S": "{ red | blue }"}}
    assert {apply_style(library, "", "after", pick("G / S", seed))[0] for seed in range(20)} == {"red", "blue"}


def test_random_is_reproducible_and_stays_in_its_group():
    assert {apply_style(LIBRARY, "", "after", rand("Look", seed))[1] for seed in range(50)} == {"Look / Film", "Look / Ink"}
    assert {apply_style(LIBRARY, "", "after", rand(ALL, seed))[1] for seed in range(100)} == set(labels(LIBRARY))
    assert apply_style(LIBRARY, "x", "after", rand(ALL, 3)) == apply_style(LIBRARY, "x", "after", rand(ALL, 3))


def test_random_style_still_varies_its_choices():
    # The style pick and its {a|b} choices must not be tied together.
    library = {"G": {"A": "{1|2|3}", "B": "{1|2|3}"}}
    seen = {}
    for seed in range(200):
        text, label = apply_style(library, "", "after", rand("G", seed))
        seen.setdefault(label, set()).add(text)
    assert seen == {"G / A": {"1", "2", "3"}, "G / B": {"1", "2", "3"}}


def test_cycle_walks_the_group_in_order_and_wraps():
    assert [apply_style(LIBRARY, "", "after", cycle("Look", i))[1] for i in range(3)] == ["Look / Film", "Look / Ink", "Look / Film"]
    assert [apply_style(LIBRARY, "", "after", cycle(ALL, i))[1] for i in range(4)] == labels(LIBRARY)


def write(folder, name, content, encoding="utf-8"):
    (folder / name).write_text(content, encoding=encoding)


def test_load_library_reads_groups_in_name_order(tmp_path):
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
        "3D render", "Camera angle", "Cartoon & Anime", "Cinematic", "Drawing & Painting", "Lens & focus",
        "Lighting", "Mood & colors", "Photo", "Shot size", "Surroundings", "Time & weather",
    ]
    for file in os.listdir(BUILTIN):
        with open(os.path.join(BUILTIN, file), encoding="utf-8") as f:
            entries = json.load(f)
        names = [e["name"] for e in entries]
        assert len(names) == len(set(names)), file
        for e in entries:
            text = e["text"]
            assert set(e) == {"name", "text"} and text.strip(), (file, e)
            # Every brace is a complete {a|b} choice.
            choices = CHOICES.findall(text)
            assert text.count("{") == text.count("}") == len(choices), (file, text)
            assert all("|" in c for c in choices), (file, text)
