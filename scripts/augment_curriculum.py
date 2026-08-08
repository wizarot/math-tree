# -*- coding: utf-8 -*-
"""将人教版小学数学新课标知识点并入 math-skill-tree 数据：
- 已有的节点 -> 打 inChineseCurriculum + curriculumLabel 标记
- 缺失的概念 -> 新增节点(cn_*)并补前置依赖边
"""
import json, re

BASE = "D:/projects/math-skill-tree"
TOPICS_F = f"{BASE}/data/math-topics.json"
DEPS_F   = f"{BASE}/data/math-dependencies.json"
HTML_F   = f"{BASE}/index.html"

data = json.load(open(TOPICS_F, encoding="utf-8"))
deps = json.load(open(DEPS_F, encoding="utf-8"))
topics = data["topics"]
by_id = {t["id"]: t for t in topics}

def find_ids(*kw):
    out = []
    for t in topics:
        zh = t.get("name_zh") or ""
        if any(k in zh for k in kw):
            out.append(t["id"])
    return out

def find_id(kw):
    ids = find_ids(kw)
    return ids[0] if ids else None

# ---------------- 1. 新课标条目 -> 匹配现有节点(打标) ----------------
# key: 人教版章节标签 ; val: 用于检索现有节点的中文关键词
MATCH = {
 "一年级上/数一数": ["数 20 以内的物体", "点数", "一一对应计数", "基数原则"],
 "一年级上/比一比": ["比较长短与高矮", "用测量比较长短", "物体的可测属性"],
 "一年级上/分一分": ["按类别分类", "分类二维与三维图形"],
 "一年级上/认位置": ["位置语言"],
 "一年级上/认数（一）": ["读写 20 以内的数", "读出并写出数字"],
 "一年级上/加减法（一）": ["5 以内加减法", "加减法应用题", "加减法的含义"],
 "一年级上/认识图形（一）": ["长方形", "正方形", "圆形", "三角形", "认图形", "画二维图形"],
 "一年级上/分类": ["按类别分类", "按属性分类图形"],
 "一年级上/认识钟表": ["认时间：整点与半点"],
 "一年级下/位置": ["位置语言", "位置、方向与运动"],
 "一年级下/20以内的退位减法": ["20 以内加减法熟练", "退位"],
 "一年级下/图形的拼组": ["组合简单图形", "拼组"],
 "一年级下/100以内数的认识": ["读写 100 以内的数"],
 "一年级下/摆一摆想一想": ["读写 100 以内的数", "用小棒"],
 "一年级下/100以内的加法和减法（一）": ["100 以内加减法熟练", "1000 以内的加减", "加减法的心算与笔算"],
 "二年级上/长度单位": ["测量长度（6 岁", "用不同单位测量", "厘米", "米"],
 "二年级上/100以内的加法和减法（二）": ["100 以内加减法熟练", "1000 以内的加减"],
 "二年级上/角的初步认识": ["角的类型", "锐角", "直角"],
 "二年级上/表内乘法（一）": ["乘法表（8 岁", "用阵列表示乘法"],
 "二年级上/表内乘法（二）": ["乘法表中的规律", "乘法表（8 岁"],
 "二年级上/认识时间": ["精确到分钟认时间"],
 "二年级下/数据收集整理": ["数据收集", "把数据按类别整理", "分类数据"],
 "二年级下/表内除法（一）": ["除法的含义", "带余数的除法"],
 "二年级下/表内除法（二）": ["带余数的除法", "笔算乘除法"],
 "二年级下/混合运算": ["混合运算口算", "运算顺序", "多步问题"],
 "二年级下/有余数的除法": ["带余数的除法"],
 "二年级下/万以内数的认识": ["读写 1000 万以内的数", "千万以内的数"],
 "三年级上/万以内的加法和减法（一）": ["1000 以内的加减", "加减法的心算与笔算"],
 "三年级上/测量": ["选择测量单位", "测量长度（7 岁", "用不同单位测量"],
 "三年级上/多位数乘一位数": ["笔算乘除法"],
 "三年级上/长方形和正方形": ["长方形的周长", "正方形的周长", "四边形分类"],
 "三年级上/分数的初步认识": ["认识分数（简单）", "单位分数", "二分之一", "四分之一"],
 "三年级下/除数是一位数的除法": ["带余数的除法", "笔算乘除法"],
 "三年级下/两位数乘两位数": ["笔算乘除法", "乘法表中的规律"],
 "三年级下/面积": ["长方形的面积", "正方形的面积", "面积单位"],
 "三年级下/小数的初步认识": ["小数与百分数记法"],
 "四年级上/大数的认识": ["读写 1000 万以内的数", "千万以内的数"],
 "四年级上/角的度量": ["测量角", "角的大小"],
 "四年级上/三位数乘两位数": ["笔算乘除法"],
 "四年级上/平行四边形和梯形": ["平行四边形", "梯形", "四边形分类"],
 "四年级上/除数是两位数的除法": ["笔算乘除法"],
 "四年级上/条形统计图": ["条形统计图", "频数表与统计图"],
 "四年级下/四则运算": ["运算顺序"],
 "四年级下/运算定律与简便运算": ["交换律", "结合律", "分配律", "运算定律", "简便运算"],
 "四年级下/小数的意义和性质": ["小数的意义", "小数的性质"],
 "四年级下/三角形的特性": ["三角形的", "三角形分类", "画高"],
 "四年级下/小数的加法和减法": ["小数的加法和减法"],
 "四年级下/图形的运动（二）": ["坐标变换（平移/旋转/反射）", "旋转", "平移"],
 "四年级下/平均数与条形统计图": ["平均数", "条形统计图"],
 "五年级上/小数乘法": ["小数乘法"],
 "五年级上/小数除法": ["小数除法"],
 "五年级上/可能性": ["排序可能性", "可能性"],
 "五年级上/简易方程": ["方程", "解方程"],
 "五年级上/多边形的面积": ["平行四边形的面积", "三角形的面积", "梯形的面积"],
 "五年级下/因数与倍数": ["因数、倍数", "10 的倍数", "100 的倍数"],
 "五年级下/长方体和正方体": ["长方体", "正方体", "表面积", "体积"],
 "五年级下/分数的意义和性质": ["分数的意义", "等值分数", "分数单位"],
 "五年级下/分数的加法和减法": ["分数的加法和减法"],
 "五年级下/图形的变换": ["坐标变换（平移/旋转/反射）", "网格上的图形变换"],
 "五年级下/长方体和正方体的体积": ["长方体的体积", "正方体的体积", "体积单位"],
 "六年级上/分数乘法": ["分数乘法"],
 "六年级上/分数除法": ["分数除法"],
 "六年级上/比": ["比的记号", "化简比", "求比值"],
 "六年级上/圆": ["圆的周长与面积", "圆的特征"],
 "六年级上/百分数的认识": ["理解百分数", "百分数与小数等值"],
 "六年级上/扇形统计图": ["饼图与折线图"],
 "六年级下/负数": ["负数", "正数与负数"],
 "六年级下/比例": ["比例", "解比例"],
 "六年级下/比例的应用": ["比例的应用", "按比例分配", "图形的放大与缩小"],
 "六年级下/图形的放缩": ["图形的放大与缩小", "放缩"],
}

