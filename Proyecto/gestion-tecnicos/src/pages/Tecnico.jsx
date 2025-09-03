export default function Tecnico() {
  return (
    <div style={{ display: "grid", gap: 16 }}>
      <h2>Panel Técnico</h2>

      <section>
        <h3>Visitas de Hoy</h3>
        <div style={{ border: "1px solid #eee", padding: 12 }}>
          {/* tabla/lista vendrá acá */}
          (sin datos)
        </div>
      </section>

      <section>
        <h3>Acciones rápidas</h3>
        <div style={{ display: "flex", gap: 8 }}>
          <button>Crear visita</button>
          <button>Reagendar</button>
        </div>
      </section>
    </div>
  );
}
