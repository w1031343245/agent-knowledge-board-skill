#!/usr/bin/env python3
"""Render agent board JSON into a realistic whiteboard sticky-note HTML preview."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


NOTE_COLORS = ["#FFF1A8", "#DDECF7", "#DFF1DD", "#F8D1C9", "#E8DDF4", "#ECEAE3"]


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
    return "".join(f'<span style="display:block;">- {esc(tag)}</span>' for tag in tags[:4])


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
        '<div style="display:inline-block;vertical-align:top;width:150px;min-height:58px;'
        'margin:8px 8px 0 0;padding:10px 12px;background:#E8DDF4;'
        'box-shadow:0 7px 14px rgba(40,35,20,.16);font-size:12px;line-height:18px;color:#34312f;">'
        '<div style="font-weight:700;border-bottom:1px solid rgba(0,0,0,.18);margin-bottom:6px;">关联旧内容</div>'
        + "<br>".join(rows)
        + "</div>"
    )


def note(title: str, body: str, color: str, width: int = 148, pin: str = "#2f75c9") -> str:
    return f"""
    <div style="display:inline-block;vertical-align:top;width:{width}px;min-height:112px;margin:8px 8px 0 0;padding:13px 14px;background:{color};box-shadow:0 9px 16px rgba(34,30,20,.18);font-size:13px;line-height:19px;color:#2b2924;position:relative;">
      <div style="width:14px;height:14px;border-radius:50%;background:{pin};box-shadow:0 2px 4px rgba(0,0,0,.25);margin:-20px auto 7px auto;"></div>
      <div style="font-size:15px;line-height:21px;font-weight:750;border-bottom:1px solid rgba(0,0,0,.18);padding-bottom:4px;margin-bottom:8px;">{esc(title)}</div>
      <div>{body}</div>
    </div>
    """


def featured_note(featured: dict[str, Any]) -> str:
    if not featured:
        return ""
    source = featured.get("source") or featured.get("url")
    body = (
        f'<div style="margin-bottom:8px;">{esc(featured.get("judgment", ""))}</div>'
        f'<div style="font-size:12px;line-height:18px;margin-bottom:8px;">{esc(featured.get("why", ""))}</div>'
    )
    if source:
        body += f'<div style="font-size:12px;">来源：{link(source, source)}</div>'
    return note(featured.get("title", "一句话判断"), body, "#FFF1A8", width=245, pin="#E5A500")


def board_summary(summary: Any) -> str:
    if isinstance(summary, dict):
        parts = [summary.get("count"), summary.get("thread"), summary.get("action")]
        return " / ".join(str(p) for p in parts if p)
    return str(summary or "")


def render_board(board: dict[str, Any], index: int) -> str:
    featured = board.get("featured") or {}
    items = board.get("items") or []
    more = board.get("more") or []
    supporting = []
    if featured.get("why"):
        supporting.append(note("为什么重要", esc(featured.get("why")), "#DDECF7", pin="#2f75c9"))
    if featured.get("source") or featured.get("url"):
        source = featured.get("source") or featured.get("url")
        supporting.append(note("来源", f"- {link(source, source)}", "#DFF1DD", pin="#2E9D55"))
    if featured.get("tags"):
        supporting.append(note("标签", tags_html(featured.get("tags")), "#F8D1C9", pin="#e7e2d8"))
    supporting.append(related_html(featured.get("related")))
    for item in items[:2]:
        supporting.append(note(item.get("title", "摘要"), esc(item.get("summary", "")), NOTE_COLORS[(index + 1) % len(NOTE_COLORS)], width=160))
    mini = []
    for entry in more[:8]:
        if isinstance(entry, dict):
            label = entry.get("label") or entry.get("title") or entry.get("url") or ""
            url = entry.get("url")
        else:
            label, url = str(entry), None
        mini.append(
            '<span style="display:inline-block;margin:6px 6px 0 0;padding:6px 9px;'
            'background:#F6F0C9;box-shadow:0 4px 8px rgba(30,25,15,.12);font-size:12px;">'
            f"{link(label, url)}</span>"
        )
    return f"""
    <section style="border-top:1px solid #cfd2cf;padding:18px 0 20px 0;">
      <div style="display:inline-block;vertical-align:top;width:105px;margin-right:14px;">
        <div style="display:inline-block;background:#f7f7f3;border:1px solid #d9d8d2;padding:8px 10px;box-shadow:0 3px 7px rgba(0,0,0,.12);font-size:18px;line-height:24px;font-weight:700;color:#174a91;">{esc(board.get("name", "Board"))}</div>
      </div>
      <div style="display:inline-block;vertical-align:top;width:545px;">
        <div style="font-size:12px;line-height:18px;color:#555;margin-bottom:4px;">{esc(board_summary(board.get("summary")))}</div>
        {featured_note(featured)}
        {"".join(supporting)}
        <div>{''.join(mini)}</div>
        <div style="margin-top:8px;font-size:13px;">{link("查看更多 ->", board.get("url"))}</div>
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
<body style="margin:0;background:#e9e2d6;padding:26px 12px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',Arial,sans-serif;color:#222;">
  <main style="max-width:760px;margin:0 auto;background:#fbfbf7;border:10px solid #c8c8c3;border-radius:18px;box-shadow:0 18px 45px rgba(0,0,0,.18);padding:26px 28px 30px 28px;">
    <header style="border-bottom:2px solid #1d3f93;padding-bottom:14px;margin-bottom:16px;">
      <div style="font-size:34px;line-height:42px;font-weight:800;letter-spacing:.2px;">{esc(data.get("title", "Agent Daily Board"))}</div>
      <div style="font-size:16px;line-height:24px;text-align:right;color:#232323;">{esc(data.get("date", ""))}</div>
    </header>
    <div style="background:#fff;border:1px solid #d8d4ca;border-radius:8px;box-shadow:0 5px 12px rgba(0,0,0,.12);padding:12px 14px;margin-bottom:14px;">
      <strong style="font-size:20px;color:#222;border-bottom:2px solid #1d3f93;">今日判断</strong>
      <span style="font-size:13px;line-height:20px;margin-left:14px;">{esc(data.get("overall_judgment", ""))}</span>
      <span style="float:right;font-size:13px;">{esc(metrics)} {link("查看完整白板 ->", full_url) if full_url else ""}</span>
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
