#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix11b: idempotent gameplay-logic fixes for build_tw.py."""
import re

p = 'build_tw.py'
src = open(p, encoding='utf-8').read()
applied = []

def sub(old, new, tag):
    global src
    if new.split('\n')[0] in src and tag in src:
        applied.append(tag + ' (already)')
        return
    assert old in src, tag
    src = src.replace(old, new, 1)
    applied.append(tag)

# ---- Sol: strip leftover TW Name attrs ----
sub('sol_thing = sol_thing.replace("<defName>TW_Mech_Doxa</defName>", "<defName>AGM_Sol</defName>")',
    'sol_thing = sol_thing.replace("<defName>TW_Mech_Doxa</defName>", "<defName>AGM_Sol</defName>")\n'
    "sol_thing = sol_thing.replace(' Name=\"TWMechDoxa\"', '')", 'sol-name')

sub('sol_kind = sol_kind.replace("<defName>TW_Mech_Doxa_Kind</defName>", "<defName>AGM_Sol</defName>")',
    'sol_kind = sol_kind.replace("<defName>TW_Mech_Doxa_Kind</defName>", "<defName>AGM_Sol</defName>")\n'
    "sol_kind = sol_kind.replace(' Name=\"TWMechDoxaKind\"', '')\n"
    'sol_kind = re.sub(r"\\s*<isBoss>true</isBoss>", "", sol_kind)\n'
    'sol_kind = sol_kind.replace("<race>AGM_Sol</race>",\n'
    '                            "<race>AGM_Sol</race>\\n      <defaultFactionType>PlayerColony</defaultFactionType>")',
    'sol-kind')

# ---- Sol: drop the duplicate TW MechEnergyLossPerHP 0.2 ----
sub('sol_thing = re.sub(r"<li>\\s*<def>MechanoidFullyFormed</def>\\s*<minAge>100</minAge>.*?</li>", "", sol_thing, flags=re.S)',
    'sol_thing = re.sub(r"<li>\\s*<def>MechanoidFullyFormed</def>\\s*<minAge>100</minAge>.*?</li>", "", sol_thing, flags=re.S)\n'
    'sol_thing = re.sub(r"\\s*<MechEnergyLossPerHP[^>]*>0\\.2</MechEnergyLossPerHP>", "", sol_thing)',
    'sol-dup-stat')

# ---- Sol rail mortar MarketValue ----
sub('rail = rail.replace("<defName>TW_Antiparticle_Rail_Mortar</defName>", "<defName>AGM_Gun_SolRailMortar</defName>")',
    'rail = rail.replace("<defName>TW_Antiparticle_Rail_Mortar</defName>", "<defName>AGM_Gun_SolRailMortar</defName>")\n'
    'rail = re.sub(r"<statBases>\\n", "<statBases>\\n      <MarketValue>8000</MarketValue>\\n", rail, count=1)\n'
    'rail = rail.replace("MarketValue>8000\\n\\n", "MarketValue>8000\\n")',
    'sol-mv')

# ---- Astra TW: vanilla pawn class ----
sub("astra = remove_comp_li(astra, 'NCL.CompProperties_TurretGunPawnOnly')",
    "astra = remove_comp_li(astra, 'NCL.CompProperties_TurretGunPawnOnly')\n"
    '# TW\'s NCL_Pawn_Worm is driven by TW\'s own garrison system and ignores vanilla mechanitor\n'
    '# ownership - use the vanilla Pawn class so Astra behaves like a regular controllable mech.\n'
    '# The TW comps/abilities are plain ThingComps/AbilityDefs and attach fine to a vanilla pawn.\n'
    'astra = re.sub(r"\\s*<thingClass>NCLWorm\\.NCL_Pawn_Worm</thingClass>", "", astra)',
    'astra-vanilla-class')

# ---- Astra kinds: no boss flag + player faction ----
sub('astra_kind = re.sub(r"\\s*<defaultFactionType>[^<]*</defaultFactionType>", "", astra_kind)',
    'astra_kind = re.sub(r"\\s*<defaultFactionType>[^<]*</defaultFactionType>", "", astra_kind)\n'
    'astra_kind = re.sub(r"\\s*<isBoss>true</isBoss>", "", astra_kind)',
    'astra-kind-boss')

anchor = 'astra_kind = re.sub(r"<lifeStages>.*?</lifeStages>", gfx("Things/Mechanoid/Astra", "12"), astra_kind, flags=re.S)'
sub(anchor,
    anchor + '\n'
    'astra_kind = astra_kind.replace("<race>AGM_Astra</race>",\n'
    '                                "<race>AGM_Astra</race>\\n    <defaultFactionType>PlayerColony</defaultFactionType>")',
    'astra-kind-faction')

sub('astra2_kind = re.sub(r"\\s*<li>NCLChaosTeleport</li>", "", astra2_kind)',
    'astra2_kind = re.sub(r"\\s*<li>NCLChaosTeleport</li>", "", astra2_kind)\n'
    'astra2_kind = re.sub(r"\\s*<isBoss>true</isBoss>", "", astra2_kind)\n'
    'astra2_kind = astra2_kind.replace("<race>AGM_Astra</race>",\n'
    '                                  "<race>AGM_Astra</race>\\n    <defaultFactionType>PlayerColony</defaultFactionType>")',
    'astra2-kind')

# ---- Luna: silent hediff via EnsureHediff comp ----
sub('luna = luna.replace("<hediff>NCL_Mech_Ironbark_Hediff</hediff>", "<hediff>AGM_Luna_Hediff</hediff>")',
    'luna = luna.replace("<hediff>NCL_Mech_Ironbark_Hediff</hediff>", "<hediff>AGM_Luna_Hediff</hediff>")\n'
    '# silent bark hediff: no HediffGiverSet (it fired a health-condition letter);\n'
    '# AGM.CompProperties_EnsureHediff applies it on spawn without notifications.\n'
    'luna = re.sub(r"\\s*<hediffGiverSets>.*?</hediffGiverSets>", "", luna, flags=re.S)\n'
    "luna = luna.replace('<li Class=\"AGM.CompProperties_DisableFeral\" />',\n"
    "                    '<li Class=\"AGM.CompProperties_DisableFeral\" />\\n'\n"
    "                    '      <li Class=\"AGM.CompProperties_EnsureHediff\">\\n'\n"
    "                    '        <hediff>AGM_Luna_Hediff</hediff>\\n'\n"
    "                    '      </li>')",
    'luna-hediff')

sub('write(OUT, "HediffDefs/HediffDefs_AGM_Luna.xml", [luna_hediff, luna_giver])',
    'write(OUT, "HediffDefs/HediffDefs_AGM_Luna.xml", [luna_hediff])',
    'luna-write')

src = re.sub(r'luna_giver = ibg\.replace\([^\n]*\n', '', src)

open(p, 'w', encoding='utf-8').write(src)
compile(src, p, 'exec')
print('applied:', applied)
