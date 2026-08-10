#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_symbols.py
为数学天赋星图的 702 个节点批量生成 SVG 矢量符号文件。

数据源: data/math-topics.json
输出:   assets/symbols/{node_id}.svg + assets/symbols/index.json

设计规范:
- viewBox="0 0 64 64"
- 纯轮廓: stroke="currentColor" fill="none" stroke-width="1.5"
          stroke-linecap="round" stroke-linejoin="round"
- 5 种类型外框 + 内部概念符号
- 不包含任何配色方案
"""

import json
import os
import html
import math
from collections import Counter, defaultdict

# ============================================================================
# 路径配置
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data', 'math-topics.json')
OUT_DIR = os.path.join(BASE_DIR, 'assets', 'symbols')


# ============================================================================
# 辅助函数
# ============================================================================
def esc(s):
    """XML 转义"""
    return html.escape(str(s), quote=False)


def txt(ch, size=20, x=32, y=32):
    """生成居中文字符号 (使用 fill 而非 stroke)；字号上限 24 以适配所有外框"""
    size = min(size, 24)
    return ('<text x="{}" y="{}" font-size="{}" text-anchor="middle" '
            'dominant-baseline="central" fill="currentColor" stroke="none" '
            'font-family="Georgia, \'Times New Roman\', serif">{}</text>'
           ).format(x, y, size, esc(ch))


def dot(cx, cy, r=1.7):
    """生成小圆点 (填充)"""
    return ('<circle cx="{}" cy="{}" r="{}" fill="currentColor" '
            'stroke="none"/>').format(cx, cy, r)


def ring(cx, cy, r=2.0):
    """生成小圆环 (描边)"""
    return '<circle cx="{}" cy="{}" r="{}"/>'.format(cx, cy, r)


def txt2(ch1, ch2, size=16):
    """并排两个文字符号（缩小字号避免溢出）"""
    return txt(ch1, size, x=24, y=32) + txt(ch2, size, x=40, y=32)


# ============================================================================
# 类型外框定义 (5 种)
# ============================================================================
def _crystal_frame():
    """八角切面晶体框 (CONCEPTUAL / CONCEPTURAL)"""
    pts = "32,5 51,12 59,32 51,52 32,59 13,52 5,32 13,12"
    return '<polygon points="{}"/>'.format(pts)


def _gear_frame():
    """六边形齿轮框 (PROCEDURAL)"""
    hex_pts = "32,7 53,19 53,45 32,57 11,45 11,19"
    teeth = ''
    for (vx, vy, dx, dy) in [(32, 7, 0, -4), (53, 19, 4, -2),
                              (53, 45, 4, 2), (32, 57, 0, 4),
                              (11, 45, -4, 2), (11, 19, -4, -2)]:
        teeth += '<line x1="{}" y1="{}" x2="{}" y2="{}"/>'.format(
            vx, vy, vx + dx, vy + dy)
    return '<polygon points="{}"/>{}'.format(hex_pts, teeth)


def _holo_frame():
    """方形全息框 - 四角光标 (REPRESENTATIONAL)"""
    return ('<path d="M8 16 L8 8 L16 8"/>'
            '<path d="M48 8 L56 8 L56 16"/>'
            '<path d="M56 48 L56 56 L48 56"/>'
            '<path d="M16 56 L8 56 L8 48"/>')


def _ring_frame():
    """圆环框 (LANGUAGE)"""
    return '<circle cx="32" cy="32" r="27"/><circle cx="32" cy="32" r="23"/>'


def _star_frame():
    """五角星芒框 (META / METACOGNITIVE)"""
    pts = []
    R, r = 27, 11
    for i in range(10):
        rad = R if i % 2 == 0 else r
        ang = math.radians(-90 + i * 36)
        x = 32 + rad * math.cos(ang)
        y = 32 + rad * math.sin(ang)
        pts.append('{:.1f},{:.1f}'.format(x, y))
    return '<polygon points="{}"/>'.format(' '.join(pts))


FRAMES = {
    'CRYSTAL': _crystal_frame(),
    'GEAR': _gear_frame(),
    'HOLO': _holo_frame(),
    'RING': _ring_frame(),
    'STAR': _star_frame(),
}

TYPE_TO_FRAME = {
    'CONCEPTUAL': 'CRYSTAL',
    'CONCEPTURAL': 'CRYSTAL',
    'PROCEDURAL': 'GEAR',
    'REPRESENTATIONAL': 'HOLO',
    'LANGUAGE': 'RING',
    'META': 'STAR',
    'METACOGNITIVE': 'STAR',
}


# ============================================================================
# 概念符号模板
# 每个符号为一小段 SVG 片段, 居中于 (32,32)
# ============================================================================
SYMBOLS = {
    # --- 基础运算符号 (字号 ≤24 以适配所有外框) ---
    'plus': txt('+', 24),
    'minus': txt('\u2212', 26),  # −
    'plus_minus': txt2('+', '\u2212', 16),
    'times': txt('\u00d7', 26),  # ×
    'divide': txt('\u00f7', 24),  # ÷
    'times_divide': txt2('\u00d7', '\u00f7', 16),
    'equals': txt('=', 22),
    'approx': txt('\u2248', 22),  # ≈
    'percent': txt('%', 22),
    'pm': txt('\u00b1', 24),  # ±
    'neq': txt('\u2260', 22),  # ≠
    'lt': txt('<', 26),
    'gt': txt('>', 26),
    'leq': txt('\u2264', 22),  # ≤
    'geq': txt('\u2265', 22),  # ≥
    'identical': txt('\u2261', 22),  # ≡

    # --- 合并 / 拆分 / 凑十 ---
    'combine': ('<circle cx="27" cy="32" r="6"/><circle cx="37" cy="32" r="6"/>'
                '<path d="M32 26 L32 38"/>'),
    'number_bond': ('<circle cx="32" cy="21" r="5"/><circle cx="23" cy="42" r="5"/>'
                    '<circle cx="41" cy="42" r="5"/>'
                    '<path d="M32 26 L25 37 M39 37 L32 26"/>'),
    'split': '<circle cx="32" cy="32" r="11"/><path d="M32 21 L32 43"/>',

    # --- 分数 / 小数 ---
    'fraction': '<circle cx="32" cy="32" r="11"/><path d="M32 21 L32 32 L43 32"/>',
    'half': '<path d="M21 32 A11 11 0 0 1 43 32"/><path d="M21 32 L43 32"/>',
    'quarter': ('<circle cx="32" cy="32" r="11"/>'
                '<path d="M32 21 L32 32 L43 32"/>'),
    'frac_bar': (txt('a', 16, x=29, y=28) +
                 '<path d="M24 32 L40 32"/>' +
                 txt('b', 16, x=29, y=38)),
    'decimal': (txt('0', 20, x=27, y=33) +
                '<circle cx="33" cy="38" r="1.5" fill="currentColor" stroke="none"/>' +
                txt('1', 20, x=38, y=33)),

    # --- 几何形状 ---
    'triangle': '<path d="M32 22 L43 42 L21 42 Z"/>',
    'square_shape': '<rect x="22" y="22" width="20" height="20"/>',
    'rectangle_shape': '<rect x="20" y="27" width="24" height="10"/>',
    'circle_shape': '<circle cx="32" cy="32" r="11"/>',
    'polygon_hex': '<polygon points="32,20 43,26 43,38 32,44 21,38 21,26"/>',
    'parallelogram': '<path d="M24 42 L30 22 L46 22 L40 42 Z"/>',
    'rhombus': '<path d="M32 20 L44 32 L32 44 L20 32 Z"/>',
    'trapezoid': '<path d="M22 42 L28 22 L44 22 L40 42 Z"/>',
    'angle_mark': '<path d="M22 42 L44 42 M22 42 L38 24"/><path d="M22 42 A7 7 0 0 0 28 36"/>',
    'angle_sym': txt('\u2220', 30),  # ∠
    'parallel_sym': txt('\u2225', 30),  # ∥
    'perp_sym': txt('\u22a5', 30),  # ⊥
    'degree': txt('\u00b0', 22),  # °
    'delta': txt('\u0394', 26),  # Δ
    'pi_sym': txt('\u03c0', 28),  # π
    'protractor': ('<path d="M22 42 A10 10 0 0 1 42 42"/>'
                    '<path d="M22 42 L42 42"/><path d="M32 42 L32 34"/>'),
    'compass_tool': ('<path d="M32 22 L24 44 M32 22 L40 44"/>'
                     '<path d="M22 44 L26 44 M38 44 L42 44"/>'
                     '<circle cx="32" cy="24" r="2"/>'),
    'ruler': ('<rect x="20" y="29" width="24" height="6"/>'
              '<path d="M24 29 L24 33 M28 29 L28 31 M32 29 L32 33 M36 29 L36 31 M40 29 L40 33"/>'),

    # --- 对称 / 变换 ---
    'symmetry': '<path d="M32 20 L32 44"/><circle cx="26" cy="32" r="3"/><circle cx="38" cy="32" r="3"/>',
    'axis_symmetry': ('<path d="M32 20 L32 44"/>'
                      '<path d="M24 24 L28 40 L24 40 Z"/><path d="M40 24 L36 40 L40 40 Z"/>'),
    'center_symmetry': ('<path d="M32 20 L44 32 L32 44 L20 32 Z"/>'
                        '<circle cx="32" cy="32" r="2" fill="currentColor" stroke="none"/>'),
    'translate': ('<path d="M20 26 L30 26 L30 38 L20 38 Z"/>'
                  '<path d="M30 32 L44 32"/>'
                  '<path d="M44 32 L40 28 M44 32 L40 36"/>'),
    'rotate': ('<path d="M24 32 A8 8 0 1 1 36 38"/>'
               '<path d="M36 38 L33 36 M36 38 L34 41"/>'),
    'reflect': ('<path d="M32 20 L32 44"/>'
                '<path d="M26 24 L22 40 M38 24 L42 40"/>'),

    # --- 面积 / 周长 / 体积 ---
    'area_grid': '<rect x="22" y="22" width="20" height="20"/><path d="M22 32 L42 32 M32 22 L32 42"/>',
    'perimeter': ('<rect x="24" y="24" width="16" height="16"/>'
                  '<path d="M22 22 L24 24 M42 22 L40 24 M22 42 L24 40 M42 42 L40 40"/>'),
    'cube_3d': ('<path d="M22 26 L36 26 L36 40 L22 40 Z"/>'
                '<path d="M36 26 L44 22 L44 36 L36 40"/>'
                '<path d="M22 26 L30 22 L44 22"/>'),
    'surface_area': ('<path d="M22 26 L36 26 L36 40 L22 40 Z"/>'
                     '<path d="M36 26 L44 22 L44 36 L36 40"/>'
                     '<path d="M22 26 L30 22 L44 22"/>'
                     '<path d="M22 33 L36 33 M36 33 L44 29"/>'),
    'sphere': '<circle cx="32" cy="32" r="11"/><ellipse cx="32" cy="32" rx="11" ry="4"/>',
    'cylinder': ('<ellipse cx="32" cy="24" rx="9" ry="3"/>'
                 '<path d="M23 24 L23 40"/><path d="M41 24 L41 40"/>'
                 '<path d="M23 40 A9 3 0 0 0 41 40"/>'),
    'cone': ('<path d="M22 42 L32 22 L42 42"/>'
             '<path d="M22 42 A10 3 0 0 0 42 42"/>'),
    'cross_section': ('<rect x="22" y="30" width="20" height="8"/>'
                      '<path d="M22 24 L22 44 M42 24 L42 44"/>'),
    'three_views': ('<rect x="22" y="22" width="8" height="8"/>'
                    '<rect x="32" y="22" width="8" height="8"/>'
                    '<rect x="22" y="32" width="8" height="8"/>'),
    'point_line_plane': (dot(25, 24) +
                         '<path d="M28 30 L42 38"/>'
                         '<path d="M26 40 L44 40 L46 36 L28 36 Z"/>'),
    'polyhedron': ('<path d="M22 24 L36 24 L36 38 L22 38 Z"/>'
                   '<path d="M36 24 L44 20 L44 34 L36 38"/>'),
    'net': ('<path d="M22 28 L32 28 L32 38 L22 38 Z"/>'
            '<path d="M32 28 L42 28 L42 38 L32 38 Z"/>'
            '<path d="M22 28 L22 38"/>'),
    'similar': ('<path d="M22 44 L32 22 L42 44 Z"/>'
                '<path d="M28 44 L32 34 L36 44 Z"/>'),
    'congruent': ('<path d="M22 42 L32 22 L42 42 Z"/>'
                  '<path d="M22 42 L32 32 L42 42"/>'
                  '<path d="M30 30 L34 30 L34 34 L30 34 Z"/>'),
    'right_triangle': ('<path d="M22 42 L42 42 L22 20 Z"/>'
                       '<path d="M22 36 L26 36 L26 42"/>'),
    'pythagoras': ('<path d="M20 42 L44 42 L20 20 Z"/>'
                   '<path d="M20 36 L24 36 L24 42"/>'
                   '<rect x="24" y="42" width="0" height="0"/>'
                   '<path d="M20 42 L20 44"/>'),

    # --- 坐标 / 坐标系 ---
    'axes': ('<path d="M22 22 L22 44 L44 44"/>'
             '<path d="M22 22 L19 25 M22 22 L25 25"/>'
             '<path d="M44 44 L41 41 M44 44 L41 47"/>'),
    'coordinate': '<path d="M22 22 L22 44 L44 44"/><path d="M30 36 L36 28"/>',
    'position': (dot(24, 26) + '<path d="M24 26 L40 38"/>'),
    'direction': ('<path d="M32 22 L32 42"/>'
                  '<path d="M32 22 L28 26 M32 22 L36 26"/>'),
    'cardinal': ('<path d="M32 20 L32 44 M20 32 L44 32"/>'
                 '<path d="M32 20 L28 24 M32 20 L36 24"/>'),
    'plot_point': '<path d="M22 22 L22 44 L44 44"/>' + dot(36, 30, 2.2),

    # --- 曲线 ---
    'parabola': '<path d="M22 44 Q32 16 42 44"/>',
    'hyperbola': '<path d="M22 22 Q32 30 24 42"/><path d="M42 22 Q32 30 40 42"/>',
    'ellipse_shape': '<ellipse cx="32" cy="32" rx="13" ry="7"/>',
    'line_eq': '<path d="M22 44 L42 20"/>',
    'slope': ('<path d="M22 42 L42 22"/>'
              '<path d="M42 22 L36 22 M42 22 L42 28"/>'),
    'curve_general': '<path d="M22 42 Q32 20 42 42"/>',

    # --- 度量 ---
    'scale_balance': ('<path d="M22 42 L42 42 M32 42 L32 24"/>'
                      '<path d="M24 24 L32 18 L40 24"/>'
                      '<path d="M20 42 L26 42 M38 42 L44 42"/>'),
    'container': '<path d="M24 22 L40 22 L38 44 L26 44 Z"/><path d="M26 32 L38 32"/>',
    'clock': ('<circle cx="32" cy="32" r="11"/>'
              '<path d="M32 32 L32 25 M32 32 L37 35"/>'
              + ring(32, 21) + ring(43, 32) + ring(32, 43) + ring(21, 32)),
    'thermometer': ('<circle cx="32" cy="42" r="3"/>'
                    '<path d="M32 42 L32 22"/>'
                    '<circle cx="32" cy="42" r="5"/>'),
    'coin': '<circle cx="32" cy="32" r="9"/><circle cx="32" cy="32" r="6"/>',
    'money': (txt('$', 22, x=28, y=33) + '<path d="M28 38 L36 38"/>'),
    'calendar': ('<rect x="22" y="24" width="20" height="18"/>'
                 '<path d="M22 30 L42 30 M30 24 L30 20 M36 24 L36 20"/>'),
    'convert': (txt('1', 16, x=26, y=30) +
                '<path d="M22 32 L42 32"/>'
                '<path d="M38 28 L42 32 L38 36"/>' +
                txt('100', 14, x=34, y=40)),

    # --- 数据统计 ---
    'bar_chart': ('<path d="M22 42 L42 42"/>'
                  '<rect x="24" y="34" width="4" height="8"/>'
                  '<rect x="30" y="28" width="4" height="14"/>'
                  '<rect x="36" y="32" width="4" height="10"/>'),
    'histogram': ('<path d="M22 42 L42 42"/>'
                  '<rect x="22" y="34" width="6" height="8"/>'
                  '<rect x="28" y="28" width="6" height="14"/>'
                  '<rect x="34" y="30" width="6" height="12"/>'),
    'pie_chart': ('<circle cx="32" cy="32" r="11"/>'
                  '<path d="M32 32 L32 21 A11 11 0 0 1 42 36 Z"/>'),
    'scatter': (dot(26, 38) + dot(30, 32) + dot(34, 28) +
                dot(38, 30) + dot(40, 26) + dot(28, 34)),
    'line_graph': '<path d="M22 42 L30 30 L36 36 L42 24"/>',
    'pictogram': (dot(26, 28) + dot(32, 28) + dot(26, 36) + '<path d="M22 42 L42 42"/>'),
    'tally': ('<path d="M24 20 L24 44 M28 20 L28 44 M32 20 L32 44 M36 20 L36 44"/>'
              '<path d="M22 26 L40 24"/>'),
    'table': ('<rect x="22" y="24" width="20" height="16"/>'
              '<path d="M22 32 L42 32 M32 24 L32 40"/>'),
    'mean': ('<path d="M22 26 L42 26"/><path d="M22 30 L22 22 M42 30 L42 22"/>'
             '<path d="M22 42 L42 42"/>'),
    'median': ('<path d="M22 42 L42 42"/>' + dot(32, 42, 2.5) +
               '<path d="M32 38 L32 24"/>'),
    'mode': (dot(26, 42) + dot(30, 42) + dot(34, 42) + dot(38, 42) +
             dot(30, 32) + dot(34, 32)),
    'variance': ('<path d="M22 42 L42 42"/><path d="M26 30 L26 38 M32 24 L32 38 M38 28 L38 38"/>'
                 '<path d="M26 30 L38 28"/>'),
    'sort': ('<circle cx="26" cy="28" r="2.5"/><circle cx="26" cy="38" r="2.5"/>'
             '<circle cx="38" cy="28" r="2.5"/><circle cx="38" cy="38" r="2.5"/>'
             '<path d="M22 32 L20 32 M44 32 L42 32"/>'),
    'distribution': ('<path d="M22 42 Q32 22 42 42"/>'
                      + dot(26, 38) + dot(30, 32) + dot(34, 30) + dot(38, 34)),
    'regression': ('<path d="M22 42 L42 22"/>'
                    + dot(26, 38) + dot(30, 34) + dot(34, 32) + dot(38, 28)),
    'survey': ('<rect x="22" y="26" width="6" height="6"/>'
               '<path d="M30 28 L42 28 M30 34 L42 34 M30 40 L38 40"/>'),
    'venn': ('<circle cx="27" cy="32" r="8"/><circle cx="37" cy="32" r="8"/>'),

    # --- 代数 ---
    'variable_x': txt('x', 26),
    'formula': txt('f', 24),
    'expression': (txt('a', 18, x=26, y=33) +
                   txt('+', 20, x=32, y=33) +
                   txt('b', 18, x=38, y=33)),
    'listing': (dot(24, 26) + dot(32, 26) + dot(40, 26) +
                dot(24, 38) + dot(32, 38) + dot(40, 38)),
    'order_ops': ('<path d="M22 26 L30 26 M34 26 L42 26"/>'
                  '<path d="M22 38 L42 38"/>'
                  '<path d="M30 26 L30 38"/>'),
    'inequality_region': ('<path d="M22 42 L42 24"/>'
                           '<path d="M22 42 L42 42 L42 24"/>'),

    # --- 高等数学符号 ---
    'sigma': txt('\u03a3', 28),  # Σ
    'integral': txt('\u222b', 32),  # ∫
    'indefinite_integral': txt('\u222b', 34),
    'definite_integral': (txt('\u222b', 28, x=28, y=32) +
                          txt('a', 11, x=36, y=22) +
                          txt('b', 11, x=36, y=42)),
    'partial': txt('\u2202', 28),  # ∂
    'infinity': txt('\u221e', 28),  # ∞
    'sqrt': txt('\u221a', 30),  # √
    'power': (txt('a', 20, x=28, y=35) + txt('n', 13, x=37, y=27)),
    'scientific': (txt('a', 16, x=24, y=33) +
                  txt('\u00d710', 13, x=34, y=33) +
                  txt('n', 11, x=42, y=27)),
    'real_num': txt('\u211d', 26),  # ℝ
    'integer_num': txt('\u2124', 26),  # ℤ
    'natural_num': txt('\u2115', 26),  # ℕ
    'rational_num': txt('\u211a', 26),  # ℚ
    'set_sym': txt('\u2208', 26),  # ∈
    'subset': txt('\u2282', 26),  # ⊂
    'union': txt('\u222a', 28),  # ∪
    'intersection': txt('\u2229', 28),  # ∩
    'forall': txt('\u2200', 24),  # ∀
    'exists': txt('\u2203', 24),  # ∃
    'empty_set': txt('\u2205', 26),  # ∅
    'propto': txt('\u221d', 26),  # ∝
    'nabla': txt('\u2207', 28),  # ∇
    'therefore': txt('\u2234', 26),  # ∴
    'because': txt('\u2235', 26),  # ∵
    'arrow_right': txt('\u2192', 30),  # →
    'arrow_bidir': txt('\u2194', 26),  # ↔

    # --- 函数 ---
    'function_fx': (txt('f', 22, x=27, y=30) +
                    txt('(x)', 16, x=37, y=35)),
    'linear_fn': '<path d="M22 44 L42 20"/>',
    'quadratic_fn': '<path d="M22 44 Q32 16 42 44"/>',
    'inverse_fn': '<path d="M22 22 Q30 22 32 32 Q34 42 42 42"/>',
    'exponential_fn': '<path d="M22 42 Q40 42 42 20"/>',
    'log_fn': '<path d="M22 20 Q22 42 42 42"/>',
    'power_fn': ('<path d="M22 42 L42 22"/>'
                 '<path d="M22 42 L22 22"/>'),
    'mapping': ('<circle cx="24" cy="27" r="2"/><circle cx="24" cy="37" r="2"/>'
                '<circle cx="40" cy="32" r="2"/>'
                '<path d="M26 27 L38 31 M26 37 L38 33"/>'),
    'monotonic': '<path d="M22 42 L30 32 L42 22"/>',
    'odd_even_fn': '<path d="M22 32 Q27 22 32 32 T42 32"/>',
    'periodic': '<path d="M20 32 Q24 24 28 32 Q32 40 36 32 Q40 24 44 32"/>',
    'domain_range': ('<path d="M22 28 L42 28 M22 36 L42 36"/>'
                     '<path d="M22 28 L22 36 M42 28 L42 36"/>'),

    # --- 微积分 ---
    'limit': txt('\u2192', 30),
    'limit_inf': (txt('x\u2192\u221e', 14, x=30, y=27) +
                  txt('L', 18, x=32, y=40)),
    'derivative': (txt('dy', 15, x=28, y=27) +
                   '<path d="M24 32 L40 32"/>' +
                   txt('dx', 15, x=28, y=39)),
    'tangent_curve': ('<path d="M20 44 Q32 18 44 44"/>'
                      '<path d="M24 40 L40 26"/>'),
    'extrema': ('<path d="M22 40 L32 24 L42 40"/>'
                + dot(32, 24, 2.5)),
    'continuity': '<path d="M22 32 Q32 28 42 32"/>',
    'differential': txt('\u2202', 28),  # ∂

    # --- 向量 ---
    'vector_arrow': ('<path d="M22 42 L40 24"/>'
                     '<path d="M40 24 L34 24 M40 24 L40 30"/>'),
    'vector_3d': ('<path d="M22 42 L34 28"/>'
                  '<path d="M22 42 L40 42"/>'
                  '<path d="M22 42 L22 24"/>'
                  '<path d="M34 28 L40 24"/>'),
    'dot_product': ('<path d="M22 42 L42 22"/>'
                    + dot(32, 32, 2.5)),
    'vector_basis': ('<path d="M32 42 L22 30"/>'
                     '<path d="M32 42 L42 30"/>'),

    # --- 三角学 ---
    'sine': '<path d="M22 32 Q27 22 32 32 T42 32"/>',
    'cosine': '<path d="M22 22 Q27 42 32 32 T42 32"/>',
    'tangent_wave': ('<path d="M22 42 Q32 42 32 32 Q32 22 42 22"/>'),
    'unit_circle': ('<circle cx="32" cy="32" r="11"/>'
                    '<path d="M32 32 L43 32"/><path d="M32 32 L38 24"/>'),
    'radian': ('<circle cx="32" cy="32" r="10"/>'
               '<path d="M32 32 L42 32 A10 10 0 0 0 38 24"/>'),
    'special_angles': ('<circle cx="32" cy="32" r="10"/>'
                       '<path d="M32 32 L42 32 M32 32 L37 24 M32 32 L32 22"/>'),
    'acute_angle': ('<path d="M22 42 L44 42 M22 42 L40 28"/>'
                    '<path d="M22 42 A6 6 0 0 0 26 38"/>'),
    'angle_relation': ('<path d="M22 42 L42 42 M32 24 L32 42"/>'
                       '<path d="M32 34 L38 34 M32 30 L26 30"/>'),

    # --- 复数 ---
    'complex_plane': ('<path d="M22 32 L42 32 M32 22 L32 42"/>'
                      + dot(38, 26, 2.5)),
    'imaginary_i': txt('i', 28),
    'polar_form': ('<circle cx="32" cy="32" r="3"/>'
                   '<path d="M32 32 L42 26"/>'
                   '<path d="M42 32 A6 6 0 0 1 36 26"/>'),

    # --- 组合数学 ---
    'permutation': (dot(24, 32) + dot(32, 32) + dot(40, 32) +
                    '<path d="M24 28 L40 28"/>'
                    '<path d="M24 36 L40 36"/>'),
    'combination': ('<circle cx="32" cy="32" r="11"/>'
                    + dot(28, 32) + dot(36, 32) + dot(32, 28) + dot(32, 36)),
    'binomial': (dot(32, 22) + dot(28, 30) + dot(36, 30) +
                 dot(24, 38) + dot(32, 38) + dot(40, 38) + dot(32, 42)),
    'counting_principle': ('<path d="M22 30 L32 22 L42 30"/>'
                            '<path d="M22 30 L22 42 M32 22 L32 42 M42 30 L42 42"/>'),

    # --- 数列 ---
    'sequence_dots': (dot(24, 42) + dot(30, 36) + dot(36, 30) + dot(42, 24)),
    'arithmetic_seq': (dot(24, 40) + dot(30, 36) + dot(36, 32) + dot(42, 28) +
                       '<path d="M24 40 L42 28"/>'),
    'geometric_seq': (dot(24, 40) + dot(28, 36) + dot(34, 30) + dot(42, 22) +
                      '<path d="M24 40 L42 22"/>'),
    'general_term': (txt('a', 16, x=28, y=28) +
                     '<path d="M25 32 L39 32"/>' +
                     txt('n', 16, x=28, y=38)),
    'sum_series': (txt('\u03a3', 24, x=28, y=30) + txt('n', 13, x=38, y=38)),
    'induction': (dot(24, 42) +
                  '<path d="M24 42 L30 36 L36 30 L42 24"/>'
                  '<path d="M42 24 L38 24 M42 24 L42 28"/>'),
    'recurrence': (dot(24, 32) + dot(32, 32) + dot(40, 32) +
                   '<path d="M26 30 L30 30 M34 30 L38 30"/>'
                   '<path d="M30 30 L28 26 M34 30 L36 26"/>'),
    'spiral': '<path d="M32 32 Q36 32 36 28 Q36 24 30 24 Q22 24 22 34 Q22 44 34 44"/>',

    # --- 方程与不等式 ---
    'linear_eq': '<path d="M22 44 L42 20"/>',
    'system_eq': '<path d="M22 26 L42 26 M22 38 L42 38"/>',
    'elimination': ('<path d="M22 28 L42 28 M22 36 L42 36"/>'
                    '<path d="M32 28 L32 36"/>'
                    '<path d="M30 32 L34 32"/>'),
    'quadratic_eq': '<path d="M22 44 Q32 16 42 44"/>',
    'complete_square': ('<rect x="24" y="28" width="8" height="8"/>'
                        '<path d="M32 32 L40 24"/>'
                        '<rect x="36" y="20" width="4" height="4"/>'),
    'quadratic_formula': (txt('x=', 14, x=26, y=27) +
                          txt('\u00b1', 18, x=32, y=28) +
                          txt('\u221a', 16, x=36, y=33) +
                          '<path d="M40 30 L42 30"/>'),
    'discriminant': (txt('\u0394', 22, x=28, y=28) +
                     txt('=', 18, x=32, y=28) +
                     txt('b\u00b2\u22124ac', 11, x=32, y=39)),
    'vieta': (txt('x\u2081+x\u2082', 13, x=28, y=27) +
              '<path d="M22 31 L42 31"/>' +
              txt('= ', 12, x=28, y=39) + txt('\u2212b/a', 12, x=35, y=39)),
    'inequality': txt2('<', '>', 22),
    'inequality_system': ('<path d="M22 32 L28 32 M36 32 L42 32"/>'
                          '<path d="M28 32 L30 26 M36 32 L38 26"/>'
                          '<path d="M28 38 L30 32 M36 38 L38 32"/>'),
    'equation_property': (txt('a=b', 14, x=32, y=28) +
                          '<path d="M22 32 L42 32"/>' +
                          txt('a+c=b+c', 11, x=32, y=40)),
    'interval': ('<path d="M22 32 L42 32"/>' + dot(26, 32, 2.5) + dot(38, 32, 2.5)),
    'matrix': ('<path d="M24 22 L22 22 L22 42 L24 42"/>'
               '<path d="M40 22 L42 22 L42 42 L40 42"/>'
               '<path d="M27 28 L37 28 M27 36 L37 36"/>'),

    # --- 数学思维 (META) ---
    'question': txt('?', 28),
    'lightbulb': ('<circle cx="32" cy="28" r="8"/>'
                  '<path d="M28 36 L36 36 M29 40 L35 40"/>'),
    'pattern': (dot(24, 32) + dot(32, 32) + dot(40, 32) +
                '<path d="M24 32 L40 32"/>'),
    'brain': ('<path d="M27 24 Q20 24 20 32 Q20 40 27 40 Q32 40 32 32 Q32 24 27 24"/>'
              '<path d="M37 24 Q44 24 44 32 Q44 40 37 40 Q32 40 32 32 Q32 24 37 24"/>'),
    'logic': txt('\u2234', 26),  # ∴
    'checkmark': '<path d="M22 32 L30 40 L42 24"/>',
    'strategy': '<path d="M22 26 L42 26 L32 42 Z"/>',
    'reasoning': txt('\u2235', 26),  # ∵
    'proof': txt('\u2234', 26),
    'modeling': ('<rect x="24" y="30" width="8" height="8"/>'
                 '<path d="M32 34 L42 24"/>'),
    'connection': ('<circle cx="24" cy="32" r="3"/><circle cx="40" cy="32" r="3"/>'
                   '<path d="M27 32 L37 32"/>'),
    'representation': ('<rect x="22" y="24" width="8" height="8"/>'
                        '<path d="M30 28 L40 28 L40 38"/>'),
    'vocab': txt('Aa', 22),
    'method': '<path d="M22 24 L22 40 L30 40 M30 24 L30 40 L42 40"/>',
    'efficient': ('<path d="M22 42 L42 22"/><path d="M22 32 L32 22"/>'),
    'multi_step': ('<path d="M22 42 L26 36 L30 30 L34 24 L42 20"/>'
                   + dot(22, 42) + dot(26, 36) + dot(30, 30) + dot(34, 24) + dot(42, 20)),
    'precision': '<circle cx="32" cy="32" r="8"/><circle cx="32" cy="32" r="2" fill="currentColor" stroke="none"/><path d="M32 20 L32 18 M32 46 L32 44 M20 32 L18 32 M46 32 L44 32"/>',
    'tool': ('<path d="M24 24 L24 40 L40 40"/>'
             '<path d="M24 24 L40 24 L40 32"/>'),
    'optimization': ('<path d="M22 42 L32 22 L42 42"/>'
                     + dot(32, 22, 2.5)),
    'tree_planting': (dot(24, 42) + dot(32, 42) + dot(40, 42) +
                      '<path d="M22 42 L42 42"/>'
                      '<path d="M24 42 L24 32 M32 42 L32 32 M40 42 L40 32"/>'),
    'structure': '<path d="M22 24 L42 24 L42 40 L22 40 Z M22 32 L42 32 M32 24 L32 40"/>',
    'generalise': ('<path d="M22 42 L32 26 L42 18"/>'
                   + dot(22, 42) + dot(32, 26) + dot(42, 18)),
    'equivalence': (txt('a\u2261b', 16)),
    'number_line': ('<path d="M20 32 L44 32"/>'
                    '<path d="M24 30 L24 34 M32 30 L32 34 M40 30 L40 34"/>'),
    'order_operations': (txt('(', 22, x=27, y=33) + txt(')', 22, x=37, y=33) +
                         txt('+', 18, x=32, y=22)),
    'real_world': ('<circle cx="32" cy="32" r="10"/>'
                   '<path d="M32 22 L32 26 M32 38 L32 42 M22 32 L26 32 M38 32 L42 32"/>'),
    'communication': txt('\u2192', 28),
    'sense_making': (txt('?', 20, x=26, y=33) + txt('!', 20, x=38, y=33)),
    'argument': ('<path d="M22 42 L32 22 L42 42 Z"/>'
                 '<path d="M32 22 L32 42"/>'),
    'tools_choose': ('<circle cx="26" cy="32" r="4"/><circle cx="40" cy="32" r="4"/>'
                     '<path d="M30 32 L36 32"/>'),
    'compound_unit': (txt('km', 14, x=28, y=28) + txt('/', 16, x=32, y=33) + txt('h', 14, x=36, y=40)),
    'scale_sym': (txt('1:', 18, x=28, y=27) + txt('n', 16, x=34, y=39)),
    'ratio_sym': (txt('a', 18, x=28, y=33) + txt(':', 18, x=32, y=33) + txt('b', 18, x=37, y=33)),
    'proportion': (txt('a/b=c/d', 12)),
    'similar_shapes': ('<path d="M22 42 L32 22 L42 42 Z"/>'
                       '<path d="M28 42 L32 34 L36 42 Z"/>'),
    'compound_units': (txt('km/h', 12)),
    'decimal_place': (txt('0.0', 16, x=32, y=33)),
    'estimation': txt('\u2248', 28),
    'frequency': (dot(24, 42) + dot(28, 36) + dot(32, 28) + dot(36, 24) +
                  '<path d="M22 42 L42 42"/>'),
    'normal_dist': '<path d="M22 42 Q28 42 32 24 Q36 42 42 42"/>',
    'binomial_dist': (dot(24, 40) + dot(28, 36) + dot(32, 24) + dot(36, 36) + dot(40, 40) +
                      '<path d="M22 42 L42 42"/>'),
    'expectation': (txt('E', 20, x=28, y=28) + txt('(X)', 16, x=35, y=33)),
    'conditional_prob': (txt('P', 18, x=26, y=28) + txt('(A|B)', 14, x=34, y=33)),
    'independence': (txt('A\u22a5B', 16)),
    'bayes': (txt('P(A|B)', 14)),
    'tree_diagram': (dot(32, 22) + dot(24, 38) + dot(40, 38) +
                     '<path d="M32 24 L25 36 M32 24 L39 36"/>'),
    'likely': ('<path d="M22 32 A10 10 0 0 1 42 32"/><path d="M22 32 L42 32"/>'),
    'experiment': ('<path d="M24 22 L24 42"/>'
                   '<path d="M24 32 L40 32 L40 26"/>'
                   + dot(40, 24)),
    'sample': (dot(26, 32) + dot(32, 32) + dot(38, 32) +
               '<path d="M22 24 L42 24 L42 40 L22 40 Z"/>'),
    'survey_sym': ('<rect x="22" y="26" width="6" height="6"/>'
                   '<path d="M30 28 L42 28 M30 34 L42 34 M30 40 L38 40"/>'),
    'correlation': ('<path d="M22 42 L42 22"/>'
                    + dot(26, 38) + dot(30, 34) + dot(34, 30) + dot(38, 26)),
    'compound_chart': ('<rect x="22" y="34" width="4" height="8"/>'
                       '<rect x="28" y="28" width="4" height="14"/>'
                       '<path d="M36 42 L40 24"/>'
                       '<path d="M22 42 L42 42"/>'),
    'theoretical': (txt('P=', 16, x=28, y=33) + txt('1/n', 14, x=37, y=33)),
    'complementary': ('<path d="M22 32 A10 10 0 0 1 42 32"/>'
                      '<path d="M22 32 A10 10 0 0 0 42 32"/>'),
    'scale_prob': ('<path d="M20 32 L44 32"/>'
                   '<path d="M20 28 L20 36 M44 28 L44 36"/>'
                   + dot(34, 32, 2) + dot(30, 32, 2)),

    # --- 度量补充 ---
    'length_measure': ('<path d="M20 32 L44 32"/>'
                       '<path d="M20 28 L20 36 M44 28 L44 36"/>'
                       '<path d="M28 30 L28 34 M36 30 L36 34"/>'),
    'mass_weight': ('<path d="M22 42 L42 42 M32 42 L32 24"/>'
                    '<path d="M24 24 L32 18 L40 24"/>'),
    'time_duration': ('<circle cx="32" cy="32" r="11"/>'
                      '<path d="M32 32 L32 26"/>'
                      '<path d="M22 32 A10 10 0 0 1 42 32"/>'),
    'calendar_sym': ('<rect x="22" y="24" width="20" height="18"/>'
                     '<path d="M22 30 L42 30 M30 24 L30 20 M36 24 L36 20"/>'),
    'unit_convert': (txt('1', 16, x=26, y=30) +
                     '<path d="M22 32 L42 32"/>'
                     '<path d="M38 28 L42 32 L38 36"/>' +
                     txt('n', 14, x=34, y=40)),
    'compare_measure': (txt('>', 22, x=32, y=33)),
    'capacity_vol': ('<path d="M24 22 L40 22 L38 44 L26 44 Z"/>'
                     '<path d="M26 33 L38 33"/>'),
    'coin_value': '<circle cx="32" cy="32" r="9"/><circle cx="32" cy="32" r="6"/>',
    'telling_time': ('<circle cx="32" cy="32" r="11"/>'
                     '<path d="M32 32 L32 25 M32 32 L37 35"/>'),
    'time_units': (txt('h:m', 16, x=32, y=33)),
    'perimeter_measure': ('<rect x="24" y="24" width="16" height="16"/>'
                          '<path d="M22 22 L24 24 M42 22 L40 24 M22 42 L24 40 M42 42 L40 40"/>'),
    'area_measure': '<rect x="22" y="22" width="20" height="20"/><path d="M22 32 L42 32 M32 22 L32 42"/>',
    'volume_measure': ('<path d="M22 26 L36 26 L36 40 L22 40 Z"/>'
                       '<path d="M36 26 L44 22 L44 36 L36 40"/>'
                       '<path d="M22 26 L30 22 L44 22"/>'),
    'measurement_general': ('<path d="M20 32 L44 32"/>'
                            '<path d="M24 28 L24 36 M40 28 L40 36"/>'),
    'estimating': txt('\u2248', 28),
    'compound_shape': ('<path d="M22 30 L32 30 L32 42 L22 42 Z"/>'
                       '<path d="M32 30 L42 30 L42 42 L32 42"/>'),
    'line_plot': ('<path d="M22 38 L42 38"/>'
                  + dot(26, 38) + dot(30, 34) + dot(34, 38) + dot(38, 30)),
    'unit_cubes': ('<path d="M22 26 L36 26 L36 40 L22 40 Z"/>'
                   '<path d="M36 26 L44 22 L44 36 L36 40"/>'
                   '<path d="M22 26 L30 22 L44 22"/>'
                   '<path d="M28 32 L36 32"/>'),

    # --- 代数补充 ---
    'algebra_sym': (txt('x', 20, x=27, y=30) + txt('+1', 16, x=36, y=35)),
    'algebra_notation': (txt('x', 22, x=28, y=33) + txt('=', 20, x=33, y=33) + txt('?', 20, x=38, y=33)),
    'algebra_transform': ('<path d="M22 28 L36 28"/>'
                          '<path d="M32 36 L42 36"/>'
                          '<path d="M36 28 L40 24 M36 28 L40 32"/>'),
    'formula_use': (txt('A=', 16, x=28, y=33) + txt('b\u00d7h', 14, x=36, y=33)),
    'pattern_rel': (dot(24, 40) + dot(30, 34) + dot(36, 28) + dot(42, 22) +
                    '<path d="M24 40 L42 22"/>'),

    # --- 图形补充 ---
    'shape_general': '<polygon points="32,20 44,28 40,42 24,42 20,28"/>',
    'flat_solid': ('<rect x="22" y="34" width="14" height="8"/>'
                   '<path d="M36 34 L44 28 L44 36 L36 42"/>'),
    'faces_3d': ('<path d="M22 26 L36 26 L36 40 L22 40 Z"/>'
                 '<path d="M36 26 L44 22 L44 36 L36 40"/>'
                 '<path d="M22 26 L30 22 L44 22"/>'),
    'edge_vertex_face': (dot(24, 24) + dot(40, 24) + dot(24, 40) + dot(40, 40) +
                         '<path d="M24 24 L40 24 L40 40 L24 40 Z M24 24 L24 40 M40 24 L40 40"/>'),
    'sorting_shapes': ('<polygon points="24,24 30,24 27,30"/>'
                       '<circle cx="38" cy="27" r="3"/>'
                       '<path d="M24 38 L40 38"/>'),
    'turn_direction': ('<path d="M32 24 A8 8 0 1 1 24 32"/>'
                       '<path d="M24 32 L20 28 M24 32 L20 36"/>'),
    'right_angle': ('<path d="M22 42 L42 42 L22 22 Z"/>'
                    '<path d="M22 36 L26 36 L26 42"/>'),
    'angle_type': ('<path d="M22 42 L44 42 M22 42 L40 30"/>'
                   '<path d="M22 42 A8 8 0 0 0 28 36"/>'),
    'classifying': ('<polygon points="24,24 30,24 27,30"/>'
                    '<rect x="36" y="24" width="6" height="6"/>'
                    '<circle cx="27" cy="38" r="3"/>'
                    '<path d="M22 20 L22 44 M20 32 L44 32"/>'),
    'polygon_general': '<polygon points="32,20 44,28 40,42 24,42 20,28"/>',
    'regular_polygon': '<polygon points="32,20 42,26 42,38 32,44 22,38 22,26"/>',
    'angle_sum': ('<path d="M32 22 L44 42 L20 42 Z"/>'
                  '<path d="M32 22 L36 34 M32 22 L28 34"/>'),
    'circle_parts': ('<circle cx="32" cy="32" r="11"/>'
                     '<path d="M32 21 L32 32 M32 32 L43 32"/>'
                     '<path d="M32 32 L32 43"/>'),
    'coordinate_transform': ('<path d="M22 22 L22 44 L44 44"/>'
                             '<path d="M24 40 L32 28 M32 28 L40 36"/>'),
    'congruence': ('<path d="M22 42 L32 22 L42 42 Z"/>'
                   '<path d="M22 42 L32 32 L42 42"/>'
                   '<path d="M30 30 L34 30 L34 34 L30 34 Z"/>'),
    'similar_figures': ('<path d="M22 44 L32 22 L42 44 Z"/>'
                        '<path d="M28 44 L32 34 L36 44 Z"/>'),
    'circumference_area': ('<circle cx="32" cy="32" r="10"/>'
                           '<path d="M32 22 L32 32 L42 32"/>'),
    'compass_construction': ('<path d="M32 22 L24 44 M32 22 L40 44"/>'
                             '<path d="M22 44 L26 44 M38 44 L42 44"/>'
                             '<circle cx="32" cy="24" r="2"/>'),
    'line_symmetry': '<path d="M32 20 L32 44"/><path d="M26 24 L22 40 M38 24 L42 40"/>',
    'arc_sector': ('<circle cx="32" cy="32" r="10"/>'
                   '<path d="M32 32 L32 22 A10 10 0 0 1 42 32 Z"/>'),
    'tangent_line': ('<circle cx="32" cy="36" r="8"/>'
                     '<path d="M20 24 L44 24"/>'),
    'position_relation': (dot(24, 26) + '<path d="M24 26 L40 40"/>'
                         '<path d="M22 22 L22 44 L44 44"/>'),
    'distance': ('<path d="M22 32 L42 32"/>'
                 '<path d="M22 28 L22 36 M42 28 L42 36"/>'),
    'space_angle': ('<path d="M22 42 L42 42 M22 42 L22 22 M22 42 L40 28"/>'
                    '<path d="M22 42 A6 6 0 0 0 26 36"/>'),
    'plane_lines': '<path d="M22 22 L42 42 M42 22 L22 42"/>',
    'point_relation': (dot(24, 24) + dot(40, 40) + '<path d="M24 24 L40 40"/>'),
    'parametric': (txt('x(t)', 14, x=28, y=28) +
                   '<path d="M22 32 L42 32"/>' +
                   txt('y(t)', 14, x=28, y=40)),
    'polar_coord': ('<circle cx="32" cy="32" r="10"/>'
                    '<path d="M32 32 L42 26"/>'
                    '<path d="M40 28 A5 5 0 0 0 36 24"/>'),
    'conic_section': ('<path d="M22 24 L42 24 L42 40 L22 40 Z"/>'
                      '<path d="M22 32 L42 32"/>'
                      '<ellipse cx="32" cy="32" rx="8" ry="4"/>'),
    'analytic_general': ('<path d="M22 22 L22 44 L44 44"/>'
                         '<path d="M24 40 L40 24"/>'),
    'line_position': ('<path d="M22 24 L42 24 M22 42 L42 42"/>'
                      '<path d="M22 33 L42 33"/>'),
    'locus': ('<circle cx="32" cy="32" r="10"/>'
              '<path d="M22 32 L42 32"/>'),
    'equation_circle': '<circle cx="32" cy="32" r="11"/><path d="M22 22 L22 44 L44 44"/>',
    'circle_line_pos': ('<path d="M22 22 L22 44 L44 44"/>'
                        '<circle cx="32" cy="36" r="6"/>'
                        '<path d="M22 30 L44 30"/>'),
    'equation_curve': ('<path d="M22 22 L22 44 L44 44"/>'
                       '<path d="M24 42 Q32 18 42 42"/>'),
    'derivative_geo': ('<path d="M20 44 Q32 18 44 44"/>'
                       '<path d="M24 40 L40 26"/>'
                       + dot(32, 26, 2)),
    'derivative_monotonic': ('<path d="M22 42 L30 32 L42 22"/>'
                             '<path d="M22 44 L42 44"/>'),
    'derivative_extrema': ('<path d="M22 40 L32 24 L42 40"/>'
                           + dot(32, 24, 2.5)),
    'derivative_app': ('<path d="M22 42 L32 24 L42 42"/>'
                       + dot(32, 24, 2.5)),
    'taylor_series': (txt('f(x)', 16, x=32, y=33)),
    'integral_app': (txt('\u222b', 30) + '<path d="M22 42 L42 42"/>'),
    'limit_formal': (txt('lim', 14, x=28, y=28) +
                     txt('x\u2192a', 12, x=34, y=38)),
    'convergence': (dot(24, 42) + dot(30, 38) + dot(36, 34) + dot(40, 32) +
                    '<path d="M24 42 L40 32"/>'),
    'continuity_formal': '<path d="M22 32 Q32 28 42 32"/>',
    'differential_eq': (txt("y'=x", 16)),
    'multivariable': txt('\u2202', 28),
    'gradient_field': (txt('\u2207f', 22)),
    'area_integral': ('<path d="M22 42 Q32 24 42 42 Z"/>'
                      '<path d="M22 42 L42 42"/>'),
    'tangent_plane': ('<path d="M22 22 L22 44 L44 44"/>'
                      '<path d="M24 40 L40 24"/>'),
    'optimization_app': ('<path d="M22 42 L32 22 L42 42"/>'
                         + dot(32, 22, 2.5)),
    'random_variable': (txt('X', 22, x=28, y=28) + txt('~', 18, x=33, y=33) + txt('p', 18, x=38, y=38)),
    'hypergeometric': (txt('H(n)', 14, x=32, y=33)),
    'distribution_general': '<path d="M22 42 Q32 22 42 42"/>',
    'statistics_general': '<path d="M22 42 L42 42"/><rect x="24" y="34" width="4" height="8"/><rect x="30" y="28" width="4" height="14"/><rect x="36" y="32" width="4" height="10"/>',
    'data_general': '<path d="M22 42 L42 42"/><rect x="24" y="34" width="4" height="8"/><rect x="30" y="28" width="4" height="14"/>',
    'probability_general': '<rect x="22" y="22" width="20" height="20" rx="3"/>' + dot(28, 28) + dot(36, 36) + dot(28, 36) + dot(36, 28),
    'vector_general': '<path d="M22 42 L40 24"/><path d="M40 24 L34 24 M40 24 L40 30"/>',
    'sequence_general': (dot(24, 42) + dot(30, 36) + dot(36, 30) + dot(42, 24)),
    'function_general': (txt('f', 22, x=27, y=30) + txt('(x)', 16, x=37, y=35)),
    'equation_general': txt('=', 28),
    'calculus_general': txt('\u222b', 30),
    'algebra_general': (txt('x', 22, x=28, y=33) + txt('=', 20, x=33, y=33) + txt('?', 20, x=38, y=33)),
    'number_general': txt('N', 26),
    'expression_general': (txt('a', 18, x=26, y=33) + txt('+', 20, x=32, y=33) + txt('b', 18, x=38, y=33)),
    'thinking_general': txt('?', 28),
    'counting_general': (dot(24, 32) + dot(32, 32) + dot(40, 32)),
    'geometry_general': '<polygon points="32,20 44,28 40,42 24,42 20,28"/>',
    'measurement_general': ('<path d="M20 32 L44 32"/>'
                            '<path d="M24 28 L24 36 M40 28 L40 36"/>'),
    'ratio_general': (txt('a:b', 16)),
    'fraction_general': '<circle cx="32" cy="32" r="11"/><path d="M32 21 L32 32 L43 32"/>',
    'trigonometry_general': '<path d="M22 32 Q27 22 32 32 T42 32"/>',
    'solid_general': ('<path d="M22 26 L36 26 L36 40 L22 40 Z"/>'
                       '<path d="M36 26 L44 22 L44 36 L36 40"/>'),
    'analytic_general_sym': ('<path d="M22 22 L22 44 L44 44"/>'
                             '<path d="M24 40 L40 24"/>'),
    'complex_general': ('<path d="M22 32 L42 32 M32 22 L32 42"/>'
                        + dot(38, 26, 2.5)),
    'combinatorics_general': (dot(24, 32) + dot(32, 32) + dot(40, 32) +
                              '<path d="M24 28 L40 28"/>'),
    'representation_strategy': ('<rect x="22" y="24" width="8" height="8"/>'
                                '<path d="M30 28 L40 28 L40 38"/>'),
    'math_structure': '<path d="M22 24 L42 24 L42 40 L22 40 Z M22 32 L42 32 M32 24 L32 40"/>',
    'math_argument': ('<path d="M22 42 L32 22 L42 42 Z"/>'
                      '<path d="M32 22 L32 42"/>'),
    'repeated_reasoning': (dot(24, 42) + dot(30, 36) + dot(36, 30) + dot(42, 24) +
                           '<path d="M24 42 L42 24"/>'),
    'precise_comm': (txt('"', 22, x=26, y=33) + txt('"', 22, x=38, y=33)),
    'advanced_vocab': txt('Aa', 22),
    'efficient_method': ('<path d="M22 42 L42 22"/><path d="M22 32 L32 22"/>'),
    'showing_working': ('<path d="M22 24 L22 40 L30 40"/>'
                        '<path d="M30 24 L30 40 L42 40"/>'),
    'math_precision': '<circle cx="32" cy="32" r="8"/><circle cx="32" cy="32" r="2" fill="currentColor" stroke="none"/><path d="M32 20 L32 18 M32 46 L32 44 M20 32 L18 32 M46 32 L44 32"/>',
    'using_structure': '<path d="M22 24 L42 24 L42 40 L22 40 Z M22 32 L42 32 M32 24 L32 40"/>',
    'constructing_arguments': ('<path d="M22 42 L32 22 L42 42 Z"/>'
                                '<path d="M32 22 L32 42"/>'),
    'connecting_reps': ('<rect x="20" y="24" width="8" height="8"/>'
                        '<circle cx="40" cy="28" r="4"/>'
                        '<path d="M28 28 L36 28"/>'),
    'real_life': ('<circle cx="32" cy="32" r="10"/>'
                  '<path d="M32 22 L32 26 M32 38 L32 42 M22 32 L26 32 M38 32 L42 32"/>'),
    'money_work': '<circle cx="32" cy="32" r="9"/><circle cx="32" cy="32" r="6"/>',
    'tools_math': ('<circle cx="26" cy="32" r="4"/><circle cx="40" cy="32" r="4"/>'
                   '<path d="M30 32 L36 32"/>'),
    'multi_step_complex': ('<path d="M22 42 L26 36 L30 30 L34 24 L42 20"/>'
                           + dot(22, 42) + dot(26, 36) + dot(30, 30) + dot(34, 24) + dot(42, 20)),
}


# ============================================================================
# 关键词映射 (有序列表, 先匹配优先级高)
# ============================================================================
KEYWORD_MAP = [
    # === 基础运算 (高优先级, 因为很多领域会有重叠) ===
    (['加减', 'addition and subtraction', 'add and subtract'], 'plus_minus'),
    (['乘除', 'multiply and divide', 'multiplication and division'], 'times_divide'),
    (['加减消元', 'addition subtraction elimination'], 'elimination'),
    (['加法', '加', 'addition', 'adding', 'plus'], 'plus'),
    (['减法', '减', 'subtraction', 'subtract', 'minus'], 'minus'),
    (['乘法', '乘', 'multiplication', 'multiply', 'times', 'product'], 'times'),
    (['除法', '除', 'division', 'divide', 'quotient'], 'divide'),
    (['凑十', '凑成十', 'number bond', '分合', '分解', '拆成', 'decompos'], 'number_bond'),
    (['合并', '合在一起', 'combining', 'putting together'], 'combine'),
    (['借位', '退位', '进位', 'regroup', 'carry', 'borrow'], 'split'),
    (['竖式', 'column', 'vertical'], 'order_ops'),
    (['运算顺序', 'order of operations', 'bidmas', 'bodmas', 'pemdas'], 'order_operations'),
    (['估算', '估计', 'estimat', 'approximat', 'rounding'], 'estimation'),
    (['运算性质', 'properties of operation', 'property of operations'], 'order_operations'),
    (['质数', 'prime number', 'prime'], 'integer_num'),
    (['混合运算', 'mixed operation', 'mental arithmetic', '口算'], 'order_operations'),
    (['逆运算', 'inverse operation'], 'arrow_bidir'),

    # === 数与计数 ===
    (['数位', '位值', 'place value'], 'frac_bar'),
    (['十格', '十阵', 'ten frame', 'ten-frame'], 'area_grid'),
    (['奇偶', 'odd and even', 'odd or even'], 'mode'),
    (['跳数', 'skip count', 'counting in'], 'sequence_dots'),
    (['一一对应', 'one-to-one', 'one to one'], 'combination'),
    (['基数', 'cardinal', 'how many'], 'counting_general'),
    (['多少', '比较', 'more or fewer', 'more or less', 'compar'], 'lt'),
    (['数数', 'counting', 'count'], 'counting_general'),
    (['读', '写', 'reading and writing', 'read and write', 'number words'], 'vocab'),
    (['进制', 'base', 'binary'], 'matrix'),
    (['算盘', 'abacus'], 'matrix'),
    (['数轴', 'number line'], 'number_line'),
    (['数字单词', 'number words'], 'vocab'),
    (['负数', 'negative number', 'negative'], 'number_line'),
    (['罗马', 'roman numeral', 'roman'], 'number_general'),
    (['倍数', 'multiple of', 'multiples'], 'sequence_dots'),
    (['排序', 'ordering number', 'order numbers'], 'lt'),
    (['十几', 'teen number', 'the teen'], 'number_general'),
    (['多十', '少十', '10 more', '10 less'], 'plus_minus'),
    (['十是个十', 'ten is ten', 'ten ones', 'a ten is'], 'number_general'),
    (['一百是', 'a hundred is', 'ten tens'], 'number_general'),
    (['数集', 'number set', '无穷', 'infinity'], 'infinity'),
    (['以内', 'numbers to', 'within'], 'number_general'),

    # === 分数 / 小数 / 百分比 ===
    (['二分之一', 'half', 'halves'], 'half'),
    (['四分之一', 'quarter', 'quarters'], 'quarter'),
    (['小数', 'decimal'], 'decimal'),
    (['百分', 'percent'], 'percent'),
    (['等值', '等价', 'equivalent', 'equivalence'], 'identical'),
    (['分数', 'fraction', 'fractions'], 'fraction'),
    (['十分位', '千分位', 'tenths', 'tenth'], 'decimal'),
    (['相等部分', 'equal part', 'splitting shape'], 'fraction'),

    # === 几何形状 ===
    (['三角形', 'triangle'], 'triangle'),
    (['正方形', 'square shape', '正方'], 'square_shape'),
    (['长方形', '矩形', 'rectangle'], 'rectangle_shape'),
    (['平行四边形', 'parallelogram'], 'parallelogram'),
    (['菱形', 'rhombus', 'diamond'], 'rhombus'),
    (['梯形', 'trapezoid', 'trapezium'], 'trapezoid'),
    (['多边形', 'polygon'], 'polygon_general'),
    (['正多边形', 'regular polygon'], 'regular_polygon'),
    (['圆', 'circle'], 'circle_shape'),
    (['椭圆', 'ellipse', 'oval'], 'ellipse_shape'),
    (['圆柱', 'cylinder'], 'cylinder'),
    (['圆锥', 'cone'], 'cone'),
    (['球', 'sphere'], 'sphere'),
    (['立方', 'cube', '正方体', '长方体', '棱柱', '棱锥', 'prism'], 'cube_3d'),
    (['二维', '2-d shape', '2d shape', 'flat shape', '平面图形'], 'polygon_general'),
    (['搭建', 'building shape', 'drawing shape', '绘制图形'], 'compass_tool'),
    (['棱', '顶点', 'edge', 'vertex', 'vertices'], 'edge_vertex_face'),
    (['相似', 'similar'], 'similar_figures'),
    (['全等', 'congruent'], 'congruent'),
    (['勾股', 'pythag', 'pythagoras'], 'pythagoras'),
    (['位似', 'homothety', 'homothetic'], 'similar_figures'),

    # === 角 / 平行 / 垂直 ===
    (['直角', 'right angle'], 'right_angle'),
    (['锐角', '钝角', 'angle type', 'types of angle', 'acute', 'obtuse'], 'angle_type'),
    (['内角和', 'angle sum', 'angle sums'], 'angle_sum'),
    (['平行线', 'parallel line', 'parallel and perpendicular'], 'parallel_sym'),
    (['垂线', 'perpendicular'], 'perp_sym'),
    (['相交', 'intersect'], 'plane_lines'),
    (['角', 'angle'], 'angle_mark'),
    (['度数', '度', 'degree', 'turn'], 'degree'),
    (['量角', 'protractor', 'measuring angle'], 'protractor'),
    (['弧', 'arc', 'sector', '扇形'], 'arc_sector'),
    (['切线', 'tangent line', 'tangent to'], 'tangent_line'),

    # === 对称 / 变换 ===
    (['轴对称', 'line symmetry', 'axisymmetric', 'symmetric figure'], 'axis_symmetry'),
    (['中心对称', 'central symmetry', 'point symmetry'], 'center_symmetry'),
    (['对称', 'symmetry'], 'symmetry'),
    (['平移', 'translate', 'translation'], 'translate'),
    (['旋转', 'rotate', 'rotation', 'turn'], 'rotate'),
    (['反射', '翻转', 'reflect', 'reflection', 'flip'], 'reflect'),
    (['变换', 'transform', 'transformation'], 'coordinate_transform'),

    # === 面积 / 周长 / 体积 ===
    (['表面积', 'surface area'], 'surface_area'),
    (['体积', 'volume', 'capacity'], 'volume_measure'),
    (['面积', 'area'], 'area_measure'),
    (['周长', 'perimeter'], 'perimeter_measure'),
    (['截面', 'cross section', 'section'], 'cross_section'),
    (['展开图', 'net', 'nets of'], 'net'),
    (['三视图', 'three view', 'viewing', 'views', 'different viewpoint'], 'three_views'),

    # === 坐标 / 位置 ===
    (['坐标系', 'coordinate system', 'cartesian', '直角坐标系'], 'axes'),
    (['坐标', 'coordinate', 'plotting', 'plot point'], 'plot_point'),
    (['第一象限', 'first quadrant'], 'plot_point'),
    (['位置', 'position', 'positional'], 'position'),
    (['方向', 'direction', 'turns & direction'], 'direction'),
    (['东南西北', 'cardinal', 'north', 'compass direction'], 'cardinal'),

    # === 度量 ===
    (['长度', 'length', 'long', 'height', 'tall'], 'length_measure'),
    (['质量', '重量', 'mass', 'weight'], 'mass_weight'),
    (['容量', 'capacity'], 'capacity_vol'),
    (['时间', 'time', 'duration', '时长'], 'time_duration'),
    (['钟', 'clock', 'telling time', '认时间', '小时', 'minute', '分钟', '秒'], 'telling_time'),
    (['日历', 'calendar', '年', '月', '日', 'day', 'week', 'month', 'year'], 'calendar_sym'),
    (['货币', '钱', 'coin', 'money', '人民币', 'change', '找零', 'pence', 'pound'], 'coin_value'),
    (['温度', 'temperature', 'thermometer'], 'thermometer'),
    (['换算', 'convert', 'conversion'], 'unit_convert'),
    (['单位', 'unit'], 'measurement_general'),
    (['尺', 'ruler', 'measuring length', '测量长度'], 'ruler'),
    (['可测', 'measurable', 'attribute'], 'measurement_general'),
    (['测量值', 'calculating with measurement'], 'plus'),
    (['英里', '公里', 'mile', 'kilometre', 'kilometer'], 'unit_convert'),

    # === 数据统计 ===
    (['平均', 'mean', 'average'], 'mean'),
    (['中位数', 'median'], 'median'),
    (['众数', 'mode'], 'mode'),
    (['方差', 'variance', '标准差', 'standard deviation', '波动', 'spread'], 'variance'),
    (['直方', 'histogram'], 'histogram'),
    (['条形', 'bar graph', 'bar chart', 'bar model'], 'bar_chart'),
    (['散点', 'scatter'], 'scatter'),
    (['相关', 'correlation', 'correlat'], 'correlation'),
    (['回归', 'regression'], 'regression'),
    (['饼图', 'pie chart', 'pie'], 'pie_chart'),
    (['折线', 'line graph', 'line plot'], 'line_plot'),
    (['象形', 'pictogram', 'pictograph'], 'pictogram'),
    (['tally', '计数符号'], 'tally'),
    (['表格', 'table', 'read table'], 'table'),
    (['分布', 'distribution'], 'distribution'),
    (['样本', 'sample', '抽样'], 'sample'),
    (['调查', 'survey'], 'survey_sym'),
    (['统计', 'statistic', 'data'], 'statistics_general'),
    (['分类', 'sort', 'category', 'categoris', 'classifying'], 'sort'),
    (['韦恩', 'venn'], 'venn'),
    (['频数', 'frequency', '频率'], 'frequency'),
    (['正态', 'normal distribution', 'normal dist'], 'normal_dist'),
    (['二项分布', 'binomial distribution', 'binomial dist'], 'binomial_dist'),
    (['期望', 'expectation', 'expected'], 'expectation'),
    (['独立性检验', 'independence test', 'chi'], 'independence'),

    # === 概率 ===
    (['条件概率', 'conditional'], 'conditional_prob'),
    (['独立', 'independent', 'independence'], 'independence'),
    (['贝叶斯', 'bayes'], 'bayes'),
    (['全概率', 'total probability', 'law of total'], 'conditional_prob'),
    (['树状', 'tree diagram'], 'tree_diagram'),
    (['可能', 'likely', 'likelihood', 'probability'], 'likely'),
    (['实验', 'experiment', 'experimental'], 'experiment'),
    (['等可能', 'equally likely'], 'likely'),
    (['互补', 'complementary'], 'complementary'),
    (['列举', 'listing', 'list'], 'listing'),
    (['随机', 'random', 'random variable'], 'random_variable'),
    (['超几何', 'hypergeometric'], 'hypergeometric'),
    (['概率', 'probability', 'chance'], 'probability_general'),

    # === 比例 / 相似 ===
    (['比例尺', 'scale', 'scaled drawing'], 'scale_sym'),
    (['比例与相似', 'scale and similar', 'similar shape'], 'similar_shapes'),
    (['按比例', 'dividing quantit', 'divide by ratio', 'dividing quantit'], 'ratio_sym'),
    (['比例图', 'proportion graph'], 'line_graph'),
    (['比例', 'proportion'], 'proportion'),
    (['比与比例', 'ratio and proportion'], 'ratio_sym'),
    (['比的', '比值', 'ratio problem', 'ratio notation'], 'ratio_sym'),

    # === 代数 ===
    (['变量', 'variable', '常量', 'constant'], 'variable_x'),
    (['公式', 'formula', 'formulae'], 'formula_use'),
    (['同类项', 'like terms'], 'combination'),
    (['因式分解', 'factoris', 'factor', '因式'], 'combination'),
    (['整式', 'polynomial', 'monomial'], 'expression_general'),
    (['分式', 'algebraic fraction'], 'fraction'),
    (['根式', 'surd', '根号', 'radical'], 'sqrt'),
    (['平方根', 'square root'], 'sqrt'),
    (['立方根', 'cube root'], 'sqrt'),
    (['平方差', 'difference of square'], 'formula_use'),
    (['完全平方', 'perfect square'], 'complete_square'),
    (['幂', '乘方', 'power', 'exponent', '指数幂'], 'power'),
    (['同底数', 'same base'], 'power'),
    (['科学记数', 'scientific notation'], 'scientific'),
    (['有理数', 'rational'], 'rational_num'),
    (['实数', 'real number'], 'real_num'),
    (['整数', 'integer'], 'integer_num'),
    (['表达式', 'expression'], 'expression_general'),
    (['展开', 'expand', 'bracket', 'expanding'], 'matrix'),
    (['代数', 'algebra'], 'algebra_general'),

    # === 方程与不等式 ===
    (['一元二次', 'quadratic equation'], 'quadratic_eq'),
    (['一元一次', 'linear equation'], 'linear_eq'),
    (['二元', '方程组', 'system of equation', 'simultaneous'], 'system_eq'),
    (['三元', 'three unknown'], 'system_eq'),
    (['消元', 'elimination', 'substitution'], 'elimination'),
    (['配方', 'completing the square'], 'complete_square'),
    (['求根公式', 'quadratic formula'], 'quadratic_formula'),
    (['判别式', 'discriminant'], 'discriminant'),
    (['韦达', 'vieta', "vieta's"], 'vieta'),
    (['不等式组', 'inequality system'], 'inequality_system'),
    (['不等', 'inequal', 'inequality'], 'inequality'),
    (['等式', 'property of equal', 'equality'], 'equation_property'),
    (['方程', 'equation'], 'equation_general'),
    (['区间', 'interval'], 'interval'),
    (['矩阵', 'matrix'], 'matrix'),

    # === 函数 ===
    (['一次函数', 'linear function'], 'linear_fn'),
    (['二次函数', 'quadratic function'], 'quadratic_fn'),
    (['反比例', '反函数', 'inverse function', 'inverse proportion'], 'inverse_fn'),
    (['指数函数', 'exponential function'], 'exponential_fn'),
    (['指数运算', 'exponent operation', 'indices', 'exponent'], 'power'),
    (['对数', 'logarithm', 'log function'], 'log_fn'),
    (['幂函数', 'power function'], 'power_fn'),
    (['单调', 'monotonic', 'monotonicity'], 'monotonic'),
    (['奇偶', 'odd even', 'odd-even', 'parity'], 'odd_even_fn'),
    (['周期', 'periodic', 'periodicity'], 'periodic'),
    (['定义域', 'domain', 'range', '值域', '三要素'], 'domain_range'),
    (['映射', 'mapping'], 'mapping'),
    (['函数', 'function'], 'function_general'),

    # === 三角学 ===
    (['正弦定理', 'sine rule', 'law of sine'], 'sine'),
    (['余弦定理', 'cosine rule', 'law of cosine'], 'cosine'),
    (['正弦', 'sine'], 'sine'),
    (['余弦', 'cosine'], 'cosine'),
    (['正切', 'tangent', 'tan'], 'tangent_wave'),
    (['单位圆', 'unit circle'], 'unit_circle'),
    (['弧度', 'radian'], 'radian'),
    (['直角三角形', 'right triangle', 'right-angled triangle'], 'right_triangle'),
    (['诱导', 'induced', 'reduction formula'], 'angle_relation'),
    (['同角', 'co-function', 'identities'], 'angle_relation'),
    (['和差角', 'sum and difference', 'addition formula'], 'angle_relation'),
    (['倍角', 'double angle', 'half angle'], 'angle_relation'),
    (['解三角形', 'solving triangle', 'solve triangle'], 'right_triangle'),
    (['特殊角', 'special angle', 'special value'], 'special_angles'),
    (['锐角', 'acute angle'], 'acute_angle'),
    (['三角函数', 'trigonometric', 'trig function'], 'sine'),
    (['三角', 'trigonometry', 'trig'], 'sine'),

    # === 向量 ===
    (['数量积', '点积', 'dot product', 'scalar product', 'inner product'], 'dot_product'),
    (['基本定理', 'basis', 'fundamental theorem'], 'vector_basis'),
    (['空间向量', '3d vector', 'spatial vector'], 'vector_3d'),
    (['坐标', 'coordinate', 'coordinate representation'], 'axes'),
    (['线性运算', 'linear operation', 'linear combination'], 'vector_arrow'),
    (['向量应用', 'vector application', 'application'], 'vector_arrow'),
    (['向量', 'vector'], 'vector_arrow'),

    # === 立体几何 ===
    (['表面积', 'surface area'], 'surface_area'),
    (['几何体', 'solid figure', 'geometric solid'], 'cube_3d'),
    (['点线面', 'point line plane', 'position relation'], 'point_line_plane'),
    (['线面平行', '面面平行', 'line plane parallel', 'plane parallel'], 'parallel_sym'),
    (['线面垂直', '面面垂直', 'line plane perpendicular', 'plane perpendicular'], 'perp_sym'),
    (['空间角', 'space angle', 'dihedral'], 'space_angle'),
    (['空间距离', 'space distance', 'distance in space'], 'distance'),
    (['立体', 'solid', '3d shape', '3-d shape', '三维'], 'cube_3d'),
    (['球', 'sphere'], 'sphere'),

    # === 解析几何 ===
    (['直线方程', 'line equation', 'equation of line'], 'line_eq'),
    (['斜率', 'slope', 'gradient'], 'slope'),
    (['圆的方程', 'equation of circle', 'circle equation'], 'equation_circle'),
    (['直线与圆', 'line and circle', 'line circle position'], 'circle_line_pos'),
    (['双曲线', 'hyperbola'], 'hyperbola'),
    (['抛物线', 'parabola', 'parabolic'], 'parabola'),
    (['椭圆', 'ellipse'], 'ellipse_shape'),
    (['圆锥曲线', 'conic', 'conic section'], 'conic_section'),
    (['参数方程', 'parametric', 'parameter equation'], 'parametric'),
    (['极坐标', 'polar', 'polar coordinate'], 'polar_coord'),
    (['位置关系', 'position relationship', 'relative position'], 'line_position'),
    (['直线', 'line', 'straight line'], 'line_eq'),
    (['解析', 'analytic'], 'analytic_general_sym'),

    # === 数列 ===
    (['等差', 'arithmetic', 'arithmetic sequence', 'arithmetic progression'], 'arithmetic_seq'),
    (['等比', 'geometric', 'geometric sequence', 'geometric progression'], 'geometric_seq'),
    (['通项', 'general term', 'nth term'], 'general_term'),
    (['求和', 'sum', 'summation', 'series sum'], 'sum_series'),
    (['归纳', 'induction', 'mathematical induction'], 'induction'),
    (['递推', 'recurrence', 'recursive'], 'recurrence'),
    (['数列', 'sequence', 'series'], 'sequence_general'),

    # === 微积分 ===
    (['不定积分', 'indefinite integral', 'antiderivative'], 'indefinite_integral'),
    (['定积分', 'definite integral'], 'definite_integral'),
    (['积分应用', 'integral application', 'application of integral'], 'area_integral'),
    (['积分', 'integral', 'integration'], 'integral'),
    (['极限', 'limit'], 'limit_formal'),
    (['导数概念', 'derivative concept', 'concept of derivative'], 'derivative'),
    (['几何意义', 'geometric meaning', 'geometric significance'], 'derivative_geo'),
    (['单调性', 'monotonicity', 'derivative monotonic'], 'derivative_monotonic'),
    (['极值', '最值', 'extrema', 'extremum', 'maximum', 'minimum'], 'derivative_extrema'),
    (['实际应用', 'practical application', 'real application'], 'derivative_app'),
    (['求导', 'derivative', 'differentiat', '导数'], 'derivative'),
    (['连续', 'continuous', 'continuity'], 'continuity_formal'),
    (['微积分', 'calculus'], 'calculus_general'),

    # === 复数 ===
    (['虚数', 'imaginary'], 'imaginary_i'),
    (['三角形式', 'trigonometric form', 'polar form of complex'], 'polar_form'),
    (['几何意义', 'geometric meaning', 'geometric'], 'complex_plane'),
    (['复数运算', 'complex operation', 'complex arithmetic'], 'complex_plane'),
    (['复数', 'complex', 'complex number'], 'complex_plane'),

    # === 组合数学 ===
    (['二项式', 'binomial', 'binomial theorem'], 'binomial'),
    (['排列组合', 'permutation and combination'], 'combination'),
    (['排列', 'permutation'], 'permutation'),
    (['组合', 'combination'], 'combination'),
    (['计数原理', 'counting principle', '分类加法', '分步乘法'], 'counting_principle'),
    (['计数', 'counting', 'enumeration'], 'counting_principle'),

    # === 数学思维 (META) ===
    (['词汇', 'vocabulary', 'notation'], 'vocab'),
    (['规律', 'pattern', 'spotting pattern', 'shape pattern'], 'pattern'),
    (['多步', 'multi-step', 'multistep', 'multiple step'], 'multi_step'),
    (['优化', 'optimization', 'optimal', 'best arrangement'], 'optimization'),
    (['植树', 'tree planting', 'interval problem'], 'tree_planting'),
    (['结构', 'structure'], 'math_structure'),
    (['概括', 'generalis', 'generalize', 'generalising'], 'generalise'),
    (['等值', 'equivalence', 'equivalent'], 'identical'),
    (['论证', 'argument', 'justifying', 'justify', 'constructing argument'], 'math_argument'),
    (['推理', 'reasoning', 'reason'], 'reasoning'),
    (['证明', 'proof', 'prove'], 'proof'),
    (['建模', 'model', 'modelling', 'modeling'], 'modeling'),
    (['联系', 'connect', 'connection', 'real world', 'real life', '现实'], 'real_world'),
    (['表征', 'representation', 'representing'], 'representation'),
    (['解释', 'explain', 'explanation', 'communicat'], 'precise_comm'),
    (['精确', 'precision', 'precise'], 'math_precision'),
    (['工具', 'tool', 'tools'], 'tools_math'),
    (['策略', 'strategy', 'strategic'], 'strategy'),
    (['方法', 'method', 'efficient'], 'efficient_method'),
    (['解题', 'problem solving', 'problem', 'sense of problem', 'sense making'], 'question'),
    (['货币', 'money', '货币问题'], 'coin_value'),
    (['分数', 'fraction'], 'fraction'),
    (['乘法', 'multiplication'], 'times'),
    (['展示', 'showing', 'working'], 'showing_working'),
    (['数学广角', 'math perspective', 'broad perspective'], 'question'),
    (['数学', 'math', 'maths'], 'question'),
]


# ============================================================================
# 领域默认符号
# ============================================================================
DOMAIN_DEFAULTS = {
    'Geometry': 'geometry_general',
    'Measurement': 'measurement_general',
    'Fractions': 'fraction_general',
    'Multiplication & Division': 'times_divide',
    'Addition & Subtraction': 'plus_minus',
    'Number Representation & Place Value': 'number_general',
    'Mathematical Thinking': 'thinking_general',
    'Data & Statistics': 'statistics_general',
    'Algebra': 'algebra_general',
    'Probability': 'probability_general',
    'Ratio & Proportion': 'ratio_general',
    'Counting & Cardinality': 'counting_general',
    'Number & Expression': 'expression_general',
    'Equations & Inequalities': 'equation_general',
    'Functions': 'function_general',
    'Trigonometry': 'trigonometry_general',
    'Vectors': 'vector_general',
    'Solid Geometry': 'solid_general',
    'Analytic Geometry': 'analytic_general_sym',
    'Sequences': 'sequence_general',
    'Calculus': 'calculus_general',
    'Complex Numbers': 'complex_general',
    'Combinatorics': 'combinatorics_general',
}


# ============================================================================
# 符号匹配逻辑
# ============================================================================
def match_symbol(topic):
    """根据 name_zh 和 name 匹配符号, 返回 (symbol_key, matched_keyword 或 None)"""
    name_zh = topic.get('name_zh', '') or ''
    name = (topic.get('name', '') or '').lower()
    combined = name_zh + ' || ' + name

    for keywords, symbol_key in KEYWORD_MAP:
        for kw in keywords:
            if kw.lower() in combined.lower():
                return symbol_key, kw

    # 未匹配关键词, 使用领域默认
    domain = topic.get('domain', '')
    default_key = DOMAIN_DEFAULTS.get(domain, 'question')
    return default_key, None


# ============================================================================
# SVG 构建
# ============================================================================
def build_svg(frame_key, symbol_svg):
    """构建完整 SVG 文件内容"""
    frame_svg = FRAMES[frame_key]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" '
        'stroke="currentColor" fill="none" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<g id="frame">{}</g>'
        '<g id="symbol">{}</g>'
        '</svg>'
    ).format(frame_svg, symbol_svg)


# ============================================================================
# 主函数
# ============================================================================
def main():
    # 加载数据
    with open(DATA_FILE, encoding='utf-8') as f:
        data = json.load(f)
    topics = data['topics']
    print('加载 {} 个节点'.format(len(topics)))

    # 创建输出目录
    os.makedirs(OUT_DIR, exist_ok=True)

    # 统计
    type_counter = Counter()
    domain_counter = Counter()
    frame_counter = Counter()
    symbol_counter = Counter()
    unmatched = []
    index_records = []

    for topic in topics:
        node_id = topic['id']
        node_type = topic.get('type', 'CONCEPTUAL')
        domain = topic.get('domain', 'Unknown')
        name_zh = topic.get('name_zh', '')
        name = topic.get('name', '')

        frame_key = TYPE_TO_FRAME.get(node_type, 'CRYSTAL')
        symbol_key, matched_kw = match_symbol(topic)

        if matched_kw is None:
            unmatched.append({
                'id': node_id,
                'name_zh': name_zh,
                'name': name,
                'domain': domain,
                'symbol': symbol_key,
            })

        symbol_svg = SYMBOLS.get(symbol_key, SYMBOLS['question'])
        svg_content = build_svg(frame_key, symbol_svg)

        # 写文件
        out_path = os.path.join(OUT_DIR, node_id + '.svg')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

        # 统计
        type_counter[node_type] += 1
        domain_counter[domain] += 1
        frame_counter[frame_key] += 1
        symbol_counter[symbol_key] += 1

        index_records.append({
            'id': node_id,
            'name': name,
            'name_zh': name_zh,
            'domain': domain,
            'type': node_type,
            'frame': frame_key,
            'symbol': symbol_key,
            'matchedKeyword': matched_kw,
        })

    # 写 index.json
    index_path = os.path.join(OUT_DIR, 'index.json')
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump({
            'description': '数学天赋星图 SVG 符号索引',
            'totalNodes': len(topics),
            'totalGenerated': len(index_records),
            'frames': {
                'CRYSTAL': '八角切面晶体框 (CONCEPTUAL/CONCEPTURAL)',
                'GEAR': '六边形齿轮框 (PROCEDURAL)',
                'HOLO': '方形全息框-四角光标 (REPRESENTATIONAL)',
                'RING': '圆环框 (LANGUAGE)',
                'STAR': '五角星芒框 (META/METACOGNITIVE)',
            },
            'records': index_records,
        }, f, ensure_ascii=False, indent=2)

    # 打印统计信息
    print('\n' + '=' * 60)
    print('生成完成!')
    print('=' * 60)
    print('总节点数: {}'.format(len(topics)))
    print('已生成 SVG: {} 个'.format(len(index_records)))
    print('未匹配关键词(使用领域默认): {} 个'.format(len(unmatched)))

    print('\n--- 各类型数量 ---')
    for t, c in type_counter.most_common():
        print('  {}: {}'.format(t, c))

    print('\n--- 各外框数量 ---')
    for f, c in frame_counter.most_common():
        print('  {}: {}'.format(f, c))

    print('\n--- 各领域数量 ---')
    for d, c in domain_counter.most_common():
        print('  {}: {}'.format(d, c))

    print('\n--- 未匹配关键词节点 (前 30 个) ---')
    for u in unmatched[:30]:
        print('  [{}] {} | {}'.format(u['domain'], u['id'], u['name_zh'] or u['name']))

    if len(unmatched) > 30:
        print('  ... 还有 {} 个'.format(len(unmatched) - 30))

    print('\n输出目录: {}'.format(OUT_DIR))
    print('索引文件: {}'.format(index_path))


if __name__ == '__main__':
    main()
