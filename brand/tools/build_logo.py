import re, sys, json
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

SP = sys.argv[1]; OUT = sys.argv[2]
src = open(f'{SP}/pdf/p1.svg', encoding='utf-8').read()
body = src.split('</defs>', 1)[1]
paths = re.findall(r'<path fill-rule="nonzero" fill="rgb\(100%, 100%, 100%\)"[^>]*d="([^"]+)"', body)
# ignore the title text: the cover symbol sits above y=340 in page units
def nums(d): return [float(n) for n in re.findall(r'-?\d+\.?\d*', d)]
sym = []
for d in paths:
    n = nums(d); ys = n[1::2]
    if max(ys) < 345: sym.append(d)
xs = [v for d in sym for v in nums(d)[0::2]]; ys = [v for d in sym for v in nums(d)[1::2]]
bx0, by0, bx1, by1 = min(xs), min(ys), max(xs), max(ys)
print('symbol paths', len(sym), 'bbox', bx0, by0, bx1, by1, file=sys.stderr)
sw, sh = bx1 - bx0, by1 - by0

def glyph_path(font_file, text, size, x, baseline, tracking=0):
    f = TTFont(font_file); gs = f.getGlyphSet(); cmap = f.getBestCmap(); upm = f['head'].unitsPerEm
    hmtx = f['hmtx']; s = size / upm
    pen = SVGPathPen(gs); cx = x
    for ch in text:
        g = cmap[ord(ch)]
        tp = TransformPen(pen, (s, 0, 0, -s, cx, baseline))
        gs[g].draw(tp)
        cx += hmtx[g][0] * s + tracking
    return pen.getCommands(), cx

def cap(font_file):
    f = TTFont(font_file); return f['OS/2'].sCapHeight / f['head'].unitsPerEm

P = json.loads(sys.argv[3])
# geometry in PNG pixel units (symbol height 138 = full logo height)
scale = P['symH'] / sh
R = TTFont  # noqa
reg = f'{SP}/fonts/x/selawk.ttf'; lig = f'{SP}/fonts/x/selawkl.ttf'
s1 = P['cap1'] / cap(reg); s2 = P['cap2'] / cap(lig)
l1, end1 = glyph_path(reg, 'EURADON -', s1, P['x1'], P['base1'], P['tr1'])
l2, end2 = glyph_path(lig, 'Verein Europäische Radonheilbäder e. V.', s2, P['x2'], P['base2'], P['tr2'])
print('line ends', round(end1,1), round(end2,1), file=sys.stderr)
W = max(end2, end1) + 2; H = P['symH']

def sym_group(fill):
    return (f'<g fill="{fill}" transform="scale({scale:.6f}) translate({-bx0:.4f} {-by0:.4f})">'
            + ''.join(f'<path d="{d.strip()}"/>' for d in sym) + '</g>')

def svg(w, h, inner, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.2f} {h:.2f}" width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{inner}</svg>\n')

T = 'EURADON – Verein Europäische Radonheilbäder e. V.'
for name, col in [('blau', '#1465B7'), ('weiss', '#FFFFFF'), ('schwarz', '#000000')]:
    open(f'{OUT}/euradon-logo-{name}.svg', 'w').write(svg(W, H, sym_group(col) + f'<g fill="{col}"><path d="{l1}"/><path d="{l2}"/></g>', T))
    open(f'{OUT}/euradon-zeichen-{name}.svg', 'w').write(svg(sw*scale, H, sym_group(col), 'EURADON Bildzeichen'))
json.dump({'W': round(W, 2), 'H': H, 'SW': round(sw * scale, 2),
           'sym': sym_group('currentColor'), 'words': f'<g fill="currentColor"><path d="{l1}"/><path d="{l2}"/></g>'},
          open(f'{OUT}/fragments.json', 'w'))
