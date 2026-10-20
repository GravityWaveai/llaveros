"""10 propuestas de silueta de ola para llavero Gravitec (envolvente ~40 mm).
Geometría construida con arcos y curvas suaves; después un 'cierre' morfológico R4,5
garantiza que toda concavidad sea mecanizable con fresa Ø9."""
import math
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union, nearest_points
from shapely import affinity

R = 4.5          # radio cóncavo mínimo (fresa Ø9)
HOLE = 4.5       # taladro anilla
Q = 48

def C(x, y, r): return Point(x, y).buffer(r, Q)
def rr(x, y, w, h, r): return box(x + r, y + r, x + w - r, y + h - r).buffer(r, Q)
def mill(g): return g.buffer(R, Q).buffer(-R, Q)
def soften(g, r=1.2): return g.buffer(-r, Q).buffer(r, Q)
def arc(cx, cy, r, a0, a1, n=60):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
def bez(p0, p1, p2, p3, n=40):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return out
def fit(g, size=40.0):
    minx, miny, maxx, maxy = g.bounds
    s = size / max(maxx - minx, maxy - miny)
    g = affinity.scale(g, s, s, origin=(0, 0)); minx, miny, _, _ = g.bounds
    return affinity.translate(g, -minx, -miny), s, (minx, miny)

def ola_clasica(cx=19, cy=22, Ro=18, w=7.5, a_end=215, base_h=7, floor=5, W=40):
    """Ola con cresta enrollada a la izquierda y base plana. Polígono CCW."""
    Ri = Ro - w
    pts = [(0, 0), (W, 0), (W, base_h)]
    a0 = -12
    p_arc0 = (cx + Ro * math.cos(math.radians(a0)), cy + Ro * math.sin(math.radians(a0)))
    pts += bez((W, base_h), (W, base_h + 6), (p_arc0[0] + 4, p_arc0[1] - 6), p_arc0)[1:]
    pts += arc(cx, cy, Ro, a0, a_end, 90)[1:]
    tip = arc(cx, cy, Ri, a_end, a_end, 1)
    pts += tip
    pts += arc(cx, cy, Ri, a_end, -70, 90)[1:]
    pe = pts[-1]
    pts += bez(pe, (pe[0] - 3, floor + 1), (10, floor), (3, floor))[1:]
    pts += [(0, floor)]
    return Polygon(pts).buffer(0)

# ---------- diseños ----------
def d01():
    g = ola_clasica()
    return g, (6, 10), "01", "Ola clásica", "La ola de siempre: cresta enrollada a la izquierda sobre base plana. Taladro en la base, bajo el tubo."
def d02():
    body = ola_clasica(a_end=330, floor=3)
    g = body.union(C(19, 22, 18).intersection(box(0, 0, 40, 40))).difference(C(19, 22, 6.5))
    g = unary_union([g, box(0, 0, 40, 6)])
    return g, None, "02", "Ola barril", "El tubo es un agujero cerrado Ø13: la anilla pasa por el barril de la ola. Sin taladro."
def d03():
    disc = C(20, 20, 20)
    sea = [(-5, 50), (45, 50), (45, 33)]
    sea += [(x, 33 - 3.2 * math.sin((x) / 40 * 2 * math.pi * 1.5)) for x in range(45, -6, -1)]
    g = disc.difference(Polygon(sea))
    return g, (20, 10), "03", "Horizonte", "Moneda Ø40 con el mar ondulado como borde superior. Superficie amplia para grabado."
def d04():
    a = ola_clasica(cx=10, cy=14, Ro=10, w=4.8, a_end=200, base_h=5, floor=3, W=22)
    b = affinity.translate(a, 19, 0)
    g = unary_union([a, b, box(0, 0, 41, 4)])
    return g, (36, 7), "04", "Doble cresta", "Dos crestas pequeñas sobre la misma base: lectura de oleaje, formato apaisado."
def d05():
    base = rr(0, 10, 40, 30, 4)
    sea = [(-5, -5), (45, -5), (45, 10)] + [(x, 10 - 3.5 * math.sin(x / 40 * 2 * math.pi * 1.5)) for x in range(45, -6, -1)]
    g = base.union(box(0, 0, 40, 12)).difference(Polygon(sea))
    return g, (20, 34), "05", "Etiqueta mar", "Placa tipo tag con la base ondulada. La más sencilla y la mejor para grabar logo o texto."
def d06():
    Ro, Ri = 16, 6.5; cx, cy = 20, 22
    pts = arc(cx, cy, Ro, 100, 100 - 300, 120)          # exterior, sentido horario desde arriba
    pts += arc(cx, cy, Ri, 100 - 300, 100, 120)         # interior de vuelta
    curl = Polygon(pts).buffer(0)
    tail = Polygon(bez((cx + Ro * math.cos(math.radians(100)), cy + Ro * math.sin(math.radians(100))), (28, 42), (38, 36), (40, 26)) +
                   bez((40, 26), (36, 30), (30, 34), (cx + Ri * math.cos(math.radians(100)), cy + Ri * math.sin(math.radians(100)))))
    g = curl.union(tail.buffer(0)).difference(C(cx, cy, Ri))
    return g, None, "06", "Espiral", "Rizo puro: la ola enrollada sobre sí misma con el hueco central como paso de anilla."
