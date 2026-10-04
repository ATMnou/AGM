using System;
using System.Collections.Generic;
using System.Linq;
using Verse;
using RimWorld;
using UnityEngine;

namespace AGM
{
    // Animation workers - verbatim ports of GD3's AnimationWorker_Jump / AnimationWorker_Trigonometric /
    // AnimationWorker_RandomShake, referenced by the copied Mythos AnimationDefs.
    public class AnimationWorker_Jump : AnimationWorker_Keyframes
    {
        public override Vector3 OffsetAtTick(int tick, AnimationDef def, PawnRenderNode node, AnimationPart part, PawnDrawParms parms)
        {
            Vector3 offset = base.OffsetAtTick(tick, def, node, part, parms);
            offset *= (float)(((3 + 2 * Math.Sqrt(2)) / 9600) * Math.Pow(tick, 2) + ((-1 - Math.Sqrt(2)) / 40) * tick);
            return offset;
        }
    }

    public class AnimationWorker_Jump_Light : AnimationWorker_Keyframes
    {
        public override Vector3 OffsetAtTick(int tick, AnimationDef def, PawnRenderNode node, AnimationPart part, PawnDrawParms parms)
        {
            Vector3 offset = base.OffsetAtTick(tick, def, node, part, parms);
            offset *= (float)((1.0 / 2400) * Math.Pow(tick, 2) + (-1.0 / 20) * tick);
            return offset;
        }
    }

    public class AnimationWorker_Trigonometric : AnimationWorker_Keyframes
    {
        public override Vector3 OffsetAtTick(int tick, AnimationDef def, PawnRenderNode node, AnimationPart part, PawnDrawParms parms)
        {
            Vector3 offset = base.OffsetAtTick(tick, def, node, part, parms);
            offset *= Mathf.Sin(tick * Mathf.PI / (def.durationTicks / 2f));
            return offset;
        }
    }

    public class AnimationWorker_RandomShake : AnimationWorker_Keyframes
    {
        private Vector3 tmpOffset = Vector3.zero;

        private int tmpInt = -1;

        public override Vector3 OffsetAtTick(int tick, AnimationDef def, PawnRenderNode node, AnimationPart part, PawnDrawParms parms)
        {
            Vector3 offset = base.OffsetAtTick(tick, def, node, part, parms);
            if (tmpInt != tick)
            {
                tmpInt = tick;
                tmpOffset = MythosUtil.RandomPointInCircle(0.10f);
            }
            return offset + tmpOffset;
        }
    }

    public static class MythosUtil
    {
        // GDUtility.RandomPointInCircle - same uniform-in-disc sampling the original uses.
        public static Vector3 RandomPointInCircle(float radius)
        {
            double angle = Rand.Range(0f, Mathf.PI * 2f);
            float r = Mathf.Sqrt(Rand.Range(0f, 1f)) * radius;
            return new Vector3((float)Math.Cos(angle) * r, 0f, (float)Math.Sin(angle) * r);
        }
    }
}
