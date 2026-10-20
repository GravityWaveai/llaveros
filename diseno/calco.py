"""Calco de la silueta del llavero desde la foto (mask_fill.png) -> polígono en mm, 40 mm de ancho."""
import numpy as np, math
from PIL import Image
import contourpy
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity

PX_BASE = [(48, 476), (440, 498)]       # línea base de la cara superior en la foto (px)
NUB_C, NUB_R = (452, 372), 44            # lóbulo de la anilla (px) (la anilla tapa su lado derecho)
LEAN = 1.06                              # corrección de escorzo vertical (la pieza está inclinada hacia atrás)
W_MM = 40.0

def contorno_foto():
    m = np.asarray(Image.open("mask_fill.png")) > 128
    H, W = m.shape
    cg = contourpy.contour_generator(z=m.astype(float))
    lines = cg.lines(0.5)
    polys = [Polygon([(x, H - y) for x, y in l]).buffer(0) for l in lines if len(l) > 3]
    g = max(polys, key=lambda p: p.area)
    return g, H

def silueta():
    g, H = contorno_foto()
    (x0, y0), (x1, y1) = PX_BASE
    y0, y1 = H - y0, H - y1
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    g = affinity.rotate(g, -ang, origin=(x0, y0))         # base horizontal
    nub = affinity.rotate(Point(NUB_C[0], H - NUB_C[1]).buffer(NUB_R, 64), -ang, origin=(x0, y0))
    g = unary_union([g, nub])
    g = g.intersection(box(-1e4, y0, 1e4, 1e4))           # solo la cara superior (quitar canto y sombra)
    g = affinity.scale(g, 1, LEAN, origin=(x0, y0))
    g = g.simplify(1.5).buffer(3, 32).buffer(-6, 32).buffer(3, 32)   # suavizar ruido de la máscara
    if g.geom_type != "Polygon": g = max(g.geoms, key=lambda p: p.area)
    minx, miny, maxx, maxy = g.bounds
    s = W_MM / (maxx - minx)
    g = affinity.scale(g, s, s, origin=(0, 0)); minx, miny, _, _ = g.bounds
    g = affinity.translate(g, -minx, -miny)
    return g

if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    g = silueta(); print(g.bounds, g.area / 100, len(g.exterior.coords))
    fig, ax = plt.subplots(1, 2, figsize=(14, 7))
    im = Image.open("/tmp/claude-0/-home-user/aa34e208-6da2-580b-b6a1-5ef1ac47aede/images/2.png")
    ax[0].imshow(im); g0, H = contorno_foto(); ax[0].plot(*g0.exterior.xy, "r-", lw=1)
    ax[0].plot([PX_BASE[0][0], PX_BASE[1][0]], [PX_BASE[0][1], PX_BASE[1][1]], "y-")
    ax[0].add_patch(plt.Circle(NUB_C, NUB_R, fill=False, color="y")); ax[0].set_ylim(636, 0)
    ax[1].fill(*g.exterior.xy, color="#2f6b62"); ax[1].set_aspect("equal"); ax[1].grid(alpha=.3)
    plt.savefig("calco.png", dpi=80)