def d07():
    sq = rr(0, 0, 40, 40, 7)
    cut = ola_clasica(cx=24, cy=22, Ro=15, w=6.5, a_end=215, base_h=6, floor=4, W=40)
    cut = affinity.scale(cut, 0.78, 0.78, origin=(0, 0)); cut = affinity.translate(cut, 13, 4)
    g = sq.difference(cut.difference(box(0, 0, 13.1, 40)))
    g = sq.difference(affinity.translate(cut, 0, 0))
    return g, (7, 33), "07", "Cuadrado ola", "Cuadrado redondeado con la ola clásica recortada: la silueta se lee en negativo."
def d08():
    path = [(3, 5), (10, 3), (18, 8), (24, 18)] + arc(30, 26, 9, -110, 200, 40)
    stroke = LineString(path).buffer(5.5, Q)
    g = stroke.difference(C(30, 26, 3.6)).union(C(30, 26, 9).buffer(0).difference(C(30, 26, 3.6)).intersection(stroke.buffer(1)))
    g = stroke
    return g, (6, 6), "08", "Trazo ola", "Una sola línea gruesa que sube y se enrolla: la más minimalista y ligera."
def d09():
    drop = Polygon(bez((20, 40), (8, 30), (0, 22), (0, 15)) + arc(20, 15, 20, 180, 360, 60) + bez((40, 15), (40, 22), (32, 30), (20, 40)))
    hollow = ola_clasica(cx=16, cy=16, Ro=13, w=5.5, a_end=215, base_h=4, floor=3, W=40)
    tube = C(16, 16, 13 - 5.5)
    # hueco: interior del tubo abierto hacia abajo-izquierda
    mouth = Polygon([(16, 16), (16 + 20 * math.cos(math.radians(215)), 16 + 20 * math.sin(math.radians(215))), (16 + 20 * math.cos(math.radians(290)), 16 + 20 * math.sin(math.radians(290)))])
    g = drop.difference(tube.union(mouth.intersection(C(16, 16, 11))))
    return g, (20, 34), "09", "Gota ola", "Gota de agua con un tubo de ola abierto en su interior. La punta de la gota lleva la anilla."
def d10():
    disc = C(20, 20, 20)
    cut = ola_clasica(cx=22, cy=20, Ro=12, w=6, a_end=215, base_h=4, floor=3, W=40)
    hollow = C(22, 20, 6).union(Polygon([(22, 20), (22 + 25 * math.cos(math.radians(200)), 20 + 25 * math.sin(math.radians(200))), (22 + 25 * math.cos(math.radians(290)), 20 + 25 * math.sin(math.radians(290)))]).intersection(C(22, 20, 12)))
    g = disc.difference(hollow)
    return g, (20, 33), "10", "Disco ola", "Moneda Ø40 con el tubo de la ola recortado por dentro: ola en negativo, muy gráfico."

DESIGNS = [d01, d02, d03, d04, d05, d06, d07, d08, d09, d10]

def best_hole(g, pref):
    core = g.buffer(-(HOLE / 2 + 2.6))
    if core.is_empty: return None
    p = Point(pref)
    if core.contains(p): return pref
    q = nearest_points(core.buffer(-0.1), p)[0]
    return (round(q.x, 2), round(q.y, 2))

def build():
    out = []
    for fn in DESIGNS:
        g, hole, code, name, desc = fn()
        g = mill(soften(g))
        g, s, (mx, my) = fit(g)
        if hole:
            hole = best_hole(g, ((hole[0] * s) - mx, (hole[1] * s) - my))
        out.append(dict(code=code, name=name, desc=desc, geom=g, hole=hole))
    return out

def qa(g, hole):
    rep = {}
    void = g.envelope.buffer(27).difference(g)
    r = R - 0.03
    miss = void.difference(void.buffer(-r, 32).buffer(r, 32))
    rep["inaccesible_mm2"] = round(sum(x.area for x in getattr(miss, "geoms", [miss]) if x.area > 0.3), 2)
    thin = g.difference(g.buffer(-2.5, join_style="mitre", mitre_limit=10).buffer(2.5, join_style="mitre", mitre_limit=10))
    rep["zonas_finas_mm2"] = round(sum(x.area for x in getattr(thin, "geoms", [thin]) if x.area > 1.0), 2)
    rep["caras"] = len(getattr(g, "geoms", [g]))
    rep["huecos"] = sum(len(p.interiors) for p in getattr(g, "geoms", [g]))
    if hole:
        rep["taladro_ok"] = g.contains(Point(hole).buffer(HOLE / 2 + 2.5))
    minx, miny, maxx, maxy = g.bounds
    rep["envolvente"] = (round(maxx - minx, 1), round(maxy - miny, 1))
    rep["area_cm2"] = round(g.area / 100, 2)
    return rep

if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    ds = build()
    fig, axs = plt.subplots(2, 5, figsize=(20, 9))
    for ax, d in zip(axs.flat, ds):
        q = qa(d["geom"], d["hole"]); print(d["code"], d["name"], d["hole"], q)
        for p in getattr(d["geom"], "geoms", [d["geom"]]):
            ax.fill(*p.exterior.xy, color="#3d796f")
            for h in p.interiors: ax.fill(*h.xy, color="white")
        if d["hole"]:
            ax.add_patch(plt.Circle(d["hole"], HOLE / 2, color="white"))
        ax.set_aspect("equal"); ax.set_xlim(-2, 42); ax.set_ylim(-2, 42); ax.set_title(f"{d['code']} {d['name']}  inac={q['inaccesible_mm2']} fin={q['zonas_finas_mm2']}", fontsize=9); ax.grid(alpha=.3)
    plt.tight_layout(); plt.savefig("preview.png", dpi=70)
