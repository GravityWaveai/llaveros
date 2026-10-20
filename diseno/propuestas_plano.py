"""Lámina de propuestas en plano (dibujo de líneas) para el llavero ola. Estilo de la foto de referencia
(ola que rompe hacia la derecha, anilla abajo a la derecha) + variantes con la ola del logo de Gravity Wave."""
import math, sys, textwrap
sys.path.insert(0, ".")
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
from olas import C, rr, mill, soften, arc, R, HOLE, qa, best_hole, Q
from logo_ola import silueta
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

LOGO = silueta(40)
LG = LOGO.buffer(1.4, Q)       # ola del logo engrosada (ninguna zona < 5 mm)

def ref_wave(closed=False, nub=True):
    """Ola estilo foto de referencia: cresta que rompe a la derecha, tubo abierto hacia la derecha,
    lóbulo abajo-derecha para la anilla."""
    pts = [(2, 0), (38, 0), (40, 3), (40, 6)]
    if closed:
        pts += [(40, 10), (40, 18)]
    else:
        pts += [(36, 8), (33, 11)]
        pts += arc(27, 21, 6.5, -55, -340, 90)      # tubo (interior) en sentido horario
        pts += [(34, 19.5), (36.5, 18.5), (38.5, 20.5), (39.5, 23.5)]   # punta del labio
    pts += [(40, 27), (39, 31), (36, 34.5), (31, 37), (25, 37.5), (19, 35), (13, 30), (8, 22), (4, 12), (2, 4)]
    g = Polygon(pts).buffer(0)
    if closed:
        g = g.difference(C(27, 21, 6.5))
    return g

def p01():
    return ref_wave(), (35, 5), "Ola referencia", "Como la foto: cresta que rompe a la derecha, tubo abierto y lóbulo inferior derecho con taladro Ø4,5 para la anilla."
def p02():
    return ref_wave(), (35, 5), "Ola referencia + grabado", "Misma silueta con grabado opcional («1 kg») en la cara A: rebaje de 1 mm que deja ver el núcleo. Solo si se pide."
def p03():
    return ref_wave(closed=True), None, "Ola barril referencia", "Labio unido a la base: el tubo queda cerrado (Ø13) y es el paso de la anilla. Sin taladro, sin lóbulo."
def p04():
    return LG, (37, 4.5), "Ola logo GW", "Silueta de la ola del imagotipo, engrosada 1,4 mm para que nada baje de 5 mm. Taladro en el rizo del final."
def p05():
    return LG.union(C(34.5, 5.5, 5.5)), (34.5, 5.5), "Ola logo + lóbulo", "Ola del logo con lóbulo redondo abajo-derecha (como la referencia) para la anilla."
def p06():
    g = LG.union(C(27.5, 10.5, 8.5)).difference(C(27.5, 10.5, 5.5))
    return g, None, "Ola logo barril", "Ola del logo con el tubo cerrado: el hueco (Ø11) es el paso de la anilla."
def p07():
    g = affinity.translate(LG, 0, 13).union(rr(0, 0, 40, 15, 4))
    return g, (20, 6.5), "Ola logo sobre placa", "Ola del logo apoyada en una placa 40 x 15 con el taladro centrado. Formato ~40 x 38, sitio para texto."
def p08():
    cut = affinity.scale(LOGO, 0.6, 0.6, origin=(0, 0)); cut = affinity.translate(cut.buffer(3.0, Q), 5, 9)
    return rr(0, 0, 40, 40, 8).difference(cut), (20, 35), "Placa con ola logo", "Placa 40 x 40 con la ola del logo recortada en negativo (ventana pasante). Taladro arriba."
def p09():
    return LG.union(C(9.5, 20, 5.5)), (9.5, 20), "Ola logo con pestaña", "Ola del logo con pestaña redonda en el lomo de la cresta: cuelga con la cresta hacia arriba."
def p10():
    return affinity.scale(LG, 1.125, 1.125, origin=(0, 0)), (41.5, 5), "Ola logo 45 mm", "La ola del logo a 45 mm de ancho (proporción real del imagotipo, ~45 x 27)."

PROPS = [p01, p02, p03, p04, p05, p06, p07, p08, p09, p10]

def build():
    out = []
    for i, fn in enumerate(PROPS, 1):
        g, hole, name, desc = fn()
        g = mill(soften(g))
        minx, miny, maxx, maxy = g.bounds
        W = 45 if "45" in name else 40
        s = W / max(maxx - minx, maxy - miny)
        g = affinity.translate(affinity.scale(g, s, s, origin=(0, 0)), -minx * s, -miny * s)
        if hole: hole = best_hole(g, ((hole[0] - minx) * s, (hole[1] - miny) * s))
        d = dict(code=f"P{i:02d}", name=name, desc=desc, geom=g, hole=hole, engrave=(i == 2))
        d["qa"] = qa(g, hole); out.append(d)
    return out

