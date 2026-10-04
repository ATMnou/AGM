#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync assets referenced by AGM defs: copy textures/sounds from the source mods
(Total Warfare, Kraltech, Protoss, MFE) into AGM when not present yet."""
import os, re, shutil, glob

AGM = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SOURCES = [
    r"D:\SteamLibrary\steamapps\workshop\content\294100\3555799437\1.6",  # Total Warfare
    r"D:\SteamLibrary\steamapps\workshop\content\294100\3555799437",       # Total Warfare root
    r"D:\SteamLibrary\steamapps\workshop\content\294100\3625664332",       # Kraltech
    r"D:\SteamLibrary\steamapps\workshop\content\294100\3464281098\1.6",   # ProtossMechPurifier
    r"D:\SteamLibrary\steamapps\workshop\content\294100\3464281098",       # Purifier root (textures)
    r"D:\SteamLibrary\steamapps\workshop\content\294100\3522838904\1.6",   # ProtossMechPersonaHero
    r"D:\SteamLibrary\steamapps\workshop\content\294100\3522838904",       # Persona root (textures)
    r"D:\SteamLibrary\steamapps\common\RimWorld\Mods\MFE",
]

IMG_EXT = (".png", ".jpg", ".jpeg", ".wav", ".mp3", ".ogg")

def asset_exists(path_noext):
    """True if <path>.* (with _east/_north/_south variants or subfolder) exists."""
    if os.path.isdir(path_noext):
        return True
    for pat in (path_noext + ".*", path_noext + "_*.*", path_noext + "/*.*", path_noext + "_*/*.*"):
        for h in glob.glob(pat):
            if os.path.isdir(path_noext) or os.path.splitext(h)[1].lower() in IMG_EXT:
                return True
    return False

def copy_asset(src_path_noext, dst_path_noext):
    """Copy ref.ext, ref_east/_north/_south/_default.ext or the whole folder."""
    copied_any = False
    if os.path.isdir(src_path_noext):
        dst = dst_path_noext
        if not os.path.isdir(dst):
            shutil.copytree(src_path_noext, dst, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("*.dds", "*.meta"))
            copied_any = True
        return copied_any
    for suffix in ("", "_east", "_north", "_south", "_default", "_menu"):
        for h in glob.glob(src_path_noext + suffix + ".*"):
            ext = os.path.splitext(h)[1].lower()
            if ext not in IMG_EXT:
                continue
            dst = dst_path_noext + suffix + ext
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(h, dst)
            copied_any = True
    return copied_any

def def_files():
    out = []
    for pat in ("Defs/**/*.xml", "Compat/**/Defs/**/*.xml"):
        out += glob.glob(os.path.join(AGM, pat), recursive=True)
    return out

refs = set()
for f in def_files():
    txt = open(f, encoding="utf-8-sig").read()
    for m in re.finditer(r"<(?:texPath|iconPath|uiIconPath|maskPath|clipFolderPath|clipPath)>([^<]+)<", txt):
        v = m.group(1).strip().strip("/")
        if v:
            refs.add(v)

copied, missing = [], []
for ref in sorted(refs):
    rel = ref.replace("/", os.sep)
    if asset_exists(os.path.join(AGM, "Textures", rel)) or asset_exists(os.path.join(AGM, "Sounds", rel)):
        continue
    found = False
    for base in ("Textures", "Sounds"):
        for src in SOURCES:
            srcp = os.path.join(src, base, rel)
            if os.path.isdir(srcp) or glob.glob(srcp + ".*") or glob.glob(srcp + "_*.*"):
                if copy_asset(srcp, os.path.join(AGM, base, rel)):
                    copied.append((base, ref))
                    found = True
                    break
        if found:
            break
    if not found:
        missing.append(ref)

print("COPIED:")
for kind, ref in copied:
    print("  [%s] %s" % (kind, ref))
print("\nMISSING (%d):" % len(missing))
for ref in missing:
    print("  " + ref)
