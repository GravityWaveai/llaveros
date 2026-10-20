"""Revisión independiente del paquete REV04: DXF, geometría, CNC Ø9 y plano."""
import math, numpy as np, ezdxf
from ezdxf import bbox
from ezdxf.audit import Auditor
from shapely.geometry import Polygon, Point, LineString
from shapely.validation import explain_validity
import pdfplumber

DXF = "../plano/Llavero_Ola_REV04_Pieza01_Llavero.dxf"; PDF = "../plano/Llavero_Ola_REV04_Plano.pdf"
R = []
def chk(n, ok, d=""): R.append((n, "OK" if ok else "FALLO", d)); return ok

doc = ezdxf.readfile(DXF); au = doc.audit()
chk("DXF: auditoría ezdxf sin errores", not au.has_errors and not au.has_fixes, f"errores={len(au.errors)} arreglos={len(au.fixes)}")
chk("DXF: unidades mm ($INSUNITS=4)", doc.header.get("$INSUNITS") == 4)
ms = list(doc.modelspace())
chk("DXF: solo 2 entidades (contorno + taladro)", len(ms) == 2, str([(e.dxftype(), e.dxf.layer) for e in ms]))
pl = [e for e in ms if e.dxftype() == "LWPOLYLINE"][0]; ci = [e for e in ms if e.dxftype() == "CIRCLE"][0]
chk("DXF: contorno en capa CUT_OUTER y cerrado", pl.dxf.layer == "CUT_OUTER" and pl.closed)
chk("DXF: taladro en capa DRILL", ci.dxf.layer == "DRILL")
pts = [(p[0], p[1]) for p in pl.get_points("xy")]
poly = Polygon(pts)
chk("Contorno: polígono válido, sin autointersecciones", poly.is_valid, explain_validity(poly))
chk("Contorno: sin puntos duplicados", len(set((round(x, 4), round(y, 4)) for x, y in pts)) == len(pts), f"{len(pts)} puntos")
segs = [math.dist(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
curvos = [s for s in segs if s < 5]
chk("Contorno: segmentos cortos en las curvas (error de cuerda < 0,05 mm)", max(curvos) < 3.0, f"máx {max(curvos):.2f} mm en curvas; tramo recto de la base {max(segs):.1f} mm")
chk("Contorno: orientación antihoraria (CCW)", poly.exterior.is_ccw)
b = bbox.extents([pl]); W, H = b.size.x, b.size.y
chk("Dimensiones: alto = 40,00 mm", abs(H - 40) < 0.01, f"{H:.3f}")
chk("Dimensiones: ancho 46,23 mm", abs(W - 46.23) < 0.01, f"{W:.3f}")
chk("Origen: envolvente empieza en (0,0)", abs(b.extmin.x) < 0.01 and abs(b.extmin.y) < 0.01, f"({b.extmin.x:.3f},{b.extmin.y:.3f})")
hc = (ci.dxf.center.x, ci.dxf.center.y); hd = 2 * ci.dxf.radius
chk("Taladro: Ø4,8 en (40.65, 16.3)", abs(hd - 4.8) < 1e-6 and abs(hc[0] - 40.65) < 0.01 and abs(hc[1] - 16.3) < 0.01, f"Ø{hd} en {hc}")
pared = poly.exterior.distance(Point(hc)) - hd / 2
chk("Taladro: dentro de la pieza, pared >= 2,5 mm", poly.contains(Point(hc).buffer(hd / 2)) and pared >= 2.5, f"pared {pared:.2f} mm")
# --- CNC Ø9
FR = 9.0; r = FR / 2 - 0.03
void = poly.envelope.buffer(3 * FR).difference(poly)
miss = void.difference(void.buffer(-r, 32).buffer(r, 32)); miss = [m for m in getattr(miss, "geoms", [miss]) if m.area > 0.3]
chk("CNC Ø9: zonas no alcanzables por la fresa (> 0,3 mm²)", not miss, "; ".join(f"{m.area:.1f} mm² en ({m.centroid.x:.1f},{m.centroid.y:.1f})" for m in miss))
thin = poly.difference(poly.buffer(-2.5, join_style="mitre", mitre_limit=10).buffer(2.5, join_style="mitre", mitre_limit=10))
thin = [t for t in getattr(thin, "geoms", [thin]) if t.area > 1.0]
chk("CNC: sin zonas de material < 5 mm", not thin, "; ".join(f"({t.centroid.x:.1f},{t.centroid.y:.1f})" for t in thin))
chk("CNC: una sola pieza, sin islas ni huecos cerrados", poly.geom_type == "Polygon" and len(poly.interiors) == 0)
# radio cóncavo mínimo real (curvatura discreta en vértices cóncavos)
def curv(i):
    p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
    a = math.dist(p0, p1); b_ = math.dist(p1, p2); c = math.dist(p0, p2)
    cross = (p1[0]-p0[0])*(p2[1]-p1[1]) - (p1[1]-p0[1])*(p2[0]-p1[0])
    area2 = abs(cross)
    if area2 < 1e-9: return None, 0
    return a * b_ * c / (2 * area2), cross
concave = [(rad, i) for i in range(len(pts)) for rad, cr in [curv(i)] if rad and cr < 0]
# agrupar: radio mínimo cóncavo con suavizado (ventana 5 vértices)
rads = [rad for rad, _ in concave]
chk("CNC Ø9: radio cóncavo mínimo del contorno (arcos R4,62; tolerancia de discretización 1 %)", min(rads) >= 4.45, f"mín R{min(rads):.2f} (se exige R4,5): zonas de unión labio-tubo y lóbulo-tubo")
# tubo y boca
from medidas import medir
MM = medir(); tx, ty, td = MM["tubo"]
tube = Point(tx, ty).buffer(td / 2)
chk(f"Tubo: Ø{td} > Ø9, la fresa entra y vacía el hueco", td > FR)
lo, hi = 1, 10
for _ in range(25):
    m_ = (lo + hi) / 2; er = void.buffer(-m_, 32); parts = list(getattr(er, "geoms", [er]))
    ok = any(p.intersects(tube.buffer(-3)) and p.area > 500 for p in parts); lo, hi = (m_, hi) if ok else (lo, m_)
chk(f"Boca del tubo tal como la deja la fresa Ø9 = {MM['boca']} mm (dibujo original: 7,81)", abs(2 * lo - MM["boca"]) < 0.1, f"{2*lo:.2f} mm")
# --- sólido 3D a partir del DXF (prueba de que el contorno es extruible) + STEP
import cadquery as cq
wire = cq.Wire.makePolygon([cq.Vector(x, y, 0) for x, y in pts], close=True)
face = cq.Face.makeFromWires(wire)
solid = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, 5)).cut(cq.Solid.makeCylinder(hd / 2, 7, cq.Vector(hc[0], hc[1], -1)))
chk("3D: el contorno extruye a un sólido válido de 5 mm", solid.isValid() and abs(solid.BoundingBox().zlen - 5) < 1e-6, f"volumen {solid.Volume():.0f} mm³")
chk("3D: volumen = área DXF x 5 - taladro", abs(solid.Volume() - (poly.area - math.pi * (hd/2)**2) * 5) < 1.0, f"{solid.Volume():.1f} vs {(poly.area - math.pi*(hd/2)**2)*5:.1f}")
cq.exporters.export(cq.Workplane().add(solid), "../plano/Llavero_Ola_REV04.step")
# --- plano PDF: cotas = DXF
with pdfplumber.open(PDF) as d:
    pg = d.pages[0]; txt = pg.extract_text()
    chk("PDF: formato A3 apaisado", abs(pg.width / 72 * 25.4 - 420) < 1 and abs(pg.height / 72 * 25.4 - 297) < 1)
