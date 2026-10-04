using RimWorld;
using Verse;

namespace AGM
{
    // DefOf lookup class for the Mythos port - mirrors GD3's GDDefOf but only for the defs
    // this mod actually ships (all defs live under the AGM_ / Mythos_ defName prefixes).
    [DefOf]
    public static class AGMDefOf
    {
        // Abilities
        public static AbilityDef AGM_MythosJump;
        public static AbilityDef AGM_MythosSuspend;
        public static AbilityDef AGM_MythosJumpAndSuspend;

        // Animations (GD3 Odyssey Annihilator set, copied def-for-def)
        public static AnimationDef Mythos_Ambient;
        public static AnimationDef Mythos_Jump;
        public static AnimationDef Mythos_Jumping;
        public static AnimationDef Mythos_ReadySuspend;
        public static AnimationDef Mythos_Suspending;
        public static AnimationDef Mythos_ResetPosture;
        public static AnimationDef Mythos_Jump_Light;
        public static AnimationDef Mythos_ReadySuspend_Light;
        public static AnimationDef Mythos_Dying;

        // Damage
        public static DamageDef AGM_Damage_MythosBeam;

        // Vanilla Core effecter used by the death sequence
        public static EffecterDef GiantExplosion;

        // Effects
        public static EffecterDef AGM_Mythos_ImpactDustCloud;
        public static EffecterDef AGM_MythosLaserRing;
        public static FleckDef AGM_Mythos_GroundCrack;
        public static FleckDef AGM_Mythos_BeamSpark;

        // Sounds
        public static SoundDef Mythos_DoJump;
        public static SoundDef Mythos_PreJump;
        public static SoundDef Mythos_Laser;
        public static SoundDef Mythos_Transform;

        // Skyfallers (jump/land/suspend carriers)
        public static ThingDef AGM_Mythos_Skyfaller_JumpingMech;
        public static ThingDef AGM_Mythos_Skyfaller_LandingMech;
        public static ThingDef AGM_Mythos_Skyfaller_SuspendReady;
    }
}
