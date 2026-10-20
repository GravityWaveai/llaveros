import sys; sys.path.insert(0, ".")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from disenos import DISENOS
from olas import qa, HOLE
fig, axs = plt.subplots(2, 5, figsize=(22, 9))
for ax, fn in zip(axs.flat, DISENOS):
    g, hole, name, _ = fn()
    q = qa(g, hole)
    for p in getattr(g, "geoms", [g]):
        ax.fill(*p.exterior.xy, color="#2f6b62"); [ax.fill(*h.xy, color="w") for h in p.interiors]
    if hole: ax.add_patch(Circle(hole, HOLE / 2, color="w"))
    ax.set_aspect("equal"); ax.set_xlim(-3, 45); ax.set_ylim(-3, 45); ax.grid(alpha=.3)
    ax.set_title(f"{name}  inac={q['inaccesible_mm2']} fin={q['zonas_finas_mm2']} caras={q['caras']} tal={q.get('taladro_ok')}", fontsize=8)
    print(name, q)
plt.tight_layout(); plt.savefig("preview.png", dpi=65)
