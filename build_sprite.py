#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_sprite.py
将 assets/symbols/ 目录下的 702 个 SVG 文件合并为一个 SVG sprite 文件，
并生成配套的 CSS 文件。

输出:
  - assets/mtf-sprite.svg   (SVG sprite, 每个符号用 <symbol id="节点ID" viewBox="0 0 64 64"> 包装)
  - assets/mtf-icons.css    (.mtf-icon 基础类 + 各节点 CSS 类)

用法 (HTML):
  <!-- 1. 内联加载 sprite -->
  <svg style="display:none" aria-hidden="true">
    <!-- 通过 fetch + 注入, 或服务端直接内联 mtf-sprite.svg 的内容 -->
  </svg>
  <!-- 2. 使用图标 -->
  <svg class="mtf-icon"><use href="#mt_yJmvUCCym7"/></svg>
"""

import os
import re
import sys
import json

# ============================================================================
# 路径配置
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYMBOLS_DIR = os.path.join(BASE_DIR, 'assets', 'symbols')
INDEX_FILE = os.path.join(SYMBOLS_DIR, 'index.json')
OUT_SPRITE = os.path.join(BASE_DIR, 'assets', 'mtf-sprite.svg')
OUT_CSS = os.path.join(BASE_DIR, 'assets', 'mtf-icons.css')

VIEWBOX = '0 0 64 64'

# ============================================================================
# 解析辅助
# ============================================================================
# 这些 SVG 是单行、无嵌套 <g> 的简单结构 (参见 generate_symbols.py)，
# 因此使用非贪婪正则提取 <g id="frame">...</g> 与 <g id="symbol">...</g> 的内部内容是安全的。
FRAME_RE = re.compile(r'<g id="frame">(.*?)</g>', re.S)
SYMBOL_RE = re.compile(r'<g id="symbol">(.*?)</g>', re.S)


def extract_groups(svg_text):
    """从 SVG 文本中提取 frame 与 symbol 的内部内容。

    返回 (frame_inner, symbol_inner)，缺失则为 None。
    """
    fm = FRAME_RE.search(svg_text)
    sm = SYMBOL_RE.search(svg_text)
    frame_inner = fm.group(1).strip() if fm else None
    symbol_inner = sm.group(1).strip() if sm else None
    return frame_inner, symbol_inner


def load_index():
    """加载 index.json, 返回 {node_id: record} 映射 (用于在 CSS 中附加可读名称)。"""
    mapping = {}
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            for rec in data.get('records', []):
                mapping[rec.get('id')] = rec
        except Exception as exc:  # noqa: BLE001
            print('  [warn] 读取 index.json 失败: {}'.format(exc))
    return mapping


def build_sprite():
    symbols_dir = SYMBOLS_DIR
    files = sorted(f for f in os.listdir(symbols_dir) if f.lower().endswith('.svg'))
    if not files:
        print('[error] assets/symbols/ 下没有找到 .svg 文件')
        sys.exit(1)

    print('=' * 70)
    print('SVG Sprite 构建')
    print('=' * 70)
    print('输入目录 : {}'.format(symbols_dir))
    print('SVG 文件数: {}'.format(len(files)))

    index_map = load_index()
    print('index.json 记录数: {}'.format(len(index_map)))

    symbol_blocks = []
    css_node_rules = []
    stats = {
        'total': len(files),
        'ok': 0,
        'missing_frame': 0,
        'missing_symbol': 0,
        'missing_both': 0,
    }
    missing_frame_files = []
    missing_symbol_files = []

    for fname in files:
        node_id = os.path.splitext(fname)[0]
        fpath = os.path.join(symbols_dir, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as fh:
                svg_text = fh.read()
        except Exception as exc:  # noqa: BLE001
            print('  [error] 读取 {} 失败: {}'.format(fname, exc))
            continue

        frame_inner, symbol_inner = extract_groups(svg_text)

        has_frame = frame_inner is not None
        has_symbol = symbol_inner is not None
        if not has_frame:
            stats['missing_frame'] += 1
            missing_frame_files.append(fname)
        if not has_symbol:
            stats['missing_symbol'] += 1
            missing_symbol_files.append(fname)
        if not has_frame and not has_symbol:
            stats['missing_both'] += 1
            continue  # 完全无法提取, 跳过

        stats['ok'] += 1

        # 合并 frame + symbol 作为 <symbol> 的内容 (frame 在前, symbol 在后)
        parts = []
        if has_frame:
            parts.append(frame_inner)
        if has_symbol:
            parts.append(symbol_inner)
        inner = '\n    '.join(parts)

        block = (
            '<symbol id="{id}" viewBox="{vb}">\n'
            '    {inner}\n'
            '  </symbol>'
        ).format(id=node_id, vb=VIEWBOX, inner=inner)
        symbol_blocks.append(block)

        # CSS: 为每个节点生成一个 hook 类, 注释中带可读名称
        rec = index_map.get(node_id)
        if rec:
            name_zh = rec.get('name_zh', '')
            name_en = rec.get('name', '')
            comment = '  /* {} | {} */'.format(name_zh, name_en)
        else:
            comment = ''
        css_node_rules.append(
            '.mtf-{nid} {{}}{cmt}'.format(nid=node_id, cmt=comment)
        )

    # 组装 sprite
    sprite = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        'style="display:none" aria-hidden="true">\n'
        '  {symbols}\n'
        '</svg>\n'
    ).format(symbols='\n  '.join(symbol_blocks))

    with open(OUT_SPRITE, 'w', encoding='utf-8') as fh:
        fh.write(sprite)
    sprite_size = os.path.getsize(OUT_SPRITE)

    # 组装 CSS
    css = []
    css.append('/* MTF Icons - SVG Sprite 配套 CSS (自动生成, 勿手动编辑) */')
    css.append('/* 用法: <svg class="mtf-icon"><use href="#节点ID"/></svg> */')
    css.append('')
    css.append('.mtf-icon {')
    css.append('  display: inline-block;')
    css.append('  width: 1em;')
    css.append('  height: 1em;')
    css.append('  fill: none;')
    css.append('  stroke: currentColor;')
    css.append('  stroke-width: 1.5;')
    css.append('  stroke-linecap: round;')
    css.append('  stroke-linejoin: round;')
    css.append('  vertical-align: middle;')
    css.append('}')
    css.append('')
    css.append('/* 各节点 hook 类 (可用作样式覆盖 / 选择器, 渲染仍需 <use href="#节点ID">) */')
    css.extend(css_node_rules)
    css.append('')
    css_text = '\n'.join(css)

    with open(OUT_CSS, 'w', encoding='utf-8') as fh:
        fh.write(css_text)
    css_size = os.path.getsize(OUT_CSS)

    # 统计输出
    print('-' * 70)
    print('解析统计:')
    print('  成功提取 (含 frame 和/或 symbol): {}'.format(stats['ok']))
    print('  缺少 frame : {}'.format(stats['missing_frame']))
    print('  缺少 symbol: {}'.format(stats['missing_symbol']))
    print('  缺少两者  : {} (已跳过)'.format(stats['missing_both']))
    if missing_frame_files:
        print('  缺 frame 的文件 (前 5): {}'.format(missing_frame_files[:5]))
    if missing_symbol_files:
        print('  缺 symbol 的文件 (前 5): {}'.format(missing_symbol_files[:5]))

    print('-' * 70)
    print('输出:')
    print('  sprite: {}'.format(OUT_SPRITE))
    print('    <symbol> 元素数: {}'.format(len(symbol_blocks)))
    print('    文件大小: {} 字节 ({:.2f} KB)'.format(sprite_size, sprite_size / 1024.0))
    print('    大小检查 (< 1MB): {}'.format('PASS' if sprite_size < 1024 * 1024 else 'FAIL'))
    print('  css   : {}'.format(OUT_CSS))
    print('    节点类数: {}'.format(len(css_node_rules)))
    print('    文件大小: {} 字节 ({:.2f} KB)'.format(css_size, css_size / 1024.0))

    # 校验: sprite 中 <symbol> 数量
    symbol_count_in_file = sprite.count('<symbol ')
    print('-' * 70)
    print('校验:')
    print('  sprite 中 <symbol> 数量: {}'.format(symbol_count_in_file))
    expected = stats['total']
    if symbol_count_in_file == expected:
        print('  数量校验 (== {}): PASS'.format(expected))
    else:
        print('  数量校验 (== {}): FAIL (实际 {})'.format(expected, symbol_count_in_file))

    print('=' * 70)
    print('完成。')
    return stats


if __name__ == '__main__':
    build_sprite()
