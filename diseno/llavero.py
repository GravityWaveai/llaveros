"""Llavero ola de la foto: silueta calcada de la imagen, 40 mm de ancho. Limpieza mínima:
base recta, esquina inferior derecha (tapada por la anilla en la foto) y lóbulo con taladro."""
import math, sys; sys.path.insert(0, ".")
from shapely.geometry import Polygon, Point, box, LineString
from shapely.ops import unary_union
from shapely import affinity
from calco import silueta

HOLE = 3.5             # taladro anilla (mm)
R_CONC = 1.0           # radio cóncavo mínimo que se respeta en la geometría (boca del tubo ~3 mm)
def C(x, y, r): return Point(x, y).buffer(r, 64)

def chaikin(coords, n=3):
    pts = list(coords)[:-1]
    for _ in range(n):
        out = []
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            out.append((0.75*p[0] + 0.25*q[0], 0.75*p[1] + 0.25*q[1])); out.append((0.25*p[0] + 0.75*q[0], 0.25*p[1] + 0.75*q[1]))
        pts = out
    return Polygon(pts).buffer(0)

def pieza():
    g = silueta()
    g = chaikin(g.simplify(0.25).exterior.coords, 3)        # suavizar el escalonado de la máscara
    g = g.intersection(box(-5, 1.2, 45, 60)); g = affinity.translate(g, 0, -1.2)      # base recta
    g = g.difference(box(36.8, -1, 45, 7.5))                                           # sombra de la anilla
    nub_c = (36.3, 9.6); nub_r = 4.6
    xr, rc = nub_c[0] + nub_r, 3.0                                                                 # esquina inferior derecha (tapada por la anilla)
    corner = unary_union([box(30, 0, xr - rc, nub_c[1]), box(30, rc, xr, nub_c[1]), C(xr - rc, rc, rc)])
    g = unary_union([g, C(*nub_c, nub_r), corner])
    g = g.buffer(-0.8, 64).buffer(0.8, 64)                  # convexo suave
    g = g.buffer(R_CONC, 64).buffer(-R_CONC, 64)            # cóncavo >= R1
    if g.geom_type != "Polygon": g = max(g.geoms, key=lambda p: p.area)
    minx, miny, maxx, maxy = g.bounds; s = 40.0 / (maxx - minx)
    g = affinity.translate(affinity.scale(g, s, s, origin=(0, 0)), -minx * s, -miny * s)
    hole = (round((nub_c[0] - minx) * s, 2), round((nub_c[1] - miny) * s, 2))
    return g.simplify(0.03), hole

def medidas(g, hole):
    """Medidas características para el plano."""
    minx, miny, maxx, maxy = g.bounds
    void = g.envelope.buffer(5).difference(g)
    conc = g.convex_hull.difference(g)
    tube = [p for p in getattr(conc, "geoms", [conc]) if p.contains(Point(27, 21))][0]
    tube = tube.intersection(Point(27, 21).buffer(7.5))     # solo el hueco, sin la boca
    outside = void.difference(tube.buffer(0.3))
    tb = tube.bounds
    # boca: anchura mínima del canal entre el labio y el cuerpo (distancia entre las dos orillas)
    # se mide como el diámetro máximo de disco que pasa: buscar r tal que void.buffer(-r) siga conectando
    lo, hi = 0.5, 6.0
    for _ in range(20):
        r = (lo + hi) / 2
        er = void.buffer(-r, 32)
        parts = list(getattr(er, "geoms", [er]))
        inside = [p for p in parts if p.intersects(tube.buffer(-0.5))]
        connected = any(p.area > 0.5 * outside.area for p in inside)
        if connected: lo = r
        else: hi = r
    boca = round(2 * lo, 1)
    xs, ys = g.exterior.xy
    top = max(zip(ys, xs)); 
    return dict(ancho=round(maxx - minx, 1), alto=round(maxy - miny, 1), tubo=(round((tb[0]+tb[2])/2, 1), round((tb[1]+tb[3])/2, 1), round(tb[2]-tb[0], 1), round(tb[3]-tb[1], 1)),
                boca=boca, cresta=(round(top[1], 1), round(top[0], 1)), taladro=hole, area=round(g.area/100, 2))

if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    from PIL import Image
    g, hole = pieza(); m = medidas(g, hole); print(m, len(g.exterior.coords))
    fig, ax = plt.subplots(1, 2, figsize=(14, 7))
    im = Image.open("/tmp/claude-0/-home-user/aa34e208-6da2-580b-b6a1-5ef1ac47aede/images/2.png"); ax[0].imshow(im); ax[0].set_title("foto")
    ax[1].fill(*g.exterior.xy, color="#2f6b62"); ax[1].add_patch(Circle(hole, HOLE/2, color="w"))
    ax[1].set_aspect("equal"); ax[1].grid(alpha=.3); ax[1].set_xlim(-2, 42); ax[1].set_ylim(-2, 40); ax[1].set_title("silueta 40 mm")
    plt.savefig("llavero.png", dpi=80)
