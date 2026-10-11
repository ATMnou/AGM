#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge KR-sourced translations into CN-S and JP DefInjected files (KR key order,
missing keys appended, stale keys dropped), then regenerate CN-T wholesale, and prune
stale Keyed entries not present in KR."""
import xml.etree.ElementTree as ET
import os, re, ctypes, glob, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
AGM = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# read KR structure: list of (relpath, [(key, value)...]) in file order
kr_files = []  # (relpath, [(key, val)])
for d in sorted(os.listdir(os.path.join(AGM, "Languages", "Korean", "DefInjected"))):
    for f in sorted(glob.glob(os.path.join(AGM, "Languages", "Korean", "DefInjected", d, "*.xml"))):
        root = ET.parse(f).getroot()
        entries = [(el.tag, (el.text or "")) for el in root]
        kr_files.append((d + "/" + os.path.basename(f), entries))

kr_keyed = [(el.tag, (el.text or "")) for el in
            ET.parse(os.path.join(AGM, "Languages", "Korean", "Keyed", "AGM.xml")).getroot()]

import _loc_cn_part1, _loc_cn_part2
import _loc_jp_part1, _loc_jp_part2
CN = dict(_loc_cn_part1.DATA)
CN.update(_loc_cn_part2.DATA)
JP = dict(_loc_jp_part1.DATA)
JP.update(_loc_jp_part2.DATA)

def build_file(header_comment, entries):
    lines = ['<?xml version="1.0" encoding="utf-8"?>', '<LanguageData>', '']
    for k, v in entries:
        v = v.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        lines.append('  <%s>%s</%s>' % (k, v, k))
    lines.append('')
    lines.append('</LanguageData>')
    return "\n".join(lines) + "\n"

def write_definjected(lang, relpath, entries):
    p = os.path.join(AGM, "Languages", lang, "DefInjected", relpath.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(build_file(None, entries))

def apply_lang(lang, DATA):
    total_added = 0
    for relpath, kr_entries in kr_files:
        trans = dict(DATA.get(relpath, []))
        entries = [(k, trans[k]) for k, _ in kr_entries if k in trans]
        write_definjected(lang, relpath, entries)
        total_added += len(entries)
    # keyed: keep only keys present in KR keyed, translated value not needed (KR keyed is
    # Korean text) - for CN/JP keep their existing translations for shared keys, drop stale
    kp = os.path.join(AGM, "Languages", lang, "Keyed", "AGM.xml")
    existing = {}
    root = ET.parse(kp).getroot()
    for el in root:
        existing[el.tag] = el.text or ""
    kr_keys = set(k for k, _ in kr_keyed)
    kept = [(k, v) for k, v in existing.items() if k in kr_keys]
    # KR-only keyed strings fall back to English value from the KR file? No - keep KR missing ones out;
    # but Doomsday/ExoPhase strings were authored in EN earlier and KR has them translated - copy EN fallback
    kr_val = dict(kr_keyed)
    for k, _ in kr_keyed:
        if k not in kept and k not in existing:
            pass  # skip, will remain untranslated (English def fallback)
    lines = ['<?xml version="1.0" encoding="utf-8"?>', '<LanguageData>', '']
    for k, v in kept:
        v = v.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        lines.append('  <%s>%s</%s>' % (k, v, k))
    lines.append('')
    lines.append('</LanguageData>')
    open(kp, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return total_added

for lang, DATA in (("ChineseSimplified", CN), ("Japanese", JP)):
    n = apply_lang(lang, DATA)
    print(lang, "entries written:", n)

# ---- regenerate CN-T from CN-S (all DefInjected + Keyed) ----
k32 = ctypes.windll.kernel32
def s2t(text):
    b = ctypes.create_unicode_buffer(text)
    size = k32.LCMapStringW(0x0804, 0x04000000, b, -1, None, 0)
    outb = ctypes.create_unicode_buffer(size)
    k32.LCMapStringW(0x0804, 0x04000000, b, -1, outb, size)
    return outb.value

count = 0
for f in glob.glob(os.path.join(AGM, "Languages", "ChineseSimplified", "**", "*.xml"), recursive=True):
    rel = os.path.relpath(f, os.path.join(AGM, "Languages", "ChineseSimplified"))
    t = os.path.join(AGM, "Languages", "ChineseTraditional", rel)
    os.makedirs(os.path.dirname(t), exist_ok=True)
    open(t, "w", encoding="utf-8").write(s2t(open(f, encoding="utf-8").read()))
    count += 1
print("CN-T regenerated:", count, "files")