def draw_piece(ax, d):
    g = d["geom"]
    for p in getattr(g, "geoms", [g]):
        ax.fill(*p.exterior.xy, color="#e6ecea", zorder=1)
        ax.plot(*p.exterior.xy, color="#0b2a30", lw=1.8, zorder=3)
        for h in p.interiors:
            ax.fill(*h.xy, color="white", zorder=2); ax.plot(*h.xy, color="#0b2a30", lw=1.8, zorder=3)
    if d["hole"]:
        hx, hy = d["hole"]
        ax.add_patch(Circle((hx, hy), HOLE / 2, fc="white", ec="#0b2a30", lw=1.5, zorder=4))
        ax.plot([hx - 4, hx + 4], [hy, hy], color="#0b2a30", lw=0.5, zorder=4); ax.plot([hx, hx], [hy - 4, hy + 4], color="#0b2a30", lw=0.5, zorder=4)
        ax.add_patch(Circle((hx + 6.5, hy - 4), 9, fc="none", ec="#aab4b2", lw=2.2, zorder=0))
    else:
        for p in getattr(g, "geoms", [g]):
            for h in p.interiors:
                c = Polygon(h).centroid
                ax.add_patch(Circle((c.x + 7, c.y - 7), 9, fc="none", ec="#aab4b2", lw=2.2, zorder=0))
    if d["engrave"]:
        ax.text(15, 11, "1 kg", fontsize=20, fontweight="bold", color="#6a8a84", ha="center", va="center", zorder=5)
    minx, miny, maxx, maxy = g.bounds
    ax.annotate("", (minx, maxy + 3.5), (maxx, maxy + 3.5), arrowprops=dict(arrowstyle="<->", lw=0.8, color="#333"))
    ax.text((minx + maxx) / 2, maxy + 4.6, f"{maxx - minx:.0f}", ha="center", va="bottom", fontsize=9, color="#333")
    ax.annotate("", (maxx + 3.5, miny), (maxx + 3.5, maxy), arrowprops=dict(arrowstyle="<->", lw=0.8, color="#333"))
    ax.text(maxx + 4.6, (miny + maxy) / 2, f"{maxy - miny:.0f}", ha="left", va="center", fontsize=9, color="#333", rotation=90)
    ax.set_aspect("equal"); ax.set_xlim(-8, 54); ax.set_ylim(-10, 50); ax.axis("off")

def draw_sheet(ds, fn):
    cols, rows = 5, 2
    fig = plt.figure(figsize=(26, 13), dpi=110); fig.patch.set_facecolor("white")
    fig.text(0.012, 0.965, "Llavero ola · propuestas en plano para selección", fontsize=20, fontweight="bold", color="#01313D")
    fig.text(0.012, 0.935, "Gravitec Formentera (o Atenas) · envolvente ≈ 40 mm · fresa Ø9: todas las concavidades ≥ R4,5 · línea continua = corte pasante · gris = anilla Ø18 orientativa · taladro Ø4,5 salvo «anilla por el hueco»",
             fontsize=11, color="#444")
    fig.text(0.012, 0.912, "P01–P03: en la línea de la foto de referencia (ola que rompe a la derecha, anilla abajo-derecha).   P04–P10: con la ola del imagotipo de Gravity Wave.",
             fontsize=11, color="#444")
    cw, ch = 1 / cols, 0.44
    for i, d in enumerate(ds):
        r, c = divmod(i, cols)
        x0 = c * cw; y0 = 0.46 - r * ch
        ax = fig.add_axes([x0 + 0.012, y0 + 0.11, cw - 0.024, ch - 0.14])
        draw_piece(ax, d)
        fig.text(x0 + 0.014, y0 + ch - 0.01, f"{d['code']} · {d['name']}", fontsize=14, fontweight="bold", color="#01313D", va="top")
        q = d["qa"]
        info = f"{q['envolvente'][0]:g} x {q['envolvente'][1]:g} mm · {q['area_cm2']:.1f} cm²" + (" · anilla por el hueco" if not d["hole"] else "")
        warn = []
        if q["inaccesible_mm2"] > 0.5: warn.append("revisar fresa")
        if q["zonas_finas_mm2"] > 2: warn.append("zona < 5 mm")
        if q["caras"] != 1: warn.append("¡varias piezas!")
        fig.text(x0 + 0.014, y0 + 0.095, info, fontsize=10, color="#333", va="top")
        if warn: fig.text(x0 + cw - 0.016, y0 + 0.095, " · ".join(warn), fontsize=9.5, color="#b00", va="top", ha="right")
        fig.text(x0 + 0.014, y0 + 0.072, "\n".join(textwrap.wrap(d["desc"], 52)), fontsize=9.3, color="#555", va="top", linespacing=1.35)
    plt.savefig(fn, facecolor="white"); plt.close(fig)

if __name__ == "__main__":
    ds = build()
    for d in ds: print(d["code"], d["name"], d["hole"], d["qa"])
    draw_sheet(ds, "propuestas/Llavero_Ola_Propuestas_Plano.png")
