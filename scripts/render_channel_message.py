#!/usr/bin/env python3
"""Render channel-specific delivery plans and message previews for an agent board."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALIASES = {
    "飞书": "feishu",
    "lark": "feishu",
    "feishu": "feishu",
    "钉钉": "dingtalk",
    "dingding": "dingtalk",
    "dingtalk": "dingtalk",
    "企业微信": "wecom",
    "企微": "wecom",
    "wecom": "wecom",
    "enterprise-wechat": "wecom",
    "微信公众号": "wechat-mp",
    "公众号": "wechat-mp",
    "wechat-mp": "wechat-mp",
    "微信": "wechat",
    "个人微信": "wechat",
    "wechat": "wechat",
    "邮箱": "email",
    "邮件": "email",
    "email": "email",
    "网页": "web",
    "web": "web",
    "markdown": "markdown",
    "md": "markdown",
}

STRATEGIES = {
    "email": ("html_board_card", "full_board_html_card", "text_fallback", False),
    "web": ("web_board_card", "full_web_board_card", "shareable_url", False),
    "feishu": ("native_message_card", "card_payload", "full_board_html_url", True),
    "dingtalk": ("action_card", "card_payload", "full_board_html_url", True),
    "wecom": ("template_or_news_card", "card_payload", "full_board_html_url", True),
    "wechat-mp": ("article_card_draft", "card_payload", "source_links", False),
    "wechat": ("image_card", "wechat_image_card_png", "manual_forward_text", False),
    "markdown": ("markdown_card_fallback", "markdown_card", "source_links", False),
}


def normalize_channel(channel: str) -> str:
    key = channel.strip().lower()
    return ALIASES.get(key, ALIASES.get(channel.strip(), key or "markdown"))


def text(value: Any) -> str:
    return "" if value is None else str(value)


def metric_label(metric: Any) -> str:
    if isinstance(metric, dict):
        return text(metric.get("label") or metric.get("value"))
    return text(metric)


def summary_text(summary: Any) -> str:
    if isinstance(summary, dict):
        return " / ".join(text(v) for v in (summary.get("count"), summary.get("thread"), summary.get("action")) if v)
    return text(summary)


def board_lines(board: dict[str, Any], max_items: int = 2) -> list[str]:
    lines = []
    name = text(board.get("name") or "Board")
    summary = summary_text(board.get("summary"))
    lines.append(f"## {name}")
    if summary:
        lines.append(summary)
    featured = board.get("featured") or {}
    if featured.get("title"):
        lines.append(f"- **{text(featured.get('title'))}**")
        if featured.get("judgment"):
            lines.append(f"  {text(featured.get('judgment'))}")
    for item in (board.get("items") or [])[:max_items]:
        title = text(item.get("title"))
        if title:
            lines.append(f"- {title}")
            if item.get("summary"):
                lines.append(f"  {text(item.get('summary'))}")
    return lines


def markdown_preview(data: dict[str, Any], channel: str) -> str:
    title = text(data.get("title") or "Agent Daily Board")
    date = text(data.get("date"))
    metrics = " | ".join(metric_label(m) for m in (data.get("metrics") or [])[:4])
    full_url = text(data.get("full_board_url") or "[完整白板链接待填]")
    lines = [f"# {title}"]
    if date:
        lines.append(date)
    if metrics:
        lines.append(metrics)
    if data.get("overall_judgment"):
        lines.extend(["", f"**今日判断**：{text(data.get('overall_judgment'))}"])

    if channel in {"email", "web", "markdown", "wechat-mp"}:
        boards = data.get("boards") or []
        max_boards = len(boards)
        max_items = 3
    else:
        boards = (data.get("boards") or [])[:5]
        max_boards = len(boards)
        max_items = 1

    for board in boards[:max_boards]:
        lines.append("")
        lines.extend(board_lines(board, max_items=max_items))

    lines.extend(["", f"查看完整白板：{full_url}"])
    return "\n".join(lines).strip() + "\n"


def top_boards(data: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    cards = []
    for board in (data.get("boards") or [])[:limit]:
        featured = board.get("featured") or {}
        cards.append(
            {
                "title": text(board.get("name") or "Board"),
                "summary": summary_text(board.get("summary")),
                "featured_title": text(featured.get("title")),
                "featured_judgment": text(featured.get("judgment")),
            }
        )
    return cards


def card_payload(data: dict[str, Any], channel: str) -> dict[str, Any]:
    title = text(data.get("title") or "Agent Daily Board")
    date = text(data.get("date"))
    full_url = text(data.get("full_board_url") or "[完整白板链接待填]")
    metrics = [metric_label(m) for m in (data.get("metrics") or [])[:4]]
    boards = top_boards(data)
    judgment = text(data.get("overall_judgment"))

    base = {
        "title": title,
        "date": date,
        "judgment": judgment,
        "metrics": metrics,
        "boards": boards,
        "full_board_url": full_url,
    }

    if channel == "feishu":
        return {
            "type": "feishu_message_card_spec",
            "header": {"template": "blue", "title": title},
            "elements": [
                {"tag": "markdown", "content": f"**今日判断**\n{judgment}"},
                {"tag": "div", "fields": [{"is_short": True, "text": m} for m in metrics]},
                {"tag": "markdown", "content": "\n".join(f"- **{b['title']}**：{b['featured_title']}" for b in boards)},
                {"tag": "action", "actions": [{"tag": "button", "text": "查看完整白板", "url": full_url}]},
            ],
            "fallback": markdown_preview(data, channel),
        }
    if channel == "dingtalk":
        return {
            "type": "dingtalk_action_card_spec",
            "title": title,
            "markdown": markdown_preview(data, channel),
            "single_title": "查看完整白板",
            "single_url": full_url,
        }
    if channel == "wecom":
        return {
            "type": "wecom_template_or_news_card_spec",
            "title": title,
            "description": judgment,
            "url": full_url,
            "sections": boards,
            "fallback": markdown_preview(data, channel),
        }
    if channel == "wechat-mp":
        return {
            "type": "wechat_mp_article_card_spec",
            "title": title,
            "digest": judgment[:120],
            "content_markdown": markdown_preview(data, channel),
            "source_url": full_url if full_url != "[完整白板链接待填]" else "",
        }
    if channel == "wechat":
        return {
            "type": "wechat_image_card_spec",
            "title": title,
            "description": judgment,
            "recommended_renderer": "render_wechat_image_card.py",
            "rendering_method": "html_to_png_screenshot",
            "image_format": "png",
            "layout_version": "ljg_card_m_multi_1080x1440",
            "image_size": "1080x1440 per card",
            "render_command": "python scripts/render_wechat_image_card.py <board.json> --output <board-wechat-card.png>",
            "send_as": "multi_image_message",
            "url": full_url if full_url != "[完整白板链接待填]" else "",
            "manual_forward_text": f"{title}：{judgment}\n完整白板：{full_url}",
            "fallback": markdown_preview(data, channel),
        }
    if channel in {"email", "web"}:
        return {
            "type": f"{channel}_visual_board_card_spec",
            "title": title,
            "full_card_artifact": "rendered_html",
            "recommended_renderer": "render_whiteboard_email.py",
            "layout_version": "v2_daily_board_720",
            "render_command": "python scripts/render_whiteboard_email.py <board.json> --output <board-whiteboard.html> --split-pages-dir <pages-dir>",
            "screenshot_rule": "Capture each split page separately; each page contains at most 2 sections.",
            "optional_summary_renderer": "render_wechat_image_card.py",
            "optional_summary_layout": "ljg_card_m_multi_1080x1440",
            "fallback": markdown_preview(data, channel),
        }
    return {
        "type": "generic_link_card_spec",
        **base,
        "fallback": markdown_preview(data, channel),
    }


def delivery_plan(data: dict[str, Any], channel_input: str) -> dict[str, Any]:
    channel = normalize_channel(channel_input)
    strategy, primary, secondary, requires_url = STRATEGIES.get(
        channel, ("generic_link_card", "card_payload", "full_board_html_url", True)
    )
    full_url = data.get("full_board_url")
    return {
        "channel": channel,
        "strategy": strategy,
        "primary_artifact": primary,
        "secondary_artifact": secondary,
        "requires_full_board_url": bool(requires_url),
        "has_full_board_url": bool(full_url),
        "send_live": False,
        "card_payload": card_payload(data, channel),
        "message_preview": markdown_preview(data, channel),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a channel delivery plan from board JSON.")
    parser.add_argument("input", help="Path to board JSON file.")
    parser.add_argument("--channel", required=True, help="Target channel, e.g. feishu, dingtalk, wecom, email.")
    parser.add_argument("--output", help="Optional output JSON path.")
    parser.add_argument("--markdown-only", action="store_true", help="Print only the message preview Markdown.")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    plan = delivery_plan(data, args.channel)

    if args.markdown_only:
        rendered = plan["message_preview"]
    else:
        rendered = json.dumps(plan, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(args.output)
    else:
        print(rendered)


if __name__ == "__main__":
    main()
