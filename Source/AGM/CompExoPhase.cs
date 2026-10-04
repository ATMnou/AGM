using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace AGM
{
    public class CompProperties_ExoPhase : CompProperties
    {
        // Ascending list of health fractions at which the phase advances (Infernum Exo Mech
        // thresholds: 0.85 / 0.625 / 0.5). phaseSpeedFactors[i] is the IAttackSpeedModifier
        // factor while CurrentPhase == i + 1, so the list has one more entry than thresholds.
        public List<float> phaseHealthPcts = new List<float>();
        public List<float> phaseSpeedFactors = new List<float>();

        public CompProperties_ExoPhase()
        {
            compClass = typeof(CompExoPhase);
        }
    }

    // Generic Infernum-style phase machine for the exo mechs: as the pawn takes damage it
    // permanently climbs through phases, each one speeding up every IExoMechWeapon on the body.
    // CompAutoWeapon/CompDashVolley/etc. read CurrentPhase to gate weapons (minPhase) and add
    // phase-bonus projectiles, mirroring how Infernum strengthens its attack patterns per phase.
    public class CompExoPhase : ThingComp, IAttackSpeedModifier
    {
        private int currentPhase = 1;

        public CompProperties_ExoPhase Props => (CompProperties_ExoPhase)props;

        public int CurrentPhase => currentPhase;

        public int MaxPhase => Props.phaseHealthPcts.Count + 1;

        float IAttackSpeedModifier.AttackSpeedFactor
        {
            get
            {
                int i = Mathf.Clamp(currentPhase - 1, 0, Props.phaseSpeedFactors.Count - 1);
                return Props.phaseSpeedFactors.Count > 0 ? Props.phaseSpeedFactors[i] : 1f;
            }
        }

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref currentPhase, "exoPhaseCurrent", 1);
        }

        public override void CompTick()
        {
            base.CompTick();

            Pawn pawn = parent as Pawn;
            if (pawn == null || !pawn.Spawned || pawn.Dead || pawn.health == null)
            {
                return;
            }

            if (currentPhase >= MaxPhase)
            {
                return;
            }

            float healthPct = pawn.health.summaryHealth.SummaryHealthPercent;
            if (healthPct > Props.phaseHealthPcts[currentPhase - 1])
            {
                return;
            }

            currentPhase++;
            // In-game message instead of a letter - phase advances are routine combat feedback,
            // not something that should stack up in the letter stack.
            TaggedString text = ("AGM.ExoPhaseAdvanceLabel".Translate(currentPhase) + " " + "AGM.ExoPhaseAdvanceText".Translate(pawn.LabelShort, currentPhase)).RawText;
            Messages.Message(text, new LookTargets(pawn), MessageTypeDefOf.NeutralEvent, false);
        }

        public override string CompInspectStringExtra()
        {
            return "AGM.ExoPhaseStatus".Translate(currentPhase, MaxPhase);
        }
    }

    public static class ExoPhaseUtility
    {
        // Current combat phase (1-based) of any exo mech, whichever phase comp it carries:
        // CompExoPhase (Ares, Artemis/Apollo) or the older CompPlaguePhase (Plaguebringer Goliath).
        public static int CurrentPhase(ThingWithComps thing)
        {
            CompExoPhase exoPhase = thing.GetComp<CompExoPhase>();
            if (exoPhase != null)
            {
                return exoPhase.CurrentPhase;
            }

            return 1;
        }
    }
}
