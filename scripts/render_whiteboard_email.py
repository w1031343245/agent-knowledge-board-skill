#!/usr/bin/env python3
"""Render agent board JSON into a realistic whiteboard sticky-note HTML preview."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


NOTE_COLORS = ["#F7F4EA", "#EEF5F8", "#F1F7EE", "#F8F0ED", "#F3EFF7", "#F4F2EE"]


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def link(label: str, url: str | None) -> str:
    safe_label = esc(label)
    if not url:
        return safe_label
    return f'<a href="{esc(url)}" style="color:#174a91;text-decoration:none;">{safe_label}</a>'


def tags_html(tags: list[Any] | None) -> str:
    if not tags:
        return ""
    return "".join(
        '<span style="display:inline-block;margin:0 6px 6px 0;padding:3px 8px;'
        'border:1px solid #ddd8cc;border-radius:999px;background:#fffdf8;'
        'font-size:12px;line-height:16px;color:#5f635b;">'
        f"{esc(tag)}</span>"
        for tag in tags[:4]
    )


def related_html(related: list[dict[str, Any]] | None) -> str:
    if not related:
        return ""
    rows = []
    for item in related[:2]:
        title = item.get("title") or item.get("path") or "旧内容"
        relation = item.get("relation") or "同主题"
        target = item.get("url") or item.get("path")
        url = target if target and str(target).startswith(("http://", "https://")) else None
        rows.append(f"{esc(relation)} - {link(title, url)}")
    return (
        '<div style="font-size:12px;line-height:18px;color:#62665f;margin-top:8px;">'
        '<strong style="color:#343831;">关联旧内容：</strong>'
        + "<br>".join(rows)
        + "</div>"
    )


def note(title: str, body: str, color: str, width: int = 148, pin: str = "#2f75c9") -> str:
    return f"""
    <div style="display:inline-block;vertical-align:top;width:{width}px;min-height:104px;margin:8px 8px 0 0;padding:13px 14px;background:{color};border:1px solid #ded8cb;border-left:4px solid {pin};box-shadow:0 5px 12px rgba(34,30,20,.08);font-size:13px;line-height:19px;color:#2b2924;">
      <div style="font-size:15px;line-height:21px;font-weight:750;padding-bottom:5px;margin-bottom:8px;border-bottom:1px solid rgba(0,0,0,.12);">{esc(title)}</div>
      <div>{body}</div>
    </div>
    """


def featured_note(featured: dict[str, Any]) -> str:
    if not featured:
        return ""
    source = featured.get("source") or featured.get("url")
    body = f'<div style="margin-bottom:8px;">{esc(featured.get("judgment", ""))}</div>'
    if source:
        body += f'<div style="font-size:12px;">来源：{link(source, source)}</div>'
    return note(featured.get("title", "一句话判断"), body, "#FFF8D8", width=250, pin="#D99A00")


def board_summary(summary: Any) -> str:
    if isinstance(summary, dict):
        parts = [summary.get("count"), summary.get("thread"), summary.get("action")]
        return " / ".join(str(p) for p in parts if p)
    return str(summary or "")


def render_board(board: dict[str, Any], index: int) -> str:
    accent = board.get("accent") or "#2f75c9"
    featured = board.get("featured") or {}
    items = board.get("items") or []
    more = board.get("more") or []
    supporting = []
    if featured.get("why"):
        supporting.append(note("为什么重要", esc(featured.get("why")), "#EEF5F8", width=172, pin="#3F7CBF"))
    if featured.get("tags"):
        supporting.append(note("标签", tags_html(featured.get("tags")), "#F8F0ED", width=172, pin="#C56B58"))
    supporting.append(related_html(featured.get("related")))
    for item in items[:2]:
        supporting.append(
            note(
                item.get("title", "摘要"),
                esc(item.get("summary", "")),
                NOTE_COLORS[(index + 1) % len(NOTE_COLORS)],
                width=172,
                pin=accent,
            )
        )
    mini = []
    for entry in more[:8]:
        if isinstance(entry, dict):
            label = entry.get("label") or entry.get("title") or entry.get("url") or ""
            url = entry.get("url")
        else:
            label, url = str(entry), None
        mini.append(
            '<span style="display:inline-block;margin:6px 6px 0 0;padding:4px 8px;'
            'background:#f8f6ee;border:1px solid #e2dccf;border-radius:999px;'
            'font-size:12px;line-height:16px;color:#5f635d;">'
            f"{link(label, url)}</span>"
        )
    mini_html = (
        '<div style="margin-top:10px;padding-top:8px;border-top:1px solid #ebe6dc;">'
        '<span style="font-size:12px;line-height:18px;color:#7a7f76;margin-right:6px;">补充索引</span>'
        + "".join(mini)
        + "</div>"
        if mini
        else ""
    )
    return f"""
    <section style="border-top:1px solid #d6d3ca;padding:20px 0 22px 0;">
      <div style="display:inline-block;vertical-align:top;width:118px;margin-right:14px;">
        <div style="border-left:5px solid {esc(accent)};padding:8px 0 8px 10px;font-size:18px;line-height:24px;font-weight:760;color:#20241f;">{esc(board.get("name", "Board"))}</div>
      </div>
      <div style="display:inline-block;vertical-align:top;width:560px;">
        <div style="font-size:12px;line-height:18px;color:#62665f;background:#f5f4ef;border:1px solid #e2ded3;padding:8px 10px;margin-bottom:8px;">{esc(board_summary(board.get("summary")))}</div>
        {featured_note(featured)}
        {"".join(supporting)}
        {mini_html}
      </div>
    </section>
    """


def metric_text(metric: Any) -> str:
    if isinstance(metric, dict):
        return str(metric.get("label") or metric.get("value") or "")
    return str(metric)


def render(data: dict[str, Any]) -> str:
    metrics = " | ".join(metric_text(m) for m in (data.get("metrics") or [])[:4])
    boards = "".join(render_board(board, i) for i, board in enumerate(data.get("boards", [])))
    full_url = data.get("full_board_url")
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(data.get("title", "Agent Daily Board"))}</title></head>
<body style="margin:0;background:#ebe7df;padding:24px 12px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',Arial,sans-serif;color:#222;">
  <main style="max-width:760px;margin:0 auto;background:#fbfaf6;border:1px solid #c7c4bc;border-radius:10px;box-shadow:0 14px 36px rgba(0,0,0,.12);padding:26px 28px 30px 28px;">
    <header style="border-bottom:2px solid #2c5c91;padding-bottom:14px;margin-bottom:16px;">
      <div style="font-size:34px;line-height:42px;font-weight:800;letter-spacing:0;">{esc(data.get("title", "Agent Daily Board"))}</div>
      <div style="font-size:15px;line-height:22px;text-align:right;color:#4f544e;">{esc(data.get("date", ""))}</div>
    </header>
    <div style="background:#ffffff;border:1px solid #ded9ce;border-left:5px solid #2c5c91;border-radius:6px;box-shadow:0 5px 12px rgba(0,0,0,.07);padding:12px 14px;margin-bottom:14px;">
      <div style="font-size:18px;line-height:24px;font-weight:760;color:#20241f;">今日判断</div>
      <div style="font-size:14px;line-height:22px;margin-top:6px;color:#343831;">{esc(data.get("overall_judgment", ""))}</div>
      <div style="font-size:12px;line-height:18px;color:#6c7169;margin-top:8px;">{esc(metrics)} {link("查看完整白板", full_url) if full_url else ""}</div>
    </div>
    {boards}
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render agent board JSON as whiteboard sticky-note HTML.")
    parser.add_argument("input", help="Path to board JSON file.")
    parser.add_argument("--output", help="Output HTML path. Defaults to input filename with -whiteboard.html.")
    args = parser.parse_args()
    input_path = Path(args.input)
    data = json.loads(input_path.read_text(encoding="utf-8"))
    output_path = Path(args.output) if args.output else input_path.with_name(input_path.stem + "-whiteboard.html")
    output_path.write_text(render(data), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
