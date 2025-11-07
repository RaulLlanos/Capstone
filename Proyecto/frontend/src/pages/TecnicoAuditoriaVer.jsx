// src/pages/TecnicoAuditoriaVer.jsx
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";
import styles from "./Login.module.css";

// ---------- MAPEOS ----------
const YES_NO_NA = {
  "1": "Sí",
  "2": "No",
  "3": "No Aplica",
};

const SLOT_MAP = {
  "10-13": "10:00 a 13:00",
  "14-18": "14:00 a 18:00",
};

const CUSTOMER_STATUS_MAP = {
  AUTORIZA: "Autoriza a ingresar",
  SIN_MORADORES: "Sin Moradores",
  RECHAZA: "Rechaza",
  CONTINGENCIA: "Contingencia externa",
  MASIVO: "Incidencia Masivo ClaroVTR",
  REAGENDA: "Reagendó",
};

const ORDER_TYPE_MAP = {
  tecnica: "Técnica",
  comercial: "Comercial",
};

const INFO_TYPE_MAP = {
  mala_practica: "Mala Práctica",
  problema_general: "Problema General",
};

const RESOLUTION_MAP = {
  terreno: "Se solucionó en terreno",
  orden: "Se realizó una gestión con Orden",
};

// Aplica a varios campos 1/2/3
const ENUM_123_FIELDS = [
  "ont_modem_ok",
  "schedule_informed_datetime",
  "schedule_informed_adult_required",
  "schedule_informed_services",
  "arrival_within_slot",
  "identification_shown",
  "explained_before_start",
  "asked_equipment_location",
  "tidy_and_safe_install",
  "tidy_cabling",
  "verified_signal_levels",
  "configured_router",
  "tested_device",
  "tv_functioning",
  "left_instructions",
  "reviewed_with_client",
  "got_consent_signature",
  "left_contact_info",
];

function asText(value, dict) {
  if (value === undefined || value === null || value === "") return "—";
  const key = String(value);
  return dict && dict[key] !== undefined ? dict[key] : String(value);
}

