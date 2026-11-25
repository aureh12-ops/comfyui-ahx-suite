import logging
import os
import shutil

import folder_paths
from comfy_api.latest import io

from .library import ALL, apply_style, labels, load_library

BUILTIN_STYLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles")
SEED_MAX = 0xFFFFFFFFFFFFFFFF


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
        # Read on every schema request, so edited style files show up after refreshing node definitions.
        library = load_library(styles_folder())
        groups = [ALL, *library]
        return io.Schema(
            node_id="AHX_PromptStyle",
            display_name="Prompt Style (ahx)",
            category="ahx/prompt",
            description="Adds a style text (look, camera angle, lighting, surroundings...) before or after a prompt.",
            search_aliases=["styler", "prompt style", "camera angle", "lighting"],
            inputs=[
                io.String.Input("prompt", multiline=True, tooltip="The prompt to style."),
                io.Combo.Input("position", options=["before", "after"], default="after",
                               tooltip="Where the style text goes, relative to the prompt."),
                io.DynamicCombo.Input(
                    "mode",
                    tooltip="pick: one style. random: a new style at each run. cycle: every style of a group in turn, one per run.",
                    options=[
                        io.DynamicCombo.Option("pick", [
                            io.Combo.Input("style", options=labels(library)),
                            io.Int.Input("seed", default=0, min=0, max=SEED_MAX, control_after_generate=io.ControlAfterGenerate.fixed,
                                         tooltip="Changes the {a|b} choices inside the style."),
                        ]),
                        io.DynamicCombo.Option("random", [
                            io.Combo.Input("group", options=groups),
                            io.Int.Input("seed", default=0, min=0, max=SEED_MAX, control_after_generate=True),
                        ]),
                        io.DynamicCombo.Option("cycle", [
                            io.Combo.Input("group", options=groups),
                            io.Int.Input("index", default=0, min=0, max=SEED_MAX, control_after_generate=io.ControlAfterGenerate.increment,
                                         tooltip="Position in the group; goes up by one at each run."),
                        ]),
                    ],
                ),
            ],
            outputs=[
                io.String.Output("prompt"),
                io.String.Output("style", tooltip="The 'Group / Style' that was used."),
            ],
        )

    @classmethod
    def execute(cls, prompt, position, mode) -> io.NodeOutput:
        return io.NodeOutput(*apply_style(load_library(styles_folder()), prompt, position, mode))
