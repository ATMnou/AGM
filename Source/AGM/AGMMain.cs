using System;
using System.Reflection;
using HarmonyLib;
using Verse;

namespace AGM
{
    // Mod entry: Harmony bootstrap. (The old WormBoss toggle was removed together with the
    // scrapped segmented-worm Astra implementation.)
    public class AGMMod : Mod
    {
        public AGMMod(ModContentPack content) : base(content)
        {
        }
    }

    [StaticConstructorOnStartup]
    public static class AGMMain
    {
        static AGMMain()
        {
            Harmony harmony = new Harmony("ATMnou.agm");
            harmony.PatchAll(Assembly.GetExecutingAssembly());
        }
    }
}
