#!/usr/bin/env python3
"""Overlay CMS content onto HTML templates for GitHub Pages."""

from __future__ import annotations

import html
import re
import shutil
from datetime import date, datetime
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
SITE = ROOT / "_site"
STATIC_DIRS = ("admin", "assets", "media")
RESERVED_SLUGS = {"admin", "assets", "berichten", "media"}


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def parse_markdown(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n?(.*)\Z", text, re.DOTALL)
    if not match:
        return {"body": text, "slug": path.stem}
    meta = yaml.safe_load(match.group(1)) or {}
    meta["body"] = match.group(2).strip()
    meta["slug"] = path.stem
    return meta


def md_to_html(text: str | None) -> str:
    if not text:
        return ""
    return markdown.markdown(text, extensions=["nl2br", "sane_lists"])


def rewrite_root_urls(html: str, depth: int, slugs: list[str] | None = None) -> str:
    prefix = "../" * depth
    names = ["media", "admin", "berichten", "assets", *(slugs or [])]
    pattern = "|".join(re.escape(name) for name in names)
    return re.sub(rf'(?<=["\'(])/((?:{pattern})/)', rf"{prefix}\1", html)


def asset(depth: int, path: str) -> str:
    return f"{'../' * depth}{path}"


def href(depth: int, path: str) -> str:
    if not path:
        return "./" if depth == 0 else "../" * depth
    return f"{'../' * depth}{path}"


def media_src(value: str | None, depth: int) -> str:
    if not value:
        return ""
    path = str(value).lstrip("/")
    return f"{'../' * depth}{path}"


def format_date(value) -> str:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        months = (
            "januari", "februari", "maart", "april", "mei", "juni",
            "juli", "augustus", "september", "oktober", "november", "december",
        )
        return f"{value.day} {months[value.month - 1]} {value.year}"
    return str(value or "")


def excerpt(post: dict, limit: int = 180) -> str:
    text = str(post.get("summary") or "").strip()
    if not text:
        text = re.sub(r"[#*_>`\[\]()]+", " ", str(post.get("body") or ""))
        text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[: limit - 1].rsplit(" ", 1)[0] + "…"
    return text


def bericht_card(post: dict, *, depth: int, href_value: str) -> str:
    title = html.escape(str(post.get("title") or "Bericht"))
    summary = html.escape(excerpt(post))
    date_label = html.escape(format_date(post.get("date")))
    img = media_src(post.get("image"), depth)
    classes = "bericht bericht--has-image" if img else "bericht"
    img_html = f'<img src="{html.escape(img)}" alt="">' if img else ""
    summary_html = f'<p class="excerpt">{summary}</p>' if summary else ""
    return (
        f'<a class="{classes}" href="{html.escape(href_value)}">'
        f"{img_html}"
        f'<div class="bericht__body">'
        f"<h3>{title}</h3>"
        f'<p class="meta">{date_label}</p>'
        f"{summary_html}"
        f"</div></a>"
    )


def menu_pages(pages: list[dict]) -> list[dict]:
    visible = [page for page in pages if page.get("menu", True) is not False]
    visible.sort(key=lambda page: (int(page.get("weight") or 10), str(page.get("title") or page["slug"]).lower()))
    return visible


def nav_items(pages: list[dict]) -> list[tuple[str, str]]:
    items = [("Home", ""), ("Berichten", "berichten/")]
    for page in menu_pages(pages):
        items.append((str(page.get("title") or page["slug"]), f"{page['slug']}/"))
    return items


def layout(*, title: str, description: str, depth: int, active: str, body: str, pages: list[dict]) -> str:
    nav = []
    for label, path in nav_items(pages):
        cls = ' class="is-active"' if label == active else ""
        nav.append(f'<li><a href="{href(depth, path)}"{cls}>{html.escape(label)}</a></li>')
    nav_html = "".join(nav)
    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Literata:opsz,wght@7..72,400;7..72,600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{asset(depth, "assets/css/site.css")}">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="{href(depth, "")}">Hoog Baarlo</a>
    <ul class="nav">{nav_html}</ul>
  </header>
  <main>
{body}
  </main>
  <footer class="site-footer">Hoog Baarlo</footer>
</body>
</html>
"""


def write_page(rel_path: str, html: str) -> None:
    dest = SITE / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")


def copy_static() -> None:
    for name in STATIC_DIRS:
        src = ROOT / name
        dest = SITE / name
        if dest.exists():
            shutil.rmtree(dest)
        if src.exists():
            shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".gitkeep"))


def build() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    copy_static()

    home = load_yaml(CONTENT / "home.yaml")
    posts = [parse_markdown(path) for path in sorted((CONTENT / "berichten").glob("*.md"))]
    posts.sort(key=lambda item: str(item.get("date") or ""), reverse=True)
    pages = [
        parse_markdown(path)
        for path in sorted((CONTENT / "pages").glob("*.md"))
        if path.stem not in RESERVED_SLUGS
    ]
    page_slugs = [page["slug"] for page in pages]

    site_title = home.get("title") or "Hoog Baarlo"
    tagline = home.get("tagline") or ""
    description = f"{site_title} — {tagline}".strip(" —")

    hero = media_src(home.get("hero"), 0)
    if hero:
        visual = f'<figure class="hero__visual"><img src="{hero}" alt=""></figure>'
    else:
        visual = '<div class="hero__visual hero__visual--empty" aria-hidden="true"></div>'

    cards = [
        bericht_card(post, depth=0, href_value=href(0, f"berichten/{post['slug']}/"))
        for post in posts[:8]
    ]
    cards_html = "\n      ".join(cards) or "<p>Nog geen berichten.</p>"

    home_body = f"""  <section class="hero">
    <div class="hero__copy">
      <h1>{site_title}</h1>
      <p>{tagline}</p>
      {rewrite_root_urls(md_to_html(home.get("intro")), 0, page_slugs)}
    </div>
    {visual}
  </section>
  <section class="section">
    <h2>Berichten</h2>
    <div class="berichten">
      {cards_html}
    </div>
  </section>"""
    write_page("index.html", layout(
        title=f"Home · {site_title}",
        description=description,
        depth=0,
        active="Home",
        body=home_body,
        pages=pages,
    ))

    list_cards = [
        bericht_card(post, depth=1, href_value=f"{post['slug']}/")
        for post in posts
    ]
    write_page("berichten/index.html", layout(
        title=f"Berichten · {site_title}",
        description=description,
        depth=1,
        active="Berichten",
        body=f"""  <section class="section">
    <div class="page-head"><h1>Berichten</h1></div>
    <div class="berichten">
      {"\n      ".join(list_cards) or "<p>Nog geen berichten.</p>"}
    </div>
  </section>""",
        pages=pages,
    ))

    for post in posts:
        img = media_src(post.get("image"), 2)
        figure = f'<figure><img src="{img}" alt="{post.get("title", "")}"></figure>' if img else ""
        body_html = rewrite_root_urls(md_to_html(post.get("body")), 2, page_slugs)
        write_page(f"berichten/{post['slug']}/index.html", layout(
            title=f"{post.get('title', 'Bericht')} · {site_title}",
            description=description,
            depth=2,
            active="Berichten",
            body=f"""  <section class="section">
    <div class="page-head">
      <h1>{html.escape(str(post.get("title", "")))}</h1>
      <p class="meta">{format_date(post.get("date"))}</p>
    </div>
    <div class="prose">
      {figure}
      {body_html}
    </div>
  </section>""",
            pages=pages,
        ))

    for page in pages:
        write_page(f"{page['slug']}/index.html", layout(
            title=f"{page.get('title', page['slug'])} · {site_title}",
            description=description,
            depth=1,
            active=str(page.get("title") or page["slug"]),
            body=f"""  <section class="section">
    <div class="page-head"><h1>{html.escape(str(page.get("title") or page["slug"]))}</h1></div>
    <div class="prose">
      {rewrite_root_urls(md_to_html(page.get("body")), 1, page_slugs)}
    </div>
  </section>""",
            pages=pages,
        ))


if __name__ == "__main__":
    build()
