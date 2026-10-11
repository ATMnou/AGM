#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compose Hellclown Tricky's TRUE idle animation by rendering the Animate symbol
timeline (SD.S symbol trees -> layers -> frames -> elements with M3D matrices) that
the FNF 'multianimateatlas' format uses. The atlas sprites are PARTS (claw, skull,
body...), so flat extraction was wrong - parts must be composited per timeline frame.

Output: 18 subsampled frames (every 4th of 72) on a fixed canvas, bottom-center.
"""
import json, os, math
from PIL import Image

SRC = r"C:\Users\user\Downloads\TrickyClownedOut\TrickyClownedOut\shared\images\characters\tricky\HClown"
DST = r"D:\SteamLibrary\steamapps\common\RimWorld\Mods\AGM\Textures\Things\Mechanoid\Exaone"
CANVAS = 340
IDLE_FRAMES, STEP = 72, 4

anim = json.load(open(os.path.join(SRC, "Animation.json"), encoding="utf-8-sig"))
symbols = {s["SN"]: s for s in anim["SD"]["S"]}

atlas = {}   # name -> (sheet_idx, x, y, w, h, rotated)
sheets = {}
for idx in (1, 2):
    meta = json.load(open(os.path.join(SRC, "spritemap%d.json" % idx), encoding="utf-8-sig"))
    for s in meta["ATLAS"]["SPRITES"]:
        sp = s["SPRITE"]
        atlas[sp["name"]] = (idx, sp["x"], sp["y"], sp["w"], sp["h"], sp.get("rotated", False))

def sheet(idx):
    if idx not in sheets:
        sheets[idx] = Image.open(os.path.join(SRC, "spritemap%d.png" % idx)).convert("RGBA")
    return sheets[idx]

def m2d(m):
    """M3D row-major 4x4 (row-vector convention) -> 2D affine (a, b, c, d, tx, ty)
    where dest = (a*x + c*y + tx, b*x + d*y + ty)."""
    return (m[0], m[4], m[12], m[1], m[5], m[13])

def mat_mul(A, B):
    """Compose two affine tuples (a,b,tx,c,d,ty): result = A * B (apply B first)."""
    a1, b1, tx1, c1, d1, ty1 = A
    a2, b2, tx2, c2, d2, ty2 = B
    return (a1 * a2 + c1 * b2,
            b1 * a2 + d1 * b2,
            a1 * tx2 + c1 * ty2 + tx1,
            b1 * tx2 + d1 * ty2 + ty1,
            c1 * a2 + d1 * b2 + c1 * 0 + 0,  # placeholder, fixed below
            0)

def compose(A, B):
    a1, b1, tx1, c1, d1, ty1 = A
    a2, b2, tx2, c2, d2, ty2 = B
    return (a1 * a2 + c1 * b2,
            a1 * c2 + c1 * d2,
            a1 * tx2 + c1 * ty2 + tx1,
            b1 * a2 + d1 * b2,
            b1 * c2 + d1 * d2,
            b1 * tx2 + d1 * ty2 + ty1)

IDENTITY = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)

def sprite_image(name):
    idx, x, y, w, h, rot = atlas[name]
    img = sheet(idx).crop((x, y, x + w, y + h))
    if rot:
        img = img.transpose(Image.ROTATE_90)
    return img

def paste_transformed(canvas, img, m):
    """Paste img onto canvas through affine m (source -> dest). Tuple order: (a, b, tx, c, d, ty)."""
    a, b, tx, c, d, ty = m
    # inverse map: dest -> source
    det = a * d - b * c
    if abs(det) < 1e-8:
        return
    ia, ib, ic, id_ = d / det, -c / det, -b / det, a / det
    itx, ity = -(ia * tx + ic * ty), -(ib * tx + id_ * ty)
    w, h = canvas.size
    out = img.transform((w, h), Image.AFFINE, (ia, ib, itx, ic, id_, ity),
                        resample=Image.BICUBIC)
    canvas.alpha_composite(out)

def frame_covering(layers_frames, frame):
    for fr in layers_frames:
        i, du = fr.get("I", 0), fr.get("DU", 1)
        if i <= frame < i + du:
            return fr
    return None

def collect_bounds(name, frame, m, bounds):
    sym = symbols.get(name)
    if sym is None:
        if name in atlas:
            img = sprite_image(name)
            w2, h2 = img.size
            xs = [m[2], m[2] + m[0] * w2 + m[1] * h2, m[2] + m[0] * w2, m[2] + m[1] * h2]
            ys = [m[5], m[5] + m[3] * w2 + m[4] * h2, m[5] + m[3] * w2, m[5] + m[4] * h2]
            bounds.append((min(xs), min(ys), max(xs), max(ys)))
        return
    layer_list = sym["TL"]["L"]
    for L in layer_list:
        fr = frame_covering(L["FR"], frame)
        if not fr:
            continue
        for e in fr.get("E", []):
            if "ASI" in e:
                asi = e["ASI"]
                wm = compose(m, m2d(asi["M3D"]))
                if asi["N"] in atlas:
                    img = sprite_image(asi["N"])
                    w2, h2 = img.size
                    xs = [wm[2], wm[2] + wm[0] * w2 + wm[1] * h2, wm[2] + wm[0] * w2, wm[2] + wm[1] * h2]
                    ys = [wm[5], wm[5] + wm[3] * w2 + wm[4] * h2, wm[5] + wm[3] * w2, wm[5] + wm[4] * h2]
                    bounds.append((min(xs), min(ys), max(xs), max(ys)))
            elif "SI" in e:
                si = e["SI"]
                wm = compose(m, m2d(si["M3D"]))
                collect_bounds(si["SN"], si.get("FF", 0), wm, bounds)

def render_symbol(name, frame, m, canvas):
    sym = symbols.get(name)
    if sym is None:
        if name in atlas:
            paste_transformed(canvas, sprite_image(name), m)
        return
    for L in sym["TL"]["L"]:
        fr = frame_covering(L["FR"], frame)
        if not fr:
            continue
        for e in fr.get("E", []):
            if "ASI" in e:
                asi = e["ASI"]
                paste_transformed(canvas, sprite_image(asi["N"]), compose(m, m2d(asi["M3D"])))
            elif "SI" in e:
                si = e["SI"]
                render_symbol(si["SN"], si.get("FF", 0), compose(m, m2d(si["M3D"])), canvas)

ROOT = "HC Idle FULLBODY"
# measure union bounds across the loop (with the root translation applied as-is)
bounds = []
root_m = m2d([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 219.5, 374.65, 0, 1])
for t in range(0, IDLE_FRAMES, STEP):
    collect_bounds(ROOT, t, root_m, bounds)
min_x = min(b[0] for b in bounds); min_y = min(b[1] for b in bounds)
max_x = max(b[2] for b in bounds); max_y = max(b[3] for b in bounds)
print("union bounds:", round(min_x), round(min_y), round(max_x), round(max_y),
      "size:", round(max_x - min_x), "x", round(max_y - min_y))

uw, uh = max_x - min_x, max_y - min_y
scale = min(1.0, (CANVAS * 0.94) / uw, (CANVAS * 0.94) / uh)
print("scale:", round(scale, 4))

os.makedirs(DST, exist_ok=True)
n = 0
for t in range(0, IDLE_FRAMES, STEP):
    canvas = Image.new("RGBA", (int(uw), int(uh)), (0, 0, 0, 0))
    render_symbol(ROOT, t, root_m, canvas)
    # shift so the union origin is at (0,0): baked in via translate before scale
    shifted = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shifted.alpha_composite(canvas, (0, 0))
    w2 = max(1, round(uw * scale)); h2 = max(1, round(uh * scale))
    out = shifted.resize((w2, h2), Image.LANCZOS)
    frame_canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    frame_canvas.paste(out, ((CANVAS - w2) // 2, CANVAS - h2), out)
    frame_canvas.save(os.path.join(DST, "Exaone_f%02d.png" % n))
    n += 1
print("saved", n, "composed frames")
