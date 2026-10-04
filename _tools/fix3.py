#!/usr/bin/env python3
# Fix build_kral.py: prefix Kraltech hediff defNames with AGM_ and update damage-def refs;
# drop the duplicate fleck block from the effects file.
import re

p = 'build_kral.py'
src = open(p, encoding='utf-8').read()

old = '''write("HediffDefs/HediffDefs_AGM_Kraltech.xml", "", [transform(raw["hediffs"])])'''
new = '''hed = transform(raw["hediffs"])
for h in ["ShockPain", "Inflammable", "IncendiaryBody", "VitalityDrain", "ArmorBreaker",
          "Instantkill", "HealthBlight1"]:
    hed = hed.replace("<defName>%s</defName>" % h, "<defName>AGM_%s</defName>" % h)
    hed = hed.replace("<hediff>%s</hediff>" % h, "<hediff>AGM_%s</hediff>" % h)
write("HediffDefs/HediffDefs_AGM_Kraltech.xml", "", [hed])'''
assert old in src
src = src.replace(old, new)

# damage defs must reference the renamed hediffs too (damages.txt flows through dmg transform)
old2 = '''dmg = transform(raw["damages"])
for d in DAMAGE_NAMES:
    dmg = dmg.replace("<defName>%s</defName>" % d, "<defName>AGM_Damage_%s</defName>" % d)'''
new2 = '''dmg = transform(raw["damages"])
for d in DAMAGE_NAMES:
    dmg = dmg.replace("<defName>%s</defName>" % d, "<defName>AGM_Damage_%s</defName>" % d)
for h in ["ShockPain", "Inflammable", "IncendiaryBody", "VitalityDrain", "ArmorBreaker",
          "Instantkill", "HealthBlight1"]:
    dmg = dmg.replace("<hediff>%s</hediff>" % h, "<hediff>AGM_%s</hediff>" % h)
    dmg = re.sub(r"(<additionalHediffs>\\s*<li>\\s*<hediff>)%s(</hediff>)" % h,
                 r"\\1AGM_%s\\2" % h, dmg)'''
assert old2 in src
src = src.replace(old2, new2)

# effects: skip the duplicated fleck (ships in AbilityDefs file)
old3 = '''for mb in re.finditer(r"<(EffecterDef|ThingDef|FleckDef)[^>]*>.*?</\\1>", eff, re.S):
    b = mb.group(0)
    m = re.search(r"<defName>([^<]+)</defName>", b)
    if m and m.group(1) in seen:
        continue'''
new3 = '''for mb in re.finditer(r"<(EffecterDef|ThingDef|FleckDef)[^>]*>.*?</\\1>", eff, re.S):
    b = mb.group(0)
    m = re.search(r"<defName>([^<]+)</defName>", b)
    if m and (m.group(1) in seen or m.group(1) == "AGM_Fleck_BlastAntiOrganicRedLine"):
        continue'''
assert old3 in src
src = src.replace(old3, new3)
open(p, 'w', encoding='utf-8').write(src)
print("patched build_kral")
