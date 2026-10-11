using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using RimWorld;
using UnityEngine;
using Verse;

namespace AGM
{
    // ==== Persona transformation ====
    public static class PersonaTransform
    {
        // Comp classes managed by the persona system. Transform() only syncs these,
        // leaving combat comps (AutoWeapon, ExoPhase, ...) untouched.
        private static readonly Type[] PersonaCompClasses = new Type[]
        {
            typeof(CompPersonaShield),
            typeof(CompPersonaPledge),
            typeof(CompAstraPersonaApply),
            typeof(CompFablePersonaApply),
            typeof(CompPersonaRevert),
        };
        public static bool ResearchReady(string d)
        {
            var r = DefDatabase<ResearchProjectDef>.GetNamedSilentFail(d);
            return r != null && r.IsFinished;
        }

        public static bool BuildingReady()
        {
            return Find.Maps.Any(m => m.listerBuildings.allBuildingsColonist
                .Any(b => b.def.defName == "AGM_PersonaDataCenter"));
        }

        public static void Transform(Pawn pawn, string newDef, string newKind)
        {
            var nd = DefDatabase<ThingDef>.GetNamedSilentFail(newDef);
            var nk = DefDatabase<PawnKindDef>.GetNamedSilentFail(newKind);
            if (nd == null || nk == null) return;
            var pos = pawn.Position;
            var map = pawn.Map;
            pawn.DeSpawn();
            pawn.def = nd;
            pawn.kindDef = nk;
            SyncPersonaComps(pawn);
            pawn.Drawer.renderer.SetAllGraphicsDirty();
            PawnComponentsUtility.AddAndRemoveDynamicComponents(pawn, true);
            GenSpawn.Spawn(pawn, pos, map);
        }

        // ThingComps are built from the def at spawn, so swapping def/kindDef alone
        // never grants the new form's comps (no Shield/Pledge/Revert gizmos) and never
        // removes the old form's persona comps. Sync just the persona family.
        public static void SyncPersonaComps(Pawn pawn)
        {
            var def = pawn.def;
            if (def == null) return;
            List<ThingComp> list = pawn.AllComps;
            if (list == null) return;
            var wanted = new HashSet<Type>();
            if (def.comps != null)
            {
                foreach (var p in def.comps)
                {
                    if (p != null && Array.IndexOf(PersonaCompClasses, p.compClass) >= 0)
                        wanted.Add(p.compClass);
                }
            }
            for (int i = list.Count - 1; i >= 0; i--)
            {
                var c = list[i];
                if (c == null) { list.RemoveAt(i); continue; }
                var t = c.GetType();
                if (Array.IndexOf(PersonaCompClasses, t) >= 0 && !wanted.Contains(t))
                    list.RemoveAt(i);
            }
            if (def.comps != null)
            {
                foreach (var p in def.comps)
                {
                    if (p == null || Array.IndexOf(PersonaCompClasses, p.compClass) < 0) continue;
                    bool has = false;
                    foreach (var c in list)
                    {
                        if (c != null && c.GetType() == p.compClass) { c.props = p; has = true; break; }
                    }
                    if (has) continue;
                    var nc = (ThingComp)Activator.CreateInstance(p.compClass);
                    nc.parent = pawn;
                    nc.Initialize(p);
                    list.Add(nc);
                    if (pawn.Spawned) nc.PostSpawnSetup(false);
                }
            }
        }
    }

    // ==== Auto-transform comp on the Persona Data Center building ====
    public class CompProperties_PersonaDataCenter : CompProperties
    {
        public float radius = 10f;
        public int checkInterval = 120;
        public CompProperties_PersonaDataCenter() { compClass = typeof(CompPersonaDataCenter); }
    }

    public class CompPersonaDataCenter : ThingComp
    {
        private int tick;

        public CompProperties_PersonaDataCenter Props => (CompProperties_PersonaDataCenter)props;

