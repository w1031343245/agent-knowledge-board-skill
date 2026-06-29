# Realistic Whiteboard Sticky Style

## Direction

Use this style when the user wants the knowledge cards to feel like papers taped onto a real whiteboard. The result should look like a photographed thinking board: paper strips, tape, ink marks, arrows, and clear sequential flow.

## Visual Language

- Whiteboard surface: clean near-white with faint paper shadows and enough empty space.
- Header: taped paper title on the left, blue boxed judgment strip in the middle, and a red stamped/circled label for emphasis.
- Papers: off-white or lightly tinted sheets with tape at the top, slight rotations, uneven vertical offsets, and lightly irregular paper edges.
- Ink language: red underlines and circled numbers for sequence; blue boxes for summaries/questions; orange arrows for flow.
- Typography: use readable Chinese, but allow handwritten-style fallback fonts such as `Segoe Print` when rendering HTML previews.

## Information Roles

- Main paper card: featured item / `一句话判断`.
- Follow-up paper cards: top 1-2 supporting summaries.
- Blue strip: board summary or "engineer question" style framing.
- Small taped note: compact index items.
- Quiet inline line: optional `关联旧内容`.

## Layout

Use a sequential whiteboard-paper layout:

1. Top: taped title paper, blue judgment strip, red circled `今日判断`.
2. Each board begins with a taped label paper and a blue summary strip.
3. Cards flow left-to-right with orange arrows between them.
4. Each main card has a red circled number and a red underline under the title.
5. Extra useful items appear as a small taped `补充索引` note. Avoid generic `查看更多` calls to action.
6. Avoid rigid grids: vary card angle, tape position, and vertical alignment slightly while keeping the reading order obvious.

## Density Rules

- Keep each board to 1 featured paper, 1-2 supporting papers, and up to 8 mini-index labels.
- If a board has too many items, keep only the useful names in `补充索引` and leave the full archive outside the email.
- Do not shrink note text below readability just to fit more content.

## Email Constraints

- Use CSS-rendered rectangles and shadows, not a single image, for real email output.
- Keep all important content as selectable text.
- Avoid JavaScript and hover-only interactions.
- Inline CSS where possible when sending as an email.
