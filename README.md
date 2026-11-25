# comfyui-ahx-suite

A suite of ComfyUI custom nodes. They all live in the **ahx** menu category.

## Nodes

### Prompt Style (ahx)

`ahx/prompt` · builds a prompt from a stack of style texts: a medium (photo, CGI, drawing, cartoon…), a lighting, a view angle, a location, a time of day, a season, an era, a color tone and more. Combine as many types as you like, in any order, to get a unique image or video. It works on text only, so the result fits any model that takes a prompt.

- **prompt**: your prompt. Type it in, or plug in the `prompt` output of another node.
- **seed**: picks the `(random)` styles and the `{a|b}` choices inside the styles. It is set to `randomize`, so each run gives a new mix; set it to `fixed` to keep a result you like.
- **The style stack**: one row per style, joined top to bottom.
  - **+ Add style** adds a row. Each row has a **type** (Lighting, Era…) and a **style** from that type, and shows the style text under it as you pick it.
  - The style list also offers `(random)`, a random style of that type at each seed, and `(cycle)`, every style of that type in turn, one per run. The row shows which one the next run uses. Each row is random or cycles on its own.
  - **your prompt** is a row too: move it with ▲ ▼ like the others to put styles before or after it. **×** removes a row.
  - Blocks are joined with a comma, or a space when the first one already ends with punctuation.
- **Last run**: the box at the bottom shows the style text of the last run, one line per style.
- **Outputs**: `prompt` (the styled prompt) and `style` (every `Type / Style` used, for example in a file name).

**Choices inside a style**: `{a|b|c}` picks one option at each run, so `in a {misty pine forest|sunlit birch forest}` gives a different forest each time.

**Built-in types**: Medium (photo, CGI, hand drawing, painting, cartoon…), and its detailed looks: Photo, Cinematic, 3D render, Cartoon & Anime, Drawing & Painting. Then Lighting, View angle, Shot size, Lens & focus, Composition, Location, Time of day, Season, Era (from the first photographs to today), Weather, Color tone and Mood. Unusual mixes are allowed: try a photo medium with a watercolor look, or an era with a futuristic city.

#### Your style library

On first use, the built-in styles are copied to `ComfyUI/user/default/ahx-styles/`. That folder is your library: edit it freely, and updating this pack never overwrites it.

- Each `.json` file is one type, named after the file. A file is a list of styles:

  ```json
  [
    {"name": "Golden hour", "text": "golden hour sunlight, warm low sun, long soft shadows"},
    {"name": "Neon", "text": "neon lighting, {magenta|cyan|purple} glow"}
  ]
  ```
- Add a style, change a text, or add a whole new file for a new type.
- After a change, press **R** in ComfyUI (refresh node definitions). No restart needed.
- A file with a mistake is skipped, with a warning in the ComfyUI console naming it.
- To get the built-in styles back, or the new types of an update, rename or delete the folder; it is copied again on next use.

## Example workflow

`example_workflows/Prompt Style - style stack.json` stacks a fixed medium, a random era, view angle, lighting and location, and a time of day that cycles, into a Preview Any node. It needs no model. In ComfyUI, find it in the Templates browser under this pack.

## Install

Clone this repo into ComfyUI's `custom_nodes` folder, then restart ComfyUI:

```
cd ComfyUI/custom_nodes
git clone https://github.com/aureh12-ops/comfyui-ahx-suite
```

## Tests

The Python tests need only `pytest`, not ComfyUI: small stand-ins replace the ComfyUI modules. The JavaScript tests need Node.js; the browser smoke test also needs Playwright (or `playwright-core` and an installed Chrome) and skips without it.

```
python -m pytest
node --test "tests/web/*.test.mjs"
node tests/web/prompt_style_dom_smoke.mjs
```

## License

MIT
