#!/usr/bin/env python3
"""Render a WeChat-friendly PNG by building a static HTML card and screenshotting it."""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


WIDTH = 1080


def text(value: Any) -> str:
    return "" if value is None else str(value)


def esc(value: Any) -> str:
    return html.escape(text(value), quote=True)


def metric_label(metric: Any) -> str:
    if isinstance(metric, dict):
        return text(metric.get("label") or metric.get("value"))
    return text(metric)


def summary_text(summary: Any) -> str:
    if isinstance(summary, dict):
        parts = [summary.get("count"), summary.get("thread"), summary.get("action")]
        return " / ".join(text(part) for part in parts if part)
    return text(summary)


def source_label(item: dict[str, Any]) -> str:
    source = item.get("source")
    if isinstance(source, str):
        return source.replace("https://", "").replace("http://", "").rstrip("/")
    return ""


def related_line(data: dict[str, Any]) -> str:
    for board in data.get("boards") or []:
        featured = board.get("featured") or {}
        related = featured.get("related") or []
        if related:
            first = related[0]
            relation = text(first.get("relation") or "知识卡片")
            return f"关联知识：[{relation}] {text(first.get('title'))}"
    return ""


def item_html(item: dict[str, Any]) -> str:
    title = esc(item.get("title"))
    if not title:
        return ""
    detail = esc(item.get("judgment") or item.get("summary"))
    source = esc(source_label(item))
    detail_html = f'<div class="item-detail">{detail}</div>' if detail else ""
    source_html = f'<div class="item-source">{source}</div>' if source else ""
    return f"""
      <div class="item">
        <div class="diamond"></div>
        <div class="item-copy">
          <div class="item-title">{title}</div>
          {detail_html}
          {source_html}
        </div>
      </div>
    """


def board_html(board: dict[str, Any], index: int) -> str:
    featured = board.get("featured") or {}
    entries: list[dict[str, Any]] = []
    if featured.get("title"):
        entries.append(featured)
    entries.extend((board.get("items") or [])[: max(0, 2 - len(entries))])
    items = "\n".join(item_html(item) for item in entries[:2])
    summary = summary_text(board.get("summary"))
    summary_html = f'<div class="section-summary">{esc(summary)}</div>' if summary else ""
    return f"""
      <section class="section section-{index % 5}">
        <div class="section-title"><span></span>{esc(board.get("name") or "Board")}</div>
        {summary_html}
        {items}
      </section>
    """


