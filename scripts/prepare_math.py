#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 withmarbleapp/os-taxonomy 全量数据中抽取数学学科子集，
生成干净的中文版数学技能树数据集。

输入:
  data/topics.json        全量微主题
  data/dependencies.json  全量前置依赖边

输出:
  data/math-topics.json   数学主题节点（按领域分组，含统计）
  data/math-dependencies.json  数学内部依赖边

用法:
  python3 scripts/prepare_math.py
"""

import json
import os
from collections import defaultdict, Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

SUBJECT = "Mathematics"


def load(name):
    with open(os.path.join(DATA, name), "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    raw_topics = load("topics.json")
    raw_deps = load("dependencies.json")

    topics_all = raw_topics["topics"]
    deps_all = raw_deps["dependencies"]

    # 1) 筛选数学主题
    math_topics = [t for t in topics_all if t.get("subject") == SUBJECT]
    math_ids = {t["id"] for t in math_topics}
    print(f"[info] 全量主题: {len(topics_all)} | 数学主题: {len(math_topics)}")

    # 2) 领域分布
    domain_counter = Counter(t.get("domain", "未知") for t in math_topics)
    print("\n[info] 数学领域分布:")
    for dom, n in domain_counter.most_common():
        print(f"  - {dom}: {n}")

    # 3) 筛选数学内部依赖边（两端都在数学集合内）
    math_deps = [
        d for d in deps_all
        if d["topicId"] in math_ids and d["prerequisiteId"] in math_ids
    ]
    print(f"\n[info] 数学内部依赖边: {len(math_deps)}")

    # 4) 统计每个节点入度/出度
    indeg = Counter()
    outdeg = Counter()
    for d in math_deps:
        indeg[d["topicId"]] += 1
        outdeg[d["prerequisiteId"]] += 1

    # 5) 精简字段，便于前端直接使用
    clean_topics = []
    for t in math_topics:
        clean_topics.append({
            "id": t["id"],
            "name": t.get("name", ""),
            "domain": t.get("domain", ""),
            "type": t.get("type", ""),
            "description": t.get("description", ""),
            "ageStart": t.get("ageRangeStart"),
            "ageEnd": t.get("ageRangeEnd"),
            "centrality": round(t.get("centrality", 0) or 0, 4),
            "evidence": t.get("evidence", []),
            "assessmentPrompt": t.get("assessmentPrompt", ""),
            "standards": t.get("standards", []),
            "inDegree": indeg[t["id"]],
            "outDegree": outdeg[t["id"]],
        })

    # 按领域排序，领域内按年龄排序，便于阅读
    clean_topics.sort(key=lambda x: (x["domain"], x["ageStart"] or 0, x["name"]))

    clean_deps = [{
        "topicId": d["topicId"],
        "prerequisiteId": d["prerequisiteId"],
        "strength": d.get("strength", ""),
        "reason": d.get("reason", ""),
    } for d in math_deps]

    # 6) 领域列表（含每领域节点数）—供前端下拉筛选
    domains = []
    for dom, n in domain_counter.most_common():
        domains.append({"domain": dom, "count": n})
        # 该领域年龄范围
    domain_age = defaultdict(lambda: [99, 0])
    for t in math_topics:
        a = t.get("ageRangeStart") or 0
        b = t.get("ageRangeEnd") or 0
        domain_age[t.get("domain")][0] = min(domain_age[t.get("domain")][0], a)
        domain_age[t.get("domain")][1] = max(domain_age[t.get("domain")][1], b)
    for d in domains:
        d["ageStart"] = domain_age[d["domain"]][0]
        d["ageEnd"] = domain_age[d["domain"]][1]

    # 7) 写文件
    out_topics = {
        "version": "v1-math",
        "subject": SUBJECT,
        "topicCount": len(clean_topics),
        "edgeCount": len(clean_deps),
        "domains": domains,
        "topics": clean_topics,
    }
    out_deps = {
        "version": "v1-math",
        "subject": SUBJECT,
        "edgeCount": len(clean_deps),
        "dependencies": clean_deps,
    }
    with open(os.path.join(DATA, "math-topics.json"), "w", encoding="utf-8") as f:
        json.dump(out_topics, f, ensure_ascii=False, indent=1)
    with open(os.path.join(DATA, "math-dependencies.json"), "w", encoding="utf-8") as f:
        json.dump(out_deps, f, ensure_ascii=False, indent=1)

    print("\n[done] 已生成:")
    print(f"  data/math-topics.json      ({len(clean_topics)} nodes)")
    print(f"  data/math-dependencies.json ({len(clean_deps)} edges)")


if __name__ == "__main__":
    main()
