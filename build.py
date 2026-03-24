#!/usr/bin/env python3
"""Собирает статический сайт из *.md в корне проекта → каталог site/."""

from __future__ import annotations

import base64
import json
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
CLI_JS_SRC = ROOT / "cli-easter-egg.js"
CLI_JS_DST = ASSETS / "cli-easter-egg.js"

# Не показывать в списке на index.html (страница всё равно собирается)
HIDDEN_FROM_INDEX_SLUGS = frozenset({"03-verite-v-boga", "06-pokroviteli-ekrana"})

# Скрытые статьи в CLI: slug, подпись, имя «файла» в ~ (открытие только через cat)
_CLI_HIDDEN_ARTICLES: tuple[tuple[str, str, str], ...] = (
    ("03-verite-v-boga", "«Вы верите в Бога?»", "._____verite._node"),
    ("06-pokroviteli-ekrana", "«Покровители экрана»", "._____screen._out"),
)

MD = markdown.Markdown(extensions=["smarty", "sane_lists"])

FONT_LINK = """  <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=VT323&display=swap" rel="stylesheet">"""

TALOS_CHATTER = """  <div class="talos-chatter" aria-hidden="true"><pre>guest@loc:~$ webcrawl --node /archive <span class="talos-chatter__hint" title="Переключатель «день / ночь» — 13 нажатий">13×night</span>
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

# Кастомный base64 для скрытой статьи (должен совпадать с tools/obfuscate_verite.py)
_B64_STANDARD_ALPHABET = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
)
_B64_CUSTOM_ALPHABET = (
    "▒▓░█▀▄▌▐├┤┴┬┼╳╱╲◆◇○●□■△▽※⁑‧ͼΞϗϞЩЪЫЭЮΓΔΘΛΠΣΦΨΩαβγδεζηθλμνξπПР⌬⍟⎊⏣"
)

# Скрытый текстовый «мусорный» файл в assets (подсказки к ⧚…⧛; в терминале: cat ._____fffd.qbf)
RECOVERY_ASSET_FILENAME = "d09efffd.~chunk.dmp"

RECOVERY_PLAINTEXT = f"""# fragment: recovery layer 3 // not for distribution

fso13: прикинь, я щас залез на сервак одного НИИ, стащил дамп страницы. там между ⧚ и ⧛ какие-то куски — не слова, а каша символов
Jenny77: кидай на шару, позыркаем
fso13: смотри: каждый кусок внутри ⧚…⧛ — отдельный токен. если крутить расшифровку, идти надо с конца пайплайна, как они клали слои
Jenny77: то есть последним шагом у них что было первым при кодировании?
fso13: логично. сначала снимаем то, что они навесили последним. у меня по логам порядок такой: в конце это просто utf-8 текст
Jenny77: ок, а до utf-8?
fso13: байты прогнали через xor. восстанавливаешь так: plain[i] = masked[i] xor ((idx*131 + i*17 + (idx*i) mod 251) mod 256). idx — номер блока ⧚…⧛ с начала страницы, с нуля. i — байт внутри блока
Jenny77: idx завязан на позицию токена, поняла. а до xor что лежало?
fso13: base64-строка в байтах, только не ascii латиницей — у них кастомный алфавит под те же 64 позиции
Jenny77: классика. значит каждый символ кастома меняешь на букву из нормального base64 с тем же индексом
fso13: да. и вот этот значок ⌯ — это у них вместо padding =, подмени на = и кормишь обычный b64decode
Jenny77: норм. а до base64 строка как-то ещё ковырялась?
fso13: ага, циклический сдвиг по кругу. n — длина строки внутри ⧚…⧛, r = (idx*11 + n*3) mod n. если n > 1, откат: s = inner[(n-r):] + inner[:(n-r)]
Jenny77: то есть сначала крутишь строку обратно, потом маппинг в стандартный b64, потом decode, потом xor, потом utf-8
fso13: ровно. обратный порядок шагов кодирования
Jenny77: скинь таблицу алфавитов, я сверю скрипт
fso13: держи STD64, 64 символа подряд:
{_B64_STANDARD_ALPHABET}
fso13: и CUSTOM64 — позиция один в один с верхней строкой:
{_B64_CUSTOM_ALPHABET}
Jenny77: принято. не светись, этот лог жги после проверки
fso13: уже
"""

# Встроено в HTML: cat ._____fffd.qbf работает и при file:// (fetch к файлу запрещён)
RECOVERY_PLAINTEXT_B64 = base64.standard_b64encode(
    RECOVERY_PLAINTEXT.encode("utf-8")
).decode("ascii")

# Второй скрытый «файл» в CLI: диалог про студенчество и экраны (cat .___bench~stk.log)
NOSTALGIA_ASSET_FILENAME = "a7f3c2.~dorm.cache"

NOSTALGIA_PLAINTEXT = """# dorm_echo.log // off-record

