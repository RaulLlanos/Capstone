// src/utils/dateFormat.js

// Convierte "YYYY-MM-DD" o "YYYY-MM-DDTHH:mm" → "DD/MM/YYYY"
export function ymdToDmy(s) {
  if (!s) return "—";
  const ymd = String(s).slice(0, 10); // por si viene con hora
  const [y, m, d] = ymd.split("-");
  if (!y || !m || !d) return s;
  return `${d.padStart(2,"0")}/${m.padStart(2,"0")}/${y}`;
}
