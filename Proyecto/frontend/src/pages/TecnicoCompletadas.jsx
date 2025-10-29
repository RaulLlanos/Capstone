/* eslint-disable no-unused-vars */
// src/pages/TecnicoCompletadas.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import styles from "./Tecnico.module.css";

// Catálogos
const TECNOLOGIAS = ["HFC", "NFTT", "FTTH"];
const MARCAS = ["CLARO", "VTR"];
const ZONAS = ["NORTE", "CENTRO", "SUR"];

// ------------------------ Utils ------------------------
function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

// DD/MM/YYYY
function ymdToDmy(s) {
  if (!s) return "—";
  const ymd = String(s).slice(0, 10);
  const [y, m, d] = ymd.split("-");
  if (!y || !m || !d) return "—";
  return `${d.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
}

function effectiveDateYMD(it) {
  const r =
    it.reagendado_fecha ||
    (it.reagendado && (it.reagendado.fecha || it.reagendado.reagendado_fecha)) ||
    it.reagendadoFecha ||
    it.reagendado_date ||
    it.fecha;
  return String(r || "");
}

function parseYMD(ymd) {
  if (!ymd) return null;
  const [y, m, d] = ymd.split("-").map((x) => parseInt(x, 10));
  if (!y || !m || !d) return null;
  const dt = new Date(y, m - 1, d);
  return isNaN(dt.getTime()) ? null : dt;
}

// Lunes a domingo
function startOfWeek(date) {
  const d = new Date(date);
  const day = d.getDay(); // 0 dom ... 1 lun ... 6 sáb
  const diff = (day === 0 ? -6 : 1 - day);
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}
function endOfWeek(date) {
  const start = startOfWeek(date);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);
  end.setHours(23, 59, 59, 999);
  return end;
}
function shiftWeeks(date, n) {
  const d = new Date(date);
  d.setDate(d.getDate() + n * 7);
  return d;
}
function isWithin(date, start, end) {
  if (!date || !start || !end) return false;
  return date >= start && date <= end;
}
function fmtDate(d) {
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
}

// ------------------------ Page ------------------------
export default function TecnicoCompletadas() {
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [flash, setFlash] = useState("");

  const [q, setQ] = useState("");
  const [filtro, setFiltro] = useState({ tecnologia: "", marca: "", zona: "" });
  const [weekOffset, setWeekOffset] = useState(0); // 0=actual, -1=anterior, +1=siguiente
  const [showAll, setShowAll] = useState(false);

  const [me, setMe] = useState(null);
  const fetchId = useRef(0);

  // ---------- Carga ----------
  const load = async () => {
    setLoading(true);
    setError("");
    const myFetch = ++fetchId.current;

    try {
      const rMe = await api.get("/api/usuarios/me/");
      const myUser = rMe.data || {};
      setMe(myUser);

      const resp = await api.get("/api/asignaciones/", {
        params: { estado: "VISITADA", asignado_a: myUser.id },
      });

      if (myFetch !== fetchId.current) return;
      setItems(normalizeList(resp.data));
    } catch (err) {
      console.error("GET completadas:", err?.response?.status, err?.response?.data);
      setError("No se pudo cargar la lista de visitas completadas.");
      setItems([]);
    } finally {
      if (myFetch === fetchId.current) setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  // ---------- Rango actual ----------
  const { rangeLabel, rangeStart, rangeEnd } = useMemo(() => {
    if (showAll) return { rangeLabel: "Todas las semanas", rangeStart: null, rangeEnd: null };

    const base = shiftWeeks(new Date(), weekOffset);
    const start = startOfWeek(base);
    const end = endOfWeek(base);
    const label = `Semana ${weekOffset === 0 ? "actual" : weekOffset === -1 ? "pasada" : ""} (${fmtDate(
      start
    )}–${fmtDate(end)})`;
    return { rangeLabel: label, rangeStart: start, rangeEnd: end };
  }, [showAll, weekOffset]);

  // ---------- Filtrado en memoria ----------
  const completadas = useMemo(() => {
    const text = q.trim().toLowerCase();
    return (items || [])
      .filter((it) => {
        if (filtro.tecnologia && String(it.tecnologia || "") !== filtro.tecnologia) return false;
        if (filtro.marca && String(it.marca || "") !== filtro.marca) return false;
        if (filtro.zona && String(it.zona || "") !== filtro.zona) return false;

        if (text) {
          const bag = [
            it.direccion,
            it.comuna,
            it.id_vivienda,
            it.rut_cliente,
            it.marca,
            it.tecnologia,
            it.zona,
            it.estado,
            it.encuesta,
          ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();
          if (!bag.includes(text)) return false;
        }

        if (!showAll) {
          const d = parseYMD(effectiveDateYMD(it));
          if (!isWithin(d, rangeStart, rangeEnd)) return false;
        }

        return true;
      })
      .sort((a, b) => {
        const da = parseYMD(effectiveDateYMD(a));
        const db = parseYMD(effectiveDateYMD(b));
        return (db?.getTime() || 0) - (da?.getTime() || 0);
      });
  }, [items, q, filtro, rangeStart, rangeEnd, showAll]);

  const renderFechaInfo = (it) => {
    const effDate = effectiveDateYMD(it);
    const effBlock =
      it.reagendado_bloque ||
      (it.reagendado && (it.reagendado.bloque || it.reagendado.reagendado_bloque)) ||
      it.reagendadoBloque ||
      it.reagendado_block ||
      it.bloque;
    const parts = [effDate ? ymdToDmy(effDate) : "—"];
    if (effBlock) parts.push(effBlock);
    return parts.join(" · ");
  };

  // ------------------------ UI ------------------------
  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        {flash && <div className={styles.success} style={{ marginBottom: 8 }}>{flash}</div>}

        <header className={styles.header}>
          <h1 className={styles.title}>Visitas completadas</h1>
          <p className={styles.subtitle}>
            Aquí ves <strong>solo</strong> las visitas marcadas como <strong>VISITADA</strong> por ti.
          </p>
        </header>

        {/* Filtros */}
        <div className={`${styles.form} ${styles.filtersRow}`}>
          <input
            className={styles.input}
            placeholder="Buscar por dirección, comuna, RUT…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            disabled={loading}
          />

          <select
            className={styles.select}
            value={filtro.tecnologia}
            onChange={(e) => setFiltro((f) => ({ ...f, tecnologia: e.target.value }))}
            disabled={loading}
          >
            <option value="">Tecnología</option>
            {TECNOLOGIAS.map((t) => (
              <option key={t} value={t}>{t}</option>
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
              <option key={m} value={m}>{m}</option>
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
              <option key={z} value={z}>{z[0] + z.slice(1).toLowerCase()}</option>
            ))}
          </select>
        </div>

        {/* Control de semanas */}
        <div style={{ display: "flex", alignItems: "center", marginTop: 10, marginBottom: 10 }}>
          {!showAll && (
            <>
              <button
                className={styles.button}
                style={{ marginRight: 8 }}
                onClick={() => setWeekOffset((o) => o - 1)}
              >
                ‹ Semana anterior
              </button>
              <div className={styles.helper} style={{ flex: 1, textAlign: "center", fontWeight: 600 }}>
                {rangeLabel}
              </div>
              <button
                className={styles.button}
                style={{ marginLeft: 8 }}
                onClick={() => setWeekOffset((o) => o + 1)}
              >
                Semana siguiente ›
              </button>
            </>
          )}
          <button
            className={styles.button}
            style={{ marginLeft: 10 }}
            onClick={() => {
              if (showAll) setShowAll(false);
              else {
                setShowAll(true);
                setWeekOffset(0);
              }
            }}
          >
            {showAll ? "Volver a semanas" : "Ver todas"}
          </button>
        </div>

        {error && <div className={styles.error}>{error}</div>}
        {loading && <div className={styles.helper}>Cargando…</div>}

        {/* Lista */}
        <section style={{ marginTop: 16 }}>
          <h2 className={styles.sectionTitle}>Total: {completadas.length}</h2>
          <div className={styles.listGrid}>
            {completadas.map((it) => (
              <div key={`comp-${it.id}`} className={styles.cardItem}>
                <div className={styles.cardItemTop}>
                  <strong>{it.direccion}</strong>
                  <small className={styles.helper}>{renderFechaInfo(it)}</small>
                </div>

                <div className={styles.helper}>
                  Comuna: {it.comuna} — Zona: {it.zona} — Marca: {it.marca} — Tec.: {it.tecnologia}
                </div>
                <div className={styles.helper}>
                  RUT cliente: {it.rut_cliente} · ID vivienda: {it.id_vivienda} · Encuesta: {it.encuesta}
                </div>

                <div className={styles.actions}>
                  <button
                    className={styles.button}
                    onClick={() => navigate(`/tecnico/auditoria/ver/${it.id}`)}
                  >
                    Ver auditoría
                  </button>
                </div>
              </div>
            ))}
            {!loading && completadas.length === 0 && (
              <div className={styles.helper}>No hay visitas en el rango seleccionado.</div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
