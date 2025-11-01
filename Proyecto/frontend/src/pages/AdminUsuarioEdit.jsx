/* eslint-disable no-unused-vars */
// src/pages/AdminUsuarioEdit.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

// Endpoints posibles (el primero que responda se usa)
const USER_DETAIL_ENDPOINTS = (id) => [
  `/api/usuarios/${id}/`,
  `/auth/users/${id}/`,
  `/api/users/${id}/`,
];

const ROLES = [
  { value: "administrador", label: "Administrador" },
  { value: "tecnico", label: "Técnico" },
];

export default function AdminUsuarioEdit() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const role = String(user?.rol || user?.role || "").toLowerCase();
  const isAdmin = role === "administrador";

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  // Form canonizado
  const [form, setForm] = useState({
    name: "",
    email: "",
    rol: "tecnico", // default
  });

  // Guardamos qué endpoint funcionó para reusar en PUT/PATCH
  const activeEndpoint = useRef(null);

  const canSave = useMemo(() => {
    return form.email.trim().length > 3 && form.rol;
  }, [form.email, form.rol]);

  // Normaliza un usuario del backend a nuestro formulario
  const normalizeUser = (u) => {
    const name =
      u.name ||
      (u.first_name || u.last_name ? `${u.first_name || ""} ${u.last_name || ""}`.trim() : "") ||
      u.full_name ||
      u.display_name ||
      "";
    const email = u.email || u.username || "";
    const rol = (u.rol || u.role || "").toString().toLowerCase() || "tecnico";
    return { name, email, rol };
  };

  // Carga detalle
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      setOk("");
      setFieldErrors({});
      try {
        let res = null;
        for (const ep of USER_DETAIL_ENDPOINTS(id)) {
          try {
            const r = await api.get(ep);
            if (r?.data) {
              res = r;
              activeEndpoint.current = ep; // éxito
              break;
            }
          } catch (_) {
            // probar siguiente
          }
        }
        if (!res) throw new Error("No se pudo obtener el usuario.");
        if (cancelled) return;
        const canon = normalizeUser(res.data || {});
        setForm(canon);
      } catch (err) {
        console.error("GET usuario:", err?.response?.status, err?.response?.data);
        setError("No se pudo cargar el usuario.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
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
    if (!form.email.trim()) fe.email = "Requerido.";
    if (!form.rol) fe.rol = "Requerido.";
    // Nombre es opcional, pero si existe validamos mínimo
    if (form.name && form.name.trim().length < 2) fe.name = "Muy corto.";
    return fe;
  };

  // Construye payload compatible con distintas APIs
  const buildPayload = () => {
    // Enviamos rol como 'rol' (nuestro backend) y también 'role' por si aplica otro endpoint.
    // Enviamos 'name', y dejamos opcionales first/last si el backend los usa.
    const payload = {
      name: form.name?.trim(),
      email: form.email?.trim(),
      username: form.email?.trim(), // por compatibilidad si el backend usa username
      rol: form.rol,
      role: form.rol,
    };
    // Limpia nullables cortos
    Object.keys(payload).forEach((k) => {
      if (payload[k] === undefined) delete payload[k];
    });
    return payload;
  };

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
      const payload = buildPayload();

      // Intentamos PUT y caemos a PATCH
      let saved = false;
      const eps = activeEndpoint.current
        ? [activeEndpoint.current]
        : USER_DETAIL_ENDPOINTS(id);
      for (const ep of eps) {
        try {
          await api.put(ep, payload);
          activeEndpoint.current = ep;
          saved = true;
          break;
        } catch (err) {
          if (err?.response?.status === 405) {
            try {
              await api.patch(ep, payload);
              activeEndpoint.current = ep;
              saved = true;
              break;
            } catch (err2) {
              // probar siguiente
            }
          } else {
            // probar siguiente endpoint
          }
        }
      }

      if (!saved) throw new Error("No se pudo guardar en ningún endpoint.");

      setOk("Usuario actualizado correctamente.");
      // Opcional: volver a la lista tras guardar
      // setTimeout(() => navigate("/admin/usuarios"), 600);
    } catch (err) {
      console.error("SAVE usuario:", err?.response?.status, err?.response?.data);
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
    } finally {
      setSaving(false);
    }
  };

  if (!isAdmin) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.card}>
          <p className={styles.error}>Solo los administradores pueden editar usuarios.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 640 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Editar usuario #{id}</h1>
          <p className={styles.subtitle}>Modifica los datos y guarda los cambios</p>
        </header>

        {loading ? (
          <div className={styles.helper}>Cargando…</div>
        ) : (
          <form onSubmit={handleSave} className={styles.form}>
            <label className={styles.label}>
              Nombre (opcional)
              <input
                className={styles.input}
                name="name"
                value={form.name}
                onChange={onChange}
                disabled={saving}
                placeholder="Nombre y apellido"
              />
              {fieldErrors.name && <small className={styles.error}>{fieldErrors.name}</small>}
            </label>

            <label className={styles.label}>
              Email (login)
              <input
                className={styles.input}
                type="email"
                name="email"
                value={form.email}
                onChange={onChange}
                disabled={saving}
                placeholder="correo@dominio.com"
              />
              {fieldErrors.email && <small className={styles.error}>{fieldErrors.email}</small>}
            </label>

            <label className={styles.label}>
              Rol
              <select
                className={styles.select}
                name="rol"
                value={form.rol}
                onChange={onChange}
                disabled={saving}
              >
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
              {fieldErrors.rol && <small className={styles.error}>{fieldErrors.rol}</small>}
              {fieldErrors.role && <small className={styles.error}>{fieldErrors.role}</small>}
            </label>

            {error && <div className={styles.error}>{error}</div>}
            {ok && <div className={styles.success}>{ok}</div>}

            <div className={styles.actions}>
              <button type="submit" className={styles.button} disabled={saving || !canSave}>
                {saving ? "Guardando…" : "Guardar cambios"}
              </button>
              <button
                type="button"
                className={styles.button}
                style={{ background: "#6b7280" }}
                onClick={() => navigate(-1)}
                disabled={saving}
              >
                Volver
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
