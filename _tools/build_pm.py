#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble AGM defs from ProtossMechPersonaHero / ProtossMechPurifier sources:
Argon (Warbringer), Flash (Taldarin) + their weapons, bodies and damage def.
Includes the ProtossMechanoid abstract inheritance (thinkTreeMain, intelligence,
head melee tool, base stats) that is lost when re-parenting to BaseMechanoid."""
import re, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "Defs"))

def load(p):
    with open(os.path.join(HERE, p), encoding="utf-8-sig") as f:
        return f.read()

def write(path, blocks):
    cleaned = []
    for b in blocks:
        b = re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", b, flags=re.S)
        cleaned.append(b)
    full = '<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n\n' + "\n".join(cleaned) + "\n\n</Defs>\n"
    p = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(full)
    print("wrote", path, len(full))

PROTOSS_HEAD_TOOL = (
    "    <tools>\n"
    "      <li>\n"
    "        <label>head</label>\n"
    "        <capacities>\n"
    "          <li>Blunt</li>\n"
    "        </capacities>\n"
    "        <power>10</power>\n"
    "        <cooldownTime>2.0</cooldownTime>\n"
    "        <linkedBodyPartsGroup>HeadAttackTool</linkedBodyPartsGroup>\n"
    "        <ensureLinkedBodyPartsGroupAlwaysUsable>true</ensureLinkedBodyPartsGroupAlwaysUsable>\n"
    "      </li>\n"
    "    </tools>\n")

AGM_COMPS = ('      <li Class="AGM.CompProperties_IgnoreMechanitorCommandRange" />\n'
             '      <li Class="AGM.CompProperties_DisableFeral" />\n')

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

things = load("pm_raw/persona_things.txt")
kinds = load("pm_raw/persona_kinds.txt")

taldarin = re.search(r'<ThingDef ParentName="ProtossMechanoid">\s*<defName>PMPH_Taldarin</defName>.*?</ThingDef>', things, re.S).group(0)
warbringer = re.search(r'<ThingDef ParentName="ProtossMechanoid">\s*<defName>PMPH_Warbringer</defName>.*?</ThingDef>', things, re.S).group(0)
taldarin_kind = re.search(r'<PawnKindDef ParentName="ProtossMechanoidKind">\s*<defName>PMPH_Taldarin</defName>.*?</PawnKindDef>', kinds, re.S).group(0)
warbringer_kind = re.search(r'<PawnKindDef ParentName="ProtossMechanoidKind">\s*<defName>PMPH_Warbringer</defName>.*?</PawnKindDef>', kinds, re.S).group(0)

COMMON_STATS = ("<MechEnergyUsageFactor>0</MechEnergyUsageFactor>\n"
                "      <WastepacksPerRecharge>0</WastepacksPerRecharge>\n"
                "      <MechEnergyLossPerHP>0</MechEnergyLossPerHP>\n"
                "      <EMPResistance>1.0</EMPResistance>\n"
                "      <StaggerDurationFactor>0</StaggerDurationFactor>\n"
                "      <BandwidthCost>%s</BandwidthCost>")
PROTOSS_STATS = ("      <PsychicSensitivity>0</PsychicSensitivity>\n"
                 "      <ControlTakingTime>30</ControlTakingTime>\n"
                 "      <WorkSpeedGlobal>1.0</WorkSpeedGlobal>\n"
                 "      <MarketValue>1000</MarketValue>\n")

def make_mech(thing, kind, newname, bw, weight, tex, shield_max):
    t = thing
    t = t.replace('ParentName="ProtossMechanoid"', 'ParentName="BaseMechanoid"')
    t = t.replace("<defName>PMPH_Taldarin</defName>", "<defName>AGM_Flash</defName>")
    t = t.replace("<defName>PMPH_Warbringer</defName>", "<defName>AGM_Argon</defName>")
    t = re.sub(r"<BandwidthCost>[^<]*</BandwidthCost>", "", t)
    # stats: common + protoss-abstract blocks
    t = re.sub(r"<statBases>\n", "<statBases>\n      " + COMMON_STATS % bw + "\n", t, count=1)
    t = re.sub(r"<statBases>\n", "<statBases>\n" + PROTOSS_STATS, t, count=1)
    t = re.sub(r"<mechWeightClass>[^<]*</mechWeightClass>",
               "<mechWeightClass>%s</mechWeightClass>" % weight, t)
    t = t.replace("<body>PMP_ImmortalBody</body>", "<body>AGM_Flash_Body</body>")
    t = t.replace("<body>PMP_ColossusBody</body>", "<body>AGM_Argon_Body</body>")
    # protoss shield -> vanilla shield comp
    t = re.sub(r'<li Class="ProtossMech\.CompProperties_ProtossMechShield">.*?</li>',
               '<li Class="CompProperties_Shield" />', t, flags=re.S)
    t = t.replace("PMP_Persona.CompProperties_NeverDowned", "AGM.CompProperties_NeverDowned")
    t = remove_comp_li(t, "ProtossMech.CompProperties_MultiTurretGun")
    t = t.replace("</comps>", '      <li Class="CompProperties_TurretGun">\n'
               '        <turretDef>AGM_Turret_PurificationBlast</turretDef>\n'
               '        <angleOffset>-90</angleOffset>\n'
               '      </li>\n    </comps>', 1)
    t = t.replace("<NeutronMaterial>125</NeutronMaterial>", "<Steel>80</Steel>\n      <Plasteel>60</Plasteel>")
    t = t.replace("<NeutronMaterial>150</NeutronMaterial>", "<Steel>100</Steel>\n      <Plasteel>80</Plasteel>")
    # energy shield stats for the vanilla shield comp
    t = re.sub(r"(<ArmorRating_Sharp>[^<]*</ArmorRating_Sharp>)",
               r"\1\n      <EnergyShieldEnergyMax>%s</EnergyShieldEnergyMax>\n      <EnergyShieldRechargeRate>0.25</EnergyShieldRechargeRate>" % shield_max,
               t, count=1)
    t = re.sub(r"(<comps>\n)", r"\1" + AGM_COMPS, t, count=1)
    # fields the ProtossMechanoid abstract used to provide (lost when re-parenting)
    t = re.sub(r"(<race>\n)", r"\1      <intelligence>ToolUser</intelligence>\n      <thinkTreeMain>Mechanoid</thinkTreeMain>\n", t, count=1)
    if "<tools>" not in t:
        t = t.replace("<comps>", PROTOSS_HEAD_TOOL + "    <comps>", 1)

    k = kind
    k = k.replace('ParentName="ProtossMechanoidKind"', 'ParentName="BaseMechanoidKind"')
    k = k.replace("<defName>PMPH_Taldarin</defName>", "<defName>AGM_Flash</defName>")
    k = k.replace("<defName>PMPH_Warbringer</defName>", "<defName>AGM_Argon</defName>")
    k = k.replace("<race>PMPH_Taldarin</race>", "<race>AGM_Flash</race>")
    k = k.replace("<race>PMPH_Warbringer</race>", "<race>AGM_Argon</race>")
    k = k.replace("<texPath>Things/Pawn/Mechanoid/Taldarin</texPath>", "<texPath>%s</texPath>" % tex)
    k = k.replace("<texPath>Things/Pawn/Mechanoid/Warbringer</texPath>", "<texPath>%s</texPath>" % tex)
    k = k.replace("<li>Gun_Taldarin</li>", "<li>AGM_GunTaldarin</li>")
    k = k.replace("<li>ThermalLances</li>", "<li>AGM_ThermalLances</li>")
    k = re.sub(r"\s*<abilities>\s*<li>PMP_RestoreShield</li>\s*</abilities>", "", k)
    return t, k

ft, fk = make_mech(taldarin, taldarin_kind, "AGM_Flash", 2, "Medium", "Things/Mechanoid/Flash", "8")
at, ak = make_mech(warbringer, warbringer_kind, "AGM_Argon", 3, "Heavy", "Things/Mechanoid/Argon", "12")

# Flash loses its PMP_RestoreShield ability; give it the vanilla smokepop for utility parity.
fk = fk.replace("    <weaponTags>", "    <abilities>\n      <li>SmokepopMech</li>\n    </abilities>\n    <weaponTags>")

write("ThingDefs_Races/Races_AGM_Flash.xml", [ft, fk])
write("ThingDefs_Races/Races_AGM_Argon.xml", [at, ak])

# ---------------- bodies ----------------
bodies = load("pm_raw/bodies.txt")
giant = load("pm_raw/giantparts.txt")
bodies = bodies.replace("<defName>PMP_ColossusBody</defName>", "<defName>AGM_Argon_Body</defName>")
bodies = bodies.replace("<defName>PMP_ImmortalBody</defName>", "<defName>AGM_Flash_Body</defName>")
for part in ["GiantMechanicalLeg", "GiantMechanicalJoint"]:
    bodies = bodies.replace("<def>%s</def>" % part, "<def>AGM_%s</def>" % part)
    giant = giant.replace("<defName>%s</defName>" % part, "<defName>AGM_%s</defName>" % part)
write("Bodies/Bodies_AGM_PM.xml", [bodies, giant])

# ---------------- weapons ----------------
wpn = load("pm_raw/taldarin_weapon.txt")
thermal = load("pm_raw/thermal.txt")

gun_tal = re.search(r'<ThingDef ParentName="BaseGun">\s*<defName>Gun_Taldarin</defName>.*?</ThingDef>', wpn, re.S).group(0)
turret = re.search(r'<ThingDef ParentName="BaseWeaponTurret">\s*<defName>turretgun_PurificationBlast</defName>.*?</ThingDef>', wpn, re.S).group(0)
proj = re.search(r'<ThingDef ParentName="BaseBullet">\s*<defName>PMPH_PurificationBlastProjectile</defName>.*?</ThingDef>', wpn, re.S).group(0)
mote = re.search(r'<ThingDef ParentName="MoteBase">\s*<defName>PMPHMote_PurificationBlast</defName>.*?</ThingDef>', wpn, re.S).group(0)

gun_tal = gun_tal.replace("<defName>Gun_Taldarin</defName>", "<defName>AGM_Gun_FlashPulse</defName>")
gun_tal = re.sub(r'\s*<comps>\s*<li Class="PMP_Persona\.CompProperties_DamageConfig">.*?</li>\s*</comps>', "", gun_tal, flags=re.S)
gun_tal = gun_tal.replace("<verbClass>PMP_Persona.Verb_GravityPulse</verbClass>", "<verbClass>Verb_Shoot</verbClass>")
gun_tal = gun_tal.replace("<defaultProjectile>Bullet_NeedleGun</defaultProjectile>", "<defaultProjectile>AGM_Bullet_FlashPulse</defaultProjectile>")
gun_tal = gun_tal.replace("<li>Gun_Taldarin</li>", "<li>AGM_GunTaldarin</li>")

flash_bullet = ('  <ThingDef ParentName="BaseBullet">\n'
                '    <defName>AGM_Bullet_FlashPulse</defName>\n'
                '    <label>flash pulse</label>\n'
                '    <graphicData>\n'
                '      <texPath>Things/Projectile/Needle</texPath>\n'
                '      <graphicClass>Graphic_Single</graphicClass>\n'
                '      <drawSize>1.3</drawSize>\n'
                '    </graphicData>\n'
                '    <projectile>\n'
                '      <damageDef>AGM_Damage_AntiArmorShock</damageDef>\n'
                '      <damageAmountBase>20</damageAmountBase>\n'
                '      <armorPenetrationBase>1.2</armorPenetrationBase>\n'
                '      <stoppingPower>1.5</stoppingPower>\n'
                '      <speed>90</speed>\n'
                '    </projectile>\n'
                '  </ThingDef>')

turret = turret.replace("<defName>turretgun_PurificationBlast</defName>", "<defName>AGM_Turret_PurificationBlast</defName>")
turret = turret.replace("<verbClass>PMP_Persona.Verb_ApplyDebuff</verbClass>", "<verbClass>Verb_Shoot</verbClass>")
turret = turret.replace("<defaultProjectile>Bullet_NeedleGun</defaultProjectile>", "<defaultProjectile>AGM_PurificationBlastProjectile</defaultProjectile>")
turret = re.sub(r'\s*<comps>\s*<li Class="PMP_Persona\.CompProperties_HediffOnHit">.*?</comps>', "", turret, flags=re.S)

proj = proj.replace("<defName>PMPH_PurificationBlastProjectile</defName>", "<defName>AGM_PurificationBlastProjectile</defName>")
proj = proj.replace("<damageAmountBase>0</damageAmountBase>", "<damageAmountBase>15</damageAmountBase>")
proj = proj.replace("<armorPenetrationBase>0</armorPenetrationBase>", "<armorPenetrationBase>0.5</armorPenetrationBase>")
proj = proj.replace("<beamMoteDef>PMPHMote_PurificationBlast</beamMoteDef>", "<beamMoteDef>AGM_Mote_PurificationBlast</beamMoteDef>")

mote = mote.replace("<defName>PMPHMote_PurificationBlast</defName>", "<defName>AGM_Mote_PurificationBlast</defName>")

thermal = thermal.replace("<defName>Gun_ThermalLances</defName>", "<defName>AGM_Gun_ThermalLances</defName>")
thermal = thermal.replace("<verbClass>ProtossMech.Verb_ShootMeltBeam</verbClass>", "<verbClass>Verb_ShootBeam</verbClass>")
thermal = thermal.replace("<li>ThermalLances</li>", "<li>AGM_ThermalLances</li>")

blast = load("pm_raw/antiararmor.txt").replace("<defName>AntiArmorShock</defName>", "<defName>AGM_Damage_AntiArmorShock</defName>")

write("ThingDefs_Weapon/Weapons_AGM_PM.xml", [thermal, gun_tal, flash_bullet, turret, proj, mote])
write("DamageDefs/DamageDefs_AGM_PM.xml", [blast])
print("done")
