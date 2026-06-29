# Agent Daily Board V2 Layout Spec

## Design Direction

Use the V2 daily-board email layout for `realistic-whiteboard`: restrained hand-journal paper, light tape, readable intelligence cards, and a fixed 720px body. The design should feel like an edited daily intelligence board, not a literal wall of scattered sticky notes. Optimize for screenshot forwarding and quick scanning, not long-webpage browsing.

## Visual Rules

- Page body: warm off-white paper at 720px CSS width.
- Typography: Georgia family for all rendered HTML.
- Blue: only for source links, extension-reading links, and thin section thesis left rules.
- Red: only for sequence numbers, key judgment labels, risks, and action prompts.
- Tape: only on the cover, section labels, and a small number of focus cards.
- Shadows: subtle and low contrast.
- Links: show readable domains only in cards.
- Cards: content-adaptive height; do not crop, hide, or overlap text.
- Screenshot pages: at most 2 sections per page.

Avoid:
- Large blue rectangle borders or summary boxes.
- Orange flow arrows between cards.
- Full paragraphs of red summary text.
- Repeated slogans such as `持续跟踪，闭环优化`.
- `补充索引` blocks or generic `查看更多` links.
- Heavy rotations that make columns look broken.
- Fixed card heights that cut off body text, tags, or source links.

## Information Hierarchy

Top cover:
1. Title: `Agent Daily Board` by default, or the user's preferred title.
2. Subtitle: `先抓重点，再做闭环`.
3. `今日主线`: one concise synthesis sentence.
4. Date and metrics on one quiet meta line.
5. Small red `今日判断` stamp.

Each board:
1. Paper section title.
2. One-line thesis with a blue left rule.
3. Adaptive card layout:
   - Chain layout for clear event progression: event, judgment, impact.
   - Parallel layout for independent hotspots: three equal cards without arrows.
   - Main-side layout for two-card boards: one wider main card and one side card.
4. One concrete `下一步` action bar.
5. One horizontal `延伸阅读` row with up to 3 links or labels.

## Card Structure

Each card should include:
- Stage label: `事件`, `判断`, or `影响`.
- Title: max 2-3 lines.
- Judgment: max 2 lines.
- Facts: up to 2 compact facts.
- Tags: up to 3.
- Source: domain only.
- No related/prior-note lists inside the card body.

Keep text complete and visible. If content is too long, shorten the string before rendering instead of relying on CSS clipping.

## Content Budgets

Per email:
- 4-6 boards.
- 1 overall judgment.
- 12-24 selected items.
- Keep full archives outside the email.

Per board:
- 1 focus card.
- 2 supporting cards.
- 1 action bar.
- 0-3 extension-reading labels.

## Knowledge Association Display

If a prior note is useful, place its short label in the `延伸阅读` row or use one compact fact. If no useful prior note is found, show nothing. Do not show empty placeholders.

Prefer relationship labels:
- `延续`
- `更新`
- `相反观点`
- `补充案例`
- `同主题`
- `待核对`

## Email Compatibility

- Use inline-friendly CSS and selectable text.
- Avoid JavaScript.
- Avoid external fonts.
- Avoid hover-only interactions.
- Use regular links for sources and full board navigation.
- When creating a screenshot preview, export at 2x resolution and capture each split page separately.
