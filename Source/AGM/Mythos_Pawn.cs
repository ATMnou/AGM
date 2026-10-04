using System;
using System.Collections.Generic;
using System.Linq;
using RimWorld;
using RimWorld.Planet;
using UnityEngine;
using Verse;
using Verse.AI;
using Verse.Sound;

namespace AGM
{
    // Mythos's pawn class - a direct port of the Glitterworld Destroyer mod's GD3.Annihilator
    // (Cont/Source/GD3/Odyssey/Annihilator.cs, workshop 3550544871), renamed and stripped of
    // Annihilator-only boss machinery (quest signals, boss music interface, leg-targeting gizmo,
    // turret comps interplay). Every technique, tick count, damage formula, camera shake and
    // visual is kept 1:1; the mech itself renders with MFE's own 3-direction Mythos sprite.
    [StaticConstructorOnStartup]
    public class Mythos_Pawn : Pawn
    {
        public AnimationDef animation;

        public Vector3 drawPosOffset;

        public LocalTargetInfo jumpTarget;

        private bool willSuspend;

        public bool Damaged => health.summaryHealth.SummaryHealthPercent < 0.4f;

        // True when no technique is in progress. animation == null means "no scribed state"
        // (e.g. a pawn loaded from before the [DefOf] fix) - treat it as idle, not busy.
        public bool AnimationIdle => animation == null || animation == AGMDefOf.Mythos_Ambient;

        public int laserTick;

        public int laserTickPassed;

        // Ticks spent in the current animation phase. We count ourselves instead of reading
        // renderTree.AnimationTick because while Flying, vanilla's CheckFlyAnimation and our
        // animation tracking fight every tick (each calls SetAnimation), which resets
        // animationStartTick every tick and freezes AnimationTick at 0 - the suspend phase could
        // never complete (hover forever, laser never opened).
        public int animationPhaseTick;

        // Sets the current technique animation and restarts the phase counter.
        public void SetPhaseAnimation(AnimationDef def)
        {
            animation = def;
            animationPhaseTick = 0;
        }

        public bool longJump;

        public TargetInfo longJumpTarget;

        public bool NoAI;

        public bool stopAnimationTracking;

        private CompAffectsSky compAffectsSky;

        public CompAffectsSky CompAffectsSky => compAffectsSky == null ? compAffectsSky = this.TryGetComp<CompAffectsSky>() : compAffectsSky;

        public bool ShouldBeDead => health.summaryHealth.SummaryHealthPercent <= 0f;

        public bool Dying => dyingTick >= 0;

        public int dyingTick = -1;

        private Sustainer sustainer;

        private Effecter beamEffecter;

        private Material cachedShadowMaterial;

        protected Material ShadowMaterial
        {
            get
            {
                if (cachedShadowMaterial == null)
                {
                    cachedShadowMaterial = MaterialPool.MatFrom("Things/Skyfaller/SkyfallerShadowCircle", ShaderDatabase.Transparent);
                }

                return cachedShadowMaterial;
            }
        }

        public List<Ability> abilitiesList;

        private static List<AbilityDef> abilitiesFight = new List<AbilityDef>
        {
            AGMDefOf.AGM_MythosJump,
            AGMDefOf.AGM_MythosSuspend,
            AGMDefOf.AGM_MythosJumpAndSuspend,
        };

        public static float IfEnemyClose = 10.9f;

        private static readonly Material BeamMat = MaterialPool.MatFrom("Other/OrbitalBeam", ShaderDatabase.MoteGlow, MapMaterialRenderQueues.OrbitalBeam);

        private static readonly Material BeamEndMat = MaterialPool.MatFrom("Other/OrbitalBeamEnd", ShaderDatabase.MoteGlow, MapMaterialRenderQueues.OrbitalBeam);

        private static readonly MaterialPropertyBlock MatPropertyBlock = new MaterialPropertyBlock();

        private static readonly List<int> DyingExplosionTick = new List<int>
        {
            1, 60, 120, 180, 210, 240, 270, 300, 330, 360, 390, 420, 440, 460, 480, 500, 520, 540, 550, 560, 570, 580, 590
        };

