#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""port_ares2: finish the standalone Ares port.
1. Port the plasma gas damage-zone ThingDef (AGM_PlasmaGasZone) + its texture.
2. Port the two missing sounds (plasma impact, tesla split) and fix the sound-def
   file's clip paths; copy the whole IFE Sounds/Ares folder.
3. Rename remaining ExoMech_* refs inside the ported weapon file."""
import re, os, shutil, glob

HERE = os.path.dirname(os.path.abspath(__file__))
AGM = os.path.normpath(os.path.join(HERE, ".."))
IFE = r"D:\SteamLibrary\steamapps\common\RimWorld\Mods\IFE"

def read(p):
    return open(p, encoding="utf-8-sig").read()

# ---- 1. gas damage zone ----
zones = read(os.path.join(IFE, "Defs", "ThingDefs_Items", "Things_ExoDamageZones.xml"))
mb = re.search(r'<ThingDef[^>]*>\s*<defName>ExoMech_PlasmaGasZone</defName>.*?</ThingDef>', zones, re.S)
assert mb, "plasma gas zone block"
blk = mb.group(0).replace("<defName>ExoMech_PlasmaGasZone</defName>", "<defName>AGM_PlasmaGasZone</defName>")
blk = blk.replace("ExoMech.DamageZone_Exo", "AGM.DamageZone_Exo")
full = '<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n\n' + blk + "\n\n</Defs>\n"
p = os.path.join(AGM, "Defs", "ThingDefs_Misc", "Things_AGM_DamageZones.xml")
os.makedirs(os.path.dirname(p), exist_ok=True)
open(p, "w", encoding="utf-8").write(full)
print("wrote Things_AGM_DamageZones.xml")

# gas texture
gtex = re.search(r"<texPath>([^<]+)</texPath>", blk).group(1)
src = os.path.join(IFE, "Textures", gtex.replace("/", os.sep))
dst = os.path.join(AGM, "Textures", gtex.replace("/", os.sep))
hits = glob.glob(src + ".*")
for h in hits:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(h, dst + os.path.splitext(h)[1])
    print("gas tex:", os.path.basename(h))

# ---- 2. sounds ----
snd = read(os.path.join(AGM, "Defs", "SoundDefs", "SoundDefs_AGM_Astra.xml"))
extra = []
snd_src = read(os.path.join(IFE, "Defs", "SoundDefs", "SoundDefs_ExoMech.xml"))
for m in re.finditer(r"<SoundDef[^>]*>\s*<defName>(ExoMech_Sound_AresPlasmaImpact|ExoMech_Sound_AresTeslaSplit)</defName>.*?</SoundDef>", snd_src, re.S):
    b = m.group(0).replace(m.group(1), "AGM_" + m.group(1).replace("ExoMech_Sound_", "Sound_"))
    extra.append(b)
snd = snd.replace("</Defs>", "\n".join(extra) + "\n\n</Defs>")
# any leftover ExoMech_ sound references inside defs -> AGM_ names
snd = re.sub(r"ExoMech_Sound_ExoMechImpendingDeath", "AGM_Sound_ImpendingDeath", snd)
snd = re.sub(r"ExoMech_Sound_", "AGM_Sound_", snd)
open(os.path.join(AGM, "Defs", "SoundDefs", "SoundDefs_AGM_Astra.xml"), "w", encoding="utf-8").write(snd)
print("sound defs updated:", len(extra), "added")

# copy the whole Ares audio folder
src = os.path.join(IFE, "Sounds", "Ares")
dst = os.path.join(AGM, "Sounds", "Ares")
if not os.path.isdir(dst):
    shutil.copytree(src, dst)
    print("audio copied:", len(os.listdir(dst)), "files")

# ---- 3. leftover ExoMech_ refs in the weapon file ----
p = os.path.join(AGM, "Defs", "ThingDefs_Weapon", "Weapons_AGM_Astra.xml")
w = read(p)
w = re.sub(r"ExoMech_Sound_ExoMechImpendingDeath", "AGM_Sound_ImpendingDeath", w)
w = re.sub(r"ExoMech_Sound_", "AGM_Sound_", w)
w = re.sub(r"ExoMech_Bullet_", "AGM_Bullet_", w)
w = re.sub(r"ExoMech_PlasmaGasZone", "AGM_PlasmaGasZone", w)
open(p, "w", encoding="utf-8").write(w)
print("weapon file refs cleaned; ExoMech leftovers:", len(re.findall(r"ExoMech", w)))
