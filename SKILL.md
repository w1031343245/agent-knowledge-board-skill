---
name: agent-knowledge-board
description: Use when turning information collected by any agent, automation, channel feed, newsletter, email, or research run into readable knowledge cards, whiteboard-style digests, categorized daily boards, Feishu/Lark, DingTalk, WeCom, WeChat, email, or web card messages, or optional links to prior notes.
---

# Agent Knowledge Board

## Overview

Transform raw information streams from any agent or automation into a calm knowledge-board brief. The current preferred visual direction is a realistic whiteboard with tactile sticky notes, while the earlier premium memo style remains acceptable for denser email clients.

Use this skill to:
- List and prioritize today's collected messages.
- Group information into category boards.
- Summarize each board with one featured memo, several compact rows, and an optional compact index for overflow items.
- Link new items to prior knowledge only when a clearly relevant match exists.
- Produce HTML email, Markdown fallback, and/or structured JSON.
- Select an appropriate delivery format for each target channel.

## Quick Workflow

1. **Ask setup questions first**:
   - Ask which visual style the user wants:
     - `realistic-whiteboard` for a realistic whiteboard with tactile sticky notes. This is the default recommendation.
     - `premium-memo` for the earlier clean analyst memo / Linear / Notion style.
     - `markdown-only` for plain Markdown without HTML styling.
   - Ask whether the user has a knowledge base path for optional prior-note linking.
   - Ask which delivery channel(s) the user wants: `email`, `feishu`, `dingtalk`, `wecom`, `wechat-mp`, `wechat`, `web`, or `markdown`.
   - Make the knowledge base path optional. The user can answer "none", "skip", or leave it blank.
   - If the user already provided style, delivery channel, or knowledge base path in the request, do not ask again; confirm the inferred choices briefly and continue.
   - If the user wants a quick run and does not answer, default to `realistic-whiteboard`, no knowledge base, and `email` + `web`.

2. **Normalize inputs** into source items:
   - `title`, `summary/raw_text`, `source`, `published_at`, `channel`, `tags`, `url`.
   - Keep original source links whenever possible.

3. **Cluster and deduplicate**:
   - Merge near-duplicates from different channels.
   - Prefer primary sources over reposts.
   - Preserve secondary links under `related_sources` when useful.

4. **Classify into boards**:
   - Default boards: `今日必看`, `AI / 技术`, `商业 / 市场`, `可行动事项`, `稍后读`.
   - Rename or add boards when the user's domain requires it.
   - Keep the email to 4-6 boards unless the user explicitly wants more.

5. **Rank items**:
   - Featured memo: one strongest item per board.
   - Supporting rows: 2-4 useful items per board.
   - Compact index: remaining useful items as short links or labels.
   - Move weak, duplicate, or non-actionable items to `稍后读`.

6. **Optionally associate prior knowledge**:
   - If the user provides a knowledge base path, search it with `rg` first.
   - Generate 3-6 search terms from each important item: named entities, product names, concepts, authors, and topic phrases.
   - Link 1-3 prior notes only when the match has clear topical overlap or explains continuity, contradiction, a follow-up, or a next action.
   - Omit `related` entirely when no strong match exists. Do not output empty "no related content" placeholders in the email.
   - Label useful relations as `延续`, `更新`, `相反观点`, `补充案例`, `同主题`, or `待核对`.
   - If no knowledge base is available, skip prior links silently unless the user asked for an audit trail.

7. **Write the brief**:
   - Start with a top-level `今日判断`.
   - Show metrics such as `5 个白板`, `精选 18 条`, `待阅读 42 条`.
   - For each board, include a summary strip, one featured memo, compact list rows, and optional `补充索引` chips. Do not add a generic `查看更多` link unless the user explicitly provides a meaningful destination and asks for it.
   - Avoid cramming full articles into email; use the email as a reading radar.
   - Use the user's preferred board title when provided. Otherwise default to `Agent Daily Board`.

8. **Render output based on chosen style**:
   - `realistic-whiteboard`: use `scripts/render_whiteboard_email.py`.
   - `premium-memo`: use `scripts/render_board_email.py`.
   - `markdown-only`: output the hierarchy as Markdown and do not run a renderer.
   - For personal WeChat image delivery, use `scripts/render_wechat_image_card.py` to build a static HTML card and screenshot it into a PNG from the same board JSON.
   - For design decisions, read `references/layout-spec.md`.
   - For the realistic style direction, read `references/whiteboard-sticky-style.md`.
   - For Markdown-only contexts, use the same hierarchy without the HTML styling.

