#!/usr/bin/env python3
"""Render ljg-card -m style WeChat PNG cards from an agent board JSON file."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


WIDTH = 1080
HEIGHT = 1440
BOARD_PAGE_SIZE = 2
CARD_TONES = ["#fffdf8", "#fff8f5", "#f8fbf7"]
CARD_LABELS = ["事件", "判断", "影响"]
CHAIN_BOARD_HINTS = ("今日必看", "商业", "市场", "行业")


def text(value: Any) -> str:
    return "" if value is None else str(value)


def esc(value: Any) -> str:
    return html.escape(text(value), quote=True)


def compact(value: Any, limit: int) -> str:
    raw = re.sub(r"\s+", " ", text(value)).strip()
    if len(raw) <= limit:
        return raw
    return raw[: max(1, limit - 1)].rstrip("，。；、,. ") + "…"


def metric_label(metric: Any) -> str:
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
        count, thread = summary_text.split("；", 1)
    return count, thread, ""


def section_thesis(summary: Any) -> str:
    _, thread, _ = summary_parts(summary)
    thesis = thread.replace("主线：", "").replace("建议动作：", "")
    return compact(thesis, 38)


def section_count(summary: Any) -> str:
    count, _, _ = summary_parts(summary)
    return compact(count.replace("今日 ", "").replace("，", " · "), 16)


def action_text(board: dict[str, Any]) -> str:
    _, _, action = summary_parts(board.get("summary"))
    if action:
        return f"下一步：{compact(action.replace('建议动作：', ''), 42)}"
    featured = board.get("featured") or {}
    title = compact(featured.get("title"), 20)
    if title:
        return f"下一步：跟踪「{title}」后续反馈。"
    return "下一步：跟踪本栏关键变化，并补充可执行判断。"


def split_detail(value: Any) -> tuple[str, str]:
    detail = text(value).strip()
    if not detail:
        return "一句话判断：", ""
    for delimiter in ("：", ":"):
        if delimiter in detail:
            label, body = detail.split(delimiter, 1)
            if len(label) <= 8:
                return f"{label}{delimiter}", compact(body, 42)
    return "一句话判断：", compact(detail, 42)


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
    return [compact(candidate, 26) for candidate in candidates if text(candidate).strip()][:2]


def tags_html(tags: list[Any] | None) -> str:
    if not tags:
        return ""
    return "".join(f'<span class="tag">{esc(compact(tag, 10))}</span>' for tag in tags[:3])


def related_labels(board: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for entry in board.get("more") or []:
        if isinstance(entry, dict):
            label = entry.get("label") or entry.get("title") or entry.get("url")
        else:
            label = entry
        if label:
            labels.append(compact(label, 16))
        if len(labels) >= 3:
            return labels
    featured = board.get("featured") or {}
    for item in featured.get("related") or []:
        label = item.get("title") or item.get("path")
        if label:
            labels.append(compact(label, 16))
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


def layout_mode(board: dict[str, Any], board_index: int, entries: list[tuple[dict[str, Any], bool]]) -> str:
    if len(entries) <= 1:
        return "single"
    if len(entries) == 2:
        return "main-side"
    name = text(board.get("name"))
    if board_index == 0 or any(hint in name for hint in CHAIN_BOARD_HINTS):
        return "chain"
    return "parallel"


def page_chunks(boards: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    return [boards[i : i + BOARD_PAGE_SIZE] for i in range(0, len(boards), BOARD_PAGE_SIZE)]


def card_item_html(item: dict[str, Any], index: int, featured: bool, mode: str) -> str:
    label, detail = split_detail(item.get("judgment") or item.get("summary"))
    facts = "".join(f"<li>{esc(fact)}</li>" for fact in fact_candidates(item, featured))
    domain = source_domain(item)
    source = source_url(item)
    source_html = f'<a class="source" href="{esc(source)}">{esc(domain)} ↗</a>' if domain and source else ""
    tone = CARD_TONES[(index - 1) % len(CARD_TONES)]
    role = CARD_LABELS[(index - 1) % len(CARD_LABELS)]
    title_limit = 30 if mode in {"single", "main-side"} else 24
    return f"""
      <article class="story-card story-card-{index}" style="background:{tone};">
        <div class="card-kicker"><span>{index}</span>{role}</div>
        <h3>{esc(compact(item.get("title"), title_limit))}</h3>
        <p class="insight"><strong>{esc(label)}</strong>{esc(detail)}</p>
        <ul>{facts}</ul>
        <div class="card-footer">
          <div>{tags_html(item.get("tags"))}</div>
          {source_html}
        </div>
      </article>
    """


def section_html(board: dict[str, Any], board_index: int) -> str:
    entries = board_entries(board)
    if not entries:
        return ""
    mode = layout_mode(board, board_index, entries)
    cards = "".join(card_item_html(item, i, featured, mode) for i, (item, featured) in enumerate(entries, start=1))
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
    return f"""
    <section class="board-section" data-layout="{mode}">
      <header class="section-header">
        <h2>{esc(board.get("name") or "Board")}</h2>
        <p>{count_html}<span>{esc(section_thesis(board.get("summary")))}</span></p>
      </header>
      <div class="story-grid">{cards}</div>
      <div class="action-bar">{esc(action_text(board))}</div>
      {related}
    </section>
    """


def cover_card_html(data: dict[str, Any], total_pages: int) -> str:
    title = esc(data.get("title") or "Agent Daily Board")
    date = esc(data.get("date"))
    judgment = esc(compact(data.get("overall_judgment"), 86))
    metrics = [metric_label(metric) for metric in (data.get("metrics") or [])[:3] if metric_label(metric)]
    stats = "".join(f"<span>{esc(metric)}</span>" for metric in metrics)
    boards = data.get("boards") or []
    board_lines = "".join(
        f"<li><strong>{esc(board.get('name') or 'Board')}</strong><span>{esc(section_thesis(board.get('summary')))}</span></li>"
        for board in boards[:4]
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>{head_html()}</head>
<body>
  <main class="ljg-card cover-card">
    <div class="corner-tape"></div>
    <header class="cover-hero">
      <p class="eyebrow">AGENT DAILY BOARD</p>
      <h1>{title}</h1>
      <p class="subtitle">先抓重点，再做闭环</p>
    </header>
    <section class="mainline">
      <span>今日主线</span>
      <p>{judgment}</p>
    </section>
    <aside class="stamp">今日<br>判断</aside>
    <section class="board-map">
      <h2>今日看板</h2>
      <ul>{board_lines}</ul>
    </section>
    <footer class="card-footer-line">
      <span>{date}</span>{stats}<em>1 / {total_pages}</em>
    </footer>
  </main>
</body>
</html>
"""


