#!/usr/bin/env python3
"""Render an agent knowledge board JSON file into standalone HTML email."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


DEFAULT_ACCENTS = ["#3D5A80", "#2D6A4F", "#B7791F", "#8A5A7A", "#5B6472"]


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def link(label: str, url: str | None) -> str:
    safe_label = esc(label)
    if not url:
        return safe_label
    return f'<a href="{esc(url)}" style="color:#2f5f8f;text-decoration:none;">{safe_label}</a>'


def render_tags(tags: list[Any] | None) -> str:
    if not tags:
        return ""
    chips = []
    for tag in tags[:4]:
        chips.append(
            '<span style="display:inline-block;margin:0 6px 6px 0;padding:3px 8px;'
            'border:1px solid #e4e0d8;border-radius:999px;color:#5f665f;'
            'font-size:12px;line-height:16px;background:#fbfaf7;">'
            f"{esc(tag)}</span>"
        )
    return "".join(chips)


def render_related(related: list[dict[str, Any]] | None) -> str:
    if not related:
        return ""
    rows = []
    for item in related[:3]:
        title = item.get("title") or item.get("path") or "Related note"
        relation = item.get("relation") or "同主题"
        target = item.get("url") or item.get("path")
        target_text = ""
        if target and not str(target).startswith(("http://", "https://")):
            target_text = f' <span style="color:#a09a90;">{esc(target)}</span>'
        linked_target = target if target and str(target).startswith(("http://", "https://")) else None
        rows.append(
            '<div style="margin-top:5px;color:#6f746d;font-size:12px;line-height:18px;">'
            f"关联旧内容：<strong>{esc(relation)}</strong> - {link(title, linked_target)}"
            f"{target_text}"
            "</div>"
        )
    return "".join(rows)


def metric_label(metric: Any) -> str:
    if isinstance(metric, dict):
        return str(metric.get("label") or metric.get("value") or "")
    return str(metric)


def summary_lines(summary: Any) -> list[str]:
    if isinstance(summary, dict):
        return [str(v) for v in (summary.get("count"), summary.get("thread"), summary.get("action")) if v]
    if summary:
        return [str(summary)]
    return []


def render_featured(featured: dict[str, Any], accent: str) -> str:
    if not featured:
        return ""
    source = featured.get("source") or featured.get("url")
    source_html = (
        f'<div style="margin-top:12px;font-size:12px;color:#6c716b;">来源：{link(source, source)}</div>'
        if source
        else ""
    )
    return f"""
    <div style="border:1px solid #ebe7df;border-left:4px solid {esc(accent)};border-radius:10px;padding:18px 18px 16px 18px;background:#fffdf8;margin-top:14px;">
      <div style="font-size:18px;line-height:26px;font-weight:700;color:#282a27;margin-bottom:10px;">{esc(featured.get("title", "主便签"))}</div>
      <div style="font-size:14px;line-height:22px;color:#3a3d38;margin-bottom:7px;"><strong>一句话判断：</strong>{esc(featured.get("judgment", ""))}</div>
      <div style="font-size:14px;line-height:22px;color:#555b54;"><strong>为什么重要：</strong>{esc(featured.get("why", ""))}</div>
      <div style="margin-top:12px;">{render_tags(featured.get("tags"))}</div>
      {source_html}
      {render_related(featured.get("related"))}
    </div>
    """


def render_item(item: dict[str, Any], accent: str) -> str:
    source = item.get("source") or item.get("url")
    return f"""
    <div style="padding:13px 0;border-top:1px solid #eeeae2;">
      <div style="display:block;font-size:14px;line-height:21px;font-weight:700;color:#30332f;">{esc(item.get("title", ""))}</div>
      <div style="margin-top:4px;font-size:13px;line-height:20px;color:#60655f;">{esc(item.get("summary", ""))}</div>
      <div style="margin-top:7px;">{render_tags(item.get("tags"))}</div>
      {f'<div style="font-size:12px;color:#777d75;">来源：{link(source, source)}</div>' if source else ""}
      {render_related(item.get("related"))}
    </div>
    """


def render_more(more: list[Any] | None) -> str:
    if not more:
        return ""
    chips = []
    for entry in more[:12]:
        if isinstance(entry, dict):
            label = entry.get("label") or entry.get("title") or entry.get("url") or ""
            url = entry.get("url")
        else:
            label = str(entry)
            url = None
        chips.append(
            '<span style="display:inline-block;margin:0 6px 7px 0;padding:5px 9px;'
            'border-radius:999px;background:#f4f2ed;border:1px solid #e6e1d8;'
            'font-size:12px;line-height:16px;color:#5f635d;">'
            f"{link(label, url)}</span>"
        )
    return f'<div style="padding-top:10px;border-top:1px solid #eeeae2;">{"".join(chips)}</div>'


def render_board(board: dict[str, Any], index: int) -> str:
    accent = board.get("accent") or DEFAULT_ACCENTS[index % len(DEFAULT_ACCENTS)]
    summaries = summary_lines(board.get("summary"))
    summary_html = "".join(
        f'<div style="font-size:12px;line-height:18px;color:#70756e;">{esc(line)}</div>' for line in summaries
    )
    items_html = "".join(render_item(item, accent) for item in board.get("items", [])[:4])
    return f"""
    <section style="margin-top:22px;padding:20px 20px 18px 20px;border:1px solid #ebe7df;border-radius:14px;background:#ffffff;">
      <div style="border-left:4px solid {esc(accent)};padding-left:12px;">
        <div style="font-size:12px;line-height:16px;letter-spacing:.04em;text-transform:uppercase;color:#8a8f87;">BOARD</div>
        <h2 style="margin:2px 0 8px 0;font-size:21px;line-height:28px;color:#262924;">{esc(board.get("name", "Board"))}</h2>
        {summary_html}
      </div>
      {render_featured(board.get("featured", {}), accent)}
      <div style="margin-top:4px;">{items_html}</div>
      {render_more(board.get("more"))}
    </section>
    """


def render(data: dict[str, Any]) -> str:
    title = data.get("title") or "Agent Daily Board"
    date = data.get("date") or ""
    metrics = data.get("metrics") or []
    metrics_html = "".join(
        '<td style="padding:10px 12px;border:1px solid #e8e3da;border-radius:10px;background:#fbfaf7;'
        'font-size:13px;color:#4f554e;">'
        f"{esc(metric_label(metric))}</td>"
        for metric in metrics[:4]
    )
    full_url = data.get("full_board_url")
    boards_html = "".join(render_board(board, i) for i, board in enumerate(data.get("boards", [])))
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
</head>
<body style="margin:0;padding:0;background:#f3f1ec;color:#2b2e2a;font-family:Georgia,'Times New Roman',serif;">
  <div style="padding:28px 12px;">
    <main style="max-width:720px;margin:0 auto;background:#fffefa;border:1px solid #e6e1d8;border-radius:18px;padding:30px 28px 34px 28px;">
      <header>
        <div style="font-size:13px;line-height:18px;color:#7c8179;">{esc(date)}</div>
        <h1 style="margin:8px 0 18px 0;font-size:34px;line-height:40px;color:#20231f;letter-spacing:0;font-weight:760;">{esc(title)}</h1>
        <div style="border-left:4px solid #3D5A80;padding:14px 16px;background:#f7f8f6;border-radius:10px;">
          <div style="font-size:12px;letter-spacing:.04em;color:#7b8179;">今日判断</div>
          <div style="margin-top:5px;font-size:16px;line-height:25px;color:#30342f;">{esc(data.get("overall_judgment", ""))}</div>
        </div>
        <table role="presentation" cellspacing="0" cellpadding="0" style="width:100%;border-collapse:separate;border-spacing:8px;margin:16px -8px 0 -8px;">
          <tr>{metrics_html}</tr>
        </table>
        {f'<div style="margin-top:12px;font-size:14px;line-height:22px;">{link("查看完整白板", full_url)}</div>' if full_url else ""}
      </header>
      {boards_html}
      <footer style="margin-top:28px;padding-top:16px;border-top:1px solid #eeeae2;color:#777d75;font-size:12px;line-height:19px;">
        Agent Daily Board is a scan layer. Keep full articles and long notes in the knowledge base.
      </footer>
    </main>
  </div>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render agent board JSON to HTML.")
    parser.add_argument("input", help="Path to board JSON file.")
    parser.add_argument("-o", "--output", help="Output HTML path. Defaults to input filename with .html.")
    args = parser.parse_args()

    input_path = Path(args.input)
    data = json.loads(input_path.read_text(encoding="utf-8"))
    output_path = Path(args.output) if args.output else input_path.with_suffix(".html")
    output_path.write_text(render(data), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
