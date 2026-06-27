# Agent Knowledge Board Schema

Use this JSON shape when preparing data for either `scripts/render_whiteboard_email.py` or `scripts/render_board_email.py`.

```json
{
  "title": "Agent Daily Board",
  "date": "2026年6月27日 星期六",
  "overall_judgment": "Agent 信息流正在从阅读列表变成自动分拣后的行动入口。",
  "metrics": [
    { "label": "5 个白板", "value": "5" },
    { "label": "精选 18 条", "value": "18" },
    { "label": "待阅读 42 条", "value": "42" }
  ],
  "full_board_url": "https://example.com/full-board",
  "boards": [
    {
      "name": "AI / 技术",
      "accent": "#3D5A80",
      "summary": {
        "count": "今日 18 条，精选 5 条",
        "thread": "主线：Agent 工具转向后台执行",
        "action": "建议动作：看 2 个工具，收藏 1 篇文章"
      },
      "featured": {
        "title": "OpenAI 新能力影响工作流入口",
        "judgment": "一句话判断：入口正在从聊天框迁移到后台任务。",
        "why": "为什么重要：会影响 agent 的自动分拣与推送方式。",
        "source": "https://example.com",
        "tags": ["AI", "Agent", "Workflow"],
        "related": [
          {
            "title": "旧笔记：Agent 工作流设计",
            "relation": "延续",
            "path": "03-Resources/Agent 工作流设计.md"
          }
        ]
      },
      "items": [
        {
          "title": "新工具 A 发布",
          "summary": "摘要：适合作为 agent 后台执行模块参考。",
          "source": "https://example.com/tool-a",
          "tags": ["工具", "自动化"],
          "related": []
        }
      ],
      "more": [
        { "label": "论文", "url": "https://example.com/paper" },
        { "label": "观点", "url": "https://example.com/opinion" }
      ]
    }
  ]
}
```

## Field Notes

- `metrics` can be either objects with `label`/`value` or plain strings.
- `accent` is optional; the renderer cycles through muted defaults.
- `summary` can be an object or a short string.
- `related` is optional on both featured and item cards. Omit it when no clearly relevant prior knowledge exists; do not force an empty relation into the email.
- `more` can contain objects with `label`/`url` or plain strings.
- Keep `featured` text concise. Email is the scan layer, not the archive.
