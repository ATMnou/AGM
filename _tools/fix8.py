#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repair the broken injected block in build_pm.py and add Protoss abstract inheritance
(thinkTreeMain / intelligence / head tool / stats) for Argon and Flash."""
import re

p = 'build_pm.py'
src = open(p, encoding='utf-8').read()

# 1. remove any broken injected block (from the race-sub line up to before '    k = kind')
broken = re.search(r'    t = re\.sub\(r"\(<race>.*?"    k = kind', src, re.S)
if broken:
    src = src.replace(broken.group(0), '    k = kind')
    print('broken block removed')

# 2. also drop the leftover comps-sub line duplication if present
src = src.replace(
    '    t = re.sub(r"(<comps>\\n)", r"\\1" + AGM_COMPS, t, count=1)\n\n    k = kind',
    '    t = re.sub(r"(<comps>\\n)", r"\\1" + AGM_COMPS, t, count=1)\n'
    '    t = re.sub(r"(<race>\\n)", r"\\1      <intelligence>ToolUser</intelligence>\\n'
    '      <thinkTreeMain>Mechanoid</thinkTreeMain>\\n", t, count=1)\n'
    '    t = re.sub(r"(<statBases>\\n)", r"\\1      <PsychicSensitivity>0</PsychicSensitivity>\\n'
    '      <ControlTakingTime>30</ControlTakingTime>\\n      <WorkSpeedGlobal>1.0</WorkSpeedGlobal>\\n'
    '      <MarketValue>1000</MarketValue>\\n", t, count=1)\n'
    '    if "<tools>" not in t:\\n'
    '        t = t.replace("<comps>", PROTOSS_HEAD_TOOL + "    <comps>", 1)\\n'
    '\\n    k = kind')

# 3. head-tool constant (idempotent)
if 'PROTOSS_HEAD_TOOL' not in src:
    src = src.replace('AGM_COMPS = (', 'PROTOSS_HEAD_TOOL = (\n'
        '    "    <tools>\\n"\n'
        '    "      <li>\\n"\n'
        '    "        <label>head</label>\\n"\n'
        '    "        <capacities>\\n"\n'
        '    "          <li>Blunt</li>\\n"\n'
        '    "        </capacities>\\n"\n'
        '    "        <power>10</power>\\n"\n'
        '    "        <cooldownTime>2.0</cooldownTime>\\n"\n'
        '    "        <linkedBodyPartsGroup>HeadAttackTool</linkedBodyPartsGroup>\\n"\n'
        '    "        <ensureLinkedBodyPartsGroupAlwaysUsable>true</ensureLinkedBodyPartsGroupAlwaysUsable>\\n"\n'
        '    "      </li>\\n"\n'
        '    "    </tools>\\n")\n\n'
        'AGM_COMPS = (', 1)

open(p, 'w', encoding='utf-8').write(src)
print('build_pm repaired')

# sanity: compile check
compile(src, p, 'exec')
print('syntax OK')
