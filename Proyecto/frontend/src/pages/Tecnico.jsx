/* eslint-disable no-unused-vars */
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

// yyyy-mm-dd local (sin timezone)
function todayLocalYMD() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

// DD/MM/YYYY (seguro con timezone)
function ymdToDmy(s) {
  if (!s) return "—";
  const ymd = String(s).slice(0, 10);
  const [y, m, d] = ymd.split("-");
  if (!y || !m || !d) return "—";
  return `${d.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
}

// === FECHA/BLOQUE EFECTIVOS (usa SIEMPRE esto) ===
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
  const hasReagendado = isReagendado(it);
  if (!hasReagendado) return false;
  // si la fecha efectiva ES hoy, no mostramos badge
  return eff !== todayLocalYMD();
}
const isCompletada = (it) => String(it.estado || "").toUpperCase() === "VISITADA";

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
    estado: "",
    tecnologia: "",
    marca: "",
    zona: "",
  });

  const fetchId = useRef(0);
  const hoyYMD = todayLocalYMD();
  const hoyDMY = ymdToDmy(hoyYMD);

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

  // Hidratar detalles si el listado indica reagendado pero no trae reagendado_* (evita perder "hoy" tras F5)
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
      } catch (_) {
        // silencioso
      }
    })();

    return () => {
      cancelled = true;
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
      .filter((it) => !isCompletada(it)) 
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
      // ordenar por fecha EFECTIVA
      .sort((a, b) => getEffectiveDate(a).localeCompare(getEffectiveDate(b)));
  }, [items, user, q, filtro]);

  // hoy con fecha EFECTIVA
  const visitasDeHoy = useMemo(
    () => misVisitas.filter((it) => getEffectiveDate(it).slice(0, 10) === hoyYMD),
    [misVisitas, hoyYMD]
  );

  // todas excepto las de HOY (para que "se muevan" visualmente)
  const todasExceptoHoy = useMemo(
    () => misVisitas.filter((it) => getEffectiveDate(it).slice(0, 10) !== hoyYMD),
    [misVisitas, hoyYMD]
  );

  // Ir a reagendamiento
  const goReagendar = (id) => navigate(`/tecnico/reagendar/${id}`);

  // UI: fecha/bloque a mostrar
  const renderFechaInfo = (it) => {
    const effDate = getEffectiveDate(it);
    const effBlock = getEffectiveBlock(it);
    const parts = [effDate ? ymdToDmy(effDate) : "—"];
    if (effBlock) parts.push(effBlock);
    return parts.join(" · ");
  };

  // Botón: Para hoy (reagenda a hoy con bloque por defecto; ajusta si quieres preguntar el bloque)
  const setParaHoy = async (item, bloque = "10-13") => {
    try {
      await api.get("/auth/csrf").catch(() => {});
      await api.post(`/api/asignaciones/${item.id}/reagendar/`, {
        fecha: hoyYMD,
        bloque,
      });

      // Optimista: reflejar en memoria la nueva fecha efectiva (sin marcar badge)
      setItems((prev) =>
        prev.map((it) =>
          it.id === item.id
            ? {
                ...it,
                estado: "REAGENDADA", 
                reagendado_fecha: hoyYMD,
                reagendado_bloque: bloque,
              }
            : it
        )
      );
      setFlash("Asignación movida a HOY.");
    } catch (err) {
      console.error("Reagendar a hoy falló:", err?.response?.status, err?.response?.data);
      const data = err?.response?.data || {};
      const msg =
        data.detail ||
        data.error ||
        "No se pudo mover a hoy. (El backend requiere fecha y bloque válidos).";
      setError(msg);
    }
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
                  {/* NO badge si es para HOY */}
                  <button
                    className={styles.button}
                    onClick={() =>
                      navigate(
                        isCompletada(it)
                          ? `/tecnico/auditoria/ver/${it.id}`     // vista solo lectura
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

        {/* Todas mis visitas (ocultando las de HOY) */}
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
