using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.Sound;

namespace AGM
{
    // A self-contained, always-on weapon system: independent targeting, independent
    // cooldown, independent burst. Multiple instances can be stacked on one pawn
    // (unlike CompProperties_TurretGun, which vanilla never stacks and which silently
    // fails to fire any weapon when stacked more than once on the same pawn).
    //
    // Infernum rework additions (all default to vanilla-off so legacy users are unaffected):
    // - fanShotCount/fanSpreadRadians/fanRandom: each shot trigger releases a fan of projectiles
    //   (Ares laser 5-wide fans every 3rd shot, plasma double fireballs, Artemis gatling triples).
    // - fanEveryNthShot: only every Nth trigger becomes a fan (Ares laser's every-3rd-shot fan).
    // - jitterRadians: random per-projectile angular jitter (Ares plasma's ±0.34 rad).
    // - aimLeadTicks: aims at the target's predicted position (Infernum arm aim predictiveness).
    // - minPhase / phaseBonusShotCount: Infernum phase gating and strengthening - a weapon idles
    //   until ExoPhaseUtility.CurrentPhase >= minPhase and fans grow by +N per phase beyond 1.
    // - soundWarmup: charge telegraph sound played when the warmup starts (Ares arm charges).
    public class CompProperties_AutoWeapon : CompProperties
    {
        public ThingDef projectileDef;
        public float range = 40f;
        public float minRange = 0f;
        public int burstShotCount = 1;
        public int ticksBetweenBurstShots = 10;
        public int cooldownTicks = 120;
        public int warmupTicks = 15;
        public SoundDef soundCast;
        public float fleckScale = 6f;

        // Infernum volley shaping.
        public int fanShotCount = 1;
        public float fanSpreadRadians = 0f;
        public bool fanRandom = false;
        public int fanEveryNthShot = 0;
        public float jitterRadians = 0f;
        public int aimLeadTicks = 0;
        public int minPhase = 1;
        public int phaseBonusShotCount = 0;
        public SoundDef soundWarmup;

        // When true, adds a Command_Toggle gizmo letting the player turn this weapon off/on
        // (Flamewall's mortar - the player may want it silent/inactive without disabling the
        // whole pawn). Off by default so every other auto-weapon user (Arbiter's sidearm, Ares,
        // etc.) is unaffected.
        public bool userToggleable = false;

        // Only meaningful when userToggleable is true: whether the weapon starts enabled on a
        // freshly-spawned pawn (Ares's Doomsday Rocket wants false - a warhead this devastating
        // firing automatically every 5 seconds should be an explicit opt-in).
        public bool defaultEnabled = true;

        // Translation keys for the toggle gizmo. Default to a generic "Toggle weapon" wording so
        // existing single-toggle pawns need no XML change, but a pawn with multiple weapons (Ares
        // has six) should override these so the player can tell which toggle is which.
        public string toggleLabelKey = "AGM.AutoWeaponToggleLabel";
        public string toggleDescKey = "AGM.AutoWeaponToggleDesc";

        public CompProperties_AutoWeapon()
        {
            compClass = typeof(CompAutoWeapon);
        }
    }

    public class CompAutoWeapon : ThingComp, IExoMechWeapon
    {
        private int cooldownTicksRemaining;
        private int warmupTicksRemaining;
        private int burstShotsRemaining;
        private int ticksToNextBurstShot;
        private int shotCounter;
        private int lastFireTick = -999999;
        private LocalTargetInfo currentTarget = LocalTargetInfo.Invalid;
        private bool weaponEnabled = true;

        public CompProperties_AutoWeapon Props => (CompProperties_AutoWeapon)props;

        public LocalTargetInfo CurrentTarget => currentTarget;

        // 0..1 pose driver for the Ares multi-joint arm renderer: ramps up during warmup, holds
        // while the burst is firing, then decays after the last shot.
        public float PoseBlend
        {
            get
            {
                if (warmupTicksRemaining > 0 && Props.warmupTicks > 0)
                {
                    return Mathf.Clamp01(1f - (float)warmupTicksRemaining / Props.warmupTicks);
                }

                if (burstShotsRemaining > 0)
                {
                    return 1f;
                }

                int sinceFire = Find.TickManager.TicksGame - lastFireTick;
                return Mathf.Clamp01(1f - sinceFire / 45f);
            }
        }

