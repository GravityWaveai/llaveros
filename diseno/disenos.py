"""Siluetas del llavero ola, dibujadas a mano (mm). Cada función devuelve (geom, taladro|None, nombre, descripción)."""
import math, sys
sys.path.insert(0, ".")
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
from curvas import path, C, rr, fit

def ola_referencia():
    """Estilo foto: cresta a la derecha, tubo abierto a la derecha (boca ≥ 10 mm), lóbulo inferior derecho con taladro."""
    nub = (34.5, 5.5); rn = 5.5
    tube = (23, 21); rt = 5.5
    tip = (32.2, 24.2); rtip = 3.0
    g = path((3, 0), [
        ('L', (34.5, 0)),
        ('A', nub, rn, -90, 125),                       # lóbulo de la anilla
        ('C', (29.5, 12.5), (26.5, 13.5), (tube[0] + rt*math.cos(math.radians(-60)), tube[1] + rt*math.sin(math.radians(-60)))),
        ('A', tube, rt, -60, -350),                     # tubo (sentido horario)
        ('C', (29.2, 22.3), (30.2, 21.4), (tip[0] + rtip*math.cos(math.radians(250)), tip[1] + rtip*math.sin(math.radians(250)))),
        ('A', tip, rtip, 250, 380),                     # punta del labio
        ('C', (37.5, 28.5), (39.5, 31), (37.5, 34)),    # exterior del labio
        ('C', (35, 37.5), (29, 38.5), (23, 37)),        # cresta
        ('C', (14, 34.5), (5, 25), (1.5, 12)),          # lomo de la ola
        ('C', (0.5, 8), (0, 4), (0, 3)),
        ('A', (3, 3), 3, 180, 270),
    ])
    return g, (34.5, 5.5), "Ola referencia", "Como la foto: cresta que rompe a la derecha, tubo abierto y lóbulo inferior derecho con el taladro de la anilla."

def ola_referencia_cerrada():
    """Misma ola con el labio unido a la base: el tubo cerrado es el paso de la anilla."""
    g = path((3, 0), [
        ('L', (37, 0)), ('A', (37, 3), 3, -90, 0),
        ('C', (40, 12), (40.5, 20), (39.5, 27)),
        ('C', (39, 31), (37.5, 34), (33, 36.5)),
        ('C', (29, 38.5), (23, 38.5), (18, 36)),
        ('C', (11, 32.5), (5, 25), (1.5, 12)),
        ('C', (0.5, 8), (0, 4), (0, 3)), ('A', (3, 3), 3, 180, 270),
    ])
    g = g.difference(C(26, 20, 6))
    return g, None, "Ola tubo cerrado", "La misma ola con el labio unido a la base: el tubo (Ø12) es el paso de la anilla. Sin lóbulo ni taladro."

def ola_logo(hole="lomo"):
    """Ola del imagotipo Gravity Wave redibujada limpia (40 x 28): lomo recto a ~50º, cresta redonda,
    labio en C abierto a la derecha, base con el rizo final."""
    tube = (25.5, 14); rt = 6.5
    tip_a = 42; tip = (tube[0] + (rt + 3) * math.cos(math.radians(tip_a)), tube[1] + (rt + 3) * math.sin(math.radians(tip_a))); rtip = 3.0
    g = path((2, 0), [
        ('L', (36, 0)), ('A', (36, 4), 4, -90, 0),       # final de la base
        ('C', (40, 7), (39.5, 10.5), (37, 10)),          # rizo final (como el logo)
        ('C', (34.5, 9.5), (33, 7.5), (31, 7.5)),
        ('L', (tube[0] + rt*math.cos(math.radians(-50)), 7.5)),
        ('A', tube, rt, -50, -318),                      # tubo abierto a la derecha
        ('C', (29.5, 19.5), (30.3, 19.2), (tip[0] + rtip*math.cos(math.radians(230)), tip[1] + rtip*math.sin(math.radians(230)))),
        ('A', tip, rtip, 230, 400),                      # punta del labio
        ('C', (34.5, 25), (31, 27.5), (24, 28)),         # labio exterior + cresta
        ('C', (16, 28.5), (10, 22), (5.5, 14)),          # lomo
        ('C', (3, 9.5), (1.5, 6), (0, 3)),
        ('A', (3, 3), 3, 180, 270),
    ])
    h = (11.5, 14) if hole == "lomo" else (36.5, 4.5)
    return g, h, "Ola logo GW", "La ola del imagotipo redibujada limpia: lomo, cresta redonda, labio en C y rizo final. Taladro en el lomo, cuelga con la cresta arriba."

def ola_logo_lobulo():
    g, _, _, _ = ola_logo()
    g = g.union(C(35, 5.5, 5.5))
    return g, (35, 5.5), "Ola logo + lóbulo", "Ola del logo con el rizo final convertido en lóbulo redondo para la anilla (como en la foto)."

