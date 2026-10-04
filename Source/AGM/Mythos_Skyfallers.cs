using System;
using System.Collections.Generic;
using System.Linq;
using RimWorld;
using Verse;
using Verse.Sound;
using UnityEngine;

namespace AGM
{
    // Skyfaller_JumpingMech - verbatim port of GD3.SkyFaller_JumpingMech. Holds the pawn while it
    // "hangs" on the spot during the jump takeoff animation, drawing it at the skyfaller position.
    public class Skyfaller_JumpingMech : Skyfaller
    {
        public Pawn Pawn;

        protected override void DrawAt(Vector3 drawLoc, bool flip = false)
        {
            GetDrawPositionAndRotation(ref drawLoc, out var _);
            Pawn?.DrawNowAt(drawLoc, flip);
            DrawDropSpotShadow();
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
            Scribe_References.Look(ref Pawn, "Pawn");
        }
    }
}
