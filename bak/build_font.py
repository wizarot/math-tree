#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_font.py
将 assets/symbols/ 目录下的 702 个 SVG 图标转换为 Icon Font (TTF / WOFF / WOFF2)。

技术路线:
  - fonttools: 构建 TrueType 字体
  - skia-pathops: 将描边 (stroke) 轮廓转换为填充 (fill) 轮廓 (icon font 必须是填充轮廓)
  - freetype-py: 将 SVG <text> 元素渲染为字形轮廓 (text -> path)

关键点:
  - 这些 SVG 是 *描边* 图 (fill=none, stroke=currentColor, stroke-width=1.5)。
    字体字形必须是 *填充* 形状, 因此对每个描边元素调用 pathops.Path.stroke() 转换。
  - 对 fill=currentColor 的元素 (如圆点) 直接作为填充轮廓。
  - <text> 元素 (如 +, -, ×, ÷, Σ, √ ...) 用 freetype 从系统字体 (times/georgia)
    提取字形轮廓并按 SVG 中的 x/y/font-size/anchor/baseline 定位。

输出:
  - assets/mtf.ttf           TrueType 字体
  - assets/mtf.woff          WOFF 字体
  - assets/mtf.woff2         WOFF2 字体 (需要 brotli)
  - assets/mtf-codepoints.json   {node_id: unicode_codepoint(int)}
  - assets/mtf-font.css      FontAwesome 风格 CSS

字符映射:
  - 每个 SVG 文件 -> 一个 Unicode 码点 (从 0xE001 开始, Private Use Area)
