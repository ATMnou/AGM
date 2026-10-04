using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using RimWorld;
using Verse;
using Verse.AI;

namespace AGM
{
    // GD3.FlyingRender_Patch port: while Mythos flies on the vanilla flight tracker, scale the
    // tracker's draw offset (vanilla FlyingOffset = 0.6 * PositionOffsetFactor) by the race's
    // IsFlyingUnit.flyingHeight (10) so the suspend/jump states lift the sprite clear off the
    // ground, exactly as the original Annihilator renders.
    [HarmonyPatch(typeof(Pawn_FlightTracker), "get_PositionOffsetFactor")]
    public static class Patch_Mythos_FlyingRender
    {
        public static void Postfix(Pawn ___pawn, ref float __result)
        {
            IsFlyingUnit ext = ___pawn.def.GetModExtension<IsFlyingUnit>();
            if (ext != null)
            {
                __result *= ext.flyingHeight;
            }
        }
    }

    // GD3.Notify_JobStarted_Patch port (flightDeterminedByCode). Vanilla combat jobs
    // (Wait_Combat / AttackStatic / AttackMelee / UseVerbOnThing*) carry tryStartFlying=true with
    // overrideFlyChance=1, which BYPASSES the race's flightStartChanceOnJobStart=0 and force-starts
    // flight the moment such a job begins - that's why Mythos auto-hovered right after being
    // recalled into a fight. With flightDeterminedByCode on the race def, job-driven takeoff is
    // suppressed entirely: Mythos only flies when OUR code calls flight.StartFlying() (the
    // suspend/jump techniques in Mythos_Pawn), exactly like the original mod.
    [HarmonyPatch(typeof(Pawn_FlightTracker), "Notify_JobStarted")]
    public static class Patch_Mythos_FlightDeterminedByCode
    {
        static bool Prefix(Pawn_FlightTracker __instance, Pawn ___pawn, ref Job job)
        {
            IsFlyingUnit ext = ___pawn.def.GetModExtension<IsFlyingUnit>();
            if (ext == null || !ext.flightDeterminedByCode)
            {
                return true;
            }

            // Never let job defs start flight on their own...
            if (!__instance.Flying)
            {
                job.flying = false;
                return false;
            }

            // ...and while airborne, only hold flight for jobs that keep it (or our own holds).
            if (job.def.ifFlyingKeepFlying || job.def.tryStartFlying)
            {
                job.flying = true;
                return false;
            }
            job.flying = false;
            return false;
        }
    }
}
