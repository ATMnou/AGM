using System.Collections.Generic;
using RimWorld;
using Verse;

namespace AGM
{
    // Silently adds a hediff to the pawn once on spawn. Replaces Total Warfare's
    // HediffGiverSet approach for Luna's passive fortification: givers can surface
    // "health condition" letters; this comp applies the hediff with no notifications.
    public class CompProperties_EnsureHediff : CompProperties
    {
        public HediffDef hediff;

        public CompProperties_EnsureHediff()
        {
            compClass = typeof(CompEnsureHediff);
        }
    }

    public class CompEnsureHediff : ThingComp
    {
        private bool added;

        public CompProperties_EnsureHediff Props => (CompProperties_EnsureHediff)props;

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            Add();
        }

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref added, "ensureHediffAdded", false);
        }

        public override void CompTick()
        {
            base.CompTick();
            if (!added)
            {
                Add();
            }
        }

        private void Add()
        {
            Pawn pawn = parent as Pawn;
            if (pawn == null || pawn.health == null || pawn.Dead || added)
            {
                return;
            }
            if (Props.hediff != null && !pawn.health.hediffSet.HasHediff(Props.hediff))
            {
                pawn.health.AddHediff(HediffMaker.MakeHediff(Props.hediff, pawn, null), null, null, null);
            }
            added = true;
        }
    }
}
