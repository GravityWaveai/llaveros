"""Trazado de siluetas con curvas (Bézier cúbicas, arcos, líneas) -> polígono shapely. mm."""
import math
from shapely.geometry import Polygon, Point
from shapely import affinity

def _bez(p0, p1, p2, p3, n=40):
    out = []
    for i in range(1, n + 1):
        t = i / n; u = 1 - t
        out.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return out

def _arc(c, r, a0, a1, n=None):
    n = n or max(8, int(abs(a1 - a0) / 3))
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(1, n + 1)]

def path(start, segs):
    """segs: ('L', (x,y)) · ('C', c1, c2, (x,y)) · ('A', center, r, a0, a1) [el punto actual debe estar en a0]
    · ('T', (x,y), tension) = curva suave hacia (x,y) usando la tangente de salida anterior."""
    pts = [start]; last_tan = None
    for s in segs:
        p0 = pts[-1]
        if s[0] == 'L':
            pts.append(s[1]); last_tan = (s[1][0]-p0[0], s[1][1]-p0[1])
        elif s[0] == 'C':
            pts += _bez(p0, s[1], s[2], s[3]); last_tan = (s[3][0]-s[2][0], s[3][1]-s[2][1])
        elif s[0] == 'A':
            c, r, a0, a1 = s[1:]
            pts += _arc(c, r, a0, a1)
            sgn = 1 if a1 > a0 else -1
            last_tan = (-math.sin(math.radians(a1)) * sgn, math.cos(math.radians(a1)) * sgn)
    return Polygon(pts).buffer(0)

def C(x, y, r): return Point(x, y).buffer(r, 64)
def rr(x, y, w, h, r):
    from shapely.geometry import box
    return box(x + r, y + r, x + w - r, y + h - r).buffer(r, 64)
def fit(g, w=None, h=None):
    minx, miny, maxx, maxy = g.bounds
    s = min(w / (maxx - minx) if w else 1e9, h / (maxy - miny) if h else 1e9)
    g = affinity.scale(g, s, s, origin=(0, 0)); minx, miny, _, _ = g.bounds
    return affinity.translate(g, -minx, -miny), s, (minx, miny)
