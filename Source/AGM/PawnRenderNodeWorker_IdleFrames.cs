using System.Collections.Generic;
using System.Linq;
using RimWorld;
using UnityEngine;
using Verse;

namespace AGM
{
    // Frame-animated render node: cycles a fixed list of textures (props.texPaths)
    // driven by the game clock. The node exposes EVERY frame through GraphicsFor so
    // vanilla re-resolves the material on each draw request
    // (PawnRenderNode.CheckMaterialEveryDrawRequest => graphics.Count > 1) - without
    // that, the material is resolved once and the sprite never advances.
    public class PawnRenderNodeProperties_IdleFrames : PawnRenderNodeProperties
    {
        public int frameTicks = 10;
    }

    public class PawnRenderNode_IdleFrames : PawnRenderNode
    {
        private Graphic[] frames;

        public PawnRenderNode_IdleFrames(Pawn pawn, PawnRenderNodeProperties props, PawnRenderTree tree)
            : base(pawn, props, tree)
        {
        }

        public PawnRenderNodeProperties_IdleFrames FrameProps => (PawnRenderNodeProperties_IdleFrames)props;

        public Graphic[] Frames
        {
            get
            {
                if (frames == null)
                {
                    List<Graphic> list = new List<Graphic>();
                    if (!props.texPaths.NullOrEmpty())
                    {
                        foreach (string path in props.texPaths)
                        {
                            list.Add(GraphicDatabase.Get<Graphic_Single>(path, ShaderFor(tree.pawn), Vector2.one, ColorFor(tree.pawn)));
                        }
                    }
                    frames = list.ToArray();
                }
                return frames;
            }
        }

        public int CurrentFrameIndex()
        {
            return Frames.Length == 0 ? 0 : Find.TickManager.TicksGame / FrameProps.frameTicks % Frames.Length;
        }

        protected override IEnumerable<Graphic> GraphicsFor(Pawn pawn)
        {
            return Frames;
        }

        public override Graphic GraphicFor(Pawn pawn)
        {
            Graphic[] array = Frames;
            return array.Length == 0 ? null : array[0];
        }
    }

    public class PawnRenderNodeWorker_IdleFrames : PawnRenderNodeWorker
    {
        protected override Graphic GetGraphic(PawnRenderNode node, PawnDrawParms parms)
        {
            PawnRenderNode_IdleFrames frameNode = (PawnRenderNode_IdleFrames)node;
            Graphic[] array = frameNode.Frames;
            if (array.Length == 0)
            {
                return null;
            }
            return array[frameNode.CurrentFrameIndex()];
        }
    }
}
