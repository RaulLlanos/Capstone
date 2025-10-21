// src/pages/Tecnico.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Tecnico.module.css";

const TECNOLOGIAS = ["HFC", "NFTT", "FTTH"];
const MARCAS = ["CLARO", "VTR"];
const ZONAS = ["NORTE", "CENTRO", "SUR"];

// ------------------------ Utils ------------------------
function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

// YYYY-MM-DD local
function todayLocalYMD() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

// DD/MM/YYYY
function ymdToDmy(s) {
  if (!s) return "—";
  const ymd = String(s).slice(0, 10);
  const [y, m, d] = ymd.split("-");
  if (!y || !m || !d) return "—";
  return `${d.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
}

// fecha/bloque efectivos (prioriza reagendado_*)
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

const isCompletada = (it) => String(it.estado || "").toUpperCase() === "VISITADA";

function showReagendadoBadge(it) {
  const eff = getEffectiveDate(it).slice(0, 10);
  const estado = String(it.estado || "").toUpperCase();
  return estado === "REAGENDADA" && eff !== todayLocalYMD();
}

// ------------------------ Page ------------------------
export default function Tecnico() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [flash, setFlash] = useState("");

  const [q, setQ] = useState("");
  const [filtro, setFiltro] = useState({ tecnologia: "", marca: "", zona: "" });

  const [meId, setMeId] = useState(user?.id ?? null);

  const fetchId = useRef(0);
  const hoyYMD = todayLocalYMD();
  const hoyDMY = ymdToDmy(hoyYMD);

  // Asegurar meId desde /api/usuarios/me/ si no viene en el contexto
  useEffect(() => {
    if (user?.id) {
      setMeId(user.id);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const r = await api.get("/api/usuarios/me/");
        if (!cancelled) setMeId(r.data?.id ?? null);
      } catch {
        // si falla, meId queda null
      }
    })();
    return () => { cancelled = true; };
  }, [user]);

  // ---------- Carga con fallback ----------
  const load = async () => {
    setLoading(true);
    setError("");
    const myFetch = ++fetchId.current;
    try {
      if (!meId) return; // esperar meId

      let list = [];
      let ok = false;
      // Intento 1: con asignado_a
      try {
        const r1 = await api.get("/api/asignaciones/", { params: { asignado_a: meId } });
        if (myFetch !== fetchId.current) return;
        list = normalizeList(r1.data);
        ok = true;
      } catch (err1) {
        const status = err1?.response?.status;
        // Si el backend no acepta el filtro (400/404), hacemos fallback sin filtro
        if (status !== 400 && status !== 404) {
          throw err1; // otros errores (500, 401, etc.) sí deben mostrar error
        }
      }

      if (!ok) {
        // Intento 2: sin filtro y filtramos en cliente
        const r2 = await api.get("/api/asignaciones/");
        if (myFetch !== fetchId.current) return;
        list = normalizeList(r2.data).filter((it) => it.asignado_a === meId);
      } else {
        // Incluso si el back lo aceptó, filtramos de nuevo por seguridad
        list = list.filter((it) => it.asignado_a === meId);
      }

      setItems(list);
    } catch (err) {
      console.error("Cargar asignaciones falló:", err?.response?.status, err?.response?.data);
      const data = err?.response?.data || {};
      setError(
        (typeof data === "string" ? data : data.detail || data.error) ||
        "No se pudo cargar la lista de visitas."
      );
      setItems([]);
    } finally {
      if (myFetch === fetchId.current) setLoading(false);
    }
  };

  useEffect(() => {
    if (meId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meId]);

  // Hidratar reagendadas que no traen reagendado_*
  useEffect(() => {
    const needDetail = (items || [])
      .filter((it) => String(it.estado || "").toUpperCase() === "REAGENDADA")
      .filter((it) => {
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
      } catch {
        /* silent */
      }
    })();
    return () => { cancelled = true; };
  }, [items]);

  // Flash desde navigate(..., {state})
  useEffect(() => {
    const msg = location.state?.flash;
    if (msg) {
      setFlash(msg);
      navigate(location.pathname, { replace: true });
      const t = setTimeout(() => setFlash(""), 3000);
      return () => clearTimeout(t);
    }
  }, [location.state, location.pathname, navigate]);

  // ---------- Filtrado en memoria ----------
  const misVisitas = useMemo(() => {
    const text = q.trim().toLowerCase();
    return (items || [])
      .filter((it) => (meId ? it.asignado_a === meId : true))
      .filter((it) => !isCompletada(it))
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
  }, [items, q, filtro, meId]);

  const visitasDeHoy = useMemo(
    () => misVisitas.filter((it) => getEffectiveDate(it).slice(0, 10) === hoyYMD),
    [misVisitas, hoyYMD]
  );

  const todasExceptoHoy = useMemo(
    () => misVisitas.filter((it) => getEffectiveDate(it).slice(0, 10) !== hoyYMD),
    [misVisitas, hoyYMD]
  );

  // ---------- Navegación ----------
  const goReagendar = (id) => navigate(`/tecnico/reagendar/${id}`);

  // Fecha/bloque a mostrar
  const renderFechaInfo = (it) => {
    const effDate = getEffectiveDate(it);
    const effBlock = getEffectiveBlock(it);
    const parts = [effDate ? ymdToDmy(effDate) : "—"];
    if (effBlock) parts.push(effBlock);
    return parts.join(" · ");
  };

  // ---------- Acción: Para hoy (mantengo tu versión) ----------
  const setParaHoy = async (item, bloque = "10-13") => {
    try {
      await api.get("/auth/csrf").catch(() => {});

      await api.post(`/api/asignaciones/${item.id}/estado_cliente/`, {
        estado_cliente: "reagendo",
        reagendado_fecha: hoyYMD,
        reagendado_bloque: bloque,
      });

      try {
        await api.patch(`/api/asignaciones/${item.id}/`, { estado: "ASIGNADA" });
      } catch {
        /* ignora si el rol no puede */
      }

      setItems((prev) =>
        prev.map((it) =>
          it.id === item.id
            ? {
                ...it,
                estado: "ASIGNADA",
                reagendado_fecha: hoyYMD,
                reagendado_bloque: bloque,
              }
            : it
        )
      );
      setFlash("Asignación movida a HOY.");
    } catch (err) {
      console.error("Mover a hoy falló:", err?.response?.status, err?.response?.data);
      const data = err?.response?.data || {};
      setError(data.detail || data.error || "No se pudo mover a hoy.");
    }
  };

  // ------------------------ UI ------------------------
  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        {flash && <div className={styles.success} style={{ marginBottom: 8 }}>{flash}</div>}

        <header className={styles.header}>
          <h1 className={styles.title}>Mis visitas</h1>
          <p className={styles.subtitle}>Revisa todas tus asignaciones y las de <strong>hoy</strong>.</p>
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

        {error && <div className={styles.error} style={{ marginTop: 8 }}>{error}</div>}
        {loading && <div className={styles.helper} style={{ marginTop: 8 }}>Cargando…</div>}

        {/* Visitas de hoy */}
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

        {/* Todas mis visitas (excepto hoy) */}
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
