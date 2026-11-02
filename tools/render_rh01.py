#!/usr/bin/env python3
"""Deterministic RH-01 device assets. Requires Pillow; no UI text is baked in.

Run ``python tools/render_rh01.py`` from any directory. The lamp states share
one geometric mask; their only differences are colour, opacity and light.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets/source/backgrounds/golden-sunrise-over-alpine-lake.png"
OUTPUT = ROOT / "assets/generated/480x480"
SCALE = 4
SIZES = {"background": (480, 480), "weather": (64, 54), "wind": (28, 26),
         "lamp-on": (96, 112), "lamp-off": (96, 112)}


def canvas(size):
    return Image.new("RGBA", tuple(v * SCALE for v in size))


def finish(im):
    return im.resize(tuple(v // SCALE for v in im.size), Image.Resampling.LANCZOS)


def ellipse(draw, box, fill):
    draw.ellipse(tuple(round(v * SCALE) for v in box), fill=fill)


def line(draw, points, fill, width=1):
    draw.line([(round(x * SCALE), round(y * SCALE)) for x, y in points],
              fill=fill, width=round(width * SCALE), joint="curve")


def bezier(*points):
    """Sample a cubic into the common lamp/wind path geometry."""
    a, b, c, d = points
    return [tuple((1-t)**3*a[k] + 3*(1-t)**2*t*b[k] +
                  3*(1-t)*t*t*c[k] + t**3*d[k] for k in (0, 1))
            for t in (i / 80 for i in range(81))]


def gaussian_glow(size, center, radii, colour, opacity):
    """Smooth alpha-only falloff, with no rectangular or opaque underlay."""
    out = canvas(size)
    pix = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r2 = ((x/SCALE-center[0])/radii[0])**2 + ((y/SCALE-center[1])/radii[1])**2
            alpha = round(opacity * math.exp(-r2 * 2))
            pix[x, y] = (*colour, alpha if alpha > 1 else 0)
    return out


def weather():
    size = SIZES["weather"]
    im = gaussian_glow(size, (27, 27), (20, 20), (255, 194, 69), 34)
    rays = canvas(size)
    d = ImageDraw.Draw(rays)
    for i in range(12):
        a = i * math.tau / 12
        line(d, [(27 + math.cos(a)*15, 27 + math.sin(a)*15),
                 (27 + math.cos(a)*19, 27 + math.sin(a)*19)], (255, 225, 143, 220), .85)
    im.alpha_composite(rays)
    sun = canvas(size)
    d = ImageDraw.Draw(sun)
    ellipse(d, (14, 14, 40, 40), (255, 220, 116, 255))
    for radius in range(51, 0, -1):
        r = radius/4
        t = radius/51
        colour = (255, round(227-40*t), round(139-73*t), 255)
        ellipse(d, (27-r, 27-r, 27+r, 27+r), colour)
    im.alpha_composite(sun)
    # Unified cloud mask: overlapping soft volumes, shaded in continuous space.
    mask = Image.new("L", im.size)
    d = ImageDraw.Draw(mask)
    for box in [(12,32,34,46),(23,25,44,46),(34,29,52,46),(41,34,56,45)]:
        ellipse(d, box, 255)
    mask = mask.filter(ImageFilter.GaussianBlur(.32*SCALE))
    cloud = canvas(size)
    px, mpx = cloud.load(), mask.load()
    for y in range(cloud.height):
        for x in range(cloud.width):
            if not mpx[x,y]:
                continue
            xx, yy = x/SCALE, y/SCALE
            shade = max(0, min(1, (yy-29)/18))
            # Tiny deterministic surface variation avoids flat vector appearance.
            texture = math.sin(xx*1.5 + yy*.7)*1.3 + math.sin(xx*.55-yy*1.1)*1.2
            v = round(255 - shade*64 + texture)
            px[x,y] = (max(0,min(255,v+2)), max(0,min(255,v+3)), max(0,min(255,v+5)), mpx[x,y])
    shadow = canvas(size)
    sd = ImageDraw.Draw(shadow)
    ellipse(sd, (12,40,56,47), (15, 29, 38, 75))
    shadow = shadow.filter(ImageFilter.GaussianBlur(1.1*SCALE))
    im.alpha_composite(shadow)
    im.alpha_composite(cloud)
    return finish(im)


def wind():
    im = canvas(SIZES["wind"])
    d = ImageDraw.Draw(im)
    colour = (255, 253, 245, 245)
    paths = [
        [(2,9),(18,9)] + bezier((18,9),(27,9),(26,2),(20,2))[1:] + bezier((20,2),(18,2),(18,3),(18,3))[1:],
        [(1,14),(22,14)] + bezier((22,14),(30,14),(28,8),(25,8))[1:],
        [(4,19),(14,19)] + bezier((14,19),(22,19),(20,25),(16,25))[1:] + bezier((16,25),(14,25),(14,24),(14,24))[1:],
    ]
    for path in paths:
        line(d,path,colour,1.6)
    return finish(im)


def lamp_mask():
    """The one source of truth for both states, in 96×112 coordinates."""
    mask = Image.new("L", (96*SCALE,112*SCALE))
    d = ImageDraw.Draw(mask)
    dome = bezier((31,67),(33,57),(38,52),(48,52)) + bezier((48,52),(58,52),(63,57),(65,67))[1:]
    rim = bezier((31,67),(41,65.5),(55,65.5),(65,67)) + bezier((65,67),(56,69),(40,69),(31,67))[1:]
    cap = bezier((44.5,52),(44.5,48),(51.5,48),(51.5,52))
    for path in (dome,rim,cap):
        line(d,path,255,1.2)
    # Wire is alpha graded, fully absent above y=20.
    for y in range(20*SCALE,49*SCALE):
        t=(y/SCALE-20)/29
        d.line([(48*SCALE,y),(48*SCALE,y)],fill=round(210*t*t),width=3)
    return mask


def lamp(on):
    size = SIZES["lamp-on"]
    im = canvas(size)
    mask = lamp_mask()
    if on:
        im.alpha_composite(gaussian_glow(size,(48,73),(28,20),(255,184,61),100))
        im.alpha_composite(gaussian_glow(size,(48,77),(13,13),(255,217,116),60))
        # A gentle interior reflection still leaves the landscape visible.
        inside = canvas(size)
        d = ImageDraw.Draw(inside)
        ellipse(d,(34,55,62,69),(255,207,101,28))
        inside = inside.filter(ImageFilter.GaussianBlur(2*SCALE))
        im.alpha_composite(inside)
        halo = Image.new("RGBA",im.size,(255,193,77,0))
        halo.putalpha(mask.filter(ImageFilter.GaussianBlur(2.2*SCALE)).point(lambda a:round(a*.8)))
        im.alpha_composite(halo)
    stroke = Image.new("RGBA",im.size,(255,238,183,0) if on else (238,238,227,0))
    stroke.putalpha(mask if on else mask.point(lambda a: round(a*.58)))
    im.alpha_composite(stroke)
    return finish(im)


def background():
    """RH-01's soft left/bottom readability grade, never a flattened UI crop.

    The source photo aligns with references/01.jpg. A smooth vignette and
    modest desaturation reproduce its darker foliage without any UI pixels.
    All operations depend only on the clean source photo and coordinates.
    """
    with Image.open(SOURCE) as source:
        im = source.convert("RGB").resize((480,480),Image.Resampling.LANCZOS)
    im = ImageEnhance.Color(im).enhance(.88)
    pixels = im.load()
    for y in range(480):
        yy = y/479
        bottom = .43 * max(0,(y-340)/139)**1.15
        for x in range(480):
            left = 1-x/479
            factor = 1 - .22*left**1.3 - .15*math.sin(math.pi*yy)*left**1.5 - bottom
            pixels[x,y] = tuple(round(c*factor) for c in pixels[x,y])
    return im


def render_all(output=OUTPUT):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    assets = {"background":background(),"weather":weather(),"wind":wind(),
              "lamp-on":lamp(True),"lamp-off":lamp(False)}
    paths=[]
    for name,im in assets.items():
        path = output / f"rh01-{name}.png"
        im.save(path,optimize=True)
        paths.append(path)
    return paths


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=OUTPUT)
    args=parser.parse_args()
    for path in render_all(args.output):
        print(path)


if __name__ == "__main__":
    main()
