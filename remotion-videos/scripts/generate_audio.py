import asyncio
from pathlib import Path
import edge_tts
import subprocess
import json

VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "+30%"
OUT_DIR = Path(__file__).resolve().parent.parent / "public" / "assets" / "audio"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 11 幕最终配音文案（痛点共鸣型 · 家长口吻 · 数字准确）
NARRATIONS = [
    ("scene1", "孩子卡在一道题，你急得直跺脚。问他哪儿不会？他说不清；你想帮，更说不清——到底缺的是哪一块？"),
    ("scene2", "课本只按年级排，从不说这题为啥要会、前面缺了啥。你让孩子刷百题，换身皮又错——知识是网，不是线。"),
    ("scene3", "如果数学是一整片星空呢？每颗星都亮着，清楚知道自己连着哪颗、通向哪颗。"),
    ("scene4", "小学到初中、四到十八岁，七百零二个知识点、一千两百七十七条依赖，画成可拖可放的宇宙。鼠标一拖就平移，滚轮对着光标缩放——整张地图尽在眼前。"),
    ("scene5", "点开任意一颗星，右侧弹出档案：前序是啥、后续学啥，缺哪块、下一步点哪颗，一眼看穿。前序后续还能直接点，顺着链路追。"),
    ("scene6", "怕学偏了？开“仅看中国课标”，一键只看对齐人教版的星，还标着一年级上、加减法那一册。学的算不算课标，心里都清楚。"),
    ("scene7", "按学科？领域下拉。按年龄？点四到六、七到九、十到十二、十三岁以上标签——二十三个领域、四个年龄段，说聚焦就聚焦。"),
    ("scene8", "孩子真懂了，就点亮这颗星。进度存本地、两页都认；点亮金紫一闪，进度环加一，下一颗该学的星开始轻轻呼吸。"),
    ("scene9", "不爱看宇宙？切“学习之河”，按年龄把星铺成有序的河。同样筛选、同样点亮，跨年级联系顺河看清。"),
    ("scene10", "搜索框秒定位、连线开关、流动动画、领域图例、一键重置进度——常用控件一笔带过，都在手边。"),
    ("scene11", "数学天赋星图，给孩子一张看得见全貌的数学地图。别再瞎补了——点亮的每一颗，都是他真正掌握的星。"),
]

async def main():
    durations = {}
    for name, text in NARRATIONS:
        out = OUT_DIR / f"{name}.mp3"
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
        await communicate.save(str(out))
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(out)],
            capture_output=True, text=True
        )
        dur = float(result.stdout.strip() or 0)
        durations[name] = round(dur, 2)
        print(f"generated {out.name}: {dur:.2f}s")
    with open(OUT_DIR / "durations.json", "w", encoding="utf-8") as f:
        json.dump(durations, f, ensure_ascii=False, indent=2)
    print("wrote durations.json")

asyncio.run(main())
