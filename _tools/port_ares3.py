#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Finalize the Ares->Astra port localization:
- add the AGM.* keyed strings (phase / targeting / weapon toggles) to all 5 languages
- drop the obsolete AGM.Setting.WormBoss* keys
- rewrite AGM_Astra label/description texts for the new titan implementation (CN/JP; KR done here too)
- update the gestation recipe description keys."""
import re, os

AGM = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

KEYED = {
"Korean": """  <AGM.ExoPhaseAdvanceLabel>AGM-series mechanoid enters Phase {0}</AGM.ExoPhaseAdvanceLabel>
  <AGM.ExoPhaseAdvanceText>{0}이(가) 큰 피해를 입고 전투 페이즈 {1}에 도달했습니다: 모든 무기 체계가 더 빠르게 순환하며, 페이즈 개방형 공격 패턴이 더 넓어집니다.</AGM.ExoPhaseAdvanceText>
  <AGM.ExoPhaseStatus>전투 페이즈 {0} / {1}</AGM.ExoPhaseStatus>
  <AGM.MultiTargetLabel>다중 표적</AGM.MultiTargetLabel>
  <AGM.FocusFireLabel>집중 사격</AGM.FocusFireLabel>
  <AGM.TargetingModeDesc>이 메카노이드의 독립 무기 체계가 여러 표적에 분산 사격할지 단일 표적에 집중할지 전환합니다.</AGM.TargetingModeDesc>
  <AGM.AutoWeaponToggleLabel>무기 전환</AGM.AutoWeaponToggleLabel>
  <AGM.AutoWeaponToggleDesc>이 메카노이드의 자동 무기를 끄거나 켭니다.</AGM.AutoWeaponToggleDesc>
  <AGM.DoomsdayRocketToggleLabel>종말 로켓 전환</AGM.DoomsdayRocketToggleLabel>
  <AGM.DoomsdayRocketToggleDesc>종말 로켓 발사를 켜거나 끕니다. 기본값은 꺼짐입니다.</AGM.DoomsdayRocketToggleDesc>""",
"English": """  <AGM.ExoPhaseAdvanceLabel>AGM-series mechanoid enters Phase {0}</AGM.ExoPhaseAdvanceLabel>
  <AGM.ExoPhaseAdvanceText>{0} has taken heavy damage and advanced to combat phase {1}: every weapon system is now cycling faster, and phase-gated attack patterns have widened.</AGM.ExoPhaseAdvanceText>
  <AGM.ExoPhaseStatus>Combat phase {0} / {1}</AGM.ExoPhaseStatus>
  <AGM.MultiTargetLabel>Multi-target</AGM.MultiTargetLabel>
  <AGM.FocusFireLabel>Focus fire</AGM.FocusFireLabel>
  <AGM.TargetingModeDesc>Toggle whether this mechanoid's independent weapon systems spread across multiple targets or concentrate fire on a single one.</AGM.TargetingModeDesc>
  <AGM.AutoWeaponToggleLabel>Toggle weapon</AGM.AutoWeaponToggleLabel>
  <AGM.AutoWeaponToggleDesc>Turn this mechanoid's automatic weapon off or on.</AGM.AutoWeaponToggleDesc>
  <AGM.DoomsdayRocketToggleLabel>Toggle Doomsday Rocket</AGM.DoomsdayRocketToggleLabel>
  <AGM.DoomsdayRocketToggleDesc>Toggle the doomsday rocket barrage. Off by default.</AGM.DoomsdayRocketToggleDesc>""",
"ChineseSimplified": """  <AGM.ExoPhaseAdvanceLabel>AGM系列机甲进入阶段 {0}</AGM.ExoPhaseAdvanceLabel>
  <AGM.ExoPhaseAdvanceText>{0}受到重创，进入战斗阶段 {1}：所有武器系统循环更快，分阶段攻击模式范围更广。</AGM.ExoPhaseAdvanceText>
  <AGM.ExoPhaseStatus>战斗阶段 {0} / {1}</AGM.ExoPhaseStatus>
  <AGM.MultiTargetLabel>多重目标</AGM.MultiTargetLabel>
  <AGM.FocusFireLabel>集中火力</AGM.FocusFireLabel>
  <AGM.TargetingModeDesc>切换该机甲的独立武器系统是分散攻击多个目标，还是集中攻击单一目标。</AGM.TargetingModeDesc>
  <AGM.AutoWeaponToggleLabel>切换武器</AGM.AutoWeaponToggleLabel>
  <AGM.AutoWeaponToggleDesc>开关该机甲的自动武器。</AGM.AutoWeaponToggleDesc>
  <AGM.DoomsdayRocketToggleLabel>切换末日火箭</AGM.DoomsdayRocketToggleLabel>
  <AGM.DoomsdayRocketToggleDesc>开关末日火箭齐射。默认关闭。</AGM.DoomsdayRocketToggleDesc>""",
"Japanese": """  <AGM.ExoPhaseAdvanceLabel>AGMシリーズ メカノイドがフェーズ {0} に移行</AGM.ExoPhaseAdvanceLabel>
  <AGM.ExoPhaseAdvanceText>{0} が大ダメージを受け、戦闘フェーズ {1} に移行しました：全武装システムの稼働が高速化し、フェーズ限定の攻撃パターンが拡大します。</AGM.ExoPhaseAdvanceText>
  <AGM.ExoPhaseStatus>戦闘フェーズ {0} / {1}</AGM.ExoPhaseStatus>
  <AGM.MultiTargetLabel>複数ターゲット</AGM.MultiTargetLabel>
  <AGM.FocusFireLabel>集中攻撃</AGM.FocusFireLabel>
  <AGM.TargetingModeDesc>このメカノイドの独立武器システムが複数ターゲットに分散するか、単一ターゲットに集中するかを切り替えます。</AGM.TargetingModeDesc>
  <AGM.AutoWeaponToggleLabel>武器切替</AGM.AutoWeaponToggleLabel>
  <AGM.AutoWeaponToggleDesc>このメカノイドの自動武器をオン/オフします。</AGM.AutoWeaponToggleDesc>
  <AGM.DoomsdayRocketToggleLabel>ドゥームズデイロケット切替</AGM.DoomsdayRocketToggleLabel>
  <AGM.DoomsdayRocketToggleDesc>ドゥームズデイロケット斉射のオン/オフ。初期状態はオフです。</AGM.DoomsdayRocketToggleDesc>""",
}

CN_T_ASTRA_DESC = "以六個獨立瞄準的武器核心重建的巨型戰爭泰坦：速射激光炮、等離子焚化炮、特斯拉炮、重型脈衝炮電池、高斯核彈頭發射器，以及一對光子撕裂武士刀。武器會預判目標移動，受損時逐階段加速。內部維修無人機可從致命損傷中完全重建。"

for lang, add in KEYED.items():
    p = os.path.join(AGM, "Languages", lang, "Keyed", "AGM.xml")
    if not os.path.exists(p):
        print("skip", lang); continue
    src = open(p, encoding="utf-8").read()
    # drop obsolete worm-boss setting keys
    src = re.sub(r"\n?\s*<AGM\.Setting\.[^<]*</AGM\.Setting\.[^>]*>", "", src)
    if "AGM.ExoPhaseStatus" not in src:
        src = src.replace("</LanguageData>", add + "\n\n</LanguageData>")
    open(p, "w", encoding="utf-8").write(src)
    print("keyed updated:", lang)

# ChineseTraditional: convert the CN-S keyed file with LCMapString
import ctypes
k32 = ctypes.windll.kernel32
def s2t(text):
    b = ctypes.create_unicode_buffer(text)
    size = k32.LCMapStringW(0x0804, 0x04000000, b, -1, None, 0)
    out = ctypes.create_unicode_buffer(size)
    k32.LCMapStringW(0x0804, 0x04000000, b, -1, out, size)
    return out.value
src = open(os.path.join(AGM, "Languages", "ChineseSimplified", "Keyed", "AGM.xml"), encoding="utf-8").read()
open(os.path.join(AGM, "Languages", "ChineseTraditional", "Keyed", "AGM.xml"), "w", encoding="utf-8").write(s2t(src))
print("CN-T keyed regenerated")

# ---- Astra description texts (CN-S ThingDef + JP ThingDef) ----
cn = os.path.join(AGM, "Languages", "ChineseSimplified", "DefInjected", "ThingDef", "Defs.xml")
src = open(cn, encoding="utf-8").read()
new_cn = "<AGM_Astra.description>以六個獨立瞄準的武器核心重建的巨型戰爭泰坦：掃射時展開多激光扇面的速射激光炮、留下高熱等離子氣體雲的等離子焚化炮、彈丸迸裂成十字火花的新特斯拉炮、重型脈衝炮電池、高斯核彈頭發射器，以及一對用於閃現斬擊終結技、以放射狀死亡射線收尾的光子撕裂武士刀。它的武器會預判目標移動，而隨著泰坦受損，它會攀升戰鬥階段——每一階段都讓所有武器循環更快、扇面更寬。內部維修無人機能在長冷卻後從致命損傷中完全重建，可手動觸發或在瀕死時自動啟動。\\n\\n它的鑄造廠基準測試只有一條評分標準：人類的最後考試。它通過了。</AGM_Astra.description>"
src = re.sub(r"<AGM_Astra\.description>.*?</AGM_Astra\.description>", new_cn, src, flags=re.S)
open(cn, "w", encoding="utf-8").write(src)
print("CN-S astra description updated")

jp = os.path.join(AGM, "Languages", "Japanese", "DefInjected", "ThingDef", "Defs.xml")
src = open(jp, encoding="utf-8").read()
new_jp = "<AGM_Astra.description>六つの独立照準武器コアを中心に再建された巨大戦争タイタン：多連レーザー扇に広がる速射レーザー砲、持続する過熱プラズマガス雲を残すプラズマ焼却砲、十字火花に炸裂するテスラ砲、重量級エクソパルス砲台、ガウス核弾頭ランチャー、そしてブラックダッシュ斬り超技を繰り出す光子リッパーの二刀。武器は標的の移動を予測し、損傷が蓄積するほど戦闘フェーズが上昇して全武装が加速する。内部修復ドローンが致命的損傷から長いクールダウン付きで完全再建する。\\n\\n訓練に使われた鋳造所のベンチマークの採点基準はただ一つ：人類の最終試験。合格した。</AGM_Astra.description>"
src = re.sub(r"<AGM_Astra\.description>.*?</AGM_Astra\.description>", new_jp, src, flags=re.S)
open(jp, "w", encoding="utf-8").write(src)
print("JP astra description updated")

# recipe description keys (KR/CN/JP) - Astra flavor
for lang, old, new in [
    ("Korean", "별들보다 오래된 분절 아르코웜 레비아탄, AGM 라인의 별의 어머니",
     "여섯 개의 독립 무기 코어를 지닌 전쟁 타이탄, AGM 라인의 레비아탄"),
    ("ChineseSimplified", "比群星更古老的分段式远古蠕虫巨兽", "拥有六个独立武器核心的战争泰坦"),
    ("Japanese", "星々より古い、分節型アーカイワームのリヴァイアサン", "六つの独立武器コアを持つ戦争タイタン"),
]:
    p = None
    for cand in (os.path.join(AGM, "Languages", lang, "DefInjected", "RecipeDef", "RecipeDefs.xml"),
                 os.path.join(AGM, "Languages", lang, "DefInjected", "RecipeDef", "Defs.xml")):
        if os.path.exists(cand):
            p = cand
            break
    src = open(p, encoding="utf-8").read()
    src = src.replace(old, new)
    open(p, "w", encoding="utf-8").write(src)
    print("recipe desc updated:", lang)
print("done")
