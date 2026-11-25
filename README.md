# comfyui-ahx-suite

A suite of ComfyUI custom nodes. They all live in the **ahx** menu category.

## Nodes

### Prompt Style (ahx)

`ahx/prompt` · adds a block of style text before or after a prompt: a look (photo, anime, 3D, painting…), a camera angle, a shot size, a lens, a lighting, surroundings, a mood or the time and weather. It works on text only, so the result fits any model that takes a prompt, for images or video.

- **prompt**: your prompt. Type it in, or plug in the `prompt` output of another node.
- **position**: put the style text `before` or `after` the prompt. The two are joined with a comma, or a space when the first part already ends with punctuation.
- **mode**:
  - `pick`: you choose the style. Its `seed` changes the `{a|b}` choices inside the style (see below).
  - `random`: a new style at each run, from one group or `(all)`. The same seed gives the same pick, so a result you like can be reproduced.
  - `cycle`: every style of a group in turn, one per run. Queue as many runs as the group has styles to compare them all.
- **Outputs**: `prompt` (the styled prompt) and `style` (the `Group / Style` that was used, for example in a file name).

**Chain them** to build a scene in layers, each with its own position and mode:

`Look (pick, before) → Camera angle (random, after) → Lighting (random, after) → Surroundings (random, after)`

**Choices inside a style**: `{a|b|c}` picks one option at each run, so `in a {misty pine forest|sunlit birch forest}` gives a different forest each time.

**Built-in groups**: 3D render, Camera angle, Cartoon & Anime, Cinematic, Drawing & Painting, Lens & focus, Lighting, Mood & colors, Photo, Shot size, Surroundings, Time & weather.

#### Your style library

On first use, the built-in styles are copied to `ComfyUI/user/default/ahx-styles/`. That folder is your library: edit it freely, and updating this pack never overwrites it.

- Each `.json` file is one group, named after the file. A file is a list of styles:

  ```json
  [
    {"name": "Golden hour", "text": "golden hour sunlight, warm low sun, long soft shadows"},
    {"name": "Neon", "text": "neon lighting, {magenta|cyan|purple} glow"}
  ]
  ```
- Add a style, change a text, or add a whole new file for a new group.
- After a change, press **R** in ComfyUI (refresh node definitions). No restart needed.
- A file with a mistake is skipped, with a warning in the ComfyUI console naming it.
- To get the built-in styles back, rename or delete the folder; it is copied again on next use.

## Example workflow

`example_workflows/Prompt Style - random scene.json` chains four Prompt Style nodes into a Preview Any node. It needs no model. In ComfyUI, find it in the Templates browser under this pack.

## Install

Clone this repo into ComfyUI's `custom_nodes` folder, then restart ComfyUI:

```
cd ComfyUI/custom_nodes
git clone https://github.com/aureh12-ops/comfyui-ahx-suite
```

## Tests

The tests need only `pytest`, not ComfyUI: small stand-ins replace the ComfyUI modules.

```
python -m pytest
```

## License

MIT
