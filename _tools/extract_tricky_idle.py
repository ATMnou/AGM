#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract Hellclown Tricky's idle animation (frames 0000-0071) from the FNF
Animate-style atlas into RimWorld frame textures.

- idle frames live in spritemap1.png / spritemap2.png, regions in the matching .json
  (Starling ATLAS format; "rotated" = stored rotated 90 degrees CW -> restore CCW).
- Every 4th frame is kept (18 frames), each cropped to content and composited on a
  fixed square canvas anchored bottom-center so the bob survives and nothing jitters.
- Output: Textures/Things/Mechanoid/Exaone/Exaone_f00.png ... _f17.png
"""
import json, os, re
from PIL import Image

SRC = r"C:\Users\user\Downloads\TrickyClownedOut\TrickyClownedOut\shared\images\characters\tricky\HClown"
DST = r"D:\SteamLibrary\steamapps\common\RimWorld\Mods\AGM\Textures\Things\Mechanoid\Exaone"
IDLE_START, IDLE_COUNT, STEP = 0, 72, 4
CANVAS = 320

atlas = {}  # name -> (png_index, x, y, w, h, rotated)
sheets = {}
for idx in (1, 2):
    meta = json.load(open(os.path.join(SRC, "spritemap%d.json" % idx), encoding="utf-8-sig"))
    sprites = meta["ATLAS"]["SPRITES"]
    for s in sprites:
        sp = s["SPRITE"]
        atlas[sp["name"]] = (idx, sp["x"], sp["y"], sp["w"], sp["h"], sp.get("rotated", False))
    # lazy-load sheets
    sheets[idx] = None

def sheet(idx):
    if sheets[idx] is None:
        sheets[idx] = Image.open(os.path.join(SRC, "spritemap%d.png" % idx)).convert("RGBA")
    return sheets[idx]

def frame(i):
    name = "%04d" % i
    entry = atlas.get(name)
    if entry is None:
        return None
    idx, x, y, w, h, rot = entry
    img = sheet(idx).crop((x, y, x + w, y + h))
    if rot:
        img = img.transpose(Image.ROTATE_90)  # undo the 90-deg CW pack rotation
    return img

# extract idle frames, measure union size
imgs = []
for i in range(IDLE_START, IDLE_START + IDLE_COUNT, STEP):
    img = frame(i)
    if img is None:
        print("MISSING FRAME", i)
        continue
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    imgs.append((i, img))

max_w = max(im.width for _, im in imgs)
max_h = max(im.height for _, im in imgs)
print("frames kept:", len(imgs), "union size:", max_w, "x", max_h)

# scale so the tallest frame fits the canvas height
scale = min(1.0, (CANVAS * 0.92) / max_h, (CANVAS * 0.92) / max_w)
os.makedirs(DST, exist_ok=True)
for n, (i, im) in enumerate(imgs):
    if scale < 1.0:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(im, ((CANVAS - im.width) // 2, CANVAS - im.height), im)
    out = os.path.join(DST, "Exaone_f%02d.png" % n)
    canvas.save(out)
print("saved", len(imgs), "frames to", DST)
