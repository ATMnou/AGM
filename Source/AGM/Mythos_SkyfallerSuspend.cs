using System;
using System.Collections.Generic;
using System.Linq;
using RimWorld;
using Verse;
using Verse.Sound;
using UnityEngine;

namespace AGM
{
    // Skyfaller_SuspendReady - verbatim port of GD3.Skyfaller_SuspendReady. The jump-and-suspend
    // carrier: eases the pawn up to half the flying height (kinematic deceleration, all original
    // constants), starts vanilla flight at AnimationChangeTick = 50, then spawns the pawn already
    // suspended with laserTick = 600 - the column laser opens the moment it touches "hover".
    public class Skyfaller_SuspendReady : Skyfaller
    {
        public static int AnimationChangeTick = 50;

        public Pawn Pawn => (Pawn)innerContainer[0];

        public Mythos_Pawn Mythos => Pawn as Mythos_Pawn;

        public float? zAccurate;

        public float? zTarget;

        public float speedNow;

        public float acceleration = 0;

        public int tickToAccelarate;

        public bool selected;

        public bool drafted;

        public override Vector3 DrawPos
        {
            get
            {
                Vector3 pos = base.DrawPos;
                pos.z = zAccurate.Value;
                return pos;
            }
        }

        public override void SpawnSetup(Map map, bool respawningAfterLoad)
        {
            base.SpawnSetup(map, respawningAfterLoad);
            speedNow = def.skyfaller.speed;
            zTarget = PositionHeld.ToVector3Shifted().z + 10f / 2f - 0.5f;
            zAccurate = zTarget.Value + 0.5f * speedNow * ticksToImpact;
            tickToAccelarate = ticksToImpact;
            acceleration = speedNow / tickToAccelarate;
            int extra = 120;
            ticksToImpact += extra;
            zAccurate += extra * speedNow;
            if (Pawn != null)
            {
                Pawn.Rotation = Rot4.East;
            }
        }

        protected override void Tick()
        {
            base.Tick();
            if (innerContainer.Any && Mythos != null)
            {
                if (zAccurate != null)
                {
                    if (ticksToImpact <= tickToAccelarate)
                    {
                        speedNow = Mathf.Clamp(speedNow, 0, speedNow - acceleration);
                    }
                    zAccurate -= speedNow;
                }
                if (ticksToImpact <= AnimationChangeTick)
                {
                    if (ticksToImpact == AnimationChangeTick)
                    {
                        AGMDefOf.Mythos_Transform.PlayOneShot(this);
                        Mythos.animation = AGMDefOf.Mythos_ReadySuspend;
                        if (Mythos.flight == null) Mythos.flight = new Pawn_FlightTracker(Mythos);
                        Mythos.flight.StartFlying();
                        Mythos.flight.FlightTick();
                        if (ticksToImpact == 1)
                        {
                            Mythos.animation = AGMDefOf.Mythos_Suspending;
                        }
                    }
                }
            }
        }

        protected override void DrawAt(Vector3 drawLoc, bool flip = false)
        {
            GetDrawPositionAndRotation(ref drawLoc, out var _);
            Pawn?.DrawNowAt(drawLoc, flip);
            DrawDropSpotShadow();
        }

        protected override void SpawnThings()
        {
            Pawn pawn = Pawn;
            if (pawn != null)
            {
                GenSpawn.Spawn(pawn, base.Position, base.Map);
                if (pawn is Mythos_Pawn mythos)
                {
                    mythos.animation = AGMDefOf.Mythos_Suspending;
                    mythos.laserTick = 600;
                    AGMDefOf.AGM_Mythos_ImpactDustCloud.Spawn(mythos, mythos, 1.2f).Cleanup();
                }
                if (selected)
                {
                    Find.Selector.Select(pawn, false);
                }
                if (drafted && pawn?.drafter != null)
                {
                    pawn.drafter.Drafted = true;
                }
            }
        }

        protected override void DrawDropSpotShadow()
        {
            Material shadowMaterial = base.ShadowMaterial;
            if (shadowMaterial != null)
            {
                Vector3 drawPos = DrawPos;
                drawPos.y = AltitudeLayer.Shadows.AltitudeFor();
                drawPos.z = base.Position.ToVector3Shifted().z;
                Skyfaller.DrawDropSpotShadow(drawPos, base.Rotation, shadowMaterial, def.skyfaller.shadowSize, ticksToImpact);
            }
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref zTarget, "zTarget");
            Scribe_Values.Look(ref zAccurate, "zAccurate");
            Scribe_Values.Look(ref speedNow, "speedNow");
            Scribe_Values.Look(ref acceleration, "acceleration");
            Scribe_Values.Look(ref tickToAccelarate, "tickToAccelarate");
            Scribe_Values.Look(ref selected, "selected");
            Scribe_Values.Look(ref drafted, "drafted");
        }
    }
}
