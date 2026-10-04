using System;
using System.Linq;
using RimWorld;
using RimWorld.Planet;
using Verse;
using Verse.Sound;
using UnityEngine;
using System.Collections.Generic;

namespace AGM
{
    // Ability effects - verbatim ports of GD3's CompAbilityEffect_AnnihilatorJump / _Suspend /
    // _JumpAndSuspend, re-pointed at Mythos_Pawn and the Mythos defOf fields.
    public class CompAbilityEffect_MythosJump : CompAbilityEffect
    {
        public override void Apply(LocalTargetInfo target, LocalTargetInfo dest)
        {
            Mythos_Pawn pawn = parent.pawn as Mythos_Pawn;
            if (pawn != null)
            {
                pawn.JumpTo(target);
            }
        }

        public override void Apply(GlobalTargetInfo target)
        {
            this.Apply(null, null);
        }

        public override bool CanApplyOn(LocalTargetInfo target, LocalTargetInfo dest)
        {
            return true;
        }

        public override bool AICanTargetNow(LocalTargetInfo target)
        {
            Mythos_Pawn pawn = parent.pawn as Mythos_Pawn;
            if (!pawn.AnimationIdle || pawn.Flying)
            {
                return false;
            }
            return true;
        }

        public override bool CanApplyOn(GlobalTargetInfo target)
        {
            return this.CanApplyOn(null, null);
        }

        public override bool GizmoDisabled(out string reason)
        {
            reason = null;
            Mythos_Pawn pawn = parent.pawn as Mythos_Pawn;
            if (!pawn.AnimationIdle || pawn.Flying)
            {
                reason = "AGM.MythosBusy".Translate(pawn.LabelShort);
                return true;
            }
            if (pawn.Dying)
            {
                return true;
            }
            return false;
        }

        public override void DrawEffectPreview(LocalTargetInfo target)
        {
            Map map = Find.CurrentMap;
            if (map != null && target.Cell.InBounds(map))
            {
                List<IntVec3> cells = map.AllCells.Where(c => GenAdj.IsInside(c, target.Cell, Rot4.East, new IntVec2(9, 9))).ToList();
                if (cells.Any())
                {
                    GenDraw.DrawFieldEdges(cells);
                }
            }
        }
    }

    public class CompAbilityEffect_MythosSuspend : CompAbilityEffect
    {
        public override void Apply(LocalTargetInfo target, LocalTargetInfo dest)
        {
            Mythos_Pawn pawn = parent.pawn as Mythos_Pawn;
            if (pawn != null)
            {
                pawn.ReadySuspend();
            }
        }

        public override void Apply(GlobalTargetInfo target)
        {
            this.Apply(null, null);
        }

        public override bool CanApplyOn(LocalTargetInfo target, LocalTargetInfo dest)
        {
            return true;
        }

        public override bool AICanTargetNow(LocalTargetInfo target)
        {
            Mythos_Pawn pawn = parent.pawn as Mythos_Pawn;
            if (!pawn.AnimationIdle || pawn.Flying)
            {
                return false;
            }
            if (pawn.PositionHeld.DistanceTo(target.Cell) > Mythos_Pawn.IfEnemyClose)
            {
                return false;
            }
            return true;
        }

        public override bool CanApplyOn(GlobalTargetInfo target)
        {
            return this.CanApplyOn(null, null);
        }

        public override bool GizmoDisabled(out string reason)
        {
            reason = null;
            Mythos_Pawn pawn = parent.pawn as Mythos_Pawn;
            if (!pawn.AnimationIdle || pawn.Flying)
            {
                reason = "AGM.MythosBusy".Translate(pawn.LabelShort);
                return true;
            }
            if (pawn.Dying)
            {
                return true;
            }
            return false;
        }
    }

    public class CompAbilityEffect_MythosJumpAndSuspend : CompAbilityEffect
    {
        public override void Apply(LocalTargetInfo target, LocalTargetInfo dest)
        {
            Mythos_Pawn pawn = parent.pawn as Mythos_Pawn;
            if (pawn != null)
            {
                pawn.JumpTo(target, true);
            }
        }

        public override void Apply(GlobalTargetInfo target)
        {
            this.Apply(null, null);
        }

        public override bool CanApplyOn(LocalTargetInfo target, LocalTargetInfo dest)
        {
            return true;
        }

        public override bool AICanTargetNow(LocalTargetInfo target)
        {
            Mythos_Pawn pawn = parent.pawn as Mythos_Pawn;
            if (!pawn.AnimationIdle || pawn.Flying)
            {
                return false;
            }
            if (pawn.PositionHeld.DistanceTo(target.Cell) <= Mythos_Pawn.IfEnemyClose)
            {
                return false;
            }
            return true;
        }

        public override bool CanApplyOn(GlobalTargetInfo target)
        {
            return this.CanApplyOn(null, null);
        }

        public override bool GizmoDisabled(out string reason)
        {
            reason = null;
            Mythos_Pawn pawn = parent.pawn as Mythos_Pawn;
            if (!pawn.AnimationIdle || pawn.Flying)
            {
                reason = "AGM.MythosBusy".Translate(pawn.LabelShort);
                return true;
            }
            if (pawn.Dying)
            {
                return true;
            }
            return false;
        }

        public override void DrawEffectPreview(LocalTargetInfo target)
        {
            Map map = Find.CurrentMap;
            if (map != null && target.Cell.InBounds(map))
            {
                List<IntVec3> cells = map.AllCells.Where(c => GenAdj.IsInside(c, target.Cell, Rot4.East, new IntVec2(9, 9))).ToList();
                if (cells.Any())
                {
                    GenDraw.DrawFieldEdges(cells);
                }
            }
        }
    }
}
