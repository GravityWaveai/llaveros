import os, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from shapely.geometry import Point
from shapely import affinity
sys.path.insert(0, ".")
import olas
from olas import build, qa, HOLE, R

SW = "/root/.claude/skills/synced/d7aa75cd-e11c-4add-92e9-f84caa64de54_593730d0-f659-4351-a80d-c95e15f0e911/interactive-product-customizer/assets/swatches/Formentera.png"
PX = 18                    # px por mm
T = 5.0                    # espesor a mostrar (mm)
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def best_hole(g, pref):
    """Coloca el taladro en el punto del cuerpo más cercano al deseado con 2,5 mm de pared."""
    core = g.buffer(-(HOLE / 2 + 2.5))
    if core.is_empty: return None
    p = Point(pref)
    if core.contains(p): return pref
    from shapely.ops import nearest_points
    q = nearest_points(core, p)[0]
    return (round(q.x, 1), round(q.y, 1))

def texture(w, h, seed=0):
    sw = Image.open(SW).convert("RGB"); sw = sw.crop((2, 2, sw.width - 2, sw.height - 14))
    sw = sw.resize((sw.width * 4, sw.height * 4), Image.LANCZOS)
    out = Image.new("RGB", (w, h)); rng = np.random.default_rng(seed)
    for y in range(0, h, sw.height):
        for x in range(0, w, sw.width):
            t = sw.rotate(int(rng.integers(0, 4)) * 90, expand=True)
            if rng.random() < .5: t = t.transpose(Image.FLIP_LEFT_RIGHT)
            out.paste(t, (x, y))
    return out.filter(ImageFilter.GaussianBlur(0.4))

def mask_of(g, size, off, scale=PX):
    m = Image.new("L", size, 0); d = ImageDraw.Draw(m)
    for poly in getattr(g, "geoms", [g]):
        d.polygon([(off[0] + x * scale, off[1] - y * scale) for x, y in poly.exterior.coords], fill=255)
        for h in poly.interiors:
            d.polygon([(off[0] + x * scale, off[1] - y * scale) for x, y in h.coords], fill=0)
    return m

def render_piece(g, hole, size_px=900, t=T):
    W = size_px; img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    minx, miny, maxx, maxy = g.bounds
    ox = (W - (maxx - minx) * PX) / 2 - minx * PX
    oy = (W + (maxy - miny) * PX) / 2 + miny * PX
    # pseudo-extrusión: canto (cara B más blanca por debajo, canto núcleo verde-grisáceo)
    dx, dy = 0.55, 0.75   # mm por mm de espesor en pantalla
    steps = int(t * 6)
    canto = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    for i in range(steps, 0, -1):
        k = i / steps
        col = (int(70 + 60 * (1 - k)), int(118 + 50 * (1 - k)), int(108 + 48 * (1 - k)), 255)
        m = mask_of(g, (W, W), (ox + dx * t * k * PX, oy + dy * t * k * PX))
        layer = Image.new("RGBA", (W, W), col); canto.paste(layer, (0, 0), m)
    # sombra
    sh = mask_of(g, (W, W), (ox + 0.9 * t * PX, oy + 1.3 * t * PX)).filter(ImageFilter.GaussianBlur(14))
    shadow = Image.new("RGBA", (W, W), (0, 0, 0, 0)); shadow.putalpha(sh.point(lambda v: int(v * 0.35)))
    img = Image.alpha_composite(img, shadow)
    img = Image.alpha_composite(img, canto)
    # cara A con textura Formentera
    tex = texture(W, W, seed=int(g.area)).convert("RGBA")
    # luz suave: ligero gradiente
    grad = Image.linear_gradient("L").resize((W, W)).rotate(35, resample=Image.BILINEAR).point(lambda v: 200 + v * 0.25)
    tex = Image.composite(tex, Image.new("RGBA", (W, W), (255, 255, 255, 255)), grad)
    m = mask_of(g, (W, W), (ox, oy))
    face = Image.new("RGBA", (W, W), (0, 0, 0, 0)); face.paste(tex, (0, 0), m)
    # borde fino del contorno (arista)
    edge = m.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
    face.paste(Image.new("RGBA", (W, W), (40, 80, 72, 255)), (0, 0), edge.filter(ImageFilter.GaussianBlur(0.6)))
    img = Image.alpha_composite(img, face)
    # taladro de la anilla
    if hole:
        hx, hy = ox + hole[0] * PX, oy - hole[1] * PX; r = HOLE / 2 * PX
        d = ImageDraw.Draw(img)
        d.ellipse([hx - r + 0.5 * t * PX * 0.55, hy - r + 0.5 * t * PX * 0.75, hx + r + 0.5 * t * PX * 0.55, hy + r + 0.5 * t * PX * 0.75], fill=(60, 95, 88, 255))
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=(0, 0, 0, 0))
        # anilla metálica
        ring = Image.new("RGBA", (W, W), (0, 0, 0, 0)); dr = ImageDraw.Draw(ring)
        rr_ = 6.5 * PX
        dr.ellipse([hx - rr_, hy - rr_ * 2 + r, hx + rr_, hy + r], outline=(185, 188, 190, 255), width=int(1.6 * PX))
        dr.ellipse([hx - rr_, hy - rr_ * 2 + r, hx + rr_, hy + r], outline=(225, 228, 230, 160), width=int(0.5 * PX))
        # la parte de la anilla que pasa por detrás de la pieza queda oculta
        behind = m.copy()
        ring_a = ring.split()[3]
        ring_a = Image.composite(Image.new("L", (W, W), 0), ring_a, behind.point(lambda v: 255 if v else 0))
        # salvo dentro del taladro
        holem = Image.new("L", (W, W), 0); ImageDraw.Draw(holem).ellipse([hx - r, hy - r, hx + r, hy + r], fill=255)
        ring_a = Image.composite(ring.split()[3], ring_a, holem)
        ring.putalpha(ring_a)
        img = Image.alpha_composite(img, ring)
    return img

