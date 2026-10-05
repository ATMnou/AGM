#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix14: the damage-def parent inliner used a flat regex to collect the child's existing
tags, so a NESTED <hediff> (inside <additionalHediffs>) made it skip the parent's top-level
<hediff>Gunshot</hediff>. Result: AGM_Damage_ArmorBreakerBullet & friends have hediff=null,
and HealthUtility.GetHediffDefFromDamage returns null -> HediffMaker NRE on every hit.
Make child_tags top-level-only via ElementTree."""
import re

p = 'build_kral.py'
src = open(p, encoding='utf-8').read()

old = '''def _inline_damage(m):
    pname, inner = m.group(1), m.group(2)
    if pname not in _dmg_parents:
        return m.group(0)
    pin = _dmg_parents[pname]
    child_tags = set(_re.findall(r"<(\\w+)[^>]*>", inner))'''
new = '''def _inline_damage(m):
    pname, inner = m.group(1), m.group(2)
    if pname not in _dmg_parents:
        return m.group(0)
    pin = _dmg_parents[pname]
    # top-level child tags only - a nested <hediff> inside <additionalHediffs> must not
    # count as "already present" or the parent's <hediff> would be skipped (null hediff
    # -> HediffMaker NRE on impact).
    try:
        import xml.etree.ElementTree as _ET
        child_tags = set(ch.tag for ch in _ET.fromstring("<Root>" + inner + "</Root>"))
    except Exception:
        child_tags = set(_re.findall(r"<(\\w+)[^>]*>", inner))'''
assert old in src, 'inline_damage block'
src = src.replace(old, new)

open(p, 'w', encoding='utf-8').write(src)
compile(src, p, 'exec')
print('fix14 applied, syntax OK')