        public override void SpawnSetup(Map map, bool respawningAfterLoad)
        {
            base.SpawnSetup(map, respawningAfterLoad);
            if (!respawningAfterLoad || animation == null)
            {
                animation = AGMDefOf.Mythos_Ambient;
            }
            abilitiesList = new List<Ability>();
            for (int i = 0; i < abilitiesFight.Count; i++)
            {
                AbilityDef def = abilitiesFight[i];
                abilitiesList.Add(abilities.GetAbility(def));
            }
            abilitiesList.RemoveAll(e => e == null);
            ResetAllAbilities(300);
        }

        protected override void Tick()
        {
            base.Tick();
            AnimationPostFix();
            Laser();

            if (Flying && this.IsHashIntervalTick(30))
            {
                DestroyRoofs();
            }

            DyingTick();
        }

        #region JumpTo/DoJump (in-map jump)
        public void JumpTo(LocalTargetInfo info, bool andSuspend = false)
        {
            AGMDefOf.Mythos_PreJump.PlayOneShot(this);
            SetPhaseAnimation(AGMDefOf.Mythos_Jump);
            jumpTarget = info;
            willSuspend = andSuspend;
            longJump = false;
            ResetAllAbilities(600);
        }

        public void DoJump(bool andSuspend = false)
        {
            SetPhaseAnimation(AGMDefOf.Mythos_Jumping);
            Map map = MapHeld;
            IntVec3 position = PositionHeld;
            AGMDefOf.Mythos_DoJump.PlayOneShot(new TargetInfo(position, map));
            AGMDefOf.AGM_Mythos_ImpactDustCloud.Spawn(this, this, 1.2f).Cleanup();
            Find.CameraDriver.shaker.DoShake(0.3f, 40);
            if (position.ShouldSpawnMotesAt(map))
            {
                FleckCreationData dataStatic = FleckMaker.GetDataStatic(DrawPos, map, AGMDefOf.AGM_Mythos_GroundCrack);
                dataStatic.scale = 10f;
                dataStatic.rotation = Rand.Range(0, 360);
                map.flecks.CreateFleck(dataStatic);
            }
            DestroyRoofs();

            bool selected = Find.Selector.IsSelected(this);
            bool drafted = Drafted;
            DeSpawn();
            Skyfaller_JumpingMech jumping = (Skyfaller_JumpingMech)SkyfallerMaker.MakeSkyfaller(AGMDefOf.AGM_Mythos_Skyfaller_JumpingMech);
            jumping.Pawn = this;
            GenSpawn.Spawn(jumping, position, map);

            IntVec3 targCell = jumpTarget.Cell;
            if (!jumpTarget.Cell.InBounds(map, 9) && CellFinder.TryFindRandomCellNear(jumpTarget.Cell, map, 9, c => c.InBounds(map, 9) && c.Standable(map), out IntVec3 result))
            {
                targCell = result;
            }
            if (!andSuspend)
            {
                Skyfaller_LandingMech landing = (Skyfaller_LandingMech)SkyfallerMaker.MakeSkyfaller(AGMDefOf.AGM_Mythos_Skyfaller_LandingMech, this);
                landing.selected = selected;
                landing.drafted = drafted;
                GenSpawn.Spawn(landing, targCell, map);
            }
            else
            {
                Skyfaller_SuspendReady landing = (Skyfaller_SuspendReady)SkyfallerMaker.MakeSkyfaller(AGMDefOf.AGM_Mythos_Skyfaller_SuspendReady, this);
                landing.selected = selected;
                landing.drafted = drafted;
                GenSpawn.Spawn(landing, targCell, map);
            }

            willSuspend = false;
        }
        #endregion

        #region ReadySuspend/DoSuspend (hover in place)
        public void ReadySuspend()
        {
            SetPhaseAnimation(AGMDefOf.Mythos_Jump_Light);
            longJump = false;
            AGMDefOf.Mythos_PreJump.PlayOneShot(this);
        }

        public void DoSuspend()
        {
            SetPhaseAnimation(AGMDefOf.Mythos_ReadySuspend_Light);
            AGMDefOf.Mythos_Transform.PlayOneShot(this);
            jobs.EndCurrentJob(JobCondition.InterruptForced);
            pather.StopDead();
            flight.StartFlying();
        }
        #endregion

        #region LongJump (out of map)
        public void LongJumpTo(TargetInfo info)
        {
            AGMDefOf.Mythos_PreJump.PlayOneShot(this);
            SetPhaseAnimation(AGMDefOf.Mythos_Jump);
            willSuspend = false;
            longJumpTarget = info;
            longJump = true;
            ResetAllAbilities(600);
        }

