export interface Selection {
  start: number;
  end: number;
}

export interface EditResult {
  value: string;
  selectionStart: number;
  selectionEnd: number;
}

export function sanitizeLabel(text: string): string {
  return text.replace(/"/g, '\\"').replace(/\r?\n/g, " ");
}

export function wrapSelection(
  value: string,
  selection: Selection,
  before: string,
  after: string,
  placeholder: string
): EditResult {
  const selected = value.slice(selection.start, selection.end);
  const inner = selected || placeholder;
  const insert = `${before}${inner}${after}`;
  const nextValue = value.slice(0, selection.start) + insert + value.slice(selection.end);
  const selectionStart = selection.start + before.length;
  const selectionEnd = selectionStart + inner.length;
  return { value: nextValue, selectionStart, selectionEnd };
}

function lineBounds(value: string, selection: Selection): { lineStart: number; lineEnd: number } {
  const lineStart = value.lastIndexOf("\n", selection.start - 1) + 1;
  const nextBreak = value.indexOf("\n", selection.end);
  const lineEnd = nextBreak === -1 ? value.length : nextBreak;
  return { lineStart, lineEnd };
}

export function prefixLines(value: string, selection: Selection, prefix: string): EditResult {
  const { lineStart, lineEnd } = lineBounds(value, selection);
  const block = value.slice(lineStart, lineEnd);
  const lines = block.split("\n");
  const prefixed = lines.map((line) => `${prefix}${line}`).join("\n");
  const nextValue = value.slice(0, lineStart) + prefixed + value.slice(lineEnd);
  const addedLength = prefixed.length - block.length;
  return {
    value: nextValue,
    selectionStart: selection.start + prefix.length,
    selectionEnd: selection.end + addedLength,
  };
}

export function numberedListLines(value: string, selection: Selection): EditResult {
  const { lineStart, lineEnd } = lineBounds(value, selection);
  const block = value.slice(lineStart, lineEnd);
  const lines = block.split("\n");
  const prefixed = lines.map((line, index) => `${index + 1}. ${line}`).join("\n");
  const nextValue = value.slice(0, lineStart) + prefixed + value.slice(lineEnd);
  const addedLength = prefixed.length - block.length;
  return {
    value: nextValue,
    selectionStart: selection.start + 3,
    selectionEnd: selection.end + addedLength,
  };
}

export function replaceSelection(value: string, selection: Selection, replacement: string): EditResult {
  const nextValue = value.slice(0, selection.start) + replacement + value.slice(selection.end);
  const selectionStart = selection.start + replacement.length;
  return { value: nextValue, selectionStart, selectionEnd: selectionStart };
}

export function buildLinkMarkdown(selectedText: string): string {
  const label = selectedText || "text";
  return `[${label}](url)`;
}

export function buildEntityDirective(
  entityType: "character" | "item" | "entry",
  slug: string,
  selectedText: string
): string {
  if (!selectedText) return `:${entityType}[${slug}]`;
  const label = sanitizeLabel(selectedText);
  return `:${entityType}[${slug}]{label="${label}"}`;
}
