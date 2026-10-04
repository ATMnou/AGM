using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.Sound;

namespace AGM
{
    public class CompProperties_KatanaSlash : CompProperties
    {
        public int cooldownTicks = 1100;
        public int warmupTicks = 60;
        public SoundDef warmupSound;
        public SoundDef slashSound;

        // Target search radius for the automatic trigger.
        public float searchRange = 30f;

        // Fan of accelerating energy slash waves hurled at the target (AresEnergySlash
        // projectiles). Fired from the current position - no repositioning.
        public ThingDef slashProjectileDef;
        public int slashCount = 3;
        public float slashSpreadRadians = 0.35f;
        public float slashRangeTiles = 14f;
        public int slashPhaseBonusCount = 1;

        // Follow-up radial deathray burst from the current position (Infernum's
        // DownwardCrossSlices telegraphed beam nova). Fires novaWarmupTicks after the waves.
        public ThingDef novaProjectileDef;
        public int novaCount = 10;
        public float novaRangeTiles = 12f;
        public int novaWarmupTicks = 30;
        public int novaPhaseBonusCount = 2;

        public CompProperties_KatanaSlash()
        {
            compClass = typeof(CompKatanaSlash);
        }
    }

    // Ares's Photon Ripper katanas, ported as a periodic automatic super: telegraph, hurl a fan
    // of accelerating energy slash waves at the target, then detonate a radial deathray nova -
    // the strongest port-friendly slice pattern from Infernum's katana attacks. Stationary by
    // design (no teleport/dash).
    public class CompKatanaSlash : ThingComp
    {
        private const byte StateIdle = 0;
        private const byte StateWarmup = 1;
        private const byte StateNovaDelay = 2;

        private byte state = StateIdle;
        private int stateTicksRemaining;
        private int cooldownTicksRemaining;
        private LocalTargetInfo currentTarget = LocalTargetInfo.Invalid;

        public CompProperties_KatanaSlash Props => (CompProperties_KatanaSlash)props;

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref state, "katanaState", StateIdle);
            Scribe_Values.Look(ref stateTicksRemaining, "katanaStateTicks", 0);
            Scribe_Values.Look(ref cooldownTicksRemaining, "katanaCooldown", 0);
        }

        public override void CompTick()
        {
            base.CompTick();

            Pawn pawn = parent as Pawn;
            if (pawn == null || !pawn.Spawned || pawn.Dead || pawn.Downed)
            {
                state = StateIdle;
                return;
            }

            if (cooldownTicksRemaining > 0)
            {
                cooldownTicksRemaining--;
                return;
            }

            switch (state)
            {
                case StateIdle:
                    TickIdle(pawn);
                    break;
                case StateWarmup:
                    TickWarmup(pawn);
                    break;
                case StateNovaDelay:
                    TickNovaDelay(pawn);
                    break;
            }
        }

        private void TickIdle(Pawn pawn)
        {
            currentTarget = AutoWeaponTargeting.FindTarget(pawn, Props.searchRange, 0f, null);
            if (!currentTarget.IsValid)
            {
                return;
            }

            state = StateWarmup;
            stateTicksRemaining = Props.warmupTicks;
            if (Props.warmupSound != null)
            {
                SoundStarter.PlayOneShot(Props.warmupSound, pawn);
            }
            FleckMaker.Static(pawn.DrawPos, pawn.Map, FleckDefOf.PsycastAreaEffect, 4f);
        }

        private void TickWarmup(Pawn pawn)
        {
            if (--stateTicksRemaining > 0)
            {
                return;
            }

            if (!currentTarget.IsValid || !TargetAlive())
            {
                Reset(StateIdle, Props.cooldownTicks);
                return;
            }

            FireSlashes(pawn);
            state = StateNovaDelay;
            stateTicksRemaining = Props.novaWarmupTicks;
        }

        private void TickNovaDelay(Pawn pawn)
        {
            if (--stateTicksRemaining > 0)
            {
                return;
            }

            if (Props.novaProjectileDef != null)
            {
                FireNova(pawn);
            }
            Reset(StateIdle, Props.cooldownTicks);
        }

        private bool TargetAlive()
        {
            return currentTarget.Thing != null && !currentTarget.Thing.Destroyed && currentTarget.Thing.Spawned;
        }

        private void Reset(byte newState, int cooldown)
        {
            state = newState;
            stateTicksRemaining = 0;
            cooldownTicksRemaining = Mathf.RoundToInt(cooldown / AutoWeaponTargeting.GetAttackSpeedFactor(parent));
        }

        private void FireSlashes(Pawn pawn)
        {
            if (Props.slashProjectileDef == null)
            {
                return;
            }

            // Fan of accelerating energy slash waves toward (roughly) the target.
            int slashCount = Mathf.Max(1, Props.slashCount + Props.slashPhaseBonusCount * Mathf.Max(0, ExoPhaseUtility.CurrentPhase(pawn) - 1));
            Vector3 origin = pawn.DrawPos;
            Vector3 aim = (TargetAlive() ? currentTarget.Thing.DrawPos : origin + Vector3.forward) - origin;
            // AngleAxis(+deg, up) rotates +x toward -z, hence the flipped z term.
            float baseAngle = Mathf.Atan2(-aim.z, aim.x) * Mathf.Rad2Deg;
            for (int i = 0; i < slashCount; i++)
            {
                float angle = baseAngle + Mathf.Lerp(-Props.slashSpreadRadians, Props.slashSpreadRadians,
                    slashCount > 1 ? (float)i / (slashCount - 1) : 0.5f) * Mathf.Rad2Deg;
                FireDirectional(pawn, origin, angle, Props.slashRangeTiles, Props.slashProjectileDef);
            }

            if (Props.slashSound != null)
            {
                SoundStarter.PlayOneShot(Props.slashSound, pawn);
            }
        }

        private void FireNova(Pawn pawn)
        {
            int count = Mathf.Max(1, Props.novaCount + Props.novaPhaseBonusCount * Mathf.Max(0, ExoPhaseUtility.CurrentPhase(pawn) - 1));
            float step = 360f / count;
            float offset = Rand.Range(0f, step);
            for (int i = 0; i < count; i++)
            {
                FireDirectional(pawn, pawn.DrawPos, offset + i * step, Props.novaRangeTiles, Props.novaProjectileDef);
            }

            FleckMaker.Static(pawn.DrawPos, pawn.Map, FleckDefOf.PsycastAreaEffect, 8f);
            if (Props.slashSound != null)
            {
                SoundStarter.PlayOneShot(Props.slashSound, pawn);
            }
        }

        private void FireDirectional(Pawn pawn, Vector3 origin, float angleDegrees, float rangeTiles, ThingDef projectileDef)
        {
            Map map = pawn.Map;
            Vector3 dir = Quaternion.AngleAxis(angleDegrees, Vector3.up) * Vector3.right;
            IntVec3 dest = (origin + dir * rangeTiles).ToIntVec3();
            if (!dest.InBounds(map))
            {
                return;
            }

            Projectile projectile = (Projectile)GenSpawn.Spawn(projectileDef, pawn.Position, map, WipeMode.Vanish);
            projectile.Launch(pawn, origin, new LocalTargetInfo(dest), new LocalTargetInfo(dest), ProjectileHitFlags.All, false, null);
        }
    }
}
