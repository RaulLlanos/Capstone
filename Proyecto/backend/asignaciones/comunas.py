# asignaciones/comunas.py
import unicodedata

def _norm(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.upper().strip()

# === Agrupación por zonas ===
_Z_NORTE = {
    "Independencia", "Recoleta", "Huechuraba", "Conchalí", "Quilicura", "Renca",
}
_Z_ORIENTE = {
    "Santiago","Estación Central","Pedro Aguirre Cerda","San Joaquín","San Miguel",
    "Providencia","Ñuñoa","Macul","La Reina","Quinta Normal","Lo Prado",
}
_Z_SUR = {
    "La Florida", "Puente Alto", "San Bernardo", "La Pintana", "El Bosque",
    "La Cisterna", "La Granja", "Lo Espejo", "San Ramón", "Maipú", "Cerrillos", "Pudahuel", "Peñalolén",
}

_COMUNAS_CONJUNTO = _Z_NORTE | _Z_ORIENTE | _Z_SUR

# Mapa normalizado → zona
_MAP = {}
for zona, conjunto in (("NORTE", _Z_NORTE), ("ORIENTE", _Z_ORIENTE), ("SUR", _Z_SUR)):
    for nombre in conjunto:
        _MAP[_norm(nombre)] = zona

# Choices para UI/serializer/admin
COMUNAS_SANTIAGO = sorted(_COMUNAS_CONJUNTO)

def zona_para_comuna(comuna: str) -> str:
    z = _MAP.get(_norm(comuna))
    if not z:
        raise ValueError("Comuna no soportada para Santiago")
    return z
