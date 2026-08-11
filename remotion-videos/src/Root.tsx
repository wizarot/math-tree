import React from "react";
import { Composition } from "remotion";
import { MathSkillTreeComposition } from "./compositions/math-skill-tree/VideoComposition";
import { TOTAL_FRAMES } from "./compositions/math-skill-tree/durations";
import { FPS, WIDTH, HEIGHT } from "./compositions/math-skill-tree/constants";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="math-skill-tree"
      component={MathSkillTreeComposition}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      defaultProps={{}}
    />
  );
};
