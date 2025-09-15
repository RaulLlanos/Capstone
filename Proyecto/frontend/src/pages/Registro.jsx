// src/pages/Registro.jsx
import { useState } from "react";
import api from "../services/api";
import styles from "./Login.module.css";

const ROLES = [
  { value: "tecnico", label: "Técnico" },
  { value: "auditor", label: "Auditor" },
];

const isEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);

export default function Registro() {
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    password2: "",
    rut_num: "",
    rut_dv: "",
    rol: "tecnico",
    is_active: true,
  });
  const [loading, setLoading] = useState(false);
  const [ok, setOk] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  const onChange = (e) => {
    const { name, value, type, checked } = e.target;
    const v = type === "checkbox" ? checked : value;
    setForm((f) => ({ ...f, [name]: v }));
    setFieldErrors((fe) => ({ ...fe, [name]: "" }));
  };

  const validate = () => {
    const fe = {};
    if (!form.first_name.trim()) fe.first_name = "Requerido.";
    if (!form.last_name.trim()) fe.last_name = "Requerido.";
    if (!isEmail(form.email)) fe.email = "Email inválido.";
    if ((form.password || "").length < 8) fe.password = "Mínimo 8 caracteres.";
    if (form.password !== form.password2) fe.password2 = "Las contraseñas no coinciden.";
    if (!/^\d+$/.test(form.rut_num)) fe.rut_num = "Solo números.";
    return fe;
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

      // Ajusta las claves si tu serializer usa otros nombres
      const payload = {
        email: form.email.trim().toLowerCase(),
        password: form.password,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        rut_num: form.rut_num.trim(),
        rut_dv: form.rut_dv.trim().toUpperCase(),
        rol: form.rol,
        is_active: form.is_active,
      };

      await api.post("/auth/register", payload);

      setOk("Usuario creado correctamente.");
      setForm({
        first_name: "",
        last_name: "",
        email: "",
        password: "",
        password2: "",
        rut_num: "",
        rut_dv: "",
        rol: "tecnico",
        is_active: true,
      });
    } catch (err) {
      const data = err?.response?.data || {};
      const fe2 = {};
      if (typeof data === "object") {
        Object.entries(data).forEach(([k, v]) => {
          if (Array.isArray(v)) fe2[k] = v.join(" ");
          else if (typeof v === "string") fe2[k] = v;
        });
      }
      if (Object.keys(fe2).length) setFieldErrors(fe2);
      else setError(data.detail || data.error || "No se pudo crear el usuario.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        <header className={styles.header}>
          <h1 className={styles.title}>Crear usuario</h1>
          <p className={styles.subtitle}>Completa los datos requeridos</p>
        </header>

        <form onSubmit={handleSubmit} className={styles.form}>
          <label className={styles.label}>
            Email
            <input className={styles.input} name="email" type="email" value={form.email} onChange={onChange} disabled={loading}/>
            {fieldErrors.email && <small className={styles.error}>{fieldErrors.email}</small>}
          </label>

          <label className={styles.label}>
            Contraseña
            <input className={styles.input} name="password" type="password" value={form.password} onChange={onChange} disabled={loading}/>
            {fieldErrors.password && <small className={styles.error}>{fieldErrors.password}</small>}
          </label>

          <label className={styles.label}>
            Contraseña (confirmación)
            <input className={styles.input} name="password2" type="password" value={form.password2} onChange={onChange} disabled={loading}/>
            {fieldErrors.password2 && <small className={styles.error}>{fieldErrors.password2}</small>}
          </label>

          <label className={styles.label}>
            Nombre
            <input className={styles.input} name="first_name" type="text" value={form.first_name} onChange={onChange} disabled={loading}/>
            {fieldErrors.first_name && <small className={styles.error}>{fieldErrors.first_name}</small>}
          </label>

          <label className={styles.label}>
            Apellido
            <input className={styles.input} name="last_name" type="text" value={form.last_name} onChange={onChange} disabled={loading}/>
            {fieldErrors.last_name && <small className={styles.error}>{fieldErrors.last_name}</small>}
          </label>

          <div style={{ display: "grid", gridTemplateColumns: "1fr auto auto", gap: "8px" }}>
            <label className={styles.label} style={{ margin: 0 }}>
              RUT (sin DV)
              <input className={styles.input} name="rut_num" type="text" value={form.rut_num} onChange={onChange} disabled={loading}/>
              {fieldErrors.rut_num && <small className={styles.error}>{fieldErrors.rut_num}</small>}
            </label>
            <label className={styles.label} style={{ margin: 0 }}>
              DV
              <input className={styles.input} name="rut_dv" type="text" maxLength={1} value={form.rut_dv} onChange={onChange} disabled={loading}/>
              {fieldErrors.rut_dv && <small className={styles.error}>{fieldErrors.rut_dv}</small>}
            </label>
            
          </div>

          <label className={styles.label}>
            Rol
            <select className={styles.select} name="rol" value={form.rol} onChange={onChange} disabled={loading}>
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
            {fieldErrors.rol && <small className={styles.error}>{fieldErrors.rol}</small>}
          </label>

          <label className={styles.label} style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input type="checkbox" name="is_active" checked={form.is_active} onChange={onChange} disabled={loading}/>
            Activo
          </label>

          {error && <div className={styles.error}>{error}</div>}
          {ok && <div className={styles.success}>{ok}</div>}

          <div className={styles.actions}>
            <button type="submit" className={styles.button} disabled={loading}>
              {loading ? "Creando…" : "Crear usuario"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
