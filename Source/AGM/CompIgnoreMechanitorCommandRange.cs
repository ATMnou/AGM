using Verse;

namespace AGM
{
    // Marker comp, checked by Patch_IgnoreMechanitorCommandRange in HarmonyPatchesMaidnoid.cs.
    // No behavior of its own - ported from Instruments for Extinction's CompIgnoreMechanitorCommandRange
    // so MFE-Origin has no compile- or load-time dependency on IFE.
    public class CompProperties_IgnoreMechanitorCommandRange : CompProperties
    {
        public CompProperties_IgnoreMechanitorCommandRange()
        {
            compClass = typeof(CompIgnoreMechanitorCommandRange);
        }
    }

    public class CompIgnoreMechanitorCommandRange : ThingComp
    {
    }
}
