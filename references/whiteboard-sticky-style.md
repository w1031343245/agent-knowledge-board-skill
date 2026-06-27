# Realistic Whiteboard Sticky Style

## Direction

Use this style when the user wants the knowledge cards to feel like a real whiteboard with physical sticky notes. The result should feel tactile, warm, and useful, not childish.

## Visual Language

- Whiteboard surface: near-white with subtle gloss, faint marker traces, and quiet gray dividers.
- Frame: thin aluminum or light gray border when rendering a full preview.
- Notes: pale yellow for featured notes; muted blue, mint, coral, lavender, and gray for supporting notes.
- Attachment cues: tiny round magnets, small tape strips, or subtle folded corners. Use sparingly.
- Shadows: soft paper shadows to create depth.
- Typography: readable printed Chinese for email HTML; handwritten-style text is acceptable only in static preview images.

## Information Roles

- Large yellow sticky note: featured item / `一句话判断`.
- Blue sticky note: `为什么重要`.
- Green sticky note: `来源`.
- Coral sticky note: `标签`.
- Lavender or gray mini-note: optional `关联旧内容`.
- Small chips or mini notes: extra index items.

## Layout

Use category lanes rather than a random wall:

1. Top overview strip: `今日判断`, metrics, and `查看完整白板`.
2. Each board is a horizontal lane with a label on the left.
3. Each lane has one featured note and 2-4 smaller notes.
4. Optional related knowledge appears as a small lavender note only when clearly relevant.
5. More items appear as compact mini notes or chips, never as tiny full cards.

## Density Rules

- Keep each board to 1 featured note, 2-4 supporting notes, and up to 8 mini-index labels.
- If a board has too many items, route the overflow to `查看更多 ->`.
- Do not shrink note text below readability just to fit more content.

## Email Constraints

- Use CSS-rendered rectangles and shadows, not a single image, for real email output.
- Keep all important content as selectable text.
- Avoid JavaScript and hover-only interactions.
- Inline CSS where possible when sending as an email.
