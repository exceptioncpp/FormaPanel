"""Render project SVG icons with Chrome, without external Python packages.

Examples:
    python tools/render_functional_icons.py
    python tools/render_functional_icons.py --only radiator-on radiator-off
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import zlib

ROOT = Path(__file__).resolve().parent.parent
CHROME = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Google/Chrome/Application/chrome.exe"
SOURCE = ROOT / "assets/source/icons"
OUTPUT = ROOT / "assets/generated/480x480/functional"


def crop_png(data: bytes, width: int, height: int) -> bytes:
    """Crop Chrome's RGBA PNG using stdlib; small Chrome windows clip SVG art."""
    chunks = []
    pos = 8
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        chunks.append((kind, payload))
        pos += length + 12
    header = next(payload for kind, payload in chunks if kind == b"IHDR")
    source_width, source_height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", header)
    if depth != 8 or color not in (2, 6) or interlace or width > source_width or height > source_height:
        raise ValueError("Unsupported Chrome screenshot PNG")
    channels = 4 if color == 6 else 3
    stride = source_width * channels
    raw = zlib.decompress(b"".join(payload for kind, payload in chunks if kind == b"IDAT"))
    previous = bytearray(stride)
    cropped = bytearray()
    for y in range(height):
        offset = y * (stride + 1)
        mode = raw[offset]
        row = bytearray(raw[offset + 1:offset + 1 + stride])
        for x in range(stride):
            left = row[x - channels] if x >= channels else 0
            above = previous[x]
            upper_left = previous[x - channels] if x >= channels else 0
            if mode == 1:
                row[x] = (row[x] + left) & 255
            elif mode == 2:
                row[x] = (row[x] + above) & 255
            elif mode == 3:
                row[x] = (row[x] + (left + above) // 2) & 255
            elif mode == 4:
                estimate = left + above - upper_left
                distances = [abs(estimate - left), abs(estimate - above), abs(estimate - upper_left)]
                predictor = [left, above, upper_left][distances.index(min(distances))]
                row[x] = (row[x] + predictor) & 255
            elif mode != 0:
                raise ValueError("Unsupported PNG filter")
        cropped.extend(b"\0" + row[:width * channels])
        previous = row
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, depth, color, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(cropped, 9)) + chunk(b"IEND", b""))


def render(source: Path, profile: Path) -> None:
    svg = source.read_text(encoding="utf-8")
    size = re.search(r'width="(\d+)" height="(\d+)"', svg)
    if size is None:
        raise ValueError(f"{source.name}: SVG requires integer width and height")
    width, height = map(int, size.groups())
    output = OUTPUT / (source.stem + ".png")
    screenshot = profile / (source.stem + ".png")
    result = subprocess.run(
        [str(CHROME), "--headless", "--disable-gpu", "--no-sandbox", "--no-first-run",
         "--no-default-browser-check", f"--user-data-dir={profile}",
         "--hide-scrollbars", "--force-device-scale-factor=1",
         "--run-all-compositor-stages-before-draw", "--virtual-time-budget=1000",
         "--default-background-color=00000000", f"--window-size={max(500,width)},{max(500,height)}",
         f"--screenshot={screenshot}", source.as_uri()],
        capture_output=True, text=True, timeout=45,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode:
        raise RuntimeError(f"Chrome failed for {source.name}: {result.stderr[-1500:]}")
    output.write_bytes(crop_png(screenshot.read_bytes(), width, height))
    png = output.read_bytes()
    if png[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", png[16:24]) != (width, height):
        raise RuntimeError(f"Wrong PNG dimensions for {output.name}")
    print(f"{output.name}: {width}x{height}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", help="SVG stem suffixes, e.g. radiator-on")
    args = parser.parse_args()
    if not CHROME.is_file():
        raise FileNotFoundError(f"Chrome not found: {CHROME}")
    sources = sorted(SOURCE.glob("functional-*.svg"))
    if args.only:
        wanted = {f"functional-{name.removesuffix('.svg').removeprefix('functional-')}" for name in args.only}
        sources = [source for source in sources if source.stem in wanted]
        missing = wanted - {source.stem for source in sources}
        if missing:
            raise FileNotFoundError(f"Unknown icons: {', '.join(sorted(missing))}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    # A disposable profile keeps the user's running Chrome session independent.
    with tempfile.TemporaryDirectory(prefix="formapanel-icons-", dir=ROOT / "local", ignore_cleanup_errors=True) as profile:
        for source in sources:
            render(source, Path(profile))


if __name__ == "__main__":
    main()
