using RimWorld;
using Verse;

namespace AGM
{
    // DefModExtension - verbatim port of GD3.IsFlyingUnit (used by its Flying_Patch to scale the
    // flight tracker's draw offset; Mythos uses flyingHeight = 10 like the original Annihilator).
    public class IsFlyingUnit : DefModExtension
    {
        public float flyingHeight = 2.0f;

        public bool flightDeterminedByCode = false;
    }
}
