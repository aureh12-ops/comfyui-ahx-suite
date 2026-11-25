import logging
import os
import shutil

import folder_paths
from comfy_api.latest import io, ui

from .library import apply_styles, load_library

BUILTIN_STYLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles")
SEED_MAX = 0xFFFFFFFFFFFFFFFF
# Drawn by web/prompt_style.js: rows of styles you add, remove and reorder.
StyleStack = io.Custom("AHX_STYLE_STACK")


def styles_folder():
    """The user's style library, outside the pack so updates never overwrite edits."""
    folder = os.path.join(folder_paths.get_user_directory(), "default", "ahx-styles")
    if not os.path.isdir(folder):
        shutil.copytree(BUILTIN_STYLES, folder)
        logging.info(f"Prompt Style (ahx): copied the built-in styles to {folder}")
    return folder


class PromptStyle(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="AHX_PromptStyle",
            display_name="Prompt Style (ahx)",
            category="ahx/prompt",
            description="Stacks style texts (look, lighting, view angle, location, era...) around a prompt.",
            search_aliases=["styler", "prompt style", "camera angle", "lighting"],
            inputs=[
                io.String.Input("prompt", multiline=True, tooltip="The prompt to style."),
                io.Int.Input("seed", default=0, min=0, max=SEED_MAX, control_after_generate=True,
                             tooltip="Picks the (random) styles and the {a|b} choices inside the styles."),
                # Read on every schema request, so edited style files show up after refreshing node definitions.
                # [name, text] pairs keep the file order in JS, where number-like keys would be sorted first.
                StyleStack.Input("styles", tooltip="The styles, in order, around your prompt.", extra_dict={
                    "library": {kind: list(styles.items()) for kind, styles in load_library(styles_folder()).items()},
                }),
            ],
            outputs=[
                io.String.Output("prompt"),
                io.String.Output("style", tooltip="The 'Type / Style' of every style used."),
            ],
        )

    @classmethod
    def execute(cls, prompt, seed, styles) -> io.NodeOutput:
        styled, labels, texts = apply_styles(load_library(styles_folder()), prompt, styles, seed)
        return io.NodeOutput(styled, ", ".join(labels), ui=ui.PreviewText("\n".join(texts)))
