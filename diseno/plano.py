"""Plano A3 del llavero ola (PDF) + DXF de corte. Pieza única calcada de la foto."""
import os, math, datetime, sys; sys.path.insert(0, ".")
import ezdxf
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from shapely.geometry import Point
from llavero import pieza, medidas, HOLE

REF = "Llavero_Ola_REV01"; PRODUCTO = "Llavero ola"
ACABADO = "Formentera"; ESPESOR = 5; CANTIDAD = "PENDIENTE"
CANTO = "PENDIENTE"; ESQUINA = "PENDIENTE"; ARISTAS = "PENDIENTE"
OUT = "../plano"

pdfmetrics.registerFont(TTFont("R", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
PW, PH = 420 * mm, 297 * mm
def M(v): return v * mm

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
            ("PROCESO:", "Corte CNC"), ("HERRAMIENTA:", "Fresa Ø9 · boca del tubo: ver nota 3"), ("UNIDADES:", "mm"),
            ("ESCALA:", "3:1 impreso en A3"), ("FECHA:", datetime.date.today().strftime("%d/%m/%Y")), ("DISEÑADO PARA:", "Gravity Wave"),
            ("CANTIDAD:", CANTIDAD), ("CARA A / B / CANTO:", f"{ACABADO} / {ACABADO} / {ACABADO}"), ("ACABADO CANTO:", CANTO),
            ("ACABADO ESQUINA:", ESQUINA), ("ACABADO ARISTAS:", ARISTAS), ("REVISIÓN:", "REV01"), ("PÁG.:", f"{pag}/{npag}")]
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
    def P(px, py, pz): return (px + kx * (-pz), py + ky * (-pz))     # z hacia el observador, abajo
    # escala
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    s = min(w / (max(xs) - min(xs) + kx * t), h / (max(ys) - min(ys) + ky * t))
    ox, oy = x - min(xs) * s + kx * t * s, y - min(ys) * s + ky * t * s
    def T(px, py, pz=0): q = P(px, py, pz); return (ox + q[0]*s, oy + q[1]*s)
    # caras laterales (pintar las que miran al observador: orden por profundidad aproximada)
    n = len(pts)
    quads = []
    for i in range(n):
        a, b = pts[i], pts[(i+1) % n]
        nx, ny = (b[1]-a[1]), -(b[0]-a[0])        # normal exterior (polígono CCW)
        if nx * kx + ny * ky < 0: continue        # ignorar caras que miran hacia atrás... (la proyección va a -z)
        quads.append(([T(*a, 0), T(*b, 0), T(*b, t), T(*a, t)], (0.80, 0.84, 0.83)))
    for q, col in quads: poly(c, q, fill=col, lw=0.3)
    poly(c, [T(*p, 0) for p in pts], fill=(0.93, 0.95, 0.94), lw=0.6)
    hx, hy = T(*hole, 0); c.setLineWidth(0.4); c.setFillColorRGB(1,1,1); c.circle(M(hx), M(hy), M(HOLE/2*s), fill=1, stroke=1); c.setFillColorRGB(0,0,0)

def dxf(g, hole, fn):
    doc = ezdxf.new("R2010", setup=False); doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = 4; doc.header["$MEASUREMENT"] = 1
    for ly, col in [("CUT_OUTER", 7), ("CUT_INNER", 1), ("POCKET", 5), ("DRILL", 3)]: doc.layers.add(ly, color=col)
    ms = doc.modelspace()
    pts = list(g.exterior.coords)[:-1]
    ms.add_lwpolyline([(x, y) for x, y in pts], close=True, dxfattribs={"layer": "CUT_OUTER"})
    ms.add_circle(hole, HOLE / 2, dxfattribs={"layer": "DRILL"})
    doc.saveas(fn)

def plano(g, hole, fn):
    m = medidas(g, hole)
    c = canvas.Canvas(fn, pagesize=(PW, PH)); c.setTitle(f"{PRODUCTO} REV01 - Plano"); c.setAuthor("Gravity Wave")
    c.setLineWidth(0.7); c.rect(M(10), M(10), M(400), M(277))
    top = cajetin(c, 1, 1)
    # ----- planta 3:1
    S = 3.0; OX, OY = 35, 120
    pts = [(OX + x*S, OY + y*S) for x, y in g.exterior.coords]
    poly(c, pts, lw=0.7)
    hx, hy = OX + hole[0]*S, OY + hole[1]*S
    c.setLineWidth(0.4); c.circle(M(hx), M(hy), M(HOLE/2*S))
    c.setLineWidth(0.2); c.setDash(3, 1.5); c.line(M(hx-8), M(hy), M(hx+8), M(hy)); c.line(M(hx), M(hy-8), M(hx), M(hy+8)); c.setDash()
    c.setFont("R", 7); c.drawString(M(OX - 1), M(OY - 4.5), "0,0"); c.circle(M(OX), M(OY), M(0.7), fill=1)
    W, Hh = m["ancho"], m["alto"]
    cota_h(c, OX, OX + W*S, OY + Hh*S, OY + Hh*S + 10, f"{W:g}")
    cota_v(c, OY, OY + Hh*S, OX + W*S, OX + W*S + 10, f"{Hh:g}")
    # taladro: posición desde 0,0
    cota_h(c, OX, hx, OY, OY - 8, f"{hole[0]:g}")
    cota_v(c, OY, hy, OX + W*S, OX + W*S + 20, f"{hole[1]:g}")
    leader(c, hx + HOLE/2*S*0.7, hy - HOLE/2*S*0.7, OX + 44*S, OY + 3*S, f"Ø{HOLE:g} taladro anilla")
    # tubo y boca
    tx, ty, tw, th = m["tubo"]
    leader(c, OX + tx*S, OY + (ty + 1)*S, OX + 44*S, OY + 27*S, f"Tubo abierto ≈ {tw:g} x {th:g} (hueco)")
    cx_, cy_ = m["cresta"]
    cota_h(c, OX, OX + cx_*S, OY + Hh*S, OY + Hh*S + 18, f"{cx_:g} (cresta)")
    leader(c, OX + (tx + tw/2 + 1)*S, OY + (ty - th/2 + 2.5)*S, OX + 44*S, OY + 16*S, f"Boca del tubo ≈ {m['boca']:g} mm (ver nota 3)")
    c.setFont("B", 9); c.drawString(M(OX), M(OY - 16), "VISTA FRONTAL (CARA A, PLANTA DE CORTE) - ESCALA 3:1")
    # ----- lateral
    LX = OX + W*S + 36
    c.setLineWidth(0.6); c.rect(M(LX), M(OY), M(ESPESOR*S), M(Hh*S))
    cota_h(c, LX, LX + ESPESOR*S, OY + Hh*S, OY + Hh*S + 10, f"{ESPESOR:g}")
    c.setFont("B", 9); c.drawString(M(LX - 6), M(OY - 16), "LATERAL")
    # ----- isométrica
    iso(c, [(x, y) for x, y in g.exterior.coords[:-1]], hole, 22, 24, 95, 62, ESPESOR)
    c.setFont("B", 8); c.drawString(M(22), M(18), "VISTA 3D (SIN ESCALA)")
    # ----- datos y notas
    y = texto(c, 252, 282, 156, "DATOS DE LA PIEZA", [
        f"Envolvente: {W:g} x {Hh:g} x {ESPESOR:g} mm. Área de la cara: {m['area']:.1f} cm².",
        f"Contorno libre calcado de la muestra de referencia: geometría exacta en el DXF ({REF}_Pieza01_Llavero.dxf), capa CUT_OUTER.",
        f"Taladro Ø{HOLE:g} en ({hole[0]:g}, {hole[1]:g}) desde 0,0 (capa DRILL). Pared mínima al taladro ≈ {round(g.exterior.distance(Point(hole)) - HOLE/2, 1):g} mm.",
        f"Tubo: hueco abierto de ≈ {tw:g} x {th:g} mm con boca de ≈ {m['boca']:g} mm bajo la punta del labio.",
        "Origen 0,0 = esquina inferior izquierda de la envolvente. Cara A = +Z en el DXF."])
    y = texto(c, 252, y - 2, 156, "NOTAS DE FABRICACIÓN", [
        "1. Corte pasante de una sola pieza; sin rebajes. DXF con geometría nominal, compensación de fresa en CAM. Tolerancia general ±0,5 mm.",
        f"2. ESPESOR: se pide 5 mm. Catálogo Gravitec: {ACABADO} se sirve en 10 / 18 / 30 mm; 5 mm solo en Niza, Ifach, Cadaqués, Marsella, Andros, Ítaca, Capri, Sicilia y Palermo. CONFIRMAR acabado/espesor antes de mecanizar.",
        f"3. BOCA DEL TUBO ≈ {m['boca']:g} mm: NO mecanizable con fresa Ø9 (radio mínimo R4,5). Opciones: (a) fresa ≤ Ø2,5 solo para la boca, (b) corte láser, (c) dejar el tubo cerrado con Ø9 (sin boca). Decidir antes de mecanizar.",
        "4. El resto del contorno y el tubo (hueco > Ø9) se mecanizan con fresa Ø9.",
        "5. Grabado «1 kg» de la muestra NO incluido: no se puede hacer con fresa Ø9 a este tamaño (opcional por láser).",
        "6. Acabado de canto, esquina y aristas: PENDIENTE de confirmar (ver cajetín). Cantidad PENDIENTE: el nesting se calcula al confirmarla.",
        "7. Nesting: girar piezas 0/90/180º en el panel; NUNCA voltear (cara A siempre arriba). Separación mínima 9 mm.",
        "8. Uso decorativo. Gravitec NO APTO PARA USO ALIMENTARIO."])
    c.showPage(); c.save()

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    g, hole = pieza()
    plano(g, hole, f"{OUT}/{REF}_Plano.pdf"); dxf(g, hole, f"{OUT}/{REF}_Pieza01_Llavero.dxf")
    print("ok", medidas(g, hole))