tagged = {}  # id -> list of labels
for label, kws in MATCH.items():
    ids = find_ids(*kws)
    for i in ids:
        tagged.setdefault(i, []).append(label)

for i, labels in tagged.items():
    t = by_id[i]
    t["inChineseCurriculum"] = True
    t["curriculumLabel"] = "；".join(labels)
    t.setdefault("source", "Marble+中国课标")

print(f"[标记] 共打标 {len(tagged)} 个已有节点（覆盖 {len(MATCH)} 个新课标章节）")

# ---------------- 2. 新增缺失的中国课标节点 ----------------
def nid(s): return "cn_" + s

NEW = [
 dict(id=nid("renminbi"), domain="Measurement", type="PROCEDURAL",
   name="Recognizing and using RMB (Chinese currency)",
   name_zh="认识人民币",
   description_zh="认识元、角、分及面值，能进行简单的人民币换算与购物计算",
   evidence_zh=["说出 1 元 = 10 角、1 角 = 10 分", "用 10 元买 3 元 5 角的文具，算出应找回多少", "把 25 角写成几元几角"],
   assessmentPrompt_zh="拿一把尺子标价 2 元 8 角、一块橡皮 5 角，问孩子：如果他给店员 5 元，应该找回多少钱？",
   ageStart=6, ageEnd=7, centrality=0.05,
   prereq=["读写 100 以内的数"], prereq_strength="hard"),

 dict(id=nid("observe3d"), domain="Geometry", type="CONCEPTUAL",
   name="Viewing 3D objects from different viewpoints",
   name_zh="观察物体（多面观察）",
   description_zh="能从正面、侧面、上面观察同一物体，辨别不同视角下的形状",
   evidence_zh=["说出玩具熊从正面和侧面看分别像什么", "把从上面看到的图形连到对应物体", "判断三视图中哪幅是左视图"],
   assessmentPrompt_zh="摆一个积木，问孩子：从左边看和从正面看，看到的形状一样吗？请他画出来。",
   ageStart=7, ageEnd=8, centrality=0.05,
   prereq=["画二维图形与认三维图形（7 岁+）"], prereq_strength="soft"),

 dict(id=nid("symaxis"), domain="Geometry", type="CONCEPTUAL",
   name="Line symmetry / axisymmetric figures",
   name_zh="轴对称图形",
   description_zh="认识轴对称现象，能找出对称轴并判断一个图形是否轴对称",
   evidence_zh=["对折一张纸剪出图形，说出折痕就是对称轴", "在正方形、平行四边形中圈出轴对称图形", "画出给定图形的对称轴"],
   assessmentPrompt_zh="给孩子一个心形和一个平行四边形，问：哪个图形对折后两边能完全重合？请他画出对称轴。",
   ageStart=7, ageEnd=9, centrality=0.05,
   prereq=["画二维图形与认三维图形（7 岁+）"], prereq_strength="soft"),

 dict(id=nid("hms"), domain="Measurement", type="PROCEDURAL",
   name="Units of time: hours, minutes, seconds",
   name_zh="时、分、秒",
   description_zh="认识时、分、秒及其进率（1 时=60 分，1 分=60 秒），能进行简单时间计算",
   evidence_zh=["说出 1 分等于多少秒", "把 2 时 30 分写成多少分", "估算一首歌大约唱了几分钟"],
   assessmentPrompt_zh="对孩子说：一节课 40 分钟，如果 8:20 开始，几点几分结束？他能算出来吗？",
   ageStart=8, ageEnd=9, centrality=0.06,
   prereq=["认时间：整点与半点"], prereq_strength="hard"),

 dict(id=nid("bei"), domain="Ratio & Proportion", type="CONCEPTUAL",
   name="Concept of 'times' (multiplicative comparison)",
   name_zh="倍的认识",
   description_zh="理解“倍”的含义，能用“倍”表示两个数量之间的倍数关系",
   evidence_zh=["说清楚 6 是 2 的几倍", "画图表示“苹果是梨的 3 倍”", "已知一份有 4 个，3 倍是多少"],
   assessmentPrompt_zh="摆 2 个红球、6 个蓝球，问孩子：蓝球的数量是红球的几倍？他能用除法想出来吗？",
   ageStart=8, ageEnd=9, centrality=0.07,
   prereq=["乘法表（8 岁+）"], prereq_strength="soft"),

 dict(id=nid("directions"), domain="Geometry", type="CONCEPTUAL",
   name="Cardinal directions (N/E/S/W) and describing position",
   name_zh="认识东南西北",
   description_zh="认识东、南、西、北四个基本方向，能在具体情境中用方向描述物体位置",
   evidence_zh=["面向太阳升起的方向说出是东", "用“学校在家的北面”描述位置", "根据“先向东再向南”找到目的地"],
   assessmentPrompt_zh="画一个简单地图，问孩子：如果图书馆在操场的东边、教学楼在南边，他从图书馆去教学楼该往哪走？",
   ageStart=8, ageEnd=9, centrality=0.05,
   prereq=["位置语言"], prereq_strength="hard"),

 dict(id=nid("compoundchart"), domain="Data & Statistics", type="PROCEDURAL",
   name="Compound / dual-category statistical charts",
   name_zh="复式统计图",
   description_zh="能绘制并分析含两组数据的复式条形图或复式统计表，进行简单对比",
   evidence_zh=["看懂复式条形图里两组数据的区别", "把两个小组的投票数画进同一张图", "说出哪组更喜欢哪种水果"],
   assessmentPrompt_zh="给孩子两张表（男生/女生各自喜欢的运动），问：他能合并画成一张图并说出男女差异吗？",
   ageStart=8, ageEnd=10, centrality=0.05,
   prereq=["频数表与统计图（11 岁+）", "把数据按类别整理"], prereq_strength="hard"),

 dict(id=nid("calendar"), domain="Measurement", type="CONCEPTUAL",
   name="Calendar: years, months, days, leap year",
   name_zh="年、月、日",
   description_zh="认识年、月、日的关系，知道大月小月与闰年，能进行简单日期推算",
   evidence_zh=["说出一年有几个月、大月有哪些", "判断某年是不是闰年", "算出自己生日再过 100 天是几月几日（近似）"],
   assessmentPrompt_zh="问孩子：今年 2 月有多少天？如果 3 月 1 日是星期一，3 月 8 日是星期几？",
   ageStart=8, ageEnd=9, centrality=0.06,
   prereq=["认时间：整点与半点"], prereq_strength="soft"),

 dict(id=nid("optimize"), domain="Mathematical Thinking", type="CONCEPTUAL",
   name="Optimization / making the best arrangement",
   name_zh="数学广角——优化",
   description_zh="初步体会统筹优化思想，能在烧水、烙饼等情境中安排出最省时的方案",
   evidence_zh=["说出“边烧水边洗茶杯”为什么更省时", "给烙 3 张饼设计最少次数的方案", "把几件家务排成最短总时长"],
   assessmentPrompt_zh="对孩子说：煮面要 8 分钟、洗菜要 3 分钟，怎样安排能最快吃上面？他能想到同时做吗？",
   ageStart=9, ageEnd=10, centrality=0.05,
   prereq=["混合运算口算（10 岁+）"], prereq_strength="soft"),

 dict(id=nid("coordpair"), domain="Algebra", type="PROCEDURAL",
   name="Describing position with coordinate pairs",
   name_zh="用数对表示位置",
   description_zh="能用数对（列，行）在方格纸上确定和描述物体的位置",
   evidence_zh=["用（3,2）表示第 3 列第 2 行", "在方格纸上标出给定数对的点", "根据座位说出自己的数对"],
   assessmentPrompt_zh="画一个 5×5 方格，问孩子：小兵在从左数第 2 列、从下数第 4 行，用数对怎么写？",
   ageStart=10, ageEnd=11, centrality=0.06,
   prereq=["位置语言", "第一象限描点"], prereq_strength="hard"),

 dict(id=nid("treeplant"), domain="Mathematical Thinking", type="PROCEDURAL",
   name="Tree-planting / interval problems",
   name_zh="植树问题",
   description_zh="理解间隔与棵数的关系，能解决两端都栽、只栽一端、环形等植树模型问题",
   evidence_zh=["说出 10 米路每隔 2 米栽一棵（两端都栽）共几棵", "区分“棵数=间隔数+1”的情形", "用同样思路解决锯木头问题"],
   assessmentPrompt_zh="问孩子：一条 20 米的小路，每隔 5 米种一棵树（两头都种），一共要种几棵？他能画图验证吗？",
   ageStart=10, ageEnd=11, centrality=0.05,
   prereq=["带余数的除法"], prereq_strength="soft"),

 dict(id=nid("linechart"), domain="Data & Statistics", type="PROCEDURAL",
   name="Line graphs",
   name_zh="折线统计图",
   description_zh="认识折线统计图，能根据数据画折线图并看出变化趋势",
   evidence_zh=["说出折线图比条形图多表达“变化”", "根据一周气温画折线图", "从图中指出哪天升温最快"],
   assessmentPrompt_zh="给孩子一周的气温数字，问他：用折线图画出来后，哪两天之间变化最大？",
   ageStart=10, ageEnd=12, centrality=0.05,
   prereq=["频数表与统计图（11 岁+）", "条形统计图"], prereq_strength="hard"),

 dict(id=nid("cylcone"), domain="Geometry", type="CONCEPTUAL",
   name="Cylinders and cones",
   name_zh="圆柱与圆锥",
   description_zh="认识圆柱与圆锥的特征，掌握表面积与体积（容积）的计算公式并解决实际问题",
   evidence_zh=["指出圆柱有几个面、圆锥有几个面", "计算一个圆柱水杯的侧面积和容积", "比较等底等高圆柱与圆锥体积的关系"],
   assessmentPrompt_zh="拿一个圆柱形薯片筒，问孩子：如果要给它包一层包装纸（不含上下底），需要算哪个面的面积？",
   ageStart=11, ageEnd=12, centrality=0.07,
   prereq=["圆的周长与面积", "长方体的体积"], prereq_strength="hard"),

 dict(id=nid("scale"), domain="Ratio & Proportion", type="PROCEDURAL",
   name="Scale (map scale) and scaled drawings",
   name_zh="比例尺",
   description_zh="认识比例尺，理解图上距离与实际距离的比，能进行比例尺计算与按比放大缩小绘图",
   evidence_zh=["说出比例尺 1:1000 的含义", "根据比例尺算出图上 2 厘米代表实际多少米", "按 2:1 把一个图形放大画出"],
   assessmentPrompt_zh="对孩子说：地图比例尺写 1:50000，图上 4 厘米相当于实际多少千米？他能换算吗？",
   ageStart=11, ageEnd=12, centrality=0.06,
   prereq=["比的记号与关系", "比例"], prereq_strength="hard"),
]

