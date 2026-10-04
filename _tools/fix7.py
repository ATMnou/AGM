#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

p = 'build_pm.py'
src = open(p, encoding='utf-8').read()

# 1. rename the thermal lance gun's own weapon tag (kind references AGM_ThermalLances)
old1 = 'thermal = thermal.replace("<verbClass>ProtossMech.Verb_ShootMeltBeam</verbClass>", "<verbClass>Verb_ShootBeam</verbClass>")'
new1 = old1 + '\nthermal = thermal.replace("<li>ThermalLances</li>", "<li>AGM_ThermalLances</li>")'
assert old1 in src, "thermal verb line"
src = src.replace(old1, new1)

# 2. remove the wrong fallback that stuffed the tag into the first <weaponClasses> (FlashPulse)
old2 = '''if "<li>AGM_ThermalLances</li>" not in thermal:
    thermal = thermal.replace("<weaponClasses>", "<weaponTags>\\n      <li>AGM_ThermalLances</li>\\n    </weaponTags>\\n    <weaponClasses>", 1)
'''
if old2 in src:
    src = src.replace(old2, '')
    print('fallback removed')
else:
    # try variant with single backslash-n written literally
    old2b = 'if "<li>AGM_ThermalLances</li>" not in thermal:\n    thermal = thermal.replace("<weaponClasses>", "<weaponTags>\\n      <li>AGM_ThermalLances</li>\\n    </weaponTags>\\n    <weaponClasses>", 1)\n'
    assert old2b in src, "fallback not found"
    src = src.replace(old2b, '')
    print('fallback removed (variant)')

# 3. Protoss abstract inheritance for Argon/Flash
old3 = '''    t = re.sub(r"(<comps>\\n)", r"\\1" + AGM_COMPS, t, count=1)
    return t, k'''
new3 = '''    t = re.sub(r"(<comps>\\n)", r"\\1" + AGM_COMPS, t, count=1)
    # fields the ProtossMechanoid abstract used to provide (lost when re-parenting to BaseMechanoid)
    t = re.sub(r"(<race>\\n)", r"\\1      <intelligence>ToolUser</intelligence>\\n      <thinkTreeMain>Mechanoid</thinkTreeMain>\\n", t, count=1)
    t = re.sub(r"(<statBases>\\n)", r"\\1      <PsychicSensitivity>0</PsychicSensitivity>\\n      <ControlTakingTime>30</ControlTakingTime>\\n      <WorkSpeedGlobal>1.0</WorkSpeedGlobal>\\n      <MarketValue>1000</MarketValue>\\n", t, count=1)
    if "<tools>" not in t:
        t = t.replace("<comps>", PROTOSS_HEAD_TOOL + "    <comps>", 1)
    return t, k'''
assert old3 in src, "make_mech end"
src = src.replace(old3, new3)

# 4. head tool constant
old4 = "AGM_COMPS = ("
new4 = '''PROTOSS_HEAD_TOOL = (
    "    <tools>\\n"
    "      <li>\\n"
    "        <label>head</label>\\n"
    "        <capacities>\\n"
    "          <li>Blunt</li>\\n"
    "        </capacities>\\n"
    "        <power>10</power>\\n"
    "        <cooldownTime>2.0</cooldownTime>\\n"
    "        <linkedBodyPartsGroup>HeadAttackTool</linkedBodyPartsGroup>\\n"
    "        <ensureLinkedBodyPartsGroupAlwaysUsable>true</ensureLinkedBodyPartsGroupAlwaysUsable>\\n"
    "      </li>\\n"
    "    </tools>\\n")

AGM_COMPS = ('''
assert old4 in src
src = src.replace(old4, new4, 1)

open(p, 'w', encoding='utf-8').write(src)
print('build_pm fully patched')
