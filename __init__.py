"""ComfyUI entry point for the ahx suite of custom nodes."""

if __package__:  # ComfyUI imports this folder as a package; pytest imports the file bare
    from .prompt_style.node import PromptStyle

    # V3 nodes carry their display names in their schemas.
    NODE_CLASS_MAPPINGS = {
        "AHX_PromptStyle": PromptStyle,
    }

    WEB_DIRECTORY = "./web"

    __all__ = ["NODE_CLASS_MAPPINGS", "WEB_DIRECTORY"]
