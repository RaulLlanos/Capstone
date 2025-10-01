/* eslint-disable no-unused-vars */
// src/pages/TecnicoReagendar.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

const BLOQUES = [
  { value: "10-13", label: "10:00–13:00" },
  { value: "14-18", label: "14:00–18:00" },
];

// normaliza lista o paginación DRF
function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

export default function TecnicoReagendar() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { id: routeId } = useParams(); // puede venir undefined
  const [asignaciones, setAsignaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ok, setOk] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const fetchId = useRef(0);

  const [form, setForm] = useState({
    asignacion_id: "",   // string (id)
    fecha: "",           // YYYY-MM-DD
    bloque: "",          // "10-13" | "14-18"
    motivo: "",          // opcional, por si tu backend lo acepta en /reagendar/
  });

  // Carga "mis asignaciones"
  const loadMine = async () => {
    setLoading(true);
    setError("");
    const myFetch = ++fetchId.current;
    try {
      const res = await api.get("/api/asignaciones/mias/");
      if (myFetch !== fetchId.current) return;
      setAsignaciones(normalizeList(res.data));
    } catch (e) {
      console.error(e);
      setError("No se pudieron cargar tus asignaciones.");
      setAsignaciones([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMine();
  }, []);

  // Preselección si viene :id en la ruta
  useEffect(() => {
    if (routeId) {
      setForm((f) => ({ ...f, asignacion_id: String(routeId) }));
      setOk("");
      setError("");
      setFieldErrors({});
    }
  }, [routeId]);

  // Asignación seleccionada
  const selected = useMemo(
    () => asignaciones.find((a) => String(a.id) === String(form.asignacion_id)),
    [asignaciones, form.asignacion_id]
  );

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    setFieldErrors((fe) => ({ ...fe, [name]: "" }));
    setOk("");
    setError("");
  };

  const validate = () => {
    const fe = {};
    if (!form.asignacion_id) fe.asignacion_id = "Selecciona una asignación.";
    if (!form.fecha) fe.fecha = "Selecciona la nueva fecha.";
    if (!form.bloque) fe.bloque = "Selecciona el nuevo bloque.";
    return fe;
  };

  // Enviar reagendamiento por la acción oficial del ViewSet
  const enviarReagendar = async () => {
    const id = form.asignacion_id;
    const payload = { fecha: form.fecha, bloque: form.bloque };
    // si tu backend acepta motivo en este endpoint, lo incluimos:
    if (form.motivo.trim()) payload.motivo = form.motivo.trim();
    return api.post(`/api/asignaciones/${id}/reagendar/`, payload);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setOk("");
    setError("");
    setFieldErrors({});

    const fe = validate();
    if (Object.keys(fe).length) {
      setFieldErrors(fe);
      return;
    }

    try {
      setSaving(true);
      await api.get("/auth/csrf").catch(() => {});
      await enviarReagendar();
      setOk("Reagendamiento enviado correctamente.");
      // limpiamos campos de acción; mantenemos la selección
      setForm((f) => ({ ...f, fecha: "", bloque: "", motivo: "" }));
      // refrescamos por si cambió el estado/reagendado_*
      await loadMine();
    } catch (err) {
      const data = err?.response?.data || {};
      const fe2 = {};
      if (data && typeof data === "object") {
        Object.entries(data).forEach(([k, v]) => {
          if (Array.isArray(v)) fe2[k] = v.join(" ");
          else if (typeof v === "string") fe2[k] = v;
        });
      }
      if (Object.keys(fe2).length) setFieldErrors((old) => ({ ...old, ...fe2 }));
      else setError(data.detail || data.error || "No se pudo reagendar.");
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const showSelector = !routeId; // si vino :id, ocultamos el dropdown

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 720 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Reagendar visita</h1>
          <p className={styles.subtitle}>
            {showSelector
              ? "Elige una de tus asignaciones y define nueva fecha/bloque."
              : `Asignación #${routeId}: define la nueva fecha y bloque.`}
          </p>
        </header>

        {error && <div className={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit} className={styles.form}>
          {/* Selector de asignación (solo cuando no viene :id) */}
          {showSelector ? (
            <label className={styles.label}>
              Asignación
              <select
                className={styles.select}
                name="asignacion_id"
                value={form.asignacion_id}
                onChange={onChange}
                disabled={loading || saving}
              >
                <option value="">— Selecciona —</option>
                {asignaciones.map((a) => (
                  <option key={a.id} value={a.id}>
                    #{a.id} · {a.fecha} · {a.comuna} · {a.direccion}
                  </option>
                ))}
              </select>
              {fieldErrors.asignacion_id && (
                <small className={styles.error}>{fieldErrors.asignacion_id}</small>
              )}
            </label>
          ) : (
            // Resumen compacto cuando viene :id
            <div
              style={{
                border: "1px solid #e5e7eb",
                borderRadius: 10,
                padding: 12,
                display: "grid",
                gap: 4,
                marginBottom: 4,
              }}
            >
              {selected ? (
                <>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <strong>#{selected.id} · {selected.direccion}</strong>
                    <small className={styles.helper}>
                      {String(selected.fecha).slice(0, 10)} · {String(selected.estado || "").toUpperCase()}
                    </small>
                  </div>
                  <div className={styles.helper}>
                    Comuna: {selected.comuna} — Zona: {selected.zona} — Marca: {selected.marca} — Tec.: {selected.tecnologia}
                  </div>
                  {(selected.reagendado_fecha || selected.reagendado_bloque) && (
                    <div className={styles.helper}>
                      Reagendado actual: {selected.reagendado_fecha || "—"} {selected.reagendado_bloque ? `· ${selected.reagendado_bloque}` : ""}
                    </div>
                  )}
                </>
              ) : (
                <div className={styles.helper}>
                  {loading
                    ? "Cargando asignación…"
                    : "Esta asignación no pertenece a tu usuario o no existe."}
                </div>
              )}
              {/* Campo oculto: mantenemos el id para submit */}
              <input type="hidden" name="asignacion_id" value={form.asignacion_id} />
            </div>
          )}

          {/* Fecha nueva */}
          <label className={styles.label}>
            Fecha nueva
            <input
              type="date"
              className={styles.input}
              name="fecha"
              value={form.fecha}
              onChange={onChange}
              disabled={saving}
            />
            {fieldErrors.fecha && <small className={styles.error}>{fieldErrors.fecha}</small>}
          </label>

          {/* Bloque nuevo */}
          <label className={styles.label}>
            Bloque nuevo
            <select
              className={styles.select}
              name="bloque"
              value={form.bloque}
              onChange={onChange}
              disabled={saving}
            >
              <option value="">— Selecciona —</option>
              {BLOQUES.map((b) => (
                <option key={b.value} value={b.value}>{b.label}</option>
              ))}
            </select>
            {fieldErrors.bloque && <small className={styles.error}>{fieldErrors.bloque}</small>}
          </label>

          {/* Motivo (opcional) */}
          <label className={styles.label}>
            Motivo (opcional)
            <textarea
              className={styles.input}
              name="motivo"
              rows={3}
              value={form.motivo}
              onChange={onChange}
              placeholder="Cliente reagenda, sin moradores, contingencia, etc."
              disabled={saving}
            />
            {fieldErrors.motivo && <small className={styles.error}>{fieldErrors.motivo}</small>}
          </label>

          {ok && <div className={styles.success}>{ok}</div>}

          <div className={styles.actions}>
            <button type="submit" className={styles.button} disabled={saving || loading || (!showSelector && !selected)}>
              {saving ? "Enviando…" : "Reagendar"}
            </button>
            <button
              type="button"
              className={styles.button}
              onClick={() => navigate(-1)}
              disabled={saving}
              style={{ background: "#6b7280" }}
            >
              Volver
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
