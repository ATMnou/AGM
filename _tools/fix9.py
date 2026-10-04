#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Line-based repair of the two broken re.sub calls in build_pm.py."""
p = 'build_pm.py'
lines = open(p, encoding='utf-8').readlines()

i_race = next(i for i, l in enumerate(lines) if '(<race>' in l and 're.sub' in l)
i_mv = next(i for i, l in enumerate(lines) if '<MarketValue>1000' in l)
i_end = i_mv + 1  # the closing '", t, count=1)' line
assert '", t, count=1)' in lines[i_end], lines[i_end]

clean = [
    '    t = re.sub(r"(<race>\\n)", r"\\1      <intelligence>ToolUser</intelligence>\\n      <thinkTreeMain>Mechanoid</thinkTreeMain>\\n", t, count=1)\n',
    '    t = re.sub(r"(<statBases>\\n)", r"\\1      <PsychicSensitivity>0</PsychicSensitivity>\\n      <ControlTakingTime>30</ControlTakingTime>\\n      <WorkSpeedGlobal>1.0</WorkSpeedGlobal>\\n      <MarketValue>1000</MarketValue>\\n", t, count=1)\n',
]
lines[i_race:i_end + 1] = clean
src = ''.join(lines)

if 'PROTOSS_HEAD_TOOL' not in src:
    tool = (
        'PROTOSS_HEAD_TOOL = (\n'
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
        '    "    </tools>\\n")\n\n')
    src = src.replace('AGM_COMPS = (', tool + 'AGM_COMPS = (', 1)

open(p, 'w', encoding='utf-8').write(src)
compile(src, p, 'exec')
print('build_pm repaired, syntax OK')
