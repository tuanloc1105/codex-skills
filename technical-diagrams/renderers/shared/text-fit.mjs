// Single-line node text fitting, shared by every renderer.
//
// Node text (`label`, `sublabel`, `tag`) renders as one <text> element with
// text-anchor="middle" and is never wrapped. Left unmeasured, an over-long
// value silently spills across its neighbours while validation still reports
// a clean receipt — the failure mode this module exists to close.
//
// Two halves, always used together:
//   - fittedNodeFontSize shrinks the text toward a legible minimum at render
//     time, so ordinary overruns simply get smaller instead of overlapping.
//   - minimumNodeTextWidth reports the width the text still needs once it has
//     shrunk as far as it may, so validation can reject what shrinking cannot
//     save.
//
// The geometry constants below are shared; the per-field `preferred` and
// `minimum` font sizes are not, because renderers set node text at different
// sizes (architecture sublabels are 9px, the rest are 7px).

import { textUnits } from './utils.mjs';

// widthFactor: px of advance width per text unit, per px of font size.
// horizontalPadding: total px reserved inside the box so text never touches
// the border.
export const nodeTextFit = {
  widthFactor: 0.6,
  horizontalPadding: 8,
};

// Largest font size at or below `preferred` that fits `text` inside `width`,
// floored at `minimum` — below that the text is no longer legible and the
// caller should be reporting a problem instead.
export function fittedNodeFontSize(text, width, preferred, minimum) {
  const units = Math.max(1, textUnits(text));
  const available = Math.max(1, width - nodeTextFit.horizontalPadding);
  const fitted = Math.min(preferred, available / (units * nodeTextFit.widthFactor));
  return Math.max(minimum, Math.floor(fitted * 10) / 10);
}

// Width `text` occupies at its legible minimum. Compare against
// `width - nodeTextFit.horizontalPadding` to decide whether shrink-to-fit can
// rescue it.
export function minimumNodeTextWidth(text, minimum) {
  return textUnits(text) * minimum * nodeTextFit.widthFactor;
}

// Available text width inside a box of `width`.
export function availableNodeTextWidth(width) {
  return width - nodeTextFit.horizontalPadding;
}

// Primary labels are centered, while renderer-owned semantic and brand marks
// occupy a top rail at either edge. Convert each occupied rail into the
// largest symmetric label width whose nearest edge keeps `gap` pixels clear.
// The tightest side wins; left and right reservations are not added together.
export function primaryNodeLabelWidth(width, {
  semanticSide = 'left',
  semanticInset = 6,
  semanticSize = 11,
  brand = false,
  brandSide = 'right',
  brandInset = 6,
  brandSize = 16,
  gap = 2,
} = {}) {
  const marks = [
    { side: semanticSide, inset: semanticInset, size: semanticSize },
    ...(brand ? [{ side: brandSide, inset: brandInset, size: brandSize }] : []),
  ];
  const railWidth = marks.reduce((available, { side, inset, size }) => {
    if (side !== 'left' && side !== 'right') return available;
    return Math.min(available, width - 2 * (inset + size + gap));
  }, width);
  // fittedNodeFontSize subtracts the shared border padding from its input.
  // Add that padding back here so its remaining width is the exact rail-safe
  // text rectangle rather than an accidentally double-padded value.
  return Math.max(1, railWidth + nodeTextFit.horizontalPadding);
}

export function primaryNodeLabelProblem(node, width, minimumFontSize, {
  subject = 'Node',
  ...railOptions
} = {}) {
  const available = primaryNodeLabelWidth(width, railOptions);
  const required = minimumNodeTextWidth(node.label, minimumFontSize);
  if (available - nodeTextFit.horizontalPadding >= required) return null;
  return `${subject} "${node.id}" primary-label rail leaves ${Math.max(0, available - nodeTextFit.horizontalPadding)}px for its label, but `
    + `"${node.label}" needs ~${Math.ceil(required)}px at the ${minimumFontSize}px legible minimum — widen the node or shorten the label.`;
}
