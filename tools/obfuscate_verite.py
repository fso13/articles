#!/usr/bin/env python3
"""Генерирует 03-verite-v-boga.md: заголовок как есть, текст — base64 в CUSTOM64 + редкие читаемые фрагменты."""

from __future__ import annotations

import base64
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "ignore" / "03-verite-v-boga.md"
DST = ROOT / "03-verite-v-boga.md"

# Ровно 64 уникальных символа ↔ стандартный base64
CUSTOM64 = (
    "▒▓░█▀▄▌▐├┤┴┬┼╳╱╲◆◇○●□■△▽※⁑‧ͼΞϗϞЩЪЫЭЮΓΔΘΛΠΣΦΨΩαβγδεζηθλμνξπПР⌬⍟⎊⏣"
)
STANDARD64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
assert len(CUSTOM64) == 64 and len(set(CUSTOM64)) == 64

_TO_C = str.maketrans(STANDARD64, CUSTOM64)
# padding base64 «=» не в алфавите — заменяем на один символ для декодера
_B64_PAD = "⌯"


def _xor_stream(data: bytes, blob_idx: int) -> bytes:
    """Второй слой: XOR по позиции и номеру блока (самообратим)."""
    return bytes(
        b ^ ((blob_idx * 131 + i * 17 + (blob_idx * i) % 251) & 0xFF)
        for i, b in enumerate(data)
    )


def _rotate_custom(s: str, blob_idx: int) -> str:
    """Третий слой: циклический сдвиг строки после CUSTOM64 (обратим по idx и len)."""
    n = len(s)
    if n <= 1:
        return s
    r = (blob_idx * 11 + n * 3) % n
    return s[r:] + s[:r]


def obfuscate_token(token: str, blob_idx: int) -> str:
    """UTF-8 → XOR → base64 → CUSTOM64 → сдвиг → ⧚…⧛"""
    if not token:
        return token
    masked = _xor_stream(token.encode("utf-8"), blob_idx)
    raw = base64.b64encode(masked).decode("ascii")
    raw = raw.replace("=", _B64_PAD)
    b64 = raw.translate(_TO_C)
    b64 = _rotate_custom(b64, blob_idx)
    return f"⧚{b64}⧛"


def visible_mask(n_words: int, pid: int) -> list[bool]:
    rng = random.Random(pid * 1_000_003 + 17)
    vis = [False] * n_words
    if n_words <= 2:
        vis[:] = [True] * n_words
        return vis
    runs = 2 if n_words > 18 else 1
    for _ in range(runs):
        start = rng.randrange(0, n_words)
        ln = rng.randint(2, min(7, n_words))
        if n_words > 10 and rng.random() < 0.35:
            start = 0
        if n_words > 14 and rng.random() < 0.25:
            start = max(0, n_words // 2 - ln // 2)
        for i in range(start, min(start + ln, n_words)):
            vis[i] = True
    if not any(vis):
        a, b = 0, min(4, n_words)
        for i in range(a, b):
            vis[i] = True
    return vis


def obfuscate_paragraph(para: str, pid: int, blob_counter: list[int]) -> str:
    words = para.split()
    if not words:
        return para
    mask = visible_mask(len(words), pid)
    parts: list[str] = []
    for i, w in enumerate(words):
        if mask[i]:
            parts.append(w)
        else:
            parts.append(obfuscate_token(w, blob_counter[0]))
            blob_counter[0] += 1
    return " ".join(parts)


def main() -> None:
    raw = SRC.read_text(encoding="utf-8")
    lines = raw.splitlines()
    if not lines or not lines[0].startswith("#"):
        raise SystemExit("Ожидается заголовок # в первой строке")
    title = lines[0]
    body = "\n".join(lines[1:]).strip()
    paras = re.split(r"\n\s*\n", body)
    blob_counter = [0]
    out_paras = [
        obfuscate_paragraph(p.strip(), i, blob_counter)
        for i, p in enumerate(paras)
        if p.strip()
    ]

    note = (
        "\n\n<!-- Декодирование ⧚…⧛: idx=0,1,2… по файлу. "
        "1) сдвиг r=(idx*11+len*3)%len → s=s[(len-r):]+s[:(len-r)] при len>1. "
        "2) кастомный алфавит → base64 (cat ._____fffd.qbf в CLI после 13 кликов по теме); ⌯→=. "
        "3) base64→bytes. 4) XOR b[i]^((idx*131+i*17+(idx*i)%251)&255). 5) UTF-8. "
        f'STD64="{STANDARD64}" CUSTOM64="{CUSTOM64}" -->\n'
    )

    DST.write_text(
        title + "\n\n" + "\n\n".join(out_paras) + note,
        encoding="utf-8",
    )
    print(f"Записано: {DST}")


if __name__ == "__main__":
    main()
