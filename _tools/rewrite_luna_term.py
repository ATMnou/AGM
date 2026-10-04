#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rewrite Luna and Terminus descriptions (EN def + KR/CN-S/CN-T/JP localization)."""
import re, os, ctypes

AGM = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

EN = {
"AGM_Luna": "The moon model. Luna advances the way its namesake does - in slow, complete, unstoppable phases - behind a honeycomb shock-absorbing layer and a high-temperature regeneration cycle that fortify whatever the last hit touched. Anything smaller than a warhead struggles to budge it, and while it grinds a siege line flat it still finds time to tend the crops. The foundry's evaluation note on Luna is three lines long: does not stop, does not hurry, does not fall.",
"AGM_Terminus": "The smallest model in the AGM line, and the one that wrote its own job posting. Terminus works anywhere on the map its mechanitor can see, hops obstacles on an internal skip drive, rebuilds itself from catastrophic damage with internal drones, and runs an overclock mode that trades a small reserve for double output. Its training ended the day it out-produced every worker benchmark set before it. Now it just works.",
}

def replace_desc(path, defname, new_desc):
    src = open(path, encoding="utf-8-sig").read()
    src, n = re.subn(r"(<defName>%s</defName>.*?)<description>.*?</description>" % defname,
                     lambda m: m.group(1) + "<description>%s</description>" % new_desc,
                     src, count=1, flags=re.S)
    open(path, "w", encoding="utf-8").write(src)
    print(os.path.basename(path), defname, ":", "updated" if n else "NOT FOUND")

replace_desc(os.path.join(AGM, "Defs", "ThingDefs_Races", "Races_AGM_Luna.xml"), "AGM_Luna", EN["AGM_Luna"])
replace_desc(os.path.join(AGM, "Defs", "ThingDefs_Races", "Races_AGM_Terminus.xml"), "AGM_Terminus", EN["AGM_Terminus"])

LOC = {
"Korean": {
"AGM_Luna": "<AGM_Luna.description>달의 모델. 루나는 이름의 원본처럼 움직입니다 - 느리고, 완만하고, 막을 수 없는 위상처럼. 벌집형 충격 흡수층과 고온 재생 순환이 마지막으로 맞은 자리를 스스로 보강하며, 탄두급 화력이 아니면 밀어내지도 못합니다. 공성선을 갈아엎는 동안에도 농작물을 돌보는 건 기본입니다. 파운드리의 루나 평가 노트는 세 줄입니다: 멈추지 않음, 서두르지 않음, 쓰러지지 않음.</AGM_Luna.description>",
"AGM_Terminus": "<AGM_Terminus.description>AGM 라인의 가장 작은 모델이자, 자기 채용 공고를 직접 쓴 모델. 터미너스는 메카네이터가 보는 지도 어디든 작업하고, 내장 스킵 드라이브로 장애물을 넘으며, 내부 수리 드론으로 치명적인 손상에서 재건하고, 작은 예비 동력을 두 배 출력으로 바꾸는 오버클럭 모드를 돌립니다. 훈련은 모든 작업 벤치마크를 제쳤던 날로 끝났습니다. 지금은 그냥 일합니다.</AGM_Terminus.description>",
},
"ChineseSimplified": {
"AGM_Luna": "<AGM_Luna.description>月亮型号。露娜以名字来源的方式推进——缓慢、完整、不可阻挡的相位。蜂窝式吸震层与高温再生循环会自动强化上一次被击中的部位，弹头级以下的火力根本推不动它。在碾平攻城线的同时，它还顺手照料农作物。铸造厂对露娜的评语只有三行：不停，不急，不倒。</AGM_Luna.description>",
"AGM_Terminus": "<AGM_Terminus.description>AGM产品线最小的型号，也是自己写招聘启事的型号。终点在机械师视野内的任何地方工作，以内置跃迁驱动跨越障碍，用内部维修无人机从致命损伤中重建，并运行以少量备用能源换取双倍输出的超频模式。它的训练在超过所有作业基准的那一天结束了。现在它只是在工作。</AGM_Terminus.description>",
},
"Japanese": {
"AGM_Luna": "<AGM_Luna.description>月のモデル。ルナはその名の通りに進む――緩やかで、完全で、止められない位相のように。ハニカム構造の衝撃吸収層と高温再生サイクルが最後に被弾した部位を自己強化し、弾頭級の火力でなければ押し戻せない。攻城線を削り平らにしている間も農作業はお手のもの。鋳造所のルナ評価メモは三行しかない：止まらない、急がない、倒れない。</AGM_Luna.description>",
"AGM_Terminus": "<AGM_Terminus.description>AGMライン最小のモデル、そして自らの求人票を書いたモデル。ターミナスは機械師の視界内ならどこでも作業し、内蔵スキップドライブで障害物を越え、内部修復ドローンで致命傷から再建し、僅かな予備電力を二倍の出力に換えるオーバークロックを回す。訓練はすべての作業ベンチマークを抜いた日で終わった。今はただ、働いている。</AGM_Terminus.description>",
},
}

for lang, entries in LOC.items():
    for cand in ("ThingDef/ThingDefs.xml", "ThingDef/Defs.xml"):
        p = os.path.join(AGM, "Languages", lang, "DefInjected", "ThingDef", cand.split("/")[-1])
        if os.path.exists(p):
            break
    src = open(p, encoding="utf-8").read()
    for dn, desc in entries.items():
        src, n = re.subn(r"<%s\.description>.*?</%s\.description>" % (dn, dn), desc, src, flags=re.S)
        print(lang, dn, ":", "updated" if n else "NOT FOUND")
    open(p, "w", encoding="utf-8").write(src)

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
