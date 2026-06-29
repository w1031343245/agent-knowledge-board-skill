#!/usr/bin/env python3
"""Render a WeChat-friendly PNG by building a static HTML card and screenshotting it."""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

WIDTH = 1080
PAPER_COLORS = ["#fffaf0", "#f7fbff", "#fff4ef", "#f3fbf4", "#f7f1ff"]
ANGLES = [-1.1, 0.7, -0.5, 1.0, -0.8]
TOPS = [0, 16, 6, 20, 10]
PAPER_SHAPES = [
    "polygon(1% 0, 99% 1%, 100% 97%, 3% 100%, 0 42%)",
    "polygon(0 2%, 98% 0, 100% 100%, 2% 97%)",
    "polygon(2% 1%, 100% 0, 98% 98%, 0 100%)",
    "polygon(0 0, 99% 2%, 100% 96%, 1% 100%)",
]


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


def tags_html(tags: list[Any] | None) -> str:
    if not tags:
        return ""
    return "".join(f'<span class="tag">{esc(tag)}</span>' for tag in tags[:3])


def more_html(more: list[Any] | None) -> str:
    if not more:
        return ""
    chips = []
    for entry in more[:6]:
        if isinstance(entry, dict):
            label = entry.get("label") or entry.get("title") or entry.get("url") or ""
        else:
            label = str(entry)
        if label:
            chips.append(f'<span class="index-chip">{esc(label)}</span>')
    if not chips:
        return ""
    return '<div class="index-note"><div class="tape tape-blue"></div><div class="index-title">补充索引</div>' + "".join(chips) + "</div>"


def related_line(data: dict[str, Any]) -> str:
    for board in data.get("boards") or []:
        featured = board.get("featured") or {}
        related = featured.get("related") or []
        if related:
            first = related[0]
            relation = text(first.get("relation") or "知识卡片")
            return f"关联知识：[{relation}] {text(first.get('title'))}"
    return ""


def item_html(item: dict[str, Any], number: int, seed: int) -> str:
    title = esc(item.get("title"))
    if not title:
        return ""
    detail = esc(item.get("judgment") or item.get("summary"))
    source = esc(source_label(item))
    detail_html = f'<div class="item-detail">{detail}</div>' if detail else ""
    source_html = f'<div class="item-source">{source}</div>' if source else ""
    tags = tags_html(item.get("tags"))
    angle = ANGLES[seed % len(ANGLES)]
    top = TOPS[seed % len(TOPS)]
    color = PAPER_COLORS[seed % len(PAPER_COLORS)]
    shape = PAPER_SHAPES[seed % len(PAPER_SHAPES)]
    return f"""
      <div class="paper-wrap" style="margin-top:{top}px; transform:rotate({angle}deg);">
        <div class="tape" style="transform:rotate({-angle / 2}deg);"></div>
        <div class="paper" style="background:{color}; clip-path:{shape};">
          <div class="item-title"><span class="num">{number}</span><span>{title}</span></div>
          {detail_html}
          {tags}
          {source_html}
        </div>
      </div>
    """


def board_html(board: dict[str, Any], index: int) -> str:
    featured = board.get("featured") or {}
    entries: list[dict[str, Any]] = []
    if featured.get("title"):
        entries.append(featured)
    entries.extend((board.get("items") or [])[: max(0, 3 - len(entries))])
    paper_items = []
    for item_index, item in enumerate(entries[:3], start=1):
        paper_items.append(item_html(item, item_index, index * 3 + item_index))
    items = "\n".join(paper_items)
    summary = summary_text(board.get("summary"))
    summary_html = f'<div class="blue-strip">{esc(summary)}</div>' if summary else ""
    more = more_html(board.get("more"))
    return f"""
      <section class="section section-{index % 5}">
        <div class="section-head">
          <div class="section-title"><span>{esc(board.get("name") or "Board")}</span></div>
          {summary_html}
        </div>
        <div class="papers">
          {items}
          {more}
        </div>
      </section>
    """


