// node --test "tests/web/*.test.mjs"
import assert from "node:assert/strict";
import { test } from "node:test";
import { CYCLE, PROMPT, RANDOM, changeType, hint, isMissing, moveRow, newRow, stepCycles, toLibrary } from "../../web/style_stack.js";

// Number-like names would come first in a plain JS object; pairs keep the file order.
const library = toLibrary({
  Era: [["1920s", "1920s photo"], ["1900", "1900 photo"]],
  Lighting: [["Soft", "soft light"], ["Neon", "neon {pink|blue} glow"]],
});

test("toLibrary keeps the file order", () => {
  assert.deepEqual([...library.Era.keys()], ["1920s", "1900"]);
});

test("a new row takes the first type not in the stack yet", () => {
  assert.deepEqual(newRow(library, [{ type: PROMPT }]), { type: "Era", style: "1920s" });
  assert.deepEqual(newRow(library, [{ type: "Era", style: "1900" }]), { type: "Lighting", style: "Soft" });
  assert.deepEqual(newRow(library, [{ type: "Era" }, { type: "Lighting" }]), { type: "Era", style: "1920s" });
});

test("changing the type keeps random and cycle, and resets the cycle position", () => {
  assert.deepEqual(changeType(library, { type: "Era", style: "1900" }, "Lighting"), { type: "Lighting", style: "Soft" });
  assert.deepEqual(changeType(library, { type: "Era", style: RANDOM }, "Lighting"), { type: "Lighting", style: RANDOM });
  assert.deepEqual(changeType(library, { type: "Era", style: CYCLE, index: 3 }, "Lighting"), { type: "Lighting", style: CYCLE });
});

test("moveRow swaps neighbours and stops at the ends", () => {
  const rows = ["a", "b", "c"];
  assert.deepEqual(moveRow(rows, 0, 1), ["b", "a", "c"]);
  assert.deepEqual(moveRow(rows, 2, -1), ["a", "c", "b"]);
  assert.equal(moveRow(rows, 0, -1), rows);
  assert.equal(moveRow(rows, 2, 1), rows);
  assert.deepEqual(rows, ["a", "b", "c"]);
});

test("hint shows what the row adds", () => {
  assert.equal(hint(library, { type: "Lighting", style: "Neon" }), "neon {pink|blue} glow");
  assert.equal(hint(library, { type: "Lighting", style: RANDOM }), "A random Lighting style, picked by the seed.");
  assert.equal(hint(library, { type: "Era", style: CYCLE }), "Next run: 1/2 1920s: 1920s photo");
  assert.equal(hint(library, { type: "Era", style: CYCLE, index: 3 }), "Next run: 2/2 1900: 1900 photo");
  assert.equal(hint(library, { type: "Gone", style: "x" }), '"Gone" is not in the style library.');
  assert.equal(hint(library, { type: "Era", style: "Gone" }), '"Gone" is not in Era.');
});

test("isMissing flags rows whose type or style left the library", () => {
  assert.equal(isMissing(library, { type: "Era", style: "1900" }), false);
  assert.equal(isMissing(library, { type: "Era", style: RANDOM }), false);
  assert.equal(isMissing(library, { type: "Era", style: CYCLE, index: 9 }), false);
  assert.equal(isMissing(library, { type: "Camera angle", style: "Low angle" }), true);
  assert.equal(isMissing(library, { type: "Camera angle", style: RANDOM }), true);
  assert.equal(isMissing(library, { type: "Era", style: "Gone" }), true);
});

test("stepCycles moves only the cycle rows on", () => {
  const rows = [{ type: PROMPT }, { type: "Era", style: CYCLE }, { type: "Lighting", style: CYCLE, index: 4 }, { type: "Era", style: "1900" }];
  assert.deepEqual(stepCycles(rows), [
    { type: PROMPT }, { type: "Era", style: CYCLE, index: 1 }, { type: "Lighting", style: CYCLE, index: 5 }, { type: "Era", style: "1900" },
  ]);
});
