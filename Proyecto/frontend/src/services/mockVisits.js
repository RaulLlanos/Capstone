export const ESTADOS = ["pendiente", "en curso", "completada", "no asistió"];

const hoy = new Date().toISOString().slice(0, 10); // YYYY-MM-DD

// datos mock
let VISITAS = [
  {
    id: "V-1001",
    fecha: hoy,
    hora: "09:00",
    cliente: "Juan Pérez",
    direccion: "Av. Siempre Viva 742",
    region: "RM",
    tecnico: "tecnico@claro.cl",
    estado: "pendiente",
    notas: "",
  },
  {
    id: "V-1002",
    fecha: hoy,
    hora: "10:30",
    cliente: "María López",
    direccion: "Los Olmos 1234",
    region: "V",
    tecnico: "tecnico@claro.cl",
    estado: "en curso",
    notas: "Llamar al llegar",
  },
  {
    id: "V-1003",
    fecha: hoy,
    hora: "12:00",
    cliente: "Carlos Díaz",
    direccion: "Pasaje Azul 55",
    region: "RM",
    tecnico: "tecnico@claro.cl",
    estado: "pendiente",
    notas: "",
  },
];

// simulamos latencia y CRUD básico en memoria
const wait = (ms = 400) => new Promise((r) => setTimeout(r, ms));

export async function getVisitasDeHoy() {
  await wait();
  const today = new Date().toISOString().slice(0, 10);
  return VISITAS.filter(v => v.fecha === today).sort((a,b)=>a.hora.localeCompare(b.hora));
}

export async function cambiarEstado(id, estado) {
  await wait(200);
  VISITAS = VISITAS.map(v => (v.id === id ? { ...v, estado } : v));
  return true;
}

export async function reagendarVisita(id, nuevaFecha, nuevaHora) {
  await wait(300);
  VISITAS = VISITAS.map(v =>
    v.id === id ? { ...v, fecha: nuevaFecha, hora: nuevaHora, estado: "pendiente" } : v
  );
  return true;
}
