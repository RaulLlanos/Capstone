// src/pages/TecnicoDireccionesLista.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import api from "../services/api";
import styles from "./Login.module.css";
import { useAuth } from "../context/AuthContext";

const LIST_ENDPOINT = "/api/asignaciones/";
const ACTION_POST = (id) => `/api/asignaciones/${id}/asignarme/`;
const ACTION_PATCH = (id) => `/api/asignaciones/${id}/`;

const MARCAS = ["CLARO", "VTR"];
const TECNOLOGIAS = ["HFC", "NFTT", "FTTH"];
const ZONAS = ["NORTE", "CENTRO", "SUR"];
const ESTADOS = ["pendiente", "asignada", "completada", "cancelada"];

// Normaliza DRF paginado
function pickResults(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.results)) return data.results;
  return [];
}

export default function TecnicoDireccionesLista() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [filtro, setFiltro] = useState({
    estado: "pendiente",
    tecnologia: "",
    marca: "",
    zona: "",
  });

  // paginación (DRF)
  const [count, setCount] = useState(0);
  const [nextUrl, setNextUrl] = useState(null);
  const [prevUrl, setPrevUrl] = useState(null);

  const fetchId = useRef(0);

  const paramsForBackend = useMemo(() => {
    // Si tu ViewSet filtra por query params, se los pasamos. Igual filtramos en frontend.
    const p = {};
    if (filtro.estado) p.estado = filtro.estado.toUpperCase(); // backend devuelve uppercase
    if (filtro.tecnologia) p.tecnologia = filtro.tecnologia;
    if (filtro.marca) p.marca = filtro.marca;
    if (filtro.zona) p.zona = filtro.zona;
    return p;
  }, [filtro]);

  const load = async (absoluteUrl) => {
    setLoading(true);
    setError("");
    const myFetch = ++fetchId.current;
    try {
      const res = absoluteUrl
        ? await api.get(absoluteUrl) // url completa de next/previous
        : await api.get(LIST_ENDPOINT, { params: paramsForBackend });

      if (myFetch !== fetchId.current) return;

      const data = res.data || {};
      setItems(pickResults(data));
      setCount(data.count ?? pickResults(data).length);
      setNextUrl(data.next || null);
      setPrevUrl(data.previous || null);
    } catch (err) {
      console.error("Error GET /api/asignaciones/:", err?.response?.status, err?.response?.data);
      setError("No se pudo cargar la lista de direcciones.");
      setItems([]);
      setCount(0);
      setNextUrl(null);
      setPrevUrl(null);
    } finally {
      if (myFetch === fetchId.current) setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsForBackend.estado, paramsForBackend.tecnologia, paramsForBackend.marca, paramsForBackend.zona]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items.filter((it) => {
      // Normalizamos estado a minúsculas para comparar con el filtro
      const estadoIt = String(it.estado || "").toLowerCase();
      if (filtro.estado && estadoIt !== filtro.estado) return false;
      if (filtro.tecnologia && String(it.tecnologia || "") !== filtro.tecnologia) return false;
      if (filtro.marca && String(it.marca || "") !== filtro.marca) return false;
      if (filtro.zona && String(it.zona || "") !== filtro.zona) return false;

      if (!q) return true;
      const bag = [
        it.comuna,
        it.direccion,
        it.id_vivienda,
        it.rut_cliente,
        it.encuesta,
        it.marca,
        it.tecnologia,
        it.zona,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return bag.includes(q);
    });
  }, [items, query, filtro]);

  async function asignarme(item) {
    const original = [...items];
    const idx = items.findIndex((x) => x.id === item.id);

    try {
      if (idx !== -1) {
        const clone = [...items];
        clone[idx] = { ...clone[idx], __busy: true };
        setItems(clone);
      }

      // 1) Acción dedicada POST /api/asignaciones/:id/asignarme/
      try {
        await api.post(ACTION_POST(item.id));
        const updated = [...original];
        if (idx !== -1) {
          updated[idx] = {
            ...original[idx],
            estado: "ASIGNADA",
            asignado_a: user?.email || user?.id || "tú",
          };
        }
        setItems(updated);
        return;
      } catch (err) {
        if (err?.response?.status !== 404) {
          // 409: ya asignada, 400: regla de negocio → recargamos para estado real
          if (err?.response?.status === 409 || err?.response?.status === 400) {
            await load();
            return;
          }
          // probamos PATCH abajo
        }
      }

      // 2) Fallback PATCH /api/asignaciones/:id/
      try {
        await api.patch(ACTION_PATCH(item.id), { asignarme: true });
        const updated = [...original];
        if (idx !== -1) {
          updated[idx] = {
            ...original[idx],
            estado: "ASIGNADA",
            asignado_a: user?.email || user?.id || "tú",
          };
        }
        setItems(updated);
        return;
      } catch (err) {
        if (err?.response?.status === 409 || err?.response?.status === 400) {
          await load();
          return;
        }
        throw err;
      }
    } catch (err) {
      console.error("Asignarme falló:", err?.response?.status, err?.response?.data);
      setError("No se pudo asignar la dirección.");
      setItems(original);
    }
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 980 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Direcciones disponibles</h1>
          <p className={styles.subtitle}>Elige una y asígnatela</p>
        </header>

        {/* Filtros */}
        <div className={styles.form} style={{ gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 8 }}>
          <input
            className={styles.input}
            placeholder="Buscar por comuna, dirección, ID vivienda, RUT…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
          />

          <select
            className={styles.select}
            value={filtro.estado}
            onChange={(e) => setFiltro((f) => ({ ...f, estado: e.target.value }))}
            disabled={loading}
          >
            {ESTADOS.map((s) => (
              <option key={s} value={s}>
                {s[0].toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>

          <select
            className={styles.select}
            value={filtro.tecnologia}
            onChange={(e) => setFiltro((f) => ({ ...f, tecnologia: e.target.value }))}
            disabled={loading}
          >
            <option value="">Tecnología</option>
            {TECNOLOGIAS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>

          <select
            className={styles.select}
            value={filtro.marca}
            onChange={(e) => setFiltro((f) => ({ ...f, marca: e.target.value }))}
            disabled={loading}
          >
            <option value="">Marca</option>
            {MARCAS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>

          <select
            className={styles.select}
            value={filtro.zona}
            onChange={(e) => setFiltro((f) => ({ ...f, zona: e.target.value }))}
            disabled={loading}
          >
            <option value="">Zona</option>
            {ZONAS.map((z) => (
              <option key={z} value={z}>
                {z[0] + z.slice(1).toLowerCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Paginación */}
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 8 }}>
          <button className={styles.button} disabled={!prevUrl || loading} onClick={() => load(prevUrl || undefined)}>
            « Anterior
          </button>
          <button className={styles.button} disabled={!nextUrl || loading} onClick={() => load(nextUrl || undefined)}>
            Siguiente »
          </button>
          <span className={styles.helper}>{count} total</span>
        </div>

        {error && <div className={styles.error} style={{ marginTop: 8 }}>{error}</div>}
        {loading && <div className={styles.helper} style={{ marginTop: 8 }}>Cargando…</div>}

        {/* Lista */}
        <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
          {filtered.map((it) => (
            <div
              key={it.id}
              style={{
                border: "1px solid #e5e7eb",
                borderRadius: 10,
                padding: 12,
                display: "grid",
                gap: 6,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                <strong>{it.direccion}</strong>
                <small className={styles.helper}>
                  {(it.fecha && new Date(it.fecha).toLocaleDateString()) || "—"} · {String(it.estado || "")}
                </small>
              </div>
              <div className={styles.helper}>
                Comuna: {it.comuna} — Zona: {it.zona} — Marca: {it.marca} — Tec.: {it.tecnologia}
              </div>
              <div className={styles.helper}>
                RUT cliente: {it.rut_cliente} · ID vivienda: {it.id_vivienda} · Encuesta: {it.encuesta}
              </div>

              <div className={styles.actions}>
                {String(it.asignado_a || "").length > 0 ? (
                  <div className={styles.helper}>
                    Asignada a: {String(it.asignado_a) === (user?.email || user?.id) ? "tí" : String(it.asignado_a)}
                  </div>
                ) : (
                  <button
                    className={styles.button}
                    onClick={() => asignarme(it)}
                    disabled={!!it.__busy || loading || String(it.estado || "").toLowerCase() !== "pendiente"}
                  >
                    {it.__busy ? "Asignando…" : "Asignarme"}
                  </button>
                )}
              </div>
            </div>
          ))}

          {!loading && filtered.length === 0 && (
            <div className={styles.helper}>No hay direcciones con los filtros actuales.</div>
          )}
        </div>
      </div>
    </div>
  );
}
