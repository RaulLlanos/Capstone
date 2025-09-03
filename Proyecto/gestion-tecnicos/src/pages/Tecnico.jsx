import { useEffect, useMemo, useState } from "react";
import Table from "../components/Table";
import {
  ESTADOS,
  getVisitasDeHoy,
  cambiarEstado,
  reagendarVisita,
} from "../services/mockVisits";

// Claves para localStorage
const LS_Q = "tecnico:q";
const LS_F_ESTADO = "tecnico:fEstado";
const LS_LAST_VISIT = "tecnico:lastVisitId";

export default function Tecnico() {
  const [visitas, setVisitas] = useState([]);
  const [loading, setLoading] = useState(true);

  // Estados con valor inicial desde localStorage
  const [q, setQ] = useState(() => localStorage.getItem(LS_Q) ?? "");
  const [fEstado, setFEstado] = useState(() => localStorage.getItem(LS_F_ESTADO) ?? "todos");
  const [lastVisitId, setLastVisitId] = useState(
    () => localStorage.getItem(LS_LAST_VISIT) ?? ""
  );

  // Carga inicial de visitas
  useEffect(() => {
    (async () => {
      setLoading(true);
      const data = await getVisitasDeHoy();
      setVisitas(data);
      setLoading(false);
    })();
  }, []);

  // Persistir filtros en localStorage
  useEffect(() => {
    localStorage.setItem(LS_Q, q);
  }, [q]);

  useEffect(() => {
    localStorage.setItem(LS_F_ESTADO, fEstado);
  }, [fEstado]);

  // Filtrado en memoria
  const filtradas = useMemo(() => {
    let out = visitas;
    if (fEstado !== "todos") out = out.filter((v) => v.estado === fEstado);
    if (q.trim()) {
      const x = q.trim().toLowerCase();
      out = out.filter(
        (v) =>
          v.cliente.toLowerCase().includes(x) ||
          v.direccion.toLowerCase().includes(x)
      );
    }
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

  const columns = [
    { key: "hora", title: "Hora", dataIndex: "hora" },
    { key: "cliente", title: "Cliente", dataIndex: "cliente" },
    { key: "direccion", title: "Dirección", dataIndex: "direccion" },
    {
      key: "estado",
      title: "Estado",
      dataIndex: "estado",
      render: (val) => <span style={{ textTransform: "capitalize" }}>{val}</span>,
    },
    {
      key: "acciones",
      title: "Acciones",
      dataIndex: "id",
      render: (_val, row) => (
        <div style={{ display: "flex", gap: 8 }}>
          <select
            value={row.estado}
            onChange={async (e) => {
              const nuevo = e.target.value;
              await cambiarEstado(row.id, nuevo);
              setLastVisitId(row.id);
              localStorage.setItem(LS_LAST_VISIT, row.id);
              const fresh = await getVisitasDeHoy();
              setVisitas(fresh);
            }}
          >
            {ESTADOS.map((es) => (
              <option key={es} value={es}>
                {es}
              </option>
            ))}
          </select>

          <button
            onClick={async () => {
              const nuevaHora = prompt("Nueva hora (HH:mm):", row.hora);
              if (!nuevaHora) return;
              const hoy = new Date().toISOString().slice(0, 10);
              await reagendarVisita(row.id, hoy, nuevaHora);
              setLastVisitId(row.id);
              localStorage.setItem(LS_LAST_VISIT, row.id);
              const fresh = await getVisitasDeHoy();
              setVisitas(fresh);
            }}
          >
            Reagendar
          </button>
        </div>
      ),
    },
  ];

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <h2>Panel Técnico</h2>

      <section>
        <h3>Visitas de Hoy</h3>

        <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
          <input
            placeholder="Buscar cliente o dirección…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />

          <select value={fEstado} onChange={(e) => setFEstado(e.target.value)}>
            <option value="todos">Todos</option>
            {ESTADOS.map((e) => (
              <option key={e} value={e}>
                {e}
              </option>
            ))}
          </select>

          <button
            onClick={async () => {
              setLoading(true);
              const fresh = await getVisitasDeHoy();
              setVisitas(fresh);
              setLoading(false);
            }}
          >
            Refrescar
          </button>

          <button
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

        {loading ? (
          <div>Cargando…</div>
        ) : (
          <Table
            columns={columns}
            data={filtradas}
            emptyText="Sin visitas para hoy"
            getRowProps={(row) => ({
              "data-row-id": row.id,
              style: {
                background:
                  row.id === lastVisitId ? "rgba(255, 215, 0, 0.18)" : "transparent",
                transition: "background 0.2s ease",
              },
            })}
          />
        )}
      </section>

      <section>
        <h3>Acciones rápidas</h3>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => alert("Crear visita (pendiente de implementar)")}>
            Crear visita
          </button>
          <button onClick={() => alert("Reagendar (selecciona desde la tabla)")}>
            Reagendar
          </button>
        </div>
      </section>
    </div>
  );
}
