#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble AGM defs from Total Warfare sources: Sol (Doxa-0), Luna (Iron Bark),
Shellsplitter escort, and the two Astra variants (TW-faithful / standalone fallback)."""
import re, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "Defs"))
OUT_TW = os.path.normpath(os.path.join(HERE, "..", "Compat", "TW", "Defs"))
OUT_NOTW = os.path.normpath(os.path.join(HERE, "..", "Compat", "NoTW", "Defs"))

def load(p):
    with open(os.path.join(HERE, p), encoding="utf-8-sig") as f:
        return f.read()

def write(base, path, blocks):
    cleaned = []
    for b in blocks:
        b = re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", b, flags=re.S)
        b = re.sub(r"^\s*<Defs>\s*", "", b, flags=re.S)
        b = re.sub(r"\s*</Defs>\s*$", "", b, flags=re.S)
        cleaned.append(b)
    full = '<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n\n' + "\n".join(cleaned) + "\n\n</Defs>\n"
    p = os.path.join(base, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(full)
    print("wrote", path, len(full))

AGM_STATS = ("<MechEnergyUsageFactor>0</MechEnergyUsageFactor>\n"
             "      <WastepacksPerRecharge>0</WastepacksPerRecharge>\n"
             "      <MechEnergyLossPerHP>0</MechEnergyLossPerHP>\n"
             "      <BandwidthCost>%s</BandwidthCost>")
AGM_COMPS = ('      <li Class="AGM.CompProperties_IgnoreMechanitorCommandRange" />\n'
             '      <li Class="AGM.CompProperties_DisableFeral" />\n')

def inject_stats(text, bw):
    m = re.search(r"<statBases>\n", text)
    if m:
        text = text[:m.end()] + "      " + AGM_STATS % bw + text[m.end():]
    text = re.sub(r"<BandwidthCost[^>]*>[^<]*</BandwidthCost>", "", text, count=0)
    # remove any other BandwidthCost lines (ours is first)
    lines = text.split("\n")
    seen = False
    out = []
    for ln in lines:
        if "<BandwidthCost" in ln:
            if seen:
                continue
            seen = True
        out.append(ln)
    return "\n".join(out)

def inject_comps(text):
    return re.sub(r"(<comps[^>]*>\n)", r"\1" + AGM_COMPS, text, count=1)

def set_weight(text, wc):
    if "<mechWeightClass>" in text:
        return re.sub(r"<mechWeightClass>[^<]*</mechWeightClass>",
                      "<mechWeightClass>%s</mechWeightClass>" % wc, text)
    return re.sub(r"(<baseBodySize>[^<]*</baseBodySize>)",
                  r"\1\n      <mechWeightClass>%s</mechWeightClass>" % wc, text, count=1)

def gfx(tex, size, shadow=True):
    sh = ("\n          <shadowData>\n            <volume>(0.7, 0.8, 0.7)</volume>\n          </shadowData>") if shadow else ""
    return ('    <lifeStages>\n      <li>\n        <bodyGraphicData>\n'
            '          <texPath>%s</texPath>\n          <shaderType>Cutout</shaderType>\n'
            '          <graphicClass>Graphic_Multi</graphicClass>\n'
            '          <drawSize>%s</drawSize>%s\n'
            '        </bodyGraphicData>\n      </li>\n    </lifeStages>' % (tex, size, sh))

def strip_block(text, pattern):
    return re.sub(pattern, "", text, flags=re.S)

def remove_comp_li(text, class_prefix):
    """Remove a balanced <li Class="prefix..."> ... </li> block, honouring nested <li> elements."""
    out = []
    pos = 0
    while True:
        m = re.search(r'\s*<li Class="%s[^"]*"' % re.escape(class_prefix), text[pos:])
        if not m:
            out.append(text[pos:])
            break
        start = pos + m.start()
        # walk forward counting <li and </li>
        depth = 0
        idx = start
        for tag in re.finditer(r"<li\b|</li>", text[start:]):
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

# ---------------- SOL (Doxa-0) ----------------
doxa = load("tw_raw/doxa_thing.txt")
doxa_thing = re.search(r'<ThingDef Name="TWMechDoxa".*?</ThingDef>', doxa, re.S).group(0)
spider_thing = re.search(r'<ThingDef ParentName="LightMechanoid">\s*<defName>TW_Mech_Shellsplitter_Spider</defName>.*?</ThingDef>', doxa, re.S).group(0)
kinds = load("tw_raw/doxa_kind.txt")
doxa_kind = re.search(r'<PawnKindDef Name="TWMechDoxaKind".*?</PawnKindDef>', kinds, re.S).group(0)
spider_kind = re.search(r'<PawnKindDef ParentName="LightMechanoidKind">\s*<defName>TW_Mech_Shellsplitter_Spider</defName>.*?</PawnKindDef>', kinds, re.S).group(0)

sol_thing = doxa_thing
sol_thing = strip_block(sol_thing, r'\s*<li Class="CompProperties_AutoMechSpawner"[^>]*/>')
sol_thing = remove_comp_li(sol_thing, 'NCL.CompProperties_AllDead')
sol_thing = sol_thing.replace('<li Class="NCL.CompProperties_MechanoidShield">\n    </li>',
    '<li Class="CompProperties_Shield" />')
sol_thing = sol_thing.replace('<li Class="NCL.CompProperties_MechanoidShield"></li>',
    '<li Class="CompProperties_Shield" />')
sol_thing = strip_block(sol_thing, r'\s*<killedLeavingsPlayerHostile>.*?</killedLeavingsPlayerHostile>')
sol_thing = sol_thing.replace("<thinkTreeMain>DoxaThinkTreeMain</thinkTreeMain>", "")
sol_thing = sol_thing.replace("<defName>TW_Mech_Doxa</defName>", "<defName>AGM_Sol</defName>")
sol_thing = sol_thing.replace(' Name="TWMechDoxa"', '')
sol_thing = sol_thing.replace("<body>Doxa0Body</body>", "<body>AGM_Sol_Body</body>")
sol_thing = sol_thing.replace("<label>Doxa</label>", "<label>Sol</label>")
sol_thing = sol_thing.replace("<spawnPawnKind>TW_Mech_Shellsplitter_Spider</spawnPawnKind>", "<spawnPawnKind>AGM_Shellsplitter</spawnPawnKind>")
# shield stats so vanilla CompProperties_Shield has values
sol_thing = sol_thing.replace("      <PsychicSensitivity>0</PsychicSensitivity>",
    "      <PsychicSensitivity>0</PsychicSensitivity>\n      <EnergyShieldEnergyMax>10</EnergyShieldEnergyMax>\n      <EnergyShieldRechargeRate>0.1</EnergyShieldRechargeRate>")
sol_thing = re.sub(r"<li>\s*<def>MechanoidFullyFormed</def>\s*<minAge>100</minAge>.*?</li>", "", sol_thing, flags=re.S)
sol_thing = re.sub(r"\s*<MechEnergyLossPerHP[^>]*>0\.2</MechEnergyLossPerHP>", "", sol_thing)
sol_thing = inject_stats(sol_thing, 3)
sol_thing = set_weight(sol_thing, "Heavy")
sol_thing = inject_comps(sol_thing)

sol_kind = doxa_kind
sol_kind = sol_kind.replace("<defName>TW_Mech_Doxa_Kind</defName>", "<defName>AGM_Sol</defName>")
sol_kind = sol_kind.replace(' Name="TWMechDoxaKind"', '')
sol_kind = re.sub(r"\s*<isBoss>true</isBoss>", "", sol_kind)

sol_kind = sol_kind.replace("<label>Doxa</label>", "<label>Sol</label>")
sol_kind = sol_kind.replace("<race>TW_Mech_Doxa</race>", "<race>AGM_Sol</race>")
sol_kind = sol_kind.replace("<race>AGM_Sol</race>",
                            "<race>AGM_Sol</race>\n      <defaultFactionType>PlayerColony</defaultFactionType>")
sol_kind = re.sub(r"<lifeStages>.*?</lifeStages>", gfx("Things/Mechanoid/Sol", "5.5"), sol_kind, flags=re.S)
sol_kind = sol_kind.replace("<li>TW_Antiparticle_Rail_Mortar</li>", "<li>AGM_SolRailMortar</li>")

sp = spider_thing + spider_kind
sp = sp.replace("<defName>TW_Mech_Shellsplitter_Spider</defName>", "<defName>AGM_Shellsplitter</defName>")
sp = sp.replace("<race>TW_Mech_Shellsplitter_Spider</race>", "<race>AGM_Shellsplitter</race>")
sp = sp.replace("<label>Shellsplitter</label>", "<label>Shellsplitter</label>")
sp = sp.replace("<labelPlural>裂壳蛛</labelPlural>", "<labelPlural>shellsplitters</labelPlural>")
sp = sp.replace("<explosiveDamageType>TW_Antiparticle_explosion</explosiveDamageType>",
                "<explosiveDamageType>AGM_Damage_Antiparticle</explosiveDamageType>")
sp = re.sub(r"<li>MeleeWeapon_Shellsplitter</li>", "", sp)
sp = re.sub(r"<lifeStages>.*?</lifeStages>", gfx("Things/Mechanoid/Clawdsplitter_Spider", "3"), sp, flags=re.S, count=1)
sp = re.sub(r"<li>\s*<def>MechanoidFullyFormed</def>\s*<minAge>100</minAge>.*?</li>", "", sp, flags=re.S)
sp = inject_stats(sp, 1)
sp = inject_comps(sp)

write(OUT, "ThingDefs_Races/Races_AGM_Sol.xml", [sol_thing, sol_kind, sp])

# ---------------- LUNA (Iron Bark) ----------------
ib = load("tw_raw/ironbark_thing.txt")
ibk = load("tw_raw/ironbark_kind.txt")
ibh = load("tw_raw/ironbark_hediff.txt")
ibg = load("tw_raw/ironbark_giverset.txt")

luna = ib
luna = luna.replace("<defName>NCL_Mech_Ironbark</defName>", "<defName>AGM_Luna</defName>")
luna = luna.replace("<label>Ironbark</label>", "<label>Luna</label>")
luna = luna.replace("<body>NCL_Mech_IronbarkBody</body>", "<body>AGM_Luna_Body</body>")
luna = luna.replace("<def>NCL_Mech_IronbarkFullyformed</def>", "<def>MechanoidFullyFormed</def>")
luna = remove_comp_li(luna, 'NCL.CompProperties_AntiInvisibilityField')
luna = remove_comp_li(luna, 'NyarsModPackOne.ModExtension_EffecterOnMelee')
luna = luna.replace("<hediff>NCL_Mech_Ironbark_Hediff</hediff>", "<hediff>AGM_Luna_Hediff</hediff>")
# silent bark hediff: no HediffGiverSet (it fired a health-condition letter);
# AGM.CompProperties_EnsureHediff applies it on spawn without notifications.
luna = re.sub(r"\s*<hediffGiverSets>.*?</hediffGiverSets>", "", luna, flags=re.S)
luna = luna.replace("NCL_Mech_Ironbark_Introduction", "AGM_Luna_Introduction")
luna = inject_stats(luna, 2)
luna = set_weight(luna, "Medium")
luna = inject_comps(luna)
luna = luna.replace('<li Class="AGM.CompProperties_DisableFeral" />',
                    '<li Class="AGM.CompProperties_DisableFeral" />\n'
                    '      <li Class="AGM.CompProperties_EnsureHediff">\n'
                    '        <hediff>AGM_Luna_Hediff</hediff>\n'
                    '      </li>')

luna_kind = ibk
luna_kind = luna_kind.replace("<defName>NCL_Mech_Ironbark_Kind</defName>", "<defName>AGM_Luna</defName>")
luna_kind = luna_kind.replace("<label>Ironbark</label>", "<label>Luna</label>")
luna_kind = luna_kind.replace("<race>NCL_Mech_Ironbark</race>", "<race>AGM_Luna</race>")
luna_kind = re.sub(r"\s*<defaultFactionType>[^<]*</defaultFactionType>", "", luna_kind)
luna_kind = re.sub(r"<lifeStages>.*?</lifeStages>", gfx("Things/Mechanoid/Luna", "4.5"), luna_kind, flags=re.S)
luna_kind = strip_block(luna_kind, r"\s*<abilities>\s*<li>Ironbark_Explosion</li>\s*</abilities>")

luna_hediff = ibh.replace("<defName>NCL_Mech_Ironbark_Hediff</defName>", "<defName>AGM_Luna_Hediff</defName>")
luna_hediff = luna_hediff.replace("<label>NCL: Ironbark</label>", "<label>Luna Bark</label>")
luna_hediff = luna_hediff.replace(
    '<li Class="NCL.HediffCompProperties_MechAutoRecovery">\n        <tickMultiflier>180</tickMultiflier>\n        <healPoint>5</healPoint>\n      </li>',
    '<li Class="AGM.HediffCompProperties_AutoRepair">\n        <tickInterval>180</tickInterval>\n        <healAmount>5</healAmount>\n      </li>')
luna_hediff = strip_block(luna_hediff, r"\s*<modExtensions>\s*<li Class=""NCL\.HediffExtension_NoNotification"" /></modExtensions>")
luna_hediff = strip_block(luna_hediff, r'\s*<modExtensions>\s*<li Class="NCL\.HediffExtension_NoNotification"\s*/>\s*</modExtensions>')


write(OUT, "ThingDefs_Races/Races_AGM_Luna.xml", [luna, luna_kind])
write(OUT, "HediffDefs/HediffDefs_AGM_Luna.xml", [luna_hediff])

# ---------------- Doxa body + Iron bark body ----------------
doxa_body = load("tw_raw/doxa_body.txt")
doxa_parts = load("tw_raw/doxa_parts.txt")
ib_body = load("tw_raw/ironbark_body.txt")
ib_parts = load("tw_raw/ironbark_parts_all.txt")

def ren(text, old, new):
    return text.replace(old, new)

doxa_body = ren(doxa_body, "<defName>Doxa0Body</defName>", "<defName>AGM_Sol_Body</defName>")
doxa_body = re.sub(r"Doxa0_(DeepLogic_NeuronCore|Turret_Mount|AntiParticleEmitter|Hatch_Module|Sensor_Cluster|FireControlModule|LimbCluster|Dorsal_First|Dorsal_Second|Dorsal_Third|Dorsal_Fourth)",
                   r"AGM_Sol_\1", doxa_body)
doxa_parts = re.sub(r"<defName>Doxa0_(DeepLogic_NeuronCore|Turret_Mount|AntiParticleEmitter|Hatch_Module|Sensor_Cluster|FireControlModule|LimbCluster|Dorsal_First|Dorsal_Second|Dorsal_Third|Dorsal_Fourth)</defName>",
                    r"<defName>AGM_Sol_\1</defName>", doxa_parts)
ib_body = ren(ib_body, "<defName>NCL_Mech_IronbarkBody</defName>", "<defName>AGM_Luna_Body</defName>")
for part in ["IronbarkCanopy","IronbarkCore","ThermalSensor","GreekFireNozzle","HydraulicCrusher",
             "FusionReactor","PhaseShieldCore","RootJoint","IronbarkTrunk","IronbarkMidTrunk",
             "IronbarkLowerTrunk","IronbarkBaseTrunk","IronbarkRootHub","InfernoEmitter","InfernoSystem"]:
    ib_body = ren(ib_body, "<def>%s</def>" % part, "<def>AGM_Luna_%s</def>" % part)
    ib_parts = ren(ib_parts, "<defName>%s</defName>" % part, "<defName>AGM_Luna_%s</defName>" % part)
# inline TW abstract bodypart parents (Doxa0Dorsal, IronbarkDorsalBase)
tw_bp_src = open(r"D:\SteamLibrary\steamapps\workshop\content\294100\3555799437\1.6\Defs\Bodies\Bodies_Doxa.xml", encoding="utf-8-sig").read()
tw_bp_src += open(r"D:\SteamLibrary\steamapps\workshop\content\294100\3555799437\1.6\Defs\Bodies\Bodies_IronRoot.xml", encoding="utf-8-sig").read()
_bp_parents2 = {}
for _m in re.finditer(r'<BodyPartDef[^>]*Abstract="True"[^>]*Name="([^"]+)">(.*?)</BodyPartDef>', tw_bp_src, re.S):
    _bp_parents2[_m.group(1)] = _m.group(2)
def _inline_bp2(m):
    pname, inner = m.group(1), m.group(2)
    pin = _bp_parents2[pname]
    if pname not in _bp_parents2:
        return m.group(0)
    child_tags = set(re.findall(r"<(\w+)[^>]*>", inner))
    add = []
    for fbm in re.finditer(r"<(\w+)[^>]*>.*?</\1>", pin, re.S):
        fb = fbm.group(0)
        tag = fbm.group(1)
        if tag not in child_tags:
            add.append("    " + fb)
    joined = ("\n" + "\n".join(add) + "\n" + inner) if add else inner
    return "<BodyPartDef>" + joined + "</BodyPartDef>"
doxa_parts = re.sub(r'<BodyPartDef ParentName="([^"]+)">(.*?)</BodyPartDef>', _inline_bp2, doxa_parts, flags=re.S)
ib_parts = re.sub(r'<BodyPartDef ParentName="([^"]+)">(.*?)</BodyPartDef>', _inline_bp2, ib_parts, flags=re.S)
# drop dangling InfernoSystem group reference (undefined even in Total Warfare)
doxa_body = doxa_body.replace("<li>InfernoSystem</li>", "")
doxa_parts = doxa_parts.replace("<li>InfernoSystem</li>", "")
ib_body = ib_body.replace("<li>InfernoSystem</li>", "")
ib_parts = ib_parts.replace("<li>InfernoSystem</li>", "")
write(OUT, "Bodies/Bodies_AGM_TW.xml", [doxa_body, doxa_parts, ib_body, ib_parts])

# ---------------- Sol weapon + shells + damage ----------------
wpn = load("tw_raw/doxa_weapon.txt")
rail = re.search(r'<ThingDef[^>]*>\s*<defName>TW_Antiparticle_Rail_Mortar</defName>.*?</ThingDef>', wpn, re.S).group(0)
shell = re.search(r'<ThingDef[^>]*>\s*<defName>Shell_TW_Antiparticle_Rail_Mortar</defName>.*?</ThingDef>', wpn, re.S).group(0)
rail = rail.replace("<defName>TW_Antiparticle_Rail_Mortar</defName>", "<defName>AGM_Gun_SolRailMortar</defName>")
rail = re.sub(r"<statBases>\n", "<statBases>\n      <MarketValue>8000</MarketValue>\n", rail, count=1)
rail = rail.replace("MarketValue>8000\n\n", "MarketValue>8000\n")
rail = rail.replace("Shell_TW_Antiparticle_Rail_Mortar", "AGM_Shell_SolRailMortar")
rail = rail.replace("<verbClass>NCL.Verb_AdvancedShoot</verbClass>", "<verbClass>Verb_Shoot</verbClass>")
rail = re.sub(r'\s*<comps>\s*<li Class="NCL\.CompProperties_AdvancedAmmo">.*?</li>\s*</comps>', "", rail, flags=re.S)
rail = rail.replace("<uiIconPath>ModIcon/Antiparticle_Rail_Mortar</uiIconPath>",
                    "<uiIconPath>Things/Building/Production/MechGestatorLarge_MenuIcon</uiIconPath>")
rail = re.sub(r"<weaponTags[^>]*>.*?</weaponTags>", "<weaponTags>\n      <li>AGM_SolRailMortar</li>\n    </weaponTags>", rail, flags=re.S)
shell = shell.replace("<defName>Shell_TW_Antiparticle_Rail_Mortar</defName>", "<defName>AGM_Shell_SolRailMortar</defName>")
shell = re.sub(r'<modExtensions>\s*<li Class="NCLProjectiles\.ModExtension_ProjectileEffects">.*?</li>\s*</modExtensions>', "", shell, flags=re.S)
shell = re.sub(r'<li Class="NCLProjectiles\.ModExtension_ProjectileEffects">.*?</li>', "", shell, flags=re.S)
shell = shell.replace("<thingClass>NCLProjectiles.Projectile_ExplosiveStagedWithEffects</thingClass>", "<thingClass>Projectile_Explosive</thingClass>")
shell = shell.replace("<damageDef>TW_Antiparticle_explosion</damageDef>", "<damageDef>AGM_Damage_Antiparticle</damageDef>")
rail = rail.replace("<damageDef>TW_Antiparticle_explosion</damageDef>", "<damageDef>AGM_Damage_Antiparticle</damageDef>")
rail = rail.replace("<explosiveDamageType>TW_Antiparticle_explosion</explosiveDamageType>", "<explosiveDamageType>AGM_Damage_Antiparticle</explosiveDamageType>")
rail = remove_comp_li(rail, "NCL")
rail = remove_comp_li(rail, "NCLProjectiles")
shell = remove_comp_li(shell, "NCL")
shell = remove_comp_li(shell, "NCLProjectiles")
blast = load("tw_raw/doxa_blast.txt").replace("<defName>TW_Antiparticle_explosion</defName>",
                                              "<defName>AGM_Damage_Antiparticle</defName>")
write(OUT, "ThingDefs_Weapon/Weapons_AGM_Sol.xml", [rail, shell])
write(OUT, "DamageDefs/DamageDefs_AGM_TW.xml", [blast])

# ---------------- Astra: TW-faithful variant ----------------
worm_thing = re.search(r'<ThingDef ParentName="BaseMechanoid">\s*<defName>NCL_MechWorm</defName>.*?</ThingDef>',
                       load("tw_raw/worm_thing.txt"), re.S).group(0)
worm_kind = load("tw_raw/worm_kind.txt")

astra = worm_thing
astra = astra.replace("<defName>NCL_MechWorm</defName>", "<defName>AGM_Astra</defName>")
astra = astra.replace("<label>ArchoWorm</label>", "<label>Astra</label>")
astra = astra.replace("<label>逆鳞</label>", "<label>reverse scale</label>")
astra = astra.replace("Races/NCLMechWorm_south", "Things/Mechanoid/Astra")
astra = astra.replace("<BandwidthCost>200</BandwidthCost>", "<BandwidthCost>4</BandwidthCost>")
astra = astra.replace("<ControlTakingTime>999</ControlTakingTime>", "<ControlTakingTime>30</ControlTakingTime>")
astra = astra.replace("<MarketValue>5</MarketValue>", "<MarketValue>12000</MarketValue>")
astra = remove_comp_li(astra, 'NCL.CompProperties_TurretGunPawnOnly')
# TW's NCL_Pawn_Worm is driven by TW's own garrison system and ignores vanilla mechanitor
# ownership - use the vanilla Pawn class so Astra behaves like a regular controllable mech.
# The TW comps/abilities are plain ThingComps/AbilityDefs and attach fine to a vanilla pawn.
astra = re.sub(r"\s*<thingClass>NCLWorm\.NCL_Pawn_Worm</thingClass>", "", astra)
astra = strip_block(astra, r"\s*<killedLeavingsPlayerHostile>.*?</killedLeavingsPlayerHostile>")
# pawn defs must not carry a ThingDef-level graphicData: it is a Graphic_Single and would
# try to load Things/Mechanoid/Astra.png (only _east/_north/_south exist for the PawnKind).
astra = re.sub(r"\s*<graphicData>\s*<texPath>Things/Mechanoid/Astra</texPath>\s*<graphicClass>Graphic_Single</graphicClass>\s*<drawSize>0\.80</drawSize>\s*</graphicData>", "", astra)
astra = inject_stats(astra, 4)
astra = inject_comps(astra)
# <comps Inherit="False"> on the worm dropped BaseMechanoid's overseer-subject and
# mech-repairable comps - without them the mechanitor cannot take Astra over at all.
OVERSEER_COMPS = (
    '      <li Class="CompProperties_OverseerSubject">\n'
    '        <needsOverseerEffect>MechUncontrolled</needsOverseerEffect>\n'
    '        <delayUntilFeralCheck>60000</delayUntilFeralCheck>\n'
    '        <feralMtbDays>10</feralMtbDays>\n'
    '        <feralCascadeRadialDistance>25</feralCascadeRadialDistance>\n'
    '      </li>\n'
    '      <li Class="CompProperties_MechRepairable" />\n')
astra = astra.replace('<li Class="AGM.CompProperties_DisableFeral" />',
                      '<li Class="AGM.CompProperties_DisableFeral" />\n' + OVERSEER_COMPS)

astra_kind = worm_kind
astra_kind = astra_kind.replace("<defName>NCL_MechWorm</defName>", "<defName>AGM_Astra</defName>")
astra_kind = astra_kind.replace("<label>ArchoWorm</label>", "<label>Astra</label>")
astra_kind = astra_kind.replace("<race>NCL_MechWorm</race>", "<race>AGM_Astra</race>")
astra_kind = re.sub(r"\s*<defaultFactionType>[^<]*</defaultFactionType>", "", astra_kind)
astra_kind = re.sub(r"\s*<isBoss>true</isBoss>", "", astra_kind)
astra_kind = re.sub(r"<lifeStages>.*?</lifeStages>", gfx("Things/Mechanoid/Astra", "12"), astra_kind, flags=re.S)
astra_kind = astra_kind.replace("<race>AGM_Astra</race>",
                                "<race>AGM_Astra</race>\n    <defaultFactionType>PlayerColony</defaultFactionType>")

# TW branch references TW's own defs (WormPressure hediff, NCL_ModBomb damage, worm abilities,
# NCL_Gun_* weapon pool) - they all exist when Total Warfare is loaded, so no copies are made.
write(OUT_TW, "ThingDefs_Races/Races_AGM_AstraTW.xml", [astra, astra_kind])

# ---------------- Astra: standalone fallback variant ----------------
worm_body = load("tw_raw/worm_body.txt").replace("<defName>NCLWormBody</defName>", "<defName>AGM_WormBody</defName>")

astra2 = astra
# de-TW: replace custom classes with vanilla equivalents
astra2 = astra2.replace("<thingClass>NCLWorm.NCL_Pawn_Worm</thingClass>\n", "")
astra2 = astra2.replace("<body>NCLWormBody</body>", "<body>AGM_WormBody</body>")
astra2 = astra2.replace("<thinkTreeConstant>MechWormConstant</thinkTreeConstant>", "")
astra2 = strip_block(astra2, r"\s*<deathAction>\s*<workerClass>NCLWorm\.DeathActionWorker_EndWar</workerClass>\s*</deathAction>")
# comps: drop every NCL/NCLWorm/TowerLaserDefense comp, keep vanilla ones
astra2 = remove_comp_li(astra2, 'NCL.CompProperties_MechAutoRecovery')
astra2 = remove_comp_li(astra2, 'NCLWorm.CompProperties_BattleCrush')
astra2 = remove_comp_li(astra2, 'NCL.CompProperties_DamageLimit')
astra2 = remove_comp_li(astra2, 'NCLWorm.CompProperties_CauseHediff_AoEAndRing')
astra2 = remove_comp_li(astra2, 'NCLWorm.CompProperties_DamageAbsorbedAndBoom')
astra2 = remove_comp_li(astra2, 'NCL.CompProperties_MechanoidShield')
astra2 = remove_comp_li(astra2, 'NCLWorm.CompProperties_ShieldNCLWorm')
astra2 = remove_comp_li(astra2, 'NCLWorm.CompProperties_NCLWormSkillList')
astra2 = remove_comp_li(astra2, 'NCL.CompProperties_WeaponGiver')
astra2 = remove_comp_li(astra2, 'TowerLaserDefense.CompProperties_LaserDefence')
# vanilla shield + big HP regen substitute: use vanilla shield comp
astra2 = astra2.replace(AGM_COMPS,
    AGM_COMPS + '      <li Class="CompProperties_Shield" />\n')
# modExtension with NyarsModPackOne class - drop
astra2 = remove_comp_li(astra2, 'NyarsModPackOne.ModExtension_EffecterOnMelee')
astra2 = re.sub(r"\s*<modExtensions>\s*</modExtensions>", "", astra2)
astra2 = astra2.replace("<damageDef>Stun</damageDef>", "<damageDef>Stun</damageDef>")

astra2_kind = astra_kind
astra2_kind = astra2_kind.replace("<li>NCLJumpWithBomb</li>", "<li>LongjumpMech</li>")
astra2_kind = re.sub(r"\s*<li>NCLBurrowAttack</li>", "", astra2_kind)
astra2_kind = re.sub(r"\s*<li>NCLPush</li>", "", astra2_kind)
astra2_kind = re.sub(r"\s*<li>NCLBeckon</li>", "", astra2_kind)
astra2_kind = re.sub(r"\s*<li>NCLChaosTeleport</li>", "", astra2_kind)
astra2_kind = re.sub(r"\s*<isBoss>true</isBoss>", "", astra2_kind)

write(OUT_NOTW, "ThingDefs_Races/Races_AGM_Astra.xml", [astra2, astra2_kind])
write(OUT_NOTW, "Bodies/Body_AGM_Worm.xml", [worm_body])
print("done")
