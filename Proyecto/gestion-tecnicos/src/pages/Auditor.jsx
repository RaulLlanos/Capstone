export default function Auditor() {
  return (
    <div style={{ display: "grid", gap: 16 }}>
      <h2>Panel Auditor</h2>

      <section>
        <h3>Métricas generales</h3>
        <div id="chart-placeholder" style={{ height: 200, border: "1px solid #eee" }}>
          {/* gráficos con Recharts irán aquí */}
          (sin datos)
        </div>
      </section>

      <section>
        <h3>Exportaciones</h3>
        <button>Exportar CSV</button>
      </section>
    </div>
  );
}
