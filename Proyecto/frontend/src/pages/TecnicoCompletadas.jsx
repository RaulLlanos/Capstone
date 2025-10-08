// src/pages/TecnicoCompletadas.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Tecnico.module.css";

// Helpers compartidos
function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}
function isMine(item, user) {
  if (!user) return false;
  const myId = user.id ?? null;
  const myEmail = user.email ?? null;

  let tecnicoId = null;
  let tecnicoEmail = null;
  const t = item.tecnico;
  if (t && typeof t === "object") {
    if (t.id != null) tecnicoId = Number(t.id);
    if (t.email) tecnicoEmail = String(t.email).toLowerCase();
  } else if (typeof t === "number") {
    tecnicoId = t;
  } else if (typeof t === "string" && t.trim() !== "") {
    const n = Number(t);
    if (!Number.isNaN(n)) tecnicoId = n;
  }

  let asignadoId = null;
  const a = item.asignado_a;
  if (typeof a === "number") asignadoId = a;
  else if (typeof a === "string" && a.trim() !== "") {
    const n = Number(a);
    if (!Number.isNaN(n)) asignadoId = n;
  }

  const emailMatch = myEmail && (tecnicoEmail && tecnicoEmail === String(myEmail).toLowerCase());
  const idMatch = myId != null && (tecnicoId === myId || asignadoId === myId);
  return Boolean(emailMatch || idMatch);
}
function ymdToDmy(s) {
  if (!s) return "—";
  const ymd = String(s).slice(0, 10);
  const [y, m, d] = ymd.split("-");
  if (!y || !m || !d) return "—";
  return `${d.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
}
function getEffectiveDate(it) {
  const r =
    it.reagendado_fecha ||
    (it.reagendado && (it.reagendado.fecha || it.reagendado.reagendado_fecha)) ||
    it.reagendadoFecha ||
    it.reagendado_date;
  return String(r || it.fecha || "");
}
// ⬇️ Intentamos detectar la “fecha de realización” real.
// Ajusta los nombres si Raúl define uno oficial (p.ej. completed_at).
function getCompletionDate(it) {
  return (
    it.completada_fecha || it.completed_at || it.fecha_auditoria ||
    (it.auditoria && (it.auditoria.fecha || it.auditoria.created_at)) ||
    it.updated_at ||
    getEffectiveDate(it) // fallback
  );
}
const isCompletada = (it) => String(it.estado || "").toUpperCase() === "VISITADA";

export default function TecnicoCompletadas() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");
  const fetchId = useRef(0);

  const load = async () => {
    setLoading(true);
    setError("");
    const myFetch = ++fetchId.current;
    try {
      const res = await api.get("/api/asignaciones/");
      if (myFetch !== fetchId.current) return;
      setItems(normalizeList(res.data));
    } catch (err) {
      console.error(err);
      setError("No se pudo cargar el historial de visitas.");
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const completadas = useMemo(() => {
    const text = q.trim().toLowerCase();

    const mineCompleted = items
      .filter((it) => isMine(it, user))
      .filter(isCompletada)
      .filter((it) => {
        if (!text) return true;
        const bag = [
          it.direccion,
          it.comuna,
          it.id_vivienda,
          it.rut_cliente,
          it.marca,
          it.tecnologia,
          it.zona,
          it.encuesta,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return bag.includes(text);
      });

    // Ordenar por fecha de realización (desc)
    return mineCompleted.sort((a, b) => {
      const da = String(getCompletionDate(a)).slice(0, 10);
      const db = String(getCompletionDate(b)).slice(0, 10);
      // descendente
      return db.localeCompare(da);
    });
  }, [items, user, q]);

  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        <header className={styles.header}>
          <h1 className={styles.title}>Visitas completadas</h1>
          <p className={styles.subtitle}>Historial de tus visitas realizadas, ordenadas por fecha.</p>
        </header>

        <div className={`${styles.form} ${styles.filtersRow}`}>
          <input
            className={styles.input}
            placeholder="Buscar por dirección, comuna, ID vivienda, RUT…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            disabled={loading}
          />
        </div>

        {error && <div className={styles.error} style={{ marginTop: 8 }}>{error}</div>}
        {loading && <div className={styles.helper} style={{ marginTop: 8 }}>Cargando…</div>}

        <section style={{ marginTop: 16 }}>
          <h2 className={styles.sectionTitle}>Historial</h2>

          <div className={styles.listGrid}>
            {completadas.map((it) => {
              const doneDate = getCompletionDate(it);
              return (
                <div key={it.id} className={styles.cardItem}>
                  <div className={styles.cardItemTop}>
                    <strong>{it.direccion}</strong>
                    <small className={styles.helper}>
                      Realizada: {ymdToDmy(doneDate)} · {String(it.estado || "").toUpperCase()}
                    </small>
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
              );
            })}

            {!loading && completadas.length === 0 && (
              <div className={styles.helper}>No tienes visitas completadas aún.</div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
