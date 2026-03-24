#!/usr/bin/env python3
"""Собирает статический сайт из *.md в корне проекта → каталог site/."""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
ARTICLES_DIR = SITE / "articles"
ASSETS = SITE / "assets"
STYLE_SRC = ROOT / "style.css"
STYLE_DST = ASSETS / "style.css"

MD = markdown.Markdown(extensions=["smarty", "sane_lists"])

FONT_LINK = """  <link href="https://fonts.googleapis.com/css2?family=VT323&display=swap" rel="stylesheet">"""

TALOS_CHATTER = """  <div class="talos-chatter" aria-hidden="true"><pre>guest@loc:~$ webcrawl --node /archive
[scan] sector 7 … ok
daemon: sphinx_idle
log: signal_lost layer=3
stderr → /dev/null
.M.M.M.M.M.M.M.M.
integrity: PENDING
ui: console v0.9
awaiting input _</pre></div>"""

TALOS_HEXBAR = """    <p class="talos-hexbar" aria-hidden="true">&lt;a href="d09e d0a8 e2fb 3c1a 9d02 a7ff 4e21 bbb0"&gt;</p>"""

THEME_HEAD_SCRIPT = """  <script>
    (function(){try{var t=localStorage.getItem("theme");if(t==="light")document.documentElement.setAttribute("data-theme","light");}catch(e){}})();
  </script>"""

THEME_CONTROL = """  <div class="theme-switch-wrap">
    <button type="button" class="theme-btn" id="theme-toggle" aria-pressed="false" aria-label="Включить светлую тему">
      <span class="theme-btn__text" id="theme-toggle-label">день</span>
    </button>
  </div>"""

THEME_FOOT_SCRIPT = """  <script>
    (function(){
      var root=document.documentElement;
      var btn=document.getElementById("theme-toggle");
      var label=document.getElementById("theme-toggle-label");
      if(!btn)return;
      function sync(){
        var light=root.getAttribute("data-theme")==="light";
        btn.setAttribute("aria-pressed",light?"true":"false");
        btn.setAttribute("aria-label",light?"Включить тёмную тему":"Включить светлую тему");
        if(label)label.textContent=light?"ночь":"день";
      }
      btn.addEventListener("click",function(){
        if(root.getAttribute("data-theme")==="light")root.removeAttribute("data-theme");
        else root.setAttribute("data-theme","light");
        try{localStorage.setItem("theme",root.getAttribute("data-theme")==="light"?"light":"dark");}catch(e){}
        sync();
      });
      sync();
    })();
  </script>"""


def first_h1_title(md_text: str) -> str | None:
    for line in md_text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def slug_from_filename(path: Path) -> str:
    return path.stem


# «Битые» вставки между абзацами (стиль Talos / повреждённый поток)
_PROSE_ARTIFACTS = (
    "0x7F_ERR // partial_frame · checksum ?",
    "▒▓░▒▓░ … stream_corrupt · retry=3",
    "<frag d09e a7ff c0de /> // EOF before close",
    "READ 0x00 │ READ 0xFF │ length ≠ bytes",
    "guest@loc: vault_dump.bin · [████░░] 62%",
    "M.M.M … echo_OFF … M.M.M · layer glitch",
    "~ §§§ … utf-8: decoder stalled at U+FFFD",
    "EM_buffer: overflow @ 0 of ∞ // dropped",
    "webcrawl: node lost · backtrace: ???",
    "█▀▄ █▄▀ ▀▄▀ // phosphor bleed",
    "signal: -∞ dB · ████████████",
    "integrity: PENDING … ████▒▒▒▒ … OK?",
)


# Вставлять артефакт только на каждом K-м зазоре между абзацами (1 = как раньше, у всех).
_ARTIFACT_EVERY_KTH_GAP = 3


def inject_prose_artifacts(html: str) -> str:
    """Вставляет строки только между некоторыми парами <p> (каждый K-й зазор)."""
    gap_num = 0
    artifact_idx = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal gap_num, artifact_idx
        gap_num += 1
        ws = m.group(1)
        if gap_num % _ARTIFACT_EVERY_KTH_GAP != 0:
            return m.group(0)
        line = _PROSE_ARTIFACTS[artifact_idx % len(_PROSE_ARTIFACTS)]
        artifact_idx += 1
        variant = artifact_idx % 6
        return (
            f"</p>{ws}<div class=\"prose-artifact prose-artifact--{variant}\" "
            f'aria-hidden="true">{_esc(line)}</div>{ws}'
        )

    return re.sub(r"</p>(\s*)(?=<p\b)", repl, html, flags=re.IGNORECASE)


def article_html(title: str, body_html: str, root_prefix: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
{THEME_HEAD_SCRIPT}  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{FONT_LINK}
  <link rel="stylesheet" href="{root_prefix}assets/style.css">
</head>
<body>
{TALOS_CHATTER}
{THEME_CONTROL}  <div class="wrap">
    <header class="site-header">
      <h1 class="site-title">Архив</h1>
      <p class="site-tagline">Заметки программиста</p>
    </header>
    <div class="wrap-inner">
{TALOS_HEXBAR}
    <main class="article">
      <a class="back" href="{root_prefix}index.html">← к списку</a>
      <article class="prose">
        {body_html}
      </article>
    </main>
    </div>
    <!-- <footer class="site-footer">Статический вывод</footer> -->
  </div>
{THEME_FOOT_SCRIPT}</body>
</html>
"""


def index_html(items: list[tuple[str, str, str]]) -> str:
    lis = []
    for slug, title, _path in items:
        lis.append(
            f'<li><a href="articles/{_esc(slug)}.html">{_esc(title)}'
            f'<span class="slug">{_esc(slug)}</span></a></li>'
        )
    list_html = "\n        ".join(lis)
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
{THEME_HEAD_SCRIPT}  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Архив статей</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{FONT_LINK}
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
{TALOS_CHATTER}
{THEME_CONTROL}  <div class="wrap">
    <header class="site-header">
      <h1 class="site-title">Архив</h1>
      <p class="site-tagline">Заметки программиста</p>
    </header>
    <div class="wrap-inner">
{TALOS_HEXBAR}
    <main>
      <ul class="article-list">
        {list_html}
      </ul>
    </main>
    </div>
     <!-- <footer class="site-footer">Статический вывод</footer> -->
  </div>
{THEME_FOOT_SCRIPT}</body>
</html>
"""


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> int:
    SITE.mkdir(parents=True, exist_ok=True)
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)

    if not STYLE_SRC.is_file():
        print(f"Нет файла стилей: {STYLE_SRC}", file=sys.stderr)
        return 1
    shutil.copy2(STYLE_SRC, STYLE_DST)

    md_files = sorted(ROOT.glob("*.md"))
    if not md_files:
        print("В каталоге нет .md файлов.", file=sys.stderr)
        return 1

    items: list[tuple[str, str, str]] = []
    for path in md_files:
        text = path.read_text(encoding="utf-8")
        title = first_h1_title(text) or path.stem
        slug = slug_from_filename(path)
        MD.reset()
        body = inject_prose_artifacts(MD.convert(text))
        out = ARTICLES_DIR / f"{slug}.html"
        out.write_text(article_html(title, body, "../"), encoding="utf-8")
        items.append((slug, title, str(path)))

    (SITE / "index.html").write_text(index_html(items), encoding="utf-8")
    print(f"Готово: {len(items)} статей → {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
