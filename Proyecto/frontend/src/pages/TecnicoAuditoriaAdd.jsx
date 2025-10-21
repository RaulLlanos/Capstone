/* eslint-disable no-unused-vars */
// src/pages/TecnicoAuditoriaAdd.jsx
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

// ===== Constantes del backend (según OpenAPI nuevo) =====
const ESTADO_CLIENTE_OPCIONES = [
  { v: "autoriza", label: "Autoriza" },
  { v: "sin_moradores", label: "Sin moradores" },
  { v: "rechaza", label: "Rechaza" },
  { v: "contingencia", label: "Contingencia" },
  { v: "masivo", label: "Incidencia masivo" },
  { v: "reagendo", label: "Reagendó" },
];

const BLOQUES = ["10-13", "14-18"];

// ===== Helpers =====
function mapEstadoAsignacion(estadoCliente) {
  switch (estadoCliente) {
    case "autoriza":
      return "VISITADA";
    case "reagendo":
      return "REAGENDADA";
    case "sin_moradores":
    case "rechaza":
    case "contingencia":
    case "masivo":
      return "CANCELADA";
    default:
      return undefined;
  }
}

async function findAuditByAsignacion(asignacionId) {
  // Intento 1: filtro directo por asignacion (común en DRF)
  try {
    const r = await api.get("/api/auditorias/", {
      params: { asignacion: asignacionId },
    });
    const data = r.data;
    const list = Array.isArray(data?.results)
      ? data.results
      : Array.isArray(data)
      ? data
      : [];
    if (list.length) return list[0];
  } catch (_) { /* empty */ }

  // Intento 2: algunos setups usan asignacion__id
  try {
    const r = await api.get("/api/auditorias/", {
      params: { "asignacion__id": asignacionId },
    });
    const data = r.data;
    const list = Array.isArray(data?.results)
      ? data.results
      : Array.isArray(data)
      ? data
      : [];
    if (list.length) return list[0];
  } catch (_) { /* empty */ }

  // Intento 3: usar search si está habilitado
  try {
    const r = await api.get("/api/auditorias/", {
      params: { search: String(asignacionId) },
    });
    const data = r.data;
    const list = Array.isArray(data?.results)
      ? data.results
      : Array.isArray(data)
      ? data
      : [];
    const hit = list.find((a) => Number(a.asignacion) === Number(asignacionId));
    if (hit) return hit;
  } catch (_) { /* empty */ }

  return null;
}