def sheet(designs, fn, cols=5, cell=760):
    rows = math.ceil(len(designs) / cols)
    header = 230; W = cols * cell + 80; H = header + rows * (cell + 150) + 60
    bg = Image.new("RGB", (W, H), (244, 246, 245)); d = ImageDraw.Draw(bg)
    fb = ImageFont.truetype(FONT_B, 54); fr = ImageFont.truetype(FONT_R, 30); fs = ImageFont.truetype(FONT_R, 24); fc = ImageFont.truetype(FONT_B, 34)
    d.text((60, 50), "Llavero ola · Gravitec Formentera · 10 propuestas de silueta", font=fb, fill=(4, 38, 44))
    d.text((60, 125), f"Envolvente ≈ 40 x 40 mm · taladro Ø{HOLE:g} mm para anilla · todas las concavidades ≥ R4,5 (fresa Ø9) · espesor mostrado {T:g} mm (ver nota de disponibilidad)", font=fr, fill=(60, 70, 70))
    for i, dsg in enumerate(designs):
        r, c = divmod(i, cols)
        x0 = 40 + c * cell; y0 = header + r * (cell + 150)
        d.rounded_rectangle([x0 + 10, y0, x0 + cell - 10, y0 + cell + 130], 24, fill=(255, 255, 255), outline=(215, 222, 220), width=2)
        im = render_piece(dsg["geom"], dsg["hole"], size_px=cell - 60)
        bg.paste(im, (x0 + 30, y0 + 20), im)
        d.text((x0 + 36, y0 + cell - 10), f"{dsg['code']} · {dsg['name']}", font=fc, fill=(4, 38, 44))
        q = dsg["qa"]
        d.text((x0 + 36, y0 + cell + 36), f"{q['envolvente'][0]:g} x {q['envolvente'][1]:g} mm · {q['area_cm2']:.1f} cm²" + ("" if dsg["hole"] else " · anilla por el hueco"), font=fs, fill=(90, 100, 100))
        # descripción en dos líneas
        words = dsg["desc"].split(); lines, cur = [], ""
        for w in words:
            if d.textlength(cur + " " + w, font=fs) > cell - 80: lines.append(cur); cur = w
            else: cur = (cur + " " + w).strip()
        lines.append(cur)
        for j, ln in enumerate(lines[:2]):
            d.text((x0 + 36, y0 + cell + 68 + j * 30), ln, font=fs, fill=(90, 100, 100))
    bg.save(fn, optimize=True)

if __name__ == "__main__":
    ds = build()
    for dsg in ds:
        if dsg["hole"]:
            dsg["hole"] = best_hole(dsg["geom"], dsg["hole"])
        dsg["qa"] = qa(dsg["geom"], dsg["hole"])
        print(dsg["code"], dsg["name"], dsg["hole"], dsg["qa"])
    os.makedirs("propuestas", exist_ok=True)
    for dsg in ds:
        render_piece(dsg["geom"], dsg["hole"], 1000).save(f"propuestas/{dsg['code']}_{dsg['name'].replace(' ', '_')}.png")
    sheet(ds, "propuestas/Llavero_Ola_10_propuestas.png")
    print("ok")
