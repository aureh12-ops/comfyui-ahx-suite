// Prompt Style (ahx): the stack of style rows around the prompt, and the style text of the last run.

import { app } from "../../scripts/app.js";
import { CYCLE, PROMPT, RANDOM, changeType, hint, isMissing, moveRow, newRow, stepCycles, toLibrary } from "./style_stack.js";

// Fixed heights, so the node knows its size before the rows are on screen.
const LINE = 22; // buttons and lists
const HINT = 28; // two lines of style text under a row
const GAP = 4;
const LAST_RUN = 48; // smallest height of the last run box
const MARGIN = 4; // ComfyUI shrinks the element by this much on each side

const CSS = `
.ahx-stack { display: flex; flex-direction: column; gap: ${GAP}px; height: 100%; box-sizing: border-box;
  font: 12px sans-serif; color: var(--input-text, #ddd); }
.ahx-stack-rows { display: flex; flex-direction: column; gap: ${GAP}px; }
.ahx-stack-row { display: grid; grid-template-columns: 20px 20px minmax(0, 1fr) minmax(0, 1.3fr) 20px;
  grid-template-rows: ${LINE}px ${HINT}px; gap: ${GAP}px 3px; }
.ahx-stack-row.ahx-stack-prompt { grid-template-rows: ${LINE}px; }
.ahx-stack button, .ahx-stack select { box-sizing: border-box; height: ${LINE}px; min-width: 0; margin: 0; padding: 0 4px;
  font: inherit; color: inherit; background: var(--comfy-input-bg, #222);
  border: 1px solid var(--border-color, #555); border-radius: 4px; }
.ahx-stack button { padding: 0; cursor: pointer; font-size: 10px; }
.ahx-stack button.ahx-stack-add { font-size: 12px; }
.ahx-stack button:disabled { opacity: 0.3; cursor: default; }
.ahx-stack-hint { grid-column: 3 / 6; font-size: 11px; line-height: 14px; color: var(--descrip-text, #999);
  overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.ahx-stack-hint.ahx-stack-missing { color: var(--error-text, #ff6b6b); }
.ahx-stack-label { grid-column: 3 / 6; box-sizing: border-box; line-height: ${LINE - 2}px; text-align: center;
  color: var(--descrip-text, #999); border: 1px dashed var(--border-color, #555); border-radius: 4px; }
.ahx-stack-last { flex: 1; min-height: 0; overflow: auto; white-space: pre-wrap; padding: 4px 6px; box-sizing: border-box;
  background: var(--comfy-input-bg, #222); border: 1px solid var(--border-color, #555); border-radius: 4px; }
.ahx-stack-last:empty::before { content: "The style text of the last run shows here."; color: var(--descrip-text, #999); }
`;

function el(tag, props, ...children) {
  const element = Object.assign(document.createElement(tag), props);
  element.append(...children);
  return element;
}

const button = (textContent, title, onclick, disabled = false) => el("button", { textContent, title, onclick, disabled });

/** A dropdown list. A value no longer in the library stays listed, so the row never changes by itself. */
function select(values, current, onchange) {
  const list = el("select", { onchange: () => onchange(list.value) },
    ...(values.includes(current) ? values : [current, ...values]).map((v) => el("option", { value: v, textContent: v })));
  list.value = current;
  return list;
}

function addStyleStack(node, name, spec) {
  let library = toLibrary(spec.library);
  let rows = [{ type: PROMPT }];

  const list = el("div", { className: "ahx-stack-rows" });
  const add = el("button", { className: "ahx-stack-add", textContent: "+ Add style", onclick: () => update([...rows, newRow(library, rows)], true) });
  const lastRun = el("div", { className: "ahx-stack-last", title: "The style text of the last run" });
  const root = el("div", { className: "ahx-stack" }, list, add, lastRun);
  // Keys typed in the lists must not reach ComfyUI's shortcuts (Delete would remove the node).
  root.addEventListener("keydown", (e) => e.stopPropagation());

  function render() {
    const types = Object.keys(library);
    list.replaceChildren(...rows.map((row, i) => {
      const set = (changed) => update(rows.map((r, j) => (j === i ? changed : r)));
      const moves = [
        button("▲", "Move up", () => update(moveRow(rows, i, -1)), i === 0),
        button("▼", "Move down", () => update(moveRow(rows, i, 1)), i === rows.length - 1),
      ];
      if (row.type === PROMPT) {
        return el("div", { className: "ahx-stack-row ahx-stack-prompt" }, ...moves,
          el("div", { className: "ahx-stack-label", textContent: "your prompt" }));
      }
      const text = hint(library, row);
      return el("div", { className: "ahx-stack-row" }, ...moves,
        select(types, row.type, (type) => set(changeType(library, row, type))),
        select([RANDOM, CYCLE, ...(library[row.type]?.keys() ?? [])], row.style, (style) => set({ type: row.type, style })),
        button("×", "Remove", () => update(rows.filter((_, j) => j !== i), true)),
        el("div", { className: `ahx-stack-hint${isMissing(library, row) ? " ahx-stack-missing" : ""}`, textContent: text, title: text }));
    }));
    add.disabled = !types.length;
  }

  function update(next, resize = false) {
    rows = next;
    render();
    if (resize) node.setSize([node.size[0], node.computeSize([...node.size])[1]]);
    node.setDirtyCanvas(true, true);
  }

  const widget = node.addDOMWidget(name, "ahx_style_stack", root, {
    socketless: true, // the rows can't come from a link
    hideOnZoom: false,
    margin: MARGIN,
    getValue: () => rows,
    setValue: (value) => {
      if (Array.isArray(value)) rows = value;
      render();
    },
    getMinHeight: () =>
      2 * MARGIN + rows.reduce((h, r) => h + LINE + GAP + (r.type === PROMPT ? 0 : HINT + GAP), 0) + LINE + GAP + LAST_RUN,
  });
  // Runs once the prompt has been queued with the current rows.
  widget.afterQueued = () => {
    if (rows.some((r) => r.style === CYCLE)) update(stepCycles(rows));
  };

  const onExecuted = node.onExecuted;
  node.onExecuted = function (output) {
    onExecuted?.apply(this, arguments);
    lastRun.textContent = output?.text?.[0] ?? "";
  };
  // ComfyUI calls this on every node when node definitions are refreshed (R): style files may have changed.
  const refresh = node.refreshComboInNode;
  node.refreshComboInNode = function (defs) {
    refresh?.apply(this, arguments);
    const fresh = defs[this.type]?.input?.required?.[name]?.[1];
    if (fresh) {
      library = toLibrary(fresh.library);
      render();
    }
  };

  render();
  return widget;
}

document.head.append(el("style", { textContent: CSS }));

app.registerExtension({
  name: "ahx.prompt_style",
  getCustomWidgets: () => ({
    AHX_STYLE_STACK: (node, name, [, spec]) => ({ widget: addStyleStack(node, name, spec), minWidth: 360 }),
  }),
});
