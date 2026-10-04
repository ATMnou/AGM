#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix13:
1. Sol's rail mortar: the weaponTags rename regex missed the block because the tag carries
   an Inherit="False" attribute - match attributes too so the gun's tag actually becomes
   AGM_SolRailMortar (kind/gun tag mismatch = weapon generation fails forever = endless repair).
2. Astra (both branches): <comps Inherit="False"> dropped BaseMechanoid's
   CompProperties_OverseerSubject and CompProperties_MechRepairable - without an overseer
   subject comp the mechanitor cannot take the mech over at all. Re-add both (our
   CompDisableFeral patch keeps the feral roll nullified)."""
import re

p = 'build_tw.py'
src = open(p, encoding='utf-8').read()

# 1. fix the weaponTags rename regex on the rail mortar
old = 'rail = re.sub(r"<weaponTags>.*?</weaponTags>", "<weaponTags>\\n      <li>AGM_SolRailMortar</li>\\n    </weaponTags>", rail, flags=re.S)'
new = 'rail = re.sub(r"<weaponTags[^>]*>.*?</weaponTags>", "<weaponTags>\\n      <li>AGM_SolRailMortar</li>\\n    </weaponTags>", rail, flags=re.S)'
assert old in src, 'rail tag regex'
src = src.replace(old, new)

# 2. overseer subject + mech repairable for astra, after inject_comps
anchor = 'astra = inject_comps(astra)'
assert anchor in src
inject = anchor + '''
# <comps Inherit="False"> on the worm dropped BaseMechanoid's overseer-subject and
# mech-repairable comps - without them the mechanitor cannot take Astra over at all.
OVERSEER_COMPS = (
    '      <li Class="CompProperties_OverseerSubject">\\n'
    '        <needsOverseerEffect>MechUncontrolled</needsOverseerEffect>\\n'
    '        <delayUntilFeralCheck>60000</delayUntilFeralCheck>\\n'
    '        <feralMtbDays>10</feralMtbDays>\\n'
    '        <feralCascadeRadialDistance>25</feralCascadeRadialDistance>\\n'
    '      </li>\\n'
    '      <li Class="CompProperties_MechRepairable" />\\n')
astra = astra.replace('<li Class="AGM.CompProperties_DisableFeral" />',
                      '<li Class="AGM.CompProperties_DisableFeral" />\\n' + OVERSEER_COMPS)'''
src = src.replace(anchor, inject, 1)

open(p, 'w', encoding='utf-8').write(src)
compile(src, p, 'exec')
print('fix13 applied, syntax OK')
