// src/pages/AuditorDireccionesLista.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

const LIST_ENDPOINT = "/api/asignaciones/";
const UPLOAD_ENDPOINT = "/api/asignaciones/cargar_csv/";
const MARCAS = ["CLARO", "VTR"];
const TECNOLOGIAS = ["HFC", "NFTT", "FTTH"];
const ZONAS = ["NORTE", "CENTRO", "SUR"];
const ESTADOS = ["pendiente", "asignada", "visitada", "cancelada", "reagendada"];

function pickResults(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.results)) return data.results;
  return [];
}

function ymdToDmy(s) {
  if (!s) return "—";
  const [y, m, d] = String(s).slice(0, 10).split("-");
  return `${d.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
}

function getEffectiveDate(it) {
  if (String(it.estado).toUpperCase() === "REAGENDADA" && it.reagendado_fecha) {
    return it.reagendado_fecha;
  }
  return it.fecha || "";
}

function buildUserLabel(u) {
  if (!u) return "—";
  if (u.first_name || u.last_name) return `${u.first_name ?? ""} ${u.last_name ?? ""}`.trim();
  return u.email || `Tec#${u.id}`;
}

export default function AuditorDireccionesLista() {
  // eslint-disable-next-line no-unused-vars
  const { user } = useAuth();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState(""); // mensajes de éxito/estado
  const [query, setQuery] = useState("");
  const [filtro, setFiltro] = useState({ estado: "", tecnologia: "", marca: "", zona: "" });
  const [count, setCount] = useState(0);
  const [nextUrl, setNextUrl] = useState(null);
  const [prevUrl, setPrevUrl] = useState(null);
  const fetchId = useRef(0);

  // Técnicos: id → usuario
  const [techMap, setTechMap] = useState(new Map());

  // input file oculto para importación
  const fileInputRef = useRef(null);

  // Cargar técnicos (paginado)
  useEffect(() => {
    (async () => {
      try {
        let url = "/api/usuarios/?rol=tecnico";
        const all = [];
        for (;;) {
          const res = await api.get(url);
          const data = res.data || {};
          all.push(...pickResults(data));
          if (!data.next) break;
          url = data.next;
        }
        const map = new Map();
        for (const u of all) map.set(u.id, u);
        setTechMap(map);
      } catch (err) {
        console.warn("No se pudieron cargar técnicos:", err);
        setTechMap(new Map());
      }
    })();
  }, []);

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
    setFeedback("");
    const myFetch = ++fetchId.current;
    try {
      const res = absoluteUrl
        ? await api.get(absoluteUrl)
        : await api.get(LIST_ENDPOINT, { params: paramsForBackend });
      if (myFetch !== fetchId.current) return;
      const data = res.data || {};
      const results = pickResults(data);
      setItems(results);
      setCount(data.count ?? results.length);
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
        it.marca, it.tecnologia, it.zona, it.estado,
      ].filter(Boolean).join(" ").toLowerCase();
      return bag.includes(q);
    });
  }, [items, query, filtro]);

  function getTecnicoNombre(it) {
    const t = it.tecnico;
    const id = it.asignado_a;
    if (t && typeof t === "object") return t.nombre || t.email || buildUserLabel(t);
    if (typeof id === "number" && techMap.has(id)) return buildUserLabel(techMap.get(id));
    if (typeof id === "number") return `Tec#${id}`;
    return "—";
  }

  async function handleDelete(item) {
    if (!confirm(`¿Eliminar la dirección "${item.direccion}" (ID ${item.id})?`)) return;
    try {
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

  // -------- Importar CSV/XLSX ----------
  function triggerFileDialog() {
    if (uploading) return;
    setError("");
    setFeedback("");
    fileInputRef.current?.click();
  }

  async function handleFileChange(e) {
    const file = e.target.files?.[0];
    e.target.value = ""; // permite volver a seleccionar el mismo archivo después
    if (!file) return;

    // Validar extensión simple
    const okExt = /\.(csv|xlsx)$/i.test(file.name);
    if (!okExt) {
      setError("Formato no soportado. Sube un .csv o .xlsx");
      return;
    }

    const form = new FormData();
    form.append("file", file);

    setUploading(true);
    setError("");
    setFeedback("");

    try {
      // CSRF primero
      await api.get("/auth/csrf");

      const res = await api.post(UPLOAD_ENDPOINT, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      // Mensaje amigable según respuesta
      const data = res?.data;
      let msg = "Archivo importado correctamente.";
      // Si tu backend devuelve algo tipo { processed, created, updated, errors }
      if (data && typeof data === "object") {
        const parts = [];
        if (data.processed != null) parts.push(`procesados: ${data.processed}`);
        if (data.created != null) parts.push(`creados: ${data.created}`);
        if (data.updated != null) parts.push(`actualizados: ${data.updated}`);
        if (data.errors?.length) parts.push(`errores: ${data.errors.length}`);
        if (parts.length) msg = `Importación OK — ${parts.join(" · ")}`;
      }

      setFeedback(msg);
      await load(); // refresca lista
    } catch (err) {
      console.error("UPLOAD asignaciones:", err?.response?.status, err?.response?.data);
      const data = err?.response?.data;
      const msg =
        (typeof data === "string" && data) ||
        data?.detail ||
        data?.error ||
        "No se pudo importar el archivo.";
      setError(msg);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 1100 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Direcciones (Auditor)</h1>
          <p className={styles.subtitle}>Gestiona todas las direcciones</p>
        </header>

        <div className={styles.actions} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Link to="/auditor/direcciones/nueva" className={styles.button}>+ Nueva dirección</Link>

          {/* Botón Importar */}
          <button
            className={styles.button}
            onClick={triggerFileDialog}
            disabled={uploading}
            title="Importar direcciones desde CSV o XLSX"
          >
            {uploading ? "Importando…" : "Importar CSV/XLSX"}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            style={{ display: "none" }}
            onChange={handleFileChange}
          />
        </div>

        {/* Mensajes */}
        {feedback && <div className={styles.success} style={{ marginTop: 8 }}>{feedback}</div>}
        {error && <div className={styles.error} style={{ marginTop: 8 }}>{error}</div>}
        {loading && <div className={styles.helper} style={{ marginTop: 8 }}>Cargando…</div>}

        {/* Filtros */}
        <div className={styles.form} style={{ gridTemplateColumns: "repeat(5, 1fr)", gap: 8, marginTop: 8 }}>
          <input
            className={styles.input}
            placeholder="Buscar por comuna, dirección, ID vivienda, RUT…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
          />
          <select className={styles.select} value={filtro.estado} onChange={(e) => setFiltro((f) => ({ ...f, estado: e.target.value }))} disabled={loading}>
            <option value="">Estado (todos)</option>
            {ESTADOS.map((s) => <option key={s} value={s}>{s[0].toUpperCase() + s.slice(1)}</option>)}
          </select>
          <select className={styles.select} value={filtro.tecnologia} onChange={(e) => setFiltro((f) => ({ ...f, tecnologia: e.target.value }))} disabled={loading}>
            <option value="">Tecnología (todas)</option>
            {TECNOLOGIAS.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <select className={styles.select} value={filtro.marca} onChange={(e) => setFiltro((f) => ({ ...f, marca: e.target.value }))} disabled={loading}>
            <option value="">Marca (todas)</option>
            {MARCAS.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
          <select className={styles.select} value={filtro.zona} onChange={(e) => setFiltro((f) => ({ ...f, zona: e.target.value }))} disabled={loading}>
            <option value="">Zona (todas)</option>
            {ZONAS.map((z) => <option key={z} value={z}>{z[0] + z.slice(1).toLowerCase()}</option>)}
          </select>
        </div>

        {/* Paginación */}
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 8 }}>
          <button className={styles.button} disabled={!prevUrl || loading} onClick={() => load(prevUrl || undefined)}>« Anterior</button>
          <button className={styles.button} disabled={!nextUrl || loading} onClick={() => load(nextUrl || undefined)}>Siguiente »</button>
          <span className={styles.helper}>{count} total</span>
        </div>

        {/* Tabla */}
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
                  <td>{getTecnicoNombre(it)}</td>
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
