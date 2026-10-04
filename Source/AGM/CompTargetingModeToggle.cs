using System.Collections.Generic;
using RimWorld;
using Verse;

namespace AGM
{
    public class CompProperties_TargetingModeToggle : CompProperties
    {
        public CompProperties_TargetingModeToggle()
        {
            compClass = typeof(CompTargetingModeToggle);
        }
    }

    // Player-facing gizmo. Read by every CompAutoWeapon/CompAutoBeamWeapon on this pawn (via
    // AutoWeaponTargeting.GatherClaimedTargets) to decide whether each weapon should avoid
    // targets its siblings are already engaging.
    public class CompTargetingModeToggle : ThingComp
    {
        public bool multiTargetMode;

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref multiTargetMode, "multiTargetMode", false);
        }

        public override IEnumerable<Gizmo> CompGetGizmosExtra()
        {
            foreach (Gizmo g in base.CompGetGizmosExtra())
            {
                yield return g;
            }

            yield return new Command_Toggle
            {
                defaultLabel = (multiTargetMode ? "AGM.MultiTargetLabel" : "AGM.FocusFireLabel").Translate(),
                defaultDesc = "AGM.TargetingModeDesc".Translate(),
                icon = multiTargetMode ? TexCommand.FireAtWill : TexCommand.Attack,
                isActive = () => multiTargetMode,
                toggleAction = () => multiTargetMode = !multiTargetMode
            };
        }
    }
}
