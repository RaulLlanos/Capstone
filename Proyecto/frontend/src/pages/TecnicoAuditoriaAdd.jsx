/* eslint-disable no-unused-vars */
// src/pages/TecnicoAuditoriaAdd.jsx
import { useEffect, useMemo, useState, useLayoutEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

// --- Enums (alineados con tu backend) ---
const CUSTOMER_STATUS = [
  { value: "", label: "— Selecciona —" },
  { value: "AUTORIZA", label: "Autoriza" },
  { value: "SIN_MORADORES", label: "Sin Moradores" },
  { value: "RECHAZA", label: "Rechaza" },
  { value: "CONTINGENCIA", label: "Contingencia" },
  { value: "MASIVO", label: "Masivo" },
  { value: "REAGENDA", label: "Reagenda" },
];

const SI_NO_NA = [
  { value: "", label: "—" },
  { value: 1, label: "Sí" },
  { value: 2, label: "No" },
  { value: 3, label: "No Aplica" },
];

const INTERNET_ISSUE_CATEGORY = [
  { value: "", label: "—" },
  { value: "lento", label: "Navegación lenta" },
  { value: "wifi_alcance", label: "Alcance WiFi" },
  { value: "cortes", label: "Cortes / días sin servicio" },
  { value: "intermitencia", label: "Intermitencia" },
  { value: "otro", label: "Otro" },
];

const TV_ISSUE_CATEGORY = [
  { value: "", label: "—" },
  { value: "sin_senal", label: "Sin señal" },
  { value: "pixelado", label: "Pixelado" },
  { value: "intermitencia", label: "Intermitencia" },
  { value: "desfase", label: "Desfase con vivo" },
  { value: "streaming", label: "Plataformas streaming" },
  { value: "zapping", label: "Zapping/lentitud" },
  { value: "equipos", label: "Equipos (Dbox, IPTV, etc.)" },
  { value: "otro", label: "Otro" },
];

const RESOLUTION = [
  { value: "", label: "—" },
  { value: "terreno", label: "Se solucionó en terreno" },
  { value: "orden", label: "Gestión con Orden" },
];

const ORDER_TYPE = [
  { value: "", label: "—" },
  { value: "tecnica", label: "Técnica" },
  { value: "comercial", label: "Comercial" },
];

const INFO_TYPE = [
  { value: "", label: "—" },
  { value: "mala_practica", label: "Mala práctica" },
  { value: "problema_general", label: "Problema general" },
];

const BLOQUES = [
  { value: "10-13", label: "10:00-13:00" },
  { value: "14-18", label: "14:00-18:00" },
];

// --- Utils ---
function toYMD(d) {
  const x = d instanceof Date ? d : new Date(d);
  const y = x.getFullYear();
  const m = String(x.getMonth() + 1).padStart(2, "0");
  const day = String(x.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

// Busca si ya hay auditoría para esta asignación (no cambia)
async function findAuditForAsignacion(asignacionId) {
  try {
    const res = await api.get(`/api/auditorias/?asignacion=${asignacionId}`);
    const list = Array.isArray(res.data?.results)
      ? res.data.results
      : Array.isArray(res.data)
      ? res.data
      : [];
    return list.length ? list[0] : null;
  } catch (err) {
    console.warn("No se pudo listar auditorías:", err?.response?.status);
    return null;
  }
}

export default function TecnicoAuditoriaAdd() {
  const { id } = useParams(); // id de asignación
  const navigate = useNavigate();
  const { user } = useAuth();

  const [detalle, setDetalle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // --- Form state (usando nombres EXACTOS del modelo) ---
  const [form, setForm] = useState({
    customer_status: "",

    // Reagenda
    reschedule_date: "",
    reschedule_slot: "",

    // Llegada
    arrival_within_slot: "",
    identification_shown: "",
    explained_before_start: "",
    llegada_comentarios: "",

    // Agendamiento informado al cliente
    schedule_informed_datetime: "",
    schedule_informed_adult_required: "",
    schedule_informed_services: "",
    agend_comentarios: "",

    // Instalación
    asked_equipment_location: "",
    tidy_and_safe_install: "",
    tidy_cabling: "",
    verified_signal_levels: "",
    proceso_comentarios: "",

    // Configuración y pruebas
    configured_router: "",
    tested_device: "",
    tv_functioning: "",
    left_instructions: "",
    config_comentarios: "",

    // Cierre
    reviewed_with_client: "",
    got_consent_signature: "",
    left_contact_info: "",
    cierre_comentarios: "",

    // Percepción / NPS
    percepcion: "",
    nps_proceso: "",
    nps_tecnico: "",
    nps_claro_vtr: "",

    // Diagnóstico / resolución / info
    ont_modem_ok: "",
    service_issues: "",          // si usas checkboxes podría ser array; aquí mantenemos string o JSON según tu front
    internet_categoria: "",
    internet_otro: "",
    tv_categoria: "",
    tv_otro: "",
    otro_descripcion: "",
    solucion_gestion: "",
    orden_tipo: "",
    info_tipo: "",
    detalle_mala_practica_empresa: "",
    detalle_mala_practica_instalador: "",
    descripcion_problema: "",

    // Solo HFC
    desc_hfc: "",

    // Fotos
    photo1: null,
    photo2: null,
    photo3: null,
  });

  // Carga asignación + redirige si ya hay auditoría
  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const res = await api.get(`/api/asignaciones/${id}/`);
        setDetalle(res.data || {});

        const existing = await findAuditForAsignacion(id);
        if (existing) {
          navigate(`/tecnico/auditoria/ver/${id}`, { replace: true });
          return;
        }
      } catch (err) {
        console.error("GET asignación:", err?.response?.status, err?.response?.data);
        setError("No se pudo cargar la asignación.");
      } finally {
        setLoading(false);
      }
    })();
  }, [id, navigate]);

  // --- Mantener scroll al cambiar selects / inputs pesados ---
  function usePreventJumpOnHeavyControls() {
    useLayoutEffect(() => {
      let lastY = 0;
      let raf = null;

      const saveY = () => { lastY = window.scrollY; };
      const restoreY = () => {
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          window.scrollTo(0, lastY);
          raf = null;
        });
      };

      const onChangeCapture = (e) => {
        const el = e.target;
        const tag = el?.tagName;
        const type = el?.type;
        if (tag === "SELECT" || type === "file") {
          saveY();
          restoreY();
        }
      };

      document.addEventListener("change", onChangeCapture, true);
      return () => {
        document.removeEventListener("change", onChangeCapture, true);
        if (raf) cancelAnimationFrame(raf);
      };
    }, []);
  }
  usePreventJumpOnHeavyControls();

  // UI helpers
  const onChange = (e) => {
    const { name, value, files } = e.target;
    if (files && files.length) setForm((f) => ({ ...f, [name]: files[0] }));
    else setForm((f) => ({ ...f, [name]: value }));
    setError("");
  };

  const onChangeNumber = (e) => {
    const { name, value } = e.target;
    const v = value === "" ? "" : Number(value);
    setForm((f) => ({ ...f, [name]: v }));
    setError("");
  };

  const needsReschedule = form.customer_status === "REAGENDA";

  // Validación mínima
  const validate = () => {
    if (!detalle?.id) return "Asignación no cargada.";
    if (!form.customer_status) return "Selecciona el estado del cliente.";
    if (needsReschedule) {
      if (!form.reschedule_date) return "Falta la fecha de re-agendamiento.";
      if (!form.reschedule_slot) return "Falta el bloque de re-agendamiento.";
    }
    return "";
  };

  // Submit
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!id) { setError("Asignación no cargada."); return; }

    const msg = validate();
    if (msg) { setError(msg); return; }

    try {
      setSaving(true);
      await api.get("/auth/csrf").catch(() => {});

      // 1) Yo
      const me = (await api.get("/api/usuarios/me/")).data;
      // 2) Asignación
      let asig = (await api.get(`/api/asignaciones/${id}/`)).data;

      // 3) Si no es mía, error
      if (asig.asignado_a !== me.id) {
        throw new Error("No se pudo tomar la asignación.");
      }

      // 4) Payload: usar NOMBRES DEL MODELO
      const fd = new FormData();
      fd.append("asignacion", parseInt(id, 10));

      if (form.customer_status) fd.append("customer_status", form.customer_status);
      if (form.reschedule_date) fd.append("reschedule_date", form.reschedule_date);
      if (form.reschedule_slot) fd.append("reschedule_slot", form.reschedule_slot);

      if (form.ont_modem_ok !== "") fd.append("ont_modem_ok", String(form.ont_modem_ok));

      // service_issues: si en tu front realmente es un array, usa JSON.stringify
      if (Array.isArray(form.service_issues)) {
        fd.append("service_issues", JSON.stringify(form.service_issues));
      } else if (form.service_issues) {
        fd.append("service_issues", form.service_issues);
      }

      if (form.internet_categoria) fd.append("internet_categoria", form.internet_categoria);
      if (form.internet_otro) fd.append("internet_otro", form.internet_otro);
      if (form.tv_categoria) fd.append("tv_categoria", form.tv_categoria);
      if (form.tv_otro) fd.append("tv_otro", form.tv_otro);
      if (form.otro_descripcion) fd.append("otro_descripcion", form.otro_descripcion);

      if (form.photo1) fd.append("photo1", form.photo1);
      if (form.photo2) fd.append("photo2", form.photo2);
      if (form.photo3) fd.append("photo3", form.photo3);

      if (form.desc_hfc) fd.append("desc_hfc", form.desc_hfc);

      if (form.schedule_informed_datetime !== "") fd.append("schedule_informed_datetime", String(form.schedule_informed_datetime));
      if (form.schedule_informed_adult_required !== "") fd.append("schedule_informed_adult_required", String(form.schedule_informed_adult_required));
      if (form.schedule_informed_services !== "") fd.append("schedule_informed_services", String(form.schedule_informed_services));
      if (form.agend_comentarios) fd.append("agend_comentarios", form.agend_comentarios);

      if (form.arrival_within_slot !== "") fd.append("arrival_within_slot", String(form.arrival_within_slot));
      if (form.identification_shown !== "") fd.append("identification_shown", String(form.identification_shown));
      if (form.explained_before_start !== "") fd.append("explained_before_start", String(form.explained_before_start));
      if (form.llegada_comentarios) fd.append("llegada_comentarios", form.llegada_comentarios);

      if (form.asked_equipment_location !== "") fd.append("asked_equipment_location", String(form.asked_equipment_location));
      if (form.tidy_and_safe_install !== "") fd.append("tidy_and_safe_install", String(form.tidy_and_safe_install));
      if (form.tidy_cabling !== "") fd.append("tidy_cabling", String(form.tidy_cabling));
      if (form.verified_signal_levels !== "") fd.append("verified_signal_levels", String(form.verified_signal_levels));
      if (form.proceso_comentarios) fd.append("proceso_comentarios", form.proceso_comentarios);

      if (form.configured_router !== "") fd.append("configured_router", String(form.configured_router));
      if (form.tested_device !== "") fd.append("tested_device", String(form.tested_device));
      if (form.tv_functioning !== "") fd.append("tv_functioning", String(form.tv_functioning));
      if (form.left_instructions !== "") fd.append("left_instructions", String(form.left_instructions));
      if (form.config_comentarios) fd.append("config_comentarios", form.config_comentarios);

      if (form.reviewed_with_client !== "") fd.append("reviewed_with_client", String(form.reviewed_with_client));
      if (form.got_consent_signature !== "") fd.append("got_consent_signature", String(form.got_consent_signature));
      if (form.left_contact_info !== "") fd.append("left_contact_info", String(form.left_contact_info));
      if (form.cierre_comentarios) fd.append("cierre_comentarios", form.cierre_comentarios);

      if (form.percepcion) fd.append("percepcion", form.percepcion);

      if (form.nps_proceso !== "") fd.append("nps_proceso", String(form.nps_proceso));
      if (form.nps_tecnico !== "") fd.append("nps_tecnico", String(form.nps_tecnico));
      if (form.nps_claro_vtr !== "") fd.append("nps_claro_vtr", String(form.nps_claro_vtr));

      if (form.solucion_gestion) fd.append("solucion_gestion", form.solucion_gestion);
      if (form.orden_tipo) fd.append("orden_tipo", form.orden_tipo);
      if (form.info_tipo) fd.append("info_tipo", form.info_tipo);
      if (form.detalle_mala_practica_empresa) fd.append("detalle_mala_practica_empresa", form.detalle_mala_practica_empresa);
      if (form.detalle_mala_practica_instalador) fd.append("detalle_mala_practica_instalador", form.detalle_mala_practica_instalador);
      if (form.descripcion_problema) fd.append("descripcion_problema", form.descripcion_problema);

      // 5) Crear auditoría
      await api.post("/api/auditorias/", fd); // 201
      await api.patch(`/api/asignaciones/${id}/`, { estado: "VISITADA" });

      // 6) Redirigir
      navigate(`/tecnico/auditoria/ver/${id}`, {
        replace: true,
        state: { flash: "Auditoría registrada." },
      });
    } catch (err) {
      console.error("POST auditoría:", err?.response?.status, err?.response?.data);
      const data = err?.response?.data || {};
      const msg =
        typeof data === "string"
          ? data
          : data.detail ||
            data.error ||
            (Array.isArray(data.non_field_errors) ? data.non_field_errors.join(" ") : "") ||
            "No se pudo registrar la auditoría.";
      setError(msg || "No se pudo registrar la auditoría.");
    } finally {
      setSaving(false);
    }
  };

  // --- UI: contenedor secciones ---
  const Section = ({ title, children }) => (
    <section style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 12, marginBottom: 12 }}>
      <div className={styles.helper} style={{ fontWeight: 700, marginBottom: 8 }}>{title}</div>
      <div className={styles.form} style={{ gap: 8 }}>{children}</div>
    </section>
  );

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 900 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Auditoría de instalación</h1>
          <p className={styles.subtitle}>Completa el formulario y adjunta evidencias si corresponde.</p>
        </header>

        {loading ? (
          <div className={styles.helper}>Cargando…</div>
        ) : (
          <>
            {/* Resumen asignación */}
            <Section title="Asignación">
              <div className={styles.helper}><strong>Dirección:</strong> {detalle?.direccion || "—"}</div>
              <div className={styles.helper}><strong>Comuna:</strong> {detalle?.comuna || "—"}</div>
              <div className={styles.helper}><strong>Marca:</strong> {detalle?.marca || "—"}</div>
              <div className={styles.helper}><strong>Tecnología:</strong> {detalle?.tecnologia || "—"}</div>
              <div className={styles.helper}><strong>RUT cliente:</strong> {detalle?.rut_cliente || "—"}</div>
              <div className={styles.helper}><strong>ID vivienda:</strong> {detalle?.id_vivienda || "—"}</div>
              <div className={styles.helper}><strong>Fecha:</strong> {String(detalle?.fecha || "").slice(0,10) || "—"}</div>
              <div className={styles.helper}><strong>Estado:</strong> {detalle?.estado || "—"}</div>
            </Section>

            <form onSubmit={handleSubmit} className={styles.form}>
              {error && <div className={styles.error} style={{ marginBottom: 8 }}>{error}</div>}

              <Section title="Estado del cliente (Q5)">
                <label className={styles.label}>
                  Resultado
                  <select
                    className={styles.select}
                    name="customer_status"
                    value={form.customer_status}
                    onChange={onChange}
                    disabled={saving}
                  >
                    {CUSTOMER_STATUS.map((o) => (
                      <option key={o.value || "blank"} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </label>

                {needsReschedule && (
                  <>
                    <label className={styles.label}>
                      Nueva fecha
                      <input
                        type="date"
                        className={styles.input}
                        name="reschedule_date"
                        value={form.reschedule_date}
                        onChange={onChange}
                        disabled={saving}
                        min={toYMD(new Date())}
                      />
                    </label>
                    <label className={styles.label}>
                      Bloque
                      <select
                        className={styles.select}
                        name="reschedule_slot"
                        value={form.reschedule_slot}
                        onChange={onChange}
                        disabled={saving}
                      >
                        <option value="">—</option>
                        {BLOQUES.map((b) => (
                          <option key={b.value} value={b.value}>{b.label}</option>
                        ))}
                      </select>
                    </label>
                  </>
                )}
              </Section>

              <Section title="Agendamiento informado al cliente">
                <label className={styles.label}>
                  Informó fecha/hora
                  <select
                    className={styles.select}
                    name="schedule_informed_datetime"
                    value={form.schedule_informed_datetime}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`sidt-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Informó adulto responsable
                  <select
                    className={styles.select}
                    name="schedule_informed_adult_required"
                    value={form.schedule_informed_adult_required}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`sadr-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Informó servicios a instalar
                  <select
                    className={styles.select}
                    name="schedule_informed_services"
                    value={form.schedule_informed_services}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`sise-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Comentarios de agendamiento
                  <textarea
                    className={styles.textarea}
                    name="agend_comentarios"
                    value={form.agend_comentarios}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChange}
                    disabled={saving}
                  />
                </label>
              </Section>

              <Section title="Llegada">
                <label className={styles.label}>
                  Llegó dentro del bloque
                  <select
                    className={styles.select}
                    name="arrival_within_slot"
                    value={form.arrival_within_slot}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`aws-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Mostró identificación
                  <select
                    className={styles.select}
                    name="identification_shown"
                    value={form.identification_shown}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`ids-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Explicó antes de iniciar
                  <select
                    className={styles.select}
                    name="explained_before_start"
                    value={form.explained_before_start}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`ebs-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Comentarios de llegada
                  <textarea
                    className={styles.textarea}
                    name="llegada_comentarios"
                    value={form.llegada_comentarios}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChange}
                    disabled={saving}
                  />
                </label>
              </Section>

              <Section title="Instalación">
                <label className={styles.label}>
                  Preguntó ubicación de equipos
                  <select
                    className={styles.select}
                    name="asked_equipment_location"
                    value={form.asked_equipment_location}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`ael-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Orden y seguridad en instalación
                  <select
                    className={styles.select}
                    name="tidy_and_safe_install"
                    value={form.tidy_and_safe_install}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`tasi-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Cableado ordenado
                  <select
                    className={styles.select}
                    name="tidy_cabling"
                    value={form.tidy_cabling}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`tc-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Niveles de señal verificados
                  <select
                    className={styles.select}
                    name="verified_signal_levels"
                    value={form.verified_signal_levels}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`vsl-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Comentarios del proceso
                  <textarea
                    className={styles.textarea}
                    name="proceso_comentarios"
                    value={form.proceso_comentarios}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChange}
                    disabled={saving}
                  />
                </label>
              </Section>

              <Section title="Configuración y pruebas">
                <label className={styles.label}>
                  Router configurado
                  <select
                    className={styles.select}
                    name="configured_router"
                    value={form.configured_router}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`cr-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Dispositivo probado
                  <select
                    className={styles.select}
                    name="tested_device"
                    value={form.tested_device}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`td-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  TV funcionando
                  <select
                    className={styles.select}
                    name="tv_functioning"
                    value={form.tv_functioning}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`tvf-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Dejó instructivo
                  <select
                    className={styles.select}
                    name="left_instructions"
                    value={form.left_instructions}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`li-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Comentarios de configuración
                  <textarea
                    className={styles.textarea}
                    name="config_comentarios"
                    value={form.config_comentarios}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChange}
                    disabled={saving}
                  />
                </label>
              </Section>

              <Section title="Cierre">
                <label className={styles.label}>
                  Revisó con el cliente
                  <select
                    className={styles.select}
                    name="reviewed_with_client"
                    value={form.reviewed_with_client}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`rwc-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Obtuvo firma de consentimiento
                  <select
                    className={styles.select}
                    name="got_consent_signature"
                    value={form.got_consent_signature}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`gcs-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Dejó info de contacto
                  <select
                    className={styles.select}
                    name="left_contact_info"
                    value={form.left_contact_info}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`lci-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Comentarios de cierre
                  <textarea
                    className={styles.textarea}
                    name="cierre_comentarios"
                    value={form.cierre_comentarios}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChange}
                    disabled={saving}
                  />
                </label>
              </Section>

              <Section title="Percepción / NPS">
                <label className={styles.label}>
                  Notas de percepción
                  <textarea
                    className={styles.textarea}
                    name="percepcion"
                    value={form.percepcion}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChange}
                    disabled={saving}
                  />
                </label>
                <label className={styles.label}>
                  NPS Proceso
                  <input
                    className={styles.input}
                    name="nps_proceso"
                    type="number"
                    min="0"
                    max="10"
                    value={form.nps_proceso}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChangeNumber}
                    disabled={saving}
                  />
                </label>
                <label className={styles.label}>
                  NPS Técnico
                  <input
                    className={styles.input}
                    name="nps_tecnico"
                    type="number"
                    min="0"
                    max="10"
                    value={form.nps_tecnico}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChangeNumber}
                    disabled={saving}
                  />
                </label>
                <label className={styles.label}>
                  NPS Marca
                  <input
                    className={styles.input}
                    name="nps_claro_vtr"
                    type="number"
                    min="0"
                    max="10"
                    value={form.nps_claro_vtr}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChangeNumber}
                    disabled={saving}
                  />
                </label>
              </Section>

              <Section title="Diagnóstico y resolución">
                <label className={styles.label}>
                  ONT/Modem OK
                  <select
                    className={styles.select}
                    name="ont_modem_ok"
                    value={form.ont_modem_ok}
                    onChange={onChangeNumber}
                    disabled={saving}
                  >
                    {SI_NO_NA.map((o) => <option key={`omo-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>

                <label className={styles.label}>
                  Problema Internet
                  <select
                    className={styles.select}
                    name="internet_categoria"
                    value={form.internet_categoria}
                    onChange={onChange}
                    disabled={saving}
                  >
                    {INTERNET_ISSUE_CATEGORY.map((o) => <option key={`iic-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  Internet (otro)
                  <input
                    className={styles.input}
                    name="internet_otro"
                    value={form.internet_otro}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChange}
                    disabled={saving}
                  />
                </label>

                <label className={styles.label}>
                  Problema TV
                  <select
                    className={styles.select}
                    name="tv_categoria"
                    value={form.tv_categoria}
                    onChange={onChange}
                    disabled={saving}
                  >
                    {TV_ISSUE_CATEGORY.map((o) => <option key={`tvic-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className={styles.label}>
                  TV (otro)
                  <input
                    className={styles.input}
                    name="tv_otro"
                    value={form.tv_otro}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChange}
                    disabled={saving}
                  />
                </label>

                <label className={styles.label}>
                  Otro problema (descripción)
                  <textarea
                    className={styles.textarea}
                    name="otro_descripcion"
                    value={form.otro_descripcion}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChange}
                    disabled={saving}
                  />
                </label>

                <label className={styles.label}>
                  Resolución
                  <select
                    className={styles.select}
                    name="solucion_gestion"
                    value={form.solucion_gestion}
                    onChange={onChange}
                    disabled={saving}
                  >
                    {RESOLUTION.map((o) => <option key={`res-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>

                <label className={styles.label}>
                  Tipo de orden
                  <select
                    className={styles.select}
                    name="orden_tipo"
                    value={form.orden_tipo}
                    onChange={onChange}
                    disabled={saving}
                  >
                    {ORDER_TYPE.map((o) => <option key={`ot-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>

                <label className={styles.label}>
                  Tipo de información
                  <select
                    className={styles.select}
                    name="info_tipo"
                    value={form.info_tipo}
                    onChange={onChange}
                    disabled={saving}
                  >
                    {INFO_TYPE.map((o) => <option key={`it-${o.value}`} value={o.value}>{o.label}</option>)}
                  </select>
                </label>

                <label className={styles.label}>
                  Detalle mala práctica (empresa)
                  <input
                    className={styles.input}
                    name="detalle_mala_practica_empresa"
                    value={form.detalle_mala_practica_empresa}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChange}
                    disabled={saving}
                  />
                </label>
                <label className={styles.label}>
                  Detalle mala práctica (instalador)
                  <input
                    className={styles.input}
                    name="detalle_mala_practica_instalador"
                    value={form.detalle_mala_practica_instalador}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChange}
                    disabled={saving}
                  />
                </label>

                <label className={styles.label}>
                  Descripción final del problema
                  <textarea
                    className={styles.textarea}
                    name="descripcion_problema"
                    value={form.descripcion_problema}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChange}
                    disabled={saving}
                  />
                </label>
              </Section>

              <Section title="Solo HFC">
                <label className={styles.label}>
                  Detalle HFC
                  <textarea
                    className={styles.textarea}
                    name="desc_hfc"
                    value={form.desc_hfc}
                    onInputCapture={(e) => e.stopPropagation()}
                    onKeyDownCapture={(e) => e.stopPropagation()}
                    onChange={onChange}
                    disabled={saving}
                  />
                </label>
              </Section>

              <Section title="Evidencias (fotos)">
                <label className={styles.label} style={{ margin: 0 }}>
                  Foto 1
                  <input className={styles.input} type="file" name="photo1" accept="image/*" onChange={onChange} disabled={saving} />
                </label>
                <label className={styles.label} style={{ margin: 0 }}>
                  Foto 2
                  <input className={styles.input} type="file" name="photo2" accept="image/*" onChange={onChange} disabled={saving} />
                </label>
                <label className={styles.label} style={{ margin: 0 }}>
                  Foto 3
                  <input className={styles.input} type="file" name="photo3" accept="image/*" onChange={onChange} disabled={saving} />
                </label>
              </Section>

              <div className={styles.actions}>
                <button type="submit" className={styles.button} disabled={saving}>
                  {saving ? "Guardando…" : "Guardar auditoría"}
                </button>
                <button
                  type="button"
                  className={styles.button}
                  style={{ background: "#6b7280" }}
                  onClick={() => navigate(-1)}
                  disabled={saving}
                >
                  Volver
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
