#!/usr/bin/env python3
"""Render agent board JSON into the V2 daily-board email HTML."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


BOARD_PAGE_SIZE = 2
CARD_TONES = ["#fffdf8", "#fff8f5", "#f8fbf7"]
CARD_LABELS = ["事件", "判断", "影响"]
CHAIN_BOARD_HINTS = ("今日必看", "商业", "市场", "行业")


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def text(value: Any) -> str:
    return "" if value is None else str(value)


def compact(value: Any, limit: int) -> str:
    raw = re.sub(r"\s+", " ", text(value)).strip()
    if len(raw) <= limit:
        return raw
    return raw[: max(1, limit - 1)].rstrip("，。；、,. ") + "…"


def clean_label(value: Any) -> str:
    raw = text(value).strip()
    return re.sub(r"^(今日\s*)?", "", raw).replace("，", " · ")


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
    summary_text = text(summary)
    count = ""
    thread = summary_text
    if "；" in summary_text:
        head, tail = summary_text.split("；", 1)
        count, thread = head, tail
    return count, thread, ""


def section_thesis(summary: Any) -> str:
    _, thread, _ = summary_parts(summary)
    thesis = thread.replace("主线：", "").replace("建议动作：", "")
    return compact(thesis, 46)


def section_count(summary: Any) -> str:
    count, _, _ = summary_parts(summary)
    return compact(clean_label(count), 18)


def action_text(board: dict[str, Any]) -> str:
    _, _, action = summary_parts(board.get("summary"))
    if action:
        action = action.replace("建议动作：", "")
        return f"下一步：{compact(action, 52)}"
    featured = board.get("featured") or {}
    title = compact(featured.get("title"), 24)
    if title:
        return f"下一步：跟踪「{title}」后续反馈。"
    return "下一步：跟踪本栏关键变化，并补充可执行判断。"


def tags_html(tags: list[Any] | None) -> str:
    if not tags:
        return ""
    return "".join(f'<span class="tag">{esc(compact(tag, 8))}</span>' for tag in tags[:3])


def split_detail(value: Any) -> tuple[str, str]:
    detail = text(value).strip()
    if not detail:
        return "一句话判断：", ""
    for delimiter in ("：", ":"):
        if delimiter in detail:
            label, body = detail.split(delimiter, 1)
            if len(label) <= 8:
                return f"{label}{delimiter}", compact(body, 52)
    return "一句话判断：", compact(detail, 52)


def fact_candidates(item: dict[str, Any], featured: bool) -> list[str]:
    candidates: list[str] = []
    for key in ("facts", "bullets", "points", "takeaways"):
        values = item.get(key)
        if isinstance(values, list):
            candidates.extend(text(value) for value in values if value)
    if featured and item.get("why"):
        candidates.append(text(item.get("why")).replace("为什么重要：", ""))
    if item.get("impact"):
        candidates.append(text(item.get("impact")).replace("影响：", ""))
    return [compact(candidate, 30) for candidate in candidates if text(candidate).strip()][:2]


def related_labels(board: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for entry in board.get("more") or []:
        if isinstance(entry, dict):
            label = entry.get("label") or entry.get("title") or entry.get("url")
        else:
            label = entry
        if label:
            labels.append(compact(label, 18))
        if len(labels) >= 3:
            return labels
    featured = board.get("featured") or {}
    for item in featured.get("related") or []:
        label = item.get("title") or item.get("path")
        if label:
            labels.append(compact(label, 18))
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


def layout_mode(board: dict[str, Any], index: int, entries: list[tuple[dict[str, Any], bool]]) -> str:
    if len(entries) <= 1:
        return "single"
    if len(entries) == 2:
        return "main-side"
    name = text(board.get("name"))
    if index == 0 or any(hint in name for hint in CHAIN_BOARD_HINTS):
        return "chain"
    return "parallel"


def card_html(item: dict[str, Any], index: int, featured: bool, mode: str) -> str:
    label, detail = split_detail(item.get("judgment") or item.get("summary"))
    facts = "".join(f"<li>{esc(fact)}</li>" for fact in fact_candidates(item, featured))
    source = source_url(item)
    domain = source_domain(item)
    source_html = (
        f'<a class="source" href="{esc(source)}">{esc(domain)} ↗</a>' if source and domain else ""
    )
    tone = CARD_TONES[(index - 1) % len(CARD_TONES)]
    role = CARD_LABELS[(index - 1) % len(CARD_LABELS)]
    return f"""
      <article class="story-card story-card-{index}" style="background:{tone};">
        <div class="card-kicker"><span>{index}</span>{role}</div>
        <h3>{esc(compact(item.get("title"), 34 if mode != "parallel" else 28))}</h3>
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
    mode = layout_mode(board, index, entries)
    cards = "\n".join(card_html(item, i, featured, mode) for i, (item, featured) in enumerate(entries, start=1))
    labels = related_labels(board)
    related = (
        '<div class="related-row"><strong>延伸阅读</strong>'
        + "".join(f"<span>{esc(label)}</span>" for label in labels[:3])
        + "</div>"
        if labels
        else ""
    )
    count = section_count(board.get("summary"))
    count_html = f'<span class="section-count">{esc(count)}</span>' if count else ""
    name = text(board.get("name") or "Board")
    return f"""
    <section class="board-section" data-layout="{mode}">
      <header class="section-header">
        <h2>{esc(name)}</h2>
        <p>{count_html}<span>{esc(section_thesis(board.get("summary")))}</span></p>
      </header>
      <div class="story-grid">
        {cards}
      </div>
      <div class="action-bar">{esc(action_text(board))}</div>
      {related}
    </section>
    """


