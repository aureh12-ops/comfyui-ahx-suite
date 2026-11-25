// Rows of the Prompt Style stack, without the DOM. prompt_style/library.py reads the same row values.
// A row is {type: "(prompt)"} or {type, style, index?}; style is a style name, "(random)" or "(cycle)".

export const PROMPT = "(prompt)";
export const RANDOM = "(random)";
export const CYCLE = "(cycle)";

/** The node definition's {type: [[name, text], ...]} as {type: Map(name -> text)}, in file order. */
export function toLibrary(spec) {
  return Object.fromEntries(Object.entries(spec ?? {}).map(([type, styles]) => [type, new Map(styles)]));
}

const firstStyle = (library, type) => library[type].keys().next().value;

/** A new style row: the first type not in the stack yet, with its first style. */
export function newRow(library, rows) {
  const types = Object.keys(library);
  const type = types.find((t) => !rows.some((r) => r.type === t)) ?? types[0];
  return { type, style: firstStyle(library, type) };
}

/** The row with another type: (random) and (cycle) stay, a style becomes the new type's first one. */
export function changeType(library, row, type) {
  return { type, style: row.style === RANDOM || row.style === CYCLE ? row.style : firstStyle(library, type) };
}

/** The rows with row i moved up (-1) or down (+1). */
export function moveRow(rows, i, delta) {
  const j = i + delta;
  if (j < 0 || j >= rows.length) return rows;
  const moved = [...rows];
  [moved[i], moved[j]] = [moved[j], moved[i]];
  return moved;
}

/** What the row adds to the prompt, shown under it. */
export function hint(library, row) {
  const styles = library[row.type];
  if (!styles) return `"${row.type}" is not in the style library.`;
  if (row.style === RANDOM) return `A random ${row.type} style, picked by the seed.`;
  if (row.style === CYCLE) {
    const names = [...styles.keys()];
    const i = (row.index ?? 0) % names.length;
    return `Next run: ${i + 1}/${names.length} ${names[i]}: ${styles.get(names[i])}`;
  }
  return styles.get(row.style) ?? `"${row.style}" is not in ${row.type}.`;
}

/** Each (cycle) row moves on to its next style; called once a run is queued. */
export function stepCycles(rows) {
  return rows.map((r) => (r.style === CYCLE ? { ...r, index: (r.index ?? 0) + 1 } : r));
}