        public void DoLongJump()
        {
            SetPhaseAnimation(AGMDefOf.Mythos_Jumping);
            Map map = MapHeld;
            Map newMap = longJumpTarget.Map;
            IntVec3 position = PositionHeld;
            IntVec3 newPosition = longJumpTarget.Cell;
            AGMDefOf.Mythos_DoJump.PlayOneShot(new TargetInfo(position, map));
            AGMDefOf.AGM_Mythos_ImpactDustCloud.Spawn(this, this, 1.2f).Cleanup();
            Find.CameraDriver.shaker.DoShake(0.3f, 40);
            if (position.ShouldSpawnMotesAt(map))
            {
                FleckCreationData dataStatic = FleckMaker.GetDataStatic(DrawPos, map, AGMDefOf.AGM_Mythos_GroundCrack);
                dataStatic.scale = 10f;
                dataStatic.rotation = Rand.Range(0, 360);
                map.flecks.CreateFleck(dataStatic);
            }
            DestroyRoofs();

            bool selected = Find.Selector.IsSelected(this);
            bool drafted = Drafted;
            DeSpawn();
            Skyfaller_JumpingMech jumping = (Skyfaller_JumpingMech)SkyfallerMaker.MakeSkyfaller(AGMDefOf.AGM_Mythos_Skyfaller_JumpingMech);
            jumping.Pawn = this;
            GenSpawn.Spawn(jumping, position, map);

            IntVec3 targCell = newPosition;
            if (!newPosition.InBounds(newMap, 9) && CellFinder.TryFindRandomCellNear(newPosition, newMap, 9, c => c.InBounds(newMap, 9) && c.Standable(newMap), out IntVec3 result))
            {
                newPosition = result;
            }
            Skyfaller_LandingMech landing = (Skyfaller_LandingMech)SkyfallerMaker.MakeSkyfaller(AGMDefOf.AGM_Mythos_Skyfaller_LandingMech, this);
            landing.selected = selected;
            landing.drafted = drafted;
            GenSpawn.Spawn(landing, targCell, newMap);
            landing.ticksToImpact += Find.WorldGrid.TraversalDistanceBetween(newMap.Tile, map.Tile) * 10;
        }
        #endregion

