using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.Sound;

namespace AGM
{
    // EXAONE's three roars (design sheet EXAONE.txt). Gizmo-button abilities with
    // per-roar cooldowns, mirroring the persona-comps pattern (no AbilityDef needed).
    public class CompProperties_ExaoneRoars : CompProperties
    {
        public int retreatCooldownTicks = 120000;
        public int frenzyCooldownTicks = 180000;
        public int damageCooldownTicks = 180000;

        public CompProperties_ExaoneRoars()
        {
            compClass = typeof(CompExaoneRoars);
        }
    }

    public class CompExaoneRoars : ThingComp
    {
        private int retreatReadyTick;
        private int frenzyReadyTick;
        private int damageReadyTick;

        public CompProperties_ExaoneRoars Props => (CompProperties_ExaoneRoars)props;

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref retreatReadyTick, "exaoneRetreatReady", 0);
            Scribe_Values.Look(ref frenzyReadyTick, "exaoneFrenzyReady", 0);
            Scribe_Values.Look(ref damageReadyTick, "exaoneDamageReady", 0);
        }

        // Eager list: TakeDamage can kill (despawn) victims, which mutates
        // mapPawns mid-loop - a lazy yield would abort after the first kill.
        private static List<Pawn> Raiders(Map map)
        {
            var list = new List<Pawn>();
            if (map == null) return list;
            Faction player = Faction.OfPlayer;
            foreach (Pawn p in map.mapPawns.AllPawnsSpawned)
            {
                if (p == null || p.Dead) continue;
                if (!p.HostileTo(player)) continue;
                list.Add(p);
            }
            return list;
        }

        private static void Shockwave(Pawn caster)
        {
            AGMDefOf.AGM_Mythos_ImpactDustCloud.Spawn(caster, caster, 1.5f).Cleanup();
        }

        private void DoRetreat(Pawn caster)
        {
            var fled = 0;
            foreach (Pawn p in Raiders(caster.Map))
            {
                if (p.Downed || !p.RaceProps.Humanlike) continue;
                if (p.mindState?.mentalStateHandler == null) continue;
                if (p.mindState.mentalStateHandler.TryStartMentalState(
                        MentalStateDefOf.PanicFlee, "AGM.ExaoneRetreatReason".Translate()))
                    fled++;
            }
            if (fled == 0)
            {
                Messages.Message("AGM.ExaoneNoRaiders".Translate(), caster, MessageTypeDefOf.NeutralEvent, false);
                return;
            }
            AGMDefOf.AGM_Sound_ExaoneGrowl.PlayOneShot(caster);
            Shockwave(caster);
            Messages.Message("AGM.ExaoneRetreatUsed".Translate(fled), caster, MessageTypeDefOf.PositiveEvent, false);
            retreatReadyTick = Find.TickManager.TicksGame + Props.retreatCooldownTicks;
        }

        private void DoFrenzy(Pawn caster)
        {
            var maddened = 0;
            foreach (Pawn p in Raiders(caster.Map))
            {
                if (p.Downed) continue;
                if (p.mindState?.mentalStateHandler == null) continue;
                if (p.mindState.mentalStateHandler.TryStartMentalState(
                        MentalStateDefOf.Berserk, "AGM.ExaoneFrenzyReason".Translate()))
                    maddened++;
            }
            if (maddened == 0)
            {
                Messages.Message("AGM.ExaoneNoRaiders".Translate(), caster, MessageTypeDefOf.NeutralEvent, false);
                return;
            }
            AGMDefOf.AGM_Sound_ExaoneLaugh.PlayOneShot(caster);
            Shockwave(caster);
            Messages.Message("AGM.ExaoneFrenzyUsed".Translate(maddened), caster, MessageTypeDefOf.PositiveEvent, false);
            frenzyReadyTick = Find.TickManager.TicksGame + Props.frenzyCooldownTicks;
        }

        private void DoDamage(Pawn caster)
        {
            var broken = 0;
            foreach (Pawn p in Raiders(caster.Map))
            {
                if (p.Dead) continue;
                int amount = Mathf.Max(1, Mathf.RoundToInt(p.MaxHitPoints * 0.5f * Rand.Range(0.8f, 1.2f)));
                p.TakeDamage(new DamageInfo(DamageDefOf.Blunt, amount, 0.75f, -1f, caster));
                broken++;
            }
            if (broken == 0)
            {
                Messages.Message("AGM.ExaoneNoRaiders".Translate(), caster, MessageTypeDefOf.NeutralEvent, false);
                return;
            }
            AGMDefOf.AGM_Sound_ExaoneScream.PlayOneShot(caster);
            Shockwave(caster);
            Messages.Message("AGM.ExaoneDamageUsed".Translate(broken), caster, MessageTypeDefOf.PositiveEvent, false);
            damageReadyTick = Find.TickManager.TicksGame + Props.damageCooldownTicks;
        }

        private Command_Action RoarButton(string labelKey, string descKey, string iconPath,
            int readyTick, int cooldownTicks, System.Action<Pawn> act, Pawn caster)
        {
            var btn = new Command_Action();
            btn.defaultLabel = labelKey.Translate();
            btn.defaultDesc = descKey.Translate().RawText;
            btn.icon = ContentFinder<Texture2D>.Get(iconPath, true);
            btn.action = delegate { act(caster); };
            if (Find.TickManager.TicksGame < readyTick)
                btn.Disable("AGM.ExaoneOnCooldown".Translate((readyTick - Find.TickManager.TicksGame) / 60000f).RawText);
            return btn;
        }

        public override IEnumerable<Gizmo> CompGetGizmosExtra()
        {
            foreach (var g in base.CompGetGizmosExtra()) yield return g;
            var pawn = parent as Pawn;
            if (pawn == null || !(pawn.IsColonyMech || pawn.IsColonistPlayerControlled)) yield break;

            yield return RoarButton("AGM.ExaoneRetreat.Label", "AGM.ExaoneRetreat.Desc",
                "Things/Abilities/Exaone_Retreat", retreatReadyTick, Props.retreatCooldownTicks, DoRetreat, pawn);
            yield return RoarButton("AGM.ExaoneFrenzy.Label", "AGM.ExaoneFrenzy.Desc",
                "Things/Abilities/Exaone_Frenzy", frenzyReadyTick, Props.frenzyCooldownTicks, DoFrenzy, pawn);
            yield return RoarButton("AGM.ExaoneDamage.Label", "AGM.ExaoneDamage.Desc",
                "Things/Abilities/Exaone_Damage", damageReadyTick, Props.damageCooldownTicks, DoDamage, pawn);
        }
    }
}
