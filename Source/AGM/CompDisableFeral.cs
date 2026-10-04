using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using RimWorld;
using Verse;

namespace AGM
{
    // Marker comp: pawns carrying it are never flagged feral. Vanilla BaseMechanoid keeps its
    // CompProperties_OverseerSubject (needed for overseer/charge bookkeeping); this postfix on
    // CompOverseerSubject.CanGoFeral simply nullifies the feral roll for AGM mechs.
    public class CompProperties_DisableFeral : CompProperties
    {
        public CompProperties_DisableFeral()
        {
            compClass = typeof(CompDisableFeral);
        }
    }

    public class CompDisableFeral : ThingComp
    {
    }

    [HarmonyPatch]
    public static class Patch_CanGoFeral
    {
        static System.Collections.Generic.IEnumerable<MethodBase> TargetMethods()
        {
            MethodBase getter = AccessTools.PropertyGetter(typeof(CompOverseerSubject), "CanGoFeral");
            if (getter == null)
            {
                getter = AccessTools.Method(typeof(CompOverseerSubject), "CanGoFeral");
            }
            if (getter != null)
            {
                yield return getter;
            }
        }

        static void Postfix(ThingWithComps ___parent, ref bool __result)
        {
            if (__result && ___parent != null && ___parent.GetComp<CompDisableFeral>() != null)
            {
                __result = false;
            }
        }
    }
}
