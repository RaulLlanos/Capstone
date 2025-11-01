// src/pages/AuditorHistorial.jsx
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import api from "../services/api";
import styles from "./Login.module.css";
import { useAuth } from "../context/AuthContext";

const TECH_ENDPOINTS = [
  "/api/usuarios/?role=tecnico",
  "/auth/users/?role=tecnico",
  "/api/users/?role=tecnico",
  "/api/usuarios/",
  "/auth/users/",
  "/api/users/",
];

function normalizeUsers(raw) {
  const arr = Array.isArray(raw?.results) ? raw.results : Array.isArray(raw) ? raw : [];
  return arr
    .map((u) => {
      const id = u.id ?? u.pk ?? null;
      const email = u.email ?? u.user?.email ?? u.username ?? "";
      const role = (u.role ?? u.rol ?? "").toString().toLowerCase();
      const name =
        u.name ||
        (u.first_name || u.last_name ? `${u.first_name || ""} ${u.last_name || ""}`.trim() : "") ||
        u.full_name ||
        u.display_name ||
        "";
      const label = [name, email].filter(Boolean).join(" — ") || email || name || `Técnico #${id ?? "?"}`;
      if (!id) return null;
      return { value: String(id), label, role };
    })
    .filter(Boolean)
    .filter((t) => t.role === "tecnico");
}

function colorAccion(accion) {
  if (!accion) return "#111827";
  const a = String(accion).toLowerCase();
  if (a.includes("asign")) return "#2563eb";   // azul
  if (a.includes("desasign")) return "#dc2626"; // rojo
  if (a.includes("visit")) return "#059669";    // verde
  if (a.includes("cre")) return "#9333ea";      // morado
  if (a.includes("edit")) return "#6b7280";     // gris
  return "#111827";
}

const th = {
  textAlign: "left",
  padding: "10px 12px",
  borderBottom: "2px solid #d1d5db",
  fontWeight: 600,
  color: "#111827",
};
const td = {
  padding: "8px 12px",
  verticalAlign: "top",
  color: "#374151",
};

