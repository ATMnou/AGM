#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove the broken PROTOSS_HEAD_TOOL constant and re-add it cleanly."""
p = 'build_pm.py'
lines = open(p, encoding='utf-8').readlines()

# find and remove the broken constant block: from the line containing 'PROTOSS_HEAD_TOOL = ('
# up to (and including) the line containing 'AGM_COMPS = ('
i_start = next(i for i, l in enumerate(lines) if 'PROTOSS_HEAD_TOOL = (' in l)
i_end = next(i for i, l in enumerate(lines) if i > i_start and 'AGM_COMPS = (' in l)

tool_lines = [
    'PROTOSS_HEAD_TOOL = (\n',
    '    "    <tools>' + chr(92) + 'n"\n',
    '    "      <li>' + chr(92) + 'n"\n',
    '    "        <label>head</label>' + chr(92) + 'n"\n',
    '    "        <capacities>' + chr(92) + 'n"\n',
    '    "          <li>Blunt</li>' + chr(92) + 'n"\n',
    '    "        </capacities>' + chr(92) + 'n"\n',
    '    "        <power>10</power>' + chr(92) + 'n"\n',
    '    "        <cooldownTime>2.0</cooldownTime>' + chr(92) + 'n"\n',
    '    "        <linkedBodyPartsGroup>HeadAttackTool</linkedBodyPartsGroup>' + chr(92) + 'n"\n',
    '    "        <ensureLinkedBodyPartsGroupAlwaysUsable>true</ensureLinkedBodyPartsGroupAlwaysUsable>' + chr(92) + 'n"\n',
    '    "      </li>' + chr(92) + 'n"\n',
    '    "    </tools>' + chr(92) + 'n")\n',
    '\n',
]
lines[i_start:i_end + 1] = tool_lines
src = ''.join(lines)
open(p, 'w', encoding='utf-8').write(src)
compile(src, p, 'exec')
print('constant repaired, syntax OK')