fso13: помнишь общагу, третий этаж, у окна стоял тот самый ЭЛТ — зелёная фосфорная пыль на стекле?
Jenny77: помню. ты тогда ещё верил, что интернет — это библиотека, а не витрина
fso13: мы жарили лапшу в чайнике и спорили, святой покровитель нужен кабелю или человеку, который кабель держит в зубах
Jenny77: как будто если дать линии имя, она перестанет нести дерьмо. смешно и грустно
fso13: на лекции по сетям препод говорил: пакет не несёт вины. я думал — зато адрес назначения выбираю я
Jenny77: а потом в комнату без стука заходил чужой свет — то сериал, то баннер, то «ещё одна серия». как будто телек был вторым соседом
fso13: мы с тобой ночью вырубали звук и смотрели на сетку на экране — как на звёзды, только это были пиксели и чужие жизни
Jenny77: студенты мы были наивные: думали, что если понять протокол, можно понять и себя
fso13: теперь я знаю: протокол честнее алгоритма ленты. лента кормит тем, что ты уже прожевал
Jenny77: зато на лавке без розетки тише. дерево не шлёт push-уведомлений
fso13: да. небесный патрон на железе — метафора. а выбор, куда смотреть, — всё ещё руками
Jenny77: береги внимание, студент. экзамен не сдан — пока ты весь в стекле
fso13: …как тогда. только стекло теперь в кармане
"""

NOSTALGIA_PLAINTEXT_B64 = base64.standard_b64encode(
    NOSTALGIA_PLAINTEXT.encode("utf-8")
).decode("ascii")


def cli_hidden_links_json(*, from_article_dir: bool) -> str:
    """from_article_dir: True — href как 03-….html; False — articles/03-….html. catFile — vnode в ~."""
    items = [
        {
            "href": (f"{slug}.html" if from_article_dir else f"articles/{slug}.html"),
            "label": label,
            "catFile": cat_file,
        }
        for slug, label, cat_file in _CLI_HIDDEN_ARTICLES
    ]
    return json.dumps(items, ensure_ascii=False)


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


def article_html(
    title: str,
    body_html: str,
    root_prefix: str,
    data_cli_hidden_links_json: str,
    data_cli_recovery_href: str,
    data_cli_recovery_b64: str,
    data_cli_nostalgia_href: str,
    data_cli_nostalgia_b64: str,
) -> str:
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
<body data-cli-hidden-links="{_esc(data_cli_hidden_links_json)}" data-cli-recovery-href="{_esc(data_cli_recovery_href)}" data-cli-recovery-b64="{_esc(data_cli_recovery_b64)}" data-cli-nostalgia-href="{_esc(data_cli_nostalgia_href)}" data-cli-nostalgia-b64="{_esc(data_cli_nostalgia_b64)}">
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
{THEME_FOOT_SCRIPT}  <script src="{root_prefix}assets/cli-easter-egg.js" defer></script>
</body>
</html>
"""


def index_html(
    items: list[tuple[str, str, str]],
    data_cli_hidden_links_json: str,
    data_cli_recovery_href: str,
    data_cli_recovery_b64: str,
    data_cli_nostalgia_href: str,
    data_cli_nostalgia_b64: str,
) -> str:
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
<body data-cli-hidden-links="{_esc(data_cli_hidden_links_json)}" data-cli-recovery-href="{_esc(data_cli_recovery_href)}" data-cli-recovery-b64="{_esc(data_cli_recovery_b64)}" data-cli-nostalgia-href="{_esc(data_cli_nostalgia_href)}" data-cli-nostalgia-b64="{_esc(data_cli_nostalgia_b64)}">
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
{THEME_FOOT_SCRIPT}  <script src="assets/cli-easter-egg.js" defer></script>
</body>
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

    if not CLI_JS_SRC.is_file():
        print(f"Нет cli-easter-egg.js: {CLI_JS_SRC}", file=sys.stderr)
        return 1
    shutil.copy2(CLI_JS_SRC, CLI_JS_DST)

    (ASSETS / RECOVERY_ASSET_FILENAME).write_text(RECOVERY_PLAINTEXT, encoding="utf-8")
    (ASSETS / NOSTALGIA_ASSET_FILENAME).write_text(NOSTALGIA_PLAINTEXT, encoding="utf-8")

    hidden_links_index = cli_hidden_links_json(from_article_dir=False)
    hidden_links_article = cli_hidden_links_json(from_article_dir=True)

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
        recovery_href_article = f"../assets/{RECOVERY_ASSET_FILENAME}"
        nostalgia_href_article = f"../assets/{NOSTALGIA_ASSET_FILENAME}"
        out.write_text(
            article_html(
                title,
                body,
                "../",
                hidden_links_article,
                recovery_href_article,
                RECOVERY_PLAINTEXT_B64,
                nostalgia_href_article,
                NOSTALGIA_PLAINTEXT_B64,
            ),
            encoding="utf-8",
        )
        if slug not in HIDDEN_FROM_INDEX_SLUGS:
            items.append((slug, title, str(path)))

    recovery_href_index = f"assets/{RECOVERY_ASSET_FILENAME}"
    nostalgia_href_index = f"assets/{NOSTALGIA_ASSET_FILENAME}"
    (SITE / "index.html").write_text(
        index_html(
            items,
            hidden_links_index,
            recovery_href_index,
            RECOVERY_PLAINTEXT_B64,
            nostalgia_href_index,
            NOSTALGIA_PLAINTEXT_B64,
        ),
        encoding="utf-8",
    )
    print(
        f"Готово: {len(md_files)} статей в site/, в индексе: {len(items)} "
        f"(скрыты: {HIDDEN_FROM_INDEX_SLUGS}) → {SITE}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
