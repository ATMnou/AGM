using System.Collections.Generic;
using System.Linq;
using RimWorld;
using Verse;

namespace AGM
{
    // Periodically applies a hediff to same-faction pawns around the parent building/pawn.
    // Generic aura used by the batch-2 maidnoids (morale, work-speed, inspiration fields).
    // The hediff itself should carry HediffCompProperties_Disappears so it expires and the
    // aura refreshes it while targets stay in range.
    public class CompProperties_AoeAura : CompProperties
    {
        public float radius = 8f;
        public int tickInterval = 125;
        public HediffDef hediff;
        public int hediffDurationTicks = 300;
        public bool humanlikeOnly = true;

        public CompProperties_AoeAura()
        {
            compClass = typeof(CompAoeAura);
        }
    }

    public class CompAoeAura : ThingComp
    {
        private int tickCounter;

        public CompProperties_AoeAura Props => (CompProperties_AoeAura)props;

        public override void CompTick()
        {
            base.CompTick();
            tickCounter++;
            if (tickCounter < Props.tickInterval)
            {
                return;
            }
            tickCounter = 0;
            Map map = parent.Map;
            if (map == null || Props.hediff == null || parent.Faction == null)
            {
                return;
            }
            foreach (Thing thing in GenRadial.RadialDistinctThingsAround(parent.Position, map, Props.radius, true))
            {
                Pawn pawn = thing as Pawn;
                if (pawn == null || pawn.Dead || pawn.health == null)
                {
                    continue;
                }
                if (pawn.Faction != parent.Faction)
                {
                    continue;
                }
                if (Props.humanlikeOnly && !pawn.RaceProps.Humanlike)
                {
                    continue;
                }
                Hediff hediff = pawn.health.hediffSet.GetFirstHediffOfDef(Props.hediff);
                if (hediff != null)
                {
                    hediff.TryGetComp<HediffComp_Disappears>()?.SetDuration(Props.hediffDurationTicks);
                    continue;
                }
                Hediff made = HediffMaker.MakeHediff(Props.hediff, pawn, null);
                made.TryGetComp<HediffComp_Disappears>()?.SetDuration(Props.hediffDurationTicks);
                pawn.health.AddHediff(made, null, null, null);
            }
        }
    }
}