        public void AnimationPostFix()
        {
            if (animation != null)
            {
                // Keep the technique animation applied (vanilla's fly-animation check may clear it
                // while airborne; we re-assert ours and count phase ticks independently - see
                // animationPhaseTick).
                if (Drawer.renderer.CurAnimation != animation && !stopAnimationTracking)
                {
                    Drawer.renderer.SetAnimation(animation);
                }
                animationPhaseTick++;
                if (animation == AGMDefOf.Mythos_Jump)
                {
                    if (animationPhaseTick >= animation.durationTicks - 1)
                    {
                        if (longJump) DoLongJump();
                        else DoJump(willSuspend);
                    }
                }
                else if (animation == AGMDefOf.Mythos_ResetPosture)
                {
                    if (animationPhaseTick >= animation.durationTicks - 1)
                    {
                        SetPhaseAnimation(AGMDefOf.Mythos_Ambient);
                        AGMDefOf.Mythos_DoJump.PlayOneShot(this);
                        AGMDefOf.AGM_Mythos_ImpactDustCloud.Spawn(this, this, 1.0f).Cleanup();
                        Find.CameraDriver.shaker.DoShake(0.1f, 30);
                        List<Thing> things = Map.listerThings.AllThings.Where(p => p.Position.IsInside(this) && p != this).ToList();
                        if (things.Any())
                        {
                            foreach (Thing victim in things)
                            {
                                float amount = (victim is Building && victim.def.useHitPoints) ? Math.Max(victim.MaxHitPoints * 0.75f, 1500) : 180;
                                victim.TakeDamage(new DamageInfo(DamageDefOf.Crush, amount, 30000f, -1, this));
                            }
                        }
                        ResetAllAbilities(200);
                    }
                }
                else if (animation == AGMDefOf.Mythos_Jump_Light)
                {
                    if (animationPhaseTick >= animation.durationTicks - 1)
                    {
                        DoSuspend();
                    }
                }
                else if (animation == AGMDefOf.Mythos_ReadySuspend_Light)
                {
                    if (animationPhaseTick >= animation.durationTicks - 1)
                    {
                        SetPhaseAnimation(AGMDefOf.Mythos_Suspending);
                        laserTick = 600;
                        AGMDefOf.AGM_Mythos_ImpactDustCloud.Spawn(this, this, 1.2f).Cleanup();
                    }
                }
                else if (animation == AGMDefOf.Mythos_Suspending)
                {
                    // Hover idles on Suspending until laserTick drains; nothing to advance here.
                }
            }
        }

        
        #region Laser (column beam)
        public void Laser()
        {
            if (!Spawned)
            {
                return;
            }
            if (laserTick > 0)
            {
                laserTick--;
                laserTickPassed++;
                if (laserTickPassed == 1)
                {
                    CompAffectsSky.StartFadeInHoldFadeOut(10, laserTick, 10);
                    Find.CameraDriver.shaker.DoShake(0.15f, 20);
                }
                if (sustainer == null)
                {
                    sustainer = AGMDefOf.Mythos_Laser.TrySpawnSustainer(SoundInfo.InMap(this, MaintenanceType.PerTick));
                }
                sustainer.Maintain();
                if (beamEffecter == null)
                {
                    beamEffecter = new Effecter(AGMDefOf.AGM_MythosLaserRing);
                    beamEffecter.offset = Vector3.zero;
                    beamEffecter.scale = 1.0f;
                    beamEffecter.Trigger(this, this);
                }
                beamEffecter.EffectTick(this, this);
                Find.CameraDriver.shaker.DoShake(0.05f, 2);
                if (this.IsHashIntervalTick(20))
                {
                    List<IntVec3> cells = GenRadial.RadialCellsAround(PositionHeld, 5.6f, true).Where(c => c.InBounds(MapHeld)).ToList();
                    if (cells.Any())
                    {
                        foreach (IntVec3 cell in cells)
                        {
                            if (Rand.Chance(0.2f))
                            {
                                FilthMaker.TryMakeFilth(cell, MapHeld, ThingDefOf.Filth_Ash);
                            }
                        }
                    }
                    List<Thing> targets = MapHeld?.listerThings.AllThings.Where(t => t.Position.IsInside(this) && t != this).ToList();
                    if (targets.Count > 0)
                    {
                        foreach (Thing target in targets)
                        {
                            if (!target.def.destroyable)
                            {
                                continue;
                            }
                            float amount = (target is Building && target.def.useHitPoints) ? Math.Max(target.MaxHitPoints / 10f, 250) : 150;
                            target.TakeDamage(new DamageInfo(AGMDefOf.AGM_Damage_MythosBeam, amount, 1.5f, -1, this));
                        }
                    }
                }
                if (laserTick == 0)
                {
                    laserTickPassed = 0;
                    ForceLand();
                }
                FleckCreationData dataStatic = FleckMaker.GetDataStatic(DrawPos - new Vector3(0, 0, flight.PositionOffsetFactor / 2f), Map, AGMDefOf.AGM_Mythos_BeamSpark, Rand.Range(3.5f, 4.5f));
                dataStatic.rotationRate = Rand.Range(-30f, 30f);
                dataStatic.velocityAngle = Rand.Range(0, 360);
                dataStatic.velocitySpeed = Rand.Range(3.5f, 4.7f);
                Map.flecks.CreateFleck(dataStatic);
            }
            else
            {
                sustainer?.End();
                sustainer = null;
                beamEffecter = null;
            }
        }
        #endregion

