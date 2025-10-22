// src/pages/Registro.jsx
import { useEffect, useRef, useState } from "react";
import api from "../services/api";
import styles from "./Login.module.css";

const ROLES = [
  { value: "tecnico", label: "Técnico" },
  { value: "administrador", label: "Administrador" },
];

const USERS_PATH = "/api/usuarios";
const REGISTER_PATH = "/auth/register";
const CSRF_PATH = "/auth/csrf";

const isEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);

// Helpers para leer listas y verificar matches exactos
function itemsFrom(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}
function someEmailEquals(data, email) {
  if (!email) return false;
  const low = email.toLowerCase();
  return itemsFrom(data).some((u) => (u?.email || "").toLowerCase() === low);
}
function someRutEquals(data, rut_num, dv) {
  if (!rut_num || !dv) return false;
  const rn = String(rut_num).replace(/\D+/g, "");
  const d = String(dv).trim().toUpperCase();
  return itemsFrom(data).some(
    (u) =>
      String(u?.rut_num || "").replace(/\D+/g, "") === rn &&
      String(u?.dv || "").trim().toUpperCase() === d
  );
}

export default function Registro() {
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    password2: "",
    rut_num: "",
    dv: "",
    rol: "tecnico",
    is_active: true,
  });

  const [loading, setLoading] = useState(false);
  const [ok, setOk] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  // Flags/verificaciones con debounce
  const [checkingRut, setCheckingRut] = useState(false);
  const [rutTaken, setRutTaken] = useState(false);
  const [checkingEmail, setCheckingEmail] = useState(false);
  const [emailTaken, setEmailTaken] = useState(false);
  const rutTimer = useRef(null);
  const emailTimer = useRef(null);

  const onChange = (e) => {
    const { name, value, type, checked } = e.target;
    const v = type === "checkbox" ? checked : value;
    setForm((f) => ({ ...f, [name]: v }));
    setFieldErrors((fe) => ({ ...fe, [name]: "" }));
    setOk("");
    setError("");
  };

  // --- Debounce: verificar RUT duplicado (match exacto) ---
  useEffect(() => {
    setRutTaken(false);
    setFieldErrors((fe) => ({ ...fe, rut_num: "", dv: "" }));

    const rut_num = (form.rut_num || "").trim().replace(/\D+/g, "");
    const dv = (form.dv || "").trim().toUpperCase();

    if (!rut_num || !dv) {
      if (rutTimer.current) clearTimeout(rutTimer.current);
      setCheckingRut(false);
      return;
    }

    if (rutTimer.current) clearTimeout(rutTimer.current);
    rutTimer.current = setTimeout(async () => {
      setCheckingRut(true);
      try {
        // Aunque el backend ignore filtros, nosotros validamos por match exacto
        const res = await api.get(USERS_PATH, { params: { rut_num, dv } });
        const taken = someRutEquals(res.data, rut_num, dv);
        setRutTaken(taken);
        if (taken) {
          setFieldErrors((fe) => ({
            ...fe,
            rut_num: "RUT ocupado. Intenta con otro.",
          }));
        }
      } catch {
        // si falla el GET, no bloqueamos por prechequeo; se resolverá en el POST
      } finally {
        setCheckingRut(false);
      }
    }, 400);

    return () => {
      if (rutTimer.current) clearTimeout(rutTimer.current);
    };
  }, [form.rut_num, form.dv]);

  // --- Debounce: verificar EMAIL duplicado (match exacto) ---
  useEffect(() => {
    setEmailTaken(false);
    setFieldErrors((fe) => ({ ...fe, email: "" }));

    const email = (form.email || "").trim().toLowerCase();
    if (!email) {
      if (emailTimer.current) clearTimeout(emailTimer.current);
      setCheckingEmail(false);
      return;
    }
    if (!isEmail(email)) return; // no llamar API si formato inválido

    if (emailTimer.current) clearTimeout(emailTimer.current);
    emailTimer.current = setTimeout(async () => {
      setCheckingEmail(true);
      try {
        const res = await api.get(USERS_PATH, { params: { email } });
        const taken = someEmailEquals(res.data, email);
        setEmailTaken(taken);
        if (taken) {
          setFieldErrors((fe) => ({ ...fe, email: "Email inválido u ocupado." }));
        }
      } catch {
        // si falla el GET, no bloqueamos por prechequeo
      } finally {
        setCheckingEmail(false);
      }
    }, 400);

    return () => {
      if (emailTimer.current) clearTimeout(emailTimer.current);
    };
  }, [form.email]);

  const validate = () => {
    const fe = {};
    if (!form.first_name.trim()) fe.first_name = "Requerido.";
    if (!form.last_name.trim()) fe.last_name = "Requerido.";

    const email = (form.email || "").trim().toLowerCase();
    if (!isEmail(email)) fe.email = "Email inválido.";

    if ((form.password || "").length < 8) fe.password = "Mínimo 8 caracteres.";
    if (form.password !== form.password2) fe.password2 = "Las contraseñas no coinciden.";

    if (!/^\d+$/.test((form.rut_num || "").trim())) fe.rut_num = "Solo números.";
    if (!form.dv.trim()) fe.dv = "Requerido.";

    // flags ya detectados por prechequeo
    if (emailTaken) fe.email = "Email inválido u ocupado.";
    if (rutTaken) fe.rut_num = "RUT ocupado. Intenta con otro.";

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
      await api.get(CSRF_PATH);

      const payload = {
        email: form.email.trim().toLowerCase(),
        password: form.password,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        rut_num: form.rut_num.trim().replace(/\D+/g, ""),
        dv: form.dv.trim().toUpperCase(),
        rol: form.rol,
        is_active: form.is_active,
      };

      await api.post(REGISTER_PATH, payload);

      setOk("Usuario creado correctamente.");
      setForm({
        first_name: "",
        last_name: "",
        email: "",
        password: "",
        password2: "",
        rut_num: "",
        dv: "",
        rol: "tecnico",
        is_active: true,
      });
      setRutTaken(false);
      setEmailTaken(false);
    } catch (err) {
      const data = err?.response?.data ?? {};
      const status = err?.response?.status;
      const fe2 = {};

      // 1) Parseo directo campo→errores (DRF)
      if (data && typeof data === "object") {
        Object.entries(data).forEach(([k, v]) => {
          if (Array.isArray(v)) fe2[k] = v.join(" ");
          else if (typeof v === "string") fe2[k] = v;
        });
      }

      // 2) Heurísticas por texto plano
      const flat = (typeof data === "string" ? data : JSON.stringify(data || {})).toLowerCase();
      const looksDuplicate =
        flat.includes("unique") ||
        flat.includes("duplicate") ||
        flat.includes("duplic") ||
        flat.includes("existe") ||
        flat.includes("ocupado") ||
        flat.includes("ya está");

      // Email duplicado / inválido
      if (
        (flat.includes("email") || fe2.email) &&
        (looksDuplicate || flat.includes("invalid"))
      ) {
        fe2.email = "Email inválido u ocupado.";
      }

      // RUT duplicado
      const looksRutContext =
        flat.includes("rut_num") ||
        flat.includes('"rut"') ||
        flat.includes('"dv"') ||
        flat.includes(" rut ") ||
        flat.includes("usuarios_usuario_rut_num_dv") ||
        flat.includes("key (rut_num") ||
        flat.includes("key (dv");

      if (looksRutContext && looksDuplicate) {
        fe2.rut_num = "RUT ocupado. Intenta con otro.";
      }

      // 3) Fallback por detail / non_field_errors
      if (!fe2.rut_num || !fe2.email) {
        const candidates = [
          typeof data?.detail === "string" ? data.detail : "",
          Array.isArray(data?.non_field_errors) ? data.non_field_errors.join(" ") : "",
        ]
          .join(" ")
          .toLowerCase();

        const dupInDetail = /(unique|duplicate|duplic|existe|ocupado|ya está)/.test(candidates);
        const rutInDetail = /(rut|rut_num|dv|usuarios_usuario_rut_num_dv|key \(rut_num|key \(dv)/.test(candidates);
        const emailInDetail = /email/.test(candidates);

        if (!fe2.rut_num && dupInDetail && rutInDetail) {
          fe2.rut_num = "RUT ocupado. Intenta con otro.";
        }
        if (!fe2.email && (dupInDetail || /invalid/.test(candidates)) && emailInDetail) {
          fe2.email = "Email inválido u ocupado.";
        }
      }

      // 4) Fallback definitivo: confirmar existencia por match exacto vía GET
      try {
        if (status === 400 || status === 409) {
          const rut_num_chk = (form.rut_num || "").trim().replace(/\D+/g, "");
          const dv_chk = (form.dv || "").trim().toUpperCase();
          const email_chk = (form.email || "").trim().toLowerCase();

          if (!fe2.rut_num && rut_num_chk && dv_chk) {
            const resRut = await api.get(USERS_PATH, { params: { rut_num: rut_num_chk, dv: dv_chk } });
            if (someRutEquals(resRut.data, rut_num_chk, dv_chk)) {
              fe2.rut_num = "RUT ocupado. Intenta con otro.";
            }
          }
          if (!fe2.email && email_chk) {
            const resEmail = await api.get(USERS_PATH, { params: { email: email_chk } });
            if (someEmailEquals(resEmail.data, email_chk)) {
              fe2.email = "Email inválido u ocupado.";
            }
          }
        }
      } catch {
        // ignorar fallos del fallback
      }

      if (Object.keys(fe2).length) {
        setFieldErrors((old) => ({ ...old, ...fe2 }));
      } else {
        setError(data?.detail || data?.error || "No se pudo crear el usuario.");
      }

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
        </header>

        <form onSubmit={handleSubmit} className={styles.form}>
          <label className={styles.label}>
            Email
            <input
              className={styles.input}
              name="email"
              type="email"
              value={form.email}
              onChange={onChange}
              disabled={loading}
              placeholder="usuario@dominio.cl"
            />
            {checkingEmail && !fieldErrors.email && (
              <small className={styles.helper}>Verificando email…</small>
            )}
            {fieldErrors.email && <small className={styles.error}>{fieldErrors.email}</small>}
          </label>

          <label className={styles.label}>
            Contraseña
            <input
              className={styles.input}
              name="password"
              type="password"
              value={form.password}
              onChange={onChange}
              disabled={loading}
            />
            {fieldErrors.password && <small className={styles.error}>{fieldErrors.password}</small>}
          </label>

          <label className={styles.label}>
            Contraseña (confirmación)
            <input
              className={styles.input}
              name="password2"
              type="password"
              value={form.password2}
              onChange={onChange}
              disabled={loading}
            />
            {fieldErrors.password2 && <small className={styles.error}>{fieldErrors.password2}</small>}
          </label>

          <label className={styles.label}>
            Nombre
            <input
              className={styles.input}
              name="first_name"
              type="text"
              value={form.first_name}
              onChange={onChange}
              disabled={loading}
            />
            {fieldErrors.first_name && <small className={styles.error}>{fieldErrors.first_name}</small>}
          </label>

          <label className={styles.label}>
            Apellido
            <input
              className={styles.input}
              name="last_name"
              type="text"
              value={form.last_name}
              onChange={onChange}
              disabled={loading}
            />
            {fieldErrors.last_name && <small className={styles.error}>{fieldErrors.last_name}</small>}
          </label>

          <div style={{ display: "grid", gridTemplateColumns: "1fr auto auto", gap: "8px" }}>
            <label className={styles.label} style={{ margin: 0 }}>
              RUT (sin DV) <span className={styles.helper}>(ej: 12345678)</span>
              <input
                className={styles.input}
                name="rut_num"
                type="text"
                value={form.rut_num}
                onChange={onChange}
                disabled={loading}
                placeholder="12345678"
              />
              {checkingRut && !fieldErrors.rut_num && (
                <small className={styles.helper}>Verificando RUT…</small>
              )}
              {fieldErrors.rut_num && <small className={styles.error}>{fieldErrors.rut_num}</small>}
            </label>
            <label className={styles.label} style={{ margin: 0 }}>
              DV <span className={styles.helper}>(ej: K)</span>
              <input
                className={styles.input}
                name="dv"
                type="text"
                maxLength={1}
                value={form.dv}
                onChange={onChange}
                disabled={loading}
                placeholder="K"
              />
              {fieldErrors.dv && <small className={styles.error}>{fieldErrors.dv}</small>}
            </label>
          </div>

          <label className={styles.label}>
            Rol
            <select
              className={styles.select}
              name="rol"
              value={form.rol}
              onChange={onChange}
              disabled={loading}
            >
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
            {fieldErrors.rol && <small className={styles.error}>{fieldErrors.rol}</small>}
          </label>

          <label className={styles.label} style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input
              type="checkbox"
              name="is_active"
              checked={form.is_active}
              onChange={onChange}
              disabled={loading}
            />
            Activo
          </label>

          {error && <div className={styles.error}>{error}</div>}
          {ok && <div className={styles.success}>{ok}</div>}

          <div className={styles.actions}>
            <button
              type="submit"
              className={styles.button}
              disabled={
                loading ||
                checkingRut ||
                checkingEmail ||
                rutTaken ||
                emailTaken ||
                (form.password && form.password2 && form.password !== form.password2)
              }
            >
              {loading ? "Creando…" : "Crear usuario"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
