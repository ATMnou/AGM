#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix5: repair all main-menu load errors found in Player.log.
1. build_kral typo explosiveDamageType + effecter/sound renames + damage abstract parents
   inlined + Kraltech DamageWorkers replaced with vanilla + Shock/DarkShock effecters
   extracted + extra SoundDefs (ExtinctionRay_Shooting_Resolve, Interact_EnergyWeapon,
   Shot_ToxCanister) + lifeStageAges collapse for Sol/Opus/Sonnet/Haiku races.
2. build_tw: Doxa0Dorsal/IronbarkDorsalBase parents inlined, InfernoSystem dangling group
   removed, Sol/Shellsplitter lifeStageAges collapse.
3. loadFolders: subfolder paths without leading slash."""
import re, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
K = r"D:\SteamLibrary\steamapps\workshop\content\294100\3625664332\Defs"
T = r"D:\SteamLibrary\steamapps\workshop\content\294100\3555799437\1.6\Defs"

# ---------------- shared: abstract-parent inliner ----------------
def make_inliner(parent_blocks):
    """parent_blocks: dict Name -> inner XML string. Returns function that resolves
    <Tag ParentName="X"> children by inlining missing fields."""
    def resolve_one(inner_parent, inner_child):
        # split parent inner into top-level field blocks
        fields = re.findall(r"<(\w+)[^>]*>.*?</\1>|<(\w+)[^>]*/>", inner_parent, re.S)
        blocks = re.findall(r"<(\w+)[^>]*>.*?</\1>", inner_parent, re.S)
        # child field tags present
        child_tags = set(re.findall(r"<(\w+)[^>]*>", inner_child))
        add = []
        for fb in blocks:
            tag = re.match(r"<(\w+)", fb).group(1)
            if tag not in child_tags:
                add.append("    " + fb)
        if not add:
            return None
        return "\n" + "\n".join(add)

    def repl_source_text(text):
        # resolve <Tag ParentName="X" ...> where X in parent_blocks
        pattern = re.compile(r'<(\w+)([^>]*ParentName="([^"]+)"[^>]*)>(.*?)</\1>', re.S)
        out = []
        pos = 0
        for m in pattern.finditer(text):
            tagname, attrs, pname, inner = m.groups()
            if pname not in parent_blocks:
                continue
            fixed = resolve_one(parent_blocks[pname], inner)
            new_inner = inner if fixed is None else fixed + "\n" + inner
            attrs = re.sub(r'\s*ParentName="[^"]*"', "", attrs)
            out.append(text[pos:m.start()])
            out.append("<%s%s>%s</%s>" % (tagname, attrs, new_inner, tagname))
            pos = m.end()
        out.append(text[pos:])
        return "".join(out)

    return repl_source_text

def extract_abstracts(path, tag):
    txt = open(path, encoding="utf-8-sig").read()
    return {m.group(1): m.group(2)
            for m in re.finditer(r'<%s[^>]*Abstract="True"[^>]*Name="([^"]+)">(.*?)</%s>' % (tag, tag), txt, re.S)}

# ---------------- build_kral.py patches ----------------
p = os.path.join(HERE, "build_kral.py")
src = open(p, encoding="utf-8").read()

# 1. typo
assert "<explosionDamageType>%s</explosionDamageType>" in src
src = src.replace("<explosionDamageType>%s</explosionDamageType>" , "<explosiveDamageType>%s</explosiveDamageType>")
src = src.replace('<explosionDamageType>AGM_Damage_%s</explosionDamageType>' , '<explosiveDamageType>AGM_Damage_%s</explosiveDamageType>')

# 2. dedicated damages pipeline: effecter renames + parent inline + worker replace
old = '''dmg = raw["damages"]
for s in SOUND_NAMES:'''
new = '''dmg = raw["damages"]
# inline Kraltech abstract damage parents (Mech_ChaingunBullets etc.)
kral_damages_src = open(os.path.join(r"D:\\SteamLibrary\\steamapps\\workshop\\content\\294100\\3625664332\\Defs", "DamageDef", "Damages_Various.xml"), encoding="utf-8-sig").read()
import re as _re
_dmg_parents = {}
for _m in _re.finditer(r'<DamageDef[^>]*Abstract="True"[^>]*Name="([^"]+)">(.*?)</DamageDef>', kral_damages_src, _re.S):
    _dmg_parents[_m.group(1)] = _m.group(2)
def _inline_damage(m):
    pname, inner = m.group(1), m.group(2)
    pin = _dmg_parents[pname]
    child_tags = set(_re.findall(r"<(\\w+)[^>]*>", inner))
    add = []
    for fb in _re.findall(r"<(\\w+)[^>]*>.*?</\\1>", pin, _re.S):
        tag = _re.match(r"<(\\w+)", fb).group(1)
        if tag not in child_tags:
            add.append("    " + fb)
    joined = ("\\n" + "\\n".join(add) + "\\n" + inner) if add else inner
    return "<DamageDef>" + joined + "</DamageDef>"
dmg = _re.sub(r'<DamageDef ParentName="([^"]+)">(.*?)</DamageDef>', _inline_damage, dmg, flags=_re.S)
# replace Kraltech custom DamageWorkers with vanilla ones
dmg = dmg.replace("Kraltech_Industries.DamageWorker_Plasma", "DamageWorker_Burn")
dmg = dmg.replace("Kraltech_Industries.DamageWorker_Charged", "DamageWorker_AddInjury")
dmg = dmg.replace("Kraltech_Industries.DamageWorker_Psychic", "DamageWorker_AddInjury")
dmg = dmg.replace("Kraltech_Industries.DamageWorker_AntiOrganics", "DamageWorker_AddInjury")
# rename effecter refs to AGM copies
dmg = dmg.replace("<explosionCenterEffecter>AntiOrganicShockwave</explosionCenterEffecter>",
                  "<explosionCenterEffecter>AGM_AntiOrganicShockwave</explosionCenterEffecter>")
dmg = dmg.replace("<explosionCellEffecter>AntiOrgElectricityArc</explosionCellEffecter>",
                  "<explosionCellEffecter>AGM_AntiOrgElectricityArc</explosionCellEffecter>")
for s in SOUND_NAMES:'''
assert old in src
src = src.replace(old, new)

# 3. hediffs: Shock/DarkShock effecter defs + rename refs
old2 = '''hed = transform(raw["hediffs"] + "\\n" + _r.stdout)'''
new2 = '''_kral_hed_src = open(os.path.join(r"D:\\SteamLibrary\\steamapps\\workshop\\content\\294100\\3625664332\\Defs", "Hediffs", "Hediffs_Various.xml"), encoding="utf-8-sig").read()
_extra_effecters = []
for _en in ("Shock", "DarkShock"):
    _em = _re.search(r'<EffecterDef>\\s*<defName>%s</defName>.*?</EffecterDef>' % _en, _kral_hed_src, _re.S)
    if _em:
        _extra_effecters.append(_em.group(0).replace("<defName>%s</defName>" % _en, "<defName>AGM_%s</defName>" % _en))
hed = transform(raw["hediffs"] + "\\n" + _r.stdout)'''
assert old2 in src
src = src.replace(old2, new2)

old3 = '''hed = hed.replace("<hediff>%s</hediff>" % h, "<hediff>AGM_%s</hediff>" % h)'''
# rename stateEffecter refs after hed built
anchor = 'write("HediffDefs/HediffDefs_AGM_Kraltech.xml", "", [hed])'
assert anchor in src
src = src.replace(anchor,
'''hed = hed.replace("<stateEffecter>Shock</stateEffecter>", "<stateEffecter>AGM_Shock</stateEffecter>")
hed = hed.replace("<stateEffecter>DarkShock</stateEffecter>", "<stateEffecter>AGM_DarkShock</stateEffecter>")
write("HediffDefs/HediffDefs_AGM_Kraltech.xml", "", [hed])
write("Effects/Effects_AGM_Kraltech_Shock.xml", "", _extra_effecters)''')

# 4. sounds: extract 3 more defs, prefix, rename refs in weapons corpus
old4 = '''snd = transform(raw["sounds"])
write("SoundDefs/SoundDefs_AGM_Kraltech.xml", "", [snd])'''
new4 = '''_kral_snd = open(os.path.join(r"D:\\SteamLibrary\\steamapps\\workshop\\content\\294100\\3625664332\\Defs", "SoundDefs", "Kraltech_Sounds.xml"), encoding="utf-8-sig").read()
_extra_sounds = []
for _sn in ("ExtinctionRay_Shooting_Resolve", "Interact_EnergyWeapon", "Shot_ToxCanister"):
    _sm = _re.search(r'<SoundDef>\\s*<defName>%s</defName>.*?</SoundDef>' % _sn, _kral_snd, _re.S)
    if _sm:
        _extra_sounds.append(_sm.group(0).replace("<defName>%s</defName>" % _sn, "<defName>AGM_%s</defName>" % _sn))
snd = transform(raw["sounds"] + "\\n" + "\\n".join(_extra_sounds))
snd = snd.replace("<sustainStopSound>ExtinctionRay_Shooting_Resolve</sustainStopSound>", "<sustainStopSound>AGM_ExtinctionRay_Shooting_Resolve</sustainStopSound>")
write("SoundDefs/SoundDefs_AGM_Kraltech.xml", "", [snd])'''
assert old4 in src
src = src.replace(old4, new4)

# rename Interact_EnergyWeapon refs in weapons corpus
old5 = '''wpn = transform(raw["weapons"] + raw["turrets"])
write("ThingDefs_Weapon/Weapons_AGM_Kraltech.xml", "", [wpn])'''
new5 = '''wpn = transform(raw["weapons"] + raw["turrets"])
wpn = wpn.replace("<soundInteract>Interact_EnergyWeapon</soundInteract>", "<soundInteract>AGM_Interact_EnergyWeapon</soundInteract>")
write("ThingDefs_Weapon/Weapons_AGM_Kraltech.xml", "", [wpn])'''
assert old5 in src
src = src.replace(old5, new5)

# 5. lifeStageAges collapse helper + apply to corp_o/corp_s/corp_h
old6 = '''def inject_traits(thingdef_text, bandwidth, weightclass=None):'''
new6 = '''def collapse_lifestages(text):
    """Drop the minAge-100 second life stage so race and PawnKind stage counts match."""
    return re.sub(r"<li>\\s*<def>MechanoidFullyFormed</def>\\s*<minAge>100</minAge>.*?</li>", "", text, flags=re.S)

def inject_traits(thingdef_text, bandwidth, weightclass=None):'''
assert old6 in src
src = src.replace(old6, new6)
src = src.replace('corp_o = inject_traits(corp_o, 3, "Heavy")', 'corp_o = collapse_lifestages(corp_o)\ncorp_o = inject_traits(corp_o, 3, "Heavy")')
src = src.replace('corp_s = inject_traits(corp_s, 2, "Medium")', 'corp_s = collapse_lifestages(corp_s)\ncorp_s = inject_traits(corp_s, 2, "Medium")')
src = src.replace('corp_h = inject_traits(corp_h, 1, "Light")', 'corp_h = collapse_lifestages(corp_h)\ncorp_h = inject_traits(corp_h, 1, "Light")')

# 6. inline bodypart parents (Kraltech) into bodyparts corpus
old7 = '''bodies = raw["bodies"] + raw["bodyparts"] + load("kral_raw/grunt_body.txt")'''
new7 = '''_bp_src = open(os.path.join(r"D:\\SteamLibrary\\steamapps\\workshop\\content\\294100\\3625664332\\Defs", "Bodies", "Bodies_n_Bodyparts_Mechanoids.xml"), encoding="utf-8-sig").read()
_bp_parents = {}
for _m in _re.finditer(r'<BodyPartDef[^>]*Abstract="True"[^>]*Name="([^"]+)">(.*?)</BodyPartDef>', _bp_src, _re.S):
    _bp_parents[_m.group(1)] = _m.group(2)
def _inline_bp(m):
    pname, inner = m.group(1), m.group(2)
    pin = _bp_parents[pname]
    child_tags = set(_re.findall(r"<(\\w+)[^>]*>", inner))
    add = []
    for fb in _re.findall(r"<(\\w+)[^>]*>.*?</\\1>", pin, _re.S):
        tag = _re.match(r"<(\\w+)", fb).group(1)
        if tag not in child_tags:
            add.append("    " + fb)
    joined = ("\\n" + "\\n".join(add) + "\\n" + inner) if add else inner
    return "<BodyPartDef>" + joined + "</BodyPartDef>"
bodies = raw["bodies"] + raw["bodyparts"] + load("kral_raw/grunt_body.txt")
bodies = _re.sub(r'<BodyPartDef ParentName="([^"]+)">(.*?)</BodyPartDef>', _inline_bp, bodies, flags=_re.S)'''
assert old7 in src
src = src.replace(old7, new7)

# build_kral uses bare `re` not _re at top - add alias
if "import re as _re" in src and "import re\n" in src:
    pass
src = src.replace("import re, os, sys", "import re, os, sys\n_re = re")
open(p, "w", encoding="utf-8").write(src)
print("build_kral patched")

# ---------------- build_tw.py patches ----------------
p = os.path.join(HERE, "build_tw.py")
src = open(p, encoding="utf-8").read()

# inline TW bodypart parents + remove InfernoSystem group + collapse Sol/shellsplitter lifestages
old8 = '''write(OUT, "Bodies/Bodies_AGM_TW.xml", [doxa_body, doxa_parts, ib_body, ib_parts])'''
new8 = '''# inline TW abstract bodypart parents (Doxa0Dorsal, IronbarkDorsalBase)
tw_bp_src = open(r"D:\\SteamLibrary\\steamapps\\workshop\\content\\294100\\3555799437\\1.6\\Defs\\Bodies\\Bodies_Doxa.xml", encoding="utf-8-sig").read()
tw_bp_src += open(r"D:\\SteamLibrary\\steamapps\\workshop\\content\\294100\\3555799437\\1.6\\Defs\\Bodies\\Bodies_IronRoot.xml", encoding="utf-8-sig").read()
_bp_parents2 = {}
for _m in re.finditer(r'<BodyPartDef[^>]*Abstract="True"[^>]*Name="([^"]+)">(.*?)</BodyPartDef>', tw_bp_src, re.S):
    _bp_parents2[_m.group(1)] = _m.group(2)
def _inline_bp2(m):
    pname, inner = m.group(1), m.group(2)
    pin = _bp_parents2[pname]
    child_tags = set(re.findall(r"<(\\w+)[^>]*>", inner))
    add = []
    for fb in re.findall(r"<(\\w+)[^>]*>.*?</\\1>", pin, re.S):
        tag = re.match(r"<(\\w+)", fb).group(1)
        if tag not in child_tags:
            add.append("    " + fb)
    joined = ("\\n" + "\\n".join(add) + "\\n" + inner) if add else inner
    return "<BodyPartDef>" + joined + "</BodyPartDef>"
doxa_parts = re.sub(r'<BodyPartDef ParentName="([^"]+)">(.*?)</BodyPartDef>', _inline_bp2, doxa_parts, flags=re.S)
ib_parts = re.sub(r'<BodyPartDef ParentName="([^"]+)">(.*?)</BodyPartDef>', _inline_bp2, ib_parts, flags=re.S)
# drop dangling InfernoSystem group reference (undefined even in Total Warfare)
doxa_body = doxa_body.replace("<li>InfernoSystem</li>", "")
doxa_parts = doxa_parts.replace("<li>InfernoSystem</li>", "")
ib_body = ib_body.replace("<li>InfernoSystem</li>", "")
ib_parts = ib_parts.replace("<li>InfernoSystem</li>", "")
write(OUT, "Bodies/Bodies_AGM_TW.xml", [doxa_body, doxa_parts, ib_body, ib_parts])'''
assert old8 in src
src = src.replace(old8, new8)

# collapse Sol + shellsplitter lifeStageAges (race 2 stages vs kind 1)
old9 = '''sol_thing = inject_stats(sol_thing, 3)'''
new9 = '''sol_thing = re.sub(r"<li>\\s*<def>MechanoidFullyFormed</def>\\s*<minAge>100</minAge>.*?</li>", "", sol_thing, flags=re.S)
sol_thing = inject_stats(sol_thing, 3)'''
assert old9 in src
src = src.replace(old9, new9)
old10 = '''sp = inject_stats(sp, 1)'''
new10 = '''sp = re.sub(r"<li>\\s*<def>MechanoidFullyFormed</def>\\s*<minAge>100</minAge>.*?</li>", "", sp, flags=re.S)
sp = inject_stats(sp, 1)'''
assert old10 in src
src = src.replace(old10, new10)
open(p, "w", encoding="utf-8").write(src)
print("build_tw patched")

# ---------------- loadFolders ----------------
p = os.path.normpath(os.path.join(HERE, "..", "loadFolders.xml"))
lf = open(p, encoding="utf-8").read()
lf = lf.replace('"/Compat/TW"', '"Compat/TW"').replace('"/Compat/NoTW"', '"Compat/NoTW"')
open(p, "w", encoding="utf-8").write(lf)
print("loadFolders patched:", '<li IfModActive="Nyar.NCLvsTW">Compat/TW</li>' in lf)
