# Agent Daily Board Layout Spec

## Design Direction

Use a premium knowledge briefing style inspired by Readwise Reader digests, Notion clean pages, Linear issue updates, and calm analyst memos.

The metaphor is "whiteboard thinking", not "literal sticky-note wall".

## Visual Rules

- Background: warm off-white or very light gray.
- Email body: white or near-white, 680-760px wide.
- Text: charcoal, never pure black.
- Accent: thin left rails, small badges, or status dots only.
- Sections: separated by quiet rules and spacing.
- Cards: memo panels with clear hierarchy; avoid full-surface bright colors.
- Shadows: subtle or none.

Avoid:
- Childish sticky notes.
- Large colorful tiles.
- Neon gradients.
- Dense mini-cards.
- Decorative icons that do not carry information.

## Information Hierarchy

Top of email:
1. Title: `Agent Daily Board` by default, or the user's preferred board title.
2. Date
3. `今日判断`: one concise synthesis sentence
4. Metrics: board count, selected count, unread/backlog count
5. Optional link: `查看完整白板`, only when it points to a useful full board

Each board:
1. Board title and summary strip
2. One featured memo
3. 2-4 supporting rows
4. Optional compact index with short chips or links. Do not add a generic `查看更多` link.

## Content Budgets

Per email:
- 4-6 boards.
- 1 overall judgment.
- 12-24 selected items.
- Keep full content outside the email when there are many items.

Per board:
- 1 featured memo.
- 2-4 supporting rows.
- 4-12 compact-index labels when they add useful scan value.

Per featured memo:
- Title: 18-28 Chinese characters when possible.
- Judgment: 40-70 Chinese characters.
- Why it matters: 40-90 Chinese characters.
- Tags: 2-4.
- Related prior notes: 0-3. Show them only when clearly relevant.

## Knowledge Association Display

Use small, quiet lines below important items:

`关联旧内容：延续 - Agent 工作流设计`

If no useful prior note is found, show nothing. Do not show "暂无关联", "未找到旧知识", or any other placeholder.

Prefer relationship labels:
- `延续`
- `更新`
- `相反观点`
- `补充案例`
- `同主题`
- `待核对`

## Email Compatibility

- Use inline CSS in the final HTML.
- Avoid JavaScript.
- Avoid external fonts.
- Avoid layouts that require hover or click to reveal essential content.
- Use regular links for sources and full board navigation.
