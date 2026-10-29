#!/usr/bin/env python3
"""Render resolution-independent FormaPanel SVG sources to profile-sized PNG previews.

This command is for design artifacts, not an ESPHome image encoder or firmware build.
"""
import argparse
from io import BytesIO
from pathlib import Path
import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PROFILES = {"480x480": (480, 480), "720x720": (720, 720)}
SOURCES = {
    "aurora-background": ROOT / "assets/source/aurora-background.svg",
    "room-home-preview": ROOT / "ui/mockups/room-home.svg",
}


def render(source: Path, output: Path, width: int, height: int, supersample: int = 2) -> Path:
    if width <= 0 or height <= 0 or not 1 <= supersample <= 4:
        raise ValueError("Invalid output dimensions or supersample")
    if not source.is_file():
        raise FileNotFoundError(source)
    png_data = cairosvg.svg2png(url=str(source), output_width=width * supersample, output_height=height * supersample)
    with Image.open(BytesIO(png_data)) as im:
        im = im.convert('RGB').resize((width, height), Image.Resampling.LANCZOS)
        output.parent.mkdir(parents=True, exist_ok=True)
        im.save(output, format='PNG', optimize=True)
    return output


def render_all() -> list[Path]:
    results = []
    for profile, (w, h) in PROFILES.items():
        for basename, source in SOURCES.items():
            out = ROOT / 'assets' / 'generated' / profile / f'{basename}.png'
            results.append(render(source, out, w, h))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true', help='Render all sources for all profiles')
    parser.add_argument('--profile', choices=PROFILES)
    parser.add_argument('--asset', choices=SOURCES)
    parser.add_argument('--supersample', type=int, default=2, choices=[1,2,3,4])
    args = parser.parse_args()
    if args.all or (args.profile is None and args.asset is None):
        for output in render_all(): print(output.relative_to(ROOT))
        return
    if not args.profile or not args.asset:
        parser.error('Supply both --profile and --asset')
    w, h = PROFILES[args.profile]
    out = ROOT / 'assets' / 'generated' / args.profile / f'{args.asset}.png'
    print(render(SOURCES[args.asset], out, w, h, args.supersample).relative_to(ROOT))

if __name__ == '__main__': main()
