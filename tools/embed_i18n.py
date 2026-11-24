#!/usr/bin/env python3
# Copyright (c) 2026 Dawid Bautsch
# SPDX-License-Identifier: MIT
"""Embed the shared translator into a standalone DaveKVM panel HTML file."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BEGIN = '// BEGIN DAVEKVM I18N\n'
END = '\n// END DAVEKVM I18N\n'
SELECTOR = ('<label class="language-picker">Language / Język '
            '<select id="language" aria-label="Language / Język">'
            '<option value="pl">Polski</option><option value="en">English</option>'
            '<option value="de">Deutsch</option><option value="cs">Čeština</option>'
            '</select></label>')


def embed(text: str, source: str) -> str:
    if BEGIN in text:
        if text.count(BEGIN) != 1 or text.count(END) != 1:
            raise ValueError('invalid existing translation markers')
        start = text.index(BEGIN)
        stop = text.index(END, start) + len(END)
        text = text[:start] + text[stop:]
    if 'id="language"' not in text:
        if text.count('</header>') != 1:
            raise ValueError('expected exactly one header')
        text = text.replace('</header>', SELECTOR + '</header>', 1)
    if text.count('<script>') != 1:
        raise ValueError('expected one inline panel script')
    return text.replace('<script>', '<script>\n' + BEGIN + source.rstrip() + END, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('Usage: embed_i18n.py PANEL.html')
    target = Path(sys.argv[1])
    result = embed(target.read_text(encoding='utf-8'), (ROOT / 'i18n.js').read_text(encoding='utf-8'))
    target.write_text(result, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
