
// src/pages/Tecnico.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Tecnico.module.css";

const TECNOLOGIAS = ["HFC", "NFTT", "FTTH"];
const MARCAS = ["CLARO", "VTR"];
const ZONAS = ["NORTE", "CENTRO", "SUR"];

// === Utils ===
function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}
function todayLocalYMD() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}
function ymdToDmy(s) {
  if (!s) return "—";
  const ymd = String(s).slice(0, 10);
  const [y, m, d] = ymd.split("-");
  if (!y || !m || !d) return "—";
  return `${d.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
}

// === Reagendamiento (efectivo) ===
function getEffectiveDate(it) {
  const r =
    it.reagendado_fecha ||
    (it.reagendado && (it.reagendado.fecha || it.reagendado.reagendado_fecha)) ||
    it.reagendadoFecha ||
    it.reagendado_date;
  return String(r || it.fecha || "");
}
function getEffectiveBlock(it) {
  const r =
    it.reagendado_bloque ||
    (it.reagendado && (it.reagendado.bloque || it.reagendado.reagendado_bloque)) ||
    it.reagendadoBloque ||
    it.reagendado_block;
  return String(r || it.bloque || "");
}
function isReagendado(it) {
  return Boolean(
    it.reagendado_fecha ||
      it.reagendado_bloque ||
      (it.reagendado && (it.reagendado.fecha || it.reagendado.bloque)) ||
      it.reagendadoFecha ||
      it.reagendadoBloque ||
      it.reagendado_date ||
      it.reagendado_block ||
      String(it.estado || "").toUpperCase() === "REAGENDADA"
  );
}
function showReagendadoBadge(it) {
  const eff = getEffectiveDate(it).slice(0, 10);
  const estado = String(it.estado || "").toUpperCase();
  // Solo mostrar si realmente está REAGENDADA y no es hoy
  return estado === "REAGENDADA" && eff !== todayLocalYMD();
}
const isCompletada = (it) => {
  const s = String(it.estado || "").toUpperCase();
  return s === "VISITADA" || s === "COMPLETADA";
};

// === Identificación del técnico asignado (defensivo) ===
function extractAssignedUser(item) {
  // Posibles campos del backend:
  // - tecnico: id | string | {id,email,...}
  // - tecnico_id: number
  // - tecnico_asignado: id | {id,email}
  // - asignado_a: id | string | {id,email}
  // - assigned_to / assigned / user: por si acaso
  const out = { id: null, email: null };

  const tryObj = (v) => {
    if (!v || typeof v !== "object") return;
    if (v.id != null) out.id = Number(v.id);
    if (v.email) out.email = String(v.email).toLowerCase();
    if (v.user && typeof v.user === "object") {
      if (out.id == null && v.user.id != null) out.id = Number(v.user.id);
      if (!out.email && v.user.email) out.email = String(v.user.email).toLowerCase();
    }
  };
  const tryScalar = (v) => {
    if (v == null || v === "") return;
    if (typeof v === "number") out.id = v;
    else if (typeof v === "string") {
      const n = Number(v);
      if (!Number.isNaN(n)) out.id = n;
      else if (v.includes("@")) out.email = v.toLowerCase();
    }
  };

  // orden de preferencia
  if ("tecnico" in item) {
    if (typeof item.tecnico === "object") tryObj(item.tecnico);
    else tryScalar(item.tecnico);
  }
  if (out.id == null && "tecnico_id" in item) tryScalar(item.tecnico_id);
  if (out.id == null && "tecnico_asignado" in item) {
    if (typeof item.tecnico_asignado === "object") tryObj(item.tecnico_asignado);
    else tryScalar(item.tecnico_asignado);
  }
  if (out.id == null && "asignado_a" in item) {
    if (typeof item.asignado_a === "object") tryObj(item.asignado_a);
    else tryScalar(item.asignado_a);
  }
  if (out.id == null && "assigned_to" in item) {
    if (typeof item.assigned_to === "object") tryObj(item.assigned_to);
    else tryScalar(item.assigned_to);
  }
  if (out.id == null && "assigned" in item) {
    if (typeof item.assigned === "object") tryObj(item.assigned);
    else tryScalar(item.assigned);
  }
  if (out.id == null && "user" in item) {
    if (typeof item.user === "object") tryObj(item.user);
    else tryScalar(item.user);
  }

  return out;
}

function belongsToUser(item, user) {
  if (!user) return false;
  const myId = user.id ?? null;
  const myEmail = user.email ? String(user.email).toLowerCase() : null;

  const assigned = extractAssignedUser(item);
  const idMatch = myId != null && assigned.id === myId;
  const emailMatch = myEmail && assigned.email && assigned.email === myEmail;
  return Boolean(idMatch || emailMatch);
}

export default function Tecnico() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [items, setItems] = useState([]);
  const [sourceIsMine, setSourceIsMine] = useState(false); // si viene de /mias/ no filtramos por usuario
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [flash, setFlash] = useState("");

  const [q, setQ] = useState("");
  const [filtro, setFiltro] = useState({ tecnologia: "", marca: "", zona: "" });

  const fetchId = useRef(0);
  const hoyYMD = todayLocalYMD();
  const hoyDMY = ymdToDmy(hoyYMD);


  const load = async () => {
    setLoading(true);
    setError("");
    const myFetch = ++fetchId.current;
    try {
      let data = null;

      // 1) Intentar /mias/
      try {
        const r1 = await api.get("/api/asignaciones/");
        if (myFetch !== fetchId.current) return;
        data = normalizeList(r1.data);
        setSourceIsMine(true);          // ya vienen “las mías”
      } catch { /* empty */ }

      setItems(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
      setError("No se pudo cargar la lista de visitas.");
      setItems([]);
    } finally {
      if (myFetch === fetchId.current) setLoading(false);
    }
  };


  useEffect(() => {
    load();
  }, []);

  // Hidratar reagendadas incompletas
  useEffect(() => {
    const needDetail = (items || [])
      .filter((it) => {
        const flagged = isReagendado(it);
        if (!flagged) return false;
        const hasEffDate =
          it.reagendado_fecha ||
          (it.reagendado && (it.reagendado.fecha || it.reagendado.reagendado_fecha)) ||
          it.reagendadoFecha ||
          it.reagendado_date;
        return !hasEffDate;
      })
      .slice(0, 10);

    if (!needDetail.length) return;
    let cancelled = false;
    (async () => {
      try {
        const results = await Promise.allSettled(
          needDetail.map((row) => api.get(`/api/asignaciones/${row.id}/`))
        );
        const byId = new Map(
          results
            .filter((r) => r.status === "fulfilled")
            .map((r) => [r.value.data.id, r.value.data])
        );
        if (cancelled || byId.size === 0) return;
        setItems((prev) => prev.map((it) => (byId.has(it.id) ? { ...it, ...byId.get(it.id) } : it)));
      } catch { /* empty */ }
    })();
    return () => {
      cancelled = true;
    };
  }, [items]);

  // Flash de navegación
  useEffect(() => {
    const msg = location.state?.flash;
    if (msg) {
      setFlash(msg);
      navigate(location.pathname, { replace: true });
      const t = setTimeout(() => setFlash(""), 3000);
      return () => clearTimeout(t);
    }
  }, [location.state, location.pathname, navigate]);

  // Mis visitas filtradas (si viene de /mias/ no aplicamos belongsToUser)
  const misVisitas = useMemo(() => {
    const text = q.trim().toLowerCase();

    return (items || [])
      .filter((it) => (sourceIsMine ? true : belongsToUser(it, user)))
      .filter((it) => String(it.estado || "").toUpperCase() !== "VISITADA")
      .filter((it) => {
        if (filtro.tecnologia && String(it.tecnologia || "") !== filtro.tecnologia) return false;
        if (filtro.marca && String(it.marca || "") !== filtro.marca) return false;
        if (filtro.zona && String(it.zona || "") !== filtro.zona) return false;
        if (!text) return true;
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
        return bag.includes(text);
      })
      .sort((a, b) => getEffectiveDate(a).localeCompare(getEffectiveDate(b)));
  }, [items, user, q, filtro, sourceIsMine]);

  // Hoy vs resto
  const visitasDeHoy = useMemo(
    () => misVisitas.filter((it) => getEffectiveDate(it).slice(0, 10) === hoyYMD),
    [misVisitas, hoyYMD]
  );
  const todasExceptoHoy = useMemo(
    () => misVisitas.filter((it) => getEffectiveDate(it).slice(0, 10) !== hoyYMD),
    [misVisitas, hoyYMD]
  );

  const goReagendar = (id) => navigate(`/tecnico/reagendar/${id}`);

  const renderFechaInfo = (it) => {
    const effDate = getEffectiveDate(it);
    const effBlock = getEffectiveBlock(it);
    const parts = [effDate ? ymdToDmy(effDate) : "—"];
    if (effBlock) parts.push(effBlock);
    return parts.join(" · ");
  };

  // Para hoy: reagendar + restaurar estado a ASIGNADA
  const setParaHoy = async (item, bloque = "10-13") => {
    try {
      await api.get("/auth/csrf").catch(() => {});
      await api.post(`/api/asignaciones/${item.id}/reagendar/`, { fecha: hoyYMD, bloque });
      await api.patch(`/api/asignaciones/${item.id}/`, { estado: "ASIGNADA" });

      setItems((prev) =>
        prev.map((it) =>
          it.id === item.id
            ? { ...it, estado: "ASIGNADA", reagendado_fecha: hoyYMD, reagendado_bloque: bloque }
            : it
        )
      );
      setFlash("Asignación movida a HOY.");
    } catch (err) {
      const data = err?.response?.data || {};
      setError(data.detail || data.error || "No se pudo mover a hoy.");
    }
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        {flash && <div className={styles.success} style={{ marginBottom: 8 }}>{flash}</div>}

        <header className={styles.header}>
          <h1 className={styles.title}>Mis visitas</h1>
          <p className={styles.subtitle}>Revisa tus asignaciones y las de <strong>hoy</strong>.</p>
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
            {TECNOLOGIAS.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <select
            className={styles.select}
            value={filtro.marca}
            onChange={(e) => setFiltro((f) => ({ ...f, marca: e.target.value }))}
            disabled={loading}
          >
            <option value="">Marca</option>
            {MARCAS.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
          <select
            className={styles.select}
            value={filtro.zona}
            onChange={(e) => setFiltro((f) => ({ ...f, zona: e.target.value }))}
            disabled={loading}
          >
            <option value="">Zona</option>
            {ZONAS.map((z) => <option key={z} value={z}>{z}</option>)}
          </select>
        </div>

        {error && <div className={styles.error}>{error}</div>}
        {loading && <div className={styles.helper}>Cargando…</div>}

        {/* Hoy */}
        <section style={{ marginTop: 16 }}>
          <h2 className={styles.sectionTitle}>Visitas de hoy ({hoyDMY})</h2>
          <div className={styles.listGrid}>
            {visitasDeHoy.map((it) => (
              <div key={`hoy-${it.id}`} className={styles.cardItem}>
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
                    onClick={() =>
                      navigate(
                        isCompletada(it)
                          ? `/tecnico/auditoria/ver/${it.id}`
                          : `/tecnico/auditoria/nueva/${it.id}`
                      )
                    }
                  >
                    {isCompletada(it) ? "Ver auditoría" : "Auditar"}
                  </button>
                  <button className={styles.button} onClick={() => goReagendar(it.id)}>
                    Reagendar
                  </button>
                </div>
              </div>
            ))}
            {!loading && visitasDeHoy.length === 0 && (
              <div className={styles.helper}>No tienes visitas programadas para hoy.</div>
            )}
          </div>
        </section>

        {/* Resto */}
        <section style={{ marginTop: 20 }}>
          <h2 className={styles.sectionTitle}>Todas mis visitas</h2>
          <div className={styles.listGrid}>
            {todasExceptoHoy.map((it) => (
              <div key={`todas-${it.id}`} className={styles.cardItem}>
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
                  {showReagendadoBadge(it) && (
                    <span className={`${styles.badge} ${styles.badgeReagendado}`}>Reagendado</span>
                  )}
                  <button
                    className={styles.button}
                    onClick={() =>
                      navigate(
                        isCompletada(it)
                          ? `/tecnico/auditoria/ver/${it.id}`
                          : `/tecnico/auditoria/nueva/${it.id}`
                      )
                    }
                  >
                    {isCompletada(it) ? "Ver auditoría" : "Auditar"}
                  </button>
                  <button className={styles.button} onClick={() => setParaHoy(it)}>
                    Para hoy
                  </button>
                  <button className={styles.button} onClick={() => goReagendar(it.id)}>
                    Reagendar
                  </button>
                </div>
              </div>
            ))}
            {!loading && todasExceptoHoy.length === 0 && (
              <div className={styles.helper}>No tienes más visitas fuera de hoy.</div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
