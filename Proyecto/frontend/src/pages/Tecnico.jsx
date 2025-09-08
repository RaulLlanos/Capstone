// src/pages/Tecnico.jsx
import { useEffect, useMemo, useState } from "react";
import styles from "./Tecnico.module.css";
import Table from "../components/Table";

// Usa tus services reales si ya conectaste backend:
import {
  fetchVisitasDeHoyMias,
  patchEstadoVisita,
  postReagendarVisita,
} from "../services/visitas";

// Estados válidos del backend
const ESTADOS = ["programada", "en_curso", "completada", "cancelada"];

// Claves para localStorage (memoria de filtros/última visita)
const LS_Q = "tecnico:q";
const LS_F_ESTADO = "tecnico:fEstado";
const LS_LAST_VISIT = "tecnico:lastVisitId";

export default function Tecnico() {
  const [visitas, setVisitas] = useState([]);
  const [loading, setLoading] = useState(true);

  const [q, setQ] = useState(() => localStorage.getItem(LS_Q) ?? "");
  const [fEstado, setFEstado] = useState(
    () => localStorage.getItem(LS_F_ESTADO) ?? "todos"
  );
  const [lastVisitId, setLastVisitId] = useState(
    () => localStorage.getItem(LS_LAST_VISIT) ?? ""
  );

  // Cargar visitas de HOY (del técnico logueado)
  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchVisitasDeHoyMias();
      setVisitas(data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  // Persistir filtros en localStorage
  useEffect(() => { localStorage.setItem(LS_Q, q); }, [q]);
  useEffect(() => { localStorage.setItem(LS_F_ESTADO, fEstado); }, [fEstado]);

  // Filtrado en memoria (campos reales del backend)
  const filtradas = useMemo(() => {
    let out = visitas;
    if (fEstado !== "todos") out = out.filter((v) => v.estado === fEstado);
    if (q.trim()) {
      const x = q.trim().toLowerCase();
      out = out.filter(
        (v) =>
          (v.cliente_nombre || "").toLowerCase().includes(x) ||
          (v.cliente_direccion || "").toLowerCase().includes(x)
      );
    }
    // ordenar por hora_programada (string HH:MM:SS o HH:MM)
    out = [...out].sort((a, b) =>
      String(a.hora_programada).localeCompare(String(b.hora_programada))
    );
    return out;
  }, [visitas, q, fEstado]);

  // Scroll a la última visita seleccionada
  useEffect(() => {
    if (!lastVisitId) return;
    const t = setTimeout(() => {
      const el = document.querySelector(`[data-row-id="${lastVisitId}"]`);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 50);
    return () => clearTimeout(t);
  }, [lastVisitId, visitas]);

  // Badge de estado
  const EstadoBadge = ({ value }) => {
    const v = String(value || "").toLowerCase();
    const base = styles.tag;
    const cls =
      v === "programada" ? styles.tagProgramada :
      v === "en_curso"   ? styles.tagEnCurso :
      v === "completada" ? styles.tagCompletada :
      styles.tagCancelada;
    return <span className={`${base} ${cls}`}>{v.replace("_", " ")}</span>;
  };

  const columns = [
    {
      key: "hora",
      title: "Hora",
      dataIndex: "hora_programada",
      render: (v) => String(v).slice(0, 5),
    },
    { key: "cliente", title: "Cliente", dataIndex: "cliente_nombre" },
    { key: "direccion", title: "Dirección", dataIndex: "cliente_direccion" },
    {
      key: "estado",
      title: "Estado",
      dataIndex: "estado",
      render: (val) => <EstadoBadge value={val} />,
    },
    {
      key: "acciones",
      title: "Acciones",
      dataIndex: "id_visita",
      render: (_val, row) => (
        <div className={styles.actions}>
          <select
            className={styles.select}
            value={row.estado}
            onChange={async (e) => {
              const nuevo = e.target.value;
              await patchEstadoVisita(row.id_visita, nuevo);
              const idStr = String(row.id_visita);
              setLastVisitId(idStr);
              localStorage.setItem(LS_LAST_VISIT, idStr);
              await load();
            }}
          >
            {ESTADOS.map((es) => (
              <option key={es} value={es}>{es}</option>
            ))}
          </select>

          <button
            className={styles.btn}
            onClick={async () => {
              const hhmm = prompt(
                "Nueva hora (HH:mm):",
                String(row.hora_programada || "").slice(0, 5) || "09:00"
              );
              if (!hhmm) return;
              const fechaHoy = new Date().toISOString().slice(0, 10);
              await postReagendarVisita(row.id_visita, fechaHoy, hhmm);
              const idStr = String(row.id_visita);
              setLastVisitId(idStr);
              localStorage.setItem(LS_LAST_VISIT, idStr);
              await load();
            }}
          >
            Reagendar
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className={styles.wrapper}>
      <div className={styles.headerRow}>
        <h2 className={styles.title}>Panel Técnico</h2>
      </div>

      <section className={styles.card}>
        <h3 className={styles.sectionTitle}>Visitas de Hoy</h3>

        <div className={styles.toolbar}>
          <input
            className={styles.input}
            placeholder="Buscar cliente o dirección…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select
            className={styles.select}
            value={fEstado}
            onChange={(e) => setFEstado(e.target.value)}
          >
            <option value="todos">Todos</option>
            {ESTADOS.map((e) => (
              <option key={e} value={e}>{e}</option>
            ))}
          </select>

          <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={load}>
            Refrescar
          </button>
          <button
            className={styles.btn}
            onClick={() => {
              localStorage.removeItem(LS_Q);
              localStorage.removeItem(LS_F_ESTADO);
              localStorage.removeItem(LS_LAST_VISIT);
              setQ("");
              setFEstado("todos");
              setLastVisitId("");
            }}
          >
            Limpiar memoria
          </button>
        </div>

        <div className={styles.tableWrap}>
          {loading ? (
            <div className={styles.empty}>Cargando…</div>
          ) : filtradas.length === 0 ? (
            <div className={styles.empty}>Sin visitas para hoy</div>
          ) : (
            <table className={styles.table}>
              <thead className={styles.thead}>
                <tr>
                  {columns.map((c) => (
                    <th key={c.key} className={styles.th}>{c.title}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtradas.map((row) => {
                  const idStr = String(row.id_visita);
                  return (
                    <tr
                      key={idStr}
                      data-row-id={idStr}
                      className={idStr === String(lastVisitId) ? styles.rowHighlight : undefined}
                    >
                      {columns.map((c) => {
                        const val = row[c.dataIndex];
                        return (
                          <td key={c.key} className={styles.td}>
                            {c.render ? c.render(val, row) : val}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </section>

      <section className={styles.card}>
        <h3 className={styles.sectionTitle}>Acciones rápidas</h3>
        <div className={styles.quickRow}>
          <button className={styles.btn}>Crear visita</button>
          <button className={styles.btn}>Reagendar</button>
        </div>
      </section>
    </div>
  );
}
