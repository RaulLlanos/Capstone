/* eslint-disable no-unused-vars */
// src/pages/TecnicoAuditoriaAdd.jsx
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

// Endpoints candidatos (ajusta si tu backend usa otros)
const AUDIT_LIST_ENDPOINTS = [
  "/api/auditorias/",
];
const AUDIT_POST_ENDPOINTS = [
  "/api/auditorias/",
];

async function findAuditByAsignacion(asignacionId) {
  // intenta varios endpoints con ?asignacion=<id>
  for (const ep of AUDIT_LIST_ENDPOINTS) {
    try {
      const res = await api.get(ep, { params: { asignacion: asignacionId } });
      const data = res.data;
      const list = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : [];
      if (list.length) return list[0]; // la más reciente / única
    } catch {
      // probar el siguiente
    }
  }
  return null;
}

async function createAudit(fd) {
  let lastErr;
  for (const ep of AUDIT_POST_ENDPOINTS) {
    try {
      return await api.post(ep, fd);
    } catch (err) {
      if (err?.response?.status === 404) {
        lastErr = err;
        continue;
      }
      throw err;
    }
  }
  throw lastErr;
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
    foto1: null,
    foto2: null,
    foto3: null,
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

        // prellenar nombre auditor
        const who = user?.name || user?.email || "";
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
    const { name, value, files } = e.target;
    if (files && files.length) setForm((f) => ({ ...f, [name]: files[0] }));
    else setForm((f) => ({ ...f, [name]: value }));
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

    try {
      setSaving(true);
      await api.get("/auth/csrf");

      const fd = new FormData();
      fd.append("asignacion", String(detalle.id));
      fd.append("nombre_auditor", form.nombre_auditor.trim());
      fd.append("estado_cliente", form.estado_cliente.trim());
      if (form.foto1) fd.append("foto1", form.foto1);
      if (form.foto2) fd.append("foto2", form.foto2);
      if (form.foto3) fd.append("foto3", form.foto3);

      await createAudit(fd);

      // Marcar la asignación como COMPLETADA
      try {
        await api.patch(`/api/asignaciones/${id}/`, { estado: "visitada" });
      } catch (err) {
        // si tu backend solo acepta PUT total:
        try {
          // traemos el objeto completo y reenviamos con estado cambiado
          const res = await api.get(`/api/asignaciones/${id}/`);
          const payload = { ...res.data, estado: "visitada" };
          await api.put(`/api/asignaciones/${id}/`, payload);
        } catch (_) {
          // no bloquear por esto
          console.warn("No se pudo marcar COMPLETADA, pero la auditoría fue creada.");
        }
      }

      // Ir a la vista de auditoría para esta asignación
      navigate(`/tecnico/auditoria/ver/${id}`, {
        replace: true,
        state: { flash: "Auditoría registrada y asignación completada." },
      });
    } catch (err) {
      console.error("POST auditoría:", err?.response?.status, err?.response?.data);
      const data = err?.response?.data || {};
      const msg = typeof data === "string" ? data : data.detail || data.error || "No se pudo registrar la auditoría.";
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
          <p className={styles.subtitle}>Se llenará con la dirección seleccionada al guardar.</p>
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
                <input className={styles.input} name="nombre_auditor" value={form.nombre_auditor} onChange={onChange} disabled={saving}/>
              </label>
              <label className={styles.label}>
                Estado cliente
                <input className={styles.input} name="estado_cliente" value={form.estado_cliente} onChange={onChange} disabled={saving}/>
              </label>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                <label className={styles.label} style={{ margin: 0 }}>
                  Foto 1
                  <input className={styles.input} type="file" name="foto1" accept="image/*" onChange={onChange} disabled={saving}/>
                </label>
                <label className={styles.label} style={{ margin: 0 }}>
                  Foto 2
                  <input className={styles.input} type="file" name="foto2" accept="image/*" onChange={onChange} disabled={saving}/>
                </label>
                <label className={styles.label} style={{ margin: 0 }}>
                  Foto 3
                  <input className={styles.input} type="file" name="foto3" accept="image/*" onChange={onChange} disabled={saving}/>
                </label>
              </div>

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
