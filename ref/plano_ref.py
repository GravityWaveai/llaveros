"""Plano A3 (PDF) + DXF de corte del llavero ola, según el dibujo de referencia (alto 40 mm, espesor 5 mm)."""
import os, math, datetime
import ezdxf
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from shapely.geometry import Point
from medidas import medir

REF = "Llavero_Ola_REV03"; PRODUCTO = "Llavero ola"
ACABADO = "Formentera"; ESPESOR = 5; CANTIDAD = "PENDIENTE"
CANTO = "PENDIENTE"; ESQUINA = "PENDIENTE"; ARISTAS = "PENDIENTE"
HOLE_D = 4.8          # taladro nominal (4,75 en el dibujo de referencia)
OUT = "../plano"

pdfmetrics.registerFont(TTFont("R", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
PW, PH = 420 * mm, 297 * mm
def M(v): return v * mm
def f(v): return f"{v:.2f}".rstrip("0").rstrip(".")

def arrow(c, x, y, ang, s=2.2):
    a = math.radians(ang); p = c.beginPath(); p.moveTo(M(x), M(y))
    p.lineTo(M(x - s*math.cos(a-0.3)), M(y - s*math.sin(a-0.3))); p.lineTo(M(x - s*math.cos(a+0.3)), M(y - s*math.sin(a+0.3))); p.close()
    c.drawPath(p, fill=1, stroke=0)
def cota_h(c, x1, x2, y_obj, y_line, txt, size=9):
    c.setLineWidth(0.25); d = 1 if y_line > y_obj else -1
    for x in (x1, x2): c.line(M(x), M(y_obj + d), M(x), M(y_line + 2*d))
    c.line(M(x1), M(y_line), M(x2), M(y_line)); arrow(c, x1, y_line, 180); arrow(c, x2, y_line, 0)
    c.setFont("R", size); c.drawCentredString(M((x1+x2)/2), M(y_line + 1.2), txt)
def cota_v(c, y1, y2, x_obj, x_line, txt, size=9):
    c.setLineWidth(0.25); d = 1 if x_line > x_obj else -1
    for y in (y1, y2): c.line(M(x_obj + d), M(y), M(x_line + 2*d), M(y))
    c.line(M(x_line), M(y1), M(x_line), M(y2)); arrow(c, x_line, y1, 270); arrow(c, x_line, y2, 90)
    c.saveState(); c.translate(M(x_line - 1.2), M((y1+y2)/2)); c.rotate(90); c.setFont("R", size); c.drawCentredString(0, 0, txt); c.restoreState()
def leader(c, x0, y0, x1, y1, txt, size=8):
    c.setLineWidth(0.25); c.line(M(x0), M(y0), M(x1), M(y1)); c.circle(M(x0), M(y0), M(0.5), fill=1)
    c.setFont("R", size); c.drawString(M(x1 + 1), M(y1 - 1), txt)
def poly(c, pts, fill=None, lw=0.6, dash=None):
    p = c.beginPath(); p.moveTo(M(pts[0][0]), M(pts[0][1]))
    for q in pts[1:]: p.lineTo(M(q[0]), M(q[1]))
    p.close(); c.setLineWidth(lw)
    if dash: c.setDash(*dash)
    if fill: c.setFillColorRGB(*fill)
    c.drawPath(p, stroke=1, fill=1 if fill else 0); c.setDash(); c.setFillColorRGB(0, 0, 0)

def cajetin(c, pag, npag):
    rows = [("PROYECTO:", f"{PRODUCTO}  ({REF})"), ("PIEZA / VISTA:", "01 Llavero (1 ud)"), ("EMPRESA:", "Gravity Wave"),
            ("MATERIAL:", "Panel plástico reciclado Gravitec"), ("ACABADO:", ACABADO), ("ESPESOR:", f"{ESPESOR} mm (ver nota 2)"),
            ("PROCESO:", "Corte CNC"), ("HERRAMIENTA:", "Fresa Ø9 mm · taladro Ø4,8"), ("UNIDADES:", "mm"),
            ("ESCALA:", "2.5:1 impreso en A3"), ("FECHA:", datetime.date.today().strftime("%d/%m/%Y")), ("DISEÑADO PARA:", "Gravity Wave"),
            ("CANTIDAD:", CANTIDAD), ("CARA A / B / CANTO:", f"{ACABADO} / {ACABADO} / {ACABADO}"), ("ACABADO CANTO:", CANTO),
            ("ACABADO ESQUINA:", ESQUINA), ("ACABADO ARISTAS:", ARISTAS), ("REVISIÓN:", "REV03"), ("PÁG.:", f"{pag}/{npag}")]
    BX, BY, BW, rh = 250, 10, 160, 5.0; BH = rh * len(rows)
    c.setLineWidth(0.6); c.rect(M(BX), M(BY), M(BW), M(BH)); c.setLineWidth(0.25)
    for i, (k, v) in enumerate(rows):
        y = BY + BH - (i+1)*rh; c.line(M(BX), M(y), M(BX+BW), M(y))
        c.setFont("B", 8); c.setFillColorRGB(0,0,0); c.drawString(M(BX+2), M(y+1.5), k)
        pend = "PENDIENTE" in v; c.setFont("B" if pend else "R", 8.5)
        if pend: c.setFillColorRGB(0.8, 0, 0)
        c.drawString(M(BX+36), M(y+1.5), v); c.setFillColorRGB(0,0,0)
    c.line(M(BX+34), M(BY), M(BX+34), M(BY+BH))
    return BY + BH

def texto(c, x, y, w, titulo, lineas, size=8, lh=4.3):
    c.setFont("B", 9); c.drawString(M(x), M(y - 5), titulo); c.setFont("R", size); y -= 11
    for ln in lineas:
        cur = ""
        for wd in ln.split(" "):
            t = (cur + " " + wd).strip()
            if pdfmetrics.stringWidth(t, "R", size) / mm > w - 2 and cur:
                c.drawString(M(x), M(y), cur); y -= lh; cur = "    " + wd
            else: cur = t
        c.drawString(M(x), M(y), cur); y -= lh
    return y

def iso(c, pts, hole, x, y, w, h, t):
    """Proyección oblicua (cabinet) de la pieza extruida t mm."""
    kx, ky = 0.5 * math.cos(math.radians(30)), 0.5 * math.sin(math.radians(30))
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    s = min(w / (max(xs) - min(xs) + kx * t), h / (max(ys) - min(ys) + ky * t))
    ox, oy = x - min(xs) * s + kx * t * s, y - min(ys) * s + ky * t * s
    def T(px, py, pz=0): return (ox + (px - kx * pz) * s, oy + (py - ky * pz) * s)
    n = len(pts); quads = []
    for i in range(n):
        a, b = pts[i], pts[(i+1) % n]
        nx, ny = (b[1]-a[1]), -(b[0]-a[0])
        if nx * kx + ny * ky > 0: continue   # polígono CCW: se ven las caras que miran hacia (-kx,-ky)
        quads.append([T(*a, 0), T(*b, 0), T(*b, t), T(*a, t)])
    for q in quads: poly(c, q, fill=(0.80, 0.84, 0.83), lw=0.3)
    poly(c, [T(*p, 0) for p in pts], fill=(0.93, 0.95, 0.94), lw=0.6)
    hx, hy = T(*hole, 0); c.setLineWidth(0.4); c.setFillColorRGB(1,1,1); c.circle(M(hx), M(hy), M(HOLE_D/2*s), fill=1, stroke=1); c.setFillColorRGB(0,0,0)

def dxf(g, hole, fn):
    doc = ezdxf.new("R2010", setup=False); doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = 4; doc.header["$MEASUREMENT"] = 1
    for ly, col in [("CUT_OUTER", 7), ("CUT_INNER", 1), ("POCKET", 5), ("DRILL", 3)]: doc.layers.add(ly, color=col)
    ms = doc.modelspace()
    pts = [(round(x, 3), round(y, 3)) for x, y in list(g.exterior.coords)[:-1]]
    ms.add_lwpolyline(pts, close=True, dxfattribs={"layer": "CUT_OUTER"})
    ms.add_circle((round(hole[0], 2), round(hole[1], 2)), HOLE_D / 2, dxfattribs={"layer": "DRILL"})
    doc.saveas(fn)

def plano(m, fn):
    g = m["g"]; hole = m["hole"]; W, Hh = m["ancho"], m["alto"]
    c = canvas.Canvas(fn, pagesize=(PW, PH)); c.setTitle(f"{PRODUCTO} REV03 - Plano"); c.setAuthor("Gravity Wave")
    c.setLineWidth(0.7); c.rect(M(10), M(10), M(400), M(277))
    cajetin(c, 1, 1)
    S = 2.5; OX, OY = 32, 122
    pts = [(OX + x*S, OY + y*S) for x, y in g.exterior.coords]
    poly(c, pts, lw=0.7)
    hx, hy = OX + hole[0]*S, OY + hole[1]*S
    c.setLineWidth(0.4); c.circle(M(hx), M(hy), M(HOLE_D/2*S))
    c.setLineWidth(0.2); c.setDash(3, 1.5); c.line(M(hx-9), M(hy), M(hx+9), M(hy)); c.line(M(hx), M(hy-9), M(hx), M(hy+9))
    # tubo: círculo de referencia
    tx, ty, td = m["tubo"]; c.circle(M(OX + tx*S), M(OY + ty*S), M(td/2*S))
    c.line(M(OX + tx*S - 6), M(OY + ty*S), M(OX + tx*S + 6), M(OY + ty*S)); c.line(M(OX + tx*S), M(OY + ty*S - 6), M(OX + tx*S), M(OY + ty*S + 6)); c.setDash()
    c.setFont("R", 7); c.drawString(M(OX - 7), M(OY - 1), "0,0"); c.circle(M(OX), M(OY), M(0.7), fill=1)
    # cotas generales
    cota_h(c, OX, OX + W*S, OY + Hh*S, OY + Hh*S + 10, f(W))
    cota_v(c, OY, OY + Hh*S, OX + W*S, OX + W*S + 10, f(Hh))
    cota_h(c, OX, OX + m["cresta"][0]*S, OY + Hh*S, OY + Hh*S + 18, f"{f(m['cresta'][0])} (cresta)")
    # taladro
    cota_h(c, OX, hx, OY, OY - 8, f(hole[0]))
    cota_v(c, OY, hy, OX + W*S, OX + W*S + 22, f(hole[1]))
    leader(c, hx + HOLE_D/2*S*0.7, hy - HOLE_D/2*S*0.7, OX + W*S + 38, OY + 6*S, f"Ø{f(HOLE_D)} taladro")
    # tubo
    cota_h(c, OX, OX + tx*S, OY + Hh*S, OY + Hh*S + 26, f(tx))
    cota_v(c, OY, OY + ty*S, OX + W*S, OX + W*S + 34, f(ty))
    leader(c, OX + (tx - td/2*0.7)*S, OY + (ty + td/2*0.7)*S, OX + 8*S, OY + 36*S, f"Tubo Ø{f(td)} (hueco)")
    # boca y lóbulo
    lx, ly, lr = m["lobulo"]
    leader(c, OX + (lx + lr*0.7)*S, OY + (ly + lr*0.7)*S, OX + W*S + 38, OY + 22*S, f"Lóbulo R{f(lr)}")
    leader(c, OX + 36.8*S, OY + 24.8*S, OX + W*S + 38, OY + 30*S, f"Boca {f(m['boca'])} (nota 3)")
    # base
    cota_h(c, OX + m["base"][0]*S, OX + m["base"][1]*S, OY, OY - 16, f"{f(m['base'][1] - m['base'][0])} (base recta)")
    c.setFont("B", 9); c.drawString(M(OX), M(OY - 24), "VISTA FRONTAL (CARA A, PLANTA DE CORTE) - ESCALA 2,5:1")
    # lateral
    LX = OX + W*S + 84
    c.setLineWidth(0.6); c.rect(M(LX), M(OY), M(ESPESOR*S), M(Hh*S))
    cota_h(c, LX, LX + ESPESOR*S, OY + Hh*S, OY + Hh*S + 10, f(ESPESOR))
    c.setFont("B", 9); c.drawString(M(LX - 6), M(OY - 24), "LATERAL")
    # 3D
    iso(c, [(x, y) for x, y in g.exterior.coords[:-1]], hole, 22, 22, 100, 62, ESPESOR)
    c.setFont("B", 8); c.drawString(M(22), M(16), "VISTA 3D (SIN ESCALA)")
    # datos y notas
    y = texto(c, 252, 282, 156, "DATOS DE LA PIEZA", [
        f"Envolvente: {f(W)} x {f(Hh)} x {f(ESPESOR)} mm. Área de la cara: {m['area']:.1f} cm². Altura total de la ola = 40 mm (referencia).",
        f"Contorno vectorizado del dibujo de referencia y adaptado a fresa Ø9 (nota 3): geometría exacta en el DXF ({REF}_Pieza01_Llavero.dxf), capa CUT_OUTER (polilínea cerrada).",
        f"Taladro Ø{f(HOLE_D)} en ({f(hole[0])}, {f(hole[1])}) desde 0,0, capa DRILL (en el dibujo: Ø{f(m['hole_d'])}). Pared mínima al taladro {f(m['pared'])} mm.",
        f"Tubo: hueco circular Ø{f(td)} centrado en ({f(tx)}, {f(ty)}), abierto hacia la derecha por una boca de {f(m['boca'])} mm.",
        f"Lóbulo de la anilla: R{f(lr)} centrado en ({f(lx)}, {f(ly)}). Base recta de {f(m['base'][1] - m['base'][0])} mm.",
        "Origen 0,0 = esquina inferior izquierda de la envolvente. Cara A = +Z en el DXF. Mecanizar siempre con la cara A arriba."])
    y = texto(c, 252, y - 2, 156, "NOTAS DE FABRICACIÓN", [
        "1. Corte pasante de una sola pieza, sin rebajes. DXF con geometría nominal; compensación de fresa en CAM. Tolerancia general ±0,5 mm.",
        f"2. ESPESOR 5 mm. Catálogo Gravitec: {ACABADO} se sirve en 10 / 18 / 30 mm; el espesor de 5 mm existe en Niza, Ifach, Cadaqués, Marsella, Andros, Ítaca, Capri, Sicilia y Palermo. CONFIRMAR acabado/espesor antes de mecanizar.",
        f"3. Geometría apta para fresa Ø9: todos los radios cóncavos del DXF son >= R4,5. Las dos uniones labio-tubo y lóbulo-tubo del dibujo original (radio pequeño) van ya con R4,5 (desviación máx. {f(m['info']['desv_cnc_mm'])} mm). La boca del tubo ({f(m['boca'])} mm) es menor que la fresa: la fresa la corta entrando por el tubo y por fuera.",
        f"4. Orden de mecanizado: (1) taladro Ø{f(HOLE_D)} con broca (capa DRILL); (2) tubo Ø{f(td)} como VACIADO completo (pocket), no como perfil, para no dejar un disco suelto; (3) contorno exterior (CUT_OUTER) con puentes de sujeción (tabs) o vacío: la pieza es pequeña y se suelta al final del corte.",
        "5. Sin zonas de menos de 5 mm salvo la pared del taladro (ver datos). Pieza de una sola cara, sin zonas flotantes.",
        "6. Acabado de canto, esquina y aristas: PENDIENTE (ver cajetín). Cantidad PENDIENTE: nesting al confirmarla (separación mínima 9 mm; girar 0/90/180º, nunca voltear).",
        "7. Uso decorativo. Gravitec NO APTO PARA USO ALIMENTARIO."])
    c.showPage(); c.save()

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    m = medir()
    plano(m, f"{OUT}/{REF}_Plano.pdf"); dxf(m["g"], m["hole"], f"{OUT}/{REF}_Pieza01_Llavero.dxf")
    print("ok")