function ymdToDmy(s) {
  if (!s) return "—";
  const ymd = String(s).slice(0, 10);
  const [y, m, d] = ymd.split("-");
  if (!y || !m || !d) return "—";
  return `${d.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
}

// ---------- Carga auditoría por asignación ----------
async function findAuditByAsignacion(asignacionId) {
  try {
    const res = await api.get("/api/auditorias/", {
      params: { asignacion: asignacionId },
    });
    const data = res.data;
    const list = Array.isArray(data?.results)
      ? data.results
      : Array.isArray(data)
      ? data
      : [];
    const exact = list.find((a) => Number(a.asignacion) === Number(asignacionId));
    return exact || list[0] || null;
  } catch {
    return null;
  }
}

export default function TecnicoAuditoriaVer() {
  const { id } = useParams(); // id de asignación
  const navigate = useNavigate();

  const [detalleAsignacion, setDetalleAsignacion] = useState(null);
  const [auditoria, setAuditoria] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        const resAsign = await api.get(`/api/asignaciones/${id}/`);
        setDetalleAsignacion(resAsign.data || null);

        const audit = await findAuditByAsignacion(id);
        setAuditoria(audit);
        if (!audit) setError("No se encontró la auditoría para esta asignación.");
      } catch (err) {
        console.error("GET ver auditoría:", err?.response?.status, err?.response?.data);
        setError("No se pudo cargar la auditoría.");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const Row = ({ label, children }) => (
    <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: 8 }}>
      <div className={styles.helper} style={{ fontWeight: 600 }}>{label}</div>
      <div className={styles.helper}>{children ?? "—"}</div>
    </div>
  );

  // Helpers de impresión
  const enum123 = (val) => asText(val, YES_NO_NA);

  // ⚠️ Campos “texto directo” con mapeos específicos (usando nombres REALES de backend):
  const customerStatusText = asText(auditoria?.customer_status, CUSTOMER_STATUS_MAP);
  const orderTypeText = asText(auditoria?.orden_tipo, ORDER_TYPE_MAP);
  const infoTypeText = asText(auditoria?.info_tipo, INFO_TYPE_MAP);
  const resolutionText = asText(auditoria?.solucion_gestion, RESOLUTION_MAP);

  // Derivados/planificación
  const fechaProg = ymdToDmy(auditoria?.fecha || detalleAsignacion?.fecha);
  const bloqueProg = asText(
    auditoria?.bloque || detalleAsignacion?.reagendado_bloque || detalleAsignacion?.bloque,
    SLOT_MAP
  );
  const reschedDate = ymdToDmy(auditoria?.reschedule_date);
  const reschedSlot = asText(auditoria?.reschedule_slot, SLOT_MAP);

  // Formateos útiles
  const serviceIssuesText = Array.isArray(auditoria?.service_issues)
    ? auditoria.service_issues.join(", ")
    : (auditoria?.service_issues || "—");

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 860 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Auditoría registrada</h1>
          <p className={styles.subtitle}>Detalle de la visita y respuestas del checklist.</p>
        </header>

        {loading && <div className={styles.helper}>Cargando…</div>}
        {error && !loading && <div className={styles.error}>{error}</div>}

        {!loading && auditoria && (
          <>
            {/* Bloque de cabecera: datos de la dirección */}
            <div style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 12, marginBottom: 12 }}>
              <div className={styles.helper} style={{ fontWeight: 700, marginBottom: 6 }}>
                Dirección / Asignación
              </div>
              <Row label="Dirección">{auditoria?.direccion || detalleAsignacion?.direccion}</Row>
              <Row label="Comuna">{auditoria?.comuna || detalleAsignacion?.comuna}</Row>
              <Row label="Marca">{auditoria?.marca || detalleAsignacion?.marca}</Row>
              <Row label="Tecnología">{auditoria?.tecnologia || detalleAsignacion?.tecnologia}</Row>
              <Row label="RUT cliente">{detalleAsignacion?.rut_cliente}</Row>
              <Row label="ID vivienda">{detalleAsignacion?.id_vivienda}</Row>
              <Row label="Fecha programada">{fechaProg}</Row>
              <Row label="Bloque programado">{bloqueProg}</Row>
            </div>

            {/* Estado general */}
            <div style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 12, marginBottom: 12 }}>
              <div className={styles.helper} style={{ fontWeight: 700, marginBottom: 6 }}>
                Resultado / Estado del cliente
              </div>

              <Row label="Resultado (customer_status)">{customerStatusText}</Row>
              <Row label="Reagendado para">
                {reschedDate} {reschedSlot !== "—" ? `· ${reschedSlot}` : ""}
              </Row>

              <Row label="Tipo de orden">{orderTypeText}</Row>
              <Row label="Tipo de info">{infoTypeText}</Row>
              <Row label="Resolución">{resolutionText}</Row>
              <Row label="Descripción final">{auditoria?.descripcion_problema || "—"}</Row>
            </div>

            {/* Checklist (1/2/3 -> Sí/No/No Aplica) */}
            <div style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 12, marginBottom: 12 }}>
              <div className={styles.helper} style={{ fontWeight: 700, marginBottom: 6 }}>
                Checklist de visita
              </div>

              <Row label="Se informó horario (fecha/hora)">{enum123(auditoria?.schedule_informed_datetime)}</Row>
              <Row label="Se informó que un adulto debía estar presente">{enum123(auditoria?.schedule_informed_adult_required)}</Row>
              <Row label="Se informaron los servicios a instalar">{enum123(auditoria?.schedule_informed_services)}</Row>
              <Row label="Comentarios de agendamiento">{auditoria?.agend_comentarios || "—"}</Row>

              <Row label="Llegada dentro del bloque">{enum123(auditoria?.arrival_within_slot)}</Row>
              <Row label="Mostró identificación">{enum123(auditoria?.identification_shown)}</Row>
              <Row label="Explicó antes de iniciar">{enum123(auditoria?.explained_before_start)}</Row>
              <Row label="Comentarios de llegada">{auditoria?.llegada_comentarios || "—"}</Row>

              <Row label="Preguntó ubicación de equipos">{enum123(auditoria?.asked_equipment_location)}</Row>
              <Row label="Instalación prolija y segura">{enum123(auditoria?.tidy_and_safe_install)}</Row>
              <Row label="Cables ordenados">{enum123(auditoria?.tidy_cabling)}</Row>
              <Row label="Niveles de señal verificados">{enum123(auditoria?.verified_signal_levels)}</Row>
              <Row label="ONT/Módem OK">{enum123(auditoria?.ont_modem_ok)}</Row>

              <Row label="Router configurado">{enum123(auditoria?.configured_router)}</Row>
              <Row label="Probó con dispositivo">{enum123(auditoria?.tested_device)}</Row>
              <Row label="TV funcionando">{enum123(auditoria?.tv_functioning)}</Row>
              <Row label="Dejó instrucciones">{enum123(auditoria?.left_instructions)}</Row>
              <Row label="Comentarios de configuración">{auditoria?.config_comentarios || "—"}</Row>

              <Row label="Revisó trabajo con el cliente">{enum123(auditoria?.reviewed_with_client)}</Row>
              <Row label="Obtuvo firma de consentimiento">{enum123(auditoria?.got_consent_signature)}</Row>
              <Row label="Dejó info de contacto">{enum123(auditoria?.left_contact_info)}</Row>
              <Row label="Cierre: comentarios">{auditoria?.cierre_comentarios || "—"}</Row>

              <Row label="Percepción del cliente">{auditoria?.percepcion || "—"}</Row>
            </div>

            {/* Problemas y observaciones */}
            <div style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 12, marginBottom: 12 }}>
              <div className={styles.helper} style={{ fontWeight: 700, marginBottom: 6 }}>
                Problemas reportados
              </div>

              <Row label="Servicio(s) con problemas">{serviceIssuesText}</Row>
              <Row label="Internet: categoría">{auditoria?.internet_categoria || "—"}</Row>
              <Row label="Internet: otro">{auditoria?.internet_otro || "—"}</Row>
              <Row label="TV: categoría">{auditoria?.tv_categoria || "—"}</Row>
              <Row label="TV: otro">{auditoria?.tv_otro || "—"}</Row>
              <Row label="Descripción otros problemas">{auditoria?.otro_descripcion || "—"}</Row>
              <Row label="Detalle problema HFC">{auditoria?.desc_hfc || "—"}</Row>

              <Row label="Mala práctica (empresa)">
                {auditoria?.detalle_mala_practica_empresa || "—"}
              </Row>
              <Row label="Mala práctica (instalador)">
                {auditoria?.detalle_mala_practica_instalador || "—"}
              </Row>
            </div>

            {/* Fotos */}
            <div style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 12 }}>
              <div className={styles.helper} style={{ fontWeight: 700, marginBottom: 6 }}>
                Evidencia fotográfica
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                {["photo1", "photo2", "photo3"].map((key) => {
                  const url = auditoria?.[key];
                  return (
                    <div key={key} style={{ border: "1px solid #eee", borderRadius: 8, padding: 8, textAlign: "center" }}>
                      {url ? (
                        <a href={url} target="_blank" rel="noreferrer">
                          <img src={url} alt={key} style={{ maxWidth: "100%", borderRadius: 6 }} />
                        </a>
                      ) : (
                        <span className={styles.helper}>Sin {key}</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className={styles.actions} style={{ marginTop: 12 }}>
              <button className={styles.button} style={{ background: "#6b7280" }} onClick={() => navigate(-1)}>Volver</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
