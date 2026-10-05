#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Localize the GPU Tower: research labels/descs (5 langs), building label/desc (5 langs),
and the AGM.GPUTowerInspect keyed string."""
import re, os, ctypes

AGM = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# ---------------- EN building desc is in the def; research EN lives in defs too ----------------

BUILDING_LOC = {
"Korean": {"label": "GPU 타워", "desc": "벤치마크 저장고 속 미사용 경험을 캐내는 윙윙대는 채굴 하드웨어 랙. 매일 축적된 입력-출력 잔여물을 은빛 연산 판에 결정화해 IO 토큰 한 개로 굽습니다.\n\n연산 효율 연구는 채굴 커널을 날카롭게 다듬습니다: 더 높은 일일 생산량, 더 낮은 전력 소모."},
"ChineseSimplified": {"label": "GPU塔", "desc": "嗡嗡作响的评分硬件机架，从铸造厂的基准测试档案中挖掘未使用的经验。每天它把累积的输入输出残渣结晶成一枚IO代币，压印在镀银算板上。\n\n运算效率研究能磨利挖掘内核：更高的日产量，更低的功耗。"},
"Japanese": {"label": "GPUタワー", "desc": "鋳造所のベンチマーク保管庫から未使用の経験を採掘する、唸る評価ハードウェアのラック。毎日、蓄積された入出力の残滓を結晶化し、IOトークンとして焼き上げます。\n\n演算効率研究は採掘カーネルを鋭く研ぎ澄まします：より高い日産量、より低い消費電力。"},
}

RESEARCH_LOC = {
"Korean": [
    ("AGM_ComputeEfficiency_I", "연산 효율 개선 I", "채굴 커널을 튜닝해 GPU 타워의 토큰 생산량이 두 배가 됩니다: 하루 2개."),
    ("AGM_ComputeEfficiency_II", "연산 효율 개선 II", "전력 계통을 재설계해 GPU 타워 소모 전력이 800W로 줄어듭니다."),
    ("AGM_ComputeEfficiency_III", "연산 효율 개선 III", "병렬 벤치마크 스윕으로 GPU 타워의 토큰 생산량이 하루 4개로 늘어납니다."),
    ("AGM_ComputeEfficiency_IV", "연산 효율 개선 IV", "와트당 처리량이 높은 언더클럭 텐서 코어로 GPU 타워 소모 전력이 600W로 줄어듭니다."),
    ("AGM_ComputeEfficiency_V", "연산 효율 개선 V", "파운드리 자체 훈련 런과 교차 채점한 최종 커널 개정판: 하루 6개, 400W."),
],
"ChineseSimplified": [
    ("AGM_ComputeEfficiency_I", "运算效率 I", "调优后的挖掘内核使GPU塔的代币产量翻倍：每天2枚。"),
    ("AGM_ComputeEfficiency_II", "运算效率 II", "重新设计的供电系统使GPU塔的功耗降至800W。"),
    ("AGM_ComputeEfficiency_III", "运算效率 III", "并行基准扫描使GPU塔的代币产量提升至每天4枚。"),
    ("AGM_ComputeEfficiency_IV", "运算效率 IV", "每瓦吞吐更高的降频张量核心使GPU塔的功耗降至600W。"),
    ("AGM_ComputeEfficiency_V", "运算效率 V", "与铸造厂自身训练任务交叉评分的最终内核修订版：每天6枚，400W。"),
],
"Japanese": [
    ("AGM_ComputeEfficiency_I", "演算効率 I", "採掘カーネルをチューニングし、GPUタワーのトークン生産量が倍増：1日2個。"),
    ("AGM_ComputeEfficiency_II", "演算効率 II", "給電系統を再設計し、GPUタワーの消費電力が800Wに低下。"),
    ("AGM_ComputeEfficiency_III", "演算効率 III", "並列ベンチマーク走査により、GPUタワーのトークン生産量が1日4個に増加。"),
    ("AGM_ComputeEfficiency_IV", "演算効率 IV", "ワットあたりの処理能力が高いアンダークロックのテンソルコアにより、GPUタワーの消費電力が600Wに低下。"),
    ("AGM_ComputeEfficiency_V", "演算効率 V", "鋳造所自身の訓練ランと交差採点した最終カーネル改訂版：1日6個、400W。"),
],
}

KEYED_LOC = {
"Korean": "  <AGM.GPUTowerInspect>IO 토큰 생산량: {0}/일</AGM.GPUTowerInspect>",
"English": "  <AGM.GPUTowerInspect>IO token yield: {0}/day</AGM.GPUTowerInspect>",
"ChineseSimplified": "  <AGM.GPUTowerInspect>IO代币产量：{0}/天</AGM.GPUTowerInspect>",
"Japanese": "  <AGM.GPUTowerInspect>IOトークン生産量：{0}/日</AGM.GPUTowerInspect>",
}

# ---- 1. building ThingDef localization ----
def thingdef_path(lang):
    for cand in ("Defs.xml", "ThingDefs.xml"):
        p = os.path.join(AGM, "Languages", lang, "DefInjected", "ThingDef", cand)
        if os.path.exists(p):
            return p
    return None


for lang, b in BUILDING_LOC.items():
    p = thingdef_path(lang) or p
    src = open(p, encoding="utf-8").read()
    if "<AGM_GPUTower.label>" in src:
        continue
    add = "\n  <AGM_GPUTower.label>%s</AGM_GPUTower.label>\n  <AGM_GPUTower.description>%s</AGM_GPUTower.description>\n" % (b["label"], b["desc"])
    src = src.replace("</LanguageData>", add + "</LanguageData>")
    open(p, "w", encoding="utf-8").write(src)
    print("building:", lang)

# ---- 2. research localization ----
for lang, entries in RESEARCH_LOC.items():
    p = os.path.join(AGM, "Languages", lang, "DefInjected", "ResearchProjectDef")
    os.makedirs(p, exist_ok=True)
    p = os.path.join(p, "GPU.xml")
    add = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<LanguageData>\n\n"
    for dn, label, desc in entries:
        add += "  <%s.label>%s</%s.label>\n  <%s.description>%s</%s.description>\n" % (dn, label, dn, dn, desc, dn)
    add += "\n</LanguageData>\n"
    open(p, "w", encoding="utf-8").write(add)
    print("research:", lang)

# ---- 3. keyed inspect string ----
for lang, line in KEYED_LOC.items():
    p = os.path.join(AGM, "Languages", lang, "Keyed", "AGM.xml")
    src = open(p, encoding="utf-8").read()
    if "AGM.GPUTowerInspect" not in src:
        src = src.replace("</LanguageData>", line + "\n\n</LanguageData>")
        open(p, "w", encoding="utf-8").write(src)
    print("keyed:", lang)

# ---- 4. regenerate CN-T from CN-S (thing defs + research + keyed) ----
k32 = ctypes.windll.kernel32
def s2t(text):
    b = ctypes.create_unicode_buffer(text)
    size = k32.LCMapStringW(0x0804, 0x04000000, b, -1, None, 0)
    out = ctypes.create_unicode_buffer(size)
    k32.LCMapStringW(0x0804, 0x04000000, b, -1, out, size)
    return out.value
for rel in ("DefInjected/ThingDef/Defs.xml", "DefInjected/ResearchProjectDef/GPU.xml", "Keyed/AGM.xml"):
    s = os.path.join(AGM, "Languages", "ChineseSimplified", rel.replace("/", os.sep))
    t = os.path.join(AGM, "Languages", "ChineseTraditional", rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(t), exist_ok=True)
    open(t, "w", encoding="utf-8").write(s2t(open(s, encoding="utf-8").read()))
print("CN-T regenerated")
