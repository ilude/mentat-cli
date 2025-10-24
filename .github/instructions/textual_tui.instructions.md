---
applyTo:
  - "**/*.py"
---

# Textual & Rich Reference Notes

This instruction file collects the Textual and Rich guidance that drove the recent Mentat REPL work. Use it whenever we adjust layout, styling, or logging for the TUI.

---

## Core Layout Patterns (Textual)
- **Vertical layout is default** on Screen; children render top-to-bottom in compose order. Use explicit containers when you need different flow.
- **Containers**:
  - `Vertical` / `Horizontal`: quick column or row grouping; respect `layout` rules from CSS.
  - `Grid`: set `layout: grid` plus `grid-size`, `grid-columns`, and `grid-rows` when you need cell-level control. Combine with `column-span` / `row-span` for complex shapes.
- **Docking** keeps chrome fixed. Add `dock: bottom;` (or top/left/right) to pin widgets like status bars or prompt areas that should never scroll away.
- **Order matters**: when multiple widgets dock to the same edge, the last yielded sits closest to the edge. Yield footer-like widgets after content to avoid overlap.
- **Overflow**: `overflow-y: auto;` on scrolling containers yields scrollbars; `overflow-x: auto;` enables sideways scrolling.

## Prompt & Chrome Placement Tips
- Wrap non-scrolling chrome in a dedicated container (for example, Container with id "chrome") and dock that container; its children can stack vertically inside it.
- Keep the scrollable chat or history region in a sibling container without docking so it consumes the remaining space.
- Avoid web CSS habits (no flex, auto margins, or gap); Textual CSS has its own rule set.
- Use height: auto with padding on prompt containers to let the input resize naturally; prefer min-height over padding hacks when you need extra breathing room.

## CSS Essentials (Textual)
- Selectors use widget types, hash prefixes for ids, and dot prefixes for classes. Combine classes (for example chat.log) when you need multiple style tags.
- Specificity: ids outrank classes, and classes outrank types. The last matching rule wins if specificity ties. The !important flag exists but keep it rare.
- You can nest selectors inside rule blocks; the ampersand stands for the outer selector (Textual 0.47+).
- CSS variables (for example $accent: color value) help keep theme accents consistent across widgets.
- Inspect the DOM with Textual Devtools (run textual run app.py --dev) to confirm widget hierarchy and class assignments when styles misbehave.

## Scrolling Content vs Fixed Bars
- Put scrollable regions (logs, history lists) inside VerticalScroll or widgets that expose scroll bars.
- When using RichLog, set an explicit height or let the parent control it via layout; avoid docking it unless you intend to freeze it.
- For sticky prompts: dock the prompt container, ensure the chat container does not have conflicting docks, and let it fill remaining space using height: 1fr or expand=True in Python code when appropriate.

## Rich Usage Inside Textual
- RichLog renders Rich renderables (markdown, tables, syntax) and handles auto-scrolling. Use write(renderable, scroll_end=True) to keep the newest message visible.
- Rich supports Console Markup (for example [bold magenta]), Markdown rendering (Markdown("**Heading**")), and syntax highlighting (Syntax(code, "python")).
- Pretty printing (from rich import pretty; pretty.install()) helps during debugging but keep it out of production paths unless you want formatted reprs.
- Combine Panel, Table, and Group renderables to give chat replies consistent styling before pushing them into the log.

## When Troubleshooting Layout
1. Start by confirming the compose order; mismatch there explains many docking surprises.
2. Check the `id` / `classes` assigned to each widget; a stray class can inherit unintended CSS.
3. Use Textual devtools or call self.query for the widget with id prompt-container during debugging to inspect live layout metrics.
4. Remove legacy CSS carried over from web habits (e.g., `margin-top: auto`); replace with supported rules like `padding`, `offset`, or `align`.
5. Re-run `textual run` with `--dev` to live tweak `.tcss` until the prompt sits where you expect.

---

Keep this reference close when iterating on the Mentat REPL. Expand it when we adopt new widgets (DataTable, TextArea, etc.) so future tweaks stay consistent with Textual best practices.
