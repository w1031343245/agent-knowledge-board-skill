#!/usr/bin/env python3
"""Render agent board JSON into the V2 daily-board email HTML."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


CARD_TONES = ["#fffdf8", "#fff8f5", "#f8fbf7"]
STAGE_LABELS = ["事件", "解读", "行动"]


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def text(value: Any) -> str:
    return "" if value is None else str(value)


def metric_text(metric: Any) -> str:
    if isinstance(metric, dict):
        return text(metric.get("label") or metric.get("value"))
    return text(metric)


def source_url(item: dict[str, Any]) -> str:
    source = item.get("source") or item.get("url")
    return source if isinstance(source, str) else ""


def source_domain(item: dict[str, Any]) -> str:
    source = source_url(item)
    if not source:
        return ""
    parsed = urlparse(source if "://" in source else f"https://{source}")
    domain = parsed.netloc or parsed.path.split("/")[0]
    return domain.replace("www.", "")


def summary_parts(summary: Any) -> tuple[str, str, str]:
    if isinstance(summary, dict):
        return (
            text(summary.get("count")),
            text(summary.get("thread")),
            text(summary.get("action")),
        )
    return text(summary), "", ""


def section_line(summary: Any) -> str:
    count, thread, _ = summary_parts(summary)
    parts = []
    if count:
        parts.append(count.replace("今日 ", "").replace("，", " · "))
    if thread:
        parts.append(thread.replace("主线：", ""))
    return " · ".join(parts)


def action_text(board: dict[str, Any]) -> str:
    _, _, action = summary_parts(board.get("summary"))
    if action:
        return action.replace("建议动作：", "下一步：")
    featured = board.get("featured") or {}
    title = text(featured.get("title"))
    if title:
        return f"下一步：跟踪「{title}」后续反馈"
    return "下一步：跟踪本栏关键变化并补充判断"


def tags_html(tags: list[Any] | None) -> str:
    if not tags:
        return ""
    return "".join(f'<span class="tag">{esc(tag)}</span>' for tag in tags[:3])


def split_detail(value: Any) -> tuple[str, str]:
    detail = text(value).strip()
    if not detail:
        return "", ""
    for delimiter in ("：", ":"):
        if delimiter in detail:
            label, body = detail.split(delimiter, 1)
            if len(label) <= 8:
                return f"{label}{delimiter}", body.strip()
    return "一句话判断：", detail


def facts_for(item: dict[str, Any], featured: bool) -> list[str]:
    facts: list[str] = []
    if featured and item.get("why"):
        facts.append(text(item.get("why")).replace("为什么重要：", ""))
    domain = source_domain(item)
    if domain:
        facts.append(f"来源：{domain}")
    return facts[:2]


def related_labels(board: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for entry in board.get("more") or []:
        if isinstance(entry, dict):
            label = entry.get("label") or entry.get("title") or entry.get("url")
        else:
            label = entry
        if label:
            labels.append(text(label))
        if len(labels) >= 3:
            return labels
    featured = board.get("featured") or {}
    for item in featured.get("related") or []:
        label = item.get("title") or item.get("path")
        if label:
            labels.append(text(label))
        if len(labels) >= 3:
            return labels
    return labels


def board_entries(board: dict[str, Any]) -> list[tuple[dict[str, Any], bool]]:
    entries: list[tuple[dict[str, Any], bool]] = []
    featured = board.get("featured") or {}
    if featured.get("title"):
        entries.append((featured, True))
    for item in board.get("items") or []:
        if item.get("title"):
            entries.append((item, False))
        if len(entries) >= 3:
            break
    return entries[:3]


def card_html(item: dict[str, Any], index: int, featured: bool) -> str:
    label, detail = split_detail(item.get("judgment") or item.get("summary"))
    facts = "".join(f"<li>{esc(fact)}</li>" for fact in facts_for(item, featured))
    source = source_url(item)
    domain = source_domain(item)
    source_html = (
        f'<a class="source" href="{esc(source)}">{esc(domain)} ↗</a>' if source and domain else ""
    )
    tone = CARD_TONES[(index - 1) % len(CARD_TONES)]
    return f"""
      <article class="story-card" style="background:{tone};">
        <div class="card-kicker"><span>{index}</span>{STAGE_LABELS[(index - 1) % len(STAGE_LABELS)]}</div>
        <h3>{esc(item.get("title"))}</h3>
        <p class="insight"><strong>{esc(label)}</strong>{esc(detail)}</p>
        <ul>{facts}</ul>
        <div class="card-footer">
          <div>{tags_html(item.get("tags"))}</div>
          {source_html}
        </div>
      </article>
    """


def section_html(board: dict[str, Any], index: int) -> str:
    entries = board_entries(board)
    if not entries:
        return ""
    cards = "\n".join(card_html(item, i, featured) for i, (item, featured) in enumerate(entries, start=1))
    labels = related_labels(board)
    related = (
        '<div class="related-row"><strong>延伸阅读</strong>'
        + "".join(f"<span>{esc(label)}</span>" for label in labels[:3])
        + "</div>"
        if labels
        else ""
    )
    name = text(board.get("name") or "Board")
    chain = " data-layout=\"chain\"" if index == 0 or "商业" in name or "市场" in name else ""
    return f"""
    <section class="board-section"{chain}>
      <header class="section-header">
        <h2>{esc(name)}</h2>
        <p>{esc(section_line(board.get("summary")))}</p>
      </header>
      <div class="story-grid">
        {cards}
      </div>
      <div class="action-bar">{esc(action_text(board))}</div>
      {related}
    </section>
    """


def render(data: dict[str, Any]) -> str:
    title = text(data.get("title") or "Agent Daily Board")
    date = text(data.get("date"))
    judgment = text(data.get("overall_judgment"))
    metrics = [metric_text(metric) for metric in (data.get("metrics") or [])[:4] if metric_text(metric)]
    meta = " · ".join(part for part in [date, "昨日汇总", *metrics] if part)
    sections = "".join(section_html(board, i) for i, board in enumerate(data.get("boards", [])))
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    :root {{
      --ink:#20242a;
      --muted:#66707a;
      --red:#e6463d;
      --blue:#2f6db2;
      --paper:#fffdf8;
      --paper-warm:#f7f0e4;
      --border:#eadfce;
      --line:#e4d9ca;
      --link:#2d72c5;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0;
      padding:24px 10px;
      background:#f4efe6;
      color:var(--ink);
      font-family:Georgia,'Times New Roman',serif;
    }}
    .daily-board {{
      width:720px;
      margin:0 auto;
      padding:20px;
      background:#fbf6ed;
      border:1px solid #e5dac8;
      box-shadow:0 10px 24px rgba(54,42,28,.08);
    }}
    .cover {{
      position:relative;
      display:grid;
      grid-template-columns:292px 1fr 74px;
      gap:16px;
      padding:24px 22px 18px;
      background:#fff8ea;
      border:1px solid #dfd0ba;
      box-shadow:0 6px 14px rgba(53,44,34,.06);
    }}
    .brand-note {{
      position:relative;
    }}
    .brand-note::before, .section-header h2::before, .story-card:first-child::before {{
      content:"";
      position:absolute;
      left:22px;
      top:-16px;
      width:68px;
      height:22px;
      background:#e6c99e;
      opacity:.55;
      transform:rotate(-7deg);
    }}
    .brand-note h1 {{
      margin:0;
      font-size:42px;
      line-height:1.05;
      font-weight:900;
      letter-spacing:0;
    }}
    .brand-note p {{
      display:inline-block;
      margin:15px 0 0;
      color:var(--red);
      font-size:22px;
      font-weight:800;
      border-bottom:4px solid rgba(230,70,61,.75);
    }}
    .daily-thesis {{
      padding-left:14px;
      border-left:5px solid var(--blue);
    }}
    .daily-thesis span {{
      display:block;
      margin-bottom:8px;
      font-size:16px;
      font-weight:800;
    }}
    .daily-thesis p {{
      margin:0;
      font-size:16px;
      line-height:1.62;
    }}
    .judgement-stamp {{
      width:70px;
      height:70px;
      border:3px solid var(--red);
      border-radius:50%;
      color:var(--red);
      display:flex;
      align-items:center;
      justify-content:center;
      text-align:center;
      font-size:21px;
      line-height:1.1;
      font-weight:900;
      transform:rotate(5deg);
    }}
    .daily-meta {{
      grid-column:1 / -1;
      margin-top:8px;
      padding-top:14px;
      border-top:1px dashed #d9cbb6;
      color:#41464b;
      text-align:center;
      font-size:14px;
      line-height:1.4;
    }}
    .board-section {{
      margin-top:26px;
      padding-top:20px;
      border-top:1px dashed var(--line);
      break-inside:avoid;
      page-break-inside:avoid;
    }}
    .section-header {{
      display:flex;
      align-items:center;
      gap:20px;
      margin-bottom:16px;
    }}
    .section-header h2 {{
      position:relative;
      min-width:130px;
      margin:0;
      padding:10px 16px;
      background:#fff8ea;
      border:1px solid var(--border);
      box-shadow:0 5px 10px rgba(53,44,34,.06);
      font-size:25px;
      line-height:1.1;
      font-weight:900;
    }}
    .section-header h2::after {{
      content:"";
      display:block;
      width:74px;
      height:4px;
      margin-top:5px;
      background:var(--red);
    }}
    .section-header p {{
      margin:0;
      padding-left:14px;
      border-left:4px solid var(--blue);
      color:#3c4147;
      font-size:15px;
      line-height:1.5;
    }}
    .story-grid {{
      display:grid;
      grid-template-columns:repeat(2,minmax(0,1fr));
      gap:14px;
      align-items:stretch;
    }}
    .story-card {{
      position:relative;
      min-height:256px;
      max-height:292px;
      padding:19px 18px 16px;
      border:1px solid var(--border);
      border-radius:7px;
      box-shadow:0 6px 14px rgba(53,44,34,.065);
      overflow:hidden;
      display:flex;
      flex-direction:column;
    }}
    .story-card:first-child {{
      grid-column:1 / -1;
      min-height:176px;
      max-height:226px;
    }}
    .card-kicker {{
      display:flex;
      align-items:center;
      gap:8px;
      margin-bottom:12px;
      color:var(--muted);
      font-size:14px;
      font-weight:800;
    }}
    .card-kicker span {{
      width:28px;
      height:28px;
      border-radius:50%;
      background:var(--red);
      color:#fff;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      font-size:16px;
      line-height:1;
    }}
    .story-card h3 {{
      margin:0 0 10px;
      color:var(--ink);
      font-size:21px;
      line-height:1.3;
      max-height:56px;
      overflow:hidden;
    }}
    .story-card:first-child h3 {{
      font-size:22px;
    }}
    .insight {{
      margin:0 0 12px;
      color:var(--muted);
      font-size:15px;
      line-height:1.55;
      max-height:47px;
      overflow:hidden;
    }}
    .insight strong {{
      color:var(--red);
    }}
    .story-card ul {{
      margin:0 0 12px 18px;
      padding:0;
      color:#3c4147;
      font-size:14px;
      line-height:1.45;
      max-height:42px;
      overflow:hidden;
    }}
    .card-footer {{
      margin-top:auto;
      display:flex;
      align-items:flex-end;
      justify-content:space-between;
      gap:10px;
    }}
    .tag {{
      display:inline-block;
      margin:0 5px 5px 0;
      padding:3px 8px;
      border:1px solid #d8cfc1;
      border-radius:999px;
      background:rgba(255,255,255,.65);
      color:#4f565d;
      font-size:12px;
      line-height:1.2;
    }}
    .source {{
      color:var(--link);
      font-size:13px;
      line-height:1.3;
      text-decoration:none;
      white-space:nowrap;
    }}
    .action-bar {{
      margin-top:16px;
      padding:12px 16px;
      border-left:4px solid var(--red);
      background:#fff8ef;
      color:var(--ink);
      font-size:15px;
      line-height:1.5;
    }}
    .related-row {{
      margin-top:10px;
      padding:11px 16px;
      background:#eef5fc;
      color:#315a8a;
      font-size:14px;
      line-height:1.45;
    }}
    .related-row strong {{
      margin-right:12px;
      color:var(--link);
    }}
    .related-row span::before {{
      content:"·";
      margin:0 10px;
    }}
  </style>
</head>
<body>
  <main class="daily-board">
    <header class="cover">
      <section class="brand-note">
        <h1>{esc(title)}</h1>
        <p>先抓重点，再做闭环</p>
      </section>
      <section class="daily-thesis">
        <span>今日主线：</span>
        <p>{esc(judgment)}</p>
      </section>
      <aside class="judgement-stamp">今日<br>判断</aside>
      <footer class="daily-meta">{esc(meta)}</footer>
    </header>
    {sections}
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render agent board JSON as V2 daily-board email HTML.")
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
