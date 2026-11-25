"""Style library: one <type>.json file per style type, a list of {"name", "text"} entries."""

import json
import logging
import os
import random
import re

# Row values of the style stack; web/style_stack.js uses the same strings.
PROMPT = "(prompt)"
RANDOM = "(random)"
CYCLE = "(cycle)"
# {a|b|c} in a style text picks one of the options.
CHOICES = re.compile(r"\{([^{}]*)\}")


def load_library(folder):
    """Return {type: {style name: text}} from folder/<type>.json."""
    library = {}
    for file in sorted(os.listdir(folder), key=str.lower):
        kind, ext = os.path.splitext(file)
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
            library[kind] = styles
    return library


def join(first, second):
    """Join two prompt blocks with a comma, or a space when the first already ends with punctuation."""
    first, second = first.strip(), second.strip()
    if not first or not second:
        return first or second
    return first + (" " if first[-1] in ".,;:!?" else ", ") + second


def pick(library, row, rng):
    """Return ('Type / Style' label, text with its {a|b} choices made) for one style row."""
    kind, name = row["type"], row["style"]
    styles = library.get(kind)
    if styles is None:
        raise ValueError(f"Prompt Style (ahx): no style type '{kind}' in the library")
    if name == RANDOM:
        name = rng.choice(list(styles))
    elif name == CYCLE:
        name = list(styles)[row.get("index", 0) % len(styles)]
    elif name not in styles:
        raise ValueError(f"Prompt Style (ahx): no style '{name}' in '{kind}'")
    text = CHOICES.sub(lambda m: rng.choice(m.group(1).split("|")).strip(), styles[name])
    return f"{kind} / {name}", text


def apply_styles(library, prompt, rows, seed):
    """Return (styled prompt, style labels, style texts) for the stack rows, top to bottom."""
    if not any(row["type"] == PROMPT for row in rows):
        rows = [{"type": PROMPT}, *rows]
    # One generator for every random pick and {a|b} choice, so they don't repeat in lockstep.
    rng = random.Random(seed)
    styled, labels, texts = "", [], []
    for row in rows:
        if row["type"] == PROMPT:
            styled = join(styled, prompt)
            continue
        label, text = pick(library, row, rng)
        styled = join(styled, text)
        labels.append(label)
        texts.append(text)
    return styled, labels, texts
