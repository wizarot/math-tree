import audioDur from "../../../public/assets/audio/durations.json";
import clipDur from "../../../public/assets/clips/durations.json";
import { FPS } from "./constants";

export type SceneKind = "card" | "clip";

export interface SceneDef {
  id: string;
  audio: string; // sceneN (no extension)
  clips: string[]; // C0..C8 (no extension)
  text: string; // 字幕 / 花字
  kind: SceneKind;
  pad: number; // 额外秒数（转场 + 余量）
}

// 幕序：痛点卡 1-3，真实录屏 4-11。clip 顺序拼接；幕时长 = max(配音, 录屏总时长) + pad
export const SCENE_DEFS: SceneDef[] = [
  { id: "scene1", audio: "scene1", clips: [], text: "孩子卡题，你却说不清缺哪块", kind: "card", pad: 1.0 },
  { id: "scene2", audio: "scene2", clips: [], text: "刷百题仍错，知识是网不是线", kind: "card", pad: 1.0 },
  { id: "scene3", audio: "scene3", clips: [], text: "如果数学，是一片星空", kind: "card", pad: 1.0 },
  { id: "scene4", audio: "scene4", clips: ["C0"], text: "702 知识点 · 1277 依赖，一图全收", kind: "clip", pad: 1.2 },
  { id: "scene5", audio: "scene5", clips: ["C1", "C5"], text: "缺哪块 · 学什么，一眼看穿", kind: "clip", pad: 1.2 },
  { id: "scene6", audio: "scene6", clips: ["C2"], text: "一键只看人教版课标星", kind: "clip", pad: 1.2 },
  { id: "scene7", audio: "scene7", clips: ["C3"], text: "按学科 · 按年龄，精准聚焦", kind: "clip", pad: 1.2 },
  { id: "scene8", audio: "scene8", clips: ["C4"], text: "真懂就点亮，下一颗呼吸亮起", kind: "clip", pad: 1.2 },
  { id: "scene9", audio: "scene9", clips: ["C6", "C7"], text: "星图 ↔ 学习之河，双视图随心", kind: "clip", pad: 1.2 },
  { id: "scene10", audio: "scene10", clips: ["C8"], text: "搜索 · 连线 · 图例，控件全在手边", kind: "clip", pad: 1.2 },
  { id: "scene11", audio: "scene11", clips: ["C0"], text: "给孩子一张，看得见全貌的数学地图", kind: "clip", pad: 2.0 },
];

export interface BuiltScene extends SceneDef {
  audioSec: number;
  clipSec: number;
  dur: number;
  durFrames: number;
}

export function buildScenes(): BuiltScene[] {
  return SCENE_DEFS.map((s) => {
    const a = (audioDur as Record<string, number>)[s.audio] ?? 0;
    const c = s.clips.reduce((acc, id) => acc + ((clipDur as Record<string, number>)[id] ?? 0), 0);
    const dur = Math.max(a, c) + s.pad;
    return { ...s, audioSec: a, clipSec: c, dur, durFrames: Math.round(dur * FPS) };
  });
}

export const TOTAL_FRAMES = buildScenes().reduce((a, s) => a + s.durFrames, 0);
