// src/pages/Tecnico.jsx
import { useEffect, useMemo, useState } from "react";
import styles from "./Tecnico.module.css";
import {
  fetchVisitasDeHoy,
  patchEstadoVisita,
  patchReagendarVisita, // usamos la opción simple
} from "../services/visitas";

const ESTADOS = ["programada", "en_curso", "completada", "reagendada", "cancelada"];
const LS_Q = "tecnico:q";
const LS_F_ESTADO = "tecnico:fEstado";
const LS_LAST_VISIT = "tecnico:lastVisitId";

export default function Tecnico() {
  const [visitas, setVisitas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const [q, setQ] = useState(() => localStorage.getItem(LS_Q) ?? "");
  const [fEstado, setFEstado] = useState(() => localStorage.getItem(LS_F_ESTADO) ?? "todos");
  const [lastVisitId, setLastVisitId] = useState(() => localStorage.getItem(LS_LAST_VISIT) ?? "");

  const load = async () => {
    setLoading(true);
    setErr("");
    try {
      const data = await fetchVisitasDeHoy(); // ← ahora usa /api/visitas/
      setVisitas(data);
    } catch (e) {
      console.error(e);
      setErr("No se pudieron cargar tus visitas. Reintenta.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => { localStorage.setItem(LS_Q, q); }, [q]);
  useEffect(() => { localStorage.setItem(LS_F_ESTADO, fEstado); }, [fEstado]);

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
    return [...out].sort((a, b) =>
      String(a.hora_programada || "").localeCompare(String(b.hora_programada || ""))
    );
  }, [visitas, q, fEstado]);

  useEffect(() => {
    if (!lastVisitId) return;
    const t = setTimeout(() => {
      const el = document.querySelector(`[data-row-id="${lastVisitId}"]`);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 80);
    return () => clearTimeout(t);
  }, [lastVisitId, visitas]);

  const EstadoBadge = ({ value }) => {
    const v = String(value || "").toLowerCase();
    const cls =
      v === "programada" ? styles.tagProgramada :
      v === "en_curso"   ? styles.tagEnCurso :
      v === "completada" ? styles.tagCompletada :
      v === "reagendada" ? styles.tagReagendada :
      styles.tagCancelada;
    return <span className={`${styles.tag} ${cls}`}>{v.replace("_", " ")}</span>;
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.headerRow}>
        <h2 className={styles.title}>Visitas de hoy</h2>
      </div>

      <section className={styles.card}>
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

        {err && <div className={styles.error}>{err}</div>}

        <div className={styles.tableWrap}>
          {loading ? (
            <div className={styles.empty}>Cargando…</div>
          ) : filtradas.length === 0 ? (
            <div className={styles.empty}>Sin visitas para hoy</div>
          ) : (
            <table className={styles.table}>
              <thead className={styles.thead}>
                <tr>
                  <th className={styles.th}>Hora</th>
                  <th className={styles.th}>Cliente</th>
                  <th className={styles.th}>Dirección</th>
                  <th className={styles.th}>Estado</th>
                  <th className={styles.th}>Acciones</th>
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
                      <td className={styles.td}>{String(row.hora_programada || "").slice(0, 5)}</td>
                      <td className={styles.td}>{row.cliente_nombre || "-"}</td>
                      <td className={styles.td}>{row.cliente_direccion || "-"}</td>
                      <td className={styles.td}>
                        <EstadoBadge value={row.estado} />
                      </td>
                      <td className={styles.td}>
                        <div className={styles.actions}>
                          <select
                            className={styles.select}
                            value={row.estado}
                            onChange={async (e) => {
                              const nuevo = e.target.value;
                              try {
                                await patchEstadoVisita(row.id_visita, nuevo);
                                const idStr2 = String(row.id_visita);
                                setLastVisitId(idStr2);
                                localStorage.setItem(LS_LAST_VISIT, idStr2);
                                await load();
                              } catch (ex) {
                                console.error(ex);
                                alert("No se pudo actualizar el estado.");
                              }
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
                              try {
                                await patchReagendarVisita(row.id_visita, fechaHoy, hhmm);
                                const idStr2 = String(row.id_visita);
                                setLastVisitId(idStr2);
                                localStorage.setItem(LS_LAST_VISIT, idStr2);
                                await load();
                              } catch (ex) {
                                console.error(ex);
                                alert("No se pudo reagendar la visita.");
                              }
                            }}
                          >
                            Reagendar
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}