def medallon():
    """Medallón: mitad inferior círculo Ø40, mitad superior la cresta de la ola del logo."""
    disc = C(20, 20, 20)
    cut = path((-5, 45), [('L', (45, 45)), ('L', (45, 14)),
        ('C', (41, 16), (39, 19), (36, 22)),
        ('C', (32, 26), (28, 26), (24, 24)),
        ('C', (29, 29), (30, 34), (25, 37)),
        ('C', (19, 40), (9, 35), (4, 24)),
        ('L', (-5, 20))])
    g = disc.difference(cut)
    return g, (20, 10), "Medallón ola", "Moneda Ø40 cuya mitad superior es la cresta de la ola rompiendo a la derecha. Mucha superficie para grabar."

def placa_ventana():
    """Placa redondeada 40x40 con la ola del logo en negativo (ventana pasante con canales ≥ 9 mm)."""
    pl = rr(0, 0, 40, 40, 9)
    tube = (23, 15); rt = 5
    win = path((9, 6), [('L', (31, 6)), ('A', (31, 10.5), 4.5, -90, 50),
        ('C', (29, 16), (30, 18), (29.5, 21)),
        ('C', (28.5, 25), (26, 27.5), (22, 28)),
        ('C', (16, 28.5), (11, 23), (9, 16)),
        ('C', (8, 12), (7.5, 9), (9, 6))])
    g = pl.difference(win)
    return g, (20, 35), "Placa con ola en negativo", "Placa 40 x 40 con la ola del logo recortada como ventana pasante. Taladro arriba."

def doble_ola():
    """Dos olas del logo: la pequeña delante, la grande detrás, fundidas en una pieza."""
    big, _, _, _ = ola_logo()
    small = affinity.scale(big, 0.62, 0.62, origin=(0, 0))
    small = affinity.translate(small, 20, 0)
    g = unary_union([big, small, box(0, 0, 40, 6)])
    return g, (11.5, 14), "Doble ola", "Serie de dos olas del logo (grande detrás, pequeña delante) fundidas en una pieza apaisada."

def rizo():
    """Rizo: la ola enrollada en círculo, hueco Ø12 descentrado, labio y cola corta."""
    disc = C(20, 21, 19)
    g = path((2, 0), [('L', (30, 0)), ('C', (34, 0), (37, 1.5), (39, 4)),
        ('C', (41, 7), (40, 10), (37, 10)),
        ('L', (32, 10)),
        ('C', (30.5, 10), (30, 11), (30.5, 12.5)),
        ('C', (32, 17), (36.5, 19), (39, 21)),
        ('C', (41, 24), (40, 30), (36, 34.5)),
        ('C', (31, 39.5), (22, 41), (14, 38)),
        ('C', (5, 34), (0, 25), (0, 16)),
        ('C', (0, 8), (0, 2), (2, 0))])
    g = g.difference(C(23, 24, 6.5))
    return g, (12, 10), "Rizo", "La ola enrollada sobre sí misma: forma casi circular con el tubo descentrado y la cola saliendo abajo a la derecha."

def trazo():
    """Trazo: la ola como una sola línea gruesa (7 mm) que sube y se enrolla."""
    from shapely.geometry import LineString
    pts = [(3, 4), (8, 4.5), (13, 7), (18, 13), (22, 22), (26, 30)]
    c = (30, 29); r = 7.5
    pts += [(c[0] + r*math.cos(math.radians(a)), c[1] + r*math.sin(math.radians(a))) for a in range(150, -120, -6)]
    g = LineString(pts).buffer(3.5, 48).union(C(3, 4, 5.5))
    return g, (3, 4), "Trazo ola", "La ola como una sola línea gruesa que sube y se enrolla: la más ligera y minimalista. Taladro en el arranque."

def ola_etiqueta():
    """Etiqueta vertical: placa 30 x 40 con la cresta del logo como remate superior y taladro en la cresta."""
    g = path((0, 3), [('A', (3, 3), 3, 180, 270), ('L', (27, 0)), ('A', (27, 3), 3, 270, 360),
        ('L', (30, 20)),
        ('C', (30, 26), (28, 30), (24, 33)),
        ('C', (20, 36), (14, 40), (8, 40)),
        ('C', (3, 40), (0, 36), (0, 30)),
        ('L', (0, 3))])
    return g, (7, 33), "Etiqueta ola", "Etiqueta vertical 30 x 40 rematada arriba con la curva de la cresta. Sencilla, mucho sitio para texto."

DISENOS = [ola_referencia, ola_referencia_cerrada, ola_logo, ola_logo_lobulo, medallon, placa_ventana, doble_ola, rizo, trazo, ola_etiqueta]
