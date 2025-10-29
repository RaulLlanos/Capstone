/* eslint-disable no-unused-vars */
// src/pages/Auditor.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import api from "../services/api";
import styles from "./Login.module.css";
import {
  ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
  BarChart, Bar,
  PieChart, Pie, Cell,
  Legend,
} from "recharts";

const COLORS = ["#EF4444", "#F59E0B", "#10B981", "#3B82F6", "#6366F1", "#6B7280", "#A855F7", "#14B8A6"];

function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

function getEffectiveDate(it) {
  const r =
    it.reagendado_fecha ||
    (it.reagendado && (it.reagendado.fecha || it.reagendado.reagendado_fecha)) ||
    it.reagendadoFecha ||
    it.reagendado_date;
  return String(r || it.fecha || "");
}

function isCompletada(it) {
  return String(it.estado || "").toUpperCase() === "VISITADA";
}

function ymdToDmy(s) {
  if (!s) return "—";
  const [y, m, d] = String(s).slice(0, 10).split("-");
  return `${d.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
}

const inc = (map, key, by = 1) => {
  map.set(key, (map.get(key) || 0) + by);
  return map;
};

function lastNDaysYMD(n) {
  const days = [];
  const now = new Date();
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(now.getDate() - i);
    days.push(d.toISOString().slice(0, 10));
  }
  return days;
}

// Helpers de nombres
function buildUserLabel(u) {
  if (!u) return "Técnico";
  return (
    u.first_name?.trim() || u.last_name?.trim()
      ? `${u.first_name ?? ""} ${u.last_name ?? ""}`.trim()
      : (u.email || `Tec#${u.id}`)
  );
}