def build_html(data: dict[str, Any]) -> str:
    title = esc(data.get("title") or "Agent Knowledge Board")
    date = esc(data.get("date"))
    header = title
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
    html, body {{ margin: 0; padding: 0; width: {WIDTH}px; background: #f5f2ea; }}
    body {{
      font-family: "Segoe Print", "Bradley Hand", "Comic Sans MS", "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
      color: #191d20;
      letter-spacing: 0;
    }}
    .frame {{
      width: {WIDTH}px;
      padding: 32px 50px 46px;
      background:
        linear-gradient(rgba(58, 84, 112, .035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(58, 84, 112, .035) 1px, transparent 1px),
        #fffefb;
      background-size: 54px 54px;
    }}
    .card {{
      width: 980px;
      padding: 18px 0 22px;
      background: transparent;
    }}
    .header {{
      position: relative;
      min-height: 194px;
      margin-bottom: 8px;
    }}
    .title-paper {{
      display: inline-block;
      position: relative;
      width: 420px;
      margin: 24px 0 0 0;
      padding: 22px 26px 24px;
      background: #fffaf0;
      border: 1px solid #e5dac8;
      border-radius: 2px 1px 3px 1px;
      box-shadow: 0 15px 28px rgba(48, 36, 18, .13);
      transform: rotate(-1.7deg);
    }}
    .tape {{
      position: absolute;
      left: 50%;
      top: -14px;
      width: 76px;
      height: 22px;
      margin-left: -38px;
      background: #eadbbf;
      opacity: .84;
      box-shadow: 0 3px 8px rgba(60, 45, 20, .12);
    }}
    .tape-blue {{ background: #8dbceb; }}
    .title {{
      margin: 0;
      font-size: 42px;
      line-height: 1.16;
      font-weight: 900;
    }}
    .subtitle {{
      display: inline-block;
      margin-top: 8px;
      color: #c9342e;
      font-size: 23px;
      line-height: 1.25;
      font-weight: 900;
      border-bottom: 4px solid #c9342e;
    }}
    .judgment {{
      position: absolute;
      left: 446px;
      top: 34px;
      width: 388px;
      padding: 14px 16px;
      border: 3px solid #245ca0;
      border-radius: 2px 1px 3px 1px;
      background: #fffef9;
      color: #202733;
      font-size: 22px;
      line-height: 1.45;
      transform: rotate(.5deg);
    }}
    .judgment-stamp {{
      position: absolute;
      right: 14px;
      top: 26px;
      width: 96px;
      height: 96px;
      border: 4px solid #c9342e;
      border-radius: 50%;
      color: #c9342e;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      font-size: 27px;
      line-height: 1.12;
      font-weight: 900;
      transform: rotate(4deg);
    }}
    .date {{
      position: absolute;
      right: 16px;
      bottom: 28px;
      color: #696f72;
      font-size: 21px;
      line-height: 1.3;
    }}
    .metrics {{ display: flex; gap: 12px; flex-wrap: wrap; justify-content: flex-end; margin: 0 0 26px; }}
    .pill {{
      display: inline-flex;
      min-height: 34px;
      align-items: center;
      padding: 4px 14px;
      border: 1px solid #e4d8c5;
      border-radius: 2px;
      background: #fffaf0;
      box-shadow: 0 5px 10px rgba(48, 36, 18, .08);
      font-size: 20px;
    }}
    .section {{
      padding: 28px 0 34px;
      border-top: 2px dashed #d9d0c0;
    }}
    .section-head {{ display: flex; align-items: flex-start; gap: 20px; margin-bottom: 24px; }}
    .section-title {{
      position: relative;
      flex: 0 0 auto;
      min-width: 168px;
      padding: 13px 18px 14px;
      background: #fffdf5;
      border: 1px solid #e1d6c5;
      box-shadow: 0 8px 15px rgba(48, 36, 18, .10);
      transform: rotate(-.8deg);
    }}
    .section-title span {{
      color: #111820;
      font-size: 31px;
      line-height: 1.18;
      font-weight: 900;
      border-bottom: 4px solid #c9342e;
    }}
    .blue-strip {{
      flex: 1 1 auto;
      padding: 13px 16px;
      border: 3px solid #245ca0;
      border-radius: 2px 1px 3px 1px;
      background: #fffef9;
      font-size: 20px;
      line-height: 1.42;
      color: #26313d;
      transform: rotate(.35deg);
    }}
    .papers {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      align-items: start;
    }}
    .paper-wrap {{
      position: relative;
      filter: drop-shadow(0 12px 18px rgba(48, 36, 18, .13));
    }}
    .paper {{
      min-height: 176px;
      padding: 22px 22px 20px;
      border: 1px solid #e6dccd;
      border-radius: 2px 1px 3px 1px;
    }}
    .item-title {{
      display: flex;
      align-items: flex-start;
      gap: 8px;
      color: #151b20;
      font-size: 25px;
      line-height: 1.28;
      font-weight: 900;
    }}
    .item-title span:last-child {{ border-bottom: 3px solid #c9342e; }}
    .num {{
      flex: 0 0 auto;
      width: 32px;
      height: 32px;
      border: 3px solid #c9342e;
      border-radius: 50%;
      color: #c9342e;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      line-height: 1;
      font-weight: 900;
    }}
    .item-detail {{
      margin-top: 13px;
      color: #c9342e;
      font-size: 20px;
      line-height: 1.48;
      font-weight: 800;
    }}
    .tag {{
      display: inline-block;
      margin: 12px 7px 0 0;
      padding: 4px 10px;
      border: 1px solid #ded5c6;
      border-radius: 999px;
      background: #fffefa;
      color: #5a5f61;
      font-size: 17px;
      line-height: 1.2;
    }}
    .item-source {{
      margin-top: 13px;
      color: #146fc2;
      font-size: 19px;
      line-height: 1.3;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: 390px;
    }}
    .index-note {{
      position: relative;
      width: 380px;
      min-height: 104px;
      padding: 17px 16px 15px;
      border: 1px solid #bad0e5;
      background: #edf6ff;
      filter: drop-shadow(0 10px 14px rgba(32, 48, 68, .12));
      transform: rotate(-.7deg);
      clip-path: polygon(0 2%, 98% 0, 100% 100%, 2% 97%);
    }}
    .index-title {{
      color: #214d87;
      font-size: 21px;
      line-height: 1.25;
      font-weight: 900;
      border-bottom: 3px solid #214d87;
      margin-bottom: 8px;
    }}
    .index-chip {{
      display: inline-block;
      margin: 5px 6px 0 0;
      padding: 5px 8px;
      background: #fffef9;
      border: 1px solid #cfdaea;
      color: #214d87;
      font-size: 17px;
      line-height: 1.2;
    }}
    .related {{
      position: relative;
      margin-top: 20px;
      padding: 18px 20px;
      border: 1px solid #d8cfe7;
      background: #f5efff;
      color: #44315f;
      font-size: 22px;
      line-height: 1.4;
      transform: rotate(.3deg);
    }}
    .full-url {{
      display: flex;
      gap: 18px;
      margin-top: 22px;
      color: #667085;
      font-size: 20px;
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
      <header class="header">
        <div class="title-paper">
          <div class="tape"></div>
          <h1 class="title">{header}</h1>
          <div class="subtitle">先抓重点，再做闭环</div>
        </div>
        <div class="judgment">{judgment}</div>
        <div class="judgment-stamp">今日<br>判断</div>
        <div class="date">{date}</div>
      </header>
      <div class="metrics">{metrics}</div>
      <div>
        {sections}
      </div>
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


def estimate_image_height(data: dict[str, Any]) -> int:
    boards = (data.get("boards") or [])[:5]
    height = 300
    for board in boards:
        featured = board.get("featured") or {}
        item_count = 1 if featured.get("title") else 0
        item_count += min(len(board.get("items") or []), max(0, 3 - item_count))
        rows = max(1, (item_count + (1 if board.get("more") else 0) + 1) // 2)
        height += 155 + rows * 235
    if related_line(data):
        height += 80
    if data.get("full_board_url"):
        height += 70
    return min(max(height, 1200), 3200)


def screenshot_html(html_path: Path, output: Path, height: int) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        screenshot_html_with_system_browser(html_path, output, height)
        return

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
        page_height = page.evaluate("document.documentElement.scrollHeight")
        page.set_viewport_size({"width": WIDTH, "height": min(max(int(page_height), 900), 3200)})
        page.screenshot(path=str(output), full_page=True)
        browser.close()


def screenshot_html_with_system_browser(html_path: Path, output: Path, height: int) -> None:
    executable = browser_executable()
    if not executable:
        raise RuntimeError(
            "No Playwright browser or system Chrome/Edge was found. "
            "Install a browser or run `playwright install chromium`."
        )
    subprocess.run(
        [
            executable,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--window-size=1080,{height}",
            f"--screenshot={output.resolve()}",
            html_path.resolve().as_uri(),
        ],
        check=True,
    )


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
        screenshot_html(html_output, output, estimate_image_height(data))
        print(output)
    print(html_output)


if __name__ == "__main__":
    main()