export default function AuditorHistorial() {
  const { user } = useAuth();
  const isAdmin = (user?.rol || user?.role) === "administrador";

  // datos
  const [rows, setRows] = useState([]);
  const [nextUrl, setNextUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");

  // filtros
  const [search, setSearch] = useState("");
  const [desde, setDesde] = useState(""); // YYYY-MM-DD
  const [hasta, setHasta] = useState(""); // YYYY-MM-DD
  const [tecnicoId, setTecnicoId] = useState("");

  // técnicos
  const [techs, setTechs] = useState([{ value: "", label: "Todos los técnicos" }]);
  const [loadingTechs, setLoadingTechs] = useState(false);

  // sentinel para infinite scroll
  const sentinelRef = useRef(null);
  const observerRef = useRef(null);
  const fetchingRef = useRef(false);

  // armar query params según filtros
  const baseListPath = "/api/asignaciones/historial/";
  const buildParams = useCallback(() => {
    const p = new URLSearchParams();
    if (tecnicoId) p.set("tecnico_id", tecnicoId);
    // El ViewSet acepta "fecha_after"/"fecha_before" o "desde"/"hasta"
    if (desde) p.set("fecha_after", desde);
    if (hasta) p.set("fecha_before", hasta);
    return p.toString();
  }, [tecnicoId, desde, hasta]);

  // carga inicial o cuando cambian filtros
  const loadFirstPage = useCallback(async () => {
    if (!isAdmin) return;
    setLoading(true);
    setError("");
    fetchingRef.current = true;
    try {
      const q = buildParams();
      const url = q ? `${baseListPath}?${q}` : baseListPath;
      const res = await api.get(url);
      const data = res.data || {};
      const list = Array.isArray(data) ? data : (data.results || []);
      setRows(list);
      setNextUrl(data.next || null);
    } catch (err) {
      console.error("GET historial:", err?.response?.status, err?.response?.data);
      setError("No se pudo cargar el historial.");
      setRows([]);
      setNextUrl(null);
    } finally {
      setLoading(false);
      fetchingRef.current = false;
    }
  }, [isAdmin, buildParams]);

  // carga siguiente página (scroll)
  const loadNextPage = useCallback(async () => {
    if (!isAdmin || !nextUrl || fetchingRef.current) return;
    setLoadingMore(true);
    fetchingRef.current = true;
    try {
      const res = await api.get(nextUrl);
      const data = res.data || {};
      const list = Array.isArray(data) ? data : (data.results || []);
      setRows((prev) => prev.concat(list));
      setNextUrl(data.next || null);
    } catch (err) {
      console.error("GET historial next:", err?.response?.status, err?.response?.data);
      setError("No se pudo cargar más historial.");
      setNextUrl(null);
    } finally {
      setLoadingMore(false);
      fetchingRef.current = false;
    }
  }, [isAdmin, nextUrl]);

  // observer para scroll infinito
  useEffect(() => {
    if (!isAdmin) return;
    if (observerRef.current) observerRef.current.disconnect();
    observerRef.current = new IntersectionObserver((entries) => {
      const first = entries[0];
      if (first && first.isIntersecting) {
        loadNextPage();
      }
    });
    const current = sentinelRef.current;
    if (current) observerRef.current.observe(current);
    return () => {
      if (observerRef.current) observerRef.current.disconnect();
    };
  }, [isAdmin, loadNextPage, rows.length]); // reanclar cuando cambie el largo

  // cargar técnicos
  useEffect(() => {
    (async () => {
      setLoadingTechs(true);
      let loaded = [];
      for (const ep of TECH_ENDPOINTS) {
        try {
          const res = await api.get(ep);
          loaded = normalizeUsers(res.data);
          if (loaded.length) break;
        // eslint-disable-next-line no-unused-vars
        } catch (_) { /* empty */ }
      }
      setTechs([{ value: "", label: "Todos los técnicos" }, ...loaded.map(({ value, label }) => ({ value, label }))]);
      setLoadingTechs(false);
    })();
  }, []);

  // cargar historial (inicial y cada vez que cambian filtros)
  useEffect(() => {
    loadFirstPage();
  }, [loadFirstPage]);

  // filtrado cliente por texto
  const filtered = useMemo(() => {
    if (!search.trim()) return rows;
    const q = search.toLowerCase();
    return rows.filter((h) =>
      [
        h?.accion,
        h?.usuario_nombre,
        h?.usuario_email,
        h?.tecnico_nombre,
        h?.direccion,
        h?.comuna,
        h?.zona,
      ]
        .filter(Boolean)
        .some((txt) => String(txt).toLowerCase().includes(q))
    );
  }, [rows, search]);

  const dateOf = (h) => {
    // preferimos created_at si existe; fallback a fecha
    const raw = h?.created_at || h?.fecha;
    if (!raw) return "—";
    const d = new Date(raw);
    return isNaN(d) ? String(raw) : d.toLocaleString("es-CL");
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 1100 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Historial de Asignaciones</h1>
          <p className={styles.subtitle}>Registro completo de acciones</p>
        </header>

        {!isAdmin && (
          <div className={styles.error}>
            Solo los administradores pueden acceder a esta sección.
          </div>
        )}

        {isAdmin && (
          <>
            {/* Filtros */}
            <div
              className={styles.form}
              style={{ gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 8, marginBottom: 8 }}
            >
              <input
                className={styles.input}
                placeholder="Buscar por técnico, dirección, comuna, usuario…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <div>
                <div className={styles.helper} style={{ fontSize: 12, marginBottom: 4 }}>
                  Desde
                </div>
                <input
                  type="date"
                  className={styles.input}
                  value={desde}
                  onChange={(e) => setDesde(e.target.value)}
                />
              </div>
              <div>
                <div className={styles.helper} style={{ fontSize: 12, marginBottom: 4 }}>
                  Hasta
                </div>
                <input
                  type="date"
                  className={styles.input}
                  value={hasta}
                  onChange={(e) => setHasta(e.target.value)}
                />
              </div>
              <div>
                <div className={styles.helper} style={{ fontSize: 12, marginBottom: 4 }}>
                  Técnico
                </div>
                <select
                  className={styles.select}
                  value={tecnicoId}
                  onChange={(e) => setTecnicoId(e.target.value)}
                  disabled={loadingTechs}
                >
                  {techs.map((t) => (
                    <option key={t.value || "__all"} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Estado de carga/errores */}
            {error && <div className={styles.error} style={{ marginBottom: 8 }}>{error}</div>}
            {loading && <div className={styles.helper} style={{ marginBottom: 8 }}>Cargando historial…</div>}

            {/* Tabla */}
            {!loading && filtered.length === 0 ? (
              <div className={styles.helper}>No hay registros con los filtros seleccionados.</div>
            ) : (
              <>
                <div style={{ overflowX: "auto", border: "1px solid #e5e7eb", borderRadius: 6 }}>
                  <table
                    style={{
                      width: "100%",
                      borderCollapse: "collapse",
                      fontSize: 14,
                      backgroundColor: "#fff",
                    }}
                  >
                    <thead style={{ background: "#f3f4f6" }}>
                      <tr>
                        <th style={th}>Fecha</th>
                        <th style={th}>Acción</th>
                        <th style={th}>Técnico</th>
                        <th style={th}>Dirección</th>
                        <th style={th}>Comuna</th>
                        <th style={th}>Zona</th>
                        <th style={th}>Usuario que realizó la acción</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map((h, i) => (
                        <tr key={`${h.id || i}-${i}`} style={{ borderBottom: "1px solid #e5e7eb" }}>
                          <td style={td}>{dateOf(h)}</td>
                          <td style={{ ...td, fontWeight: 600, color: colorAccion(h.accion) }}>
                            {h.accion || "—"}
                          </td>
                          <td style={td}>{h.tecnico_nombre || "—"}</td>
                          <td style={td}>{h.direccion || "—"}</td>
                          <td style={td}>{h.comuna || "—"}</td>
                          <td style={td}>{h.zona || "—"}</td>
                          <td style={td}>{h.usuario_nombre || h.usuario_email || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Sentinel para scroll infinito */}
                <div ref={sentinelRef} style={{ height: 1 }} />

                {/* Indicador de paginación */}
                <div style={{ display: "flex", justifyContent: "center", padding: 8 }}>
                  {loadingMore && <span className={styles.helper}>Cargando más…</span>}
                  {!nextUrl && !loadingMore && rows.length > 0 && (
                    <span className={styles.helper}>No hay más registros.</span>
                  )}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
