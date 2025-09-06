// src/services/visitas.js
import api from "./api";

/**
 * Obtiene las visitas del técnico logueado para HOY.
 * Usa los filtros que expone el backend (?mias=1&fecha=YYYY-MM-DD).
 */
export async function fetchVisitasDeHoyMias() {
  const fecha = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
  const { data } = await api.get("/visitas/", {
    params: { mias: 1, fecha },
  });
  return data;
}

/**
 * Cambia el estado de la visita en el backend.
 * Estados válidos (según backend): programada | en_curso | completada | cancelada
 */
export async function patchEstadoVisita(id_visita, estado) {
  await api.patch(`/visitas/${id_visita}/estado/`, { estado });
}

/**
 * Reagenda una visita a una nueva fecha/hora.
 * Formatos: fecha = YYYY-MM-DD, hora = HH:MM (24h).
 */
export async function postReagendarVisita(id_visita, fecha, hora, motivo = "") {
  await api.post(`/visitas/${id_visita}/reagendar/`, { fecha, hora, motivo });
}
