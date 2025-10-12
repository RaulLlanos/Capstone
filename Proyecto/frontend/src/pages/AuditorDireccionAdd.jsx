// src/pages/AuditorDireccionAdd.jsx
import { useMemo, useState } from "react";
//import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

// Choices del backend (models.TextChoices)
const MARCAS = [
  { value: "CLARO", label: "CLARO" },
  { value: "VTR",   label: "VTR"   },
];

const TECNOLOGIAS = [
  { value: "HFC",  label: "HFC"  },
  { value: "NFTT", label: "NFTT" },
  { value: "FTTH", label: "FTTH" },
];

const ZONAS = [
  { value: "NORTE",  label: "Norte"  },
  { value: "CENTRO", label: "Centro" },
  { value: "SUR",    label: "Sur"    },
];

// Comunas de Santiago agrupadas por zona (ajústalas si quieres)
const COMUNAS_POR_ZONA = {
  NORTE: [
    "Huechuraba", "Recoleta", "Independencia", "Conchalí",
    "Quilicura", "Renca", "Vitacura", "Las Condes", "Lo Barnechea"
  ],
  CENTRO: [
    "Santiago", "Providencia", "Ñuñoa", "Macul", "La Reina",
    "Estación Central", "Quinta Normal", "Pedro Aguirre Cerda",
    "San Miguel", "Cerrillos", "Maipú", "Pudahuel", "Lo Prado"
  ],
  SUR: [
    "San Joaquín", "La Cisterna", "San Ramón", "La Granja",
    "El Bosque", "La Pintana", "Lo Espejo", "San Bernardo",
    "Puente Alto", "Pirque"
  ],
};

const ENCUESTAS = [
  { value: "post_visita", label: "Post visita"   },
  { value: "instalacion", label: "Instalación"   },
  { value: "operaciones", label: "Operaciones"   },
];

// Intentaremos ambos endpoints según cómo esté registrado el router:
const CANDIDATE_ENDPOINTS = ["/api/asignaciones/"];