def page_chunks(boards: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    return [boards[i : i + BOARD_PAGE_SIZE] for i in range(0, len(boards), BOARD_PAGE_SIZE)]


def cover_html(data: dict[str, Any]) -> str:
    title = text(data.get("title") or "Agent Daily Board")
    date = text(data.get("date"))
    judgment = compact(data.get("overall_judgment"), 74)
    metrics = [metric_text(metric) for metric in (data.get("metrics") or [])[:3] if metric_text(metric)]
    meta = " · ".join(part for part in [date, "昨日汇总", *metrics] if part)
    return f"""
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
    """


def mini_cover_html(data: dict[str, Any], page_no: int) -> str:
    title = text(data.get("title") or "Agent Daily Board")
    date = text(data.get("date"))
    return f"""
    <header class="mini-cover">
      <strong>{esc(title)}</strong>
      <span>{esc(date)} · 第 {page_no} 张</span>
    </header>
    """


def board_page_html(data: dict[str, Any], boards: list[dict[str, Any]], page_no: int) -> str:
    sections = "".join(section_html(board, i) for i, board in enumerate(boards))
    heading = cover_html(data) if page_no == 1 else mini_cover_html(data, page_no)
    return f"""
  <main class="daily-board" data-page="{page_no}">
    {heading}
    {sections}
  </main>
    """


def styles() -> str:
    return """
    :root {
      --ink:#20242a;
      --muted:#66707a;
      --red:#e6463d;
      --blue:#2f6db2;
      --paper:#fffdf8;
      --paper-warm:#f7f0e4;
      --border:#eadfce;
      --line:#e4d9ca;
      --link:#2d72c5;
    }
    * { box-sizing:border-box; }
    body {
      margin:0;
      padding:24px 10px;
      background:#f4efe6;
      color:var(--ink);
      font-family:Georgia,'Times New Roman',serif;
    }
    .daily-board {
      width:720px;
      margin:0 auto 22px;
      padding:20px;
      background:#fbf6ed;
      border:1px solid #e5dac8;
      box-shadow:0 10px 24px rgba(54,42,28,.08);
      break-after:page;
    }
    .cover {
      position:relative;
      display:grid;
      grid-template-columns:292px 1fr 64px;
      gap:16px;
      padding:24px 22px 18px;
      background:#fff8ea;
      border:1px solid #dfd0ba;
      box-shadow:0 6px 14px rgba(53,44,34,.06);
    }
    .mini-cover {
      display:flex;
      justify-content:space-between;
      align-items:center;
      gap:16px;
      padding:14px 18px;
      background:#fff8ea;
      border:1px solid #dfd0ba;
      color:#3c4147;
      font-size:14px;
    }
    .mini-cover strong {
      font-size:24px;
      color:var(--ink);
    }
    .brand-note {
      position:relative;
    }
    .brand-note::before, .section-header h2::before, .board-section[data-layout="chain"] .story-card-1::before {
      content:"";
      position:absolute;
      left:22px;
      top:-16px;
      width:68px;
      height:22px;
      background:#e6c99e;
      opacity:.50;
      transform:rotate(-7deg);
    }
    .brand-note h1 {
      margin:0;
      font-size:42px;
      line-height:1.05;
      font-weight:900;
      letter-spacing:0;
    }
    .brand-note p {
      display:inline-block;
      margin:15px 0 0;
      color:var(--red);
      font-size:22px;
      font-weight:800;
      border-bottom:4px solid rgba(230,70,61,.75);
    }
    .daily-thesis {
      padding-left:14px;
      border-left:5px solid var(--blue);
    }
    .daily-thesis span {
      display:block;
      margin-bottom:8px;
      font-size:16px;
      font-weight:800;
    }
    .daily-thesis p {
      margin:0;
      font-size:16px;
      line-height:1.62;
    }
    .judgement-stamp {
      width:58px;
      height:58px;
      border:3px solid var(--red);
      border-radius:50%;
      color:var(--red);
      display:flex;
      align-items:center;
      justify-content:center;
      text-align:center;
      font-size:17px;
      line-height:1.08;
      font-weight:900;
      transform:rotate(5deg);
    }
    .daily-meta {
      grid-column:1 / -1;
      margin-top:8px;
      padding-top:14px;
      border-top:1px dashed #d9cbb6;
      color:#41464b;
      text-align:center;
      font-size:14px;
      line-height:1.4;
    }
    .board-section {
      margin-top:24px;
      padding-top:18px;
      border-top:1px dashed var(--line);
      break-inside:avoid;
      page-break-inside:avoid;
    }
    .section-header {
      display:flex;
      align-items:center;
      gap:18px;
      margin-bottom:14px;
    }
    .section-header h2 {
      position:relative;
      min-width:126px;
      margin:0;
      padding:10px 16px;
      background:#fff8ea;
      border:1px solid var(--border);
      box-shadow:0 5px 10px rgba(53,44,34,.055);
      font-size:25px;
      line-height:1.1;
      font-weight:900;
      white-space:nowrap;
    }
    .section-header h2::after {
      content:"";
      display:block;
      width:74px;
      height:4px;
      margin-top:5px;
      background:var(--red);
    }
    .section-header p {
      flex:1;
      margin:0;
      padding-left:13px;
      border-left:4px solid var(--blue);
      color:#3c4147;
      font-size:15px;
      line-height:1.5;
    }
    .section-count {
      display:inline-block;
      margin-right:8px;
      color:#7d858d;
      font-size:13px;
    }
    .story-grid {
      display:grid;
      gap:14px;
      align-items:start;
    }
    .board-section[data-layout="chain"] .story-grid,
    .board-section[data-layout="parallel"] .story-grid {
      grid-template-columns:repeat(3,minmax(0,1fr));
    }
    .board-section[data-layout="main-side"] .story-grid {
      grid-template-columns:1.45fr 1fr;
    }
    .board-section[data-layout="single"] .story-grid {
      grid-template-columns:1fr;
    }
    .story-card {
      position:relative;
      padding:18px 18px 16px;
      border:1px solid var(--border);
      border-radius:7px;
      box-shadow:0 6px 14px rgba(53,44,34,.06);
      display:flex;
      flex-direction:column;
    }
    .board-section[data-layout="chain"] .story-card:not(:last-child)::after {
      content:"→";
      position:absolute;
      right:-24px;
      top:45%;
      color:#f07b25;
      font-size:24px;
      font-weight:700;
    }
    .card-kicker {
      display:flex;
      align-items:center;
      gap:8px;
      margin-bottom:10px;
      color:var(--muted);
      font-size:13px;
      font-weight:800;
    }
    .card-kicker span {
      width:26px;
      height:26px;
      border-radius:50%;
      background:var(--red);
      color:#fff;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      font-size:15px;
      line-height:1;
    }
    .story-card h3 {
      margin:0 0 9px;
      color:var(--ink);
      font-size:20px;
      line-height:1.25;
      overflow-wrap:anywhere;
    }
    .board-section[data-layout="chain"] .story-card h3,
    .board-section[data-layout="parallel"] .story-card h3 {
      font-size:18px;
    }
    .insight {
      margin:0 0 10px;
      color:var(--muted);
      font-size:14px;
      line-height:1.5;
    }
    .insight strong {
      color:var(--red);
    }
    .story-card ul {
      margin:0 0 11px 17px;
      padding:0;
      color:#3c4147;
      font-size:13px;
      line-height:1.45;
    }
    .card-footer {
      margin-top:auto;
      display:flex;
      align-items:flex-end;
      justify-content:space-between;
      gap:10px;
    }
    .tag {
      display:inline-block;
      margin:0 5px 5px 0;
      padding:3px 8px;
      border:1px solid #d8cfc1;
      border-radius:999px;
      background:rgba(255,255,255,.70);
      color:#4f565d;
      font-size:12px;
      line-height:1.2;
      white-space:nowrap;
    }
    .source {
      color:var(--link);
      font-size:13px;
      line-height:1.3;
      text-decoration:none;
      white-space:nowrap;
    }
    .action-bar {
      margin-top:14px;
      padding:12px 16px;
      border-left:4px solid var(--red);
      background:#fff8ef;
      color:var(--ink);
      font-size:15px;
      line-height:1.5;
    }
    .related-row {
      margin-top:10px;
      padding:10px 16px;
      background:#eef5fc;
      color:#315a8a;
      font-size:14px;
      line-height:1.45;
    }
    .related-row strong {
      margin-right:12px;
      color:var(--link);
    }
    .related-row span::before {
      content:"·";
      margin:0 10px;
    }
  """


def render(data: dict[str, Any], page_boards: list[dict[str, Any]] | None = None, page_no: int | None = None) -> str:
    boards = page_boards if page_boards is not None else data.get("boards", [])
    if page_no is not None:
        pages = board_page_html(data, boards, page_no)
    else:
        pages = "\n".join(
            board_page_html(data, chunk, i)
            for i, chunk in enumerate(page_chunks(list(boards)), start=1)
        )
    title = text(data.get("title") or "Agent Daily Board")
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=720, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
{styles()}
  </style>
</head>
<body>
{pages}
</body>
</html>
"""


def write_split_pages(data: dict[str, Any], output_dir: Path, source_path: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for page_no, boards in enumerate(page_chunks(data.get("boards", [])), start=1):
        output = output_dir / f"{source_path.stem}-whiteboard-page-{page_no}.html"
        output.write_text(render(data, boards, page_no), encoding="utf-8")
        print(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render agent board JSON as V2 daily-board email HTML.")
    parser.add_argument("input", help="Path to board JSON file.")
    parser.add_argument("--output", help="Output HTML path. Defaults to input filename with -whiteboard.html.")
    parser.add_argument("--split-pages-dir", help="Optional directory for screenshot-ready per-page HTML files.")
    args = parser.parse_args()
    input_path = Path(args.input)
    data = json.loads(input_path.read_text(encoding="utf-8"))
    output_path = Path(args.output) if args.output else input_path.with_name(input_path.stem + "-whiteboard.html")
    output_path.write_text(render(data), encoding="utf-8")
    print(output_path)
    if args.split_pages_dir:
        write_split_pages(data, Path(args.split_pages_dir), input_path)


if __name__ == "__main__":
    main()
