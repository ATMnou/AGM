#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix11: gameplay-logic fixes.
1. Sol/Astra: drop isBoss (no bossgroup attached), add defaultFactionType PlayerColony,
   remove leftover Name="TWMechDoxa(Kind)" attrs (duplicate-name clash with Total Warfare),
   remove duplicate MechEnergyLossPerHP, give Sol's rail mortar a MarketValue so weapon
   generation actually equips it (missing weapon = permanent repair alert).
2. Astra TW branch: use the vanilla Pawn class instead of NCLWorm.NCL_Pawn_Worm so the
   mechanitor can own/assign it like a regular mech.
3. Luna: apply the bark hediff silently via AGM.CompProperties_EnsureHediff (new C# comp)
   instead of a HediffGiverSet that triggers a health-condition letter."""
import re

p = 'build_tw.py'
src = open(p, encoding='utf-8').read()

# ---- Sol ----
old = '''sol_thing = sol_thing.replace("<defName>TW_Mech_Doxa</defName>", "<defName>AGM_Sol</defName>")'''
new = '''sol_thing = sol_thing.replace("<defName>TW_Mech_Doxa</defName>", "<defName>AGM_Sol</defName>")
sol_thing = sol_thing.replace(' Name="TWMechDoxa"', '')'''
assert old in src
src = src.replace(old, new)

old = '''sol_kind = sol_kind.replace("<defName>TW_Mech_Doxa_Kind</defName>", "<defName>AGM_Sol</defName>")'''
new = '''sol_kind = sol_kind.replace("<defName>TW_Mech_Doxa_Kind</defName>", "<defName>AGM_Sol</defName>")
sol_kind = sol_kind.replace(' Name="TWMechDoxaKind"', '')
# boss flag without a bossgroup makes vanilla treat it as a boss mech, not a regular one
sol_kind = re.sub(r"\\s*<isBoss>true</isBoss>", "", sol_kind)
# dev-spawn as a player-owned mech (mirrors the Protoss heroes' kind)
sol_kind = sol_kind.replace("<race>AGM_Sol</race>",
                            "<race>AGM_Sol</race>\\n      <defaultFactionType>PlayerColony</defaultFactionType>")'''
assert old in src
src = src.replace(old, new)

# duplicate MechEnergyLossPerHP (AGM injected 0; the TW original 0.2 survives later in the file)
old = '''sol_thing = sol_thing.replace("      <PsychicSensitivity>0</PsychicSensitivity>",'''
idx = src.find(old)
assert idx > 0
src = src.replace(
    'sol_thing = re.sub(r"<li>\\s*<def>MechanoidFullyFormed</def>\\s*<minAge>100</minAge>.*?</li>", "", sol_thing, flags=re.S)',
    'sol_thing = re.sub(r"<li>\\s*<def>MechanoidFullyFormed</def>\\s*<minAge>100</minAge>.*?</li>", "", sol_thing, flags=re.S)\n'
    'sol_thing = re.sub(r"\\s*<MechEnergyLossPerHP[^>]*>0\\.2</MechEnergyLossPerHP>", "", sol_thing)')

# rail mortar MarketValue so it fits the kind's weaponMoney range and actually gets equipped
old = '''rail = rail.replace("<defName>TW_Antiparticle_Rail_Mortar</defName>", "<defName>AGM_Gun_SolRailMortar</defName>")'''
new = '''rail = rail.replace("<defName>TW_Antiparticle_Rail_Mortar</defName>", "<defName>AGM_Gun_SolRailMortar</defName>")
# without a MarketValue the gun cannot be generated into the kind's 9999 weaponMoney range,
# leaving Sol permanently "missing its weapon" (endless repair alert)
rail = rail.replace("<statBases>\\n\\t  <WorkToMake>20000</WorkToMake>", "<statBases>\\n      <MarketValue>8000</MarketValue>\\n\\t  <WorkToMake>20000</WorkToMake>")
if "MarketValue>8000" not in rail:
    rail = rail.replace("<statBases>", "<statBases>\\n      <MarketValue>8000</MarketValue>", 1)'''
assert old in src
src = src.replace(old, new)

# ---- Astra TW branch ----
old = '''astra = astra.replace("<thingClass>NCLWorm.NCL_Pawn_Worm</thingClass>\\n", "")'''
# the TW branch currently KEEPS the custom class; force vanilla pawn so the mechanitor can own it
old2 = '''astra = strip_block(astra, r'\\s*<li Class="NCL\\.CompProperties_TurretGunPawnOnly">.*?</li>')'''
new2 = '''astra = strip_block(astra, r'\\s*<li Class="NCL\\.CompProperties_TurretGunPawnOnly">.*?</li>')
# TW's NCL_Pawn_Worm is driven by TW's own garrison system and ignores vanilla mechanitor
# ownership - use the vanilla Pawn class so Astra behaves like a regular controllable mech.
# The TW comps/abilities below are plain ThingComps/AbilityDefs and attach fine to it.
astra = astra.replace("<thingClass>NCLWorm.NCL_Pawn_Worm</thingClass>\\n", "")'''
assert old2 in src
src = src.replace(old2, new2)

old = '''astra_kind = re.sub(r"\\s*<defaultFactionType>[^<]*</defaultFactionType>", "", astra_kind)
astra_kind = re.sub(r"<lifeStages>.*?</lifeStages>", gfx("Things/Mechanoid/Astra", "12"), astra_kind, flags=re.S)'''
new = '''astra_kind = re.sub(r"\\s*<defaultFactionType>[^<]*</defaultFactionType>", "", astra_kind)
astra_kind = re.sub(r"<lifeStages>.*?</lifeStages>", gfx("Things/Mechanoid/Astra", "12"), astra_kind, flags=re.S)
astra_kind = re.sub(r"\\s*<isBoss>true</isBoss>", "", astra_kind)
astra_kind = astra_kind.replace("<race>AGM_Astra</race>",
                                "<race>AGM_Astra</race>\\n    <defaultFactionType>PlayerColony</defaultFactionType>")'''
assert old in src
src = src.replace(old, new)

# ---- Astra NoTW branch ----
old = '''astra2_kind = re.sub(r"\\s*<li>NCLChaosTeleport</li>", "", astra2_kind)'''
new = old + '''
astra2_kind = re.sub(r"\\s*<isBoss>true</isBoss>", "", astra2_kind)
astra2_kind = astra2_kind.replace("<race>AGM_Astra</race>",
                                  "<race>AGM_Astra</race>\\n    <defaultFactionType>PlayerColony</defaultFactionType>")'''
assert old in src
src = src.replace(old, new)

# ---- Luna: silent hediff ----
old = '''luna = luna.replace("<hediff>NCL_Mech_Ironbark_Hediff</hediff>", "<hediff>AGM_Luna_Hediff</hediff>")'''
new = old + '''
# apply the bark hediff silently: no HediffGiverSet (its application fired a
# "health condition" letter). AGM.CompProperties_EnsureHediff adds it on spawn.
luna = re.sub(r"\\s*<hediffGiverSets>.*?</hediffGiverSets>", "", luna, flags=re.S)
luna = luna.replace("<li Class=\\"AGM.CompProperties_DisableFeral\\" />",
                    "<li Class=\\"AGM.CompProperties_DisableFeral\\" />\\n"
                    "      <li Class=\\"AGM.CompProperties_EnsureHediff\\">\\n"
                    "        <hediff>AGM_Luna_Hediff</hediff>\\n"
                    "      </li>")'''
assert old in src
src = src.replace(old, new)

# luna hediff file: keep only the hediff def, drop the giver set
old = '''write(OUT, "HediffDefs/HediffDefs_AGM_Luna.xml", [luna_hediff, luna_giver])'''
new = '''write(OUT, "HediffDefs/HediffDefs_AGM_Luna.xml", [luna_hediff])'''
assert old in src
src = src.replace(old, new)
# drop the giver parsing block entirely (unused now)
src = re.sub(r'luna_giver = ibg\.replace\([^\n]*\n', '', src)

open(p, 'w', encoding='utf-8').write(src)
compile(src, p, 'exec')
print('build_tw patched, syntax OK')
