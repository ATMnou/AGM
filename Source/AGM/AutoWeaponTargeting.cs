using System.Collections.Generic;
using UnityEngine;
using Verse;
using Verse.AI;

namespace AGM
{
    // Implemented by every independent weapon comp on Ares (CompAutoWeapon, CompAutoBeamWeapon)
    // so the shared targeting helper and CompTargetingModeToggle can see what each weapon is
    // currently pointed at without needing to know about each other's concrete type.
    public interface IExoMechWeapon
    {
        LocalTargetInfo CurrentTarget { get; }
    }

    // Implemented by any comp that wants to speed up (>1) or slow down (<1) every weapon and
    // spawner comp on the same pawn - see AutoWeaponTargeting.GetAttackSpeedFactor. CompTwinLink
    // (Artemis/Apollo's link performance), CompToxicWasteCore (the Plaguebringer Goliath's waste
    // stockpile) and CompPlaguePhase (its Phase 2 escalation) all implement this.
    public interface IAttackSpeedModifier
    {
        float AttackSpeedFactor { get; }
    }

    public static class AutoWeaponTargeting
    {
        // Multiplies together every IAttackSpeedModifier comp on the pawn (1.0 if there are
        // none), clamping each individually so a single comp can never fully stall a weapon.
        public static float GetAttackSpeedFactor(ThingWithComps parent)
        {
            float factor = 1f;
            List<ThingComp> comps = parent.AllComps;
            for (int i = 0; i < comps.Count; i++)
            {
                if (comps[i] is IAttackSpeedModifier mod)
                {
                    factor *= Mathf.Max(0.05f, mod.AttackSpeedFactor);
                }
            }
            return factor;
        }

        // Deliberately does NOT use AttackTargetFinder.BestShootTargetFromCurrentPosition:
        // that method sizes its search range off pawn.CurrentEffectiveVerb, and Ares has no
        // ranged Verb (only melee tools), so it silently clamped every search to melee range.
        // Scanning the raw hostile-target cache ourselves makes every weapon's range independent
        // of whatever verb/job the pawn's vanilla AI thinks it currently has.
        //
        // "exclude" is used by the multi-target toggle: targets already claimed by a sibling
        // weapon this tick are skipped on the first pass, but still used as a fallback so a
        // weapon never idles just because every visible enemy is already claimed.
        public static LocalTargetInfo FindTarget(Pawn pawn, float range, float minRange, HashSet<Thing> exclude)
        {
            List<IAttackTarget> potentialTargets = pawn.Map.attackTargetsCache.GetPotentialTargetsFor(pawn);

            Thing best = null;
            float bestDistSq = float.MaxValue;
            Thing fallback = null;
            float fallbackDistSq = float.MaxValue;

            for (int i = 0; i < potentialTargets.Count; i++)
            {
                IAttackTarget candidate = potentialTargets[i];
                Thing thing = candidate.Thing;
                if (thing == null || thing.Destroyed || !thing.Spawned || thing.Map != pawn.Map)
                {
                    continue;
                }

                if (candidate.ThreatDisabled(pawn))
                {
                    continue;
                }

                float dist = pawn.Position.DistanceTo(thing.Position);
                if (dist > range || dist < minRange)
                {
                    continue;
                }

                if (!GenSight.LineOfSight(pawn.Position, thing.Position, pawn.Map, skipFirstCell: true))
                {
                    continue;
                }

                float distSq = dist * dist;
                if (distSq < fallbackDistSq)
                {
                    fallbackDistSq = distSq;
                    fallback = thing;
                }

                if (exclude != null && exclude.Contains(thing))
                {
                    continue;
                }

                if (distSq < bestDistSq)
                {
                    bestDistSq = distSq;
                    best = thing;
                }
            }

            Thing result = best ?? fallback;
            return result != null ? new LocalTargetInfo(result) : LocalTargetInfo.Invalid;
        }

        public static HashSet<Thing> GatherClaimedTargets(Pawn pawn, IExoMechWeapon self)
        {
            HashSet<Thing> claimed = null;
            List<ThingComp> comps = pawn.AllComps;
            for (int i = 0; i < comps.Count; i++)
            {
                if (comps[i] is IExoMechWeapon weapon && !ReferenceEquals(weapon, self)
                    && weapon.CurrentTarget.IsValid && weapon.CurrentTarget.Thing != null)
                {
                    if (claimed == null)
                    {
                        claimed = new HashSet<Thing>();
                    }
                    claimed.Add(weapon.CurrentTarget.Thing);
                }
            }
            return claimed;
        }
    }
}
