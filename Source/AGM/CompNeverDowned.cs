using HarmonyLib;
using RimWorld;
using Verse;

namespace AGM
{
    // Marker comp + patch: persona-grade AGM mechs (Argon / Flash) never go downed -
    // they fight on until destroyed. Ported in spirit from ProtossMechPersonaHero's
    // CompNeverDowned so AGM carries no dependency on that mod.
    public class CompProperties_NeverDowned : CompProperties
    {
        public CompProperties_NeverDowned()
        {
            compClass = typeof(CompNeverDowned);
        }
    }

    public class CompNeverDowned : ThingComp
    {
    }

    [HarmonyPatch(typeof(Pawn_HealthTracker), "ShouldBeDowned")]
    public static class Patch_NeverDowned
    {
        static void Postfix(Pawn ___pawn, ref bool __result)
        {
            if (__result && ___pawn != null && ___pawn.GetComp<CompNeverDowned>() != null)
            {
                __result = false;
            }
        }
    }
}
