using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace AGM
{
    // Extra projectile behaviors configured straight in XML via the <projectile Class=...> block.
    // Deliberately does NOT touch the vanilla flight path - everything here happens at impact
    // time, so the projectile flies exactly like any vanilla bullet while gaining Infernum-style
    // on-death effects.
    public class ProjectileProperties_Exo : ProjectileProperties
    {
        // On impact, spawns splitChildCount projectiles of splitChildDef in an even ring around
        // the impact cell (Ares plasma bolts, tesla orb sparks, Plague Vomit seeker bursts).
        // splitPlusPattern swaps the ring for a 4-point plus shape like AresTeslaOrb's sparks.
        public ThingDef splitChildDef;
        public int splitChildCount;
        public bool splitPlusPattern;
        public float splitChildRange = 8f;

        // On impact, spawns one lingering area-denial field (ExoMech.DamageZone_Exo), e.g. the
        // Ares plasma cannon's green gas variant or the Plaguebringer's dash trail clouds.
        public ThingDef gasZoneDef;
        public float gasZoneChance = 1f;

        public bool HasSplit => splitChildDef != null && splitChildCount > 0;
    }

    public class Projectile_Exo : Projectile_Explosive
    {
        public ProjectileProperties_Exo ExoProps => def.projectile as ProjectileProperties_Exo;

        protected override void Impact(Thing hitThing, bool blockedByShieldOfSelf = false)
        {
            base.Impact(hitThing, blockedByShieldOfSelf);

            ProjectileProperties_Exo props = ExoProps;
            if (props == null || !Spawned || Map == null)
            {
                return;
            }

            if (props.HasSplit)
            {
                LaunchSplitChildren(props);
            }

            if (props.gasZoneDef != null && Rand.Chance(props.gasZoneChance))
            {
                GenSpawn.Spawn(props.gasZoneDef, Position, Map, WipeMode.Vanish);
            }
        }

        private void LaunchSplitChildren(ProjectileProperties_Exo props)
        {
            Map map = Map;
            Thing launcherThing = launcher;
            IntVec3 originCell = Position;

            for (int i = 0; i < props.splitChildCount; i++)
            {
                float angle;
                if (props.splitPlusPattern)
                {
                    float baseAngle = Rand.Range(0f, 360f);
                    angle = baseAngle + i * 90f;
                }
                else
                {
                    float step = 360f / props.splitChildCount;
                    angle = Rand.Range(0f, step) + i * step;
                }

                Vector3 dir = Quaternion.AngleAxis(angle, Vector3.up) * Vector3.forward;
                IntVec3 dest = (originCell.ToVector3Shifted() + dir * props.splitChildRange).ToIntVec3();
                if (!dest.InBounds(map))
                {
                    dest = originCell;
                }

                Projectile child = (Projectile)GenSpawn.Spawn(props.splitChildDef, originCell, map, WipeMode.Vanish);
                child.Launch(launcherThing, originCell.ToVector3Shifted() + dir.normalized, new LocalTargetInfo(dest),
                    new LocalTargetInfo(dest), ProjectileHitFlags.All, false, null);
            }
        }
    }

    // Lingering area-denial field (Ares plasma gas, plague clouds, tesla gas fields): an
    // invisible-to-collision translucent cloud thing that repeatedly damages every pawn inside
    // its radius for a fixed duration, then vanishes. Modeled on Infernum's PlasmaGas /
    // AresTeslaGasField / PlagueCloud - damaging only while "opaque" is approximated by a
    // damage-free tail period (last quarter of its lifetime).
    public class DamageZone_Exo : Thing
    {
        private int age;
        private int ticksUntilDamage;

        public DefModExtension_DamageZone Props => def.GetModExtension<DefModExtension_DamageZone>();

        protected override void Tick()
        {
            base.Tick();

            DefModExtension_DamageZone props = Props;
            if (props == null)
            {
                Destroy(DestroyMode.Vanish);
                return;
            }

            age++;
            if (age >= props.durationTicks)
            {
                Destroy(DestroyMode.Vanish);
                return;
            }

            // Last quarter of the lifetime is the visual fade-out tail: harmless, like Infernum's
            // opacity-gated gas.
            if (age < props.durationTicks * 3 / 4 && --ticksUntilDamage <= 0)
            {
                ticksUntilDamage = props.damageIntervalTicks;
                DamagePawnsInside(props);
            }

            if (props.fleckDef != null && Find.TickManager.TicksGame % props.fleckIntervalTicks == 0)
            {
                Vector3 center = DrawPos + new Vector3(Rand.Range(-props.radius, props.radius) * 0.7f, 0f,
                    Rand.Range(-props.radius, props.radius) * 0.7f);
                FleckMaker.Static(center, Map, props.fleckDef, props.fleckScale);
            }
        }

        private void DamagePawnsInside(DefModExtension_DamageZone props)
        {
            Map map = Map;
            foreach (Thing thing in GenRadial.RadialDistinctThingsAround(Position, map, props.radius, true))
            {
                if (thing is Pawn victim && !victim.Dead && victim.def != def)
                {
                    DamageInfo dinfo = new DamageInfo(props.damageDef, props.damageAmount, props.armorPenetration, -1f, null);
                    victim.TakeDamage(dinfo);

                    if (props.fireChancePerInterval > 0f && Rand.Chance(props.fireChancePerInterval))
                    {
                        FireUtility.TryAttachFire(victim, 0.3f, null);
                    }
                }
            }
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref age, "zoneAge", 0);
            Scribe_Values.Look(ref ticksUntilDamage, "zoneTicksUntilDamage", 0);
        }
    }

    public class DefModExtension_DamageZone : DefModExtension
    {
        public float radius = 2.5f;
        public int durationTicks = 180;
        public int damageIntervalTicks = 15;
        public float damageAmount = 3f;
        public DamageDef damageDef;
        public float armorPenetration = 0.3f;
        public float fireChancePerInterval = 0f;
        public FleckDef fleckDef;
        public float fleckScale = 1.5f;
        public int fleckIntervalTicks = 20;
    }
}
