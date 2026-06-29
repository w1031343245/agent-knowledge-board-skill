# Realistic Whiteboard Sticky Style

## Direction

Use this style when the user wants the knowledge cards to feel like a real whiteboard-inspired briefing. The result should feel tactile, warm, and useful, not childish or cluttered.

## Visual Language

- Whiteboard surface: near-white with subtle gloss, faint marker traces, and quiet gray dividers.
- Frame: thin aluminum or light gray border when rendering a full preview.
- Notes: use pale yellow only for the featured item; use muted off-white panels with restrained accent rails for supporting notes.
- Attachment cues: optional and very subtle; do not rely on visible pins or magnets for every note.
- Shadows: soft and low-contrast. Avoid floating-note chaos.
- Typography: readable printed Chinese for email HTML; handwritten-style text is acceptable only in static preview images.

## Information Roles

- Featured panel: featured item / `一句话判断`.
- Supporting panels: `为什么重要`, `标签`, and the top 1-2 supporting summaries. Keep source links as quiet lines inside the relevant item, not as standalone cards.
- Quiet inline line: optional `关联旧内容`.
- Small chips: extra index items.

## Layout

Use category lanes rather than a random wall:

1. Top overview strip: `今日判断`, metrics, and `查看完整白板`.
2. Each board is a horizontal lane with a clear label on the left and content on the right.
3. Each lane has one featured panel and 2-4 smaller supporting panels.
4. Optional related knowledge appears as a quiet inline line only when clearly relevant.
5. Extra useful items appear as compact `补充索引` chips. Avoid generic `查看更多` calls to action.

## Density Rules

- Keep each board to 1 featured note, 2-4 supporting notes, and up to 8 mini-index labels.
- If a board has too many items, keep only the useful names in `补充索引` and leave the full archive outside the email.
- Do not shrink note text below readability just to fit more content.

## Email Constraints

- Use CSS-rendered rectangles and shadows, not a single image, for real email output.
- Keep all important content as selectable text.
- Avoid JavaScript and hover-only interactions.
- Inline CSS where possible when sending as an email.