        #region Death
        public void DyingTick()
        {
            if (dyingTick == -1 && ShouldBeDead)
            {
                if (Flying && animation != AGMDefOf.Mythos_ResetPosture)
                {
                    laserTick = 0;
                    laserTickPassed = 0;
                    ForceLand();
                }
                if (animation == null || animation == AGMDefOf.Mythos_Ambient)
                {
                    dyingTick++;
                    SetPhaseAnimation(AGMDefOf.Mythos_Dying);
                    Find.CameraDriver.shaker.DoShake(1.55f, 30);
                    DefDatabase<SoundDef>.GetNamed("Pawn_Mech_Diabolus_Death").PlayOneShot(this);
                }
            }
            else if (dyingTick >= 0)
            {
                dyingTick++;
                if (DyingExplosionTick.Contains(dyingTick))
                {
                    IntVec3 cell = MapHeld.AllCells.Where(c => c.IsInside(this)).RandomElement();
                    GenExplosion.DoExplosion(cell, MapHeld, 3.9f, DamageDefOf.Bomb, null, 40, 0.8f, null, null, null, null, null, 0f, 1, null, null, 255, false, null, 0f, 1, 0f, false, null, new List<Thing> { this }, null, true, 1f, 0f, true, null, 1f);
                    FleckMaker.ThrowFireGlow(cell.ToVector3Shifted(), MapHeld, 1.5f);
                    for (int i = 0; i < 5; i++)
                    {
                        FleckMaker.ThrowSmoke(cell.ToVector3Shifted(), MapHeld, 2.0f);
                    }
                }
                if (dyingTick == 400)
                {
                    AGMDefOf.Mythos_Transform.PlayOneShot(this);
                }
                if (dyingTick >= 599)
                {
                    IntVec3 vec = PositionHeld;
                    Map map = MapHeld;

                    Thing.allowDestroyNonDestroyable = true;
                    Kill(null);
                    Thing.allowDestroyNonDestroyable = false;

                    GenExplosion.DoExplosion(vec, map, 14.9f, DamageDefOf.Flame, null, 120, 0.8f, null, null, null, null, ThingDefOf.Filth_Fuel, 0.4f, 1, null, null, 255, false, null, 0f, 1, 0.5f, false, null, null, null, true, 1f, 0f, true, null, 1f);
                    AGMDefOf.GiantExplosion.Spawn(vec, map, 1.5f);
                    Find.CameraDriver.shaker.DoShake(6f, 90);
                }
            }
        }
        #endregion

        public void ForceLand()
        {
            if (Flying)
            {
                SetPhaseAnimation(AGMDefOf.Mythos_ResetPosture);
                AGMDefOf.Mythos_Transform.PlayOneShot(this);
                jobs.EndCurrentJob(JobCondition.InterruptForced);
                pather.StopDead();
                flight.ForceLand();
            }
        }

        protected override void DrawAt(Vector3 drawLoc, bool flip = false)
        {
            base.DrawAt(drawLoc, flip);
            if (Spawned && Map != null)
            {
                // Shadow
                Material shadowMaterial = ShadowMaterial;
                if (shadowMaterial != null)
                {
                    drawLoc.y = AltitudeLayer.Shadows.AltitudeFor();
                    if (Flying)
                    {
                        drawLoc.z -= flight.PositionOffsetFactor / 2f;
                    }
                    Skyfaller.DrawDropSpotShadow(drawLoc, base.Rotation, shadowMaterial, new Vector2(16, 16), 0);
                }
                // Laser
                if (laserTick > 0)
                {
                    drawLoc.x -= 0.1f;
                    Vector3 drawPos = drawLoc - new Vector3(0, 0, flight.PositionOffsetFactor / 3f);
                    float num = (drawLoc.z + flight.PositionOffsetFactor / 2f - drawPos.z) * 1f;
                    float angle = 0;
                    Vector3 vector = Vector3Utility.FromAngleFlat(angle - 90f);
                    Vector3 vector2 = drawPos + vector * num * 0.5f;
                    vector2.y = AltitudeLayer.Projectile.AltitudeFor();
                    float alpha = Mathf.Min((float)laserTickPassed / 10f, 1f);
                    float num2 = 1f;
                    Vector3 vector3 = vector * ((1f - num2) * num);
                    float num3 = 0.975f + Mathf.Sin((float)laserTickPassed * 0.3f) * 0.025f;
                    if (laserTick < 10)
                    {
                        num3 *= (float)laserTick / 10f;
                    }
                    Color color = new Color(1f, 0.96f, 0.84f, 0.95f * alpha);
                    color.a *= num3;
                    MatPropertyBlock.SetColor(ShaderPropertyIDs.Color, color);
                    Matrix4x4 matrix = default(Matrix4x4);
                    float width = 10f;
                    float beamEndHeight = width * 0.5f;
                    matrix.SetTRS(vector2 + vector * beamEndHeight * 0.5f + vector3, Quaternion.Euler(0f, angle, 0f), new Vector3(width, 1f, num));
                    Graphics.DrawMesh(MeshPool.plane10, matrix, BeamMat, 0, null, 0, MatPropertyBlock);
                    Vector3 pos = drawPos + vector3;
                    pos.y = AltitudeLayer.Projectile.AltitudeFor();
                    Matrix4x4 matrix2 = default(Matrix4x4);
                    matrix2.SetTRS(pos, Quaternion.Euler(0f, angle, 0f), new Vector3(width, 1f, beamEndHeight));
                    Graphics.DrawMesh(MeshPool.plane10, matrix2, BeamEndMat, 0, null, 0, MatPropertyBlock);
                }
            }
        }

