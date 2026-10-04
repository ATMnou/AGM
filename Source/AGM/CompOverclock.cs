using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace AGM
{
    public class CompProperties_Overclock : CompProperties
    {
        public float statMultiplier = 2.0f;
        public float drainPerDay = 0.10f;
        public float rechargePerDay = 0.20f;
        public string iconPath = "Things/Abilities/Overclock";

        public CompProperties_Overclock()
        {
            compClass = typeof(CompOverclock);
        }
    }

    // Ported from Instruments for Extinction's CompOverclock so MFE-Origin has no compile- or
    // load-time dependency on IFE. XM-05 Thanatos's toggleable output boost: while active, doubles
    // MoveSpeed and WorkSpeedGlobal (applied via Patch_Overclock_StatBoost in HarmonyPatchesMaidnoid.cs)
    // at the cost of a self-contained 0-1 energy reserve that drains while active and slowly
    // recharges while idle. Auto-disables the moment the reserve hits zero.
    public class CompOverclock : ThingComp
    {
        private const float TicksPerDay = 60000f;

        private bool active;
        private float reserve = 1f;
        private Texture2D iconCached;

        public CompProperties_Overclock Props => (CompProperties_Overclock)props;

        public bool Active => active;

        public float StatMultiplier => active ? Props.statMultiplier : 1f;

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref active, "overclockActive", false);
            Scribe_Values.Look(ref reserve, "overclockReserve", 1f);
        }

        public override void CompTick()
        {
            base.CompTick();

            if (active)
            {
                reserve -= Props.drainPerDay / TicksPerDay;
                if (reserve <= 0f)
                {
                    reserve = 0f;
                    active = false;
                }
            }
            else if (reserve < 1f)
            {
                reserve = Mathf.Min(1f, reserve + Props.rechargePerDay / TicksPerDay);
            }
        }

        public override string CompInspectStringExtra()
        {
            return "AGM.OverclockReserveStatus".Translate(Mathf.RoundToInt(reserve * 100f));
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

            yield return new Command_Toggle
            {
                defaultLabel = "AGM.OverclockLabel".Translate(),
                defaultDesc = "AGM.OverclockDesc".Translate(Mathf.RoundToInt(reserve * 100f)),
                icon = iconCached,
                isActive = () => active,
                disabledReason = (!active && reserve <= 0f) ? "AGM.OverclockNoReserve".Translate() : null,
                toggleAction = () => active = !active
            };
        }
    }
}
