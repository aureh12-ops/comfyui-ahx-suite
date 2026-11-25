"""Style library: one <group>.json file per group, a list of {"name", "text"} entries."""

import json
import logging
import os
import random
import re

ALL = "(all)"
# {a|b|c} in a style text picks one of the options.
CHOICES = re.compile(r"\{([^{}]*)\}")


def load_library(folder):
    """Return {group: {style name: text}} from folder/<group>.json."""
    library = {}
    for file in sorted(os.listdir(folder), key=str.lower):
        group, ext = os.path.splitext(file)
        if ext.lower() != ".json":
            continue
        try:
            # utf-8-sig: Notepad may save a BOM.
            with open(os.path.join(folder, file), encoding="utf-8-sig") as f:
                styles = {s["name"]: s["text"] for s in json.load(f)}
        except (OSError, ValueError, KeyError, TypeError) as e:
            # A typo in one hand-edited file should not take the whole node down.
            logging.warning(f"Prompt Style (ahx): skipped {file}: {e}")
            continue
        if styles:
            library[group] = styles
    return library


def labels(library, group=ALL):
    """'Group / Style' labels of one group, or of every group."""
    groups = library if group == ALL else [group]
    return [f"{g} / {name}" for g in groups for name in library[g]]


def join(first, second):
    """Join two prompt blocks with a comma, or a space when the first already ends with punctuation."""
    first, second = first.strip(), second.strip()
    if not first or not second:
        return first or second
    return first + (" " if first[-1] in ".,;:!?" else ", ") + second


def apply_style(library, prompt, position, mode):
    """Return (styled prompt, 'Group / Style' label) for the node's settings."""
    kind = mode["mode"]
    # One generator for both the style pick and its {a|b} choices, so they don't repeat in lockstep.
    rng = random.Random(mode["index"] if kind == "cycle" else mode["seed"])
    if kind == "pick":
        label = mode["style"]
    elif kind == "random":
        label = rng.choice(labels(library, mode["group"]))
    else:
        choices = labels(library, mode["group"])
        label = choices[mode["index"] % len(choices)]
    group, name = label.split(" / ", 1)
    style = CHOICES.sub(lambda m: rng.choice(m.group(1).split("|")).strip(), library[group][name])
    return (join(style, prompt) if position == "before" else join(prompt, style)), label