export default function Auditor() {
  const [items, setItems] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Técnicos
  const [techMap, setTechMap] = useState(new Map()); // id:number -> usuario
  const [techOptions, setTechOptions] = useState([]); // [{id, label}]
  const [selectedTechId, setSelectedTechId] = useState("ALL");

  // Cargar todas las asignaciones
  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        let url = "/api/asignaciones/";
        let acc = [];
        for (;;) {
          const res = await api.get(url);
          const data = res.data || {};
          acc = acc.concat(normalizeList(data));
          if (!data.next) break;
          url = data.next;
        }
        setItems(acc);
        setCount(acc.length);
      } catch (e) {
        console.error(e);
        setError("No se pudieron cargar las asignaciones.");
        setItems([]);
        setCount(0);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // Cargar técnicos (usuarios con rol=tecnico)
  useEffect(() => {
    (async () => {
      try {
        let url = "/api/usuarios/?rol=tecnico";
        const all = [];
        for (;;) {
          const res = await api.get(url);
          const data = res.data || {};
          const list = normalizeList(data);
          all.push(...list);
          if (!data.next) break;
          url = data.next;
        }
        const map = new Map();
        for (const u of all) map.set(u.id, u);
        setTechMap(map);

        const opts = all
          .map((u) => ({ id: u.id, label: buildUserLabel(u) }))
          .sort((a, b) => a.label.localeCompare(b.label));
        setTechOptions(opts);
      } catch (e) {
        console.warn("No se pudieron cargar técnicos:", e);
        setTechMap(new Map());
        setTechOptions([]);
      }
    })();
  }, []);

  // Dado un item, obtener el id del técnico (asignado)
  function getTecnicoIdFromItem(it) {
    // El schema de asignaciones expone "asignado_a" (int, readOnly).
    // Si existiera it.tecnico como obj/num, también lo consideramos.
    if (typeof it.asignado_a === "number") return it.asignado_a;
    if (typeof it.tecnico === "number") return it.tecnico;
    if (it.tecnico && typeof it.tecnico === "object" && typeof it.tecnico.id === "number") return it.tecnico.id;
    return null;
  }

  // Dado un item, obtener el label del técnico
  function getTecnicoLabelFromItem(it) {
    const id = getTecnicoIdFromItem(it);
    if (id && techMap.has(id)) return buildUserLabel(techMap.get(id));
    // fallback: si vino un objeto técnico embedido
    if (it.tecnico && typeof it.tecnico === "object") {
      return it.tecnico.nombre || it.tecnico.full_name || it.tecnico.email || `Tec#${it.tecnico.id ?? "?"}`;
    }
    if (typeof it.tecnico === "string") return it.tecnico;
    if (typeof it.asignado_a === "number") return `Tec#${it.asignado_a}`;
    return "Sin técnico";
  }

  // Items filtrados por técnico seleccionado
  const itemsFiltrados = useMemo(() => {
    if (selectedTechId === "ALL") return items;
    const sel = Number(selectedTechId);
    return items.filter((it) => getTecnicoIdFromItem(it) === sel);
  }, [items, selectedTechId]);

  // --- Cálculos del dashboard (sobre itemsFiltrados) ---
  const {
    porEstado,
    porMarca,
    porTecnologia,
    porZona,
    tasaReagendamiento,
    asignadasVsSinAsignar,
    completadasPorDia14,
    topComunas,
    productividadTecnicos30,
  } = useMemo(() => {
    const byEstado = new Map();
    const byMarca = new Map();
    const byTec = new Map();
    const byZona = new Map();
    const byComuna = new Map();
    const byTecnico30 = new Map();
    let reagendadas = 0, asignadas = 0, sinAsignar = 0;

    const days14 = lastNDaysYMD(14);
    const set14 = new Set(days14);
    const comp14 = new Map();
    days14.forEach((d) => comp14.set(d, 0));

    for (const it of itemsFiltrados) {
      const estado = String(it.estado || "").toUpperCase();
      inc(byEstado, estado);
      inc(byMarca, String(it.marca || "—"));
      inc(byTec, String(it.tecnologia || "—"));
      inc(byZona, String(it.zona || "—"));
      inc(byComuna, String(it.comuna || "—"));

      const hasAssignee = getTecnicoIdFromItem(it) !== null;
      if (hasAssignee) asignadas++; else sinAsignar++;

      const hasReag = it.reagendado_fecha || it.reagendado_bloque;
      if (hasReag) reagendadas++;

      if (isCompletada(it)) {
        const eff = getEffectiveDate(it).slice(0, 10);
        if (set14.has(eff)) comp14.set(eff, (comp14.get(eff) || 0) + 1);

        const label = getTecnicoLabelFromItem(it);
        inc(byTecnico30, label);
      }
    }

    const total = itemsFiltrados.length || 1;
    const tasaReag = Math.round((reagendadas / total) * 100);

    return {
      porEstado: Array.from(byEstado, ([name, value]) => ({ name, value })),
      porMarca: Array.from(byMarca, ([name, value]) => ({ name, value })),
      porTecnologia: Array.from(byTec, ([name, value]) => ({ name, value })),
      porZona: Array.from(byZona, ([name, value]) => ({ name, value })),
      tasaReagendamiento: tasaReag,
      asignadasVsSinAsignar: [
        { name: "Asignadas", value: asignadas },
        { name: "Sin asignar", value: sinAsignar },
      ],
      completadasPorDia14: lastNDaysYMD(14).map((d) => ({ day: ymdToDmy(d), value: comp14.get(d) || 0 })),
      topComunas: Array.from(byComuna, ([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 10),
      productividadTecnicos30: Array.from(byTecnico30, ([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 12),
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itemsFiltrados, techMap]);

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 1200 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Panel Administrador</h1>
          <p className={styles.subtitle}>
            Resumen de asignaciones ({itemsFiltrados.length} de {count} totales)
          </p>
        </header>

        {/* Filtro por técnico */}
        <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
          <label className={styles.helper} style={{ fontWeight: 600 }}>Filtrar por técnico:</label>
          <select
            className={styles.select}
            value={selectedTechId}
            onChange={(e) => setSelectedTechId(e.target.value)}
          >
            <option value="ALL">Todos los técnicos</option>
            {techOptions.map((t) => (
              <option key={t.id} value={t.id}>{t.label}</option>
            ))}
          </select>
        </div>

        {error && <div className={styles.error}>{error}</div>}
        {loading && <div className={styles.helper}>Cargando…</div>}

        {!loading && !error && (
          <>
            {/* KPIs */}
            <section style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
              <KpiCard label="Total asignaciones" value={itemsFiltrados.length} />
              <KpiCard label="Reagendadas (%)" value={`${tasaReagendamiento}%`} />
              <KpiCard label="Asignadas" value={asignadasVsSinAsignar[0]?.value || 0} />
              <KpiCard label="Sin asignar" value={asignadasVsSinAsignar[1]?.value || 0} />
            </section>

            {/* Estado + Completadas */}
            <section style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 12, marginTop: 12 }}>
              <ChartPie title="Distribución por estado" data={porEstado} />
              <ChartLine title="Completadas por día (últimos 14)" data={completadasPorDia14} />
            </section>

            {/* Marca + Tecnología */}
            <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
              <ChartBar title="Por marca" data={porMarca} color="#EF4444" />
              <ChartBar title="Por tecnología" data={porTecnologia} color="#3B82F6" />
            </section>

            {/* Asignación + Zona */}
            <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
              <ChartPie title="Asignación" data={asignadasVsSinAsignar} />
              <ChartBar title="Por zona" data={porZona} color="#6B7280" />
            </section>

            {/* Productividad + Top comunas */}
            <section style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 12, marginTop: 12 }}>
              <ChartBar title="Productividad por técnico (últimos 30 días)" data={productividadTecnicos30} color="#10B981" />
              <div className={styles.card} style={{ padding: 12 }}>
                <h3 className={styles.title} style={{ fontSize: 16, marginBottom: 8 }}>Top 10 comunas</h3>
                {topComunas.map((c, i) => (
                  <div key={c.name} style={{ display: "flex", justifyContent: "space-between", fontSize: 14 }}>
                    <span>{i + 1}. {c.name}</span>
                    <strong>{c.value}</strong>
                  </div>
                ))}
                {topComunas.length === 0 && <div className={styles.helper}>Sin datos.</div>}
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
}

function KpiCard({ label, value }) {
  return (
    <div className={styles.card} style={{ padding: 16 }}>
      <div className={styles.helper} style={{ fontSize: 12 }}>{label}</div>
      <div className={styles.title} style={{ marginTop: 4, fontSize: 22 }}>{value}</div>
    </div>
  );
}

function ChartPie({ title, data }) {
  return (
    <div className={styles.card} style={{ padding: 12 }}>
      <h3 className={styles.title} style={{ fontSize: 16, marginBottom: 8 }}>{title}</h3>
      <div style={{ height: 260 }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" outerRadius={90}>
              {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Legend />
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function ChartLine({ title, data }) {
  return (
    <div className={styles.card} style={{ padding: 12 }}>
      <h3 className={styles.title} style={{ fontSize: 16, marginBottom: 8 }}>{title}</h3>
      <div style={{ height: 260 }}>
        <ResponsiveContainer>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#EF4444" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function ChartBar({ title, data, color }) {
  return (
    <div className={styles.card} style={{ padding: 12 }}>
      <h3 className={styles.title} style={{ fontSize: 16, marginBottom: 8 }}>{title}</h3>
      <div style={{ height: 240 }}>
        <ResponsiveContainer>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="value" fill={color} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
