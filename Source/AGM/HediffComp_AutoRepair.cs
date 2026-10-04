using System.Collections.Generic;
using RimWorld;
using Verse;

namespace AGM
{
    // Simple self-repair hediff comp (used by Luna's passive fortification hediff): heals the
    // most damaged injury by healAmount every tickInterval ticks. Replaces Total Warfare's
    // NCL.HediffCompProperties_MechAutoRecovery so AGM stays standalone.
    public class HediffCompProperties_AutoRepair : HediffCompProperties
    {
        public int tickInterval = 180;
        public float healAmount = 5f;

        public HediffCompProperties_AutoRepair()
        {
            compClass = typeof(HediffComp_AutoRepair);
        }
    }

    public class HediffComp_AutoRepair : HediffComp
    {
        private int tickCounter;

        public HediffCompProperties_AutoRepair Props => (HediffCompProperties_AutoRepair)props;

        public override void CompPostTick(ref float severityAdjustment)
        {
            base.CompPostTick(ref severityAdjustment);
            tickCounter++;
            if (tickCounter < Props.tickInterval)
            {
                return;
            }
            tickCounter = 0;
            Pawn pawn = Pawn;
            if (pawn == null || pawn.health == null || pawn.Dead)
            {
                return;
            }
            foreach (Hediff hediff in pawn.health.hediffSet.hediffs)
            {
                if (hediff is Hediff_Injury injury && injury.CanHealNaturally())
                {
                    injury.Heal(Props.healAmount);
                    break;
                }
            }
        }
    }
}
