#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-reference validator for the AGM mod.
Checks that every def referenced by AGM defs exists in: AGM itself, vanilla game data,
or (for Compat/TW defs only) the Total Warfare data set."""
import os, re, sys, glob
import xml.etree.ElementTree as ET

AGM = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DATA = r"D:\SteamLibrary\steamapps\common\RimWorld\Data"
TW = r"D:\SteamLibrary\steamapps\workshop\content\294100\3555799437"
KRAL = r"D:\SteamLibrary\steamapps\workshop\content\294100\3625664332"
PMP = r"D:\SteamLibrary\steamapps\workshop\content\294100\3464281098"
PH = r"D:\SteamLibrary\steamapps\workshop\content\294100\3522838904"
AB = r"D:\SteamLibrary\steamapps\workshop\content\294100\3493889625"

def collect_defnames(roots, db):
    for root in roots:
        for f in glob.glob(os.path.join(root, "**", "*.xml"), recursive=True):
            if os.path.basename(f) == "LoadFolders.xml":
                continue
            try:
                tree = ET.parse(f)
            except ET.ParseError:
                continue
            for el in tree.getroot():
                dn = el.find("defName")
                name = el.get("Name")
                if dn is not None and dn.text:
                    db.setdefault(el.tag, set()).add(dn.text)
                if name:
                    db.setdefault(el.tag, set()).add(name)

print("loading vanilla...")
van = {}
collect_defnames([os.path.join(DATA, d) for d in os.listdir(DATA) if os.path.isdir(os.path.join(DATA, d))], van)
print("  %d def types" % len(van))
tw = {}
collect_defnames([os.path.join(TW, "1.6", "Defs"), os.path.join(TW, "GD5")], tw)
kral = {}
collect_defnames([os.path.join(KRAL, "Defs"), os.path.join(KRAL, "Patches")], kral)
pmpph = {}
collect_defnames([os.path.join(PMP, "1.6", "Defs"), os.path.join(PH, "1.6", "Defs")], pmpph)
ab = {}
collect_defnames([os.path.join(AB, "1.6"), os.path.join(AB, "Common"), os.path.join(AB, "1.5")], ab)
for extra in ("Defs", "1.6"):
    p = os.path.join(AB, extra)
    if os.path.isdir(p):
        collect_defnames([p], ab)

agm = {}
collect_defnames([os.path.join(AGM, "Defs")], agm)
agm_tw = {}
collect_defnames([os.path.join(AGM, "Compat", "TW", "Defs")], agm_tw)
collect_defnames([os.path.join(AGM, "Compat", "NoTW", "Defs")], agm)

def exists(tag, name, in_tw_branch=False):
    if name is None:
        return True
    dbs = [agm, van]
    if in_tw_branch:
        dbs += [tw, agm_tw]
    dbs += [ab]
    for db in dbs:
        if name in db.get(tag, set()):
            return True
    return False

errors, warnings = [], []

def check(f, el, tag, field, reftag, tw_branch=False, optional=False):
    node = el.find(field)
    if node is None or not (node.text or "").strip():
        return
    name = node.text.strip()
    if not exists(reftag, name, tw_branch):
        (warnings if optional else errors).append("%s: <%s>%s %s '%s' not found" % (os.path.relpath(f, AGM), tag, field, reftag, name))

def check_list(f, el, tag, listpath, reftag, tw_branch=False, optional=False):
    for node in el.findall(listpath):
        name = (node.text or "").strip()
        if name and not exists(reftag, name, tw_branch):
            (warnings if optional else errors).append("%s: %s %s ref '%s' not found" % (os.path.relpath(f, AGM), tag, listpath, name))

# foreign class refs
FOREIGN = re.compile(r'Class="(NCL\.|NCLWorm\.|NCLProjectiles\.|NyarsModPackOne\.|NyarsModPackTwo\.|TowerLaserDefense\.|ProtossMech\.|PMP_Persona\.|Kraltech_Industries\.|ExoMech\.|ExoMaidnoid\.)')

for f in glob.glob(os.path.join(AGM, "Defs", "**", "*.xml"), recursive=True) + \
         glob.glob(os.path.join(AGM, "Compat", "TW", "Defs", "**", "*.xml"), recursive=True) + \
         glob.glob(os.path.join(AGM, "Compat", "NoTW", "Defs", "**", "*.xml"), recursive=True):
    tw_branch = os.sep + "Compat" + os.sep + "TW" + os.sep in f
    txt = open(f, encoding="utf-8-sig").read()
    for m in FOREIGN.finditer(txt):
        if not tw_branch:
            errors.append("%s: foreign class %s" % (os.path.relpath(f, AGM), m.group(1)))
    try:
        tree = ET.parse(f)
    except ET.ParseError as e:
        errors.append("%s: XML parse error %s" % (os.path.relpath(f, AGM), e))
        continue
    for el in tree.getroot():
        tag = el.tag
        if tag not in ("ThingDef", "PawnKindDef", "RecipeDef", "AbilityDef", "ResearchProjectDef",
                       "BodyDef", "DamageDef", "HediffDef", "SoundDef", "EffecterDef", "FleckDef",
                       "StatDef", "DutyDef", "ResearchTabDef", "ThingDef"):
            continue
        dn = el.find("defName")
        dn = dn.text if dn is not None else "?"
        # generic checks
        if tag == "ThingDef":
            dd = el.find("projectile/damageDef")
            if dd is not None and not exists("DamageDef", (dd.text or "").strip(), tw_branch):
                errors.append("%s: projectile damageDef '%s' not found" % (os.path.relpath(f, AGM), dd.text))
            b = el.find("race/body")
            if b is not None and not exists("BodyDef", (b.text or "").strip(), tw_branch):
                errors.append("%s: ThingDef %s body '%s' not found" % (os.path.relpath(f, AGM), dn, b.text))
            for c in el.findall("comps/li"):
                cls = c.get("Class", "")
                if cls.startswith("CompProperties_TurretGun"):
                    td = c.find("turretDef")
                    if td is not None and not exists("ThingDef", td.text, tw_branch):
                        errors.append("%s: turretDef '%s' not found" % (os.path.relpath(f, AGM), td.text))
            for v in el.findall("verbs/li"):
                dp = v.find("defaultProjectile")
                if dp is not None and not exists("ThingDef", dp.text, tw_branch):
                    errors.append("%s: defaultProjectile '%s' not found" % (os.path.relpath(f, AGM), dp.text))
                sc = v.find("soundCast")
                if sc is not None and not exists("SoundDef", sc.text, tw_branch):
                    warnings.append("%s: soundCast '%s' not found" % (os.path.relpath(f, AGM), sc.text))
                bm = v.find("beamMoteDef")
                if bm is not None and not exists("ThingDef", bm.text, tw_branch):
                    errors.append("%s: beamMoteDef '%s' not found" % (os.path.relpath(f, AGM), bm.text))
                be = v.find("beamEndEffecterDef")
                if be is not None and not exists("EffecterDef", be.text, tw_branch):
                    warnings.append("%s: beamEndEffecterDef '%s' not found" % (os.path.relpath(f, AGM), be.text))
            for ls in el.findall("race/lifeStageAges/li/def"):
                if not exists("LifeStageDef", ls.text):
                    errors.append("%s: LifeStageDef '%s' not found" % (os.path.relpath(f, AGM), ls.text))
            for bp in el.findall("butcherProducts/*"):
                if not exists("ThingDef", bp.tag, tw_branch):
                    errors.append("%s: butcherProduct '%s' not found" % (os.path.relpath(f, AGM), bp.tag))
            for cp in el.findall("costList/*"):
                if not exists("ThingDef", cp.tag, tw_branch):
                    errors.append("%s: costList '%s' not found" % (os.path.relpath(f, AGM), cp.tag))
        if tag == "PawnKindDef":
            r = el.find("race")
            if r is not None and not exists("ThingDef", r.text, tw_branch):
                errors.append("%s: PawnKind %s race '%s' not found" % (os.path.relpath(f, AGM), dn, r.text))
            check_list(f, el, tag, "abilities/li", "AbilityDef", tw_branch, optional=True)
            for ls in el.findall("lifeStages/li/def"):
                if not exists("LifeStageDef", ls.text):
                    errors.append("%s: kind LifeStageDef '%s' not found" % (os.path.relpath(f, AGM), ls.text))
            ft = el.find("defaultFactionType")
            if ft is not None and not exists("FactionDef", ft.text, tw_branch):
                errors.append("%s: FactionDef '%s' not found" % (os.path.relpath(f, AGM), ft.text))
        if tag == "RecipeDef":
            check(f, el, tag, "researchPrerequisite", "ResearchProjectDef")
            for p in el.findall("products/*"):
                if not exists("ThingDef", p.tag, tw_branch):
                    errors.append("%s: recipe %s product '%s' not found" % (os.path.relpath(f, AGM), dn, p.tag))
            for td in el.findall("ingredients/li/filter/thingDefs/li"):
                if not exists("ThingDef", td.text):
                    errors.append("%s: recipe %s ingredient '%s' not found" % (os.path.relpath(f, AGM), dn, td.text))
            for ru in el.findall("recipeUsers/li"):
                if not exists("ThingDef", ru.text):
                    errors.append("%s: recipeUsers '%s' not found" % (os.path.relpath(f, AGM), ru.text))
        if tag == "AbilityDef":
            pd = el.find("comps/li/projectileDef")
            if pd is not None and not exists("ThingDef", pd.text, tw_branch):
                errors.append("%s: ability %s projectileDef '%s' not found" % (os.path.relpath(f, AGM), dn, pd.text))
            ip = el.find("iconPath")
            # icon textures are vanilla-copied; skip
        if tag == "ResearchProjectDef":
            check_list(f, el, tag, "prerequisites/li", "ResearchProjectDef")
            t = el.find("tab")
            if t is not None and not exists("ResearchTabDef", t.text):
                errors.append("%s: research tab '%s' not found" % (os.path.relpath(f, AGM), t.text))
        if tag == "DamageDef":
            check(f, el, tag, "hediff", "HediffDef", optional=True)
            se = el.find("soundExplosion")
            if se is not None and not exists("SoundDef", se.text, tw_branch):
                warnings.append("%s: damage %s soundExplosion '%s' not found" % (os.path.relpath(f, AGM), dn, se.text))
            ec = el.find("explosionCellFleck")
            if ec is not None and not exists("FleckDef", ec.text, tw_branch):
                warnings.append("%s: damage %s explosionCellFleck '%s' not found" % (os.path.relpath(f, AGM), dn, ec.text))
            cl = el.find("combatLogRules")
            if cl is not None and not exists("RulePackDef", cl.text):
                errors.append("%s: damage %s combatLogRules '%s' not found" % (os.path.relpath(f, AGM), dn, cl.text))
        if tag == "HediffDef":
            pass
        if tag == "SoundDef":
            pass
        if tag == "EffecterDef":
            for md in el.findall(".//moteDef"):
                if not exists("ThingDef", md.text, tw_branch):
                    errors.append("%s: effecter %s moteDef '%s' not found" % (os.path.relpath(f, AGM), dn, md.text))
            for fd in el.findall(".//fleckDef"):
                if not exists("FleckDef", fd.text, tw_branch):
                    errors.append("%s: effecter %s fleckDef '%s' not found" % (os.path.relpath(f, AGM), dn, fd.text))
        if tag == "FleckDef":
            pass

print("\n=== ERRORS (%d) ===" % len(errors))
for e in errors:
    print(" ", e)
print("\n=== WARNINGS (%d) ===" % len(warnings))
for w in warnings:
    print(" ", w)
