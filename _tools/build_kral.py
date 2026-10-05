#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble AGM Kraltech-derived defs (Fable/Opus/Sonnet/Haiku + escorts + support defs).
Reads raw extracted blocks from _tools/kral_raw/ and the per-file extracts, applies the
rename/override map, and writes final Defs files into the AGM mod folder."""
import re, os, sys
_re = re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "Defs"))

def load(p):
    with open(os.path.join(HERE, p), encoding="utf-8-sig") as f:
        return f.read()

mechs = load("kral_mechs.txt")
kind_emp = load("kral_kind_empress.txt")
kind_war = load("kral_kind_warlord.txt")
kind_drg = load("kral_kind_dragon.txt")
apo = load("kral_apocriton.txt")
raw = {n: load(os.path.join("kral_raw", n + ".txt")) for n in
       ("weapons", "turrets", "abilities", "proj1", "skyfaller", "bodies", "bodyparts",
        "damages", "hediffs", "sounds", "effects", "effects2", "effects3", "motes", "motes2",
        "flecks", "duty")}
stats = load("kral_raw/stats.xml")

DAMAGE_NAMES = ["ChargeBlast","BlastFlame","PsiBlast","PsiExplosion","AntiHumanNanites",
    "AntiOrganicBlast","AntiHumanNanitesFlame","BleedBullets","Inflamable","Incinerate",
    "VitalityDrainBullet","ArmorBreakerBullet","DeathBullet","BulletHealthBlight","ShockBullets"]
ABILITY_NAMES = ["BladeShot","PsychicBlast","PlasmaBlast","ChargeBlast","AntiOrganicGrenade",
    "AntiOrganicBlast","AntiOrganicOrbitalStrike","DeathRay"]
PROJ_NAMES = ["PlasmaBlastz","ChargeBlastz","PSIBlast","AntiGrainGrenade","AntiOrgBlast",
    "AntiOrgPreOrbital","AntiOrgPostOrbital","DeathShotz","BladeShotz"]
SOUND_NAMES = ["Shot_EmpressBlade","Shot_Doom","Shot_MechChargedSniperRifle","Shot_LaserBlaster",
    "Shot_ChainGun","Shot_HeavyLaser","Shot_ExtinctionRay","Explosion_PlasmaCannon","Shot_ToxCanister"]
STAT_NAMES = ["HeatNullNaniteResistance","HeatNullNaniteEnvironmentResistance",
    "ColdNullNaniteResistance","ColdNullNaniteEnvironmentResistance","RadiationResistance",
    "RadiationEnvironmentResistance","AntiOrgToxinResistance","AntiOrgToxinEnvironmentResistance",
    "RageVirusResistance","RageVirusEnvironmentResistance"]
EFFECT_NAMES = ["SupremeApocrionAttached","AntiOrganicShockwave","AntiOrgElectricityArc"]
MOTE_NAMES = ["Mote_LaserBlasterEX","Mote_DeathRayz","Mote_ValyrianBlast_Charge",
    "Mote_AntiOrganicSparkArch"]
WEAPON_TAGS = ["MechChaingun","MechLaserBlaster","MechHeavyLaserBlaster"]
STRIP_TAGS = ["MK2MechanoidGunShortRange","MechAssaultRiflez","MechAssaultRifleStunz",
    "MechAssaultRifleFrostz","MechanoidMonoSword","MechTriShot"]

def alt_names(name):
    """Damage-def style alternatives for the shared ability/damage name."""
    return {"ChargeBlast","PlasmaBlast","PsychicBlast","AntiOrganicBlast","AntiHumanNanites"}

# ---------------- per-kind graphics replacement ----------------
BOSS_GFX = {
    "Mech_SupremeApocriton": ("Things/Mechanoid/Fable", "7", "AGM_Fable"),
    "Mech_DragonWarlord":    ("Things/Mechanoid/Opus", "5", "AGM_Opus"),
    "Mech_HydraulicEmpress": ("Things/Mechanoid/Sonnet", "5", "AGM_Sonnet"),
    "Mech_Dragon":           ("Things/Mechanoid/Haiku", "4.5", "AGM_Haiku"),
}

def replace_boss_lifestages(kind_text, tex, size):
    gfx = ('    <lifeStages>\n      <li>\n        <bodyGraphicData>\n'
           '          <texPath>%s</texPath>\n          <shaderType>Cutout</shaderType>\n'
           '          <graphicClass>Graphic_Multi</graphicClass>\n'
           '          <drawSize>%s</drawSize>\n'
           '          <shadowData>\n            <volume>(0.7, 0.8, 0.7)</volume>\n'
           '          </shadowData>\n        </bodyGraphicData>\n      </li>\n'
           '    </lifeStages>' % (tex, size))
    return re.sub(r"<lifeStages>.*?</lifeStages>", gfx, kind_text, flags=re.S)

# ---------------- global transform ----------------
def transform(text):
    # 1. body refs first (before defName renames)
    text = re.sub(r"<body>Mech_Empress</body>", "<body>AGM_Body_Empress</body>", text)
    text = re.sub(r"<body>Mech_Warlord</body>", "<body>AGM_Body_Warlord</body>", text)
    text = re.sub(r"<body>Mech_Dragon</body>", "<body>AGM_Body_Wyvern</body>", text)
    text = re.sub(r"<body>Mech_SupremeApocriton</body>", "<body>AGM_Body_Fable</body>", text)
    # 2. defName / race / spawnPawnKind renames (longest first)
    pairs = [
        ("Mech_SupremeApocriton", "AGM_Fable"),
        ("Mech_DragonWarlord", "AGM_Opus"),
        ("Mech_HydraulicEmpress", "AGM_Sonnet"),
        ("Mech_DragonKnight", "AGM_KnightWarlord"),
        ("Mech_HydraulicKnight", "AGM_KnightEmpress"),
        ("Mech_ScythUrchin", "AGM_Urchin"),
        ("Mech_Dragon", "AGM_Haiku"),
    ]
    for old, new in pairs:
        text = text.replace("<defName>%s</defName>" % old, "<defName>%s</defName>" % new)
        text = text.replace("<race>%s</race>" % old, "<race>%s</race>" % new)
        text = text.replace("<spawnPawnKind>%s</spawnPawnKind>" % old, "<spawnPawnKind>%s</spawnPawnKind>" % new)
    # 3. abstract names
    text = text.replace('ParentName="MechBosses"', 'ParentName="AGM_KralBossBase"')
    text = re.sub(r'Name="Mech(?:SupremeApocriton|DragonWarlord|HydraulicEmpress|Dragon)(?:Kind)?" ', '', text)
    # 4. custom stat tags
    for s in STAT_NAMES:
        text = text.replace("<%s>" % s, "<AGM_%s>" % s).replace("</%s>" % s, "</AGM_%s>" % s)
    # 5. duty
    text = text.replace("<dutyBoss>MilitorQueen</dutyBoss>", "<dutyBoss>AGM_MilitorQueen</dutyBoss>")
    text = text.replace("<defName>MilitorQueen</defName>", "<defName>AGM_MilitorQueen</defName>")
    # 6. damage refs (context-specific)
    for d in DAMAGE_NAMES:
        text = text.replace("<damageDef>%s</damageDef>" % d, "<damageDef>AGM_Damage_%s</damageDef>" % d)
        text = text.replace("<explosiveDamageType>%s</explosiveDamageType>" % d, "<explosiveDamageType>AGM_Damage_%s</explosiveDamageType>" % d)
        text = text.replace("<explosionDamage>%s</explosionDamage>" % d, "<explosionDamage>AGM_Damage_%s</explosionDamage>" % d)
        text = re.sub(r"<def>%s</def>" % d, "<def>AGM_Damage_%s</def>" % d, text)
    # 7. ability list refs and ability defNames (only where unambiguous tags)
    for a in ABILITY_NAMES:
        text = text.replace("<li>%s</li>" % a, "<li>AGM_%s</li>" % a)
        text = re.sub(r"<defName>%s</defName>" % a, "<defName>AGM_%s</defName>" % a, text)
    # 8. projectile refs + defNames
    for p in PROJ_NAMES:
        text = text.replace("<projectileDef>%s</projectileDef>" % p, "<projectileDef>AGM_%s</projectileDef>" % p)
        text = text.replace("<postExplosionSpawnThingDef>%s</postExplosionSpawnThingDef>" % p,
                            "<postExplosionSpawnThingDef>AGM_%s</postExplosionSpawnThingDef>" % p)
        text = re.sub(r"<defName>%s</defName>" % p, "<defName>AGM_%s</defName>" % p, text)
    # 9. weapons / turrets / bullets
    for w in ["Gun_ChainGunTurret","Gun_MechLaserBlasterTurret","Gun_MechLaserBlasterTurretEX",
              "Gun_MechChaingun","Gun_MechLaserBlaster","Gun_MechHeavyLaserBlaster",
              "Bullet_ChainGunTurret","Bullet_MechLaserBlasterTurret","Bullet_MechLaserBlasterTurretEX",
              "Bullet_MechChaingun","Bullet_MechLaserBlaster","Bullet_MechHeavyLaserBlaster"]:
        text = text.replace("<turretDef>%s</turretDef>" % w, "<turretDef>AGM_%s</turretDef>" % w)
        text = re.sub(r"<defName>%s</defName>" % w, "<defName>AGM_%s</defName>" % w, text)
        text = text.replace("<defaultProjectile>%s</defaultProjectile>" % w, "<defaultProjectile>AGM_%s</defaultProjectile>" % w)
    for t in WEAPON_TAGS:
        text = text.replace("<li>%s</li>" % t, "<li>AGM_%s</li>" % t)
        # weapon tags inside the gun defs themselves
        text = re.sub(r"(<weaponTags>\s*)<li>%s</li>" % t, r"\1<li>AGM_%s</li>" % t, text)
    for t in STRIP_TAGS:
        text = text.replace("<li>%s</li>" % t, "")
    # 10. sounds
    for s in SOUND_NAMES:
        text = text.replace("<defName>%s</defName>" % s, "<defName>AGM_%s</defName>" % s)
        text = re.sub(r"(<soundCast>)%s(</soundCast>)" % s, r"\1AGM_%s\2" % s, text)
        text = re.sub(r"(<soundExplosion>)%s(</soundExplosion>)" % s, r"\1AGM_%s\2" % s, text)
    # 11. effects / motes / flecks
    for e in EFFECT_NAMES:
        text = text.replace("<defName>%s</defName>" % e, "<defName>AGM_%s</defName>" % e)
        text = text.replace("<effecterDef>%s</effecterDef>" % e, "<effecterDef>AGM_%s</effecterDef>" % e)
        text = text.replace("<explosionCenterEffecter>%s</explosionCenterEffecter>" % e, "<explosionCenterEffecter>AGM_%s</explosionCenterEffecter>" % e)
        text = text.replace("<explosionCellEffecter>%s</explosionCellEffecter>" % e, "<explosionCellEffecter>AGM_%s</explosionCellEffecter>" % e)
    for m in MOTE_NAMES:
        text = text.replace("<defName>%s</defName>" % m, "<defName>AGM_%s</defName>" % m)
        text = text.replace("<moteDef>%s</moteDef>" % m, "<moteDef>AGM_%s</moteDef>" % m)
        text = text.replace("<laserMote>%s</laserMote>" % m, "<laserMote>AGM_%s</laserMote>" % m)
    text = text.replace("<defName>Fleck_BlastAntiOrganicRedLine</defName>", "<defName>AGM_Fleck_BlastAntiOrganicRedLine</defName>")
    text = text.replace("<fleckDef>Fleck_BlastAntiOrganicRedLine</fleckDef>", "<fleckDef>AGM_Fleck_BlastAntiOrganicRedLine</fleckDef>")
    for fl in ["FireBlast", "ChargedBlast", "DroneExplosion", "AntiOrganicBlastZone"]:
        text = text.replace("<defName>%s</defName>" % fl, "<defName>AGM_Fleck_%s</defName>" % fl)
        text = text.replace("<explosionCellFleck>%s</explosionCellFleck>" % fl, "<explosionCellFleck>AGM_Fleck_%s</explosionCellFleck>" % fl)
    # 12. LaserBeamz removal
    text = re.sub(r'\s*<comps>\s*<li Class="Kraltech_Industries\.LaserBeamz_CompProperties">.*?</li>\s*</comps>', '', text, flags=re.S)
    text = text.replace("<thingClass>Kraltech_Industries.LaserBeamzProj</thingClass>", "<thingClass>Bullet</thingClass>")
    # 13. killed leavings / butcher body part drop
    text = re.sub(r"\s*<killedLeavingsPlayerHostile>.*?</killedLeavingsPlayerHostile>", "", text, flags=re.S)
    text = re.sub(r"\s*<butcherBodyPart>.*?</butcherBodyPart>", "", text, flags=re.S)
    return text

# ---------------- AGM trait injection ----------------
AGM_STATS = ("<MechEnergyUsageFactor>0</MechEnergyUsageFactor>\n"
             "      <WastepacksPerRecharge>0</WastepacksPerRecharge>\n"
             "      <MechEnergyLossPerHP>0</MechEnergyLossPerHP>\n"
             "      <BandwidthCost>%s</BandwidthCost>")
AGM_COMPS = ('      <li Class="AGM.CompProperties_IgnoreMechanitorCommandRange" />\n'
             '      <li Class="AGM.CompProperties_DisableFeral" />\n')

def collapse_lifestages(text):
    """Drop the minAge-100 second life stage so race and PawnKind stage counts match."""
    return re.sub(r"<li>\s*<def>MechanoidFullyFormed</def>\s*<minAge>100</minAge>.*?</li>", "", text, flags=re.S)

def inject_traits(thingdef_text, bandwidth, weightclass=None):
    # stats: insert after <statBases>
    m = re.search(r"<statBases>\n", thingdef_text)
    if m:
        thingdef_text = thingdef_text[:m.end()] + "      " + AGM_STATS % bandwidth + thingdef_text[m.end():]
    else:
        print("WARN: no statBases found", file=sys.stderr)
    # normalize any existing MechEnergyLossPerHP to 0
    thingdef_text = re.sub(r"<MechEnergyLossPerHP>[^<]*</MechEnergyLossPerHP>",
                           "<MechEnergyLossPerHP>0</MechEnergyLossPerHP>", thingdef_text)
    # weight class
    if weightclass:
        if "<mechWeightClass>" in thingdef_text:
            thingdef_text = re.sub(r"<mechWeightClass>[^<]*</mechWeightClass>",
                                   "<mechWeightClass>%s</mechWeightClass>" % weightclass, thingdef_text)
        else:
            thingdef_text = re.sub(r"(<baseBodySize>[^<]*</baseBodySize>)",
                                   r"\1\n      <mechWeightClass>%s</mechWeightClass>" % weightclass,
                                   thingdef_text, count=1)
    # comps: insert right after the first <comps...> open tag
    thingdef_text = re.sub(r"(<comps[^>]*>\n)", r"\1" + AGM_COMPS, thingdef_text, count=1)
    return thingdef_text

# ---------------- corpus assembly ----------------
apo_kind = re.search(r'<PawnKindDef Name="MechSupremeApocritonKind".*?</PawnKindDef>', apo, re.S).group(0)
kinds = {"Mech_SupremeApocriton": replace_boss_lifestages(apo_kind, *BOSS_GFX["Mech_SupremeApocriton"][:2]),
         "Mech_DragonWarlord": replace_boss_lifestages(kind_war, *BOSS_GFX["Mech_DragonWarlord"][:2]),
         "Mech_HydraulicEmpress": replace_boss_lifestages(kind_emp, *BOSS_GFX["Mech_HydraulicEmpress"][:2]),
         "Mech_Dragon": replace_boss_lifestages(kind_drg, *BOSS_GFX["Mech_Dragon"][:2])}

things = {}
for name, (tex, size, newname) in BOSS_GFX.items():
    m = re.search(r"<ThingDef[^>]*>\s*<defName>%s</defName>.*?</ThingDef>" % name, mechs, re.S)
    things[name] = m.group(0)

esc_urchin_kind = re.search(r'<PawnKindDef ParentName="LightMechanoidKind">\s*<defName>Mech_ScythUrchin</defName>.*?</PawnKindDef>', load("kral_urchin.txt"), re.S).group(0)
m = re.search(r'<ThingDef ParentName="LightMechanoid">\s*<defName>Mech_ScythUrchin</defName>.*?</ThingDef>', mechs, re.S)
esc_urchin_thing = m.group(0)
knight_txt = load("kral_knight.txt")
dgnk_txt = load("kral_dragonknight.txt")
esc_knight_thing = re.search(r'<ThingDef ParentName="BaseMechanoidWalker">\s*<defName>Mech_HydraulicKnight</defName>.*?</ThingDef>', knight_txt, re.S).group(0)
esc_knight_kind = re.search(r'<PawnKindDef ParentName="BaseMechanoidKind">\s*<defName>Mech_HydraulicKnight</defName>.*?</PawnKindDef>', knight_txt, re.S).group(0)
esc_dknight_thing = re.search(r'<ThingDef ParentName="BaseMechanoidWalker">\s*<defName>Mech_DragonKnight</defName>.*?</ThingDef>', dgnk_txt, re.S).group(0)
esc_dknight_kind = re.search(r'<PawnKindDef ParentName="BaseMechanoidKind">\s*<defName>Mech_DragonKnight</defName>.*?</PawnKindDef>', dgnk_txt, re.S).group(0)

BANDWIDTH = {"AGM_Fable": (4, "UltraHeavy"), "AGM_Opus": (3, "Heavy"),
             "AGM_Sonnet": (2, "Medium"), "AGM_Haiku": (1, "Light"),
             "AGM_Urchin": (1, "Light"), "AGM_KnightEmpress": (1, "Light"),
             "AGM_KnightWarlord": (1, "Light")}

def write(path, header, blocks):
    cleaned = []
    for b in blocks:
        b = re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", b, flags=re.S)
        b = re.sub(r"^\s*<Defs>\s*", "", b, flags=re.S)
        b = re.sub(r"\s*</Defs>\s*$", "", b, flags=re.S)
        cleaned.append(b)
    full = '<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n\n' + header + "\n".join(cleaned) + "\n\n</Defs>\n"
    p = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(full)
    print("wrote", path, len(full))

# ---- race files ----
ABSTRACT = '''  <ThingDef Name="AGM_KralBossBase" ParentName="HeavyMechanoid" Abstract="True">
    <statBases>
      <MarketValue>5500</MarketValue>
      <ControlTakingTime>30</ControlTakingTime>
      <BandwidthCost>3</BandwidthCost>
      <MechEnergyUsageFactor>0</MechEnergyUsageFactor>
      <WastepacksPerRecharge>0</WastepacksPerRecharge>
    </statBases>
    <race>
      <baseHealthScale>10.5</baseHealthScale>
    </race>
    <butcherProducts Inherit="False">
      <Steel>500</Steel>
      <Plasteel>250</Plasteel>
    </butcherProducts>
  </ThingDef>
'''

corp_a = transform(things["Mech_SupremeApocriton"] + kinds["Mech_SupremeApocriton"])
corp_o = transform(things["Mech_DragonWarlord"] + kinds["Mech_DragonWarlord"])
corp_s = transform(things["Mech_HydraulicEmpress"] + kinds["Mech_HydraulicEmpress"])
corp_h = transform(things["Mech_Dragon"] + kinds["Mech_Dragon"])

corp_a = inject_traits(corp_a, 4, "UltraHeavy")
corp_o = collapse_lifestages(corp_o)
corp_o = inject_traits(corp_o, 3, "Heavy")
corp_s = collapse_lifestages(corp_s)
corp_s = inject_traits(corp_s, 2, "Medium")
corp_h = collapse_lifestages(corp_h)
corp_h = inject_traits(corp_h, 1, "Light")

write("ThingDefs_Races/Races_AGM_Fable.xml", ABSTRACT, [corp_a])
write("ThingDefs_Races/Races_AGM_Opus.xml", "", [corp_o])
write("ThingDefs_Races/Races_AGM_Sonnet.xml", "", [corp_s])
write("ThingDefs_Races/Races_AGM_Haiku.xml", "", [corp_h])

# ---- escorts ----
esc = transform(esc_urchin_thing + esc_urchin_kind + esc_knight_thing + esc_knight_kind +
                esc_dknight_thing + esc_dknight_kind)
esc = esc.replace("<body>Mech_Grunt</body>", "<body>AGM_Knight_Body</body>")
# inject traits into each escort ThingDef
esc = inject_traits(esc, 1)  # first block only gets stats via count=1; do per-block instead
esc = transform_inject_all = esc
# per-block injection:
def inject_all_blocks(text):
    out = []
    pos = 0
    for m in re.finditer(r"<ThingDef[^>]*>.*?</ThingDef>", text, re.S):
        out.append(text[pos:m.start()])
        out.append(inject_traits(m.group(0), 1))
        pos = m.end()
    out.append(text[pos:])
    return "".join(out)
esc = inject_all_blocks(esc)
write("ThingDefs_Races/Races_AGM_Support.xml", "", [esc])

# ---- bodies ----
_bp_src = open(os.path.join(r"D:\SteamLibrary\steamapps\workshop\content\294100\3625664332\Defs", "Bodies", "Bodies_n_Bodyparts_Mechanoids.xml"), encoding="utf-8-sig").read()
_bp_parents = {}
for _m in _re.finditer(r'<BodyPartDef[^>]*Abstract="True"[^>]*Name="([^"]+)">(.*?)</BodyPartDef>', _bp_src, _re.S):
    _bp_parents[_m.group(1)] = _m.group(2)
def _inline_bp(m):
    pname, inner = m.group(1), m.group(2)
    pin = _bp_parents[pname]
    child_tags = set(_re.findall(r"<(\w+)[^>]*>", inner))
    add = []
    for fbm in _re.finditer(r"<(\w+)[^>]*>.*?</\1>", pin, _re.S):
        fb = fbm.group(0)
        tag = fbm.group(1)
        if tag not in child_tags:
            add.append("    " + fb)
    joined = ("\n" + "\n".join(add) + "\n" + inner) if add else inner
    return "<BodyPartDef>" + joined + "</BodyPartDef>"
bodies = raw["bodies"] + raw["bodyparts"] + load("kral_raw/grunt_body.txt")
bodies = _re.sub(r'<BodyPartDef ParentName="([^"]+)">(.*?)</BodyPartDef>', _inline_bp, bodies, flags=_re.S)
bodies = bodies.replace("<defName>Mech_Empress</defName>", "<defName>AGM_Body_Empress</defName>")
bodies = bodies.replace("<defName>Mech_Warlord</defName>", "<defName>AGM_Body_Warlord</defName>")
bodies = bodies.replace("<defName>Mech_Dragon</defName>", "<defName>AGM_Body_Wyvern</defName>")
bodies = bodies.replace("<defName>Mech_SupremeApocriton</defName>", "<defName>AGM_Body_Fable</defName>")
bodies = bodies.replace("<defName>Mech_Grunt</defName>", "<defName>AGM_Knight_Body</defName>")
write("Bodies/Bodies_AGM_Kraltech.xml", "", [bodies])

# ---- abilities + projectiles + flecks ----
abil = transform(raw["abilities"] + raw["proj1"] + raw["skyfaller"] + raw["flecks"])
# drop the Valkyrian ability (not part of AGM), then dedupe blocks by defName so the
# DeathRay/DeathShotz duplicates from the skyfaller extract are dropped, not the originals.
abil = re.sub(r'<AbilityDef Name="LongJumpMech">\s*<defName>ValkyrianLongjumpMech</defName>.*?</AbilityDef>', '', abil, flags=re.S)
blocks_abil, seen_ab = [], set()
for mb in re.finditer(r"<(AbilityDef|ThingDef|FleckDef)[^>]*>.*?</\1>", abil, re.S):
    b = mb.group(0)
    m2 = re.search(r"<defName>([^<]+)</defName>", b)
    if not m2 or m2.group(1) == "ValkyrianLongjumpMech":
        continue
    if m2.group(1) in seen_ab:
        continue
    seen_ab.add(m2.group(1))
    blocks_abil.append(b)
write("AbilityDefs/AbilityDefs_AGM_Kraltech.xml", "", blocks_abil)

# ---- damages / hediffs / stats / duty ----
# Dedicated transform for damage defs: do NOT run the generic transform() here - its
# ability defName renames would clobber the shared names (ChargeBlast etc.).
dmg = raw["damages"]
# inline Kraltech abstract damage parents (Mech_ChaingunBullets etc.)
kral_damages_src = open(os.path.join(r"D:\SteamLibrary\steamapps\workshop\content\294100\3625664332\Defs", "DamageDef", "Damages_Various.xml"), encoding="utf-8-sig").read()
import re as _re
_dmg_parents = {}
for _m in _re.finditer(r'<DamageDef[^>]*Abstract="True"[^>]*Name="([^"]+)">(.*?)</DamageDef>', kral_damages_src, _re.S):
    _dmg_parents[_m.group(1)] = _m.group(2)
def _inline_damage(m):
    pname, inner = m.group(1), m.group(2)
    if pname not in _dmg_parents:
        return m.group(0)
    pin = _dmg_parents[pname]
    # top-level child tags only - a nested <hediff> inside <additionalHediffs> must not
    # count as "already present" or the parent's <hediff> would be skipped (null hediff
    # -> HediffMaker NRE on impact).
    try:
        import xml.etree.ElementTree as _ET
        child_tags = set(ch.tag for ch in _ET.fromstring("<Root>" + inner + "</Root>"))
    except Exception:
        child_tags = set(_re.findall(r"<(\w+)[^>]*>", inner))
    add = []
    for fbm in _re.finditer(r"<(\w+)[^>]*>.*?</\1>", pin, _re.S):
        fb = fbm.group(0)
        tag = fbm.group(1)
        if tag not in child_tags:
            add.append("    " + fb)
    joined = ("\n" + "\n".join(add) + "\n" + inner) if add else inner
    return "<DamageDef>" + joined + "</DamageDef>"
dmg = _re.sub(r'<DamageDef ParentName="([^"]+)">(.*?)</DamageDef>', _inline_damage, dmg, flags=_re.S)
# replace Kraltech custom DamageWorkers with vanilla ones
dmg = dmg.replace("Kraltech_Industries.DamageWorker_Plasma", "DamageWorker_Flame")
dmg = dmg.replace("Kraltech_Industries.DamageWorker_Charged", "DamageWorker_AddInjury")
dmg = dmg.replace("Kraltech_Industries.DamageWorker_Psychic", "DamageWorker_AddInjury")
dmg = dmg.replace("Kraltech_Industries.DamageWorker_AntiOrganics", "DamageWorker_AddInjury")
# rename effecter refs to AGM copies
dmg = dmg.replace("<explosionCenterEffecter>AntiOrganicShockwave</explosionCenterEffecter>",
                  "<explosionCenterEffecter>AGM_AntiOrganicShockwave</explosionCenterEffecter>")
dmg = dmg.replace("<explosionCellEffecter>AntiOrgElectricityArc</explosionCellEffecter>",
                  "<explosionCellEffecter>AGM_AntiOrgElectricityArc</explosionCellEffecter>")
for s in SOUND_NAMES:
    dmg = dmg.replace("<soundExplosion>%s</soundExplosion>" % s, "<soundExplosion>AGM_%s</soundExplosion>" % s)
for fl in ["FireBlast", "ChargedBlast", "DroneExplosion", "AntiOrganicBlastZone"]:
    dmg = dmg.replace("<explosionCellFleck>%s</explosionCellFleck>" % fl, "<explosionCellFleck>AGM_Fleck_%s</explosionCellFleck>" % fl)
for d in DAMAGE_NAMES:
    dmg = dmg.replace("<defName>%s</defName>" % d, "<defName>AGM_Damage_%s</defName>" % d)
for h in ["ShockPain", "Inflammable", "IncendiaryBody", "VitalityDrain", "ArmorBreaker",
          "Instantkill", "HealthBlight1", "Bleed"]:
    dmg = dmg.replace("<hediff>%s</hediff>" % h, "<hediff>AGM_%s</hediff>" % h)
write("DamageDefs/DamageDefs_AGM_Kraltech.xml", "", [dmg])
import subprocess
_r = subprocess.run(["python", "extract_blocks.py",
                     r"D:\SteamLibrary\steamapps\workshop\content\294100\3625664332\Defs\Hediffs\Hediffs_Various.xml",
                     "HediffDef", "Bleed"], capture_output=True, text=True)
_kral_hed_src = open(os.path.join(r"D:\SteamLibrary\steamapps\workshop\content\294100\3625664332\Defs", "Hediffs", "Hediffs_Various.xml"), encoding="utf-8-sig").read()
_extra_effecters = []
for _en in ("Shock", "DarkShock"):
    _em = _re.search(r'<EffecterDef>\s*<defName>%s</defName>.*?</EffecterDef>' % _en, _kral_hed_src, _re.S)
    if _em:
        _blk = _em.group(0).replace("<defName>%s</defName>" % _en, "<defName>AGM_%s</defName>" % _en)
        _blk = _blk.replace("<moteDef>Mote_AntiOrganicSparkArch</moteDef>", "<moteDef>AGM_Mote_AntiOrganicSparkArch</moteDef>")
        _extra_effecters.append(_blk)
hed = transform(raw["hediffs"] + "\n" + _r.stdout)
for h in ["ShockPain", "Inflammable", "IncendiaryBody", "VitalityDrain", "ArmorBreaker",
          "Instantkill", "HealthBlight1", "Bleed"]:
    hed = hed.replace("<defName>%s</defName>" % h, "<defName>AGM_%s</defName>" % h)
    hed = hed.replace("<hediff>%s</hediff>" % h, "<hediff>AGM_%s</hediff>" % h)
hed = hed.replace("<stateEffecter>Shock</stateEffecter>", "<stateEffecter>AGM_Shock</stateEffecter>")
hed = hed.replace("<stateEffecter>DarkShock</stateEffecter>", "<stateEffecter>AGM_DarkShock</stateEffecter>")
write("HediffDefs/HediffDefs_AGM_Kraltech.xml", "", [hed])
write("Effects/Effects_AGM_Kraltech_Shock.xml", "", _extra_effecters)
statdefs = stats
for s in STAT_NAMES:
    statdefs = statdefs.replace("<defName>%s</defName>" % s, "<defName>AGM_%s</defName>" % s)
write("StatDefs/StatDefs_AGM.xml", "", [statdefs])
write("DutyDefs/DutyDefs_AGM.xml", "", [transform(raw["duty"])])

# ---- weapons ----
wpn = transform(raw["weapons"] + raw["turrets"])
wpn = wpn.replace("<soundInteract>Interact_EnergyWeapon</soundInteract>", "<soundInteract>AGM_Interact_EnergyWeapon</soundInteract>")
write("ThingDefs_Weapon/Weapons_AGM_Kraltech.xml", "", [wpn])

# ---- sounds ----
_kral_snd = open(os.path.join(r"D:\SteamLibrary\steamapps\workshop\content\294100\3625664332\Defs", "SoundDefs", "Kraltech_Sounds.xml"), encoding="utf-8-sig").read()
_extra_sounds = []
for _sn in ("ExtinctionRay_Shooting_Resolve", "Interact_EnergyWeapon", "Shot_ToxCanister"):
    _sm = _re.search(r'<SoundDef>\s*<defName>%s</defName>.*?</SoundDef>' % _sn, _kral_snd, _re.S)
    if _sm:
        _extra_sounds.append(_sm.group(0).replace("<defName>%s</defName>" % _sn, "<defName>AGM_%s</defName>" % _sn))
snd = transform(raw["sounds"] + "\n" + "\n".join(_extra_sounds))
snd = snd.replace("<sustainStopSound>ExtinctionRay_Shooting_Resolve</sustainStopSound>", "<sustainStopSound>AGM_ExtinctionRay_Shooting_Resolve</sustainStopSound>")
write("SoundDefs/SoundDefs_AGM_Kraltech.xml", "", [snd])

# ---- effects/motes ----
kfx = load("kral_raw/flecks2.txt")
eff = transform(raw["effects"] + raw["effects2"] + raw["effects3"] + raw["motes"] + raw["motes2"] + kfx)
# remove duplicate Fleck_BlastAntiOrganicRedLine (present in effects3 twice? once) - dedupe by defName
seen = set()
out_blocks = []
for mb in re.finditer(r"<(EffecterDef|ThingDef|FleckDef)[^>]*>.*?</\1>", eff, re.S):
    b = mb.group(0)
    m = re.search(r"<defName>([^<]+)</defName>", b)
    if m and (m.group(1) in seen or m.group(1) == "AGM_Fleck_BlastAntiOrganicRedLine"):
        continue
    if m:
        seen.add(m.group(1))
    out_blocks.append(b)
write("Effects/Effects_AGM_Kraltech.xml", "", [b for b in out_blocks])

print("done")