export default function TecnicoAuditoriaAdd() {
  const { id } = useParams(); // id de asignación
  const navigate = useNavigate();
  const { user } = useAuth();

  const [detalle, setDetalle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    nombre_auditor: "",
    estado_cliente: "",
    reagendado_fecha: "",
    reagendado_bloque: "",
  });

  // Si ya existe auditoría, redirige a la vista
  useEffect(() => {
    (async () => {
      try {
        setLoading(true);

        // 1) Carga asignación
        const res = await api.get(`/api/asignaciones/${id}/`);
        setDetalle(res.data || {});

        // 2) Busca auditoría existente para esta asignación
        const existing = await findAuditByAsignacion(id);
        if (existing) {
          navigate(`/tecnico/auditoria/ver/${id}`, { replace: true });
          return;
        }

        // prellenar nombre auditor (solo UI)
        const who = user?.name || user?.first_name || user?.email || "";
        if (who) setForm((f) => ({ ...f, nombre_auditor: who }));
      } catch (err) {
        console.error("GET asignación:", err?.response?.status, err?.response?.data);
        setError("No se pudo cargar la asignación.");
      } finally {
        setLoading(false);
      }
    })();
  }, [id, user, navigate]);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!detalle?.id) {
      setError("Asignación no cargada.");
      return;
    }
    if (!form.nombre_auditor.trim()) {
      setError("Ingresa tu nombre (auditor).");
      return;
    }
    if (!form.estado_cliente) {
      setError("Selecciona el estado del cliente.");
      return;
    }
    if (form.estado_cliente === "reagendo") {
      if (!form.reagendado_fecha) {
        setError("Debes indicar la fecha para reagendar.");
        return;
      }
      if (!form.reagendado_bloque) {
        setError("Debes indicar el bloque para reagendar.");
        return;
      }
    }

    try {
      setSaving(true);
      await api.get("/auth/csrf").catch(() => {});

      // payload JSON según schema
      const payload = {
        asignacion: Number(detalle.id),
        estado_cliente: form.estado_cliente,
      };
      if (form.estado_cliente === "reagendo") {
        payload.reagendado_fecha = form.reagendado_fecha; // YYYY-MM-DD
        payload.reagendado_bloque = form.reagendado_bloque; // 10-13 | 14-18
      }

      await api.post("/api/auditorias/", payload);

      // Best-effort: actualizar estado de la asignación
      const nuevoEstado = mapEstadoAsignacion(form.estado_cliente);
      if (nuevoEstado) {
        try {
          await api.patch(`/api/asignaciones/${id}/`, { estado: nuevoEstado });
        } catch (err) {
          // Si no hay permiso de PATCH para técnico, no bloquear el flujo
          console.warn("PATCH estado asignación rechazado (se ignora):", err?.response?.status);
        }
      }

      // Ir a la vista de auditoría para esta asignación
      navigate(`/tecnico/auditoria/ver/${id}`, {
        replace: true,
        state: { flash: "Auditoría registrada." },
      });
    } catch (err) {
      console.error("POST auditoría:", err?.response?.status, err?.response?.data);
      const data = err?.response?.data || {};
      const msg =
        typeof data === "string"
          ? data
          : data.detail ||
            data.error ||
            "No se pudo registrar la auditoría.";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const Row = ({ label, children }) => (
    <div style={{ display: "grid", gridTemplateColumns: "160px 1fr", gap: 8 }}>
      <div className={styles.helper} style={{ fontWeight: 600 }}>{label}</div>
      <div className={styles.helper}>{children || "—"}</div>
    </div>
  );

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 720 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Auditoría de instalación</h1>
          <p className={styles.subtitle}>Se vinculará a la dirección seleccionada al guardar.</p>
        </header>

        {loading ? (
          <div className={styles.helper}>Cargando…</div>
        ) : (
          <>
            <div style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 12, marginBottom: 12 }}>
              <div className={styles.helper} style={{ fontWeight: 700, marginBottom: 6 }}>
                Dirección / Asignación
              </div>
              <Row label="Dirección">{detalle?.direccion}</Row>
              <Row label="Comuna">{detalle?.comuna}</Row>
              <Row label="Marca">{detalle?.marca}</Row>
              <Row label="Tecnología">{detalle?.tecnologia}</Row>
              <Row label="RUT cliente">{detalle?.rut_cliente}</Row>
              <Row label="ID vivienda">{detalle?.id_vivienda}</Row>
              <Row label="Fecha">{String(detalle?.fecha || "").slice(0,10)}</Row>
              <Row label="Estado">{detalle?.estado}</Row>
            </div>

            <form onSubmit={handleSubmit} className={styles.form}>
              <label className={styles.label}>
                Nombre auditor
                <input
                  className={styles.input}
                  name="nombre_auditor"
                  value={form.nombre_auditor}
                  onChange={onChange}
                  disabled={saving}
                />
              </label>

              <label className={styles.label}>
                Estado cliente
                <select
                  className={styles.input}
                  name="estado_cliente"
                  value={form.estado_cliente}
                  onChange={onChange}
                  disabled={saving}
                >
                  <option value="">Selecciona…</option>
                  {ESTADO_CLIENTE_OPCIONES.map((o) => (
                    <option key={o.v} value={o.v}>{o.label}</option>
                  ))}
                </select>
              </label>

              {form.estado_cliente === "reagendo" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                  <label className={styles.label} style={{ margin: 0 }}>
                    Fecha reagendada
                    <input
                      className={styles.input}
                      type="date"
                      name="reagendado_fecha"
                      value={form.reagendado_fecha}
                      onChange={onChange}
                      disabled={saving}
                    />
                  </label>
                  <label className={styles.label} style={{ margin: 0 }}>
                    Bloque
                    <select
                      className={styles.input}
                      name="reagendado_bloque"
                      value={form.reagendado_bloque}
                      onChange={onChange}
                      disabled={saving}
                    >
                      <option value="">Selecciona…</option>
                      {BLOQUES.map((b) => (
                        <option key={b} value={b}>{b}</option>
                      ))}
                    </select>
                  </label>
                </div>
              )}

              {error && <div className={styles.error}>{error}</div>}

              <div className={styles.actions}>
                <button type="submit" className={styles.button} disabled={saving}>
                  {saving ? "Guardando…" : "Guardar auditoría"}
                </button>
                <button type="button" className={styles.button} onClick={() => navigate(-1)} disabled={saving}>
                  Volver
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
