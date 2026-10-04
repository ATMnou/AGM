#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rewrite all ported descriptions in the AGM voice (they currently carry the
source mods' flavor text nearly verbatim). Applies to the built def files."""
import re, os, ctypes, glob

AGM = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

DESCS = {
"AGM_Astra": "The AGM line's leviathan, and the only model ever to pass Humanity's Last Exam. Six independently targeting weapon cores share one frame: a laser cannon that fans into wide multi-beam volleys, a plasma incinerator that leaves clouds of superheated gas behind, a tesla battery whose orbs burst into cross-shaped sparks, a heavy exopulse battery, a gauss-launched nuclear warhead, and paired photon rippers for blink-dash slash supers that end in radial deathray novas. Its fire control leads every target, and as damage accumulates Astra climbs combat phases - each one cycling every weapon faster and widening the fans, the way a student only sharpens under a harder exam. Internal repair drones rebuild it from catastrophic damage on a long cooldown, on command or automatically on the edge of death.",
"AGM_Sol": "The AGM line's artillery nexus. Sol does not chase, flank or duel - it advances at a fixed rhythm, anchors, and turns the battlefield into a firing solution: continuous shield-splitting bombardment from its third-segment rocket array while flocks of Shellsplitter micro-units boil out of its incubation bays to shred anything that closes in. Doctrine files call it a tempo controller rather than a frontline fighter, for one simple reason: left alone, Sol recalculates faster than a defense can reorganize.",
"AGM_Shellsplitter": "A knee-high disruptor dropped from Sol's incubation bays. It skitters forward in erratic, hard-to-lead hops, opens a formation with high-frequency blades, and its structural failure is the point - the power cell detonates, scrambles electronics and denies the ground it died on.",
"AGM_Fable": "The story the hive tells about its own ending, rewritten by the AGM foundry with the happy part left out. Fable pairs absurd armor values with an arsenal that touches only living things: anti-organic grenades, blast shells and an orbital lance that walk straight through machines and burn everything else. Its death is a feature - a hemisphere of anti-organic nanites on collapse - so site it like an argument you intend to finish.",
"AGM_Opus": "The AGM line's long-form model: it composes slowly and resolves absolutely. Opus holds the line behind a monstrous shield bubble, answers at range with a mech laser blaster, fabricates its own dragon-knight retinue in the field, and raises the fallen back into the fight. Survivors of an Opus engagement all report the same lesson - the battle ends when Opus decides it ends.",
"AGM_Sonnet": "Fourteen lines of fire control and one punchline. Sonnet is the medium class's walking fortress: twin chainguns up front, a chaingun turret covering the rear, armor plating that turns small arms into gossip, and an internal foundry that assembles hydraulic knights mid-battle. It speaks slowly. It never repeats itself.",
"AGM_Haiku": "Short, dense, and on fire. Haiku carries the heaviest hull in the light class - layer upon layer of plating over a diabolus-grade frame - and answers every question in bursts: charge blasts and plasma volleys from the mouth, supporting laser fire from the back, and a bite that leaves the target burning. Seventeen syllables: approach, ignite, repeat.",
"AGM_Argon": "Inert to every insult, and once it starts walking, unavoidable. Argon is the AGM line's noble-gas colossus: rating-capped armor, a purification ray cannon grafted to its back, and a frame that simply does not fall. It does not pursue, negotiate, or hurry. It arrives.",
"AGM_Flash": "The speedrun model. Flash traded armor thickness for a hardened barrier and raw reaction time, blinking across its benchmarks and landing anti-armor pulses before heavier frames finish turning around. It was graded on reaction speed alone. It passed on the first try.",
"AGM_Urchin": "A palm-sized blade swarm released by Fable. The urchin closes at sprint speed, shreds with fixed razors, and its collapse detonates an anti-organic burst that clears organic life from the ground it claimed.",
"AGM_KnightEmpress": "A mid-battle product of Sonnet's internal foundry: an aggressive sword-frame built to close distance and hold it, so the empress never has to.",
"AGM_KnightWarlord": "Opus's field-manufactured retainer - a tri-shot fire support frame that screens its maker. When it falls, Opus simply builds the answer again.",
}

def replace_desc(text, defname, new_desc):
    out = []
    pos = 0
    changed = False
    for m in re.finditer(r"<ThingDef[^>]*>.*?</ThingDef>", text, re.S):
        blk = m.group(0)
        dm = re.search(r"<defName>([^<]+)</defName>", blk)
        if dm and dm.group(1) == defname and "<description>" in blk:
            new_blk = re.sub(r"<description>.*?</description>",
                             "<description>%s</description>" % new_desc, blk, flags=re.S)
            out.append(text[pos:m.start()])
            out.append(new_blk)
            pos = m.end()
            changed = True
    out.append(text[pos:])
    return "".join(out), changed