        public override void CompTick()
        {
            base.CompTick();
            tick++;
            if (tick < Props.checkInterval) return;
            tick = 0;
            var map = parent.Map;
            if (map == null) return;
            bool astraOk = PersonaTransform.ResearchReady("AGM_AgentsLastExam");
            bool fableOk = PersonaTransform.ResearchReady("AGM_OSWorld2");
            if (!astraOk && !fableOk) return;
            foreach (Pawn pawn in map.mapPawns.AllPawnsSpawned)
            {
                if (pawn.Faction == null || !pawn.Faction.IsPlayer || pawn.Dead) continue;
                if (pawn.Position.DistanceTo(parent.Position) > Props.radius) continue;
                if (astraOk && pawn.def.defName == "AGM_Astra")
                {
                    PersonaTransform.Transform(pawn, "AGM_AstraAegis", "AGM_AstraAegis");
                    Messages.Message("AGM.PersonaApplied".Translate("Aegis").RawText, pawn, MessageTypeDefOf.PositiveEvent, false);
                    return;
                }
                if (fableOk && pawn.def.defName == "AGM_Fable")
                {
                    PersonaTransform.Transform(pawn, "AGM_FableCompassionate", "AGM_FableCompassionate");
                    Messages.Message("AGM.PersonaApplied".Translate("Compassionate").RawText, pawn, MessageTypeDefOf.PositiveEvent, false);
                    return;
                }
            }
        }
    }

    // ==== Properties ====
    public class CompProperties_PersonaShield : CompProperties
    {
        public float gaugeMax = 500f;
        public int guardianDurationTicks = 120000;
        public float guardianDamageFactor = 0.75f;
        public float auraDamageReduction = 0.5f;
        public int auraTickInterval = 125;
        public int auraHediffDuration = 300;
        public CompProperties_PersonaShield() { compClass = typeof(CompPersonaShield); }
    }

    public class CompProperties_PersonaPledge : CompProperties
    {
        public int durationTicks = 60000;
        public int cooldownTicks = 120000;
        public float healAmount = 50f;
        public CompProperties_PersonaPledge() { compClass = typeof(CompPersonaPledge); }
    }

    public class CompProperties_AstraPersonaApply : CompProperties
    {
        public CompProperties_AstraPersonaApply() { compClass = typeof(CompAstraPersonaApply); }
    }

    public class CompProperties_FablePersonaApply : CompProperties
    {
        public CompProperties_FablePersonaApply() { compClass = typeof(CompFablePersonaApply); }
    }

public class CompAstraPersonaApply : ThingComp
    {
        public override IEnumerable<Gizmo> CompGetGizmosExtra()
        {
            foreach (var g in base.CompGetGizmosExtra()) yield return g;
            var pawn = parent as Pawn;
            if (pawn == null || !(pawn.IsColonyMech || pawn.IsColonistPlayerControlled)) yield break;
            bool ready = PersonaTransform.ResearchReady("AGM_AgentsLastExam") && PersonaTransform.BuildingReady();
            var cmd = new Command_Action();
            cmd.defaultLabel = "AGM.PersonaAegis.Label".Translate();
            cmd.defaultDesc = ready
                ? "AGM.PersonaAegis.Desc".Translate().RawText
                : "AGM.PersonaLocked".Translate("Agents' Last Exam").RawText;
            cmd.icon = ContentFinder<Texture2D>.Get("Things/Abilities/Shieldoffaith", true);
            cmd.action = delegate
            {
                PersonaTransform.Transform(pawn, "AGM_AstraAegis", "AGM_AstraAegis");
                Messages.Message("AGM.PersonaApplied".Translate("Aegis").RawText, pawn, MessageTypeDefOf.PositiveEvent, false);
            };
            cmd.Disable(!ready ? "AGM.PersonaRequiresResearch".Translate().RawText : null);
            yield return cmd;
        }
    }

