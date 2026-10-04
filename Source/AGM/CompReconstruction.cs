using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace AGM
{
    public class CompProperties_Reconstruction : CompProperties
    {
        public int cooldownTicks = 3600;
        public HediffDef reconstructHediff;
        public string iconPath = "Things/Abilities/Reconstruction";

        public CompProperties_Reconstruction()
        {
            compClass = typeof(CompReconstruction);
        }
    }

    // Ported from Instruments for Extinction's CompReconstruction so MFE-Origin has no compile- or
    // load-time dependency on IFE. Fully heals the pawn and removes all injuries, then leaves it
    // briefly all-but-invulnerable and immobile while its repair drones finish (reconstructHediff),
    // before going on a long cooldown. Can be triggered manually via the gizmo below, and is also
    // triggered automatically instead of dying - see Patch_Reconstruction_PreventDeath.
    public class CompReconstruction : ThingComp
    {
        private int lastUsedTick = -999999;
        private Texture2D iconCached;

        public CompProperties_Reconstruction Props => (CompProperties_Reconstruction)props;

        public bool CanReviveNow => Find.TickManager.TicksGame - lastUsedTick >= Props.cooldownTicks;

        public int TicksUntilReady => Mathf.Max(0, Props.cooldownTicks - (Find.TickManager.TicksGame - lastUsedTick));

        public void DoReconstruct()
        {
            Pawn pawn = parent as Pawn;
            if (pawn == null || pawn.Map == null)
            {
                return;
            }

            lastUsedTick = Find.TickManager.TicksGame;

            pawn.health.Reset();

            if (Props.reconstructHediff != null)
            {
                Hediff hediff = HediffMaker.MakeHediff(Props.reconstructHediff, pawn, null);
                pawn.health.AddHediff(hediff, null, null, null);
            }

            FleckMaker.Static(pawn.DrawPos, pawn.Map, FleckDefOf.ShotFlash, 12f);
        }

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref lastUsedTick, "lastUsedTick", -999999);
        }

        public override IEnumerable<Gizmo> CompGetGizmosExtra()
        {
            foreach (Gizmo g in base.CompGetGizmosExtra())
            {
                yield return g;
            }

            if (iconCached == null)
            {
                iconCached = ContentFinder<Texture2D>.Get(Props.iconPath, true);
            }

            bool ready = CanReviveNow;
            yield return new Command_Action
            {
                defaultLabel = "Reconstruct",
                defaultDesc = ready
                    ? "Instantly repair all damage and remove all injuries. The repair drones then need time to recharge."
                    : "Reconstruction is recharging: " + (TicksUntilReady / 60f).ToString("F0") + "s remaining.",
                icon = iconCached,
                disabledReason = ready ? null : "Not ready yet.",
                action = ready ? (System.Action)DoReconstruct : null
            };
        }
    }
}
