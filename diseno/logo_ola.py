"""Silueta de la ola del logo de Gravity Wave (imagotipo) como polígono shapely, en mm."""
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon
from shapely import affinity
import contourpy

ICON = "/root/.claude/skills/synced/d7aa75cd-e11c-4add-92e9-f84caa64de54_593730d0-f659-4351-a80d-c95e15f0e911/gravity-wave-propuestas/assets/logo-gravity-icono.png"

def silueta(ancho_mm=40.0, simplificar=0.15):
    im = Image.open(ICON).convert("RGBA")
    a = np.asarray(im)[..., 3] > 128
    # rellenar huecos interiores (las escamas): flood fill del fondo desde el borde
    m = Image.fromarray((~a).astype("uint8") * 255)  # fondo=255
    m2 = Image.new("L", (m.width + 2, m.height + 2), 255); m2.paste(m, (1, 1))
    ImageDraw.floodfill(m2, (0, 0), 128)
    bg = np.asarray(m2)[1:-1, 1:-1] == 128
    filled = ~bg
    H, W = filled.shape
    cg = contourpy.contour_generator(z=filled.astype(float))
    lines = cg.lines(0.5)
    polys = [Polygon([(x, H - y) for x, y in l]) for l in lines if len(l) > 3]
    polys = [p.buffer(0) for p in polys if p.is_valid or True]
    g = max(polys, key=lambda p: p.area)
    s = ancho_mm / W
    g = affinity.scale(g, s, s, origin=(0, 0))
    g = g.simplify(simplificar)
    minx, miny, _, _ = g.bounds
    return affinity.translate(g, -minx, -miny)

if __name__ == "__main__":
    g = silueta()
    print(g.bounds, g.area, len(g.exterior.coords), len(g.interiors))
