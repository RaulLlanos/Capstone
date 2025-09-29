// src/pages/Tecnico.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

const ESTADOS = ["PENDIENTE", "ASIGNADA", "COMPLETADA", "CANCELADA"];
const TECNOLOGIAS = ["HFC", "NFTT", "FTTH"];
const MARCAS = ["CLARO", "VTR"];
const ZONAS = ["NORTE", "CENTRO", "SUR"];

// normaliza respuesta: lista directa o paginada
function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

// yyyy-mm-dd en hora local (Santiago)
function todayLocalYMD() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

// detecta si la asignación pertenece al usuario autenticado
function isMine(item, user) {
  if (!user) return false;

  const myId = user.id ?? null;
  const myEmail = user.email ?? null;

  // campo "tecnico" puede venir como id, string o objeto {id,email,...}
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

  // algunos backends exponen "asignado_a" como id del usuario
  let asignadoId = null;
  const a = item.asignado_a;
  if (typeof a === "number") asignadoId = a;
  else if (typeof a === "string" && a.trim() !== "") {
    const n = Number(a);
    if (!Number.isNaN(n)) asignadoId = n;
  }

  const emailMatch =
    myEmail &&
    (tecnicoEmail && tecnicoEmail === String(myEmail).toLowerCase());

  const idMatch =
    (myId != null && (tecnicoId === myId || asignadoId === myId));

  return Boolean(emailMatch || idMatch);
}

export default function Tecnico() {
  const { user } = useAuth();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [q, setQ] = useState("");
  const [filtro, setFiltro] = useState({
    estado: "", // todas por defecto
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

  // Filtro base: solo las mías (asignadas a mí)
  const misVisitas = useMemo(() => {
    const text = q.trim().toLowerCase();

    return items
      .filter((it) => isMine(it, user))
      .filter((it) => {
        // filtros adicionales
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
      .sort((a, b) => String(a.fecha).localeCompare(String(b.fecha)));
  }, [items, user, q, filtro]);

  // Solo las de hoy (en Santiago)
  const hoyYMD = todayLocalYMD();
  const visitasDeHoy = useMemo(
    () => misVisitas.filter((it) => String(it.fecha).slice(0, 10) === hoyYMD),
    [misVisitas, hoyYMD]
  );

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 1024 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Mis visitas</h1>
          <p className={styles.subtitle}>
            Revisa todas tus asignaciones y las de <strong>hoy</strong>.
          </p>
        </header>

        {/* Barra de filtros / búsqueda */}
        <div className={styles.form} style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr", gap: 8 }}>
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

        {/* Sección: Visitas de hoy */}
        <section style={{ marginTop: 16 }}>
          <h2 className={styles.title} style={{ fontSize: 18, marginBottom: 8 }}>
            Visitas de hoy ({hoyYMD})
          </h2>

          <div style={{ display: "grid", gap: 10 }}>
            {visitasDeHoy.map((it) => (
              <div
                key={`hoy-${it.id}`}
                style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 12, display: "grid", gap: 6 }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
                  <strong>{it.direccion}</strong>
                  <small className={styles.helper}>
                    {String(it.fecha).slice(0, 10)} · {String(it.estado || "").toUpperCase()}
                  </small>
                </div>
                <div className={styles.helper}>
                  Comuna: {it.comuna} — Zona: {it.zona} — Marca: {it.marca} — Tec.: {it.tecnologia}
                </div>
                <div className={styles.helper}>
                  RUT cliente: {it.rut_cliente} · ID vivienda: {it.id_vivienda} · Encuesta: {it.encuesta}
                </div>
              </div>
            ))}

            {!loading && visitasDeHoy.length === 0 && (
              <div className={styles.helper}>No tienes visitas programadas para hoy.</div>
            )}
          </div>
        </section>

        {/* Sección: Todas mis visitas */}
        <section style={{ marginTop: 20 }}>
          <h2 className={styles.title} style={{ fontSize: 18, marginBottom: 8 }}>Todas mis visitas</h2>

          <div style={{ display: "grid", gap: 10 }}>
            {misVisitas.map((it) => (
              <div
                key={`todas-${it.id}`}
                style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 12, display: "grid", gap: 6 }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
                  <strong>{it.direccion}</strong>
                  <small className={styles.helper}>
                    {String(it.fecha).slice(0, 10)} · {String(it.estado || "").toUpperCase()}
                  </small>
                </div>
                <div className={styles.helper}>
                  Comuna: {it.comuna} — Zona: {it.zona} — Marca: {it.marca} — Tec.: {it.tecnologia}
                </div>
                <div className={styles.helper}>
                  RUT cliente: {it.rut_cliente} · ID vivienda: {it.id_vivienda} · Encuesta: {it.encuesta}
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
