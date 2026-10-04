#!/usr/bin/env python3
# Fix the damages pipeline in build_kral.py: dedicated transform that avoids the
# ability defName renames clobbering damage defNames; extract Kraltech's Bleed hediff.
import re

p = 'build_kral.py'
src = open(p, encoding='utf-8').read()

old = '''dmg = transform(raw["damages"])
for d in DAMAGE_NAMES:
    dmg = dmg.replace("<defName>%s</defName>" % d, "<defName>AGM_Damage_%s</defName>" % d)
for h in ["ShockPain", "Inflammable", "IncendiaryBody", "VitalityDrain", "ArmorBreaker",
          "Instantkill", "HealthBlight1"]:
    dmg = dmg.replace("<hediff>%s</hediff>" % h, "<hediff>AGM_%s</hediff>" % h)
    dmg = re.sub(r"(<additionalHediffs>\\s*<li>\\s*<hediff>)%s(</hediff>)" % h,
                 r"\\1AGM_%s\\2" % h, dmg)'''
new = '''# Dedicated transform for damage defs: do NOT run the generic transform() here - its
# ability defName renames would clobber the shared names (ChargeBlast etc.).
dmg = raw["damages"]
for s in SOUND_NAMES:
    dmg = dmg.replace("<soundExplosion>%s</soundExplosion>" % s, "<soundExplosion>AGM_%s</soundExplosion>" % s)
for fl in ["FireBlast", "ChargedBlast", "DroneExplosion", "AntiOrganicBlastZone"]:
    dmg = dmg.replace("<explosionCellFleck>%s</explosionCellFleck>" % fl, "<explosionCellFleck>AGM_Fleck_%s</explosionCellFleck>" % fl)
for d in DAMAGE_NAMES:
    dmg = dmg.replace("<defName>%s</defName>" % d, "<defName>AGM_Damage_%s</defName>" % d)
for h in ["ShockPain", "Inflammable", "IncendiaryBody", "VitalityDrain", "ArmorBreaker",
          "Instantkill", "HealthBlight1", "Bleed"]:
    dmg = dmg.replace("<hediff>%s</hediff>" % h, "<hediff>AGM_%s</hediff>" % h)'''
assert old in src, "damage pipeline block not found"
src = src.replace(old, new)

# hediffs: add Kraltech Bleed to the extracted set
old2 = '''hed = transform(raw["hediffs"])
for h in ["ShockPain", "Inflammable", "IncendiaryBody", "VitalityDrain", "ArmorBreaker",
          "Instantkill", "HealthBlight1"]:'''
new2 = '''import subprocess
_r = subprocess.run(["python", "extract_blocks.py",
                     r"D:\\SteamLibrary\\steamapps\\workshop\\content\\294100\\3625664332\\Defs\\Hediffs\\Hediffs_Various.xml",
                     "HediffDef", "Bleed"], capture_output=True, text=True)
hed = transform(raw["hediffs"] + "\\n" + _r.stdout)
for h in ["ShockPain", "Inflammable", "IncendiaryBody", "VitalityDrain", "ArmorBreaker",
          "Instantkill", "HealthBlight1", "Bleed"]:'''
assert old2 in src
src = src.replace(old2, new2)
open(p, 'w', encoding='utf-8').write(src)
print("build_kral damage pipeline fixed")

# validator: add projectile damageDef checks
p = 'validate_agm.py'
src = open(p, encoding='utf-8').read()
old3 = '''        if tag == "ThingDef":
            check(f, el, tag, "graphicData/texPath", "TextureRef" ) if False else None'''
new3 = '''        if tag == "ThingDef":
            dd = el.find("projectile/damageDef")
            if dd is not None and not exists("DamageDef", (dd.text or "").strip(), tw_branch):
                errors.append("%s: projectile damageDef '%s' not found" % (os.path.relpath(f, AGM), dd.text))'''
assert old3 in src
src = src.replace(old3, new3)
open(p, 'w', encoding='utf-8').write(src)
print("validator extended")
