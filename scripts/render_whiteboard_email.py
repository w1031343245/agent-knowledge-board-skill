#!/usr/bin/env python3
"""Render agent board JSON into a whiteboard paper-note HTML preview."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


PAPER_COLORS = ["#FFFCF4", "#FBF7EC", "#F7FBFF", "#FFF8F5", "#F8FBF2"]


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
        '<div style="font-size:12px;line-height:18px;color:#62665f;margin-top:9px;">'
        '<strong style="color:#343831;">关联旧内容：</strong>'
        + "<br>".join(rows)
        + "</div>"
    )


def tape(color: str = "#eadfc8") -> str:
    return (
        f'<div style="position:absolute;left:50%;top:-12px;width:58px;height:18px;'
        f'margin-left:-29px;background:{color};opacity:.82;'
        'box-shadow:0 2px 5px rgba(60,45,20,.12);"></div>'
    )


def paper_note(
    title: str,
    body: str,
    number: int | None = None,
    width: int = 170,
    accent: str = "#C9362E",
    paper: str = "#FFFCF4",
) -> str:
    number_html = (
        f'<span style="display:inline-block;width:26px;height:26px;margin-right:6px;border:2px solid {accent};'
        f'border-radius:50%;text-align:center;line-height:24px;color:{accent};font-size:18px;font-weight:800;">'
        f"{number}</span>"
        if number is not None
        else ""
    )
    return f"""
    <div style="display:inline-block;vertical-align:top;width:{width}px;min-height:164px;margin:18px 10px 0 0;padding:18px 18px 16px 18px;background:{paper};border:1px solid #e5ddcf;box-shadow:0 10px 22px rgba(44,33,18,.16);font-size:13px;line-height:20px;color:#2b2924;position:relative;">
      {tape()}
      <div style="font-size:20px;line-height:28px;font-weight:800;color:#171b1f;margin-bottom:8px;">
        {number_html}<span style="border-bottom:3px solid {accent};">{esc(title)}</span>
      </div>
      <div>{body}</div>
    </div>
    """


def blue_strip(text: str, width: int | None = None) -> str:
    width_style = f"width:{width}px;" if width else ""
    return (
        '<div style="display:inline-block;vertical-align:top;'
        + width_style
        + 'padding:9px 12px;background:#fffef9;border:2px solid #2f63a3;'
        'box-shadow:0 4px 9px rgba(20,40,80,.08);font-size:13px;line-height:20px;color:#26313d;">'
        f"{esc(text)}</div>"
    )


def featured_note(featured: dict[str, Any], number: int, accent: str) -> str:
    if not featured:
        return ""
    source = featured.get("source") or featured.get("url")
    body = (
        f'<div style="color:#C9362E;font-weight:700;line-height:21px;margin-bottom:8px;">{esc(featured.get("judgment", ""))}</div>'
        f'<ul style="margin:8px 0 0 18px;padding:0;font-size:13px;line-height:22px;color:#2d2f2b;">'
    )
    if featured.get("why"):
        body += f"<li>{esc(featured.get('why'))}</li>"
    if source:
        body += f"<li>来源：{link(source, source)}</li>"
    body += "</ul>"
    if featured.get("tags"):
        body += f'<div style="margin-top:10px;">{tags_html(featured.get("tags"))}</div>'
    body += related_html(featured.get("related"))
    return paper_note(featured.get("title", "一句话判断"), body, number=number, width=248, accent=accent)


def board_summary(summary: Any) -> str:
    if isinstance(summary, dict):
        parts = [summary.get("count"), summary.get("thread"), summary.get("action")]
        return " / ".join(str(p) for p in parts if p)
    return str(summary or "")


def render_board(board: dict[str, Any], index: int) -> str:
    accent = "#C9362E"
    blue = board.get("accent") or "#2F63A3"
    featured = board.get("featured") or {}
    items = board.get("items") or []
    more = board.get("more") or []
    cards = [featured_note(featured, 1, accent)]
    for item_index, item in enumerate(items[:2], start=2):
        body = (
            f'<div style="color:#C9362E;font-weight:700;margin-bottom:8px;">{esc(item.get("summary", ""))}</div>'
            f'<div style="margin-top:8px;">{tags_html(item.get("tags"))}</div>'
        )
        source = item.get("source") or item.get("url")
        if source:
            body += f'<div style="font-size:12px;line-height:18px;margin-top:8px;">来源：{link(source, source)}</div>'
        cards.append(
            paper_note(
                item.get("title", "摘要"),
                body,
                number=item_index,
                width=198,
                accent=accent,
                paper=PAPER_COLORS[(index + item_index) % len(PAPER_COLORS)],
            )
        )
    arrows = '<span style="display:inline-block;vertical-align:top;margin:74px 12px 0 2px;color:#F07B22;font-size:40px;line-height:40px;font-weight:800;">→</span>'
    mini = []
    for entry in more[:8]:
        if isinstance(entry, dict):
            label = entry.get("label") or entry.get("title") or entry.get("url") or ""
            url = entry.get("url")
        else:
            label, url = str(entry), None
        mini.append(
            '<span style="display:inline-block;margin:6px 6px 0 0;padding:4px 8px;'
            'background:#fffdf5;border:1px solid #d8e2ee;border-radius:0;'
            'font-size:12px;line-height:16px;color:#244c83;">'
            f"{link(label, url)}</span>"
        )
    mini_html = (
        '<div style="display:inline-block;vertical-align:top;width:200px;margin:18px 0 0 0;padding:12px 12px;background:#F1F7FF;border:1px solid #bfd0e3;box-shadow:0 7px 14px rgba(32,48,68,.12);position:relative;">'
        + tape("#7fb0e5")
        + '<div style="font-size:14px;line-height:20px;font-weight:800;color:#244c83;border-bottom:2px solid #244c83;margin-bottom:6px;">补充索引</div>'
        + "".join(mini)
        + "</div>"
        if mini
        else ""
    )
    card_flow = arrows.join(card for card in cards if card)
    return f"""
    <section style="padding:24px 0 26px 0;border-top:1px dashed #d8d1c3;">
      <div style="margin-bottom:12px;">
        <div style="display:inline-block;vertical-align:top;min-width:122px;padding:11px 16px 12px 16px;background:#fffdf5;border:1px solid #e0d6c4;box-shadow:0 7px 14px rgba(44,33,18,.12);transform:rotate(-1deg);font-size:22px;line-height:30px;font-weight:850;color:#171b1f;">
          <span style="border-bottom:3px solid {esc(accent)};">{esc(board.get("name", "Board"))}</span>
        </div>
        <div style="display:inline-block;vertical-align:top;margin-left:16px;">{blue_strip(board_summary(board.get("summary")), 500)}</div>
      </div>
      <div style="white-space:normal;">
        {card_flow}
        {mini_html}
      </div>
      <div style="text-align:center;color:#F07B22;font-size:15px;line-height:22px;font-weight:800;margin-top:14px;">
        <span style="border-bottom:3px solid #F07B22;">持续跟踪，闭环优化</span>
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
    title = data.get("title", "Agent Daily Board")
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)}</title></head>
<body style="margin:0;background:#f7f5ef;padding:24px 12px;font-family:'Segoe Print','Bradley Hand','Comic Sans MS','Microsoft YaHei',Arial,sans-serif;color:#222;">
  <main style="max-width:980px;margin:0 auto;background:#fffefb;border:1px solid #e5e0d4;box-shadow:0 16px 42px rgba(0,0,0,.10);padding:28px 34px 34px 34px;">
    <header style="padding-bottom:18px;margin-bottom:8px;">
      <div style="display:inline-block;vertical-align:top;padding:15px 22px 16px 22px;background:#fffaf0;border:1px solid #e2d7c4;box-shadow:0 9px 18px rgba(44,33,18,.14);transform:rotate(-2deg);position:relative;">
        {tape("#ead6b5")}
        <div style="font-size:36px;line-height:44px;font-weight:900;letter-spacing:0;color:#12161a;">{esc(title)}</div>
        <div style="font-size:18px;line-height:24px;color:#C9362E;font-weight:800;border-bottom:3px solid #C9362E;">先抓重点，再做闭环</div>
      </div>
      <div style="display:inline-block;vertical-align:top;margin:6px 0 0 26px;">{blue_strip(data.get("overall_judgment", ""), 420)}</div>
      <div style="display:inline-block;vertical-align:top;margin:6px 0 0 18px;text-align:center;">
        <div style="display:inline-block;width:72px;height:72px;border:3px solid #C9362E;border-radius:50%;color:#C9362E;font-size:20px;line-height:27px;font-weight:900;padding-top:10px;">今日<br>判断</div>
      </div>
      <div style="font-size:14px;line-height:22px;text-align:right;color:#4f544e;margin-top:8px;">{esc(data.get("date", ""))}</div>
    </header>
    <div style="margin:0 0 10px 0;text-align:right;font-size:13px;line-height:20px;color:#6c7169;">
      {esc(metrics)} {link("查看完整白板", full_url) if full_url else ""}
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
