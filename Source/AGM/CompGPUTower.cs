using System.Collections.Generic;
using System.Linq;
using RimWorld;
using Verse;

namespace AGM
{
    // GPU Tower: converts grid power into IO Tokens. Yield (1/2/4/6 per day) scales with the
    // Compute Efficiency research chain and applies to existing buildings the moment research
    // completes. Power draw scaling is handled by vanilla powerUpgrades on the def.
    // Finished tokens drop onto free cells around the tower (stacks merge via ThingPlaceMode.Near).
    public class CompProperties_GPUTower : CompProperties
    {
        public CompProperties_GPUTower()
        {
            compClass = typeof(CompGPUTower);
        }
    }

    public class CompGPUTower : ThingComp
    {
        private const int TicksPerDay = 60000;

        private CompPowerTrader power;
        private int acc;
        private ResearchProjectDef effI;
        private ResearchProjectDef effIII;
        private ResearchProjectDef effV;

        public CompProperties_GPUTower Props => (CompProperties_GPUTower)props;

        private static ResearchProjectDef GetEff(string suffix)
        {
            return DefDatabase<ResearchProjectDef>.GetNamedSilentFail("AGM_ComputeEfficiency_" + suffix);
        }

        private static bool Finished(ResearchProjectDef def)
        {
            return def != null && def.IsFinished;
        }

        public int TokensPerDay()
        {
            if (Finished(effV)) return 6;
            if (Finished(effIII)) return 4;
            if (Finished(effI)) return 2;
            return 1;
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            power = parent.GetComp<CompPowerTrader>();
            effI = GetEff("I");
            effIII = GetEff("III");
            effV = GetEff("V");
        }

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref acc, "gpuTokenAcc", 0);
        }

        public override void CompTick()
        {
            base.CompTick();
            if (power == null || !power.PowerOn)
            {
                return;
            }
            acc++;
            if (acc >= TicksPerDay / TokensPerDay())
            {
                acc = 0;
                SpawnToken();
            }
        }

        private void SpawnToken()
        {
            Map map = parent.Map;
            if (map == null)
            {
                return;
            }
            Thing token = ThingMaker.MakeThing(DefDatabase<ThingDef>.GetNamed("AGM_IOToken"));
            token.stackCount = 1;
            bool placed = GenPlace.TryPlaceThing(token, parent.Position, map, ThingPlaceMode.Near, null,
                extraValidator: delegate (IntVec3 c)
                {
                    if (c.Fogged(map))
                    {
                        return false;
                    }
                    List<Thing> things = c.GetThingList(map);
                    return !things.Any(t => t.def.passability == Traversability.Impassable);
                });
            if (!placed)
            {
                // no free cell right now - retry shortly by rewinding the accumulator one step
                acc = TicksPerDay / TokensPerDay() - 1;
            }
        }

        public override string CompInspectStringExtra()
        {
            // Only report the yield while actually powered - the unpowered state is already
            // signalled by the vanilla needs-power overlay, and reporting a yield there
            // alongside a misleading 0 W draw just confuses things.
            if (power == null || !power.PowerOn)
            {
                return null;
            }
            return "AGM.GPUTowerInspect".Translate(TokensPerDay());
        }
    }
}