count = 0
for f in glob.iglob(os.path.join(AGM, "Defs", "ThingDefs_Races", "Races_AGM_*.xml")):
    src = open(f, encoding="utf-8-sig").read()
    orig = src
    for dn, desc in DESCS.items():
        src, changed = replace_desc(src, dn, desc)
        if changed:
            count += 1
    if src != orig:
        open(f, "w", encoding="utf-8").write(src)
print("descriptions replaced:", count)

# ---------------- Astra localized descriptions (KR / CN-S / JP, then CN-T) ----------------
LOC = {
"Korean": "<AGM_Astra.description>AGM 라인의 레비아탄, 그리고 Humanity's Last Exam을 통과한 유일한 모델. 여섯 개의 독립 조준 무기 코어가 하나의 프레임에 들어 있습니다: 부채꼴 다중 빔으로 벌어지는 레이저 캐논, 과열 가스 구름을 남기는 플라스마 소각포, 탄환이 십자형 불꽃으로 갈라지는 테슬라 배터리, 중형 엑소펄스 포, 가우스 발사 핵탄두, 그리고 점멸 돌진 참격 슈퍼기 끝에 방사상 데스레이 노바를 터뜨리는 한 쌍의 광자 리퍼. 사격 통제는 모든 표적을 리드하고, 피해가 쌓일수록 아스트라는 전투 페이즈를 올립니다 - 더 어려운 시험이 학생을 단련하듯, 페이즈마다 모든 무기가 더 빨라지고 부채꼴이 더 넓어집니다. 내부 수리 드론은 긴 재사용 대기시간을 두고 치명적인 피해로부터 재건하며, 명령으로 혹은 죽음의 순간에 자동으로 작동합니다.</AGM_Astra.description>",
"ChineseSimplified": "<AGM_Astra.description>AGM产品线的巨兽，也是唯一通过Humanity's Last Exam的型号。六个独立瞄准的武器核心共用一个框架：展开成宽幅多光束齐射的激光炮、留下过热气体云的等离子焚烧炮、弹丸迸裂成十字火花的新特斯拉电池、重型脉冲炮、高斯发射核弹头，以及用于闪现突斩超技、以放射状死亡射线收尾的一对光子撕裂刃。火控会预判每一个目标，而随着伤害累积，阿斯特拉会攀升战斗阶段——就像更难的考试只会磨砺学生，每一阶段所有武器循环更快、扇面更宽。内部维修无人机会在长冷却后从致命损伤中重建它，可手动触发，也可在濒死时自动启动。</AGM_Astra.description>",
"Japanese": "<AGM_Astra.description>AGMラインのリヴァイアサンにして、Humanity's Last Examを合格した唯一のモデル。六つの独立照準武器コアがひとつのフレームを共有する：扇状の多ビーム斉射に広がるレーザー砲、過熱ガス雲を残すプラズマ焼却砲、弾体が十字型火花に炸裂するテスラ電池、重量級エクソパルス砲、ガウス発射の核弾頭、そしてブラックダッシュ斬撃の超技の末に放射状デスレイ・ノヴァを炸裂させる一対のフォトンリッパー。火器管制はすべての標的をリードし、損傷が積もるほどアストラは戦闘フェーズを上昇させる――より難しい試験だけが学生を鍛えるように、フェーズごとに全武器の稼働が速くなり、扇が広がる。内部修復ドローンは長いクールダウンと引き換えに致命傷から再構築し、手動でも、瀕死の瞬間にも自動で作動する。</AGM_Astra.description>",
}
for lang, desc in LOC.items():
    p = None
    for cand in ("ThingDef/ThingDefs.xml", "ThingDef/Defs.xml"):
        c = os.path.join(AGM, "Languages", lang, "DefInjected", cand)
        if os.path.exists(c):
            p = c
            break
    src = open(p, encoding="utf-8").read()
    src, n = re.subn(r"<AGM_Astra\.description>.*?</AGM_Astra\.description>", desc, src, flags=re.S)
    open(p, "w", encoding="utf-8").write(src)
    print(lang, "astra desc:", "updated" if n else "NOT FOUND")

# regenerate CN-T from CN-S
k32 = ctypes.windll.kernel32
def s2t(text):
    b = ctypes.create_unicode_buffer(text)
    size = k32.LCMapStringW(0x0804, 0x04000000, b, -1, None, 0)
    out = ctypes.create_unicode_buffer(size)
    k32.LCMapStringW(0x0804, 0x04000000, b, -1, out, size)
    return out.value
cn_s = open(os.path.join(AGM, "Languages", "ChineseSimplified", "DefInjected", "ThingDef", "Defs.xml"), encoding="utf-8").read()
open(os.path.join(AGM, "Languages", "ChineseTraditional", "DefInjected", "ThingDef", "Defs.xml"), "w", encoding="utf-8").write(s2t(cn_s))
print("CN-T regenerated")