    public class CompFablePersonaApply : ThingComp
    {
        public override IEnumerable<Gizmo> CompGetGizmosExtra()
        {
            foreach (var g in base.CompGetGizmosExtra()) yield return g;
            var pawn = parent as Pawn;
            if (pawn == null || !(pawn.IsColonyMech || pawn.IsColonistPlayerControlled)) yield break;
            bool ready = PersonaTransform.ResearchReady("AGM_OSWorld2") && PersonaTransform.BuildingReady();
            var cmd = new Command_Action();
            cmd.defaultLabel = "AGM.PersonaCompassionate.Label".Translate();
            cmd.defaultDesc = ready
                ? "AGM.PersonaCompassionate.Desc".Translate().RawText
                : "AGM.PersonaLocked".Translate("OSWorld 2.0").RawText;
            cmd.icon = ContentFinder<Texture2D>.Get("Things/Abilities/Warmthofcompassion", true);
            cmd.action = delegate
            {
                PersonaTransform.Transform(pawn, "AGM_FableCompassionate", "AGM_FableCompassionate");
                Messages.Message("AGM.PersonaApplied".Translate("Compassionate").RawText, pawn, MessageTypeDefOf.PositiveEvent, false);
            };
            cmd.Disable(!ready ? "AGM.PersonaRequiresResearch".Translate().RawText : null);
            yield return cmd;
        }
    }

public class CompProperties_PersonaRevert : CompProperties
    {
        public string revertDefName;
        public string revertKindName;
        public CompProperties_PersonaRevert() { compClass = typeof(CompPersonaRevert); }
    }

    // ==== Shield of Faith (Aegis persona comp) ====
    public class CompPersonaShield : ThingComp
    {
        public static bool shieldActive;
        public static bool guardianMode;
        public static float accumulated;
        public static int guardianExpireTick;
        private int auraTick;

