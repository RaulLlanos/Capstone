// src/pages/AuditorDireccionesLista.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
//import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

const LIST_ENDPOINT = "/api/asignaciones/";

const MARCAS = ["CLARO", "VTR"];
const TECNOLOGIAS = ["HFC", "NFTT", "FTTH"];
const ZONAS = ["NORTE", "CENTRO", "SUR"];
const ESTADOS = ["pendiente", "asignada", "completada", "cancelada", "reagendada"];

function pickResults(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.results)) return data.results;
  return [];
}

  // Convierte "YYYY-MM-DD" (o con hora) a "DD/MM/YYYY" sin problemas de zona horaria
  function ymdToDmy(s) {
    if (!s) return "—";
    const ymd = String(s).slice(0, 10);
    const [y, m, d] = ymd.split("-");
    if (!y || !m || !d) return "—";
    return `${d.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
  }

  function getEffectiveDate(it) {
    if (String(it.estado).toUpperCase() === "REAGENDADA" && it.reagendado_fecha) {
      return it.reagendado_fecha;
    }
    return it.fecha || "";
  }



export default function AuditorDireccionesLista() {
  const { user } = useAuth();
  //const navigate = useNavigate();

  if (user && (user.role || user.rol) !== "auditor") {
    // navigate("/");
  }

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [query, setQuery] = useState("");
  const [filtro, setFiltro] = useState({
    estado: "",
    tecnologia: "",
    marca: "",
    zona: "",
  });

  const [count, setCount] = useState(0);
  const [nextUrl, setNextUrl] = useState(null);
  const [prevUrl, setPrevUrl] = useState(null);

  const fetchId = useRef(0);

  const paramsForBackend = useMemo(() => {
    const p = {};
    if (filtro.estado) p.estado = filtro.estado.toUpperCase();
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
      const res = absoluteUrl ? await api.get(absoluteUrl) : await api.get(LIST_ENDPOINT, { params: paramsForBackend });
      if (myFetch !== fetchId.current) return;
      const data = res.data || {};
      setItems(pickResults(data));
      setCount(data.count ?? pickResults(data).length);
      setNextUrl(data.next || null);
      setPrevUrl(data.previous || null);
    } catch (err) {
      console.error("GET asignaciones:", err?.response?.status, err?.response?.data);
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
      if (filtro.estado && String(it.estado || "").toLowerCase() !== filtro.estado) return false;
      if (filtro.tecnologia && String(it.tecnologia || "") !== filtro.tecnologia) return false;
      if (filtro.marca && String(it.marca || "") !== filtro.marca) return false;
      if (filtro.zona && String(it.zona || "") !== filtro.zona) return false;

      if (!q) return true;
      const bag = [
        it.comuna, it.direccion, it.id_vivienda, it.rut_cliente, it.encuesta,
        it.marca, it.tecnologia, it.zona, it.estado, it.asignado_a,
      ].filter(Boolean).join(" ").toLowerCase();
      return bag.includes(q);
    });
  }, [items, query, filtro]);

  async function handleDelete(item) {
    if (!confirm(`¿Eliminar la dirección "${item.direccion}" (ID ${item.id})? Esta acción no se puede deshacer.`)) {
      return;
    }
    try {
      // CSRF antes de DELETE
      await api.get("/auth/csrf");
      await api.delete(`/api/asignaciones/${item.id}/`);
      setItems((arr) => arr.filter((x) => x.id !== item.id));
      setCount((c) => Math.max(0, c - 1));
    } catch (err) {
      console.error("DELETE asignacion:", err?.response?.status, err?.response?.data);
      const data = err?.response?.data;
      const msg = typeof data === "string" ? data : (data?.detail || data?.error);
      setError(msg || "No se pudo eliminar la dirección.");
    }
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 1100 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Direcciones (Auditor)</h1>
          <p className={styles.subtitle}>Gestiona todas las direcciones</p>
        </header>

        <div className={styles.actions} style={{ display: "flex", gap: 8 }}>
          <Link to="/auditor/direcciones/nueva" className={styles.button}>+ Nueva dirección</Link>
        </div>

        <div className={styles.form} style={{ gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr", gap: 8, marginTop: 8 }}>
          <input className={styles.input} placeholder="Buscar por comuna, dirección, ID vivienda, RUT, técnico…"
                 value={query} onChange={(e) => setQuery(e.target.value)} disabled={loading}/>
          <select className={styles.select} value={filtro.estado}
                  onChange={(e) => setFiltro((f) => ({ ...f, estado: e.target.value }))} disabled={loading}>
            <option value="">Estado (todos)</option>
            {ESTADOS.map((s) => <option key={s} value={s}>{s[0].toUpperCase() + s.slice(1)}</option>)}
          </select>
          <select className={styles.select} value={filtro.tecnologia}
                  onChange={(e) => setFiltro((f) => ({ ...f, tecnologia: e.target.value }))} disabled={loading}>
            <option value="">Tecnología (todas)</option>
            {TECNOLOGIAS.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <select className={styles.select} value={filtro.marca}
                  onChange={(e) => setFiltro((f) => ({ ...f, marca: e.target.value }))} disabled={loading}>
            <option value="">Marca (todas)</option>
            {MARCAS.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
          <select className={styles.select} value={filtro.zona}
                  onChange={(e) => setFiltro((f) => ({ ...f, zona: e.target.value }))} disabled={loading}>
            <option value="">Zona (todas)</option>
            {ZONAS.map((z) => <option key={z} value={z}>{z[0] + z.slice(1).toLowerCase()}</option>)}
          </select>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 8 }}>
          <button className={styles.button} disabled={!prevUrl || loading} onClick={() => load(prevUrl || undefined)}>« Anterior</button>
          <button className={styles.button} disabled={!nextUrl || loading} onClick={() => load(nextUrl || undefined)}>Siguiente »</button>
          <span className={styles.helper}>{count} total</span>
        </div>

        {error && <div className={styles.error} style={{ marginTop: 8 }}>{error}</div>}
        {loading && <div className={styles.helper} style={{ marginTop: 8 }}>Cargando…</div>}

        <div style={{ overflowX: "auto", marginTop: 12 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead style={{ textAlign: "left" }}>
              <tr>
                <th>Fecha</th><th>Dirección</th><th>Comuna</th><th>Zona</th><th>Marca</th><th>Tec.</th>
                <th>Estado</th><th>Asignado a</th><th>ID viv.</th><th>Encuesta</th><th style={{ width: 220 }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((it) => (
                <tr key={it.id} style={{ borderTop: "1px solid #e5e7eb" }}>
                  <td>{ymdToDmy(getEffectiveDate(it))}</td>
                  <td>{it.direccion}</td>
                  <td>{it.comuna}</td>
                  <td>{it.zona}</td>
                  <td>{it.marca}</td>
                  <td>{it.tecnologia}</td>
                  <td>{String(it.estado || "")}</td>
                  <td>{(it.tecnico && (it.tecnico.nombre || it.tecnico.email)) || it.asignado_a || "—"}</td>
                  <td>{it.id_vivienda}</td>
                  <td>{it.encuesta}</td>
                  <td style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    <Link className={styles.button} to={`/auditor/direcciones/${it.id}/editar`}>Editar</Link>
                    <button className={styles.button} onClick={() => handleDelete(it)}>Eliminar</button>
                  </td>
                </tr>
              ))}
              {!loading && filtered.length === 0 && (
                <tr><td colSpan={11} className={styles.helper}>Sin resultados con los filtros actuales.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
