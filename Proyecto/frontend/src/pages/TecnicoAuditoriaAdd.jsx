/* eslint-disable no-unused-vars */
// src/pages/TecnicoAuditoriaAdd.jsx
import { useEffect, useState, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

// ENUM del backend (OpenAPI)
const ESTADOS_CLIENTE = [
  { value: "autoriza", label: "Autoriza a ingresar" },
  { value: "sin_moradores", label: "Sin Moradores" },
  { value: "rechaza", label: "Rechaza" },
  { value: "contingencia", label: "Contingencia externa" },
  { value: "masivo", label: "Incidencia masivo" },
  { value: "reagendo", label: "Reagendó" },
];

// util: YYYY-MM-DD local
function todayLocalYMD() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export default function TecnicoAuditoriaAdd() {
  const { id } = useParams(); // id de asignación
  const navigate = useNavigate();
  const { user } = useAuth();

  const [detalle, setDetalle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [flash, setFlash] = useState("");

  // Form mínimo compatible con el backend actual
  const [form, setForm] = useState({
    estado_cliente: "",
    // ocultos/condicionales para reagendo
    reagendado_fecha: todayLocalYMD(),
    reagendado_bloque: "10-13", // valores válidos: "10-13" | "14-18"
  });

  const requiereReagendo = form.estado_cliente === "reagendo";

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const res = await api.get(`/api/asignaciones/${id}/`);
        setDetalle(res.data || {});
      } catch (err) {
        console.error("GET asignación:", err?.response?.status, err?.response?.data);
        setError("No se pudo cargar la asignación.");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

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
    if (!form.estado_cliente) {
      setError("Selecciona el estado del cliente.");
      return;
    }
    if (requiereReagendo) {
      if (!form.reagendado_fecha || !form.reagendado_bloque) {
        setError("Para reagendar debes indicar fecha y bloque.");
        return;
      }
    }

    try {
      setSaving(true);
      await api.get("/auth/csrf").catch(() => {});

      // 1) Crear auditoría mínima: asignacion + estado_cliente
      const fd = new FormData();
      fd.append("asignacion", String(detalle.id));
      fd.append("estado_cliente", form.estado_cliente);
      // (El backend tiene MUCHOS campos opcionales; no los enviamos y pasan las validaciones.)

      await api.post("/api/auditorias/", fd);

      // 2) Sincronizar el estado de la asignación con el endpoint oficial:
      //    /api/asignaciones/{id}/estado_cliente/
      //    - Si es "reagendo", exige reagendado_fecha + reagendado_bloque (OpenAPI actual).
      const payload = requiereReagendo
        ? {
            estado_cliente: "reagendo",
            reagendado_fecha: form.reagendado_fecha,
            reagendado_bloque: form.reagendado_bloque,
          }
        : { estado_cliente: form.estado_cliente };

      try {
        await api.post(`/api/asignaciones/${id}/estado_cliente/`, payload);
      } catch (err) {
        // No bloquear la UX si falla, pero informar en consola
        console.warn("No se pudo actualizar estado de asignación:", err?.response?.status, err?.response?.data);
      }

      // 3) Ir a la vista (si la tienes) o volver con flash
      setFlash("Auditoría registrada.");
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
          : data.detail || data.error || "No se pudo registrar la auditoría.";
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
          <p className={styles.subtitle}>Usa el estado del cliente según lo observado en la visita.</p>
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
              <Row label="Fecha">{String(detalle?.fecha || "").slice(0, 10)}</Row>
              <Row label="Estado">{detalle?.estado}</Row>
            </div>

            <form onSubmit={handleSubmit} className={styles.form}>
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
                  {ESTADOS_CLIENTE.map((e) => (
                    <option key={e.value} value={e.value}>{e.label}</option>
                  ))}
                </select>
              </label>

              {requiereReagendo && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                  <label className={styles.label} style={{ margin: 0 }}>
                    Fecha (YYYY-MM-DD)
                    <input
                      className={styles.input}
                      name="reagendado_fecha"
                      value={form.reagendado_fecha}
                      onChange={onChange}
                      disabled={saving}
                      placeholder="YYYY-MM-DD"
                      type="date"
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
                      <option value="10-13">10:00-13:00</option>
                      <option value="14-18">14:00-18:00</option>
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