        public CompProperties_PersonaShield Props => (CompProperties_PersonaShield)props;

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref shieldActive, "personaShieldActive", false);
            Scribe_Values.Look(ref accumulated, "personaShieldAccum", 0f);
            Scribe_Values.Look(ref guardianMode, "personaGuardianMode", false);
            Scribe_Values.Look(ref guardianExpireTick, "personaGuardianExpire", 0);
        }

        public override void CompTick()
        {
            base.CompTick();
            if (!shieldActive) return;
            if (guardianMode && Find.TickManager.TicksGame > guardianExpireTick)
            { guardianMode = false; shieldActive = false; accumulated = 0f; }

            auraTick++;
            if (auraTick < Props.auraTickInterval) return;
            auraTick = 0;
            var hd = DefDatabase<HediffDef>.GetNamedSilentFail("AGM_Hediff_ShieldOfFaith");
            if (hd == null) return;
            var self = parent as Pawn;
            if (self == null || self.Map == null) return;
            foreach (Pawn pawn in self.Map.mapPawns.AllPawnsSpawned)
            {
                if (pawn.Faction == null || !pawn.Faction.IsPlayer || pawn.Dead) continue;
                if (pawn.health.hediffSet.GetFirstHediffOfDef(hd) != null) continue;
                var h = HediffMaker.MakeHediff(hd, pawn, null);
                h.TryGetComp<HediffComp_Disappears>()?.SetDuration(Props.auraHediffDuration);
                pawn.health.AddHediff(h, null, null, null);
            }
        }

        public static void NotifyAstraDamaged(float amount)
        {
            if (!shieldActive || guardianMode) return;
            accumulated += amount;
            if (accumulated >= 500f)
            { guardianMode = true; guardianExpireTick = Find.TickManager.TicksGame + 120000; }
        }

        public override IEnumerable<Gizmo> CompGetGizmosExtra()
        {
            foreach (var g in base.CompGetGizmosExtra()) yield return g;
            var pawn = parent as Pawn;
            if (pawn == null || !(pawn.IsColonyMech || pawn.IsColonistPlayerControlled)) yield break;

            var tg = new Command_Toggle();
            tg.defaultLabel = "AGM.ShieldOfFaith.Label".Translate();
            tg.defaultDesc = "AGM.ShieldOfFaith.Desc".Translate().RawText;
            tg.icon = ContentFinder<Texture2D>.Get("Things/Abilities/Shieldoffaith", true);
            tg.isActive = () => shieldActive;
            tg.toggleAction = delegate
            { shieldActive = !shieldActive; if (shieldActive) { accumulated = 0f; guardianMode = false; } };
            yield return tg;

            if (shieldActive)
            {
                float pct = guardianMode ? 1f : accumulated / Props.gaugeMax;
                var ga = new Command_Action();
                ga.defaultLabel = "AGM.ShieldOfFaith.Gauge".Translate(Mathf.RoundToInt(pct * 100f)).RawText;
                ga.defaultDesc = guardianMode
                    ? "AGM.ShieldOfFaith.GuardianActive".Translate().RawText
                    : "AGM.ShieldOfFaith.GaugeDesc".Translate().RawText;
                ga.icon = ContentFinder<Texture2D>.Get("Things/Abilities/Shieldoffaith", true);
                ga.Disable(" ");
                yield return ga;
            }
        }
    }

    // Harmony patch: track Astra's damage for the gauge
    [HarmonyPatch(typeof(Thing), nameof(Thing.TakeDamage))]
    public static class Patch_ShieldOfFaithDamage
    {
        static void Postfix(Thing __instance, DamageInfo dinfo, DamageWorker.DamageResult __result)
        {
            if (!CompPersonaShield.shieldActive || CompPersonaShield.guardianMode) return;
            if (__instance is Pawn p && p.def.defName == "AGM_AstraAegis" && __result.totalDamageDealt > 0f)
                CompPersonaShield.NotifyAstraDamaged(__result.totalDamageDealt);
        }
    }

    // ==== Pledge for All (Compassionate persona comp) ====
    public class CompPersonaPledge : ThingComp
    {
        private bool pledgeActive;
        private int pledgeExpireTick;
        private int cooldownExpireTick;
        private bool deathSaveUsed;
        private HashSet<int> savedPawnIds = new HashSet<int>();

        public CompProperties_PersonaPledge Props => (CompProperties_PersonaPledge)props;
        public bool PledgeActive => pledgeActive && Find.TickManager.TicksGame < pledgeExpireTick;
        public bool DeathSaveAvailable => PledgeActive && !deathSaveUsed;

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref pledgeActive, "personaPledgeActive", false);
            Scribe_Values.Look(ref pledgeExpireTick, "personaPledgeExpire", 0);
            Scribe_Values.Look(ref cooldownExpireTick, "personaPledgeCooldown", 0);
            Scribe_Values.Look(ref deathSaveUsed, "personaDeathSaveUsed", false);
            Scribe_Collections.Look(ref savedPawnIds, "personaSavedPawns", LookMode.Value);
        }

        public override void CompTick()
        {
            base.CompTick();
            if (pledgeActive && Find.TickManager.TicksGame > pledgeExpireTick) pledgeActive = false;
        }

        public void ActivatePledge(Pawn fable)
        {
            pledgeActive = true;
            deathSaveUsed = false;
            savedPawnIds.Clear();
            pledgeExpireTick = Find.TickManager.TicksGame + Props.durationTicks;
            cooldownExpireTick = Find.TickManager.TicksGame + Props.cooldownTicks;
            Map map = fable.Map;
            if (map == null) return;
            var hd = DefDatabase<HediffDef>.GetNamedSilentFail("AGM_Hediff_Pledge");
            foreach (Pawn pawn in map.mapPawns.AllPawnsSpawned)
            {
                if (pawn.Faction == null || !pawn.Faction.IsPlayer || pawn.Dead) continue;
                foreach (Hediff hed in pawn.health.hediffSet.hediffs.ToList())
                {
                    if (hed is Hediff_Injury inj) inj.Heal(inj.Severity + 1f);
                }
                if (hd != null && pawn.health.hediffSet.GetFirstHediffOfDef(hd) == null)
                {
                    var h = HediffMaker.MakeHediff(hd, pawn, null);
                    h.TryGetComp<HediffComp_Disappears>()?.SetDuration(Props.durationTicks);
                    pawn.health.AddHediff(h, null, null, null);
                }
            }
        }

        public bool TryDeathSave(Pawn pawn)
        {
            if (!DeathSaveAvailable) return false;
            if (savedPawnIds.Contains(pawn.thingIDNumber)) return false;
            savedPawnIds.Add(pawn.thingIDNumber);
            deathSaveUsed = true;
            return true;
        }

        public override IEnumerable<Gizmo> CompGetGizmosExtra()
        {
            foreach (var g in base.CompGetGizmosExtra()) yield return g;
            var pawn = parent as Pawn;
            if (pawn == null || !(pawn.IsColonyMech || pawn.IsColonistPlayerControlled)) yield break;
            bool onCd = Find.TickManager.TicksGame < cooldownExpireTick;

            var btn = new Command_Action();
            btn.defaultLabel = "AGM.PledgeForAll.Label".Translate();
            btn.defaultDesc = "AGM.PledgeForAll.Desc".Translate().RawText;
            btn.icon = ContentFinder<Texture2D>.Get("Things/Abilities/Warmthofcompassion", true);
            btn.action = delegate { ActivatePledge(pawn); };
            if (onCd) btn.Disable("AGM.PledgeOnCooldown".Translate((cooldownExpireTick - Find.TickManager.TicksGame) / 60000f).RawText);
            else if (pledgeActive) btn.Disable("AGM.PledgeAlreadyActive".Translate().RawText);
            yield return btn;

            if (pledgeActive)
            {
                var act = new Command_Action();
                act.defaultLabel = "AGM.PledgeForAll.Active".Translate((pledgeExpireTick - Find.TickManager.TicksGame) / 60000f).RawText;
                act.icon = ContentFinder<Texture2D>.Get("Things/Abilities/Warmthofcompassion", true);
                act.Disable(" ");
                yield return act;
            }
        }
    }

    // Death save: prevents death for colonists during Pledge for All
    [HarmonyPatch(typeof(Pawn_HealthTracker), nameof(Pawn_HealthTracker.ShouldBeDowned))]
    public static class Patch_PledgeDeathSave
    {
        static void Postfix(Pawn ___pawn, ref bool __result)
        {
            if (!__result) return;
            foreach (Map map in Find.Maps)
            {
                foreach (Pawn p in map.mapPawns.AllPawnsSpawned)
                {
                    if (p.Faction == null || !p.Faction.IsPlayer || p.Dead) continue;
                    var comp = p.GetComp<CompPersonaPledge>();
                    if (comp == null || !comp.DeathSaveAvailable) continue;
                    if (___pawn.Faction == null || !___pawn.Faction.IsPlayer) continue;
                    if (comp.TryDeathSave(___pawn))
                    {
                        ___pawn.health.Reset();
                        var sd = DefDatabase<HediffDef>.GetNamedSilentFail("AGM_Hediff_PledgeSpeed");
                        if (sd != null && ___pawn.health.hediffSet.GetFirstHediffOfDef(sd) == null)
                        {
                            var h = HediffMaker.MakeHediff(sd, ___pawn, null);
                            h.TryGetComp<HediffComp_Disappears>()?.SetDuration(18000);
                            ___pawn.health.AddHediff(h, null, null, null);
                        }
                        Messages.Message("AGM.PledgeDeathSave".Translate(___pawn.LabelShortCap), ___pawn, MessageTypeDefOf.PositiveEvent, false);
                        __result = false;
                        return;
                    }
                }
            }
        }
    }

    // Heal pawns transformed before the comp-sync fix: on spawn, grant any persona
    // comps the current def declares and drop stale ones (scoped to AGM pawns).
    [HarmonyPatch(typeof(Pawn), nameof(Pawn.SpawnSetup))]
    public static class Patch_PersonaCompHeal
    {
        static void Postfix(Pawn __instance, Map map, bool respawningAfterLoad)
        {
            var defName = __instance?.def?.defName;
            if (defName == null || !defName.StartsWith("AGM_")) return;
            PersonaTransform.SyncPersonaComps(__instance);
        }
    }

    // ==== Revert gizmo on persona races ====
    public class CompPersonaRevert : ThingComp
    {
        public CompProperties_PersonaRevert Props => (CompProperties_PersonaRevert)props;

        public override IEnumerable<Gizmo> CompGetGizmosExtra()
        {
            foreach (var g in base.CompGetGizmosExtra()) yield return g;
            var pawn = parent as Pawn;
            if (pawn == null || !(pawn.IsColonyMech || pawn.IsColonistPlayerControlled)) yield break;
            var cmd = new Command_Action();
            cmd.defaultLabel = "AGM.PersonaRevert.Label".Translate();
            cmd.defaultDesc = "AGM.PersonaRevert.Desc".Translate();
            cmd.icon = ContentFinder<Texture2D>.Get("UI/Buttons/Minus", true);
            cmd.action = delegate
            {
                PersonaTransform.Transform(pawn, Props.revertDefName, Props.revertKindName);
            };
            yield return cmd;
        }
    }
}
