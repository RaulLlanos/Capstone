/* eslint-disable no-unused-vars */
// src/pages/AdminAuditoriasLista.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

// ---- Helpers ----

// Extrae lista desde DRF paginado o array llano
function pickResults(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.results)) return data.results;
  return [];
}

// Normaliza status (customer_status / estado_cliente / estado)
function normStatus(aud) {
  return String(aud?.customer_status ?? aud?.estado_cliente ?? aud?.estado ?? "").toUpperCase();
}

// Obtiene una etiqueta de técnico desde distintas formas posibles
function techLabel(aud, asign) {
  const t =
    asign?.tecnico?.email ||
    asign?.tecnico?.nombre ||
    asign?.tecnico?.full_name ||
    asign?.tecnico ||
    asign?.asignado_a?.email ||
    asign?.asignado_a?.nombre ||
    asign?.asignado_a ||
    aud?.tecnico_email ||
    aud?.tecnico_nombre ||
    "";
  return t || "—";
}

// Construye una fecha presentable (prioriza reagendado, luego fecha de asignación, y si no, created_at)
function dateStr(aud, asign) {
  const raw =
    aud?.reagendado_fecha ||
    asign?.reagendado_fecha ||
    asign?.fecha ||
    aud?.created_at ||
    "";
  if (!raw) return "—";
  const d = String(raw).slice(0, 10);
  const [y, m, dd] = d.split("-");
  if (!y || !m || !dd) return "—";
  return `${dd.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
}

// Divide un arreglo en chunks
function chunk(arr, size) {
  const out = [];
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
  return out;
}

export default function AdminAuditoriasLista() {
  const { user } = useAuth();
  const role = String(user?.rol || user?.role || "").toLowerCase();
  const isAdmin = role === "administrador";

  const [rows, setRows] = useState([]);  // filas normalizadas
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [query, setQuery] = useState("");

  const fetchId = useRef(0);

  // Carga todas las auditorías y “enriquece” con datos de la asignación (si solo viene el id)
  const load = async () => {
    setLoading(true);
    setErr("");
    const myFetch = ++fetchId.current;

    try {
      // 1) Traer todas las auditorías (paginar DRF)
      let url = "/api/auditorias/";
      const allAud = [];
      for (;;) {
        const res = await api.get(url);
        const data = res?.data || {};
        allAud.push(...pickResults(data));
        if (!data.next) break;
        url = data.next; // DRF puede entregar URL absoluta: api ya lo maneja
      }

      // 2) Construir set de IDs de asignación (solo número/id, evitar objetos)
      const asigIds = Array.from(
        new Set(
          allAud
            .map((a) =>
              typeof a.asignacion === "number"
                ? a.asignacion
                : (a.asignacion?.id ?? a.asignacion_id ?? a.asignacionId ?? null)
            )
            .filter(Boolean)
        )
      );

      // 3) Traer asignaciones en paralelo, con chunks para no saturar
      const asignMap = new Map();
      for (const group of chunk(asigIds, 10)) {
        const batch = await Promise.allSettled(
          group.map((id) => api.get(`/api/asignaciones/${id}/`))
        );
        batch.forEach((r, i) => {
          const id = group[i];
          if (r.status === "fulfilled") asignMap.set(id, r.value?.data || null);
        });
      }

      // 4) Normalizar filas (cada fila representa una auditoría)
      const normalized = allAud.map((a) => {
        const asigId =
          typeof a.asignacion === "number"
            ? a.asignacion
            : (a.asignacion?.id ?? a.asignacion_id ?? a.asignacionId ?? null);

        const asig = asigId ? asignMap.get(asigId) : (typeof a.asignacion === "object" ? a.asignacion : null);

        const direccion = a.direccion || asig?.direccion || a.asignacion_direccion || "—";
        const comuna = a.comuna || asig?.comuna || a.asignacion_comuna || "—";
        const marca = (a.marca || asig?.marca || "—").toString().toUpperCase();

        return {
          id: a.id,                     // id de la AUDITORÍA (lo que debes usar para ver detalle)
          asignacion_id: asigId || null,
          fecha: dateStr(a, asig),
          direccion,
          comuna,
          tecnico: techLabel(a, asig),
          marca,
          status: normStatus(a),
        };
      });

      if (myFetch !== fetchId.current) return;
      setRows(normalized);
    } catch (e) {
      console.error("AdminAuditoriasLista load error:", e?.response?.status, e?.response?.data);
      if (myFetch !== fetchId.current) return;
      setErr("No se pudieron cargar las auditorías.");
      setRows([]);
    } finally {
      if (myFetch === fetchId.current) setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Filtro por texto libre
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) =>
      [r.id, r.asignacion_id, r.direccion, r.comuna, r.tecnico, r.marca, r.status]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(q))
    );
  }, [rows, query]);

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
      <div className={styles.card} style={{ maxWidth: 1100 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Auditorías completadas</h1>
          <p className={styles.subtitle}>Filtra y revisa las visitas realizadas</p>
        </header>

        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <input
            className={styles.input}
            placeholder="Buscar dirección / id vivienda / rut / técnico…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
            style={{ flex: 1 }}
          />
          <button className={styles.button} onClick={load} disabled={loading}>
            Recargar
          </button>
        </div>

        {err && <div className={styles.error} style={{ marginTop: 8 }}>{err}</div>}
        {loading && <div className={styles.helper} style={{ marginTop: 8 }}>Cargando…</div>}

        <div style={{ overflowX: "auto", marginTop: 12 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead style={{ textAlign: "left" }}>
              <tr>
                <th>ID</th>
                <th>Fecha</th>
                <th>Dirección</th>
                <th>Comuna</th>
                <th>Técnico</th>
                <th>Marca</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id} style={{ borderTop: "1px solid #e5e7eb" }}>
                  <td>{r.id}</td>
                  <td>{r.fecha}</td>
                  <td>{r.direccion}</td>
                  <td>{r.comuna}</td>
                  <td>{r.tecnico}</td>
                  <td>{r.marca}</td>
                  <td>
                    {/* Enlaza por ID de AUDITORÍA (correcto) */}
                    <Link className={styles.button} to={`/panel/auditorias/${r.id}`}>
                      Ver detalles
                    </Link>
                  </td>
                </tr>
              ))}

              {!loading && filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className={styles.helper}>Sin resultados.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