        public override void Destroy(DestroyMode mode = DestroyMode.Vanish)
        {
            base.Destroy(mode);
        }

        public void ResetAllAbilities(int tick)
        {
            foreach (Ability a in abilities.AllAbilitiesForReading)
            {
                if (a.CooldownTicksRemaining > tick)
                {
                    continue;
                }
                a.StartCooldown(tick);
            }
        }

        public void DestroyRoofs()
        {
            List<IntVec3> cells = MapHeld?.AllCells.Where(c => c.IsInside(this)).ToList();
            if (!cells.NullOrEmpty())
            {
                foreach (IntVec3 cell in cells)
                {
                    if (cell.Roofed(MapHeld))
                    {
                        MapHeld.roofGrid.SetRoof(cell, null);
                        FleckMaker.ThrowDustPuff(cell.ToVector3Shifted() + Gen.RandomHorizontalVector(0.6f), MapHeld, 2f);
                    }
                }
                Find.CameraDriver.shaker.DoShake(0.1f, 20);
                SoundDefOf.Roof_Collapse.PlayOneShot(this);
            }
        }

        public override void PreApplyDamage(ref DamageInfo dinfo, out bool absorbed)
        {
            base.PreApplyDamage(ref dinfo, out absorbed);
            if (Flying && !dinfo.Def.isRanged && !dinfo.Def.isExplosive && dinfo.Def != DamageDefOf.EMP)
            {
                Pawn pawn = dinfo.Instigator as Pawn;
                if (pawn != null && pawn.Flying)
                {
                    return;
                }
                absorbed = true;
            }
            if (dinfo.Def == DamageDefOf.Crush)
            {
                absorbed = true;
                return;
            }
            if (Flying)
            {
                dinfo.SetAmount(dinfo.Amount * 0.4f);
            }
        }

        public override void PostApplyDamage(DamageInfo dinfo, float totalDamageDealt)
        {
            base.PostApplyDamage(dinfo, totalDamageDealt);
            Drawer.renderer.SetAllGraphicsDirty();
            if (mindState.enemyTarget == null)
            {
                mindState.enemyTarget = dinfo.Instigator;
            }
        }

        public override IEnumerable<Gizmo> GetGizmos()
        {
            foreach (Gizmo gizmo in base.GetGizmos())
            {
                if (!(gizmo is Command_Target command) || command.defaultLabel != "CommandMeleeAttack".Translate())
                {
                    yield return gizmo;
                }
            }
            if (DebugSettings.ShowDevGizmos)
            {
                Command_Toggle command_Toggle = new Command_Toggle
                {
                    defaultLabel = "DEV: No AI",
                    toggleAction = delegate ()
                    {
                        NoAI = !NoAI;
                    },
                    isActive = (() => NoAI)
                };
                Command_Toggle command_Toggle2 = new Command_Toggle
                {
                    defaultLabel = "DEV: Stop Animation Tracking",
                    toggleAction = delegate ()
                    {
                        stopAnimationTracking = !stopAnimationTracking;
                    },
                    isActive = (() => stopAnimationTracking)
                };
                Command_Action command_Action = new Command_Action
                {
                    defaultLabel = "DEV: Instant Kill",
                    action = delegate
                    {
                        Kill(null);
                    }
                };
                yield return command_Toggle;
                yield return command_Toggle2;
                yield return command_Action;
            }
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref drawPosOffset, "drawPosOffset");
            Scribe_Values.Look(ref willSuspend, "willSuspend");
            Scribe_Values.Look(ref laserTick, "laserTick");
            Scribe_Values.Look(ref laserTickPassed, "laserTickPassed");
            Scribe_Values.Look(ref longJump, "longJump");
            Scribe_Values.Look(ref NoAI, "NoAI");
            Scribe_Values.Look(ref dyingTick, "dyingTick", -1);
            Scribe_Values.Look(ref stopAnimationTracking, "stopAnimationTracking");
            Scribe_Defs.Look(ref animation, "animation");
            Scribe_TargetInfo.Look(ref jumpTarget, "jumpTarget");
            Scribe_TargetInfo.Look(ref longJumpTarget, "longJumpTarget");
        }
    }
}