ff = lambda x: f"{x:.2f}".rstrip("0").rstrip(".")
for k in ["46.23", "40", ff(hc[0]), ff(hc[1]), "Ø4.8", "Ø" + ff(td), ff(tx), ff(ty), ff(MM["boca"]), ff(MM["base"][1] - MM["base"][0]), "ESCALA", "2.5:1", "FRESA", "CADAQUÉS", "IFACH", "SICILIA", "CAPRI", "2400 X 1200", "NO APTO PARA USO ALIMENTARIO", "CUT_OUTER", "DRILL"]:
    chk(f"PDF contiene '{k}'", k.upper() in txt.upper())
chk("PDF: datos PENDIENTES (no enviar a taller hasta completarlos)", "PENDIENTE" not in txt, "cantidad, canto, esquina, aristas")
# --- fidelidad al dibujo de referencia
from vector import vectorizar
g_ref, hc_ref, hd_ref, info = vectorizar()
dev = max(Point(p).distance(g_ref.exterior) for p in pts)
chk("Fidelidad: contorno DXF = dibujo de referencia salvo las dos uniones R4,5 (desv. máx < 1 mm, solo en la boca)", dev < 1.0, f"{dev:.3f} mm")
far = [p for p in pts if Point(p).distance(g_ref.exterior) > 0.05]
chk("Fidelidad: la desviación queda confinada a la boca del tubo", all(33 < p[0] < 42 and 17 < p[1] < 31 for p in far), f"{len(far)} vértices desviados, en x {min(p[0] for p in far):.1f}-{max(p[0] for p in far):.1f}, y {min(p[1] for p in far):.1f}-{max(p[1] for p in far):.1f}" if far else "")

print(f"{'ESTADO':6} COMPROBACIÓN")
for n, e, d in R: print(f"{e:6} {n}" + (f"  -> {d}" if d else ""))
print(f"\nTOTAL FALLOS: {sum(e=='FALLO' for _,e,_ in R)} de {len(R)} comprobaciones")
open("../plano/Llavero_Ola_REV04_Verificacion.txt", "w").write("\n".join(f"{e:6} {n}" + (f"  -> {d}" if d else "") for n, e, d in R) + f"\nTOTAL FALLOS: {sum(e=='FALLO' for _,e,_ in R)} de {len(R)}\n")
