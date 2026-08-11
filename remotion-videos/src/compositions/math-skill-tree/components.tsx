import React from "react";
import {
  AbsoluteFill,
  Sequence,
  Audio,
  Video,
  staticFile,
  useCurrentFrame,
  interpolate,
  Easing,
} from "remotion";
import clipDur from "../../../public/assets/clips/durations.json";
import { FPS } from "./constants";

const FONT = '"Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", sans-serif';

// 字幕 / 花字（录屏幕底部）
export const Subtitle: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const op = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 96,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          maxWidth: 1560,
          textAlign: "center",
          color: "#fff",
          fontFamily: FONT,
          fontSize: 46,
          fontWeight: 700,
          lineHeight: 1.35,
          opacity: op,
          textShadow: "0 2px 14px rgba(0,0,0,0.95)",
          background: "rgba(8,10,25,0.42)",
          padding: "18px 36px",
          borderRadius: 20,
          border: "1px solid rgba(255,217,138,0.4)",
          backdropFilter: "blur(2px)",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

// 淡入（每幕开头）
export const Fade: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const op = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ opacity: op }}>{children}</AbsoluteFill>;
};

// 痛点文字卡（暗场渐变 + 大字）
export const CardScene: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, 22], [0.9, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const op = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 50% 38%, #15203f 0%, #0a0e1f 55%, #05060f 100%)",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          opacity: op,
          maxWidth: 1460,
          textAlign: "center",
          color: "#ffe9b8",
          fontFamily: FONT,
          fontSize: 74,
          fontWeight: 800,
          lineHeight: 1.32,
          letterSpacing: 1,
          textShadow: "0 6px 28px rgba(0,0,0,0.85)",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

// 录屏幕：顺序拼接多个 clip + 字幕 + 配音
export const ClipScene: React.FC<{ clips: string[]; text: string; audio: string }> = ({
  clips,
  text,
  audio,
}) => {
  let from = 0;
  const els = clips.map((c) => {
    const sec = (clipDur as Record<string, number>)[c] ?? 8;
    const frames = Math.max(1, Math.round(sec * FPS));
    const el = (
      <Sequence key={c} from={from} durationInFrames={frames}>
        <AbsoluteFill>
          <Video
            src={staticFile(`assets/clips/${c}.mp4`)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </AbsoluteFill>
      </Sequence>
    );
    from += frames;
    return el;
  });
  return (
    <AbsoluteFill>
      {els}
      <Subtitle text={text} />
      <Audio src={staticFile(`assets/audio/${audio}.mp3`)} />
    </AbsoluteFill>
  );
};
