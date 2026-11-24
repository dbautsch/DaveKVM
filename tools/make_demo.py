#!/usr/bin/env python3
# Copyright (c) 2026 Dawid Bautsch
# SPDX-License-Identifier: MIT
"""Create offline demo pages with synthetic frames for documentation screenshots."""

import base64
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def svg_for(kind: str) -> str:
    if kind == 'desktop':
        return '''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720">
<rect width="1280" height="720" fill="#183651"/><circle cx="1030" cy="200" r="260" fill="#22556a"/>
<rect x="0" y="675" width="1280" height="45" fill="#111b2b"/>
<rect x="130" y="100" width="750" height="430" rx="12" fill="#eef3f8"/>
<rect x="130" y="100" width="750" height="50" rx="12" fill="#285074"/>
<text x="160" y="133" font-family="sans-serif" font-size="23" fill="white">Demo workspace</text>
<text x="170" y="245" font-family="sans-serif" font-size="42" fill="#183651">DaveKVM demonstration</text>
<text x="170" y="300" font-family="sans-serif" font-size="25" fill="#526779">Synthetic desktop - no real device data</text>
</svg>'''
    if kind == 'console':
        return '''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720">
<rect width="1280" height="720" fill="#101721"/>
<text x="75" y="110" font-family="monospace" font-size="29" fill="#a8e6cf">Demo Linux console</text>
<text x="75" y="180" font-family="monospace" font-size="25" fill="#e6edf2">system ready</text>
<text x="75" y="225" font-family="monospace" font-size="25" fill="#e6edf2">demo login: operator</text>
<text x="75" y="270" font-family="monospace" font-size="25" fill="#e6edf2">operator@demo:~$ _</text>
<text x="75" y="620" font-family="sans-serif" font-size="22" fill="#8da5bb">Synthetic example - no real device data</text>
</svg>'''
    raise ValueError('unknown demo')


def render_demo(html: str, kind: str) -> str:
    mock = """<script>window.fetch=async function(url){return {ok:true,json:async()=>String(url).includes('devices')?[{id:'video0',name:'Demo HDMI capture',control:true}]:{qsv:false},arrayBuffer:async()=>new ArrayBuffer(0)}};</script>"""
    uri = 'data:image/svg+xml;base64,' + base64.b64encode(svg_for(kind).encode()).decode()
    demo = ("<script>setTimeout(()=>{current='video0';controllableDevices.add('video0');"
            "previewReady=true;video.hidden=true;rawImage.hidden=false;rawImage.src="
            + json.dumps(uri) + ";empty.hidden=true;status.textContent='Demo HDMI capture - video0';"
            "renderControl();const language=document.querySelector('#language');"
            "language.value='en';language.dispatchEvent(new Event('change'));},300);</script>")
    if html.count('<script>') != 1 or html.count('</body>') != 1:
        raise ValueError('unexpected panel structure')
    return html.replace('<script>', mock + '<script>', 1).replace('</body>', demo + '</body>', 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('Usage: make_demo.py EXISTING_OUTPUT_DIRECTORY')
    output = Path(sys.argv[1])
    if not output.is_dir():
        raise ValueError('output directory must already exist')
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    for kind in ('desktop', 'console'):
        (output / f'{kind}.html').write_text(render_demo(html, kind), encoding='utf-8')


if __name__ == '__main__':
    main()