"""

import os
import re
import sys
import json
import html

# ----------------------------------------------------------------------------
# 路径配置
# ----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYMBOLS_DIR = os.path.join(BASE_DIR, 'assets', 'symbols')
INDEX_FILE = os.path.join(SYMBOLS_DIR, 'index.json')
OUT_TTF = os.path.join(BASE_DIR, 'assets', 'mtf.ttf')
OUT_WOFF = os.path.join(BASE_DIR, 'assets', 'mtf.woff')
OUT_WOFF2 = os.path.join(BASE_DIR, 'assets', 'mtf.woff2')
OUT_CODEPOINTS = os.path.join(BASE_DIR, 'assets', 'mtf-codepoints.json')
OUT_CSS = os.path.join(BASE_DIR, 'assets', 'mtf-font.css')

FONT_FAMILY = 'MTF Icons'
FIRST_CODEPOINT = 0xE001  # Private Use Area 起点

# 系统字体 (Windows) - 用于 <text> -> 轮廓; 顺序即回退顺序
SYSTEM_FONTS = [
    r'C:\Windows\Fonts\times.ttf',     # Times New Roman: 覆盖大量数学符号
    r'C:\Windows\Fonts\georgia.ttf',   # Georgia: SVG 中声明的首选字体
]

# SVG -> 字体 坐标变换
# unitsPerEm = 1000; SVG 0..64 映射到约 800 单位, 居中于方形 em
UPEM = 1000
SVG_SCALE = 12.5            # 64 * 12.5 = 800
SVG_X_OFFSET = 100.0        # (1000 - 800) / 2
SVG_Y_TOP = 700.0           # svg y=0 -> font y=700; svg y=64 -> 700-800=-100
ASCENT = 800
DESCENT = -200

# ----------------------------------------------------------------------------
# 延迟导入 (便于在缺少依赖时给出清晰提示)
# ----------------------------------------------------------------------------
def _import_deps():
    missing = []
    try:
        import fontTools  # noqa
    except ImportError:
        missing.append('fonttools')
    try:
        import pathops  # noqa
    except ImportError:
        missing.append('skia-pathops')
    try:
        import freetype  # noqa
    except ImportError:
        missing.append('freetype-py')
    if missing:
        print('[error] 缺少依赖: {}'.format(', '.join(missing)))
        print('        请运行: python -m pip install {} brotli'.format(' '.join(missing)))
        sys.exit(1)


_import_deps()

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.misc.transform import Transform
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont
import pathops
import freetype

# 变换矩阵: x' = SVG_SCALE*x + X_OFFSET;  y' = -SVG_SCALE*y + Y_TOP  (翻转 y)
MATRIX = Transform(SVG_SCALE, 0, 0, -SVG_SCALE, SVG_X_OFFSET, SVG_Y_TOP)

# 描边参数 (与 SVG 一致: stroke-width=1.5, round cap/join)
STROKE_WIDTH = 1.5
STROKE_CAP = pathops.LineCap.ROUND_CAP
STROKE_JOIN = pathops.LineJoin.ROUND_JOIN
STROKE_MITER = 4.0

# ----------------------------------------------------------------------------
# SVG 解析
# ----------------------------------------------------------------------------
FRAME_RE = re.compile(r'<g id="frame">(.*?)</g>', re.S)
SYMBOL_RE = re.compile(r'<g id="symbol">(.*?)</g>', re.S)

# 矢量元素 (自闭合)
VEC_ELEM_RE = re.compile(
    r'<(path|polygon|polyline|line|rect|circle|ellipse)\b([^>]*?)/>', re.S
)
# 文本元素
TEXT_ELEM_RE = re.compile(r'<text\b([^>]*?)>(.*?)</text>', re.S)
# 属性
ATTR_RE = re.compile(r'([A-Za-z_:][\w:.-]*)\s*=\s*"([^"]*)"')


def extract_groups(svg_text):
    fm = FRAME_RE.search(svg_text)
    sm = SYMBOL_RE.search(svg_text)
    return (fm.group(1) if fm else ''), (sm.group(1) if sm else '')


def parse_attrs(attr_str):
    return {k: v for k, v in ATTR_RE.findall(attr_str)}


def _f(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def elem_to_path_d(tag, a):
    """把矢量元素转换为 SVG path d 字符串。返回 None 表示跳过。"""
    if tag == 'path':
        return a.get('d')
    if tag in ('polygon', 'polyline'):
        pts = a.get('points', '').replace(',', ' ')
        toks = pts.split()
        if len(toks) < 2:
            return None
        nums = []
        for t in toks:
            try:
                nums.append(float(t))
            except ValueError:
                return None
        if len(nums) % 2 != 0:
            return None
        coords = list(zip(nums[0::2], nums[1::2]))
        d = 'M{},{} '.format(coords[0][0], coords[0][1])
        d += ' '.join('L{},{}'.format(x, y) for x, y in coords[1:])
        if tag == 'polygon':
            d += ' Z'
        return d
    if tag == 'line':
        x1, y1 = _f(a.get('x1')), _f(a.get('y1'))
        x2, y2 = _f(a.get('x2')), _f(a.get('y2'))
        return 'M{},{} L{},{}'.format(x1, y1, x2, y2)
    if tag == 'rect':
        x, y = _f(a.get('x')), _f(a.get('y'))
        w, h = _f(a.get('width')), _f(a.get('height'))
        if w == 0 or h == 0:
            return None  # 零面积, 跳过
        return 'M{},{} L{},{} L{},{} L{},{} Z'.format(x, y, x + w, y, x + w, y + h, x, y + h)
    if tag == 'circle':
        cx, cy, r = _f(a.get('cx')), _f(a.get('cy')), _f(a.get('r'))
        if r <= 0:
            return None
        return 'M{},{} A{},{},0,1,0 {},{} A{},{},0,1,0 {},{} Z'.format(
            cx - r, cy, r, r, cx + r, cy, r, r, cx - r, cy)
    if tag == 'ellipse':
        cx, cy = _f(a.get('cx')), _f(a.get('cy'))
        rx, ry = _f(a.get('rx')), _f(a.get('ry'))
        if rx <= 0 or ry <= 0:
            return None
        return 'M{},{} A{},{},0,1,0 {},{} A{},{},0,1,0 {},{} Z'.format(
            cx - rx, cy, rx, ry, cx + rx, cy, rx, ry, cx - rx, cy)
    return None


def is_filled_element(a):
    """判断元素是否为填充 (而非描边)。

    SVG 根: fill=none stroke=currentColor。
    元素若显式 fill != none -> 填充; 否则继承 fill=none -> 描边。
    """
    fill = a.get('fill')
    if fill is not None and fill.lower() != 'none':
        return True
    return False


# ----------------------------------------------------------------------------
# freetype 字体加载 (用于 <text> -> 轮廓)
# ----------------------------------------------------------------------------
class FontResolver:
    def __init__(self, paths):
        self.faces = []
        for p in paths:
            if os.path.exists(p):
                try:
                    self.faces.append(freetype.Face(p))
                except Exception as exc:  # noqa: BLE001
                    print('  [warn] 加载字体 {} 失败: {}'.format(p, exc))
            else:
                print('  [warn] 字体文件不存在: {}'.format(p))

    def get_glyph(self, ch):
        """返回 (face, glyph_index) 或 (None, 0)。"""
        for face in self.faces:
            idx = face.get_char_index(ord(ch))
            if idx != 0:
                return face, idx
        return None, 0


def _ptxy(p):
    """freetype outline 点可能是 Vector 对象或 (x, y) 元组。"""
    if isinstance(p, (list, tuple)):
        return p[0], p[1]
    return p.x, p.y


def draw_freetype_outline(outline, to_svg, pen):
    """把 freetype 字形轮廓 (二次贝塞尔) 绘制到 pen, 经 to_svg 变换。"""
    points = outline.points
    tags = outline.tags
    contours = outline.contours
    start = 0
    for end in contours:
        cnt_pts = [_ptxy(points[i]) for i in range(start, end + 1)]
        cnt_tags = [bool(tags[i] & 1) for i in range(start, end + 1)]
        start = end + 1
        _draw_quad_contour(cnt_pts, cnt_tags, to_svg, pen)


def _draw_quad_contour(pts, tags, to_svg, pen):
    n = len(pts)
    if n == 0:
        return
    on_idx = [i for i, t in enumerate(tags) if t]
    if not on_idx:
        # 全部离点: 在相邻离点中点插入隐式 on-curve
        sx = (pts[-1][0] + pts[0][0]) / 2.0
        sy = (pts[-1][1] + pts[0][1]) / 2.0
        pen.moveTo(to_svg(sx, sy))
        for i in range(n):
            cx, cy = pts[i]
            nx, ny = pts[(i + 1) % n]
            mx = (cx + nx) / 2.0
            my = (cy + ny) / 2.0
            pen.qCurveTo(to_svg(cx, cy), to_svg(mx, my))
        pen.closePath()
        return
    # 旋转使首个 on-curve 在索引 0
    k = on_idx[0]
    pts = pts[k:] + pts[:k]
    tags = tags[k:] + tags[:k]
    n = len(pts)
    pen.moveTo(to_svg(*pts[0]))
    i = 1
    while i < n:
        if tags[i]:
            pen.lineTo(to_svg(*pts[i]))
            i += 1
        else:
            ctrl = pts[i]
            i += 1
            while i < n and not tags[i]:
                nxt = pts[i]
                mx = (ctrl[0] + nxt[0]) / 2.0
                my = (ctrl[1] + nxt[1]) / 2.0
                pen.qCurveTo(to_svg(*ctrl), to_svg(mx, my))
                ctrl = nxt
                i += 1
            if i < n:
                pen.qCurveTo(to_svg(*ctrl), to_svg(*pts[i]))
                i += 1
            else:
                pen.qCurveTo(to_svg(*ctrl), to_svg(*pts[0]))
    pen.closePath()


def render_text(content, attrs, pen, resolver, stats):
    """把一个 <text> 元素渲染为字形轮廓并绘制到 pen。"""
    chars = html.unescape(content).strip()
    if not chars:
        return
    x = _f(attrs.get('x'), 32.0)
    y = _f(attrs.get('y'), 32.0)
    size = _f(attrs.get('font-size'), 16.0)
    anchor = attrs.get('text-anchor', 'middle')
    baseline = attrs.get('dominant-baseline', 'central')
    if size <= 0:
        return

    # 预解析每个字符的字形
    glyph_infos = []  # (face, idx, outline, upem, advance_x)
    total_adv = 0.0
    for ch in chars:
        face, idx = resolver.get_glyph(ch)
        if idx == 0:
            stats['text_chars_missing'] += 1
            stats['missing_chars'].add(ch)
            glyph_infos.append(None)
            continue
        face.load_glyph(idx, freetype.FT_LOAD_NO_BITMAP | freetype.FT_LOAD_NO_SCALE)
        gl = face.glyph
        outline = gl.outline
        upem = face.units_per_EM
        adv = gl.advance.x if gl.advance.x else 0
        total_adv += adv
        glyph_infos.append((face, idx, outline, upem, adv))

    if total_adv <= 0:
        # 退化为单字符中心化
        total_adv = 0.0

    cum_adv = 0.0
    n_valid = sum(1 for g in glyph_infos if g)
    char_index = 0
    for gi in glyph_infos:
        if gi is None:
            continue
        face, idx, outline, upem, adv = gi
        scale = size / upem
        pts = outline.points
        if not pts:
            continue
        xs = [_ptxy(p)[0] for p in pts]
        ys = [_ptxy(p)[1] for p in pts]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        center_fx = (minx + maxx) / 2.0
        center_fy = (miny + maxy) / 2.0

        if n_valid == 1 and anchor == 'middle':
            # 单字符: bbox 中心对齐 (x, y)
            def to_svg(fx, fy, _x=x, _y=y, _cf=center_fx, _cfy=center_fy, _s=scale):
                return (_x + (fx - _cf) * _s, _y + (_cfy - fy) * _s)
        else:
            # 多字符: 左到右布局, 起点按 anchor 调整
            if anchor == 'middle':
                char_left = x - (total_adv * scale) / 2.0 + cum_adv * scale
            elif anchor == 'end':
                char_left = x - total_adv * scale + cum_adv * scale
            else:  # start
                char_left = x + cum_adv * scale

            def to_svg(fx, fy, _cl=char_left, _y=y, _minx=minx, _cfy=center_fy, _s=scale):
                return (_cl + (fx - _minx) * _s, _y + (_cfy - fy) * _s)

        draw_freetype_outline(outline, to_svg, pen)
        cum_adv += adv
        char_index += 1
    stats['text_elements_rendered'] += 1


# ----------------------------------------------------------------------------
# 字形构建
# ----------------------------------------------------------------------------
def build_glyph(svg_text, resolver, stats):
    """为单个 SVG 构建一个 TTGlyph。"""
    frame_inner, symbol_inner = extract_groups(svg_text)
    tpen = TTGlyphPen(None)
    # Cu2QuPen: 把 SVG 弧线转换产生的三次贝塞尔转为二次 (TrueType 要求)
    qpen = Cu2QuPen(tpen, max_err=1.0)
    xpen = TransformPen(qpen, MATRIX)

    # 矢量元素 (frame + symbol)
    for inner in (frame_inner, symbol_inner):
        if not inner:
            continue
        for m in VEC_ELEM_RE.finditer(inner):
            tag = m.group(1)
            attrs = parse_attrs(m.group(2))
            d = elem_to_path_d(tag, attrs)
            if not d:
                continue
            p = pathops.Path()
            try:
                parse_path(d, p.getPen())
            except Exception as exc:  # noqa: BLE001
                stats['path_parse_errors'] += 1
                continue
            filled = is_filled_element(attrs)
            if filled:
                # 填充: 仅转换可能的 conic (圆弧) 为 quad
                try:
                    p.convertConicsToQuads()
                except Exception:  # noqa: BLE001
                    pass
            else:
                # 描边: stroke -> fill
                width = _f(attrs.get('stroke-width'), STROKE_WIDTH)
                if width <= 0:
                    width = STROKE_WIDTH
                try:
                    p.stroke(width, cap=STROKE_CAP, join=STROKE_JOIN,
                             miter_limit=STROKE_MITER)
                    p.convertConicsToQuads()
                except Exception as exc:  # noqa: BLE001
                    stats['stroke_errors'] += 1
                    continue
            try:
                p.draw(xpen)
            except Exception as exc:  # noqa: BLE001
                stats['draw_errors'] += 1
        # 文本元素 (只在当前 inner 里查找)
        for tm in TEXT_ELEM_RE.finditer(inner):
            attrs = parse_attrs(tm.group(1))
            content = tm.group(2)
            render_text(content, attrs, xpen, resolver, stats)

    return tpen.glyph()


# ----------------------------------------------------------------------------
# 字体组装
# ----------------------------------------------------------------------------
def sanitize_glyph_name(node_id):
    # 字形名仅允许 [A-Za-z0-9_], 其他替换为 _
    return re.sub(r'[^A-Za-z0-9_]', '_', node_id)


def build_font():
    print('=' * 70)
    print('Icon Font 构建 (fonttools + skia-pathops + freetype-py)')
    print('=' * 70)
    files = sorted(f for f in os.listdir(SYMBOLS_DIR) if f.lower().endswith('.svg'))
    if not files:
        print('[error] assets/symbols/ 下没有 .svg 文件')
        sys.exit(1)
    print('SVG 文件数: {}'.format(len(files)))

    resolver = FontResolver(SYSTEM_FONTS)
    print('已加载系统字体: {} 个'.format(len(resolver.faces)))

    # 字形名 (去重防冲突)
    glyph_names = []          # 顺序 (含 .notdef)
    name_to_node = {}         # glyph_name -> node_id
    node_to_name = {}         # node_id -> glyph_name
    used_names = set()
    for f in files:
        node_id = os.path.splitext(f)[0]
        gname = sanitize_glyph_name(node_id)
        if gname in used_names:
            # 冲突: 追加数字后缀
            i = 2
            while '{}_{}'.format(gname, i) in used_names:
                i += 1
            gname = '{}_{}'.format(gname, i)
            print('  [warn] 字形名冲突, 重命名 {} -> {}'.format(node_id, gname))
        used_names.add(gname)
        glyph_names.append(gname)
        node_to_name[node_id] = gname
        name_to_node[gname] = node_id

    stats = {
        'path_parse_errors': 0,
        'stroke_errors': 0,
        'draw_errors': 0,
        'text_elements_rendered': 0,
        'text_chars_missing': 0,
        'missing_chars': set(),
        'empty_glyphs': 0,
    }

    # 构建所有字形
    glyphs = {}                  # glyph_name -> TTGlyph
    codepoints = {}             # node_id -> int codepoint
    cmap = {}                   # codepoint -> glyph_name
    cp = FIRST_CODEPOINT
    print('-' * 70)
    print('构建字形...')
    for idx, fname in enumerate(files):
        node_id = os.path.splitext(fname)[0]
        gname = node_to_name[node_id]
        fpath = os.path.join(SYMBOLS_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as fh:
                svg_text = fh.read()
        except Exception as exc:  # noqa: BLE001
            print('  [error] 读取 {} 失败: {}'.format(fname, exc))
            glyphs[gname] = TTGlyphPen(None).glyph()  # 空
        glyph = build_glyph(svg_text, resolver, stats)
        # 检查空字形
        try:
            if glyph.numberOfContours == 0:
                stats['empty_glyphs'] += 1
        except Exception:  # noqa: BLE001
            pass
        glyphs[gname] = glyph
        codepoints[node_id] = cp
        cmap[cp] = gname
        cp += 1
        if (idx + 1) % 100 == 0:
            print('  已处理 {}/{}'.format(idx + 1, len(files)))

    print('  完成, 共 {} 个字形'.format(len(glyphs)))

    # .notdef 空字形
    notdef = TTGlyphPen(None).glyph()

    # 水平度量: advance = UPEM, lsb = glyph.xMin (兜底 0)
    metrics = {}
    metrics['.notdef'] = (UPEM, 0)
    for gname in glyph_names:
        g = glyphs[gname]
        try:
            lsb = int(round(g.xMin))
        except Exception:  # noqa: BLE001
            lsb = 0
        metrics[gname] = (UPEM, max(0, lsb))

    print('-' * 70)
    print('组装字体表...')
    fb = FontBuilder(unitsPerEm=UPEM, isTTF=True)
    fb.setupGlyphOrder(['.notdef'] + glyph_names)
    fb.setupCharacterMap(cmap)
    glyf_table = {'.notdef': notdef}
    glyf_table.update(glyphs)
    fb.setupGlyf(glyf_table)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupNameTable({
        'familyName': FONT_FAMILY,
        'styleName': 'Regular',
    })
    fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=DESCENT, sTypoLineGap=0,
                usWinAscent=ASCENT, usWinDescent=abs(DESCENT))
    fb.setupPost()
    fb.setupHead(unitsPerEm=UPEM)
    font = fb.font

    # 保存 TTF
    font.save(OUT_TTF)
    ttf_size = os.path.getsize(OUT_TTF)
    print('  TTF  : {} ({} 字节, {:.2f} KB)'.format(OUT_TTF, ttf_size, ttf_size / 1024.0))

    # WOFF
    try:
        wf = TTFont(OUT_TTF)
        wf.flavor = 'woff'
        wf.save(OUT_WOFF)
        woff_size = os.path.getsize(OUT_WOFF)
        print('  WOFF : {} ({} 字节, {:.2f} KB)'.format(OUT_WOFF, woff_size, woff_size / 1024.0))
    except Exception as exc:  # noqa: BLE001
        print('  [error] WOFF 生成失败: {}'.format(exc))

    # WOFF2 (需要 brotli)
    try:
        import brotli  # noqa: F401
        wf2 = TTFont(OUT_TTF)
        wf2.flavor = 'woff2'
        wf2.save(OUT_WOFF2)
        woff2_size = os.path.getsize(OUT_WOFF2)
        print('  WOFF2: {} ({} 字节, {:.2f} KB)'.format(OUT_WOFF2, woff2_size, woff2_size / 1024.0))
    except ImportError:
        print('  [skip] WOFF2 跳过: 未安装 brotli')
    except Exception as exc:  # noqa: BLE001
        print('  [error] WOFF2 生成失败: {}'.format(exc))

    # codepoints.json
    with open(OUT_CODEPOINTS, 'w', encoding='utf-8') as fh:
        json.dump(codepoints, fh, ensure_ascii=False, indent=2, sort_keys=True)
    cp_size = os.path.getsize(OUT_CODEPOINTS)
    print('  JSON : {} ({} 字节, {} 项)'.format(OUT_CODEPOINTS, cp_size, len(codepoints)))

    # CSS (FontAwesome 风格)
    css = []
    css.append('/* MTF Icons - Icon Font CSS (自动生成, 勿手动编辑) */')
    css.append('/* 用法: <i class="mtf-font mtf-mt_yJmvUCCym7"></i> */')
    css.append('')
    css.append('@font-face {')
    css.append("  font-family: '{}';".format(FONT_FAMILY))
    css.append("  src: url('mtf.woff2') format('woff2'),")
    css.append("       url('mtf.woff') format('woff'),")
    css.append("       url('mtf.ttf') format('truetype');")
    css.append('  font-weight: normal;')
    css.append('  font-style: normal;')
    css.append('  font-display: block;')
    css.append('}')
    css.append('')
    css.append('.mtf-font {')
    css.append("  font-family: '{}';".format(FONT_FAMILY))
    css.append('  font-style: normal;')
    css.append('  font-weight: normal;')
    css.append('  font-variant: normal;')
    css.append('  text-rendering: auto;')
    css.append('  -webkit-font-smoothing: antialiased;')
    css.append('  display: inline-block;')
    css.append('  font-size: 1em;')
    css.append('  line-height: 1;')
    css.append('  vertical-align: middle;')
    css.append('}')
    css.append('')
    css.append('/* 各节点图标类 (通过 ::before content 引用 PUA 码点) */')
    index_map = {}
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, 'r', encoding='utf-8') as fh:
                index_map = {r['id']: r for r in json.load(fh).get('records', [])}
        except Exception:  # noqa: BLE001
            pass
    for node_id in codepoints:
        cpv = codepoints[node_id]
        rec = index_map.get(node_id, {})
        name_zh = rec.get('name_zh', '')
        cmt = '  /* {} */'.format(name_zh) if name_zh else ''
        css.append('.mtf-{}::before {{'.format(node_id))
        css.append('  content: "\\{:X}";'.format(cpv))
        css.append('}}{}'.format(cmt))
    css_text = '\n'.join(css) + '\n'
    with open(OUT_CSS, 'w', encoding='utf-8') as fh:
        fh.write(css_text)
    css_size = os.path.getsize(OUT_CSS)
    print('  CSS  : {} ({} 字节, {:.2f} KB)'.format(OUT_CSS, css_size, css_size / 1024.0))

    # 统计
    print('-' * 70)
    print('统计:')
    print('  字形总数 (含 .notdef): {}'.format(len(glyph_names) + 1))
    print('  码点范围: U+{:04X} .. U+{:04X}'.format(FIRST_CODEPOINT, cp - 1))
    print('  文本元素渲染: {}'.format(stats['text_elements_rendered']))
    print('  缺失字符 (跳过): {} {}'.format(
        stats['text_chars_missing'],
        ', '.join("'{}'(U+{:04X})".format(c, ord(c)) for c in sorted(stats['missing_chars']))
        if stats['missing_chars'] else ''))
    print('  路径解析错误: {}'.format(stats['path_parse_errors']))
    print('  描边错误    : {}'.format(stats['stroke_errors']))
    print('  绘制错误    : {}'.format(stats['draw_errors']))
    print('  空字形      : {}'.format(stats['empty_glyphs']))

    # 校验
    print('-' * 70)
    print('校验:')
    ok = True
    if len(glyphs) == len(files):
        print('  字形数 == SVG 数 ({}): PASS'.format(len(files)))
    else:
        ok = False
        print('  字形数 == SVG 数: FAIL ({} vs {})'.format(len(glyphs), len(files)))
    if len(codepoints) == len(files):
        print('  码点数 == SVG 数 ({}): PASS'.format(len(files)))
    else:
        ok = False
        print('  码点数 == SVG 数: FAIL ({} vs {})'.format(len(codepoints), len(files)))
    if os.path.exists(OUT_TTF):
        print('  TTF 已生成: PASS')
    else:
        ok = False
        print('  TTF 已生成: FAIL')
    print('=' * 70)
    print('完成。' if ok else '完成 (存在校验失败, 请检查上方日志)。')
    return stats


if __name__ == '__main__':
    build_font()
