import sys, math; sys.path.insert(0, ".")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from curvas import path, C
from olas import qa, HOLE

def llavero():
    """Llavero de la foto, 40 mm de ancho. Cresta a la derecha, tubo abierto hacia la derecha-abajo,
    lóbulo inferior derecho con el taladro de la anilla."""
    nub = (34.5, 5.5); rn = 5.5
    tube = (23.5, 20.5); rt = 5.5
    tip = (32.6, 24.6); rtip = 3.2
    a_in, a_out = -62, -352           # tubo: de la boca (abajo-dcha) en sentido horario hasta el labio
    p_in = (tube[0] + rt*math.cos(math.radians(a_in)), tube[1] + rt*math.sin(math.radians(a_in)))
    p_tip_in = (tip[0] + rtip*math.cos(math.radians(245)), tip[1] + rtip*math.sin(math.radians(245)))
    g = path((3, 0), [
        ('L', (34.5, 0)),
        ('A', nub, rn, -90, 118),
        ('C', (29.6, 12.8), (27.2, 14.0), p_in),
        ('A', tube, rt, a_in, a_out),
        ('C', (29.6, 22.4), (30.4, 21.6), p_tip_in),
        ('A', tip, rtip, 245, 385),
        ('C', (37.8, 29), (39.6, 31.5), (37.4, 34.2)),
        ('C', (34.8, 37.4), (28.5, 38.4), (22.5, 36.8)),
        ('C', (13.5, 34.2), (4.6, 24.5), (1.4, 12)),
        ('C', (0.5, 8.5), (0, 5), (0, 3)),
        ('A', (3, 3), 3, 180, 270),
    ])
    return g, nub

if __name__ == "__main__":
    g, hole = llavero(); q = qa(g, hole); print(q)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.fill(*g.exterior.xy, color="#2f6b62"); ax.add_patch(Circle(hole, HOLE/2, color="w"))
    # zonas inaccesibles
    void = g.envelope.buffer(27).difference(g); r = 4.47
    miss = void.difference(void.buffer(-r, 32).buffer(r, 32))
    for m in getattr(miss, "geoms", [miss]):
        if m.area > 0.3: ax.fill(*m.exterior.xy, color="red")
    ax.set_aspect("equal"); ax.set_xlim(-2, 42); ax.set_ylim(-2, 42); ax.grid(alpha=.3)
    plt.savefig("refina.png", dpi=80)