9. **Select channel delivery plan**:
   - Read `references/channel-routing.md` when the user asks about pushing or sending to a channel.
   - Use `scripts/render_channel_message.py` to generate channel-specific card plans and preview messages from the same board JSON.
   - Prefer full visual board cards for email/web and native or native-like card payloads for chat tools.
   - Treat `card_payload` as an intermediate channel card spec unless a platform-specific compiler explicitly says it emits official send-ready payloads.
   - Do not attempt to send to live channels unless the user explicitly provides credentials/webhooks and asks to send.

## Startup Prompt

When the user invokes the skill without providing preferences, ask this concise question before processing:

`你想用哪种风格？1. 写实白板便签（推荐） 2. 高级 memo 简报 3. 纯 Markdown。要推送到哪些渠道？如邮箱、飞书、钉钉、企业微信、公众号、网页。有没有知识库路径要关联？没有可以说“跳过”。`

Do not ask more than this at startup unless the user's input is unusable.

## Knowledge Base Linking Rules

- Prefer local, user-owned notes over web search.
- Do not invent prior-note links. If a relationship is only inferred from memory, mark it as `推测关联`.
- Treat knowledge-base links as optional enrichment, not a required field.
- Use a conservative threshold: when uncertain, omit the relation.
- When quoting prior notes, quote short snippets only; otherwise paraphrase.
- Keep link blocks short: one line per related note is usually enough.
- Prior knowledge should help the user see continuity, contradiction, or next action; do not attach loosely related notes just to look thorough.

## Email Design Rules

- Prefer a realistic whiteboard surface with restrained sticky notes, paper texture, soft shadows, small magnets/tape cues, and clear category lanes.
- Keep the board mature and organized; do not make it a childish or cluttered sticky-note wall.
- Use sticky-note color to express information roles, not decoration.
- Keep email width around 680-760px.
- Use simple HTML and inline CSS; do not use JavaScript, external fonts, complex grids, or interactive-only behavior.
- The email must remain useful even if images are blocked.

## Channel Routing Rules

- Treat the board JSON as the canonical source. Never rewrite content separately per channel.
- Prefer card-style delivery on every channel.
- Email and web receive full visual board cards.
- Feishu/Lark receives native message-card style payloads.
- DingTalk receives ActionCard-style payloads.
- WeCom receives template-card/news-card style payloads when possible.
- WeChat public account receives article-card/draft structure.
- Personal WeChat receives a generated PNG image card as the primary artifact, preferably created from an HTML card screenshot; text copy is only a fallback. Do not rely on unofficial personal-account automation.
- Markdown is only the fallback preview or fallback body, not the preferred channel artifact.
- If a channel is unknown, generate a generic link-card spec plus Markdown fallback.

## Resource Map

- `references/schema.md`: JSON structure for board data.
- `references/layout-spec.md`: visual style, content budgets, and HTML/email constraints.
- `references/whiteboard-sticky-style.md`: realistic whiteboard and sticky-note direction.
- `references/channel-routing.md`: delivery-channel selection rules and output contracts.
- `scripts/render_channel_message.py`: render channel-specific push plans and message previews from board JSON.
- `scripts/render_wechat_image_card.py`: build a personal-WeChat-friendly HTML card and screenshot it into a PNG from board JSON.
- `scripts/render_whiteboard_email.py`: render structured board JSON into the realistic whiteboard style.
- `scripts/render_board_email.py`: render structured board JSON into the earlier premium memo style.
- `assets/sample-board.json`: sample data for testing and as a starting point.
- `assets/agent-whiteboard-preview.png`: current realistic whiteboard preview reference.

## Example Requests

- "Use Agent Knowledge Board to turn today's agent messages into a board email."
- "把某个 agent 今天收集的信息做成知识白板，并关联我的 Obsidian 旧笔记。"
- "Generate JSON and HTML for an Agent Daily Board from these newsletter items."
- "把 Browser Agent / Research Agent / Workflow Agent 收集的信息统一整理成知识卡片。"
- "把这些渠道消息分类成今日必看、AI 技术、商业市场和可行动事项。"
