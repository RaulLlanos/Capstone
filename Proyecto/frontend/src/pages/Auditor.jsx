/* eslint-disable no-unused-vars */
// src/pages/Auditor.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import api from "../services/api";
import styles from "./Login.module.css";

// Recharts
import {
  ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
  BarChart, Bar,
  PieChart, Pie, Cell,
  Legend,
} from "recharts";

// Paleta simple (rojos/azules/grises). Recharts auto-asigna si faltan.
const COLORS = ["#EF4444", "#F59E0B", "#10B981", "#3B82F6", "#6366F1", "#6B7280", "#A855F7", "#14B8A6"];

function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

// Fecha efectiva para mostrar/comparar (reagendada si existe)
function getEffectiveDate(it) {
  const r =
    it.reagendado_fecha ||
    (it.reagendado && (it.reagendado.fecha || it.reagendado.reagendado_fecha)) ||
    it.reagendadoFecha ||
    it.reagendado_date;
  return String(r || it.fecha || "");
}

function isCompletada(it) {
  return String(it.estado || "").toUpperCase() === "visitada" || String(it.estado || "").toUpperCase() === "VISITADA";
}

function ymdToDmy(s) {
  if (!s) return "—";
  const ymd = String(s).slice(0, 10);
  const [y, m, d] = ymd.split("-");
  if (!y || !m || !d) return "—";
  return `${d.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
}

// Para agrupar por clave
const inc = (map, key, by = 1) => {
  map.set(key, (map.get(key) || 0) + by);
  return map;
};

// Rango de días YYYY-MM-DD (hoy - (n-1) … hoy)
function lastNDaysYMD(n) {
  const days = [];
  const now = new Date();
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(now.getDate() - i);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    days.push(`${y}-${m}-${day}`);
  }
  return days;
}

export default function Auditor() {
  const [items, setItems] = useState([]);
  const [count, setCount] = useState(0);
  const [next, setNext] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const fetching = useRef(false);

  // Carga con paginación (DRF)
  const loadAll = async () => {
    if (fetching.current) return;
    fetching.current = true;
    setLoading(true);
    setError("");
    try {
      let url = "/api/asignaciones/";
      let acc = [];
      let total = 0;
      for (;;) {
        const res = await api.get(url);
        const data = res.data || {};
        const chunk = normalizeList(data);
        acc = acc.concat(chunk);
        total = data.count ?? acc.length;
        if (!data.next) break;
        url = data.next; // next absoluto
      }
      setItems(acc);
      setCount(total);
      setNext(null);
    } catch (e) {
      console.error(e);
      setError("No se pudieron cargar las asignaciones.");
      setItems([]);
      setCount(0);
    } finally {
      setLoading(false);
      fetching.current = false;
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  // ---- Métricas derivadas ----
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

    let reagendadas = 0;
    let asignadas = 0;
    let sinAsignar = 0;

    // Ventanas de tiempo
    const days14 = lastNDaysYMD(14);
    const days30 = lastNDaysYMD(30);
    const set14 = new Set(days14);
    const set30 = new Set(days30);

    // Inicializa series de completadas 14 días
    const comp14 = new Map();
    days14.forEach((d) => comp14.set(d, 0));

    for (const it of items) {
      const estado = String(it.estado || "").toUpperCase();
      const marca = String(it.marca || "—");
      const tec = String(it.tecnologia || "—");
      const zona = String(it.zona || "—");
      const comuna = String(it.comuna || "—");

      inc(byEstado, estado);
      inc(byMarca, marca);
      inc(byTec, tec);
      inc(byZona, zona);
      inc(byComuna, comuna);

      // asignación (FK tecnico / asignado_a)
      const hasTecnico = it.tecnico != null && it.tecnico !== "";
      if (hasTecnico || it.asignado_a != null) asignadas++;
      else sinAsignar++;

      // reagendamiento presente (cualquier variante)
      const hasReag =
        it.reagendado_fecha ||
        it.reagendado_bloque ||
        (it.reagendado && (it.reagendado.fecha || it.reagendado.bloque || it.reagendado.reagendado_fecha || it.reagendado.reagendado_bloque)) ||
        it.reagendadoFecha ||
        it.reagendadoBloque;
      if (hasReag) reagendadas++;

      // completadas por día (14 días) usando fecha efectiva (o actualizada si tienes un completed_at)
      if (isCompletada(it)) {
        const eff = getEffectiveDate(it).slice(0, 10);
        if (set14.has(eff)) {
          comp14.set(eff, (comp14.get(eff) || 0) + 1);
        }
        // productividad por técnico (30 días)
        const eff30 = getEffectiveDate(it).slice(0, 10);
        if (set30.has(eff30)) {
          // label técnico
          let label = "Sin técnico";
          const t = it.tecnico;
          if (t && typeof t === "object") {
            label = t.nombre || t.full_name || t.display_name || t.email || `Tec#${t.id ?? "?"}`;
          } else if (typeof t === "string") {
            label = t;
          } else if (typeof t === "number") {
            label = `Tec#${t}`;
          }
          inc(byTecnico30, label);
        }
      }
    }

    const total = items.length || 1; // evita /0
    const tasaReag = Math.round((reagendadas / total) * 100);

    const porEstadoArr = Array.from(byEstado.entries()).map(([name, value]) => ({ name, value }));
    const porMarcaArr = Array.from(byMarca.entries()).map(([name, value]) => ({ name, value }));
    const porTecArr = Array.from(byTec.entries()).map(([name, value]) => ({ name, value }));
    const porZonaArr = Array.from(byZona.entries()).map(([name, value]) => ({ name, value }));

    const completadas14Arr = days14.map((d) => ({ day: ymdToDmy(d), value: comp14.get(d) || 0 }));

    const topComunasArr = Array.from(byComuna.entries())
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);

    const prodTec30Arr = Array.from(byTecnico30.entries())
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 12);

    return {
      porEstado: porEstadoArr,
      porMarca: porMarcaArr,
      porTecnologia: porTecArr,
      porZona: porZonaArr,
      tasaReagendamiento: tasaReag,
      asignadasVsSinAsignar: [
        { name: "Asignadas", value: asignadas },
        { name: "Sin asignar", value: sinAsignar },
      ],
      completadasPorDia14: completadas14Arr,
      topComunas: topComunasArr,
      productividadTecnicos30: prodTec30Arr,
    };
  }, [items]);

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 1200 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Panel Administrador</h1>
          <p className={styles.subtitle}>
            Resumen de asignaciones ({count} registros). Datos desde <code>/api/asignaciones/</code>.
          </p>
        </header>

        {error && <div className={styles.error}>{error}</div>}
        {loading && <div className={styles.helper}>Cargando…</div>}

        {!loading && !error && (
          <>
            {/* KPIs rápidos */}
            <section style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
              <KpiCard label="Total asignaciones" value={count} />
              <KpiCard label="Reagendadas (%)" value={`${tasaReagendamiento}%`} />
              <KpiCard
                label="Asignadas"
                value={(asignadasVsSinAsignar.find(x => x.name === "Asignadas")?.value || 0)}
              />
              <KpiCard
                label="Sin asignar"
                value={(asignadasVsSinAsignar.find(x => x.name === "Sin asignar")?.value || 0)}
              />
            </section>

            {/* Fila 1: Estado (pie) + Completadas 14 días (línea) */}
            <section style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 12, marginTop: 12 }}>
              <div className={styles.card} style={{ padding: 12 }}>
                <h3 className={styles.title} style={{ fontSize: 16, marginBottom: 8 }}>Distribución por estado</h3>
                <div style={{ height: 260 }}>
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie data={porEstado} dataKey="value" nameKey="name" outerRadius={90}>
                        {porEstado.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Legend />
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className={styles.card} style={{ padding: 12 }}>
                <h3 className={styles.title} style={{ fontSize: 16, marginBottom: 8 }}>
                  Completadas por día (últimos 14)
                </h3>
                <div style={{ height: 260 }}>
                  <ResponsiveContainer>
                    <LineChart data={completadasPorDia14}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="day" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Line type="monotone" dataKey="value" stroke="#EF4444" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </section>

            {/* Fila 2: Marca y Tecnología (barras) */}
            <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
              <div className={styles.card} style={{ padding: 12 }}>
                <h3 className={styles.title} style={{ fontSize: 16, marginBottom: 8 }}>Por marca</h3>
                <div style={{ height: 240 }}>
                  <ResponsiveContainer>
                    <BarChart data={porMarca}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#EF4444" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className={styles.card} style={{ padding: 12 }}>
                <h3 className={styles.title} style={{ fontSize: 16, marginBottom: 8 }}>Por tecnología</h3>
                <div style={{ height: 240 }}>
                  <ResponsiveContainer>
                    <BarChart data={porTecnologia}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#3B82F6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </section>

            {/* Fila 3: Asignadas vs sin asignar (pie) + Zonas (barras) */}
            <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
              <div className={styles.card} style={{ padding: 12 }}>
                <h3 className={styles.title} style={{ fontSize: 16, marginBottom: 8 }}>Asignación</h3>
                <div style={{ height: 240 }}>
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie data={asignadasVsSinAsignar} dataKey="value" nameKey="name" outerRadius={90}>
                        {asignadasVsSinAsignar.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Legend />
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className={styles.card} style={{ padding: 12 }}>
                <h3 className={styles.title} style={{ fontSize: 16, marginBottom: 8 }}>Por zona</h3>
                <div style={{ height: 240 }}>
                  <ResponsiveContainer>
                    <BarChart data={porZona}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#6B7280" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </section>

            {/* Fila 4: Productividad por técnico (30 días) + Top comunas */}
            <section style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 12, marginTop: 12 }}>
              <div className={styles.card} style={{ padding: 12 }}>
                <h3 className={styles.title} style={{ fontSize: 16, marginBottom: 8 }}>
                  Productividad por técnico (últimos 30 días)
                </h3>
                <div style={{ height: 280 }}>
                  <ResponsiveContainer>
                    <BarChart data={productividadTecnicos30}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" interval={0} angle={-20} textAnchor="end" height={70} />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#10B981" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className={styles.card} style={{ padding: 12 }}>
                <h3 className={styles.title} style={{ fontSize: 16, marginBottom: 8 }}>Top 10 comunas</h3>
                <div style={{ display: "grid", gap: 6 }}>
                  {topComunas.map((c, i) => (
                    <div key={c.name} style={{ display: "flex", justifyContent: "space-between", fontSize: 14 }}>
                      <span>{i + 1}. {c.name}</span>
                      <strong>{c.value}</strong>
                    </div>
                  ))}
                  {topComunas.length === 0 && <div className={styles.helper}>Sin datos.</div>}
                </div>
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
}

// Componente simple para KPIs
function KpiCard({ label, value }) {
  return (
    <div className={styles.card} style={{ padding: 16 }}>
      <div className={styles.helper} style={{ fontSize: 12 }}>{label}</div>
      <div className={styles.title} style={{ marginTop: 4, fontSize: 22 }}>{value}</div>
    </div>
  );
}
