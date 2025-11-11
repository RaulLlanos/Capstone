// src/pages/AdminUsuarioEdit.jsx
import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

export default function AdminUsuarioEdit() {
  const { user } = useAuth();
  const role = String(user?.rol || user?.role || "").toLowerCase();
  const isAdmin = role === "administrador";

  const { id } = useParams();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    rol: "tecnico",
    is_active: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const res = await api.get(`/api/usuarios/${id}/`);
        if (!mounted) return;
        const d = res.data || {};
        setForm({
          first_name: d.first_name || "",
          last_name: d.last_name || "",
          email: d.email || "",
          rol: (d.rol || d.role || "tecnico").toLowerCase(),
          is_active: d.is_active !== false,
        });
      } catch (e) {
        console.error("GET usuario", e?.response?.status, e?.response?.data);
        if (mounted) setError("No se pudo cargar el usuario.");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [id]);

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.get("/auth/csrf");
      await api.patch(`/api/usuarios/${id}/`, form);
      navigate("/panel/usuarios", { replace: true });
    } catch (e) {
      console.error("PATCH usuario", e?.response?.status, e?.response?.data);
      setError("No se pudieron guardar los cambios.");
    } finally {
      setSaving(false);
    }
  }

  if (!isAdmin) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.card}><p className={styles.error}>Solo administradores.</p></div>
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

        {error && <div className={styles.error} style={{ marginTop: 8 }}>{error}</div>}
        {loading ? (
          <div className={styles.helper} style={{ marginTop: 8 }}>Cargando…</div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: "grid", gap: 10 }}>
            <label>
              <div>Nombre (opcional)</div>
              <input
                className={styles.input}
                placeholder="Nombre"
                value={form.first_name}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })}
              />
            </label>
            <label>
              <div>Apellido (opcional)</div>
              <input
                className={styles.input}
                placeholder="Apellido"
                value={form.last_name}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              />
            </label>
            <label>
              <div>Email (login)</div>
              <input
                className={styles.input}
                type="email"
                placeholder="correo@dominio.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </label>
            <label>
              <div>Rol</div>
              <select
                className={styles.select}
                value={form.rol}
                onChange={(e) => setForm({ ...form, rol: e.target.value })}
              >
                <option value="tecnico">Técnico</option>
                <option value="administrador">Administrador</option>
              </select>
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              />
              <span>Activo</span>
            </label>

            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              <button className={styles.button} type="submit" disabled={saving}>
                Guardar
              </button>
              <Link className={styles.button} to="/panel/usuarios">Cancelar</Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
