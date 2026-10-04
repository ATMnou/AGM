#!/usr/bin/env python3
import re

# ---- fix build_kral.py: dedupe abilities instead of blanket removal ----
p = 'build_kral.py'
src = open(p, encoding='utf-8').read()
old = '''# drop the extra DeathRay ability copy + Valkyrian ability from skyfaller extract
abil = re.sub(r'<AbilityDef>\\s*<defName>AGM_DeathRay</defName>.*?</AbilityDef>', '', abil, flags=re.S)
abil = re.sub(r'<AbilityDef Name="LongJumpMech">\\s*<defName>ValkyrianLongjumpMech</defName>.*?</AbilityDef>', '', abil, flags=re.S)
abil = re.sub(r'<ThingDef ParentName="BaseBullet">\\s*<defName>AGM_DeathShotz</defName>.*?</ThingDef>', '', abil, flags=re.S)
# drop the first copy of AntiOrgPreOrbital from proj1 (skyfaller extract has the full one)
blocks_abil = [m.group(0) for m in re.finditer(r"<(AbilityDef|ThingDef|FleckDef)[^>]*>.*?</\\1>", abil, re.S)]
write("AbilityDefs/AbilityDefs_AGM_Kraltech.xml", "", blocks_abil)'''
new = '''# drop the Valkyrian ability (not part of AGM), then dedupe blocks by defName so the
# DeathRay/DeathShotz duplicates from the skyfaller extract are dropped, not the originals.
abil = re.sub(r'<AbilityDef Name="LongJumpMech">\\s*<defName>ValkyrianLongjumpMech</defName>.*?</AbilityDef>', '', abil, flags=re.S)
blocks_abil, seen_ab = [], set()
for mb in re.finditer(r"<(AbilityDef|ThingDef|FleckDef)[^>]*>.*?</\\1>", abil, re.S):
    b = mb.group(0)
    m2 = re.search(r"<defName>([^<]+)</defName>", b)
    if not m2 or m2.group(1) == "ValkyrianLongjumpMech":
        continue
    if m2.group(1) in seen_ab:
        continue
    seen_ab.add(m2.group(1))
    blocks_abil.append(b)
write("AbilityDefs/AbilityDefs_AGM_Kraltech.xml", "", blocks_abil)'''
assert old in src, "kral ability block not found"
src = src.replace(old, new)
open(p, 'w', encoding='utf-8').write(src)
print("build_kral fixed")

# ---- fix build_pm.py: balanced MultiTurretGun removal ----
p = 'build_pm.py'
src = open(p, encoding='utf-8').read()
old = '''    t = re.sub(r'<li Class="ProtossMech\\.CompProperties_MultiTurretGun">.*?</li>',
               '      <li Class="CompProperties_TurretGun">\\n'
               '        <turretDef>AGM_Turret_PurificationBlast</turretDef>\\n'
               '        <angleOffset>-90</angleOffset>\\n'
               '      </li>', t, flags=re.S)'''
new = '''    t = remove_comp_li(t, "ProtossMech.CompProperties_MultiTurretGun")
    t = t.replace("</comps>", '      <li Class="CompProperties_TurretGun">\\n'
               '        <turretDef>AGM_Turret_PurificationBlast</turretDef>\\n'
               '        <angleOffset>-90</angleOffset>\\n'
               '      </li>\\n    </comps>', 1)'''
assert old in src, "pm multiturret block not found"
src = src.replace(old, new)
helper = '''
def remove_comp_li(text, class_prefix):
    """Remove a balanced <li Class="prefix..."> ... </li> block, honouring nested <li> elements."""
    out = []
    pos = 0
    while True:
        m = re.search(r'\\s*<li Class="%s[^"]*"' % re.escape(class_prefix), text[pos:])
        if not m:
            out.append(text[pos:])
            break
        start = pos + m.start()
        depth = 0
        idx = start
        for tag in re.finditer(r"<li\\b|</li>", text[start:]):
            if tag.group(0) == "<li":
                depth += 1
            else:
                depth -= 1
                if depth == 0:
                    idx = start + tag.end()
                    break
        out.append(text[pos:start])
        pos = idx
    return "".join(out)

'''
marker = "things = load(\"pm_raw/persona_things.txt\")"
assert marker in src
src = src.replace(marker, helper + marker, 1)
open(p, 'w', encoding='utf-8').write(src)
print("build_pm fixed")

# ---- extract BladeShotz projectile into proj corpus ----
import subprocess
K = r"D:\SteamLibrary\steamapps\workshop\content\294100\3625664332\Defs"
r = subprocess.run(["python", "extract_blocks.py", K + r"\AbilityDef\Abilities_Mechanoids.xml",
                    "ThingDef", "BladeShotz"], capture_output=True, text=True)
open("kral_raw/proj1.txt", "a", encoding="utf-8").write("\n" + r.stdout)
# add BladeShotz to PROJ_NAMES in build_kral
src = open('build_kral.py', encoding='utf-8').read()
old = '''PROJ_NAMES = ["PlasmaBlastz","ChargeBlastz","PSIBlast","AntiGrainGrenade","AntiOrgBlast",
    "AntiOrgPreOrbital","AntiOrgPostOrbital","DeathShotz"]'''
new = '''PROJ_NAMES = ["PlasmaBlastz","ChargeBlastz","PSIBlast","AntiGrainGrenade","AntiOrgBlast",
    "AntiOrgPreOrbital","AntiOrgPostOrbital","DeathShotz","BladeShotz"]'''
assert old in src
src = src.replace(old, new)
open('build_kral.py', 'w', encoding='utf-8').write(src)
print("BladeShotz added")
