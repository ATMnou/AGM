#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix12: correct ordering of the fix11 injections in build_tw.py."""
import re

p = 'build_tw.py'
src = open(p, encoding='utf-8').read()

# a) remove the misplaced luna EnsureHediff block (ran before inject_comps -> no-op)
misplaced = '''luna = luna.replace('<li Class="AGM.CompProperties_DisableFeral" />',
                    '<li Class="AGM.CompProperties_DisableFeral" />\\n'
                    '      <li Class="AGM.CompProperties_EnsureHediff">\\n'
                    '        <hediff>AGM_Luna_Hediff</hediff>\\n'
                    '      </li>')
'''
if misplaced in src:
    src = src.replace(misplaced, '')
    print('misplaced luna block removed')

# b) re-add after inject_comps
anchor = 'luna = inject_comps(luna)'
assert anchor in src
inject = anchor + '''
luna = luna.replace('<li Class="AGM.CompProperties_DisableFeral" />',
                    '<li Class="AGM.CompProperties_DisableFeral" />\\n'
                    '      <li Class="AGM.CompProperties_EnsureHediff">\\n'
                    '        <hediff>AGM_Luna_Hediff</hediff>\\n'
                    '      </li>')'''
src = src.replace(anchor, inject, 1)
print('luna hediff moved after inject_comps')

# c) Sol faction: move the injection after the race rename
old = '''sol_kind = sol_kind.replace("<race>AGM_Sol</race>",
                            "<race>AGM_Sol</race>\\n      <defaultFactionType>PlayerColony</defaultFactionType>")'''
assert old in src
src = src.replace(old, '')
anchor2 = 'sol_kind = sol_kind.replace("<race>TW_Mech_Doxa</race>", "<race>AGM_Sol</race>")'
assert anchor2 in src
src = src.replace(anchor2, anchor2 + '''
sol_kind = sol_kind.replace("<race>AGM_Sol</race>",
                            "<race>AGM_Sol</race>\\n      <defaultFactionType>PlayerColony</defaultFactionType>")''', 1)
print('sol faction moved after race rename')

# d) astra2: drop the duplicate faction add (astra2_kind copies astra_kind which already has it)
dup = '''astra2_kind = re.sub(r"\\s*<isBoss>true</isBoss>", "", astra2_kind)
astra2_kind = astra2_kind.replace("<race>AGM_Astra</race>",
                                  "<race>AGM_Astra</race>\\n    <defaultFactionType>PlayerColony</defaultFactionType>")'''
if dup in src:
    src = src.replace(dup, 'astra2_kind = re.sub(r"\\s*<isBoss>true</isBoss>", "", astra2_kind)')
    print('astra2 duplicate faction removed')

open(p, 'w', encoding='utf-8').write(src)
compile(src, p, 'exec')
print('fix12 done, syntax OK')
