#!/usr/bin/env python3
"""Render a WeChat-friendly 2x PNG from an agent board JSON file."""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


WIDTH = 720
SCALE = 2
CARD_BACKGROUNDS = ["#fff9f1", "#f8fbf7", "#fff6f1", "#f7f8fd", "#fbf9ef"]


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
        return " · ".join(text(part) for part in parts if part)
    return text(summary)


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


def tags_html(tags: list[Any] | None) -> str:
    if not tags:
        return ""
    return "".join(f'<span class="tag">{esc(tag)}</span>' for tag in tags[:3])


def detail_html(value: Any) -> str:
    detail = text(value).strip()
    if not detail:
        return ""
    for delimiter in ("：", ":"):
        if delimiter in detail:
            label, body = detail.split(delimiter, 1)
            if len(label) <= 8:
                return f'<p><strong>{esc(label)}{delimiter}</strong>{esc(body.strip())}</p>'
    return f"<p>{esc(detail)}</p>"


def related_items(data: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for board in data.get("boards") or []:
        featured = board.get("featured") or {}
        for item in featured.get("related") or []:
            title = text(item.get("title") or item.get("path"))
            if title:
                labels.append(title)
            if len(labels) >= 3:
                return labels
    return labels


def more_labels(board: dict[str, Any], data: dict[str, Any]) -> list[str]:
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
    for label in related_items(data):
        if label not in labels:
            labels.append(label)
        if len(labels) >= 3:
            return labels
    return labels


def board_entries(board: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    entries: list[dict[str, Any]] = []
    featured = board.get("featured") or {}
    if featured.get("title"):
        entries.append(featured)
    for item in board.get("items") or []:
        if item.get("title"):
            entries.append(item)
    if not entries:
        return {}, []
    return entries[0], entries[1:3]


def card_html(item: dict[str, Any], number: int, tone: int, featured: bool = False) -> str:
    if not item:
        return ""
    title = esc(item.get("title"))
    domain = esc(source_domain(item))
    source = source_url(item)
    source_html = (
        f'<a class="source" href="{esc(source)}">{domain}<span>↗</span></a>' if source and domain else ""
    )
    tags = tags_html(item.get("tags"))
    feature_class = " featured-card" if featured else ""
    background = CARD_BACKGROUNDS[tone % len(CARD_BACKGROUNDS)]
    return f"""
      <article class="info-card{feature_class}" style="background:{background};">
        <div class="card-head">
          <span class="num">{number}</span>
          <h3>{title}</h3>
        </div>
        {detail_html(item.get("judgment") or item.get("summary"))}
        <div class="card-meta">
          <div>{tags}</div>
          {source_html}
        </div>
      </article>
    """


def section_html(board: dict[str, Any], index: int, data: dict[str, Any]) -> str:
    focus, normals = board_entries(board)
    if not focus:
        return ""
    normal_html = "\n".join(card_html(item, idx + 2, index + idx + 1) for idx, item in enumerate(normals[:2]))
    labels = more_labels(board, data)
    extension = ""
    if labels:
        extension = (
            '<div class="extension"><span class="extension-label">延伸阅读</span>'
            + "".join(f"<span>{esc(label)}</span>" for label in labels[:3])
            + "</div>"
        )
    summary = summary_text(board.get("summary"))
    return f"""
      <section class="section">
        <div class="section-head">
          <div class="section-note"><span>{esc(board.get("name") or "Board")}</span></div>
          <div class="section-summary">{esc(summary)}</div>
        </div>
        <div class="section-grid">
          {card_html(focus, 1, index, featured=True)}
          {normal_html}
        </div>
        {extension}
      </section>
    """


def build_html(data: dict[str, Any]) -> str:
    title = esc(data.get("title") or "Agent Daily Board")
    date = esc(data.get("date"))
    judgment = esc(data.get("overall_judgment"))
    metrics = [metric_label(metric) for metric in (data.get("metrics") or [])[:4]]
    stats = "".join(f"<span>{esc(metric)}</span>" for metric in metrics if metric)
    sections = "\n".join(section_html(board, idx, data) for idx, board in enumerate((data.get("boards") or [])[:5]))

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width={WIDTH}, initial-scale=1">
  <style>
    * {{ box-sizing: border-box; }}
    html, body {{ margin:0; padding:0; width:{WIDTH}px; background:#f4efe5; }}
    body {{
      color:#202124;
      font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",Arial,sans-serif;
      letter-spacing:0;
    }}
    .page {{
      width:{WIDTH}px;
      padding:18px 18px 24px;
      background:
        radial-gradient(circle at 8px 8px, rgba(110,90,60,.08) 1px, transparent 1px),
        linear-gradient(#f7f1e8, #fbf7ee);
      background-size:22px 22px, auto;
    }}
    .cover {{
      position:relative;
      min-height:158px;
      padding:24px 24px 18px 58px;
      border:1px solid #ddcfba;
      background:#fff8ea;
      box-shadow:0 8px 18px rgba(69,49,24,.12);
    }}
    .cover::before {{
      content:"";
      position:absolute;
      left:18px;
      top:19px;
      width:24px;
      height:118px;
      background:
        radial-gradient(circle, #e8dccb 0 4px, transparent 5px) 0 0/24px 24px repeat-y;
    }}
    .corner-tape {{
      position:absolute;
      left:8px;
      top:-8px;
      width:64px;
      height:28px;
      background:#e7cfa8;
      opacity:.7;
      transform:rotate(-22deg);
      box-shadow:0 2px 8px rgba(70,45,20,.12);
    }}
    .cover-title {{
      width:330px;
      font-size:38px;
      line-height:1.08;
      font-weight:900;
      margin:0;
    }}
    .cover-subtitle {{
      display:inline-block;
      margin-top:10px;
      color:#d43b2f;
      font-size:19px;
      line-height:1.2;
      font-weight:800;
      border-bottom:4px solid rgba(212,59,47,.85);
    }}
    .mainline {{
      position:absolute;
      left:382px;
      top:34px;
      width:210px;
      min-height:72px;
      padding:0 0 0 14px;
      border-left:4px solid #1666ad;
      font-size:14px;
      line-height:1.65;
    }}
    .mainline strong {{ display:block; margin-bottom:2px; }}
    .stamp {{
      position:absolute;
      right:20px;
      top:22px;
      width:72px;
      height:72px;
      border:3px solid #d43b2f;
      border-radius:50%;
      color:#d43b2f;
      display:flex;
      align-items:center;
      justify-content:center;
      text-align:center;
      font-size:22px;
      line-height:1.08;
      font-weight:900;
      transform:rotate(5deg);
    }}
    .cover-meta {{
      position:absolute;
      left:300px;
      right:24px;
      bottom:16px;
      padding-top:10px;
      border-top:1px dashed #dbcdb8;
      color:#4b4d4f;
      display:flex;
      gap:14px;
      align-items:center;
      justify-content:flex-start;
      font-size:12px;
      white-space:nowrap;
    }}
    .cover-meta span + span::before {{
      content:"|";
      color:#b7a994;
      margin-right:8px;
    }}
    .section {{
      padding:18px 18px 0;
      border-top:1px dashed #ded1be;
    }}
    .section:first-of-type {{ border-top:0; }}
    .section-head {{
      display:flex;
      align-items:center;
      gap:16px;
      margin-bottom:12px;
    }}
    .section-note {{
      position:relative;
      flex:0 0 auto;
      min-width:120px;
      padding:9px 14px 10px;
      background:#fff7e8;
      border:1px solid #eadcc7;
      box-shadow:0 3px 8px rgba(70,45,20,.08);
      transform:rotate(-1.5deg);
    }}
    .section-note::before, .featured-card::before {{
      content:"";
      position:absolute;
      left:50%;
      top:-10px;
      width:48px;
      height:16px;
      margin-left:-24px;
      background:#e7cfa8;
      opacity:.65;
    }}
    .section-note span {{
      font-size:23px;
      line-height:1.1;
      font-weight:900;
      border-bottom:3px solid #d43b2f;
    }}
    .section-summary {{
      flex:1;
      padding-left:12px;
      border-left:4px solid #1666ad;
      color:#383b3f;
      font-size:14px;
      line-height:1.5;
    }}
    .section-grid {{
      display:grid;
      grid-template-columns:1fr 1fr;
      gap:10px;
    }}
    .info-card {{
      position:relative;
      min-height:118px;
      padding:15px 16px 14px;
      border:1px solid #eadccf;
      border-radius:6px;
      box-shadow:0 4px 10px rgba(60,42,18,.08);
    }}
    .featured-card {{
      grid-column:1 / -1;
      min-height:106px;
      padding-top:20px;
    }}
    .card-head {{
      display:flex;
      gap:10px;
      align-items:flex-start;
    }}
    .num {{
      flex:0 0 auto;
      width:24px;
      height:24px;
      border-radius:50%;
      background:#d94135;
      color:#fff;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      font-size:15px;
      line-height:1;
      font-weight:900;
    }}
    h3 {{
      margin:0;
      color:#1f2327;
      font-size:17px;
      line-height:1.35;
      font-weight:900;
      display:-webkit-box;
      -webkit-line-clamp:2;
      -webkit-box-orient:vertical;
      overflow:hidden;
    }}
    .info-card p {{
      margin:10px 0 0;
      color:#2d3034;
      font-size:14px;
      line-height:1.5;
      font-weight:500;
      display:-webkit-box;
      -webkit-line-clamp:2;
      -webkit-box-orient:vertical;
      overflow:hidden;
    }}
    .info-card p strong {{
      color:#d43b2f;
      font-weight:800;
    }}
    .card-meta {{
      display:flex;
      align-items:flex-end;
      justify-content:space-between;
      gap:12px;
      margin-top:10px;
    }}
    .tag {{
      display:inline-block;
      margin:0 5px 5px 0;
      padding:3px 8px;
      border:1px solid #ddd4c7;
      border-radius:999px;
      background:rgba(255,255,255,.66);
      color:#555b60;
      font-size:12px;
      line-height:1.1;
    }}
    .source {{
      flex:0 1 auto;
      max-width:190px;
      color:#075ca8;
      font-size:13px;
      line-height:1.2;
      text-decoration:none;
      white-space:nowrap;
      overflow:hidden;
      text-overflow:ellipsis;
    }}
    .source span {{ margin-left:4px; }}
    .extension {{
      margin-top:10px;
      padding:9px 12px;
      border:1px solid #d8e3ee;
      border-radius:4px;
      background:#eef6ff;
      color:#173b68;
      font-size:13px;
      line-height:1.45;
      box-shadow:0 3px 8px rgba(20,60,100,.06);
    }}
    .extension-label {{
      display:inline-block;
      margin-right:10px;
      color:#075ca8;
      font-weight:800;
    }}
    .extension span:not(.extension-label)::before {{
      content:"·";
      margin:0 8px 0 4px;
      color:#075ca8;
    }}
  </style>
</head>
<body>
  <main class="page">
    <header class="cover">
      <div class="corner-tape"></div>
      <h1 class="cover-title">{title}</h1>
      <div class="cover-subtitle">先抓重点，再做闭环</div>
      <div class="mainline"><strong>今日主线：</strong>{judgment}</div>
      <div class="stamp">今日<br>判断</div>
      <div class="cover-meta"><span>{date}</span>{stats}</div>
    </header>
    {sections}
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
    height = 210
    for board in (data.get("boards") or [])[:5]:
        focus, normals = board_entries(board)
        if not focus:
            continue
        height += 82
        height += 132
        if normals:
            height += 136
        if more_labels(board, data):
            height += 44
        height += 24
    return min(max(height, 900), 2200)


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
            browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": 900}, device_scale_factor=SCALE)
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page_height = page.evaluate("document.documentElement.scrollHeight")
        page.set_viewport_size({"width": WIDTH, "height": min(max(int(page_height), 900), 2600)})
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
            f"--force-device-scale-factor={SCALE}",
            f"--window-size={WIDTH},{height}",
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