def content_card_html(data: dict[str, Any], boards: list[dict[str, Any]], page_no: int, total_pages: int) -> str:
    title = esc(data.get("title") or "Agent Daily Board")
    sections = "".join(section_html(board, i) for i, board in enumerate(boards))
    names = " / ".join(text(board.get("name") or "Board") for board in boards)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>{head_html()}</head>
<body>
  <main class="ljg-card content-card">
    <header class="running-head">
      <span>{title}</span>
      <em>{esc(names)}</em>
    </header>
    {sections}
    <footer class="card-footer-line">
      <span>{esc(data.get("date"))}</span><em>{page_no} / {total_pages}</em>
    </footer>
  </main>
</body>
</html>
"""


def head_html() -> str:
    return f"""
<meta charset="utf-8">
<meta name="viewport" content="width={WIDTH}, initial-scale=1">
<style>
  :root {{
    --ink:#20242a;
    --muted:#68717b;
    --dim:#9a9287;
    --red:#e6463d;
    --blue:#2f6db2;
    --paper:#fbf6ed;
    --paper-card:#fffdf8;
    --border:#eadfce;
    --line:#e4d9ca;
    --link:#1f68b3;
  }}
  * {{ box-sizing:border-box; }}
  html, body {{
    width:{WIDTH}px;
    height:{HEIGHT}px;
    margin:0;
    padding:0;
    overflow:hidden;
    background:#f4efe6;
    color:var(--ink);
    font-family:Georgia,"Times New Roman",serif;
  }}
  .ljg-card {{
    position:relative;
    width:{WIDTH}px;
    height:{HEIGHT}px;
    padding:72px 74px 58px;
    background:
      radial-gradient(circle at 10px 10px, rgba(110,90,60,.055) 1px, transparent 1px),
      linear-gradient(#fbf6ed, #f7f0e6);
    background-size:24px 24px, auto;
    overflow:hidden;
  }}
  .corner-tape {{
    position:absolute;
    left:64px;
    top:48px;
    width:118px;
    height:36px;
    background:#e7cfa8;
    opacity:.72;
    transform:rotate(-11deg);
    box-shadow:0 4px 12px rgba(70,45,20,.12);
  }}
  .cover-hero {{
    width:560px;
    padding-top:40px;
  }}
  .eyebrow {{
    margin:0 0 18px;
    color:var(--dim);
    font-size:24px;
    letter-spacing:.08em;
  }}
  h1 {{
    margin:0;
    color:#1f2328;
    font-size:78px;
    line-height:1.04;
    font-weight:900;
    letter-spacing:0;
  }}
  .subtitle {{
    display:inline-block;
    margin:26px 0 0;
    color:var(--red);
    font-size:34px;
    line-height:1.2;
    font-weight:800;
    border-bottom:6px solid rgba(230,70,61,.72);
  }}
  .mainline {{
    position:absolute;
    left:650px;
    top:132px;
    width:310px;
    min-height:220px;
    padding-left:24px;
    border-left:8px solid var(--blue);
  }}
  .mainline span {{
    display:block;
    margin-bottom:16px;
    font-size:28px;
    font-weight:900;
  }}
  .mainline p {{
    margin:0;
    font-size:28px;
    line-height:1.62;
    color:#31363b;
  }}
  .stamp {{
    position:absolute;
    right:88px;
    top:88px;
    width:94px;
    height:94px;
    border:5px solid var(--red);
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
    color:var(--red);
    font-size:29px;
    line-height:1.08;
    font-weight:900;
    transform:rotate(5deg);
  }}
  .board-map {{
    position:absolute;
    left:74px;
    right:74px;
    bottom:150px;
    padding:34px 36px;
    background:rgba(255,253,248,.78);
    border:1px solid var(--border);
    box-shadow:0 10px 24px rgba(54,42,28,.07);
  }}
  .board-map h2 {{
    margin:0 0 22px;
    font-size:34px;
    line-height:1.2;
  }}
  .board-map ul {{
    list-style:none;
    margin:0;
    padding:0;
  }}
  .board-map li {{
    display:grid;
    grid-template-columns:180px 1fr;
    gap:22px;
    padding:16px 0;
    border-top:1px dashed var(--line);
    font-size:24px;
    line-height:1.45;
  }}
  .board-map li:first-child {{ border-top:0; }}
  .board-map strong {{ color:#20242a; }}
  .board-map span {{ color:var(--muted); }}
  .running-head {{
    display:flex;
    align-items:flex-end;
    justify-content:space-between;
    gap:28px;
    padding-bottom:24px;
    margin-bottom:28px;
    border-bottom:1px solid var(--line);
  }}
  .running-head span {{
    font-size:28px;
    line-height:1.2;
    font-weight:900;
  }}
  .running-head em {{
    color:var(--muted);
    font-style:normal;
    font-size:22px;
  }}
  .board-section {{
    margin-top:28px;
    padding-top:26px;
    border-top:1px dashed var(--line);
  }}
  .board-section:first-of-type {{
    margin-top:0;
    padding-top:0;
    border-top:0;
  }}
  .section-header {{
    display:flex;
    align-items:center;
    gap:24px;
    margin-bottom:20px;
  }}
  .section-header h2 {{
    position:relative;
    flex:0 0 auto;
    margin:0;
    padding:14px 20px 15px;
    background:#fff8ea;
    border:1px solid var(--border);
    box-shadow:0 7px 14px rgba(53,44,34,.055);
    font-size:34px;
    line-height:1.1;
    font-weight:900;
    white-space:nowrap;
  }}
  .section-header h2::before {{
    content:"";
    position:absolute;
    left:34px;
    top:-15px;
    width:72px;
    height:20px;
    background:#e7cfa8;
    opacity:.58;
    transform:rotate(-6deg);
  }}
  .section-header h2::after {{
    content:"";
    display:block;
    width:96px;
    height:5px;
    margin-top:7px;
    background:var(--red);
  }}
  .section-header p {{
    flex:1;
    margin:0;
    padding-left:18px;
    border-left:5px solid var(--blue);
    color:#3c4147;
    font-size:22px;
    line-height:1.5;
  }}
  .section-count {{
    display:inline-block;
    margin-right:10px;
    color:#858079;
    font-size:19px;
  }}
  .story-grid {{
    display:grid;
    gap:16px;
    align-items:start;
  }}
  .board-section[data-layout="chain"] .story-grid,
  .board-section[data-layout="parallel"] .story-grid {{
    grid-template-columns:repeat(3,minmax(0,1fr));
  }}
  .board-section[data-layout="main-side"] .story-grid {{
    grid-template-columns:1.45fr 1fr;
  }}
  .board-section[data-layout="single"] .story-grid {{
    grid-template-columns:1fr;
  }}
  .story-card {{
    position:relative;
    padding:22px 20px 18px;
    border:1px solid var(--border);
    border-radius:8px;
    box-shadow:0 7px 15px rgba(53,44,34,.06);
  }}
  .board-section[data-layout="chain"] .story-card:not(:last-child)::after {{
    content:"→";
    position:absolute;
    right:-27px;
    top:44%;
    color:#f07b25;
    font-size:30px;
    font-weight:700;
  }}
  .card-kicker {{
    display:flex;
    align-items:center;
    gap:10px;
    margin-bottom:12px;
    color:var(--muted);
    font-size:18px;
    font-weight:800;
  }}
  .card-kicker span {{
    width:34px;
    height:34px;
    border-radius:50%;
    background:var(--red);
    color:#fff;
    display:inline-flex;
    align-items:center;
    justify-content:center;
    font-size:20px;
    line-height:1;
  }}
  .story-card h3 {{
    margin:0 0 12px;
    color:#20242a;
    font-size:25px;
    line-height:1.24;
    font-weight:900;
    overflow-wrap:anywhere;
  }}
  .board-section[data-layout="chain"] .story-card h3,
  .board-section[data-layout="parallel"] .story-card h3 {{
    font-size:22px;
  }}
  .insight {{
    margin:0 0 10px;
    color:var(--muted);
    font-size:19px;
    line-height:1.45;
  }}
  .insight strong {{ color:var(--red); }}
  .story-card ul {{
    margin:0 0 12px 20px;
    padding:0;
    color:#42464b;
    font-size:17px;
    line-height:1.42;
  }}
  .card-footer {{
    display:flex;
    align-items:flex-end;
    justify-content:space-between;
    gap:12px;
    margin-top:12px;
  }}
  .tag {{
    display:inline-block;
    margin:0 5px 5px 0;
    padding:4px 9px;
    border:1px solid #d8cfc1;
    border-radius:999px;
    background:rgba(255,255,255,.72);
    color:#555d64;
    font-size:15px;
    line-height:1.15;
  }}
  .source {{
    color:var(--link);
    font-size:16px;
    line-height:1.3;
    text-decoration:none;
    white-space:nowrap;
  }}
  .action-bar {{
    margin-top:16px;
    padding:15px 18px;
    border-left:6px solid var(--red);
    background:#fff8ef;
    color:#20242a;
    font-size:21px;
    line-height:1.45;
  }}
  .related-row {{
    margin-top:12px;
    padding:13px 18px;
    background:#eef5fc;
    color:#315a8a;
    font-size:19px;
    line-height:1.45;
  }}
  .related-row strong {{
    margin-right:14px;
    color:var(--link);
  }}
  .related-row span::before {{
    content:"·";
    margin:0 10px;
  }}
  .card-footer-line {{
    position:absolute;
    left:74px;
    right:74px;
    bottom:52px;
    display:flex;
    align-items:center;
    justify-content:flex-end;
    gap:12px;
    padding-top:18px;
    border-top:1px solid var(--line);
    color:#7d766f;
    font-size:20px;
  }}
  .card-footer-line span + span::before {{
    content:"|";
    margin-right:10px;
    color:#c2b8aa;
  }}
  .card-footer-line em {{
    margin-left:auto;
    font-style:normal;
    color:#a29a91;
  }}
</style>
"""


def build_pages(data: dict[str, Any]) -> list[str]:
    board_pages = page_chunks(data.get("boards") or [])
    total_pages = 1 + len(board_pages)
    pages = [cover_card_html(data, total_pages)]
    for index, boards in enumerate(board_pages, start=2):
        pages.append(content_card_html(data, boards, index, total_pages))
    return pages


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


def output_paths(path: Path, count: int, suffix: str) -> list[Path]:
    if count == 1:
        return [path]
    return [path.with_name(f"{path.stem}-{index:02d}{suffix}") for index in range(1, count + 1)]


def write_compat_first(path: Path, first_path: Path) -> None:
    if path == first_path:
        return
    shutil.copyfile(first_path, path)


def screenshot_html(html_path: Path, output: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        screenshot_html_with_system_browser(html_path, output)
        return

    with sync_playwright() as p:
        executable = browser_executable()
        if executable:
            browser = p.chromium.launch(executable_path=executable)
        else:
            browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=1)
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.screenshot(path=str(output), full_page=False)
        browser.close()


def screenshot_html_with_system_browser(html_path: Path, output: Path) -> None:
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
            f"--window-size={WIDTH},{HEIGHT}",
            f"--screenshot={output.resolve()}",
            html_path.resolve().as_uri(),
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Render ljg-card -m style WeChat PNG cards.")
    parser.add_argument("input", help="Path to board JSON file.")
    parser.add_argument("--output", help="Output PNG path or base path. Defaults to <input>-wechat-card.png.")
    parser.add_argument("--html-output", help="Output HTML path or base path. Defaults to <input>-wechat-card.html.")
    parser.add_argument("--html-only", action="store_true", help="Only write the HTML artifacts.")
    args = parser.parse_args()

    input_path = Path(args.input)
    data = json.loads(input_path.read_text(encoding="utf-8"))
    pages = build_pages(data)

    png_base = Path(args.output) if args.output else input_path.with_name(f"{input_path.stem}-wechat-card.png")
    html_base = (
        Path(args.html_output) if args.html_output else input_path.with_name(f"{input_path.stem}-wechat-card.html")
    )
    html_paths = output_paths(html_base, len(pages), ".html")
    png_paths = output_paths(png_base, len(pages), ".png")

    for html_path, page_html in zip(html_paths, pages):
        html_path.write_text(page_html, encoding="utf-8")
        print(html_path)

    if not args.html_only:
        for html_path, png_path in zip(html_paths, png_paths):
            screenshot_html(html_path, png_path)
            print(png_path)
        if len(png_paths) > 1:
            write_compat_first(png_base, png_paths[0])
            print(png_base)
    if len(html_paths) > 1:
        write_compat_first(html_base, html_paths[0])
        print(html_base)


if __name__ == "__main__":
    main()
