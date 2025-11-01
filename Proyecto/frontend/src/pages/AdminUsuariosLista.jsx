// src/pages/AdminUsuariosLista.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

const USER_ENDPOINTS = [
  "/api/usuarios/",
  "/auth/users/",
  "/api/users/",
];

export default function AdminUsuariosLista() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [nextUrl, setNextUrl] = useState(null);
  const [prevUrl, setPrevUrl] = useState(null);

  const fetchId = useRef(0);
  const role = String(user?.rol || user?.role || "").toLowerCase();
  const isAdmin = role === "administrador";

  const pickResults = (data) => {
    if (!data) return [];
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.results)) return data.results;
    return [];
  };

  const load = async (absoluteUrl) => {
    setLoading(true);
    setError("");
    const myFetch = ++fetchId.current;
    try {
      let res;
      for (const ep of USER_ENDPOINTS) {
        try {
          res = absoluteUrl ? await api.get(absoluteUrl) : await api.get(ep);
          if (res?.data) break;
        // eslint-disable-next-line no-unused-vars
        } catch (_) { /* empty */ }
      }
      if (!res) throw new Error("No se pudo obtener usuarios.");
      if (myFetch !== fetchId.current) return;
      const data = res.data || {};
      setItems(pickResults(data));
      setNextUrl(data.next || null);
      setPrevUrl(data.previous || null);
    } catch (err) {
      console.error("GET usuarios:", err?.response?.status, err?.response?.data);
      setError("No se pudieron cargar los usuarios.");
      setItems([]);
      setNextUrl(null);
      setPrevUrl(null);
    } finally {
      if (myFetch === fetchId.current) setLoading(false);
    }
  };

  useEffect(() => {
    load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((u) =>
      [u.name, u.email, u.username, u.rol, u.role]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(q))
    );
  }, [items, query]);

  async function handleDelete(u) {
    if (!window.confirm(`¿Eliminar usuario "${u.email}" (${u.rol || u.role})?`)) return;
    try {
      await api.get("/auth/csrf");
      await api.delete(`/api/usuarios/${u.id}/`);
      setItems((arr) => arr.filter((x) => x.id !== u.id));
    } catch (err) {
      console.error("DELETE usuario:", err?.response?.status, err?.response?.data);
      alert("No se pudo eliminar el usuario.");
    }
  }

  if (!isAdmin) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.card}>
          <p className={styles.error}>Solo los administradores pueden acceder a esta sección.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 900 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Usuarios</h1>
          <p className={styles.subtitle}>Gestión de cuentas y roles</p>
        </header>

        <div className={styles.actions} style={{ display: "flex", gap: 8 }}>
          <Link to="/registro" className={styles.button}>+ Crear usuario</Link>
        </div>

        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <input
            className={styles.input}
            placeholder="Buscar por nombre, email o rol…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
            style={{ flex: 1 }}
          />
          <button className={styles.button} onClick={() => load()} disabled={loading}>
            Recargar
          </button>
        </div>

        {error && <div className={styles.error} style={{ marginTop: 8 }}>{error}</div>}
        {loading && <div className={styles.helper} style={{ marginTop: 8 }}>Cargando usuarios…</div>}

        <div style={{ overflowX: "auto", marginTop: 12 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead style={{ textAlign: "left" }}>
              <tr>
                <th>Nombre</th>
                <th>Email</th>
                <th>Rol</th>
                <th style={{ width: 220 }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => (
                <tr key={u.id} style={{ borderTop: "1px solid #e5e7eb" }}>
                  <td>{u.name || `${u.first_name || ""} ${u.last_name || ""}`.trim() || "—"}</td>
                  <td>{u.email || u.username || "—"}</td>
                  <td>{(u.rol || u.role || "—").toString().toUpperCase()}</td>
                  <td style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    <Link className={styles.button} to={`/admin/usuarios/${u.id}/editar`}>
                      Editar
                    </Link>
                    <button
                      className={styles.button}
                      style={{ background: "#dc2626" }}
                      onClick={() => handleDelete(u)}
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
              {!loading && filtered.length === 0 && (
                <tr>
                  <td colSpan={4} className={styles.helper}>
                    Sin resultados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 8 }}>
          <button
            className={styles.button}
            disabled={!prevUrl || loading}
            onClick={() => load(prevUrl || undefined)}
          >
            « Anterior
          </button>
          <button
            className={styles.button}
            disabled={!nextUrl || loading}
            onClick={() => load(nextUrl || undefined)}
          >
            Siguiente »
          </button>
        </div>
      </div>
    </div>
  );
}