def build_html(data: dict[str, Any]) -> str:
    title = esc(data.get("title") or "Agent Knowledge Board")
    date = esc(data.get("date"))
    header = f"{title} · {date}" if date else title
    judgment = esc(data.get("overall_judgment"))
    metrics = "".join(f'<span class="pill">{esc(metric_label(metric))}</span>' for metric in (data.get("metrics") or [])[:4])
    sections = "\n".join(board_html(board, idx) for idx, board in enumerate((data.get("boards") or [])[:5]))
    related = related_line(data)
    related_block = f'<div class="related">{esc(related)}</div>' if related else ""
    full_url = text(data.get("full_board_url"))
    full_url_block = (
        f'<div class="full-url"><span>完整白板</span><strong>{esc(full_url)}</strong></div>' if full_url else ""
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width={WIDTH}, initial-scale=1">
  <style>
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; width: {WIDTH}px; background: #edf3ed; }}
    body {{
      font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", Arial, sans-serif;
      color: #202124;
      letter-spacing: 0;
    }}
    .frame {{ width: {WIDTH}px; padding: 52px; background: #edf3ed; }}
    .card {{
      width: 976px;
      padding: 44px 40px 52px;
      border-radius: 34px;
      background: #fffdf7;
      box-shadow: 8px 10px 0 rgba(44, 71, 54, .10);
    }}
    .title {{
      font-size: 38px;
      line-height: 1.22;
      font-weight: 800;
      margin: 0 0 26px;
    }}
    .judgment {{
      display: grid;
      grid-template-columns: 22px 108px 1fr;
      gap: 14px;
      align-items: start;
      margin-bottom: 28px;
      font-size: 27px;
      line-height: 1.45;
    }}
    .dot {{ width: 20px; height: 20px; border-radius: 99px; margin-top: 9px; background: #2f7d57; }}
    .judgment-label {{ font-weight: 800; white-space: nowrap; }}
    .metrics {{ display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 32px; }}
    .pill {{
      display: inline-flex;
      min-height: 38px;
      align-items: center;
      padding: 4px 18px;
      border-radius: 999px;
      background: #edf4ef;
      font-size: 24px;
    }}
    .section {{
      padding: 34px 0 30px;
      border-top: 2px solid #e5e0d6;
    }}
    .section-title {{
      display: flex;
      align-items: center;
      gap: 13px;
      margin-bottom: 18px;
      font-size: 29px;
      font-weight: 800;
      line-height: 1.25;
    }}
    .section-title span {{ width: 17px; height: 17px; border-radius: 99px; background: #ff8a34; flex: 0 0 auto; }}
    .section-1 .section-title span {{ background: #cc4aa2; }}
    .section-2 .section-title span {{ background: #2d7dbf; }}
    .section-3 .section-title span {{ background: #db6d2f; }}
    .section-4 .section-title span {{ background: #2f7d57; }}
    .section-summary {{
      margin: 0 0 14px 30px;
      color: #667085;
      font-size: 24px;
      line-height: 1.45;
    }}
    .item {{
      display: grid;
      grid-template-columns: 22px 1fr;
      gap: 12px;
      margin: 14px 0 0 4px;
    }}
    .diamond {{
      width: 11px;
      height: 11px;
      margin-top: 13px;
      transform: rotate(45deg);
      background: #2474b5;
    }}
    .item-title {{
      font-size: 27px;
      line-height: 1.35;
      font-weight: 800;
    }}
    .item-detail {{
      margin-top: 4px;
      color: #667085;
      font-size: 23px;
      line-height: 1.45;
    }}
    .item-source {{
      margin-top: 3px;
      color: #1476c9;
      font-size: 23px;
      line-height: 1.35;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: 760px;
    }}
    .related {{
      margin-top: 22px;
      padding: 18px 24px;
      border-left: 4px solid #e0ddd5;
      border-radius: 12px;
      background: #f3f0e8;
      font-size: 24px;
      line-height: 1.4;
    }}
    .full-url {{
      display: flex;
      gap: 18px;
      margin-top: 28px;
      color: #667085;
      font-size: 23px;
      line-height: 1.4;
    }}
    .full-url strong {{
      color: #1476c9;
      font-weight: 500;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
  </style>
</head>
<body>
  <main class="frame">
    <article class="card">
      <h1 class="title">{header}</h1>
      <div class="judgment">
        <div class="dot"></div>
        <div class="judgment-label">今日判断</div>
        <div>{judgment}</div>
      </div>
      <div class="metrics">{metrics}</div>
      {sections}
      {related_block}
      {full_url_block}
    </article>
  </main>
</body>
</html>
"""


def browser_executable() -> str | None:
    candidates = [
        shutil.which("chrome"),
        shutil.which("chrome.exe"),
        shutil.which("msedge"),
        shutil.which("msedge.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def screenshot_html(html_path: Path, output: Path) -> None:
    with sync_playwright() as p:
        executable = browser_executable()
        if executable:
            browser = p.chromium.launch(executable_path=executable)
        else:
            try:
                browser = p.chromium.launch()
            except Exception as exc:
                raise RuntimeError(
                    "No Playwright browser or system Chrome/Edge was found. "
                    "Install a browser or run `playwright install chromium`."
                ) from exc
        page = browser.new_page(viewport={"width": WIDTH, "height": 900}, device_scale_factor=1)
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        height = page.evaluate("document.documentElement.scrollHeight")
        page.set_viewport_size({"width": WIDTH, "height": min(max(int(height), 900), 3200)})
        page.screenshot(path=str(output), full_page=True)
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a WeChat PNG card via static HTML screenshot.")
    parser.add_argument("input", help="Path to board JSON file.")
    parser.add_argument("--output", help="Output PNG path. Defaults to <input>-wechat-card.png.")
    parser.add_argument("--html-output", help="Output HTML path. Defaults to <input>-wechat-card.html.")
    parser.add_argument("--html-only", action="store_true", help="Only write the HTML artifact.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output = Path(args.output) if args.output else input_path.with_name(f"{input_path.stem}-wechat-card.png")
    html_output = (
        Path(args.html_output) if args.html_output else input_path.with_name(f"{input_path.stem}-wechat-card.html")
    )
    data = json.loads(input_path.read_text(encoding="utf-8"))
    html_output.write_text(build_html(data), encoding="utf-8")

    if not args.html_only:
        screenshot_html(html_output, output)
        print(output)
    print(html_output)


if __name__ == "__main__":
    main()
