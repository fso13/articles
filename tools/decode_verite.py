#!/usr/bin/env python3
"""Восстанавливает plaintext из обфусцированного .md с ⧚…⧛ (03, 06 и т.д.; stdin или путь к файлу)."""

from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

CUSTOM64 = (
    "▒▓░█▀▄▌▐├┤┴┬┼╳╱╲◆◇○●□■△▽※⁑‧ͼΞϗϞЩЪЫЭЮΓΔΘΛΠΣΦΨΩαβγδεζηθλμνξπПР⌬⍟⎊⏣"
)
STANDARD64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_B64_PAD = "⌯"
_C_TO_STD = {c: s for s, c in zip(STANDARD64, CUSTOM64)}


def _xor_stream(data: bytes, blob_idx: int) -> bytes:
    return bytes(
        b ^ ((blob_idx * 131 + i * 17 + (blob_idx * i) % 251) & 0xFF)
        for i, b in enumerate(data)
    )


def _unrotate_custom(s: str, blob_idx: int) -> str:
    n = len(s)
    if n <= 1:
        return s
    r = (blob_idx * 11 + n * 3) % n
    return s[n - r :] + s[: n - r]


def decode_blob(inner: str, blob_idx: int) -> str:
    inner = _unrotate_custom(inner, blob_idx)
    inner = inner.replace(_B64_PAD, "=")
    b64 = "".join(_C_TO_STD.get(ch, ch) for ch in inner)
    masked = base64.b64decode(b64)
    plain = _xor_stream(masked, blob_idx)
    return plain.decode("utf-8")


def decode_text(s: str) -> str:
    idx = 0
    out: list[str] = []
    pos = 0
    for m in re.finditer(r"⧚([^⧛]+)⧛", s):
        out.append(s[pos : m.start()])
        out.append(decode_blob(m.group(1), idx))
        idx += 1
        pos = m.end()
    out.append(s[pos:])
    return "".join(out)


def main() -> None:
    if len(sys.argv) > 1:
        raw = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    # убрать HTML-комментарий в конце
    raw = re.sub(r"<!--.*?-->\s*\Z", "", raw, flags=re.DOTALL)
    sys.stdout.write(decode_text(raw))


if __name__ == "__main__":
    main()
