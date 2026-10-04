using System.Collections.Generic;
using HarmonyLib;
using RimWorld;
using Verse;
using Verse.AI;

namespace AGM
{
    // Harmony patches backing the comps ported from Instruments for Extinction (CompIgnoreMechanitorCommandRange,
    // CompReconstruction, CompOverclock) so MFE-Origin has no compile- or load-time dependency on IFE.
    // Mirrors IFE's own HarmonyPatches.cs patches of the same names exactly.

    // Any pawn carrying CompIgnoreMechanitorCommandRange can be commanded (move/attack orders)
    // from anywhere on the map, regardless of distance from its mechanitor.
    [HarmonyPatch(typeof(MechanitorUtility), "InMechanitorCommandRange")]
    public static class Patch_IgnoreMechanitorCommandRange
    {
        static bool Prefix(Pawn mech, LocalTargetInfo target, ref bool __result)
        {
            if (mech != null && mech.GetComp<CompIgnoreMechanitorCommandRange>() != null)
            {
                __result = true;
                return false;
            }
            return true;
        }
    }

    // A pawn carrying CompReconstruction that is off cooldown survives lethal damage: instead of
    // dying, its repair drones fully rebuild it (CompReconstruction.DoReconstruct).
    [HarmonyPatch(typeof(Pawn), nameof(Pawn.Kill))]
    public static class Patch_Reconstruction_PreventDeath
    {
        static bool Prefix(Pawn __instance)
        {
            CompReconstruction comp = __instance.GetComp<CompReconstruction>();
            if (comp != null && comp.CanReviveNow)
            {
                comp.DoReconstruct();
                return false;
            }
            return true;
        }
    }

    // XM-05 Thanatos's overclock toggle (CompOverclock) doubles MoveSpeed and WorkSpeedGlobal
    // while active.
    [HarmonyPatch(typeof(StatWorker), nameof(StatWorker.GetValue), typeof(StatRequest), typeof(bool))]
    public static class Patch_Overclock_StatBoost
    {
        private static readonly HashSet<StatDef> boostedStats = new HashSet<StatDef>();
        private static bool initialized;

        private static void EnsureInitialized()
        {
            if (initialized)
            {
                return;
            }
            initialized = true;

            void Add(string defName)
            {
                StatDef def = DefDatabase<StatDef>.GetNamedSilentFail(defName);
                if (def != null)
                {
                    boostedStats.Add(def);
                }
            }

            Add("MoveSpeed");
            Add("WorkSpeedGlobal");
        }

        static void Postfix(StatRequest req, ref float __result, StatDef ___stat)
        {
            EnsureInitialized();

            if (!boostedStats.Contains(___stat) || !(req.Thing is Pawn pawn))
            {
                return;
            }

            CompOverclock comp = pawn.GetComp<CompOverclock>();
            if (comp != null && comp.Active)
            {
                __result *= comp.StatMultiplier;
            }
        }
    }
}