        public override void Initialize(CompProperties props)
        {
            base.Initialize(props);
            weaponEnabled = Props.defaultEnabled;
        }

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref weaponEnabled, "autoWeaponEnabled", Props.defaultEnabled);
            Scribe_Values.Look(ref shotCounter, "autoWeaponShotCounter", 0);
        }

        public override IEnumerable<Gizmo> CompGetGizmosExtra()
        {
            foreach (Gizmo gizmo in base.CompGetGizmosExtra())
            {
                yield return gizmo;
            }

            if (!Props.userToggleable)
            {
                yield break;
            }

            yield return new Command_Toggle
            {
                defaultLabel = Props.toggleLabelKey.Translate(),
                defaultDesc = Props.toggleDescKey.Translate(),
                icon = TexCommand.Attack,
                isActive = () => weaponEnabled,
                toggleAction = () => weaponEnabled = !weaponEnabled,
            };
        }

        // Scaled by every IAttackSpeedModifier comp on this pawn - twin-link performance
        // (Artemis/Apollo), toxic waste stockpile, phase escalation, etc. Pawns with none of
        // those comps (e.g. Ares) are unaffected.
        private int ScaledCooldown()
        {
            return Mathf.RoundToInt(Props.cooldownTicks / AutoWeaponTargeting.GetAttackSpeedFactor(parent));
        }

        private bool PhaseAllows()
        {
            return ExoPhaseUtility.CurrentPhase(parent) >= Props.minPhase;
        }

        private int FanShotCount()
        {
            return Mathf.Max(1, Props.fanShotCount + Props.phaseBonusShotCount * Mathf.Max(0, ExoPhaseUtility.CurrentPhase(parent) - 1));
        }

        public override void CompTick()
        {
            base.CompTick();

            Pawn pawn = parent as Pawn;
            if (pawn == null || !pawn.Spawned || pawn.Dead || pawn.Downed)
            {
                return;
            }

            if (Props.userToggleable && !weaponEnabled)
            {
                return;
            }

            if (!PhaseAllows())
            {
                return;
            }

            if (cooldownTicksRemaining > 0)
            {
                cooldownTicksRemaining--;
                return;
            }

            if (warmupTicksRemaining > 0)
            {
                warmupTicksRemaining--;
                if (warmupTicksRemaining <= 0)
                {
                    FireShot(pawn);
                }
                return;
            }

            if (burstShotsRemaining > 0)
            {
                if (ticksToNextBurstShot > 0)
                {
                    ticksToNextBurstShot--;
                    return;
                }

                if (!TargetStillValid(pawn))
                {
                    burstShotsRemaining = 0;
                    cooldownTicksRemaining = ScaledCooldown();
                    return;
                }

                FireShot(pawn);
                burstShotsRemaining--;
                if (burstShotsRemaining > 0)
                {
                    ticksToNextBurstShot = Props.ticksBetweenBurstShots;
                }
                else
                {
                    cooldownTicksRemaining = ScaledCooldown();
                }
                return;
            }

            CompTargetingModeToggle toggle = parent.GetComp<CompTargetingModeToggle>();
            HashSet<Thing> exclude = (toggle != null && toggle.multiTargetMode)
                ? AutoWeaponTargeting.GatherClaimedTargets(pawn, this)
                : null;

            LocalTargetInfo target = AutoWeaponTargeting.FindTarget(pawn, Props.range, Props.minRange, exclude);
            if (!target.IsValid)
            {
                return;
            }

            currentTarget = target;
            if (Props.warmupTicks > 0)
            {
                warmupTicksRemaining = Props.warmupTicks;
                if (Props.soundWarmup != null)
                {
                    SoundStarter.PlayOneShot(Props.soundWarmup, pawn);
                }
            }
            else
            {
                FireShot(pawn);
            }
        }

        // One shot trigger: releases FanShotCount() projectiles in a fan (or with jitter), then
        // schedules the rest of the burst.
        private void FireShot(Pawn pawn)
        {
            if (!TargetStillValid(pawn))
            {
                cooldownTicksRemaining = ScaledCooldown();
                return;
            }

            LaunchFan(pawn);
            shotCounter++;

            burstShotsRemaining = Mathf.Max(0, Props.burstShotCount - 1);
            if (burstShotsRemaining > 0)
            {
                ticksToNextBurstShot = Props.ticksBetweenBurstShots;
            }
            else
            {
                cooldownTicksRemaining = ScaledCooldown();
            }
        }

        private bool TargetStillValid(Pawn pawn)
        {
            if (!currentTarget.IsValid || currentTarget.Thing == null || currentTarget.Thing.Destroyed || !currentTarget.Thing.Spawned)
            {
                return false;
            }

            if (currentTarget.Thing.Map != pawn.Map)
            {
                return false;
            }

            float dist = pawn.Position.DistanceTo(currentTarget.Cell);
            if (dist > Props.range || dist < Props.minRange)
            {
                return false;
            }

            if (!GenSight.LineOfSight(pawn.Position, currentTarget.Cell, pawn.Map, skipFirstCell: true))
            {
                return false;
            }

            return true;
        }

        // Aims at the target's predicted position like Infernum's arm aim predictiveness: the
        // target's current cell plus its estimated movement over aimLeadTicks.
        private IntVec3 AimCell(Pawn pawn)
        {
            IntVec3 cell = currentTarget.Cell;
            if (Props.aimLeadTicks <= 0 || !(currentTarget.Thing is Pawn moving) || moving.pather == null || !moving.pather.Moving)
            {
                return cell;
            }

            IntVec3 dir = moving.pather.nextCell - moving.Position;
            if (dir == IntVec3.Zero)
            {
                return cell;
            }

            float tilesPerTick = moving.GetStatValue(StatDefOf.MoveSpeed) / 60f;
            Vector3 lead = dir.ToVector3().normalized * (tilesPerTick * Props.aimLeadTicks);
            IntVec3 predicted = (cell.ToVector3Shifted() + lead).ToIntVec3();
            return predicted.InBounds(pawn.Map) ? predicted : cell;
        }

        private void LaunchFan(Pawn pawn)
        {
            if (Props.projectileDef == null)
            {
                return;
            }

            lastFireTick = Find.TickManager.TicksGame;

            bool fanThisShot = Props.fanEveryNthShot <= 0 || shotCounter % Props.fanEveryNthShot == Props.fanEveryNthShot - 1;
            int shots = fanThisShot ? FanShotCount() : 1;
            IntVec3 aimCell = AimCell(pawn);
            Vector3 origin = pawn.DrawPos;

            for (int i = 0; i < shots; i++)
            {
                float angleOffset = 0f;
                if (fanThisShot && shots > 1)
                {
                if (Props.fanRandom)
                {
                    angleOffset = Rand.Range(-Props.fanSpreadRadians, Props.fanSpreadRadians);
                }
                else
                {
                    angleOffset = Mathf.Lerp(-Props.fanSpreadRadians, Props.fanSpreadRadians, (float)i / (shots - 1));
                }
                }

                angleOffset += Rand.Range(-Props.jitterRadians, Props.jitterRadians);
                LaunchOne(pawn, origin, aimCell, angleOffset, i == 0);
            }

            if (Props.soundCast != null)
            {
                SoundStarter.PlayOneShot(Props.soundCast, pawn);
            }

            FleckMaker.Static(pawn.DrawPos, pawn.Map, FleckDefOf.ShotFlash, Props.fleckScale);
        }

        // Rotates the aim offset around the shooter by angleOffset radians, keeping the same
        // flight distance, so fans spread while range stays intact.
        private void LaunchOne(Pawn pawn, Vector3 origin, IntVec3 aimCell, float angleOffset, bool first)
        {
            Map map = pawn.Map;
            Vector3 offset = aimCell.ToVector3Shifted() - origin;
            Vector3 rotatedOffset = Quaternion.AngleAxis(angleOffset * Mathf.Rad2Deg, Vector3.up) * offset;
            IntVec3 dest = (origin + rotatedOffset).ToIntVec3();
            if (!dest.InBounds(map))
            {
                dest = aimCell;
            }

            Projectile projectile = (Projectile)GenSpawn.Spawn(Props.projectileDef, pawn.Position, map, WipeMode.Vanish);
            projectile.Launch(pawn, origin, new LocalTargetInfo(dest), currentTarget, ProjectileHitFlags.All, false, null);
        }
    }
}
