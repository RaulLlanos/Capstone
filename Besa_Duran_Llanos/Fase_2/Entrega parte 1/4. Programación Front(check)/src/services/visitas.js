// src/services/visitas.js
import api from "./api";

/**
 * Normaliza los campos tal como vienen del backend actual.
 * (Si luego cambian nombres, solo tocas esta función.)
 */
function normalizeVisita(v) {
  return {
    id_visita: v.id_visita ?? v.id ?? v.pk,
    cliente_nombre: [v.cliente_nombre, v.cliente_apellido].filter(Boolean).join(" "),
    cliente_direccion: v.cliente_direccion ?? "",
    fecha_programada: v.fecha_programada ?? "", // YYYY-MM-DD
    hora_programada: v.hora_programada ?? "",   // HH:MM:SS
    estado: String(v.estado || "programada").toLowerCase(),
    tipo_servicio: v.tipo_servicio ?? "",
  };
}

/**
 * Trae visitas desde /api/visitas/ y filtra por HOY (fecha_programada == hoy)
 * Si prefieres ver todas, quita el filtro por fecha.
 */
export async function fetchVisitasDeHoy() {
  const { data } = await api.get("/api/visitas/");
  const list = Array.isArray(data) ? data : (Array.isArray(data?.results) ? data.results : []);
  const hoy = new Date().toISOString().slice(0, 10);
  return list.map(normalizeVisita).filter(v => (v.fecha_programada || "").startsWith(hoy));
}

/**
 * Cambia estado de la visita con PATCH /api/visitas/:id/
 */
export async function patchEstadoVisita(id_visita, nuevoEstado) {
  await api.patch(`/api/visitas/${id_visita}/`, { estado: nuevoEstado });
}

/**
 * Reagendar: opción A (simple) — actualiza la visita directamente
 * Si quieres registrar el histórico, usa createReagendamiento() de abajo.
 */
export async function patchReagendarVisita(id_visita, fechaNueva /* YYYY-MM-DD */, horaNueva /* HH:mm */) {
  const payload = {
    fecha_programada: fechaNueva,
    hora_programada: `${horaNueva}:00`, // el backend usa TimeField
    estado: "reagendada",
  };
  await api.patch(`/api/visitas/${id_visita}/`, payload);
}

/**
 * Reagendar: opción B (con histórico) — crea registro en /api/reagendamientos/
 * Necesitas la info anterior y el id de usuario (backend exige FK usuario).
 */
export async function createReagendamiento({
  visita_id,
  fecha_anterior, // YYYY-MM-DD
  hora_anterior,  // HH:mm
  fecha_nueva,    // YYYY-MM-DD
  hora_nueva,     // HH:mm
  motivo,
  usuario_id,     // id del usuario logueado (si tu backend lo requiere)
}) {
  const body = {
    visita: visita_id,
    fecha_anterior,
    hora_anterior: `${hora_anterior}:00`,
    fecha_nueva,
    hora_nueva: `${hora_nueva}:00`,
    motivo,
    usuario: usuario_id,
  };
  await api.post("/api/reagendamientos/", body);
}