export default function AuditorDireccionAdd() {
  const { user } = useAuth();
  //const navigate = useNavigate();

  // (defensa extra; igual protege la ruta en AppRouter)
  if (user && (user.rol || user.role) !== "auditor") {
    // navigate("/"); // opcional
  }

  const [form, setForm] = useState({
    fecha: "",            // YYYY-MM-DD
    direccion: "",        // "direccion" en modelo = Dirección del cliente
    comuna: "",
    zona: "",
    marca: "",
    tecnologia: "",
    rut_cliente: "",
    id_vivienda: "",
    encuesta: "",
    id_qualtrics: "",
  });

  const [loading, setLoading] = useState(false);
  const [ok, setOk] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  // Comunas disponibles según la zona elegida
  const comunasOptions = useMemo(
    () => (COMUNAS_POR_ZONA[form.zona] ?? []),
    [form.zona]
  );

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => {
      if (name === "zona") {
        const nuevas = COMUNAS_POR_ZONA[value] ?? [];
        const comunaValida = nuevas.includes(f.comuna) ? f.comuna : "";
        return { ...f, zona: value, comuna: comunaValida };
      }
      return { ...f, [name]: value };
    });
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
    return fe;
    // Nota: 'id_qualtrics' es opcional según el modelo.
  };

  // Post con fallback de endpoint
  const postDireccion = async (payload) => {
    let lastErr;
    for (const path of CANDIDATE_ENDPOINTS) {
      try {
        return await api.post(path, payload);
      } catch (err) {
        const status = err?.response?.status;
        lastErr = err;
        if (status === 404) continue; // intenta el siguiente
        throw err;
      }
    }
    throw lastErr;
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
      setLoading(true);
      await api.get("/auth/csrf");

      // Nombres EXACTOS que espera el serializer:
      const payload = {
        fecha: form.fecha,                                  // DateField
        tecnologia: form.tecnologia,                        // CharField (choice)
        marca: form.marca,                                  // CharField (choice)
        rut_cliente: form.rut_cliente.trim(),               // CharField
        id_vivienda: form.id_vivienda.trim(),               // CharField
        direccion: form.direccion.trim(),                   // CharField
        comuna: form.comuna.trim(),                         // CharField
        zona: form.zona,                                    // CharField (choice)
        encuesta: form.encuesta,                            // CharField (choice)
        id_qualtrics: form.id_qualtrics.trim() || "",       // CharField (blank ok)
        // NO enviar: estado, reagendado_fecha, reagendado_bloque, asignado_a
      };

      await postDireccion(payload);

      setOk("Dirección creada correctamente.");
      setForm({
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
      });
      // opcional: navegar al listado
      // navigate("/auditor/direcciones");
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
      else setError(data.detail || data.error || "No se pudo crear la dirección.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 720 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Añadir Dirección</h1>
          <p className={styles.subtitle}>Información del cliente</p>
        </header>

        <form onSubmit={handleSubmit} className={styles.form}>
          <label className={styles.label}>
            Fecha programada
            <input
              className={styles.input}
              type="date"
              name="fecha"
              value={form.fecha}
              onChange={onChange}
              disabled={loading}
            />
            {fieldErrors.fecha && <small className={styles.error}>{fieldErrors.fecha}</small>}
          </label>

          <label className={styles.label}>
            Dirección del cliente
            <input
              className={styles.input}
              name="direccion"
              value={form.direccion}
              onChange={onChange}
              disabled={loading}
            />
            {fieldErrors.direccion && <small className={styles.error}>{fieldErrors.direccion}</small>}
          </label>

          {/* Comuna dependiente de Zona */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
            <label className={styles.label} style={{ margin: 0 }}>
              Zona
              <select
                className={styles.select}
                name="zona"
                value={form.zona}
                onChange={onChange}
                disabled={loading}
              >
                <option value="">— Seleccionar —</option>
                {ZONAS.map((z) => (
                  <option key={z.value} value={z.value}>{z.label}</option>
                ))}
              </select>
              {fieldErrors.zona && <small className={styles.error}>{fieldErrors.zona}</small>}
            </label>

            <label className={styles.label} style={{ margin: 0 }}>
              Comuna
              <select
                className={styles.select}
                name="comuna"
                value={form.comuna}
                onChange={onChange}
                disabled={loading || !form.zona}
              >
                <option value="">{form.zona ? "— Seleccionar —" : "Selecciona zona primero"}</option>
                {comunasOptions.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              {fieldErrors.comuna && <small className={styles.error}>{fieldErrors.comuna}</small>}
            </label>

            <label className={styles.label} style={{ margin: 0 }}>
              Marca
              <select
                className={styles.select}
                name="marca"
                value={form.marca}
                onChange={onChange}
                disabled={loading}
              >
                <option value="">— Seleccionar —</option>
                {MARCAS.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
              {fieldErrors.marca && <small className={styles.error}>{fieldErrors.marca}</small>}
            </label>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <label className={styles.label} style={{ margin: 0 }}>
              Tecnología
              <select
                className={styles.select}
                name="tecnologia"
                value={form.tecnologia}
                onChange={onChange}
                disabled={loading}
              >
                <option value="">— Seleccionar —</option>
                {TECNOLOGIAS.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
              {fieldErrors.tecnologia && <small className={styles.error}>{fieldErrors.tecnologia}</small>}
            </label>

            <label className={styles.label} style={{ margin: 0 }}>
              ID vivienda
              <input
                className={styles.input}
                name="id_vivienda"
                value={form.id_vivienda}
                onChange={onChange}
                disabled={loading}
              />
              {fieldErrors.id_vivienda && <small className={styles.error}>{fieldErrors.id_vivienda}</small>}
            </label>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <label className={styles.label} style={{ margin: 0 }}>
              RUT cliente
              <input
                className={styles.input}
                name="rut_cliente"
                value={form.rut_cliente}
                onChange={onChange}
                disabled={loading}
                placeholder="12345678-K"
              />
              {fieldErrors.rut_cliente && <small className={styles.error}>{fieldErrors.rut_cliente}</small>}
            </label>

            <label className={styles.label} style={{ margin: 0 }}>
              Encuesta de origen
              <select
                className={styles.select}
                name="encuesta"
                value={form.encuesta}
                onChange={onChange}
                disabled={loading}
              >
                <option value="">— Seleccionar —</option>
                {ENCUESTAS.map((e) => (
                  <option key={e.value} value={e.value}>{e.label}</option>
                ))}
              </select>
              {fieldErrors.encuesta && <small className={styles.error}>{fieldErrors.encuesta}</small>}
            </label>
          </div>

          <label className={styles.label}>
            ID Qualtrics (opcional)
            <input
              className={styles.input}
              name="id_qualtrics"
              value={form.id_qualtrics}
              onChange={onChange}
              disabled={loading}
              placeholder="p.ej. SV_abc123"
            />
            {fieldErrors.id_qualtrics && <small className={styles.error}>{fieldErrors.id_qualtrics}</small>}
          </label>

          {error && <div className={styles.error}>{error}</div>}
          {ok && <div className={styles.success}>{ok}</div>}

          <div className={styles.actions}>
            <button type="submit" className={styles.button} disabled={loading}>
              {loading ? "Guardando…" : "Guardar dirección"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
