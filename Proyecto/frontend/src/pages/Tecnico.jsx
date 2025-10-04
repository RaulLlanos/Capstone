// src/pages/Tecnico.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Tecnico.module.css";

const ESTADOS = ["PENDIENTE", "ASIGNADA", "COMPLETADA", "CANCELADA", "REAGENDADA"];
const TECNOLOGIAS = ["HFC", "NFTT", "FTTH"];
const MARCAS = ["CLARO", "VTR"];
const ZONAS = ["NORTE", "CENTRO", "SUR"];

// lista o paginada
function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

// yyyy-mm-dd local
function todayLocalYMD() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

const isCompletada = (it) => String(it.estado || "").toUpperCase() === "COMPLETADA";

// --- NUEVO: helpers de “fecha/bloque efectivos” ---
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
  return String(r || "");
}
function isReagendado(it) {
  const hasDate =
    it.reagendado_fecha ||
    (it.reagendado && (it.reagendado.fecha || it.reagendado.reagendado_fecha)) ||
    it.reagendadoFecha ||
    it.reagendado_date;
  const hasBlock =
    it.reagendado_bloque ||
    (it.reagendado && (it.reagendado.bloque || it.reagendado.reagendado_bloque)) ||
    it.reagendadoBloque ||
    it.reagendado_block;
  return Boolean(hasDate || hasBlock || String(it.estado).toUpperCase() === "REAGENDADA");
}

// asignación pertenece al usuario
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

  // Convierte "YYYY-MM-DD" (o "YYYY-MM-DDTHH:mm") a "DD/MM/YYYY"
  function ymdToDmy(s) {
    if (!s) return "—";
    const ymd = String(s).slice(0, 10); // por si viene con hora
    const [y, m, d] = ymd.split("-");
    if (!y || !m || !d) return s;
    return `${d.padStart(2,"0")}/${m.padStart(2,"0")}/${y}`;
  }


export default function Tecnico() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [flash, setFlash] = useState("");

  const [q, setQ] = useState("");
  const [filtro, setFiltro] = useState({
    estado: "", // todas
    tecnologia: "",
    marca: "",
    zona: "",
  });

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
      setError("No se pudo cargar la lista de visitas.");
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  // Hidratación: si la lista trae "reagendado" sin fecha, pedimos el detalle
  useEffect(() => {
    // candidatos: marcados como reagendados pero sin fecha efectiva
    const needDetail = items
      .filter((it) => isReagendado(it))
      .filter((it) => {
        const hasDate =
          it.reagendado_fecha ||
          (it.reagendado && (it.reagendado.fecha || it.reagendado.reagendado_fecha)) ||
          it.reagendadoFecha ||
          it.reagendado_date;
        return !hasDate; // faltante
      })
      .slice(0, 10); // límite de cortesía para no sobrecargar (ajusta si quieres)

    if (!needDetail.length) return;

    let isCancelled = false;

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
        if (isCancelled || byId.size === 0) return;

        // fusionamos en memoria: prioridad a datos del detalle
        setItems((prev) =>
          prev.map((it) => (byId.has(it.id) ? { ...it, ...byId.get(it.id) } : it))
        );
      } catch (e) {
        // silencioso; no interrumpe la UI
        console.warn("No se pudo hidratar detalles de reagendado:", e);
      }
    })();

    return () => {
      isCancelled = true;
    };
  }, [items]);


  // flash (por ejemplo, luego de reagendar)
  useEffect(() => {
    const msg = location.state?.flash;
    if (msg) {
      setFlash(msg);
      navigate(location.pathname, { replace: true });
      const t = setTimeout(() => setFlash(""), 3000);
      return () => clearTimeout(t);
    }
  }, [location.state, location.pathname, navigate]);

  // solo las mías + filtros
  const misVisitas = useMemo(() => {
    const text = q.trim().toLowerCase();

    return items
      .filter((it) => isMine(it, user))
      .filter((it) => {
        if (filtro.estado && String(it.estado || "").toUpperCase() !== filtro.estado) return false;
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
      // ordenar por fecha efectiva
      .sort((a, b) => getEffectiveDate(a).localeCompare(getEffectiveDate(b)));
  }, [items, user, q, filtro]);

  // hoy con fecha EFECTIVA
  const hoyYMD = todayLocalYMD();
  const hoyDMY = ymdToDmy(hoyYMD);
  const visitasDeHoy = useMemo(
    () => misVisitas.filter((it) => getEffectiveDate(it).slice(0, 10) === hoyYMD),
    [misVisitas, hoyYMD]
  );

  const goReagendar = (id) => navigate(`/tecnico/reagendar/${id}`);

  // UI: fecha/bloque a mostrar
  const renderFechaInfo = (it) => {
    const effDate = getEffectiveDate(it);     // ya lo tienes
    const effBlock = getEffectiveBlock(it);   // ya lo tienes
    const estado = String(it.estado || "").toUpperCase();
    const base = effDate ? ymdToDmy(effDate) : "—";  // <- aquí el cambio
    const parts = [base];
    if (effBlock) parts.push(effBlock);
    parts.push(estado);
    return parts.join(" · ");
  };


  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        {flash && <div className={styles.success} style={{ marginBottom: 8 }}>{flash}</div>}

        <header className={styles.header}>
          <h1 className={styles.title}>Mis visitas</h1>
          <p className={styles.subtitle}>
            Revisa todas tus asignaciones y las de <strong>hoy</strong>.
          </p>
        </header>

        {/* Filtros */}
        <div className={`${styles.form} ${styles.filtersRow}`}>
          <input
            className={styles.input}
            placeholder="Buscar por dirección, comuna, ID vivienda, RUT…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            disabled={loading}
          />

          <select
            className={styles.select}
            value={filtro.estado}
            onChange={(e) => setFiltro((f) => ({ ...f, estado: e.target.value }))}
            disabled={loading}
          >
            <option value="">Todos los estados</option>
            {ESTADOS.map((s) => (
              <option key={s} value={s}>
                {s}
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

        {error && <div className={styles.error} style={{ marginTop: 8 }}>{error}</div>}
        {loading && <div className={styles.helper} style={{ marginTop: 8 }}>Cargando…</div>}

        {/* Visitas de hoy (por fecha efectiva) */}
        <section style={{ marginTop: 16 }}>
          <h2 className={styles.sectionTitle}>
            Visitas de hoy ({hoyDMY})
          </h2>

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
                  {isReagendado(it) && <span className={`${styles.badge} ${styles.badgeReagendado}`}>Reagendado</span>}
                  <button
                    className={styles.button}
                    onClick={() =>
                      navigate(
                        isCompletada(it)
                          ? `/tecnico/auditoria/ver/${it.id}`     // vista solo lectura (por asignación)
                          : `/tecnico/auditoria/nueva/${it.id}`   // crear auditoría
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

        {/* Todas mis visitas (con fecha/bloque efectivos) */}
        <section style={{ marginTop: 20 }}>
          <h2 className={styles.sectionTitle}>Todas mis visitas</h2>

          <div className={styles.listGrid}>
            {misVisitas.map((it) => (
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
                  {isReagendado(it) && <span className={`${styles.badge} ${styles.badgeReagendado}`}>Reagendado</span>}
                  <button className={styles.button} onClick={() => navigate(`/tecnico/auditoria/nueva/${it.id}`)}>
                    Auditar
                  </button>
                  <button className={styles.button} onClick={() => goReagendar(it.id)}>
                    Reagendar
                  </button>
                </div>
              </div>
            ))}

            {!loading && misVisitas.length === 0 && (
              <div className={styles.helper}>No tienes visitas asignadas.</div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
