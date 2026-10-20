"""Vectoriza el plano de referencia (3.webp): contorno exterior (línea central del trazo) y taladro.
Escala: altura total de la ola = 40 mm."""
import numpy as np, math
from PIL import Image
import scipy.ndimage as ndi
import contourpy
from shapely.geometry import Polygon, Point
from shapely import affinity

SRC = "/tmp/claude-0/-home-user/aa34e208-6da2-580b-b6a1-5ef1ac47aede/images/3.webp"
ALTO_MM = 40.0

def vectorizar():
    a = np.asarray(Image.open(SRC).convert("L")).astype(float)
    ink = a < 128
    ink[:, :255] = False                                   # cota y texto de la izquierda
    # grosor del trazo
    dt = ndi.distance_transform_edt(ink)
    lab, n = ndi.label(ink)
    sizes = ndi.sum(ink, lab, range(1, n + 1)); order = np.argsort(sizes)[::-1]
    outline = lab == order[0] + 1; hole = lab == order[1] + 1
    # quitar líneas de extensión (más finas que el trazo): apertura 3x3
    outline = ndi.binary_opening(outline, structure=np.ones((3, 3)))
    lab2, n2 = ndi.label(outline); s2 = ndi.sum(outline, lab2, range(1, n2 + 1)); outline = lab2 == (np.argmax(s2) + 1)
    filled = ndi.binary_fill_holes(outline)
    interior = filled & ~outline
    H = a.shape[0]
    def contour(mask, smooth=0.0):
        m = ndi.gaussian_filter(mask.astype(float), smooth) if smooth else mask.astype(float)
        lines = contourpy.contour_generator(z=m).lines(0.5)
        polys = [Polygon([(x, H - y) for x, y in l]).buffer(0) for l in lines if len(l) > 3]
        return max(polys, key=lambda p: p.area)
    g_in = contour(interior, 1.0)
    stroke = outline.sum() / g_in.exterior.length          # grosor medio del trazo (px)
    g = g_in.buffer(stroke / 2, 64)                        # línea central del trazo
    # taladro: círculo ajustado a la línea central del trazo
    ys, xs = np.nonzero(hole); cx, cy = xs.mean(), H - ys.mean()
    d = np.hypot(xs - cx, (H - ys) - cy); r_hole = d.mean()
    # escala y origen
    minx, miny, maxx, maxy = g.bounds
    s = ALTO_MM / (maxy - miny)
    g = affinity.translate(affinity.scale(g, s, s, origin=(0, 0)), -minx * s, -miny * s)
    hole_c = ((cx - minx) * s, (cy - miny) * s); hole_d = 2 * r_hole * s
    return g.simplify(0.01), hole_c, hole_d, dict(stroke_px=stroke, px_mm=1 / s)

if __name__ == "__main__":
    g, hc, hd, info = vectorizar()
    print(info, g.bounds, "taladro", hc, hd, "puntos", len(g.exterior.coords), "interiores", len(g.interiors))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 7)); ax.plot(*g.exterior.xy, "k-", lw=1); ax.add_patch(plt.Circle(hc, hd / 2, fill=False))
    ax.set_aspect("equal"); ax.grid(alpha=.3); plt.savefig("vector.png", dpi=80)
