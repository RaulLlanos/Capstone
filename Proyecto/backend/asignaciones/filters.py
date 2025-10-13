from django.utils import timezone
import django_filters as filters
from django.db.models import Q
from asignaciones.models import HistorialAsignacion

def _parse_dateish(value):
    if not value:
        return None
    v = str(value).strip()
    if v.upper() == "HOY":
        return timezone.localdate()
    # Acepta YYYY-MM-DD
    try:
        from datetime import datetime
        return datetime.strptime(v, "%Y-%m-%d").date()
    except Exception:
        pass
    # Acepta DD-MM-YYYY
    try:
        from datetime import datetime
        return datetime.strptime(v, "%d-%m-%Y").date()
    except Exception:
        return None

class HistorialAsignacionFilter(filters.FilterSet):
    # Campos directos sobre la asignación relacionada
    estado = filters.CharFilter(field_name="asignacion__estado", label="Estado")
    marca = filters.CharFilter(field_name="asignacion__marca", label="Marca")
    tecnologia = filters.CharFilter(field_name="asignacion__tecnologia", label="Tecnología")
    comuna = filters.CharFilter(field_name="asignacion__comuna", label="Comuna")
    zona = filters.CharFilter(field_name="asignacion__zona", label="Zona")
    encuesta = filters.CharFilter(field_name="asignacion__encuesta", label="Encuesta de origen")

    # Técnico: coincide si lo registró o si la asignación era suya
    tecnico_id = filters.NumberFilter(method="filter_tecnico", label="Técnico asignado (ID)")

    # Rangos por fecha programada (asignación)
    desde = filters.CharFilter(method="filter_fecha_prog_desde", label="Fecha (desde) YYYY-MM-DD o HOY")
    hasta = filters.CharFilter(method="filter_fecha_prog_hasta", label="Fecha (hasta) YYYY-MM-DD o HOY")

    # Rangos por creado del historial
    creado_desde = filters.CharFilter(method="filter_creado_desde", label="Historial creado (desde)")
    creado_hasta = filters.CharFilter(method="filter_creado_hasta", label="Historial creado (hasta)")

    class Meta:
        model = HistorialAsignacion
        fields = [
            "estado", "marca", "tecnologia", "comuna", "zona", "encuesta",
            "tecnico_id", "desde", "hasta", "creado_desde", "creado_hasta"
        ]

    def filter_tecnico(self, qs, name, value):
        return qs.filter(Q(usuario_id=value) | Q(asignacion__asignado_a_id=value))

    def filter_fecha_prog_desde(self, qs, name, value):
        d = _parse_dateish(value)
        return qs.filter(asignacion__fecha__gte=d) if d else qs

    def filter_fecha_prog_hasta(self, qs, name, value):
        d = _parse_dateish(value)
        return qs.filter(asignacion__fecha__lte=d) if d else qs

    def filter_creado_desde(self, qs, name, value):
        d = _parse_dateish(value)
        return qs.filter(created_at__date__gte=d) if d else qs

    def filter_creado_hasta(self, qs, name, value):
        d = _parse_dateish(value)
        return qs.filter(created_at__date__lte=d) if d else qs
