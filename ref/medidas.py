"""Medidas de fabricación de la pieza vectorizada + comprobación CNC (fresa Ø9)."""
import math, numpy as np
from shapely.geometry import Point, Polygon, LineString, box
from vector import vectorizar

FRESA = 9.0; R_MIN = FRESA / 2

def fit_circle(pts):
    x = np.array([p[0] for p in pts]); y = np.array([p[1] for p in pts])
    A = np.c_[2*x, 2*y, np.ones(len(x))]; b = x**2 + y**2
    c, *_ = np.linalg.lstsq(A, b, rcond=None); cx, cy = c[0], c[1]; r = math.sqrt(c[2] + cx**2 + cy**2)
    return cx, cy, r

def medir(cnc=True):
    g, hc, hd, info = vectorizar()
    if cnc:   # geometría apta para fresa Ø9: cierre morfológico R4,5 (solo cambia las dos uniones de radio pequeño)
        from shapely.geometry.polygon import orient
        g0 = g
        g = orient(g.buffer(R_MIN + 0.12, 96).buffer(-(R_MIN + 0.12), 96).simplify(0.01), sign=1.0)   # R4,62: tras discretizar queda >= R4,5
        info["desv_cnc_mm"] = round(max(max(g.exterior.distance(Point(p)) for p in g0.exterior.coords), max(g0.exterior.distance(Point(p)) for p in g.exterior.coords)), 2)
        info["area_cnc_mm2"] = round(g.area - g0.area, 2)
    minx, miny, maxx, maxy = g.bounds
    pts = list(g.exterior.coords)
    # tubo: puntos del contorno dentro de la zona del hueco (ajuste por círculo)
    tube_pts = [p for p in pts if Point(p).distance(Point(28.8, 24.5)) < 7.3 and p[0] < 33.5]
    tcx, tcy, tr = fit_circle(tube_pts)
    # lóbulo de la anilla (arco exterior alrededor del taladro)
    nub_pts = [p for p in pts if 4.5 < Point(p).distance(Point(hc)) < 7.5 and p[1] > hc[1] - 2]
    ncx, ncy, nr = fit_circle(nub_pts)
    # boca del tubo: mayor disco que pasa desde fuera hasta el tubo
    void = g.envelope.buffer(10).difference(g)
    tube_zone = Point(tcx, tcy).buffer(tr * 0.6)
    lo, hi = 0.5, 10.0
    for _ in range(25):
        r = (lo + hi) / 2; er = void.buffer(-r, 32)
        parts = list(getattr(er, "geoms", [er]))
        ok = any(p.intersects(tube_zone) and p.area > 500 for p in parts)
        lo, hi = (r, hi) if ok else (lo, r)
    boca = 2 * lo
    # cresta, punta del labio, base
    top = max(pts, key=lambda p: p[1])
    base_pts = [p for p in pts if p[1] < 0.05]; base = (min(p[0] for p in base_pts), max(p[0] for p in base_pts))
    tip = max([p for p in pts if 27 < p[1] < 32 and p[0] > 34], key=lambda p: p[0])     # punto más a la derecha del labio
    # pared mínima al taladro
    pared = g.exterior.distance(Point(hc)) - hd / 2
    # --- comprobación CNC Ø9
    rr = R_MIN - 0.03
    miss = void.difference(void.buffer(-rr, 32).buffer(rr, 32))
    miss = [m for m in getattr(miss, "geoms", [miss]) if m.area > 0.3]
    thin = g.difference(g.buffer(-2.5, join_style="mitre", mitre_limit=10).buffer(2.5, join_style="mitre", mitre_limit=10))
    thin = [t for t in getattr(thin, "geoms", [thin]) if t.area > 1.0]
    return dict(g=g, hole=(round(hc[0], 2), round(hc[1], 2)), hole_d=round(hd, 2), ancho=round(maxx - minx, 2), alto=round(maxy - miny, 2),
                tubo=(round(tcx, 2), round(tcy, 2), round(2 * tr, 2)), lobulo=(round(ncx, 2), round(ncy, 2), round(nr, 2)),
                boca=round(boca, 2), cresta=(round(top[0], 2), round(top[1], 2)), base=(round(base[0], 2), round(base[1], 2)),
                labio=(round(tip[0], 2), round(tip[1], 2)), pared=round(pared, 2), area=round(g.area / 100, 2), info=info,
                cnc_inaccesible=[(round(m.area, 1), round(m.centroid.x, 1), round(m.centroid.y, 1)) for m in miss],
                finas=[(round(t.area, 1), round(t.centroid.x, 1), round(t.centroid.y, 1)) for t in thin])

if __name__ == "__main__":
    m = medir(); g = m.pop("g")
    for k, v in m.items(): print(k, v)