# 写新节点
new_count = 0
for n in NEW:
    prereq_ids = []
    for kw in n.pop("prereq"):
        pid = find_id(kw)
        if pid: prereq_ids.append(pid)
    strength = n.pop("prereq_strength", "soft")
    node = {
        "id": n["id"],
        "name": n["name"],
        "domain": n["domain"],
        "type": n["type"],
        "description": n["description_zh"],
        "ageStart": n["ageStart"], "ageEnd": n["ageEnd"],
        "centrality": n["centrality"],
        "evidence": n["evidence_zh"],
        "assessmentPrompt": n["assessmentPrompt_zh"].replace("孩子", "{{name}}"),
        "standards": ["中国课标"],
        "inChineseCurriculum": True,
        "curriculumLabel": "人教版·中国小学数学课标",
        "source": "中国课标",
        "name_zh": n["name_zh"],
        "description_zh": n["description_zh"],
        "evidence_zh": n["evidence_zh"],
        "assessmentPrompt_zh": n["assessmentPrompt_zh"],
        "uncertain": False,
        "inDegree": 0, "outDegree": 0,
    }
    topics.append(node)
    by_id[node["id"]] = node
    new_count += 1
    # 补前置边
    for pid in prereq_ids:
        deps["dependencies"].append({
            "topicId": node["id"], "prerequisiteId": pid,
            "strength": strength,
            "reason": f"中国课标前置：{by_id[pid].get('name_zh','')} → {node['name_zh']}"
        })

print(f"[新增] 共添加 {new_count} 个中国课标节点")

# ---------------- 3. 重算计数 ----------------
for t in topics:
    t["inDegree"] = sum(1 for e in deps["dependencies"] if e["topicId"] == t["id"])
    t["outDegree"] = sum(1 for e in deps["dependencies"] if e["prerequisiteId"] == t["id"])

# 更新 domains 计数
dcount = {}
for t in topics:
    dcount[t["domain"]] = dcount.get(t["domain"], 0) + 1
for d in data["domains"]:
    d["count"] = dcount.get(d["domain"], d["count"])

data["topicCount"] = len(topics)
data["edgeCount"] = len(deps["dependencies"])

json.dump(data, open(TOPICS_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(deps, open(DEPS_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"已写回。总节点={len(topics)} 总边={len(deps['dependencies'])}")
print("打标节点中示例 curriculumLabel:", by_id[find_id('读写 100 以内的数')]['curriculumLabel'])
