#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Port IFE XF-09 Ares support defs into AGM (standalone, AGM_-prefixed):
projectiles, plasma gas zone, and the Ares sound defs (+ audio files)."""
import re, os, shutil, glob

HERE = os.path.dirname(os.path.abspath(__file__))
AGM = os.path.normpath(os.path.join(HERE, ".."))
IFE = r"D:\SteamLibrary\steamapps\common\RimWorld\Mods\IFE"

RENAME_DEFS = [
    # (old defName, new defName)
    ("ExoMech_Bullet_AresLaser", "AGM_Bullet_AresLaser"),
    ("ExoMech_Bullet_AresPlasmaFireball", "AGM_Bullet_AresPlasmaFireball"),
    ("ExoMech_Bullet_AresTeslaOrb", "AGM_Bullet_AresTeslaOrb"),
    ("ExoMech_Bullet_AresTeslaSpark", "AGM_Bullet_AresTeslaSpark"),
    ("ExoMech_Bullet_AresPulseBlast", "AGM_Bullet_AresPulseBlast"),
    ("ExoMech_Bullet_AresSlashWave", "AGM_Bullet_AresSlashWave"),
    ("ExoMech_Bullet_AresNovaBeam", "AGM_Bullet_AresNovaBeam"),
    ("ExoMech_Bullet_AresGaussNuke", "AGM_Bullet_AresGaussNuke"),
    ("ExoMech_Bullet_AresDoomsdayRocket", "AGM_Bullet_AresDoomsdayRocket"),
    ("ExoMech_PlasmaGasZone", "AGM_PlasmaGasZone"),
]
RENAME_SOUNDS = [
    ("ExoMech_Sound_AresLaserArmCharge", "AGM_Sound_AresLaserArmCharge"),
    ("ExoMech_Sound_AresLaserCannon", "AGM_Sound_AresLaserCannon"),
    ("ExoMech_Sound_AresPlasmaCannon", "AGM_Sound_AresPlasmaCannon"),
    ("ExoMech_Sound_AresTeslaCannon", "AGM_Sound_AresTeslaCannon"),
    ("ExoMech_Sound_AresPulseCannonCharge", "AGM_Sound_AresPulseCannonCharge"),
    ("ExoMech_Sound_AresPulseCannon", "AGM_Sound_AresPulseCannon"),
    ("ExoMech_Sound_AresGaussNuke", "AGM_Sound_AresGaussNuke"),
    ("ExoMech_Sound_AresSlash", "AGM_Sound_AresSlash"),
    ("ExoMech_Sound_ExoMechImpendingDeath", "AGM_Sound_ImpendingDeath"),
]

def read(p):
    return open(p, encoding="utf-8-sig").read()

def blocks(text, tag):
    return [m.group(0) for m in re.finditer(r"<%s[^>]*>.*?</%s>" % (tag, tag), text, re.S)]

def write(path, blocks_list):
    full = '<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n\n' + "\n".join(blocks_list) + "\n\n</Defs>\n"
    p = os.path.join(AGM, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(full)
    print("wrote", path, len(full))

def rename(text, pairs):
    for old, new in pairs:
        text = text.replace("<defName>%s</defName>" % old, "<defName>%s</defName>" % new)
        text = text.replace(">%s<" % old, ">%s<" % new)   # reference tags
        text = text.replace('">%s<' % old, '">%s<' % new)
    return text

# ---------------- projectiles + gas zone ----------------
wpn = read(os.path.join(IFE, "Defs", "ThingDefs_Weapon", "Weapons_XF09Ares.xml"))
proj_blocks = blocks(wpn, "ThingDef")

wanted = [old for old, _ in RENAME_DEFS if old.startswith("ExoMech_Bullet")]
picked = []
for b in proj_blocks:
    m = re.search(r"<defName>([^<]+)</defName>", b)
    if m and m.group(1) in wanted:
        picked.append(b)

# gas zone def (GasZoneDef) - find its file
gas_txt = None
for f in glob.glob(os.path.join(IFE, "Defs", "**", "*.xml"), recursive=True):
    t = read(f)
    if "<defName>ExoMech_PlasmaGasZone</defName>" in t:
        for b in blocks(t, "GasZoneDef"):
            if "ExoMech_PlasmaGasZone" in b:
                picked.append(b)
                gas_txt = t
                break
        if gas_txt:
            break

picked = [rename(b, RENAME_DEFS) for b in picked]
# class refs inside projectiles point at AGM's ported classes already (thingClass ExoMech.Projectile_Exo)
picked = [b.replace("ExoMech.Projectile_Exo", "AGM.Projectile_Exo")
           .replace("ExoMech.ProjectileProperties_Exo", "AGM.ProjectileProperties_Exo") for b in picked]
write("ThingDefs_Weapon/Weapons_AGM_Astra.xml", picked)

# check what the gas zone references (overlay tex etc.)
gas_block = [b for b in picked if "PlasmaGasZone" in b]
if gas_block:
    print("GAS ZONE:", re.sub(r"\s+", " ", gas_block[0])[:400])

# ---------------- sounds ----------------
snd_txt = read(os.path.join(IFE, "Defs", "SoundDefs", "SoundDefs_ExoMech.xml"))
snd_blocks = []
audio_folders = set()
for b in blocks(snd_txt, "SoundDef"):
    m = re.search(r"<defName>([^<]+)</defName>", b)
    if not m:
        continue
    for old, new in RENAME_SOUNDS:
        if m.group(1) == old:
            b2 = rename(b, [(old, new)])
            snd_blocks.append(b2)
            audio_folders |= set(re.findall(r"<clipFolderPath>([^<]+)<", b2))
            break
write("SoundDefs/SoundDefs_AGM_Astra.xml", snd_blocks)

# copy audio files
for folder in sorted(audio_folders):
    src = os.path.join(IFE, "Sounds", folder.replace("/", os.sep))
    dst = os.path.join(AGM, "Sounds", folder.replace("/", os.sep))
    if os.path.isdir(src):
        if not os.path.isdir(dst):
            shutil.copytree(src, dst, dirs_exist_ok=True)
            print("audio:", folder)
    else:
        print("AUDIO MISSING:", folder)

# ---------------- texture check ----------------
tex_refs = set()
for b in picked:
    tex_refs |= set(re.findall(r"<texPath>([^<]+)<", b))
for t in sorted(tex_refs):
    p = os.path.join(AGM, "Textures", t.replace("/", os.sep))
    ok = os.path.isdir(p) or glob.glob(p + ".*") or glob.glob(p + "_*.*")
    print(("TEX OK " if ok else "TEX MISSING ") + t)
