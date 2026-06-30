# Channel Routing

Use this reference when the user asks to push, send, notify, publish, or distribute an Agent Knowledge Board.

## Principle

Keep one canonical board JSON. Generate different channel outputs from that JSON:

- Full reading channels get the complete board as visual cards.
- Chat channels get native, native-like, or image-card artifacts with a concise fallback and full-board link.
- Public publishing channels get article cards or draft-card structures.

Do not force the realistic whiteboard HTML into chat apps. Instead, translate the same board JSON into each platform's closest card primitive.

Current `card_payload` values are channel card specs. They are intentionally shaped toward each platform, but they are not guaranteed to be official send-ready webhook payloads until a platform-specific compiler validates and emits that exact API shape.

## Channel Decision Table

| Channel | Best card output | What to include | What to avoid |
|---|---|---|---|
| `email` | Full HTML board card + optional ljg-card multi-image summary | Selectable complete board, source links, optional summary PNGs | Pure image-only email |
| `web` | Full web board card | Complete board, stable URL, share image | Chat-only truncation |
| `feishu` / `lark` | Message card | Header, metrics, board modules, button to full board | Full HTML, dense sticky notes |
| `dingtalk` | ActionCard | Title, short summary, key bullets, button/link | Long nested sections |
| `wecom` / `enterprise-wechat` | Template card or news card | Title, description, key boards, full-board link | Long article body in chat |
| `wechat-mp` | Article card / draft structure | Cover/title, digest, sections, sources | Raw webhook notification style |
| `wechat` | ljg-card `-m` style multi-image cards | 1080x1440 cards: cover, then 1-2 sections per card, optional full-board link | Sending long text blocks or one very tall image as the primary message |
| `markdown` | Markdown card fallback | Complete readable fallback | HTML-only visual assumptions |
| unknown | Generic link card | Title, judgment, board summaries, full-board link | Pretending unsupported platforms have native cards |

## Automatic Selection

When the user names a channel:

1. Normalize aliases:
   - 飞书, Lark -> `feishu`
   - 钉钉, DingTalk -> `dingtalk`
   - 企业微信, 企微, WeCom -> `wecom`
   - 微信公众号, 公众号 -> `wechat-mp`
   - 微信, 个人微信 -> `wechat`
2. Choose the best card output from the table.
3. If the chosen channel is a chat tool, include `full_board_url` or ask where the full board will live.
4. If no URL exists yet, generate the card with a clear placeholder: `[完整白板链接待填]`.
5. Do not send live messages unless the user explicitly asks and provides credentials or webhook configuration.

## Chat Message Budget

For Feishu, DingTalk, and WeCom cards:

- Title
- Date
- One `今日判断`
- Metrics
- 3-5 board summaries
- 1-2 top items per board
- Full-board link

Keep the chat card as a door, not the room.

## Personal WeChat Image Cards

Personal WeChat should use an actual image message as the primary artifact, not a gray text block or long Markdown message.

- Generate static HTML first, then screenshot it into PNGs with `scripts/render_wechat_image_card.py`.
- Use ljg-card `-m` style multi-card output: each card is 1080x1440.
- Card 1 is the cover and today's mainline. Later cards contain at most 2 sections each.
- Show one title, one `今日判断`, 3-4 metrics, and compact section cards.
- Use text fallback only for accessibility, manual forwarding, or when image sending fails.
- Do not use unofficial automation unless the user explicitly accepts that risk.

## Email Summary Images

Email should keep the V2 HTML body as primary because it is searchable, selectable, and link-friendly. If the sender wants a forwardable visual preview, attach or embed the same ljg-card `-m` PNG set as a secondary summary artifact.

## Output Contract

Channel adapters should output:

```json
{
  "channel": "feishu",
  "strategy": "native_message_card",
  "primary_artifact": "card_payload",
  "secondary_artifact": "full_board_html_url",
  "requires_full_board_url": true,
  "send_live": false,
  "card_payload": {},
  "message_preview": "..."
}
```

Use `scripts/render_channel_message.py` to produce this contract.

For production sending, add platform compilers that transform `card_payload` into official API payloads:

- `compile_feishu_card.py`
- `compile_dingtalk_actioncard.py`
- `compile_wecom_card.py`
- `compile_wechat_mp_article.py`
