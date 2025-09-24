// src/pages/AuditorDireccionEdit.jsx
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

const MARCAS = ["CLARO", "VTR"];
const TECNOLOGIAS = ["HFC", "NFTT", "FTTH"];
const ZONAS = ["NORTE", "CENTRO", "SUR"];
const ENCUESTAS = ["post_visita", "instalacion", "operaciones"];
const ESTADOS = ["PENDIENTE", "ASIGNADA", "COMPLETADA", "CANCELADA"]; // backend en uppercase

export default function AuditorDireccionEdit() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  if (user && (user.role || user.rol) !== "auditor") {
    // navigate("/");
  }

  const [form, setForm] = useState({
    fecha: "",
    direccion: "",
    comuna: "",
    zona: "",
    marca: "",
    tecnologia: "",
    rut_cliente: "",
    id_vivienda: "",
    encuesta: "",
    id_qualtrics: "",
    estado: "PENDIENTE",
    asignado_a: "", // email/identificador o vacío para null
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const res = await api.get(`/api/asignaciones/${id}/`);
        const d = res.data || {};
        setForm({
          fecha: d.fecha || "",
          direccion: d.direccion || "",
          comuna: d.comuna || "",
          zona: d.zona || "",
          marca: d.marca || "",
          tecnologia: d.tecnologia || "",
          rut_cliente: d.rut_cliente || "",
          id_vivienda: d.id_vivienda || "",
          encuesta: d.encuesta || "",
          id_qualtrics: d.id_qualtrics || "",
          estado: (d.estado || "PENDIENTE").toUpperCase(),
          asignado_a: d.asignado_a || "",
        });
      } catch (err) {
        console.error("GET detalle falló:", err?.response?.status, err?.response?.data);
        setError("No se pudo cargar la dirección.");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    setFieldErrors((fe) => ({ ...fe, [name]: "" }));
    setOk("");
    setError("");
  };

  const validate = () => {
    const fe = {};
    if (!form.fecha) fe.fecha = "Requerido.";
    if (!form.direccion.trim()) fe.direccion = "Requerido.";
    if (!form.comuna.trim()) fe.comuna = "Requerido.";
    if (!form.marca) fe.marca = "Requerido.";
    if (!form.tecnologia) fe.tecnologia = "Requerido.";
    if (!form.zona) fe.zona = "Requerido.";
    if (!form.rut_cliente.trim()) fe.rut_cliente = "Requerido.";
    if (!form.id_vivienda.trim()) fe.id_vivienda = "Requerido.";
    if (!form.encuesta) fe.encuesta = "Requerido.";
    if (!form.estado) fe.estado = "Requerido.";
    return fe;
  };

  // Construye SIEMPRE el objeto completo (evita KeyError en validadores del backend)
  const buildFullPayload = () => ({
    fecha: form.fecha,
    tecnologia: form.tecnologia,
    marca: form.marca,
    rut_cliente: form.rut_cliente.trim(),
    id_vivienda: form.id_vivienda.trim(),
    direccion: form.direccion.trim(),
    comuna: form.comuna.trim(),
    zona: form.zona,
    encuesta: form.encuesta,
    id_qualtrics: form.id_qualtrics.trim() || "",
    estado: String(form.estado || "PENDIENTE").toUpperCase(),
    // si va vacío, mejor null que string vacío
    asignado_a: form.asignado_a.trim() ? form.asignado_a.trim() : null,
  });

  const handleSave = async (e) => {
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
      await api.get("/auth/csrf");

      const payload = buildFullPayload();

      // Preferimos PUT (objeto completo) para satisfacer validadores que exigen todos los campos
      try {
        await api.put(`/api/asignaciones/${id}/`, payload);
      } catch (err) {
        // Si PUT no está permitido, intentamos PATCH con el mismo objeto completo
        if (err?.response?.status === 405) {
          await api.patch(`/api/asignaciones/${id}/`, payload);
        } else {
          throw err;
        }
      }

      setOk("Dirección actualizada correctamente.");
      // navigate(-1);
    } catch (err) {
      const data = err?.response?.data || {};
      const fe2 = {};
      if (data && typeof data === "object") {
        Object.entries(data).forEach(([k, v]) => {
          if (Array.isArray(v)) fe2[k] = v.join(" ");
          else if (typeof v === "string") fe2[k] = v;
        });
      }
      if (Object.keys(fe2).length) {
        setFieldErrors((old) => ({ ...old, ...fe2 }));
      } else {
        setError(data.detail || data.error || "No se pudo guardar.");
      }
      console.error("Guardar falló:", err?.response?.status, err?.response?.data);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 720 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Editar dirección #{id}</h1>
          <p className={styles.subtitle}>Modifica los datos necesarios</p>
        </header>

        {loading ? (
          <div className={styles.helper}>Cargando…</div>
        ) : (
          <form onSubmit={handleSave} className={styles.form}>
            <label className={styles.label}>
              Fecha programada
              <input className={styles.input} type="date" name="fecha" value={form.fecha} onChange={onChange} disabled={saving}/>
              {fieldErrors.fecha && <small className={styles.error}>{fieldErrors.fecha}</small>}
            </label>

            <label className={styles.label}>
              Dirección del cliente
              <input className={styles.input} name="direccion" value={form.direccion} onChange={onChange} disabled={saving}/>
              {fieldErrors.direccion && <small className={styles.error}>{fieldErrors.direccion}</small>}
            </label>

            <label className={styles.label}>
              Comuna
              <input className={styles.input} name="comuna" value={form.comuna} onChange={onChange} disabled={saving}/>
              {fieldErrors.comuna && <small className={styles.error}>{fieldErrors.comuna}</small>}
            </label>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
              <label className={styles.label} style={{ margin: 0 }}>
                Zona
                <select className={styles.select} name="zona" value={form.zona} onChange={onChange} disabled={saving}>
                  <option value="">— seleccionar —</option>
                  {ZONAS.map((z) => <option key={z} value={z}>{z[0] + z.slice(1).toLowerCase()}</option>)}
                </select>
                {fieldErrors.zona && <small className={styles.error}>{fieldErrors.zona}</small>}
              </label>

              <label className={styles.label} style={{ margin: 0 }}>
                Marca
                <select className={styles.select} name="marca" value={form.marca} onChange={onChange} disabled={saving}>
                  <option value="">— seleccionar —</option>
                  {MARCAS.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
                {fieldErrors.marca && <small className={styles.error}>{fieldErrors.marca}</small>}
              </label>

              <label className={styles.label} style={{ margin: 0 }}>
                Tecnología
                <select className={styles.select} name="tecnologia" value={form.tecnologia} onChange={onChange} disabled={saving}>
                  <option value="">— seleccionar —</option>
                  {TECNOLOGIAS.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
                {fieldErrors.tecnologia && <small className={styles.error}>{fieldErrors.tecnologia}</small>}
              </label>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <label className={styles.label} style={{ margin: 0 }}>
                RUT cliente
                <input className={styles.input} name="rut_cliente" value={form.rut_cliente} onChange={onChange} disabled={saving}/>
                {fieldErrors.rut_cliente && <small className={styles.error}>{fieldErrors.rut_cliente}</small>}
              </label>

              <label className={styles.label} style={{ margin: 0 }}>
                ID vivienda
                <input className={styles.input} name="id_vivienda" value={form.id_vivienda} onChange={onChange} disabled={saving}/>
                {fieldErrors.id_vivienda && <small className={styles.error}>{fieldErrors.id_vivienda}</small>}
              </label>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <label className={styles.label} style={{ margin: 0 }}>
                Encuesta de origen
                <select className={styles.select} name="encuesta" value={form.encuesta} onChange={onChange} disabled={saving}>
                  <option value="">— seleccionar —</option>
                  {ENCUESTAS.map((e) => <option key={e} value={e}>{e}</option>)}
                </select>
                {fieldErrors.encuesta && <small className={styles.error}>{fieldErrors.encuesta}</small>}
              </label>

              <label className={styles.label} style={{ margin: 0 }}>
                ID Qualtrics (opcional)
                <input className={styles.input} name="id_qualtrics" value={form.id_qualtrics} onChange={onChange} disabled={saving}/>
                {fieldErrors.id_qualtrics && <small className={styles.error}>{fieldErrors.id_qualtrics}</small>}
              </label>
            </div>

            {/* Estado y asignado_a */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <label className={styles.label} style={{ margin: 0 }}>
                Estado
                <select className={styles.select} name="estado" value={form.estado} onChange={onChange} disabled={saving}>
                  {ESTADOS.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
                {fieldErrors.estado && <small className={styles.error}>{fieldErrors.estado}</small>}
              </label>

              <label className={styles.label} style={{ margin: 0 }}>
                Asignado a (email o identificador)
                <input className={styles.input} name="asignado_a" value={form.asignado_a} onChange={onChange} disabled={saving} placeholder="ej: tecnico@dominio.cl"/>
                {fieldErrors.asignado_a && <small className={styles.error}>{fieldErrors.asignado_a}</small>}
              </label>
            </div>

            {error && <div className={styles.error}>{error}</div>}
            {ok && <div className={styles.success}>{ok}</div>}

            <div className={styles.actions}>
              <button type="submit" className={styles.button} disabled={saving}>{saving ? "Guardando…" : "Guardar cambios"}</button>
              <button type="button" className={styles.button} onClick={() => navigate(-1)} disabled={saving}>Volver</button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
