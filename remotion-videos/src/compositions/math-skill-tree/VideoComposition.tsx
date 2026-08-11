import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { buildScenes } from "./durations";
import { CardScene, ClipScene, Fade } from "./components";

export const MathSkillTreeComposition: React.FC = () => {
  const scenes = buildScenes();
  let from = 0;
  return (
    <AbsoluteFill style={{ background: "#05060f" }}>
      {scenes.map((s) => {
        const seq = (
          <Sequence key={s.id} from={from} durationInFrames={s.durFrames}>
            <Fade>
              {s.kind === "card" ? (
                <CardScene text={s.text} />
              ) : (
                <ClipScene clips={s.clips} text={s.text} audio={s.audio} />
              )}
            </Fade>
          </Sequence>
        );
        from += s.durFrames;
        return seq;
      })}
    </AbsoluteFill>
  );
};
